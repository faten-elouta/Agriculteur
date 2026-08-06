"""Rapport de comparaison : archive JSON dans reports/ et export CSV téléchargeable."""

from __future__ import annotations

import csv
import io
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9_-]+")


def build_comparison_report(result: dict[str, Any], simulated_by_culture: dict[str, dict[str, float]] | None = None) -> dict[str, Any]:
    """Assemble un rapport archivable à partir d'un résultat calculé, avec les chiffres simulés éventuels."""
    simulated_by_culture = simulated_by_culture or {}
    cultures = []
    for crop in result["cultures"]:
        entry = {
            "culture": crop["culture"],
            "rang": crop["rang"],
            "etat": crop["etat"],
            "recouvrement_avec_tension_j": crop["recouvrement_avec_tension_j"],
            "besoin_irrigation_mm": crop["besoin_irrigation_mm"],
            "marge_scenario_eur_ha": crop["marge_brute_eur_ha"],
            "decomposition_marge": crop["decomposition_marge"],
        }
        simulation = simulated_by_culture.get(crop["culture"])
        if simulation is not None:
            entry["marge_simulee_eur_ha"] = simulation["marge_eur_ha"]
        cultures.append(entry)
    return {
        "genere_le": result["genere_le"],
        "parcelle_id": result["parcelle_id"],
        "commune": result["commune"],
        "surface_ha": result["surface_ha"],
        "sol": result["sol"],
        "date_semis": result["date_semis"],
        "horizon_mois": result["horizon_mois"],
        "confiance": result["confiance"],
        "cultures": cultures,
        "provenance": result["provenance"],
    }


def save_report(report: dict[str, Any], reports_dir: str | Path, today: date) -> Path:
    """Archive le rapport en JSON, à la manière des rapports d'impact de la Sentinelle."""
    out_dir = Path(reports_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_parcelle = _UNSAFE_CHARS.sub("_", str(report["parcelle_id"]))
    path = out_dir / f"comparaison_{today.isoformat()}_{safe_parcelle}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def report_to_csv(report: dict[str, Any]) -> str:
    """Sérialise le rapport en CSV, une ligne par culture."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Culture", "Rang", "État", "Jours à risque", "Besoin irrigation (mm)", "Marge scénario (€/ha)", "Marge simulée (€/ha)"])
    for crop in report["cultures"]:
        writer.writerow(
            [
                crop["culture"],
                crop["rang"],
                crop["etat"],
                crop["recouvrement_avec_tension_j"],
                crop["besoin_irrigation_mm"],
                crop["marge_scenario_eur_ha"],
                crop.get("marge_simulee_eur_ha", ""),
            ]
        )
    return buffer.getvalue()
