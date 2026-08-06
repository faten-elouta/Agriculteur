from ui.weather_scene import compute_header_state, render_header_scene, crop_badge_html, render_grass_band


def test_compute_header_state_default_calm_without_result():
    assert compute_header_state({}) == {"sun": "calme", "clouds": 0, "storm": False}


def test_compute_header_state_storm_on_failure_message():
    assert compute_header_state({"failure_message": "3 recommandations invalidées."}) == {
        "sun": "none",
        "clouds": 3,
        "storm": True,
    }


def test_compute_header_state_calme_when_no_crop_at_risk():
    result = {"cultures": [{"etat": "sûr"}, {"etat": "sûr"}], "confiance": {"niveau": "haute"}}
    assert compute_header_state({"result": result})["sun"] == "calme"


def test_compute_header_state_voile_below_half_at_risk():
    result = {"cultures": [{"etat": "sûr"}, {"etat": "sûr"}, {"etat": "vigilance"}], "confiance": {"niveau": "haute"}}
    assert compute_header_state({"result": result})["sun"] == "voile"


def test_compute_header_state_chaud_at_or_above_half_at_risk():
    result = {"cultures": [{"etat": "sûr"}, {"etat": "rupture"}], "confiance": {"niveau": "haute"}}
    assert compute_header_state({"result": result})["sun"] == "chaud"


def test_compute_header_state_insuffisante_confidence_forces_chaud():
    result = {"cultures": [], "confiance": {"niveau": "insuffisante"}}
    assert compute_header_state({"result": result})["sun"] == "chaud"


def test_render_header_scene_returns_valid_html_for_extreme_states():
    calm = render_header_scene({"sun": "calme", "clouds": 0, "storm": False}, "EYEBROW", "Titre")
    assert "<h1>Titre</h1>" in calm
    assert 'class="sun calme"' in calm
    stormy = render_header_scene({"sun": "none", "clouds": 4, "storm": True}, "E", "T")
    assert stormy.count('class="drop"') <= 40
    assert 'class="flash"' in stormy
    assert '<div class="sun' not in stormy


def test_render_header_scene_escapes_title():
    out = render_header_scene({"sun": "calme", "clouds": 0, "storm": False}, "<x>", "<y>")
    assert "<x>" not in out
    assert "<y>" not in out


def test_crop_badge_html_variants_render_without_error():
    for etat in ["sûr", "vigilance", "rupture"]:
        assert "crop-badge" in crop_badge_html(etat)


def test_render_grass_band_caps_blade_count():
    assert render_grass_band().count('class="blade"') == 15
