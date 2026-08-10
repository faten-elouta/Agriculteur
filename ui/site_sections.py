"""Site vitrine façon Consilium BSF : onglets, hero avec images, sections.

Format repris du site de référence (consilium-bsf.fr/vision) :
navbar d'onglets, hero titré avec collage d'images, bande de chiffres clés,
section « à propos » (image + texte + liste), valeurs en cartes à cocher,
cartes d'expertise illustrées, approche numérotée, bandeau CTA, footer
en trois colonnes. Toutes les images sont embarquées en base64 (versions
web optimisées des cultures) : aucun appel réseau, compatible Vercel.

Les onglets ne sont que des boutons Streamlit stylés en navbar (position
fixe) qui pilotent `st.session_state.view` ; le contenu de chaque vue est
rendu ailleurs dans l'application.
"""

from __future__ import annotations

import base64
import html
from pathlib import Path
from typing import Any

from ui.i18n import MS, t

ROOT = Path(__file__).resolve().parent.parent
WEB_IMAGES = {
    "mais": ROOT / "assets" / "cultures" / "web" / "mais.jpg",
    "tournesol": ROOT / "assets" / "cultures" / "web" / "tournesol.jpg",
    "orge": ROOT / "assets" / "cultures" / "web" / "orge-printemps.jpg",
}

_SVG_CACHE: dict[str, str] = {}


def _svg_image(name: str, svg: str) -> str:
    """Illustration SVG embarquée, mise en cache."""
    _SVG_CACHE[name] = svg
    return svg


def _img_data_uri(key: str) -> str:
    path = WEB_IMAGES[key]
    if not path.exists():
        return ""
    return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode()


def _crop_img(key: str, *, alt: str, cls: str = "") -> str:
    uri = _img_data_uri(key)
    return f'<img src="{uri}" alt="{html.escape(alt)}" loading="lazy" class="{cls}"/>'


# ---------------------------------------------------------------------------
# Illustrations SVG
# ---------------------------------------------------------------------------

_PARCEL_SVG = """<svg viewBox="0 0 420 250" role="img" aria-label="Parcelles agricoles" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;">
<rect width="420" height="250" fill="#EDF2E9"/>
<path d="M20 80 L400 80 L400 235 L20 235 Z" fill="#DCE6D2"/>
<path d="M20 80 L400 80 L400 235 L20 235 Z" fill="none" stroke="#9FB3A8" stroke-width="2"/>
<path d="M60 80 L60 235 M110 80 L110 235 M160 80 L160 235 M210 80 L210 235 M260 80 L260 235 M310 80 L310 235 M360 80 L360 235" stroke="#C4D2B6" stroke-width="2" stroke-dasharray="10 8"/>
<rect x="22" y="82" width="36" height="60" fill="#3F7A5A" opacity=".55"/>
<rect x="22" y="150" width="36" height="40" fill="#B9852A" opacity=".5"/>
<rect x="212" y="82" width="36" height="60" fill="#2B6C8F" opacity=".35"/>
<path d="M320 120 a22 22 0 0 0 44 0 c0 -14 -22 -28 -22 -28 s-22 14 -22 28 z" fill="#2B6C8F" opacity=".85"/>
<circle cx="331" cy="118" r="4" fill="#fff" opacity=".9"/>
<circle cx="341" cy="112" r="3" fill="#fff" opacity=".9"/>
<text x="24" y="225" font-family="ui-monospace,monospace" font-size="11" fill="#4A5A50">RPG · parcelles réelles</text>
</svg>"""

_WATER_SVG = """<svg viewBox="0 0 420 250" role="img" aria-label="Gestion de l'eau" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;">
<rect width="420" height="250" fill="#E9F1F5"/>
<path d="M30 190 C 90 160 150 210 210 185 C 270 160 330 195 390 175 L 390 235 L 30 235 Z" fill="#2B6C8F"/>
<path d="M30 190 C 90 160 150 210 210 185 C 270 160 330 195 390 175" fill="none" stroke="#7FB3D5" stroke-width="4"/>
<path d="M210 40 a30 30 0 0 0 -60 0 c0 20 30 42 30 42 s30 -22 30 -42 z" fill="#4A90D9" opacity=".9"/>
<path d="M200 52 l10 6 l-10 6 l-4 -12 z M212 40 a3 3 0 0 1 6 0 a3 3 0 0 1 -6 0" fill="#fff" opacity=".9"/>
<rect x="150" y="200" width="130" height="26" rx="6" fill="#fff" opacity=".85"/>
<rect x="158" y="208" width="60" height="10" rx="5" fill="#B9852A"/>
<rect x="158" y="208" width="34" height="10" rx="5" fill="#3F7A5A"/>
<text x="300" y="215" font-family="ui-monospace,monospace" font-size="11" fill="#14394B">réserve utile 92 mm</text>
<text x="30" y="30" font-family="ui-monospace,monospace" font-size="11" fill="#14394B">Hub'Eau · stations en service</text>
</svg>"""

_ECONOMY_SVG = """<svg viewBox="0 0 420 250" role="img" aria-label="Chiffrage économique" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;">
<rect width="420" height="250" fill="#F6F2E8"/>
<line x1="60" y1="210" x2="390" y2="210" stroke="#C9C2B2" stroke-width="2"/>
<rect x="90" y="150" width="52" height="60" rx="5" fill="#3F7A5A"/>
<rect x="180" y="96" width="52" height="114" rx="5" fill="#2B6C8F"/>
<rect x="270" y="52" width="52" height="158" rx="5" fill="#B9852A"/>
<text x="116" y="142" font-family="ui-monospace,monospace" font-size="12" fill="#1A231D" text-anchor="middle">1 020</text>
<text x="206" y="88" font-family="ui-monospace,monospace" font-size="12" fill="#1A231D" text-anchor="middle">1 440</text>
<text x="296" y="44" font-family="ui-monospace,monospace" font-size="12" fill="#1A231D" text-anchor="middle">1 890</text>
<text x="116" y="235" font-family="system-ui" font-size="12" fill="#1A231D" text-anchor="middle">orge</text>
<text x="206" y="235" font-family="system-ui" font-size="12" fill="#1A231D" text-anchor="middle">blé</text>
<text x="296" y="235" font-family="system-ui" font-size="12" fill="#1A231D" text-anchor="middle">maïs</text>
<text x="60" y="28" font-family="ui-monospace,monospace" font-size="11" fill="#1A231D">marge brute estimée (€/ha)</text>
</svg>"""

_PARCEL_SVG = _svg_image("parcel", _PARCEL_SVG)
_WATER_SVG = _svg_image("water", _WATER_SVG)
_ECONOMY_SVG = _svg_image("economy", _ECONOMY_SVG)


# ---------------------------------------------------------------------------
# Sections du site
# ---------------------------------------------------------------------------

def navbar_html(active: str, lang: str = MS) -> str:
    """Barre de navigation (rendue en HTML, onglets = liens natifs ?view=...)."""
    items = [
        ("accueil", t(lang, "nav.vision")),
        ("application", t(lang, "nav.application")),
        ("donnees", t(lang, "nav.graph")),
        ("contact", t(lang, "nav.contact")),
    ]
    dots = "".join(
        f'<a class="site-nav-item{" active" if key == active else ""}" href="?view={key}&lang={lang}">{label}</a>'
        for key, label in items
    )
    lang_switch = (
        '<div class="site-nav-lang">'
        f'<a class="site-lang-link{" active" if lang == "fr" else ""}" href="?view={active}&lang=fr">FR</a>'
        '<span class="site-lang-sep">·</span>'
        f'<a class="site-lang-link{" active" if lang == "en" else ""}" href="?view={active}&lang=en">EN</a>'
        "</div>"
    )
    return (
        '<div class="site-navbar">'
        '<div class="site-navbar-inner">'
        '<div class="site-brand">'
        '<svg viewBox="0 0 32 32" width="30" height="30" aria-hidden="true">'
        '<circle cx="16" cy="16" r="15" fill="#3F7A5A"/>'
        '<path d="M16 25 C 9 20 8 12 16 7 C 24 12 23 20 16 25 Z" fill="#F4F6F2"/>'
        '<path d="M13 16 L15 18 L19 13" stroke="#3F7A5A" stroke-width="2" fill="none" stroke-linecap="round"/>'
        "</svg>"
        '<span class="site-brand-name">Terroir<em>Context</em>Agents</span>'
        "</div>"
        f'<nav class="site-nav-dots">{dots}</nav>'
        f"{lang_switch}"
        "</div>"
        "</div>"
    )


def hero_html(lang: str = MS) -> str:
    """Hero titré + collage de trois images de cultures."""
    return (
        '<section class="site-hero" id="hero">'
        '<div class="site-hero-inner">'
        '<div class="site-hero-text">'
        f'<div class="site-eyebrow">{t(lang, "hero.eyebrow")}</div>'
        f'<h1 class="site-hero-title">{t(lang, "hero.title")}</h1>'
        f'<p class="site-hero-lead">{t(lang, "hero.lead")}</p>'
        '<div class="site-hero-cta">'
        f'<a class="site-btn site-btn-primary" href="?view=application&lang={lang}">{t(lang, "hero.cta.analyze")}</a>'
        f'<a class="site-btn site-btn-ghost" href="?view=donnees&lang={lang}">{t(lang, "hero.cta.graph")}</a>'
        "</div>"
        '<div class="site-hero-chips">'
        f'<span class="site-chip"><i class="chip-dot sur"></i>{t(lang, "hero.chip.sources")}</span>'
        f'<span class="site-chip"><i class="chip-dot eau"></i>{t(lang, "hero.chip.crops")}</span>'
        f'<span class="site-chip"><i class="chip-dot vigilance"></i>{t(lang, "hero.chip.mcp")}</span>'
        "</div>"
        "</div>"
        '<div class="site-hero-visual">'
        '<div class="site-collage">'
        + _crop_img("tournesol", alt="Champ de tournesol", cls="site-collage-main")
        + '<div class="site-collage-card">'
        + _crop_img("mais", alt="Champ de maïs", cls="site-collage-side")
        + '</div><div class="site-collage-card bottom">'
        + _crop_img("orge", alt="Champ d'orge de printemps", cls="site-collage-side")
        + '</div></div></div></div></section>'
    )


def stats_band_html(lang: str = MS) -> str:
    """Bande de chiffres clés (compteurs animés)."""
    stats = [
        ("11", "", t(lang, "stats.sources"), "sur"),
        ("3", "", t(lang, "stats.crops"), "eau"),
        ("7", "", t(lang, "stats.steps"), "vigilance"),
        ("12", "", t(lang, "stats.mcp"), "eau"),
    ]
    cells = "".join(
        f'<div class="site-stat {tone}">'
        f'<b class="animate-count-up" data-target="{value}">0</b>'
        f'<span class="site-stat-unit">{unit}</span>'
        f'<small>{label}</small></div>'
        for value, unit, label, tone in stats
    )
    return f'<section class="site-stats">{cells}</section>'


def about_html(lang: str = MS) -> str:
    """À propos : image + texte + liste à coches, comme la section « Un conseil humain »."""
    return (
        '<section class="site-section" id="apropos">'
        '<div class="site-section-grid two">'
        '<div class="site-figure">'
        f'<div class="site-figure-frame">{_PARCEL_SVG}</div>'
        f'<div class="site-figure-caption">{t(lang, "about.caption")}</div>'
        "</div>"
        '<div class="site-section-text">'
        f'<div class="site-eyebrow">{t(lang, "about.eyebrow")}</div>'
        f"<h2>{t(lang, 'about.title')}</h2>"
        f"<p>{t(lang, 'about.p1')}</p>"
        f"<p>{t(lang, 'about.p2')}</p>"
        '<ul class="site-checklist">'
        f"<li><i>✓</i>{t(lang, 'about.check1')}</li>"
        f"<li><i>✓</i>{t(lang, 'about.check2')}</li>"
        f"<li><i>✓</i>{t(lang, 'about.check3')}</li>"
        "</ul>"
        "</div>"
        "</div>"
        "</section>"
    )


def values_html(lang: str = MS) -> str:
    """Trois valeurs en cartes à cocher, comme Humain / Efficience / Adaptabilité."""
    values = [
        (t(lang, "values.transparence"), t(lang, "values.transparence.text"), "transparence"),
        (t(lang, "values.autonomie"), t(lang, "values.autonomie.text"), "autonomie"),
        (t(lang, "values.fiabilite"), t(lang, "values.fiabilite.text"), "fiabilite"),
    ]
    cards = "".join(
        '<div class="site-value-card">'
        '<svg viewBox="0 0 28 28" width="26" height="26" aria-hidden="true">'
        '<circle cx="14" cy="14" r="12" fill="none" stroke="currentColor" stroke-width="2"/>'
        '<path d="M8.5 14.5 L12 18 L19.5 10.5" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round"/>'
        "</svg>"
        f"<h3>{name}</h3><p>{text}</p>"
        "</div>"
        for name, text, _ in values
    )
    return (
        '<section class="site-section">'
        '<div class="site-kicker-row"><span class="site-eyebrow">' + t(lang, "values.eyebrow") + "</span>"
        f"<h2>{t(lang, 'values.title')}</h2></div>"
        f'<div class="site-value-grid">{cards}</div>'
        "</section>"
    )


def expertise_html(lang: str = MS) -> str:
    """Trois cartes d'expertise illustrées, comme Restructuration / Transaction / Stratégie."""
    cards = [
        (t(lang, "expertise.card1.title"), t(lang, "expertise.card1.text"), _PARCEL_SVG, "donnees"),
        (t(lang, "expertise.card2.title"), t(lang, "expertise.card2.text"), _WATER_SVG, "application"),
        (t(lang, "expertise.card3.title"), t(lang, "expertise.card3.text"), _ECONOMY_SVG, "application"),
    ]
    items = "".join(
        '<article class="site-expertise-card">'
        f'<div class="site-expertise-media">{media}</div>'
        '<div class="site-expertise-body">'
        f"<h3>{name}</h3><p>{text}</p>"
        f'<a class="site-expertise-link" href="?view={nav}&lang={lang}">{t(lang, "expertise.explore")} <b>→</b></a>'
        "</div></article>"
        for name, text, media, nav in cards
    )
    return (
        '<section class="site-section" id="expertise">'
        '<div class="site-kicker-row"><span class="site-eyebrow">' + t(lang, "expertise.eyebrow") + "</span>"
        f"<h2>{t(lang, 'expertise.title')}</h2></div>"
        f'<div class="site-expertise-grid">{items}</div>'
        "</section>"
    )


def approach_html(lang: str = MS) -> str:
    """Approche numérotée, comme « Notre approche » du site de référence."""
    steps = [
        (t(lang, "approach.step1.title"), t(lang, "approach.step1.text")),
        (t(lang, "approach.step2.title"), t(lang, "approach.step2.text")),
        (t(lang, "approach.step3.title"), t(lang, "approach.step3.text")),
    ]
    items = "".join(
        '<div class="site-step">'
        f'<span class="site-step-num">0{index + 1}</span>'
        f"<h3>{name}</h3><p>{text}</p>"
        "</div>"
        for index, (name, text) in enumerate(steps)
    )
    return (
        '<section class="site-section" id="approche">'
        '<div class="site-kicker-row"><span class="site-eyebrow">' + t(lang, "approach.eyebrow") + "</span>"
        f"<h2>{t(lang, 'approach.title')}</h2></div>"
        f'<div class="site-steps">{items}</div>'
        "</section>"
    )


def app_hero_html(lang: str = MS) -> str:
    """Hero de la vue Application : mêmes codes visuels que l'accueil, sans collage."""
    return (
        '<section class="site-hero site-hero-app" id="application">'
        '<div class="site-hero-inner">'
        '<div class="site-hero-text">'
        f'<div class="site-eyebrow">{t(lang, "apphero.eyebrow")}</div>'
        f'<h1 class="site-hero-title">{t(lang, "hero.title")}</h1>'
        f'<p class="site-hero-lead">{t(lang, "apphero.lead")}</p>'
        '<div class="site-hero-chips">'
        f'<span class="site-chip"><i class="chip-dot sur"></i>{t(lang, "apphero.chip.parcels")}</span>'
        f'<span class="site-chip"><i class="chip-dot eau"></i>{t(lang, "apphero.chip.crops")}</span>'
        f'<span class="site-chip"><i class="chip-dot vigilance"></i>{t(lang, "apphero.chip.certificate")}</span>'
        "</div>"
        "</div>"
        '<div class="site-hero-visual">'
        '<div class="site-hero-card">'
        f'{_PARCEL_SVG}'
        f"<p>{t(lang, 'apphero.card')}</p>"
        "</div>"
        "</div>"
        "</div>"
        "</section>"
    )


def section_header_html(kicker: str, title: str, lead: str = "") -> str:
    """En-tête de section fonctionnelle, au format du site (kicker + titre + lead)."""
    lead_html = f"<p class='site-section-lead'>{lead}</p>" if lead else ""
    return (
        f'<div class="site-section-head">'
        f'<div class="site-eyebrow">{html.escape(kicker)}</div>'
        f"<h2>{html.escape(title)}</h2>"
        f"{lead_html}"
        "</div>"
    )


def cta_html(lang: str = MS) -> str:
    """Bandeau d'appel à l'action."""
    return (
        '<section class="site-cta">'
        '<div class="site-cta-inner">'
        f"<h2>{t(lang, 'cta.title')}</h2>"
        f"<p>{t(lang, 'cta.text')}</p>"
        f'<a class="site-btn site-btn-primary site-btn-lg" href="?view=application&lang={lang}">{t(lang, "cta.btn")}</a>'
        "</div>"
        "</section>"
    )


def footer_html(lang: str = MS) -> str:
    """Pied de page en trois colonnes, comme le site de référence."""
    return (
        '<footer class="site-footer">'
        '<div class="site-footer-inner">'
        '<div class="site-footer-col brand">'
        '<div class="site-brand">'
        '<svg viewBox="0 0 32 32" width="26" height="26" aria-hidden="true">'
        '<circle cx="16" cy="16" r="15" fill="#3F7A5A"/>'
        '<path d="M16 25 C 9 20 8 12 16 7 C 24 12 23 20 16 25 Z" fill="#F4F6F2"/>'
        "</svg>"
        '<span class="site-brand-name">Terroir<em>Context</em>Agents</span>'
        "</div>"
        f"<p>{t(lang, 'footer.tagline')}</p>"
        "</div>"
        '<div class="site-footer-col">'
        f"<h4>{t(lang, 'footer.contact_title')}</h4>"
        "<p>Hackathon Devpost — Build with DataHub: The Agent Hackathon<br/>"
        '<a href="https://github.com/faten-elouta/Agriculteur">github.com/faten-elouta/Agriculteur</a></p>'
        f'<p class="site-live"><i></i>{t(lang, "footer.online")} : '
        '<a href="https://terroir-context-agents.vercel.app">terroir-context-agents.vercel.app</a></p>'
        "</div>"
        '<div class="site-footer-col">'
        f"<h4>{t(lang, 'footer.links_title')}</h4>"
        f'<a class="site-foot-link" href="?view=accueil&lang={lang}">{t(lang, "nav.vision")}</a>'
        f'<a class="site-foot-link" href="?view=application&lang={lang}">{t(lang, "nav.application")}</a>'
        f'<a class="site-foot-link" href="?view=donnees&lang={lang}">{t(lang, "nav.graph")}</a>'
        f'<a class="site-foot-link" href="?view=contact&lang={lang}">{t(lang, "nav.contact")}</a>'
        "</div>"
        "</div>"
        f'<div class="site-footer-legal">{t(lang, "footer.legal")}</div>'
        "</footer>"
    )


def render_landing_html(lang: str = MS) -> str:
    """La page Vision complète (sans la navbar, gérée par l'application)."""
    return "".join(
        [
            hero_html(lang),
            stats_band_html(lang),
            about_html(lang),
            values_html(lang),
            expertise_html(lang),
            approach_html(lang),
            cta_html(lang),
            footer_html(lang),
        ]
    )
