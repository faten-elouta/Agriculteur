"""Tests du client DataHub contre un faux GMS local (http.server, aucune dépendance)."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import MagicMock
from urllib.parse import unquote, urlparse

import pytest

from services.datahub_client import DataHubClient

HYDRO_URN = "urn:li:dataset:(urn:li:dataPlatform:duckdb,hubeau_hydrometrie,PROD)"
RECO_URN = "urn:li:dataset:(urn:li:dataPlatform:duckdb,recommandations_parcelle,PROD)"


class FakeGMS:
    """Mini GMS : /health, propriétés de dataset, lineage, incidents, upserts."""

    def __init__(self) -> None:
        self.received: list[dict] = []
        self.properties: dict[str, dict] = {}
        self.relationships: dict[str, list[dict]] = {}
        self.incidents: list[dict] = []
        self._server = HTTPServer(("127.0.0.1", 0), self._make_handler())
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def url(self) -> str:
        host, port = self._server.server_address
        return f"http://{host}:{port}"

    def start(self) -> "FakeGMS":
        self._thread.start()
        return self

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()

    def _make_handler(self):
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _send(self, code: int, payload: dict) -> None:
                body = json.dumps(payload).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _body(self) -> dict:
                length = int(self.headers.get("Content-Length", 0))
                return json.loads(self.rfile.read(length) or b"{}")

            def do_GET(self):
                path = urlparse(self.path).path
                if path == "/health":
                    self._send(200, {"status": "ok"})
                    return
                if path.startswith("/openapi/v3/entity/dataset/") and path.endswith("/lineage"):
                    urn = unquote(path.split("/openapi/v3/entity/dataset/", 1)[1].removesuffix("/lineage"))
                    self._send(200, {"results": [{"urn": urn, "relationships": fake.relationships.get(urn, [])}]})
                    return
                if path.startswith("/openapi/v3/entity/dataset/"):
                    urn = unquote(path.split("/openapi/v3/entity/dataset/", 1)[1])
                    if urn in fake.properties:
                        self._send(200, {"results": [{"urn": urn, "aspects": {"datasetProperties": fake.properties[urn]}}]})
                    else:
                        self._send(200, {"results": []})
                    return
                self._send(404, {"error": "not found"})

            def do_POST(self):
                path = urlparse(self.path).path
                payload = self._body()
                fake.received.append({"path": path, "body": payload})
                if path == "/openapi/v3/entity/dataset":
                    aspects = payload.get("aspects", {})
                    props = aspects.get("datasetProperties", {})
                    fake.properties[payload["urn"]] = props
                    self._send(201, {"results": [{"urn": payload["urn"]}]})
                    return
                if path == "/openapi/v3/entity/incident":
                    urn = f"urn:li:incident:(simulated,{len(fake.incidents) + 1})"
                    fake.incidents.append({"urn": urn, **payload})
                    self._send(201, {"results": [{"urn": urn}]})
                    return
                if path.startswith("/openapi/v3/entity/incident/"):
                    urn = unquote(path.split("/openapi/v3/entity/incident/", 1)[1])
                    fake.incidents.append({"urn": urn, **payload})
                    self._send(200, {"results": [{"urn": urn}]})
                    return
                self._send(404, {"error": "not found"})

        return Handler


@pytest.fixture()
def fake_gms():
    server = FakeGMS().start()
    server.properties[HYDRO_URN] = {
        "name": "hubeau_hydrometrie",
        "customProperties": {"last_updated": "2026-08-04", "freshness_sla_days": "5"},
    }
    server.relationships[HYDRO_URN] = [
        {"entity": RECO_URN, "type": "DOWNSTREAM"},
    ]
    yield server
    server.stop()


def test_repli_local_sans_gms():
    client = DataHubClient(gms_url="", token="")
    assert client.enabled is False
    assert client.connected() is False
    assert client.dataset_properties(HYDRO_URN) is None
    assert client.dataset_lineage(HYDRO_URN) is None
    assert client.upsert_dataset_properties(HYDRO_URN, {"a": "b"}) is False
    assert client.create_incident("t", "d", HYDRO_URN) is None
    assert client.resolve_incident("urn:li:incident:(x,1)") is False
    assert client.search_entities() == []
    assert client.get_entity(HYDRO_URN) is None


def test_connected(fake_gms):
    client = DataHubClient(gms_url=fake_gms.url, token="secret")
    assert client.connected() is True


def test_gms_injoignable():
    client = DataHubClient(gms_url="http://127.0.0.1:1", token="")
    assert client.connected() is False
    assert client.dataset_properties(HYDRO_URN) is None


def test_dataset_properties(fake_gms):
    client = DataHubClient(gms_url=fake_gms.url, token="")
    properties = client.dataset_properties(HYDRO_URN)
    assert properties is not None
    assert properties["name"] == "hubeau_hydrometrie"
    assert properties["custom_properties"]["freshness_sla_days"] == "5"


def test_dataset_properties_inconnu(fake_gms):
    client = DataHubClient(gms_url=fake_gms.url, token="")
    assert client.dataset_properties("urn:li:dataset:(urn:li:dataPlatform:duckdb,inconnu,PROD)") is None


def test_dataset_lineage(fake_gms):
    client = DataHubClient(gms_url=fake_gms.url, token="")
    edges = client.dataset_lineage(HYDRO_URN)
    assert edges == [{"urn": RECO_URN, "direction": "DOWNSTREAM"}]


def test_upsert_dataset_properties(fake_gms):
    client = DataHubClient(gms_url=fake_gms.url, token="")
    assert client.upsert_dataset_properties(RECO_URN, {"last_run_status": "SUCCESS"}, "desc") is True
    stored = fake_gms.properties[RECO_URN]
    assert stored["customProperties"]["last_run_status"] == "SUCCESS"
    assert stored["description"] == "desc"


def test_emit_run(fake_gms):
    client = DataHubClient(gms_url=fake_gms.url, token="")
    assert client.emit_run(RECO_URN, "SUCCESS", "2 cultures comparées") is True
    stored = fake_gms.properties[RECO_URN]["customProperties"]
    assert stored["last_run_status"] == "SUCCESS"
    assert stored["last_run_summary"] == "2 cultures comparées"
    assert "last_run_at" in stored


def test_incident_create_and_resolve(fake_gms):
    client = DataHubClient(gms_url=fake_gms.url, token="")
    urn = client.create_incident("Panne de station", "impact", HYDRO_URN)
    assert urn and urn.startswith("urn:li:incident:")
    assert fake_gms.incidents[-1]["entityUrns"] == [HYDRO_URN]
    assert client.resolve_incident(urn) is True
    assert fake_gms.incidents[-1]["aspects"]["incidentInfo"]["status"]["state"] == "RESOLVED"


def test_freshness_summary(fake_gms):
    client = DataHubClient(gms_url=fake_gms.url, token="")
    fake_gms.properties["urn:li:dataset:(urn:li:dataPlatform:duckdb,ancienne_source,PROD)"] = {
        "name": "ancienne_source",
        "customProperties": {"last_updated": "2020-01-01", "freshness_sla_days": "5"},
    }
    summary = client.freshness_summary([HYDRO_URN, RECO_URN, "urn:li:dataset:(urn:li:dataPlatform:duckdb,ancienne_source,PROD)"])
    assert summary["sources"][HYDRO_URN]["status"] == "ok"
    assert summary["sources"][RECO_URN]["status"] == "unknown"
    assert summary["sources"]["urn:li:dataset:(urn:li:dataPlatform:duckdb,ancienne_source,PROD)"]["status"] == "stale"
    assert summary["ok"] == 1
    assert summary["stale"] == 1
    assert summary["unknown"] == 1


# ---------------------------------------------------------------------------
# search_entities / get_entity : passent par le SDK acryl-datahub (get_urns_by_filter,
# get_entities_v2), pas par le sous-ensemble REST maison. On simule le SDK plutôt que
# le réseau — c'est la même frontière que agents.sentinelle.LiveBackend teste ailleurs.
# ---------------------------------------------------------------------------

def _client_with_fake_graph(fake_graph: MagicMock) -> DataHubClient:
    client = DataHubClient(gms_url="http://fake-gms:8080", token="")
    client._sdk_graph = fake_graph
    return client


def test_search_entities_appelle_get_urns_by_filter():
    fake_graph = MagicMock()
    fake_graph.get_urns_by_filter.return_value = iter([HYDRO_URN, RECO_URN])
    client = _client_with_fake_graph(fake_graph)

    results = client.search_entities(query="*", entity_type="DATASET", platform="duckdb", count=10)

    assert results == [{"urn": HYDRO_URN}, {"urn": RECO_URN}]
    fake_graph.get_urns_by_filter.assert_called_once_with(entity_types=["dataset"], platform="duckdb", query="*")


def test_search_entities_tronque_a_count():
    fake_graph = MagicMock()
    fake_graph.get_urns_by_filter.return_value = iter([HYDRO_URN, RECO_URN, "urn:li:dataset:(x,y,PROD)"])
    client = _client_with_fake_graph(fake_graph)

    assert client.search_entities(count=2) == [{"urn": HYDRO_URN}, {"urn": RECO_URN}]


def test_search_entities_erreur_sdk_renvoie_liste_vide():
    fake_graph = MagicMock()
    fake_graph.get_urns_by_filter.side_effect = RuntimeError("gms down")
    client = _client_with_fake_graph(fake_graph)

    assert client.search_entities() == []


def test_get_entity_deballe_les_aspects():
    fake_graph = MagicMock()
    fake_graph.get_entities_v2.return_value = {
        HYDRO_URN: {
            "datasetProperties": {"value": {"name": "hubeau_hydrometrie", "customProperties": {"owner": "data-team"}}},
            "status": {"value": {"removed": False}},
        }
    }
    client = _client_with_fake_graph(fake_graph)

    entity = client.get_entity(HYDRO_URN, aspects=["datasetProperties", "status"])

    assert entity == {
        "datasetProperties": {"name": "hubeau_hydrometrie", "customProperties": {"owner": "data-team"}},
        "status": {"removed": False},
    }
    fake_graph.get_entities_v2.assert_called_once_with("dataset", [HYDRO_URN], aspects=["datasetProperties", "status"])


def test_get_entity_urn_absente():
    fake_graph = MagicMock()
    fake_graph.get_entities_v2.return_value = {}
    client = _client_with_fake_graph(fake_graph)

    assert client.get_entity(HYDRO_URN) is None


def test_get_entity_erreur_sdk_renvoie_none():
    fake_graph = MagicMock()
    fake_graph.get_entities_v2.side_effect = RuntimeError("gms down")
    client = _client_with_fake_graph(fake_graph)

    assert client.get_entity(HYDRO_URN) is None
