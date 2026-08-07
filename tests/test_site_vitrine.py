"""Tests du site vitrine (ui.site_sections) et des vues de l'application.

L'app est devenue un site avec des onglets : accueil (landing), application
(tunnel décisionnel existant), donnees (graphe & IA), contact.
"""

from __future__ import annotations

import html

from ui.site_sections import (
    about_html,
    approach_html,
    cta_html,
    expertise_html,
    footer_html,
    hero_html,
    navbar_html,
    render_landing_html,
    stats_band_html,
    values_html,
)


def test_navbar_has_four_tabs_and_active_state():
    out = navbar_html("application")
    for label in ("Vision", "Application", "Graphe & IA", "Contact"):
        assert label in out
    assert 'data-nav="accueil"' in out
    assert 'data-nav="application"' in out
    assert 'data-nav="donnees"' in out
    assert 'data-nav="contact"' in out
    assert 'class="site-nav-item active" data-nav="application"' in out
    assert "Terroir" in out


def test_hero_has_title_cta_and_images():
    out = hero_html()
    assert "Choisir sa culture" in out
    assert 'data-nav="application"' in out
    assert 'data-nav="donnees"' in out
    assert "data:image/jpeg;base64," in out
    assert "site-collage-main" in out
    assert "site-collage-card" in out


def test_hero_images_are_web_optimized():
    out = hero_html()
    for keyword in ("mais", "tournesol", "orge"):
        assert keyword in out.lower() or keyword in out


def test_stats_band_has_four_counters():
    out = stats_band_html()
    assert out.count("animate-count-up") == 4
    assert "11" in out and "12" in out


def test_about_mentions_datahub_and_checklist():
    out = about_html()
    assert "données" in out.lower()
    assert "site-section" in out
    assert "SLA" in out


def test_values_has_three_cards():
    out = values_html()
    assert "Transparence" in out
    assert "Autonomie" in out
    assert "Fiabilité" in out
    assert out.count("site-value-card") == 3


def test_expertise_has_three_illustrated_cards():
    out = expertise_html()
    assert "Parcelle" in out
    assert "Eau" in out
    assert "Économie" in out
    assert out.count("site-expertise-card") == 3
    assert "svg" in out


def test_approach_has_three_steps():
    out = approach_html()
    assert out.count("site-step") >= 3


def test_cta_points_to_application():
    out = cta_html()
    assert "Lancer l'application" in out
    assert 'data-nav="application"' in out


def test_footer_has_columns_and_legal():
    out = footer_html()
    assert "site-footer" in out
    assert "Terroir" in out


def test_landing_assembles_all_sections():
    out = render_landing_html()
    for section in (hero_html(), stats_band_html(), about_html(), values_html(),
                    expertise_html(), approach_html(), cta_html(), footer_html()):
        assert section in out


def test_hero_text_is_html_escaped():
    out = hero_html()
    assert html.escape("Choisir sa culture") in out


def test_navbar_html_is_not_empty_for_each_tab():
    for tab in ("accueil", "application", "donnees", "contact"):
        assert len(navbar_html(tab)) > 200


def test_auto_demo_via_url_starts_sequence():
    """?view=application&demo=1 lance la démo sans clic (URL dédiée juges/tournage)."""
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file("app.py", default_timeout=60)
    at.query_params.update({"view": "application", "demo": "1"})
    at.run()
    assert not at.exception
    assert any("Arrêter" in b.label for b in at.button)
