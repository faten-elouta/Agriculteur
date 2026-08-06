"""Tests du serveur GMS-compatible : contrat vérifié par le vrai DataHubClient en HTTP."""

from __future__ import annotations

import socket
import threading
import time

import pytest

from services.datahub_client import DataHubClient

HYDRO = "urn:li:dataset:(urn:li:dataPlatform:duckdb,hubeau_hydrometrie,PROD)"
RECO = "urn:li:dataset:(urn:li:dataPlatform:duckdb,recommandations_parcelle,PROD)"


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


def test_seed_et_health(gms_url):
    client = DataHubClient(gms_url=gms_url, token="")
    assert client.connected() is True


def test_proprietes_seedees(gms_url):
    client = DataHubClient(gms_url=gms_url, token="")
    properties = client.dataset_properties(HYDRO)
    assert properties is not None
    assert properties["name"] == "hubeau_hydrometrie"
    custom = properties["custom_properties"]
    assert custom["niveau_de_preuve"] == "mesure"
    assert custom["freshness_sla_days"] == "5"
    assert custom["last_updated"]


def test_lineage_amont_aval(gms_url):
    client = DataHubClient(gms_url=gms_url, token="")
    features = "urn:li:dataset:(urn:li:dataPlatform:duckdb,features_bilan_hydrique,PROD)"
    edges = client.dataset_lineage(features)
    assert edges is not None
    upstreams = [e["urn"] for e in edges if e["direction"] == "UPSTREAM"]
    downstreams = [e["urn"] for e in edges if e["direction"] == "DOWNSTREAM"]
    assert HYDRO in upstreams
    assert "urn:li:dataset:(urn:li:dataPlatform:duckdb,scenarios_cultures,PROD)" in downstreams


def test_upsert_run_et_relecture(gms_url):
    client = DataHubClient(gms_url=gms_url, token="")
    assert client.emit_run(RECO, "SUCCESS", "3 cultures comparées") is True
    properties = client.dataset_properties(RECO)
    custom = properties["custom_properties"]
    assert custom["last_run_status"] == "SUCCESS"
    assert custom["last_run_summary"] == "3 cultures comparées"
    assert "last_run_at" in custom
    assert custom["niveau_de_preuve"]  # propriétés d'origine conservées


def test_incident_create_resolve(gms_url):
    client = DataHubClient(gms_url=gms_url, token="")
    urn = client.create_incident("Panne de station", "impact lineage", HYDRO)
    assert urn and urn.startswith("urn:li:incident:")
    assert client.resolve_incident(urn) is True


def test_freshness_summary(gms_url):
    client = DataHubClient(gms_url=gms_url, token="")
    summary = client.freshness_summary([HYDRO, RECO])
    assert summary["sources"][HYDRO]["status"] in ("ok", "stale")
    assert summary["sources"][RECO]["status"] in ("ok", "stale")
    assert summary["ok"] + summary["stale"] == 2
