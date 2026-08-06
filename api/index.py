"""Wrapper ASGI pour déployer l'app Streamlit sur Vercel (Fluid Compute).

Vercel ne peut pas exécuter Streamlit en tant que serveur natif : cette fonction
démarre le serveur Streamlit (Tornado) dans l'instance persistante de la fonction
et proxifie l'ensemble du trafic HTTP + WebSocket (/_stcore/...).

Limites connues (beta WebSocket Vercel) : connexion plafonnée à ~5 min par session
et premier chargement lent (démarrage du serveur ~15-30 s à froid).
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
import websockets
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect

ROOT = Path(__file__).resolve().parent.parent
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))
BASE = f"http://127.0.0.1:{STREAMLIT_PORT}"
LOG_FILE = Path("/tmp/streamlit_vercel.log")

app = FastAPI(title="Terroir Context Agents (Vercel wrapper)")
_logger = logging.getLogger("vercel-streamlit")
logging.basicConfig(level=logging.INFO)

_proc: subprocess.Popen | None = None
_ready = False
_last_error: str | None = None


def _env_with_deps() -> dict:
    """PYTHONPATH hérité des deps de la fonction (Vercel installe dans /tmp/_vc_deps)."""
    env = os.environ.copy()
    deps = [p for p in sys.path if "site-packages" in p and p.startswith("/tmp")]
    if deps:
        env["PYTHONPATH"] = os.pathsep.join(deps) + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _start_streamlit() -> None:
    """Démarre Streamlit dans l'instance de fonction (idempotent)."""
    global _proc, _ready, _last_error
    if _ready and _proc is not None and _proc.poll() is None:
        return
    if _proc is not None and _proc.poll() is None:
        _proc.terminate()
    entry = ROOT / "app.py"
    if not entry.exists():
        _last_error = f"app.py introuvable dans {ROOT} (cwd={os.getcwd()})"
        raise RuntimeError(_last_error)
    log = LOG_FILE.open("a")
    _proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(entry),
            "--server.port",
            str(STREAMLIT_PORT),
            "--server.address=127.0.0.1",
            "--server.headless=true",
            "--server.enableCORS=false",
            "--server.enableXsrfProtection=false",
            "--browser.gatherUsageStats=false",
        ],
        cwd=str(ROOT),
        env=_env_with_deps(),
        stdout=log,
        stderr=log,
    )
    for _ in range(120):
        if _proc.poll() is not None:
            tail = "".join(LOG_FILE.read_text(errors="replace").splitlines()[-5:])
            _last_error = f"streamlit s'est arrêté au démarrage (rc={_proc.returncode}) — {tail}"
            raise RuntimeError(_last_error)
        try:
            with httpx.Client(timeout=2.0) as client:
                if client.get(f"{BASE}/_stcore/health").status_code == 200:
                    _ready = True
                    _last_error = None
                    return
        except Exception:
            pass
        time.sleep(0.5)
    _last_error = "streamlit n'a pas répondu dans les délais"
    raise RuntimeError(_last_error)


async def _proxy(request: Request) -> Response:
    await asyncio.to_thread(_start_streamlit)
    url = BASE + request.url.path
    if request.url.query:
        url += "?" + request.url.query
    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length", "connection", "upgrade", "accept-encoding")
    }
    body = await request.body()
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.request(request.method, url, headers=headers, content=body)
    except httpx.HTTPError as exc:
        return Response(content=str(exc), status_code=502)
    response_headers = {
        k: v
        for k, v in resp.headers.items()
        if k.lower() not in ("transfer-encoding", "connection", "upgrade", "content-encoding", "vary", "etag", "last-modified")
    }
    return Response(content=resp.content, status_code=resp.status_code, headers=response_headers)


@app.get("/api/health")
async def api_health() -> dict:
    import site
    import sys as sys_mod

    streamlit_import = "absent"
    try:
        import streamlit  # noqa: F401

        streamlit_import = "ok"
    except Exception as exc:
        streamlit_import = f"echec: {exc}"
    info = {
        "ok": False,
        "executable": sys_mod.executable,
        "prefix": sys_mod.prefix,
        "site_packages": [p for p in sys_mod.path if "site-packages" in p],
        "streamlit": streamlit_import,
        "root": str(ROOT),
        "cwd": os.getcwd(),
        "last_error": _last_error,
    }
    try:
        await asyncio.to_thread(_start_streamlit)
    except Exception as exc:
        info["error"] = str(exc)
        return info
    info["ok"] = True
    return info


@app.websocket("/_stcore/{rest:path}")
async def streamlit_ws(websocket: WebSocket, rest: str) -> None:
    """Proxifie le canal WebSocket de Streamlit vers le serveur interne."""
    query = websocket.url.query
    requested_protocols = websocket.headers.get("sec-websocket-protocol", "")
    subprotocol = requested_protocols.split(",")[0].strip() or None
    _logger.info("WS handshake: path=%s subprotocol=%r query=%s", rest, subprotocol, query)
    await websocket.accept(subprotocol=subprotocol)
    await asyncio.to_thread(_start_streamlit)
    upstream_url = BASE.replace("http://", "ws://") + "/_stcore/" + rest + (f"?{query}" if query else "")
    try:
        connect_kwargs = {"max_size": None, "ping_interval": None}
        if subprotocol:
            connect_kwargs["subprotocols"] = [subprotocol]
        async with websockets.connect(upstream_url, **connect_kwargs) as upstream:
            _logger.info("WS upstream connected: %s", rest)

            async def upstream_to_client() -> None:
                count = 0
                try:
                    while True:
                        message = await upstream.recv()
                        count += 1
                        if isinstance(message, bytes):
                            await websocket.send_bytes(message)
                        else:
                            await websocket.send_text(message)
                except Exception as exc:
                    _logger.info("WS upstream pump end after %d msgs: %s", count, exc)
                    try:
                        await websocket.close()
                    except Exception:
                        pass

            pump = asyncio.create_task(upstream_to_client())
            try:
                while True:
                    incoming = await websocket.receive()
                    message_type = incoming.get("type")
                    if message_type == "websocket.disconnect":
                        break
                    data = incoming.get("bytes")
                    if data is None:
                        data = incoming.get("text")
                    if data is not None:
                        await upstream.send(data)
            finally:
                pump.cancel()
    except (WebSocketDisconnect, websockets.exceptions.WebSocketException, OSError) as exc:
        _logger.info("WS proxy closed: %s", exc)


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
async def catch_all(path: str, request: Request) -> Response:
    return await _proxy(request)
