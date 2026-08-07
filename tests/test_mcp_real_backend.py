"""Mode réel du serveur MCP : chaque outil lit/écrit dans un vrai GMS via DataHubClient.

Le GMS minimal (gms/main.py) sert aussi le contrat SDK (GraphQL scroll +
OpenAPI v2 batch) : on le démarre en HTTP, on pointe DATAHUB_GMS_URL dessus,
et on appelle les outils MCP directement — la chaîne complète est exercée :
outil MCP → DataHubClient (SDK + REST) → HTTP du GMS. Aucun mock de SDK ici.

Le mode démo (sans DATAHUB_GMS_URL) reste couvert par le même test.
"""

from __future__ import annotations

import socket
import threading
import time

import pytest

# gms.main doit être importé avant gms.mcp_server (gms.main importe gms.mcp_server).
from gms import main as gms_main  # noqa: E402,F401
from gms import mcp_server  # noqa: E402

HYDRO = "urn:li:dataset:(urn:li:dataPlatform:duckdb,hubeau_hydrometrie,PROD)"


@pytest.fixture()
def gms_url():
    """Sert gms.main:app sur un port libre et renvoie son URL (HTTP réel)."""
    from gms import main as gms_main

    gms_main._seed()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    import uvicorn

    thread = threading.Thread(
        target=lambda: uvicorn.run(gms_main.app, host="127.0.0.1", port=port, log_level="error"),
        daemon=True,
    )
    thread.start()
    time.sleep(2.0)
    yield f"http://127.0.0.1:{port}"


def _real(monkeypatch, url):
    """Branche les outils MCP sur le GMS réel (comme en production)."""
    monkeypatch.setenv("DATAHUB_GMS_URL", url)
    return mcp_server._backend()


def test_mode_reel_liste_les_datasets_du_graphe(monkeypatch, gms_url):
    backend = _real(monkeypatch, gms_url)
    datasets = backend.list_datasets()
    assert len(datasets) == 11
    hydro = next(d for d in datasets if d["name"] == "hubeau_hydrometrie")
    assert hydro["customProperties"]["niveau_de_preuve"] == "mesure"
    assert hydro["customProperties"]["freshness_sla_days"] == "5"


def test_mode_reel_lineage_et_fraicheur(monkeypatch, gms_url):
    backend = _real(monkeypatch, gms_url)
    lineage = backend.get_lineage("hubeau_hydrometrie")
    assert lineage == {"dataset": "hubeau_hydrometrie", "upstream": [], "downstream": ["features_bilan_hydrique"]}
    summary = backend.freshness_summary()
    assert len(summary["sources"]) == 11
    assert summary["ok"] + summary["stale"] + summary["unknown"] == 11
    assert summary["sources"]["hubeau_hydrometrie"]["urn"] == HYDRO


def test_mode_reel_ecrit_dans_le_graphe(monkeypatch, gms_url):
    backend = _real(monkeypatch, gms_url)

    run = backend.emit_run("recommandations_parcelle", "SUCCESS", "3 cultures comparées")
    assert run["ok"] is True
    dataset = backend.get_dataset("recommandations_parcelle")
    assert dataset["customProperties"]["last_run_status"] == "SUCCESS"

    incident = backend.create_incident("hubeau_hydrometrie", "Station HS", "impact aval")
    assert incident["ok"] is True
    incidents = backend.list_incidents()
    assert any(i["urn"] == incident["incident_urn"] and i["status"] == "ACTIVE" for i in incidents)

    resolved = backend.resolve_incident(incident["incident_urn"])
    assert resolved["ok"] is True
    incidents = backend.list_incidents()
    assert any(i["urn"] == incident["incident_urn"] and i["status"] == "RESOLVED" for i in incidents)


def test_mode_reel_dataset_inconnu(monkeypatch, gms_url):
    backend = _real(monkeypatch, gms_url)
    assert backend.get_dataset("inconnu") is None
    assert backend.get_lineage("inconnu") is None
    assert backend.emit_run("inconnu", "SUCCESS", "x")["ok"] is False
    assert backend.create_incident("inconnu", "t", "d")["ok"] is False


def test_mode_demo_sans_gms_configure(monkeypatch):
    monkeypatch.delenv("DATAHUB_GMS_URL", raising=False)
    backend = mcp_server._backend()
    datasets = backend.list_datasets()
    assert len(datasets) == 11
    assert any(d["name"] == "hubeau_hydrometrie" for d in datasets)
