"""Tests des KPIs : définitions (Confiance / Produit / IA) et rendu du tableau de bord."""

from __future__ import annotations

import json
from datetime import date

from services.kpi_service import MCP_TOOLS, Kpi, build_kpis, _freshness
from services.recommendation_service import build_recommendation
from ui.kpis import render_kpi_dashboard, _kpi_tile

GRAPH = json.load(open("fixtures/graph.json", encoding="utf-8"))
SPECS = json.load(open("data/cultures_reference.json", encoding="utf-8"))

PARCEL = {
    "id": "RPG-2025-DEMO",
    "commune": "Vierzon",
    "surface_ha": 12.5,
    "sol": "limono-argileux",
    "reserve_utile_mm": 92,
    "culture_actuelle": "blé tendre",
    "geometry": {
        "type": "Polygon",
        "coordinates": [[[2.05, 47.22], [2.062, 47.22], [2.062, 47.212], [2.05, 47.212], [2.05, 47.22]]],
    },
}


def _result() -> dict:
    result = build_recommendation(GRAPH, PARCEL, SPECS, date(2027, 4, 15), 3, date(2026, 7, 30))
    result["mode_donnees"] = "reel_hybride"
    result["parcelle_source"] = "RPG 2024"
    result["soil_resolution"] = {"method": "mesure_utilisateur"}
    result["hydro_confidence"] = "moyenne"
    return result


def test_three_families_with_six_kpis_each():
    kpis = build_kpis(GRAPH, _result())
    assert list(kpis) == ["confiance", "produit", "ia"]
    for family in kpis.values():
        assert len(family) == 6
        for kpi in family:
            assert isinstance(kpi, Kpi)
            assert kpi.label and kpi.caption


def test_confidence_kpis_reflect_fixture_state():
    kpis = build_kpis(GRAPH, _result())
    confiance = {k.key: k for k in kpis["confiance"]}
    sla = confiance["sla"]
    assert sla.unit == "%"
    # En août, 6 sources sur 11 dépassent leur SLA → conformité 45 % → rupture.
    assert sla.value == round(5 / 11 * 100)
    assert sla.tone == "rupture"
    # Preuve : 4 sources en mesure sur 11.
    preuve = confiance["preuve"]
    assert preuve.value == round(4 / 11 * 100)
    assert confiance["traçabilité"].display == "Oui"


def test_product_kpis_from_result():
    kpis = build_kpis(GRAPH, _result())
    produit = {k.key: k for k in kpis["produit"]}
    assert produit["cultures"].value == len(_result()["cultures"])
    assert produit["eau"].unit == "mm"
    assert produit["ecart_marge"].unit == "€/ha"
    assert produit["decision"].value == 7
    assert produit["parcelle"].display is None or produit["parcelle"].value == 1


def test_ai_kpis_static_and_dynamic():
    kpis = build_kpis(GRAPH, _result())
    ia = {k.key: k for k in kpis["ia"]}
    assert ia["mcp"].value == MCP_TOOLS == 12
    assert ia["skills"].value == 3  # repli hors DataHub
    assert ia["incidents"].value == 0  # repli hors DataHub
    assert ia["modele"].display == "1.0.0"
    assert ia["score_technique"].unit == "/100"


def test_live_path_reads_graph():
    class FakeClient:
        def connected(self) -> bool:
            return True

        def freshness_summary(self, urns: list[str]) -> dict:
            return {"sources": {u: {"status": "ok"} for u in urns}, "ok": len(urns), "stale": 0, "unknown": 0}

        def list_skills(self) -> list[dict]:
            return [{"name": "a"}, {"name": "b"}]

        def list_incidents(self) -> list[dict]:
            return [{"status": "ACTIVE"}, {"status": "RESOLVED"}]

    kpis = build_kpis(GRAPH, _result(), FakeClient())
    confiance = {k.key: k for k in kpis["confiance"]}
    ia = {k.key: k for k in kpis["ia"]}
    assert confiance["sla"].value == 100
    assert confiance["sla"].tone == "sur"
    assert ia["skills"].value == 2
    assert ia["incidents"].value == 1


def test_freshness_matches_status_badges():
    fresh = _freshness(GRAPH)
    assert fresh["total"] == 11
    assert fresh["ok"] + fresh["stale"] + fresh["unknown"] == 11
    assert fresh["stale"] >= 1  # climat_journalier et prevision hors SLA en août


def test_kpi_tile_count_up_and_tone():
    kpi = Kpi("test", "Conformité SLA", 82.0, "%", "sur", "8 à jour sur 10")
    html = _kpi_tile(kpi, 0, 0)
    assert "animate-count-up" in html
    assert '<b class="animate-count-up" data-target="82.00">0</b>' in html
    assert "kpi-tile sur" in html
    assert "kpi-static" not in html  # le compteur part de 0, la cible est dans data-target


def test_kpi_tile_static_display():
    kpi = Kpi("test", "Traçabilité", 1, "", "sur", "chaîne vérifiée", display="Oui")
    html = _kpi_tile(kpi, 0, 0)
    assert "kpi-static" in html
    assert "Oui" in html
    assert "animate-count-up" not in html


def test_dashboard_renders_three_groups_and_note():
    kpis = build_kpis(GRAPH, _result())
    html = render_kpi_dashboard(kpis, live=False, mode_donnees="reel_hybride")
    assert html.count('class="kpi-group"') == 3
    assert "CONFIANCE" in html and "PRODUIT" in html and "IA & AGENTS" in html
    assert html.count("kpi-tile") == 18
    assert "calcul local (fixture)" in html
    assert "aucun chiffre inventé" in html


def test_dashboard_note_changes_with_live():
    kpis = build_kpis(GRAPH, _result())
    html = render_kpi_dashboard(kpis, live=True, mode_donnees="reel_hybride")
    assert "graphe DataHub" in html


def test_dashboard_escapes_html():
    kpis = build_kpis(GRAPH, _result())
    kpis["confiance"][0] = Kpi("x", "<script>alert(1)</script>", 1, "", "sur", "<b>boom</b>")
    html = render_kpi_dashboard(kpis)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
