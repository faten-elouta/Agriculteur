"""Tests des nouveaux modules visuels : lineage, console de supervision, carte et courbes d'eau."""

from __future__ import annotations

import json
from datetime import date

from ui.lineage_graph import (
    STATUS_OK,
    STATUS_STALE,
    STATUS_UNKNOWN,
    build_statuses,
    render_lineage_graph,
)
from ui.parcel_map import (
    OTHER_FILL,
    SELECTED_FILL,
    _polygons,
    _station_coords,
    render_parcel_map,
)
from ui.supervision_console import replay_supervision
from ui.water_chart import render_water_chart

from services.datahub_client import DataHubClient

GRAPH = json.load(open("fixtures/graph.json", encoding="utf-8"))


def _crop(name: str, semis: str, recolte: str, besoin: float, etat: str = "sûr") -> dict:
    return {
        "culture": name,
        "etat": etat,
        "besoin_irrigation_mm": besoin,
        "recouvrement_avec_tension_j": 0,
        "calendrier": {"semis": semis, "recolte_estimee": recolte},
    }


# --- Graphe de lineage -----------------------------------------------------


def test_lineage_nodes_and_edges_rendered():
    html = render_lineage_graph(GRAPH)
    assert "lineage-svg" in html
    # 12 nœuds rendus (11 datasets + gr4j_cher_v1 présent seulement dans les arêtes).
    assert html.count('class="lineage-node') == 12
    assert html.count('class="lineage-edge"') == sum(
        len(targets) for targets in GRAPH["lineage"].values()
    )
    assert "AGENTSKILL" not in html


def test_lineage_statuses_computed_from_metadata():
    statuses = build_statuses(GRAPH["datasets"], set())
    for urn, meta in GRAPH["datasets"].items():
        assert urn in statuses
        # Fixture datée de juillet : climat_journalier (SLA 10 j) est périmé en août.
    assert statuses["urn:li:dataset:(urn:li:dataPlatform:duckdb,climat_journalier,PROD)"][0] == STATUS_STALE
    assert statuses["urn:li:dataset:(urn:li:dataPlatform:duckdb,sol_rrp,PROD)"][0] == STATUS_OK
    # Impact simulé : la recommandation devient périmée (rouge).
    reco = "urn:li:dataset:(urn:li:dataPlatform:duckdb,recommandations_parcelle,PROD)"
    statuses = build_statuses(GRAPH["datasets"], {reco})
    assert statuses[reco][0] == STATUS_STALE


def test_lineage_status_unknown_when_malformed():
    datasets = {"urn:li:dataset:(p,a,PROD)": {"last_updated": "pas-une-date"}}
    statuses = build_statuses(datasets, set())
    assert statuses["urn:li:dataset:(p,a,PROD)"][0] == STATUS_UNKNOWN


def test_lineage_render_with_custom_statuses_and_details():
    statuses = {
        urn: (STATUS_OK, "À jour")
        for urn in GRAPH["datasets"]
    }
    html = render_lineage_graph(GRAPH, statuses=statuses, impacted_urns=set())
    assert "lineage-legend" in html
    assert '<details id="ln-' in html
    assert "freshness_sla_days" not in html  # fiche = libellés lisibles


def test_lineage_stale_node_is_pulsing():
    statuses = build_statuses(GRAPH["datasets"], set())
    html = render_lineage_graph(GRAPH, statuses=statuses)
    assert "pulse" in html


def test_lineage_escapes_html():
    datasets = {
        "urn:li:dataset:(p,<script>alert(1)</script>,PROD)": {
            "last_updated": "2026-01-01", "freshness_sla_days": "10",
        }
    }
    html = render_lineage_graph({"datasets": datasets, "lineage": {}})
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html

# --- Console de supervision -------------------------------------------------


def test_replay_supervision_offline_full_loop():
    steps = replay_supervision(None, GRAPH)
    assert len(steps) == 6
    assert steps[0]["title"] == "Charge les skills de l'agent"
    assert "simulation" in steps[0]["detail"]
    # La fixture d'août a des sources périmées → étape 3 en action.
    assert steps[2]["state"] == "action"
    assert "périmée" in steps[2]["detail"]
    assert steps[-1]["state"] == "ok"


def test_replay_supervision_connected_path():
    class FakeClient:
        def __init__(self) -> None:
            self.created = 0
            self.resolved = False

        def connected(self) -> bool:
            return True

        def list_skills(self) -> list[dict]:
            return [{"name": "freshness-sla-monitoring", "id": "freshness-sla"}]

        def freshness_summary(self, urns: list[str]) -> dict:
            return {"sources": {u: {"status": "ok"} for u in urns}, "ok": len(urns), "stale": 0, "unknown": 0}

        def create_incident(self, title: str, description: str, entity_urn: str) -> str:
            self.created += 1
            return f"urn:li:incident:demo-{self.created}"

        def emit_run(self, urn: str, status: str, summary: str) -> bool:
            return True

        def resolve_incident(self, incident_urn: str) -> bool:
            self.resolved = True
            return True

    fake = FakeClient()
    steps = replay_supervision(fake, GRAPH)
    assert len(steps) == 6
    assert fake.created == 0  # aucune source périmée côté API
    assert "simulation" not in steps[0]["detail"]
    assert steps[2]["state"] == "ok"
    assert steps[4]["state"] == "ok"


def test_replay_supervision_incident_created_and_resolved():
    class StaleClient:
        def connected(self) -> bool:
            return True

        def list_skills(self) -> list[dict]:
            return []

        def freshness_summary(self, urns: list[str]) -> dict:
            return {
                "sources": {
                    "urn:li:dataset:(urn:li:dataPlatform:duckdb,climat_journalier,PROD)": {"status": "stale"},
                    **{u: {"status": "ok"} for u in urns if "climat" not in u},
                },
                "ok": len(urns) - 1,
                "stale": 1,
                "unknown": 0,
            }

        def create_incident(self, title: str, description: str, entity_urn: str) -> str:
            self.incident = entity_urn
            return "urn:li:incident:reel-1"

        def emit_run(self, urn: str, status: str, summary: str) -> bool:
            return True

        def resolve_incident(self, incident_urn: str) -> bool:
            return True

    client = StaleClient()
    steps = replay_supervision(client, GRAPH)
    assert steps[2]["state"] == "action"
    assert "features_bilan_hydrique" in steps[2]["detail"]
    assert steps[3]["state"] == "action"
    assert client.incident == "urn:li:dataset:(urn:li:dataPlatform:duckdb,features_bilan_hydrique,PROD)"
    assert steps[5]["state"] == "ok"


def test_replay_supervision_console_html_smoke():
    from ui.supervision_console import _console_html

    steps = replay_supervision(None, GRAPH)
    html = _console_html(steps)
    assert html.count('class="console-step ') == 6
    assert "--cs-i:0" in html and "--cs-i:5" in html
    assert "AGENT TERROR-CONTEXT" in html


# --- Carte parcelle ---------------------------------------------------------


def _square_parcel(pid: str, label: str) -> dict:
    return {
        "id": pid,
        "label": label,
        "commune": "Vierzon",
        "surface_ha": 12.5,
        "sol": "limoneux",
        "reserve_utile_mm": 90,
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[2.05, 47.22], [2.06, 47.22], [2.06, 47.21], [2.05, 47.21], [2.05, 47.22]]],
        },
    }


def test_parcel_map_renders_polygons_stations_and_legend():
    parcels = [_square_parcel("p1", "Parcelle A"), _square_parcel("p2", "Parcelle B")]
    stations = [{"code_station": "S1", "libelle_station": "Cher", "longitude": 2.055, "latitude": 47.215}]
    html = render_parcel_map(parcels, stations, selected_id="p1")
    assert html.count("<polygon") == 2
    assert "station-marker" in html
    assert "Parcelle sélectionnée" in html
    # La parcelle sélectionnée porte la couleur mise en évidence.
    assert html.count(f'fill="{SELECTED_FILL}"') >= 1


def test_parcel_map_station_coords_flexible():
    assert _station_coords({"longitude": 1.5, "latitude": 2.5}) == (1.5, 2.5)
    assert _station_coords({"lon": 1, "lat": 2}) == (1.0, 2.0)
    assert _station_coords({"geometry": {"type": "Point", "coordinates": [3, 4]}}) == (3.0, 4.0)
    assert _station_coords({"code_station": "S1"}) is None


def test_parcel_map_polygon_flattening():
    mp = {"type": "MultiPolygon", "coordinates": [[[[0, 0], [1, 0], [1, 1], [0, 0]]]]}
    rings = _polygons(mp)
    assert len(rings) == 1
    assert (0.0, 0.0) in rings[0][0]
    assert _polygons(None) == []
    assert _polygons({"type": "Polygon", "coordinates": []}) == []


def test_parcel_map_empty_is_empty():
    assert render_parcel_map([], [], None) == ""


def test_parcel_map_handles_missing_geometry():
    parcels = [{"id": "p1", "label": "sans géométrie", "surface_ha": 1}]
    html = render_parcel_map(parcels, [], "p1")
    assert "sans géométrie" in html  # fiche rendue même sans polygone
    assert "<svg" not in html


# --- Lame d'eau mensuelle ---------------------------------------------------


def test_water_chart_monthly_bars():
    crops = [
        _crop("blé tendre", "2027-04-15", "2027-08-01", 120),
        _crop("maïs", "2027-05-01", "2027-09-15", 210),
    ]
    tension = [{"mois": "2027-06", "intensite": "forte"}]
    html = render_water_chart(crops, tension)
    assert "water-bar" in html
    assert "FENÊTRE DE TENSION HYDRIQUE" in html
    assert "120 mm" in html
    assert "210 mm" in html


def test_water_chart_no_crops_empty():
    assert render_water_chart([], []) == ""


def test_water_chart_animates_bars_in_sequence():
    crops = [_crop("maïs", "2027-05-01", "2027-09-15", 210)]
    html = render_water_chart(crops, [])
    assert "--wc-i:0" in html
