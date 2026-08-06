from ui.styles import CSS


def test_css_defines_tunnel_classes():
    for selector in [".om-tunnel-header", ".om-progress-seg", ".om-kicker", ".st-key-om_screen", ".assolement-spine-full"]:
        assert selector in CSS


def test_css_defines_fade_up_keyframe():
    assert "@keyframes omFadeUp" in CSS


def test_css_respects_reduced_motion_for_om_screen():
    idx_media = CSS.index("prefers-reduced-motion:reduce) {\n  .weather-hero")
    idx_om_screen_anim = CSS.index(".st-key-om_screen { max-width:760px")
    assert idx_om_screen_anim < idx_media
    assert ".st-key-om_screen { animation:none !important; }" in CSS
