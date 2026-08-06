"""Construit la vue d'audit experte depuis un résultat O1."""

from __future__ import annotations

from typing import Any

from .data_quality_service import build_quality_certificate
from .provenance_service import short_name

SCORE_MAP = {"elevee": 100, "élevée": 100, "moyenne": 65, "faible": 30, "insuffisante": 0}


def build_expert_report(result: dict[str, Any]) -> dict[str, Any]:
    certificate = build_quality_certificate(result)
    attempts = result.get("resolution_log", [])
    collected = [{"Donnée": a["field"], "Source": a["source"], "État": a["status"]} for a in attempts if "utilisée" in a.get("status", "")]
    for source in result.get("provenance", {}).get("datasets_amont", []):
        collected.append({"Donnée": short_name(source["urn"]), "Source": source["urn"], "État": f'{source.get("niveau_de_preuve", "inconnu")} · {source.get("last_updated", "date absente")}'})
    failures = [{"Donnée": a["field"], "Source essayée": a["source"], "Cause": a["status"]} for a in attempts if "échec" in a.get("status", "") or "aucune" in a.get("status", "")]
    models = [
        {"Modèle": "Degrés-jours", "Rôle": "Dater les stades", "Type": "déterministe", "Version": "M1"},
        {"Modèle": "Bilan hydrique", "Rôle": "Estimer l'eau manquante", "Type": "déterministe", "Version": "M1"},
        {"Modèle": "Recouvrement", "Rôle": "Compter les jours à risque", "Type": "intersection de dates", "Version": "O1"},
        {"Modèle": "Marge brute", "Rôle": "Produit − charges − eau − risque", "Type": "déterministe", "Version": "O1"},
        {"Modèle": "Interpolation IDW", "Rôle": "Compléter le sol en dernier recours", "Type": "spatial", "Version": "1.0"},
        {"Modèle": result.get("provenance", {}).get("modele", {}).get("urn", "GR4J"), "Rôle": "Contexte hydrologique", "Type": "hydrologique", "Version": result.get("provenance", {}).get("modele", {}).get("version", "inconnue")},
    ]
    scores = [{"Dimension": item["name"], "Niveau": item["level"], "Score / 100": SCORE_MAP[item["level"]], "Preuve": item["evidence"]} for item in certificate["checks"]]
    overall = round(sum(row["Score / 100"] for row in scores) / len(scores)) if scores else 0
    return {"collected": collected, "failures": failures, "models": models, "scores": scores, "overall_score": overall, "certificate": certificate}
