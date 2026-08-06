#!/usr/bin/env python3
"""Démo autonome contre le graphe de contexte DataHub public de Terroir Context.

Ce script tourne avec la bibliothèque standard uniquement (aucun pip install) :
il interroge le serveur GMS-compatible hébergé sur Render, lit les propriétés
et le lineage des 11 datasets, trace un run, crée/résout un incident et résume
la fraîcheur des sources.

Usage :
    python examples/gms_demo.py

Le GMS public par défaut est https://terroir-context-gms.onrender.com ; on peut
le remplacer avec la variable d'environnement DATAHUB_GMS_URL.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.datahub_client import DataHubClient  # noqa: E402

GMS_URL = os.getenv("DATAHUB_GMS_URL", "https://terroir-context-gms.onrender.com")

DATASETS = [
    ("climat_journalier", "Historique climatique quotidien (températures, pluie, ETP)."),
    ("sol_rrp", "Référentiel régional pédologique : types de sol et réserve utile."),
    ("hubeau_hydrometrie", "Piézomètres et débits des rivières (hub.eaufrance.fr)."),
    ("hubeau_onde", "Observations nationales des étages (hub.eaufrance.fr)."),
    ("hubeau_piezometrie", "Niveaux piézométriques (hub.eaufrance.fr)."),
    ("prevision_saisonniere", "Prévisions saisonnières (pluie, ETP, tension)."),
    ("parcelles", "Registre parcellaire graphique : emprise et assolement."),
    ("ref_agro_economique", "Marges brutes, coûts de production et prix par culture."),
    ("scenarios_cultures", "Scénarios de stress hydrique par stade cultural."),
    ("recommandations_parcelle", "Recommandation finale : culture chiffrée la plus sûre."),
    ("features_bilan_hydrique", "Indicateurs agrégés par parcelle (tension, besoin d'eau)."),
]


def dataset_urn(name: str) -> str:
    return f"urn:li:dataset:(urn:li:dataPlatform:duckdb,{name},PROD)"


def main() -> int:
    client = DataHubClient(gms_url=GMS_URL)
    print(f"GMS : {client.gms_url}")
    print(f"Connexion : {'OK' if client.connected() else 'ECHEC'}\n")
    if not client.enabled or not client.connected():
        print("Le GMS ne répond pas.")
        return 1

    print("=" * 72)
    print("1. Les 11 datasets du graphe de contexte")
    print("=" * 72)
    for name, description in DATASETS:
        properties = client.dataset_properties(dataset_urn(name))
        if properties is None:
            print(f"  {name:<26} introuvable")
            continue
        custom = properties.get("custom_properties") or {}
        freshness = custom.get("last_updated", "?")
        print(f"  {name:<26} fraîcheur: {freshness}  ({description[:40]})")

    print()
    print("=" * 72)
    print("2. Lineage : d'où viennent les indicateurs bilan hydrique ?")
    print("=" * 72)
    edges = client.dataset_lineage(dataset_urn("features_bilan_hydrique")) or []
    for edge in edges:
        target = edge["urn"].split(",")[1] if "," in edge["urn"] else edge["urn"]
        print(f"  [{edge['direction']:<10}] {target}")

    print()
    print("=" * 72)
    print("3. Écriture dans le graphe : run + incident")
    print("=" * 72)
    ran = client.emit_run(dataset_urn("recommandations_parcelle"), "SUCCESS", "Démo examples/gms_demo.py")
    print(f"  Run tracé sur recommandations_parcelle : {'oui' if ran else 'non'}")
    incident_urn = client.create_incident(
        "Démo : source sol_rrp en dépassement de SLA",
        "Créé depuis examples/gms_demo.py pour montrer le cycle de vie d'un incident.",
        dataset_urn("sol_rrp"),
    )
    print(f"  Incident créé : {incident_urn or 'échec'}")
    if incident_urn:
        resolved = client.resolve_incident(incident_urn)
        print(f"  Incident résolu : {'oui' if resolved else 'non'}")

    print()
    print("=" * 72)
    print("4. Fraîcheur des sources (SLA annoncé vs dernière mise à jour)")
    print("=" * 72)
    summary = client.freshness_summary([dataset_urn(name) for name, _ in DATASETS])
    for urn, info in summary["sources"].items():
        name = urn.split(",")[1] if "," in urn else urn
        if info.get("status") == "unknown":
            print(f"  {name:<26} inconnue")
        else:
            print(f"  {name:<26} {info['status']:<6} maj {info['last_updated']} (SLA {info['sla_days']} j, écart {info['delta_days']} j)")
    print(f"\n  Bilan : {summary['ok']} à jour · {summary['stale']} en dépassement · {summary['unknown']} inconnues")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
