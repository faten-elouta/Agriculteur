#!/usr/bin/env python3
"""Génère des artefacts de code à partir du graphe de contexte réel Terroir.

`CodeGenerationService.discover_datasets()` interroge un DataHub GMS en direct
via le SDK (voir `services/code_generation_service.py`). Ce script exécute la
même logique de génération (`generate_ingestion_recipe`, `generate_transformation_sql`,
`generate_airflow_dag`) mais construit les `DatasetSchema` depuis `fixtures/graph.json`
— le graphe réellement ingéré par `catalog/ingest_datahub.py` et servi par
`gms/main.py` — pour produire des exemples inspectables sans instance DataHub à
faire tourner.

Les 11 datasets, leur lineage et leurs licences/SLA sont ceux du projet ; le
schéma de colonnes n'est pas suivi dans ce graphe et n'est donc pas inventé
(`fields=[]`).

Usage :
    .venv/bin/python examples/generate_from_fixture.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.code_generation_service import CodeGenerationService, DatasetSchema  # noqa: E402
from services.datahub_client import DataHubClient  # noqa: E402


def _short_name(urn: str) -> str:
    return urn.split(",")[1]


def load_dataset_schemas(service: CodeGenerationService) -> list[DatasetSchema]:
    graph = json.loads((ROOT / "fixtures" / "graph.json").read_text(encoding="utf-8"))
    lineage: dict[str, list[str]] = graph["lineage"]
    upstream_of: dict[str, list[str]] = {urn: [] for urn in graph["datasets"]}
    for urn, targets in lineage.items():
        for target in targets:
            upstream_of.setdefault(target, []).append(urn)

    schemas = []
    for urn, props in graph["datasets"].items():
        schemas.append(
            DatasetSchema(
                urn=urn,
                name=_short_name(urn),
                platform=service._extract_platform(urn),
                description="Source du graphe de contexte Terroir Context Agents.",
                fields=[],
                upstream_urns=upstream_of.get(urn, []),
                downstream_urns=lineage.get(urn, []),
                custom_properties={k: str(v) for k, v in props.items()},
                tags=[],
                glossary_terms=[],
            )
        )
    return schemas


def main() -> None:
    output_dir = ROOT / "examples" / "generated"
    # Client désactivé : la génération elle-même ne fait aucun appel réseau,
    # `load_dataset_schemas` fournit déjà le lineage lu depuis le fixture réel.
    service = CodeGenerationService(DataHubClient(gms_url="", token=""))
    datasets = load_dataset_schemas(service)

    for ds in datasets:
        service.generate_ingestion_recipe(ds, output_dir / "ingestion")
        service.generate_transformation_sql(ds, output_dir / "transformations")

    dag_path = service.generate_airflow_dag(datasets, output_dir / "dags")

    print(f"{len(datasets)} datasets du graphe Terroir -> {output_dir}")
    print(f"DAG : {dag_path}")


if __name__ == "__main__":
    main()
