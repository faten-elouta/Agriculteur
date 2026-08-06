"""Serveur GMS-compatible pour la démo publique.

Implémente le sous-ensemble de l'API OpenAPI de DataHub GMS utilisé par
l'application (fraîcheur, lineage, runs, incidents), avec les données seedées
depuis fixtures/graph.json. Stockage en mémoire : l'état se réinitialise au
redémarrage — adapté à la démo, pas à la production.

Endpoints (contrat identique à DataHub GMS) :
- GET  /health
- GET  /openapi/v3/entity/dataset/{urn}?aspects=...
- GET  /openapi/v3/entity/dataset/{urn}/lineage
- POST /openapi/v3/entity/dataset
- POST /openapi/v3/entity/mlModel
- POST /openapi/v3/entity/incident
- POST /openapi/v3/entity/incident/{urn}
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

ROOT = Path(__file__).resolve().parent.parent
GRAPH_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "graph.json"

app = FastAPI(title="Terroir Context Agents — GMS compatible (démo)")

_STORE: dict[str, dict[str, Any]] = {}
_RELATIONSHIPS: dict[str, list[dict[str, str]]] = {}
_INCIDENTS: dict[str, dict[str, Any]] = {}
_INCIDENT_COUNTER = 0


def short_name(urn: str) -> str:
    return urn.split(",")[1]


def _load_graph() -> dict[str, Any]:
    if not GRAPH_PATH.exists():
        raise RuntimeError(f"fixtures/graph.json introuvable : {GRAPH_PATH}")
    return json.loads(GRAPH_PATH.read_text(encoding="utf-8"))


def _seed() -> None:
    graph = _load_graph()
    _STORE.clear()
    _RELATIONSHIPS.clear()
    _INCIDENTS.clear()
    for urn, props in graph.get("datasets", {}).items():
        custom = {
            "niveau_de_preuve": str(props.get("niveau_de_preuve", "")),
            "freshness_sla_days": str(props.get("freshness_sla_days", "")),
            "last_updated": str(props.get("last_updated", "")),
            "spatial_coverage": str(props.get("spatial_coverage", "")),
            "licence": str(props.get("licence", "")),
            "redistribuable": str(props.get("redistribuable", "")),
        }
        _STORE[urn] = {
            "name": short_name(urn),
            "description": "Source de contexte Terroir Context Agents — licence et SLA déclarés par l'ingestion.",
            "customProperties": custom,
        }
    lineage = graph.get("lineage", {})
    for urn in list(_STORE):
        upstreams = [k for k, targets in lineage.items() if urn in targets]
        downstreams = lineage.get(urn, [])
        _RELATIONSHIPS[urn] = [{"entity": u, "type": "UPSTREAM"} for u in upstreams] + [
            {"entity": d, "type": "DOWNSTREAM"} for d in downstreams
        ]


_seed()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/")
async def root() -> dict:
    return {
        "service": "Terroir Context Agents — serveur GMS compatible (démo)",
        "datasets": len(_STORE),
        "incidents": len(_INCIDENTS),
        "graph": str(GRAPH_PATH),
    }


@app.get("/openapi/v3/entity/dataset/{urn}")
async def dataset_get(urn: str, aspects: Optional[str] = None) -> dict:
    entity = _STORE.get(urn)
    if entity is None:
        return {"results": []}
    wanted = set((aspects or "").split(",")) if aspects else None
    result_aspects: dict[str, Any] = {}
    if wanted is None or "datasetProperties" in wanted:
        result_aspects["datasetProperties"] = entity
    if wanted is None or "status" in wanted:
        result_aspects["status"] = {"removed": False}
    return {"results": [{"urn": urn, "aspects": result_aspects}]}


@app.get("/openapi/v3/entity/dataset/{urn}/lineage")
async def dataset_lineage(urn: str) -> dict:
    if urn not in _STORE:
        return {"results": []}
    return {"results": [{"urn": urn, "relationships": _RELATIONSHIPS.get(urn, [])}]}


@app.post("/openapi/v3/entity/dataset")
async def dataset_upsert(request: Request) -> dict:
    body = await request.json()
    urn = body.get("urn", "")
    aspects = body.get("aspects", {})
    properties = aspects.get("datasetProperties", {})
    existing = _STORE.get(urn, {"name": short_name(urn), "description": "", "customProperties": {}})
    custom = dict(existing.get("customProperties", {}))
    custom.update(properties.get("customProperties", {}))
    _STORE[urn] = {
        "name": properties.get("name", existing.get("name", short_name(urn))),
        "description": properties.get("description", existing.get("description", "")),
        "customProperties": custom,
    }
    return JSONResponse(status_code=201, content={"results": [{"urn": urn}]})


@app.post("/openapi/v3/entity/mlModel")
async def ml_model_upsert(request: Request) -> dict:
    body = await request.json()
    urn = body.get("urn", "")
    _STORE.setdefault(urn, {"name": short_name(urn), "description": "", "customProperties": {}})
    return JSONResponse(status_code=201, content={"results": [{"urn": urn}]})


@app.post("/openapi/v3/entity/incident")
async def incident_create(request: Request) -> dict:
    global _INCIDENT_COUNTER
    body = await request.json()
    _INCIDENT_COUNTER += 1
    urn = f"urn:li:incident:(demo,{_INCIDENT_COUNTER})"
    info = body.get("aspects", {}).get("incidentInfo", {})
    _INCIDENTS[urn] = {
        "title": info.get("title", ""),
        "description": info.get("description", ""),
        "entityUrns": body.get("entityUrns", []),
        "status": "ACTIVE",
        "createdAt": info.get("createdAt", int(time.time() * 1000)),
    }
    return JSONResponse(status_code=201, content={"results": [{"urn": urn}]})


@app.post("/openapi/v3/entity/incident/{urn}")
async def incident_update(urn: str, request: Request) -> dict:
    body = await request.json()
    info = body.get("aspects", {}).get("incidentInfo", {})
    incident = _INCIDENTS.setdefault(urn, {"title": "", "description": "", "entityUrns": [], "status": "ACTIVE"})
    state = info.get("status", {}).get("state", "ACTIVE")
    if state == "RESOLVED":
        incident["status"] = "RESOLVED"
        incident["resolvedAt"] = info.get("resolvedAt", int(time.time() * 1000))
    else:
        incident["status"] = state
    return {"results": [{"urn": urn}]}


@app.get("/openapi/v3/entity/incident/{urn}")
async def incident_get(urn: str) -> dict:
    incident = _INCIDENTS.get(urn)
    if incident is None:
        return {"results": []}
    return {
        "results": [
            {
                "urn": urn,
                "aspects": {
                    "incidentInfo": {
                        "incidentType": "OPERATIONAL",
                        "title": incident["title"],
                        "description": incident["description"],
                        "status": {"state": incident["status"]},
                        "createdAt": incident.get("createdAt"),
                    }
                },
            }
        ]
    }


@app.get("/openapi/v3/entity/incident")
async def incident_list() -> dict:
    return {
        "results": [
            {
                "urn": urn,
                "aspects": {
                    "incidentInfo": {
                        "incidentType": "OPERATIONAL",
                        "title": incident["title"],
                        "description": incident["description"],
                        "status": {"state": incident["status"]},
                    }
                },
            }
            for urn, incident in _INCIDENTS.items()
        ]
    }
