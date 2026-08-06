"""Porte de confiance calculée exclusivement depuis le graphe."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any

from .provenance_service import short_name, upstream_closure, urn_for


@dataclass(frozen=True)
class ConfidenceResult:
    niveau: str
    motifs: list[str]
    fiabilite_prevision: str
    sources: list[dict[str, str]]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_confidence(graph: dict[str, Any], today: date, horizon_months: int) -> ConfidenceResult:
    """Évalue fraîcheur, preuve, couverture, licence et continuité du lineage."""
    reliability = {3: "utile", 6: "faible", 12: "climatologique"}[horizon_months]
    try:
        target = urn_for(graph, "recommandations_parcelle")
    except ValueError as exc:
        return ConfidenceResult("insuffisante", [f"Lineage rompu: {exc}"], reliability, [])
    upstream = upstream_closure(graph, target)
    required_names = {"hubeau_hydrometrie", "hubeau_piezometrie", "hubeau_onde", "climat_journalier", "prevision_saisonniere", "features_bilan_hydrique", "scenarios_cultures"}
    present = {short_name(urn) for urn in upstream | {target}}
    missing = sorted(required_names - present)
    if missing:
        return ConfidenceResult("insuffisante", [f"Lineage rompu: maillons absents: {', '.join(missing)}."], reliability, [])

    sources: list[dict[str, str]] = []
    degraded: list[str] = []
    insufficient: list[str] = []
    for urn in sorted(upstream | {target}):
        props = graph["datasets"].get(urn)
        if not props:
            insufficient.append(f"Lineage rompu vers {short_name(urn)}.")
            continue
        name = short_name(urn)
        last = date.fromisoformat(str(props["last_updated"])[:10])
        sla = int(props["freshness_sla_days"])
        age = max(0, (today - last).days)
        state = "sûr"
        if age > 2 * sla:
            state = "rupture"
            insufficient.append(f"{name}: dernière donnée {last.isoformat()}, âge {age} j, supérieur à 2 × son SLA de {sla} j.")
        elif age > sla:
            state = "vigilance"
            degraded.append(f"{name}: dernière donnée {last.isoformat()}, âge {age} j, au-delà de son SLA de {sla} j.")
        if props["niveau_de_preuve"] == "dire_d_expert":
            state = "vigilance" if state == "sûr" else state
            degraded.append(f"{name} est une source critique de type dire_d_expert.")
        if not str(props["spatial_coverage"]).strip() or not str(props["licence"]).strip():
            insufficient.append(f"{name}: couverture spatiale ou licence absente.")
            state = "rupture"
        sources.append({"urn": urn, "last_updated": last.isoformat(), "niveau_de_preuve": str(props["niveau_de_preuve"]), "etat": state})
    if insufficient:
        return ConfidenceResult("insuffisante", insufficient, reliability, sources)
    if degraded:
        return ConfidenceResult("degradee", degraded, reliability, sources)
    return ConfidenceResult("haute", ["Toutes les sources respectent leur SLA et le lineage est complet."], reliability, sources)
