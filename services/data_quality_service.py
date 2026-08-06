"""Certificat lisible de qualité des données d'une recommandation."""

from __future__ import annotations

from typing import Any


def build_quality_certificate(result: dict[str, Any]) -> dict[str, Any]:
    """Distingue les garanties vérifiées des hypothèses à confirmer."""
    sources = result.get("provenance", {}).get("datasets_amont", [])
    lineage_ok = bool(result.get("provenance", {}).get("chaine_lineage_verifiee"))
    real_parcel = result.get("mode_donnees") == "reel_hybride"
    soil = result.get("soil_resolution") or {}
    soil_method = soil.get("method")
    checks = [
        {"name": "Parcelle", "level": "elevee" if real_parcel else "faible", "evidence": result.get("parcelle_source", "RPG public anonymisé")},
        {"name": "Traçabilité", "level": "elevee" if lineage_ok else "insuffisante", "evidence": f"{len(sources)} sources reliées au calcul" if lineage_ok else "chaîne de sources rompue"},
        {"name": "Calculs", "level": "elevee", "evidence": "formules Python déterministes; aucun chiffre produit par un LLM"},
        {"name": "Sol", "level": {"mesure_utilisateur": "elevee", "source_secondaire": "moyenne", "interpolation_idw": "faible"}.get(soil_method, "faible"), "evidence": soil.get("detail", "sol non mesuré")},
        {"name": "Eau", "level": result.get("hydro_confidence", "faible"), "evidence": result.get("hydro_detail", "mesure absente")},
        {"name": "Prévision", "level": "moyenne" if result.get("horizon_mois") == 3 else "faible", "evidence": "horizon de 3 mois" if result.get("horizon_mois") == 3 else "horizon lointain"},
        {"name": "Économie", "level": "moyenne", "evidence": "prix et charges moyens à remplacer par les valeurs de l’exploitation"},
    ]
    verified = sum(item["level"] == "elevee" for item in checks)
    return {
        "checks": checks,
        "verified_count": verified,
        "total_count": len(checks),
        "lineage_verified": lineage_ok,
        "safe_to_compare": lineage_ok and result.get("confiance", {}).get("niveau") != "insuffisante",
        "statement": "Comparaison utilisable, décision à confirmer" if lineage_ok else "Comparaison non utilisable",
    }
