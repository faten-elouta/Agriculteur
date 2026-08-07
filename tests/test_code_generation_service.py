"""Tests du service de génération de code (services/code_generation_service.py).

Avant cette suite, ce service appelait DataHubClient.search_entities / get_entity,
deux méthodes qui n'existaient pas encore sur le client (AttributeError dès le
premier appel). On simule ici le SDK acryl-datahub sous-jacent — la même frontière
que test_datahub_client.py — pour vérifier que la génération produit de vrais
artefacts à partir d'un graphe DataHub.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from services.code_generation_service import CodeGenerationService
from services.datahub_client import DataHubClient

ORDERS_URN = "urn:li:dataset:(urn:li:dataPlatform:postgres,public.orders,PROD)"
RAW_ORDERS_URN = "urn:li:dataset:(urn:li:dataPlatform:postgres,public.raw_orders,PROD)"
MODEL_URN = "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model,PROD)"

DATASET_ASPECTS = {
    ORDERS_URN: {
        "datasetProperties": {
            "name": "orders",
            "description": "Commandes agrégées",
            "customProperties": {"owner": "data-team", "database": "shop", "schema": "public"},
        },
        "schemaMetadata": {"fields": [{"fieldPath": "id", "type": {"type": {}}, "nativeDataType": "int", "description": ""}]},
        "globalTags": {"tags": [{"tag": "urn:li:tag:pii"}]},
        "glossaryTerms": {"terms": [{"urn": "urn:li:glossaryTerm:Revenue"}]},
        "upstreamLineage": {"upstreams": [{"dataset": RAW_ORDERS_URN}]},
        "ownership": {"owners": [{"owner": "urn:li:corpuser:alice"}]},
    },
    RAW_ORDERS_URN: {
        "schemaMetadata": {"fields": [{"fieldPath": "raw_id", "type": {"type": {}}, "nativeDataType": "text", "description": ""}]},
    },
}

MODEL_ASPECTS = {
    MODEL_URN: {
        "mlModelProperties": {"name": "churn_model", "description": "Prédit le churn", "version": {"versionTag": "2.0.0"}, "customProperties": {}},
        "mlModelGroups": {},
        "upstreamLineage": {"upstreams": [{"dataset": ORDERS_URN}]},
    }
}


def _fake_client() -> DataHubClient:
    client = DataHubClient(gms_url="http://fake-gms:8080", token="")
    fake_graph = MagicMock()

    def get_urns_by_filter(*, entity_types=None, platform=None, query=None):
        if entity_types == ["dataset"]:
            return iter([ORDERS_URN])
        if entity_types == ["mlmodel"]:
            return iter([MODEL_URN])
        return iter([])

    def get_entities_v2(entity_name, urns, aspects=None):
        urn = urns[0]
        pool = DATASET_ASPECTS if entity_name == "dataset" else MODEL_ASPECTS
        data = pool.get(urn, {})
        wanted = aspects or list(data.keys())
        return {urn: {name: {"value": data[name]} for name in wanted if name in data}}

    fake_graph.get_urns_by_filter.side_effect = get_urns_by_filter
    fake_graph.get_entities_v2.side_effect = get_entities_v2
    client._sdk_graph = fake_graph
    return client


def test_discover_datasets_lit_le_schema_et_le_lineage():
    service = CodeGenerationService(_fake_client())

    datasets = service.discover_datasets()

    assert len(datasets) == 1
    ds = datasets[0]
    assert ds.name == "orders"
    assert ds.platform == "postgres"
    assert ds.fields[0]["name"] == "id"
    assert ds.upstream_urns == [RAW_ORDERS_URN]
    assert ds.tags == ["pii"]
    assert ds.glossary_terms == ["Revenue"]
    assert ds.custom_properties["owner"] == "data-team"


def test_discover_datasets_sans_client_connecte_renvoie_liste_vide():
    service = CodeGenerationService(DataHubClient(gms_url="", token=""))
    assert service.discover_datasets() == []


def test_discover_ml_models_resout_le_lineage_vers_les_features():
    service = CodeGenerationService(_fake_client())

    models = service.discover_ml_models()

    assert len(models) == 1
    assert models[0].name == "churn_model"
    assert models[0].version == "2.0.0"
    assert models[0].training_data_urns == [ORDERS_URN]


def test_generate_all_artifacts_ecrit_des_fichiers_reels(tmp_path):
    service = CodeGenerationService(_fake_client())

    results = service.generate_all_artifacts(tmp_path)

    assert len(results["ingestion_recipes"]) == 1
    assert results["ingestion_recipes"][0].exists()
    recipe_text = results["ingestion_recipes"][0].read_text()
    assert "postgres" in recipe_text
    assert "data-team" in recipe_text

    assert len(results["transformations"]) == 1
    sql_text = results["transformations"][0].read_text()
    assert "orders" in sql_text

    assert len(results["dags"]) == 1
    dag_text = results["dags"][0].read_text()
    assert "ingest_orders" in dag_text
    # Régression : le générateur interpolait `ds.name` avec des accolades doubles,
    # ce qui produisait un DAG où `ds` n'existe pas à l'exécution (NameError dès
    # le premier run Airflow). Le nom doit être écrit en dur dans le fichier généré.
    assert 'print("Ingesting orders")' in dag_text
    assert "print(f\"Ingesting" not in dag_text

    assert len(results["ml"]) == 1
    training_text = results["ml"][0].read_text()
    assert "churn_model" in training_text
