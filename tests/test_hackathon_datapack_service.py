"""Tests du service datapacks hackathon (services/hackathon_datapack_service.py).

Comme code_generation_service, ce service appelait client.search_entities /
client.get_entity avant qu'ils n'existent sur DataHubClient — il plantait dès
`discover_datapack_datasets`. On simule le SDK acryl-datahub sous-jacent pour
vérifier la découverte, la détection d'anomalies et le lineage cross-plateforme.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from services.datahub_client import DataHubClient
from services.hackathon_datapack_service import HackathonDatapackService

FRESH_URN = "urn:li:dataset:(urn:li:dataPlatform:postgres,public.trips_fresh,PROD)"
STALE_URN = "urn:li:dataset:(urn:li:dataPlatform:postgres,public.trips_stale,PROD)"

DATASET_ASPECTS = {
    FRESH_URN: {
        "datasetProperties": {"name": "trips_fresh", "customProperties": {"last_updated": "2026-08-06", "freshness_sla_days": "1"}},
        "schemaMetadata": {"fields": [{"fieldPath": "id"}]},
        "status": {"removed": False},
        "upstreamLineage": {"upstreams": [{"dataset": "urn:li:dataset:(urn:li:dataPlatform:postgres,public.raw,PROD)"}]},
    },
    STALE_URN: {
        "datasetProperties": {"name": "trips_stale", "customProperties": {"last_updated": "2020-01-01", "freshness_sla_days": "1"}},
        "schemaMetadata": {"fields": []},
        "status": {"removed": False},
        "upstreamLineage": {"upstreams": []},
    },
}


def _fake_client() -> DataHubClient:
    client = DataHubClient(gms_url="http://fake-gms:8080", token="")
    fake_graph = MagicMock()

    # side_effect (pas return_value) : chaque appel doit renvoyer un itérateur
    # frais — generate_datapack_report interroge la découverte plusieurs fois.
    fake_graph.get_urns_by_filter.side_effect = lambda **kwargs: iter([FRESH_URN, STALE_URN])

    def get_entities_v2(entity_name, urns, aspects=None):
        urn = urns[0]
        data = DATASET_ASPECTS.get(urn, {})
        wanted = aspects or list(data.keys())
        return {urn: {name: {"value": data[name]} for name in wanted if name in data}}

    fake_graph.get_entities_v2.side_effect = get_entities_v2
    client._sdk_graph = fake_graph
    return client


def test_discover_datapack_datasets_utilise_le_client_reel():
    service = HackathonDatapackService(_fake_client())

    datasets = service.discover_datapack_datasets("nyc-taxi")

    assert {d["urn"] for d in datasets} == {FRESH_URN, STALE_URN}


def test_detect_anomalies_signale_la_source_perimee():
    service = HackathonDatapackService(_fake_client())

    anomalies = service.detect_anomalies("nyc-taxi")

    freshness = [a for a in anomalies if a["type"] == "freshness_breach"]
    assert len(freshness) == 1
    assert freshness[0]["dataset_name"] == "trips_stale"
    assert freshness[0]["severity"] == "critical"


def test_detect_anomalies_sans_client_connecte_ne_plante_pas():
    service = HackathonDatapackService(DataHubClient(gms_url="", token=""))
    assert service.detect_anomalies("nyc-taxi") == []


def test_generate_datapack_report_ecrit_un_fichier(tmp_path):
    service = HackathonDatapackService(_fake_client())

    output_file = service.generate_datapack_report("nyc-taxi", tmp_path)

    assert output_file.exists()
    import json

    report = json.loads(output_file.read_text())
    assert report["summary"]["total_datasets"] == 2
    assert report["summary"]["anomalies_found"] == 1
