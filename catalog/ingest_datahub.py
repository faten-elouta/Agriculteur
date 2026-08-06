"""Ingestion du graphe de contexte « Terroir Context Agents » dans DataHub.

Lit `fixtures/graph.json` (déjà au format URN DataHub) et écrit, dans le GMS
de DataHub, les datasets (propriétés + licence + SLA de fraîcheur) puis le
lineage (aspect `upstreamLineage`), avec un modèle ML `recommandations_parcelle`.

Usage :
    .venv/bin/python catalog/ingest_datahub.py --dry-run          # affiche les payloads
    DATAHUB_GMS_URL=http://localhost:8080 .venv/bin/python catalog/ingest_datahub.py

En mode `--dry-run`, aucun appel réseau n'est fait ; chaque payload est imprimé
en JSON — c'est aussi ce que montre la démo.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.datahub_client import DataHubClient  # noqa: E402
from services.provenance_service import short_name  # noqa: E402


def build_dataset_payloads(graph: dict) -> list[dict]:
    """Payloads upsert par dataset (propriétés issues de fixtures/graph.json)."""
    payloads = []
    for urn, props in graph["datasets"].items():
        custom = {
            "niveau_de_preuve": str(props.get("niveau_de_preuve", "")),
            "freshness_sla_days": str(props.get("freshness_sla_days", "")),
            "last_updated": str(props.get("last_updated", "")),
            "spatial_coverage": str(props.get("spatial_coverage", "")),
            "licence": str(props.get("licence", "")),
            "redistribuable": str(props.get("redistribuable", "")),
        }
        payloads.append(
            {
                "urn": urn,
                "aspects": {
                    "datasetProperties": {
                        "name": short_name(urn),
                        "description": "Source de contexte Terroir Context Agents — licence et SLA déclarés par l'ingestion.",
                        "customProperties": custom,
                    }
                },
            }
        )
    return payloads


def build_lineage_payloads(graph: dict) -> list[dict]:
    """Payloads `upstreamLineage` : pour chaque dataset aval, ses sources amont."""
    payloads = []
    for upstream_urn, downstream_urns in graph["lineage"].items():
        for downstream_urn in downstream_urns:
            payloads.append(
                {
                    "urn": downstream_urn,
                    "aspects": {
                        "upstreamLineage": {"upstreams": [{"dataset": upstream_urn}]},
                    },
                }
            )
    return payloads


def build_model_payload(graph: dict) -> dict | None:
    """Modèle ML `recommandations_parcelle` relié à ses datasets d'entrée (sources feuilles)."""
    input_urns = [urn for urn in graph["datasets"] if urn not in {t for v in graph["lineage"].values() for t in v}]
    if not input_urns:
        return None
    return {
        "urn": "urn:li:mlModel:(urn:li:dataPlatform:duckdb,recommandations_parcelle,PROD)",
        "aspects": {
            "mlModelProperties": {
                "name": "recommandations_parcelle",
                "description": "Modèle de recommandation de culture avant semis — produit par Terroir Context Agents à partir des sources de contexte (eau, sol, climat, économie, parcelle).",
            },
            "upstreamLineage": {"upstreams": [{"dataset": urn} for urn in sorted(input_urns)]},
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--graph", default=str(ROOT / "fixtures" / "graph.json"))
    parser.add_argument("--dry-run", action="store_true", help="affiche les payloads sans appel réseau")
    parser.add_argument("--with-model", action="store_true", help="ingère aussi le modèle ML recommandations_parcelle")
    args = parser.parse_args()

    graph = json.loads(Path(args.graph).read_text(encoding="utf-8"))
    dataset_payloads = build_dataset_payloads(graph)
    lineage_payloads = build_lineage_payloads(graph)
    model_payload = build_model_payload(graph) if args.with_model else None

    if args.dry_run:
        print(f"# datasets : {len(dataset_payloads)}")
        for payload in dataset_payloads:
            print(json.dumps(payload, ensure_ascii=False, indent=1))
        print(f"# lineage  : {len(lineage_payloads)}")
        for payload in lineage_payloads:
            print(json.dumps(payload, ensure_ascii=False, indent=1))
        if model_payload:
            print("# modele   : 1")
            print(json.dumps(model_payload, ensure_ascii=False, indent=1))
        return

    client = DataHubClient()
    if not client.enabled:
        print("DATAHUB_GMS_URL non défini — rien à faire. Passez --dry-run pour voir les payloads.")
        sys.exit(1)
    if not client.connected():
        print(f"GMS injoignable : {client.gms_url} — vérifiez DATAHUB_GMS_URL et DATAHUB_TOKEN.")
        sys.exit(1)

    ok = 0
    for payload in dataset_payloads:
        if client.upsert_dataset_properties(payload["urn"], payload["aspects"]["datasetProperties"]["customProperties"], payload["aspects"]["datasetProperties"]["description"]):
            ok += 1
    for payload in lineage_payloads:
        if client._request("POST", "/openapi/v3/entity/dataset", payload) is not None:
            ok += 1
    if model_payload and client._request("POST", "/openapi/v3/entity/mlModel", model_payload) is not None:
        ok += 1
    print(f"Ingestion terminée : {ok}/{len(dataset_payloads) + len(lineage_payloads) + (1 if model_payload else 0)} entités écrites dans {client.gms_url}.")


if __name__ == "__main__":
    main()
