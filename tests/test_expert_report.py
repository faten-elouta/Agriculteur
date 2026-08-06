from services.expert_report_service import build_expert_report


def test_expert_report_separates_success_and_failure():
    result = {"horizon_mois": 3, "mode_donnees": "reel_hybride", "parcelle_source": "RPG", "soil_resolution": {"method": "interpolation_idw"}, "hydro_confidence": "moyenne", "hydro_detail": "station", "confiance": {"niveau": "degradee"}, "resolution_log": [{"field": "parcelles", "source": "RPG 2023", "status": "échec: vide"}, {"field": "parcelles", "source": "RPG 2022", "status": "utilisée"}], "provenance": {"chaine_lineage_verifiee": True, "datasets_amont": [], "modele": {"urn": "GR4J", "version": "1"}}}
    report = build_expert_report(result)
    assert report["collected"][0]["Source"] == "RPG 2022"
    assert report["failures"][0]["Source essayée"] == "RPG 2023"
    assert len(report["models"]) >= 5
    assert 0 <= report["overall_score"] <= 100
