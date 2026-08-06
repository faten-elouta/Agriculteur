from services.data_quality_service import build_quality_certificate


def test_certificate_never_calls_interpolation_high():
    result = {"mode_donnees": "reel_hybride", "parcelle_source": "RPG", "soil_resolution": {"method": "interpolation_idw", "detail": "interpolé"}, "hydro_confidence": "moyenne", "hydro_detail": "station", "horizon_mois": 3, "confiance": {"niveau": "degradee"}, "provenance": {"chaine_lineage_verifiee": True, "datasets_amont": [{"urn": "u"}]}}
    certificate = build_quality_certificate(result)
    soil = next(item for item in certificate["checks"] if item["name"] == "Sol")
    assert soil["level"] == "faible"
    assert certificate["safe_to_compare"] is True


def test_broken_lineage_blocks_comparison():
    result = {"horizon_mois": 3, "confiance": {"niveau": "insuffisante"}, "provenance": {"chaine_lineage_verifiee": False, "datasets_amont": []}}
    assert build_quality_certificate(result)["safe_to_compare"] is False
