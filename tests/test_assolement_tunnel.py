from ui.assolement import no_risk_panel_html, screen_kicker_html, tunnel_header_html


def test_tunnel_header_shows_step_count():
    out = tunnel_header_html(2, 4)
    assert "Étape 2 / 4" in out
    assert "Choisir sa culture" in out


def test_tunnel_header_marks_segments_done_up_to_current():
    out = tunnel_header_html(3, 4)
    assert out.count('class="om-progress-seg') == 4
    assert out.count('om-progress-seg done') == 3


def test_tunnel_header_first_screen_marks_only_current_segment_done():
    out = tunnel_header_html(1, 4)
    assert out.count('om-progress-seg done') == 1


def test_screen_kicker_escapes_label():
    out = screen_kicker_html("<x>")
    assert "<x>" not in out
    assert "&lt;x&gt;" in out


def test_screen_kicker_contains_label():
    assert "La question" in screen_kicker_html("La question")


def test_no_risk_panel_mentions_no_collision():
    out = no_risk_panel_html()
    assert "aucune" in out.lower()
    assert "<div" in out
