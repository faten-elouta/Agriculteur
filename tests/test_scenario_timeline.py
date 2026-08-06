from ui.scenario_timeline import render_crop_scenario


def _crop(etat="sûr"):
    return {
        "culture": "tournesol",
        "etat": etat,
        "calendrier": {
            "semis": "2027-04-15",
            "recolte_estimee": "2027-09-05",
            "stade_critique": {"debut": "2027-07-10", "fin": "2027-08-05"},
        },
    }


def test_render_crop_scenario_contains_month_cells_and_cursor():
    out = render_crop_scenario(_crop(), tension_months=set(), play_token=1)
    assert "frise-month" in out
    assert "frise-cursor" in out
    assert "Tournesol" in out


def test_render_crop_scenario_marks_risk_when_critical_overlaps_tension():
    tension = {"2027-07", "2027-08"}
    out = render_crop_scenario(_crop("rupture"), tension_months=tension, play_token=1)
    assert "frise-risk" in out


def test_render_crop_scenario_no_risk_marker_when_crop_is_safe():
    tension = {"2027-07"}
    out = render_crop_scenario(_crop("sûr"), tension_months=tension, play_token=1)
    assert "frise-risk" not in out


def test_render_crop_scenario_play_token_changes_output():
    a = render_crop_scenario(_crop(), tension_months=set(), play_token=1)
    b = render_crop_scenario(_crop(), tension_months=set(), play_token=2)
    assert a != b
