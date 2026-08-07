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

def navbar_html(active: str) -> str:
    """Barre de navigation (rendue en HTML, onglets = liens natifs ?view=...)."""
    items = [
        ("accueil", "Vision"),
        ("application", "Application"),
        ("donnees", "Graphe & IA"),
        ("contact", "Contact"),
    ]
    dots = "".join(
        f'<a class="site-nav-item{" active" if key == active else ""}" href="?view={key}">{label}</a>'
        for key, label in items
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
        "</div>"
        "</div>"
    )


def hero_html() -> str:
    """Hero titré + collage de trois images de cultures."""
    return (
        '<section class="site-hero" id="hero">'
        '<div class="site-hero-inner">'
        '<div class="site-hero-text">'
        '<div class="site-eyebrow">DÉCISION AGRICOLE SOURCÉE — DATAHUB, MCP & IA</div>'
        '<h1 class="site-hero-title">Choisir sa culture avec des <em>preuves</em>, pas des intuitions</h1>'
        '<p class="site-hero-lead">Terroir Context Agents compare les cultures d\'une parcelle réelle '
        "à partir de données ouvertes tracées : sol, eau, climat, marchés. Chaque chiffre est relié "
        "à sa source, contrôlé par un agent de supervision, et barré s'il devient périmé.</p>"
        '<div class="site-hero-cta">'
        '<a class="site-btn site-btn-primary" href="?view=application">Lancer l\'application</a>'
        '<a class="site-btn site-btn-ghost" href="?view=donnees">Voir le graphe & l\'IA</a>'
        "</div>"
        '<div class="site-hero-chips">'
        '<span class="site-chip"><i class="chip-dot sur"></i>11 sources de données</span>'
        '<span class="site-chip"><i class="chip-dot eau"></i>3 cultures comparées</span>'
        '<span class="site-chip"><i class="chip-dot vigilance"></i>12 outils MCP</span>'
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


def stats_band_html() -> str:
    """Bande de chiffres clés (compteurs animés)."""
    stats = [
        ("11", "", "sources de données tracées", "sur"),
        ("3", "", "cultures comparées par parcelle", "eau"),
        ("7", "", "étapes du parcours décisionnel", "vigilance"),
        ("12", "", "outils MCP pour un agent", "eau"),
    ]
    cells = "".join(
        f'<div class="site-stat {tone}">'
        f'<b class="animate-count-up" data-target="{value}">0</b>'
        f'<span class="site-stat-unit">{unit}</span>'
        f'<small>{label}</small></div>'
        for value, unit, label, tone in stats
    )
    return f'<section class="site-stats">{cells}</section>'


def about_html() -> str:
    """À propos : image + texte + liste à coches, comme la section « Un conseil humain »."""
    return (
        '<section class="site-section" id="apropos">'
        '<div class="site-section-grid two">'
        '<div class="site-figure">'
        f'<div class="site-figure-frame">{_PARCEL_SVG}</div>'
        '<div class="site-figure-caption">parcelle RPG réelle · géométrie WGS84 · sol SoilGrids</div>'
        "</div>"
        '<div class="site-section-text">'
        '<div class="site-eyebrow">NOTRE MISSION</div>'
        "<h2>Un conseil fondé sur les données, pas sur l'intuition</h2>"
        "<p>Comme un cabinet accompagne un dirigeant, Terroir Context Agents accompagne "
        "l'agriculteur dans son choix de culture : chaque recommandation s'appuie sur des "
        "données publiques vérifiées (RPG, Hub'Eau, SoilGrids, prévisions saisonnières) "
        "assemblées dans un graphe de contexte DataHub.</p>"
        "<p>Un agent MCP supervise en continu la fraîcheur des sources : si une station ne "
        "répond plus, les recommandations devenues fragiles sont barrées et un incident est "
        "ouvert dans le graphe. La décision reste humaine — les preuves, elles, sont auditées.</p>"
        '<ul class="site-checklist">'
        '<li><i>✓</i>Traçabilité complète de la source jusqu\'au chiffre</li>'
        '<li><i>✓</i>Fraîcheur contrôlée par SLA, périmés signalés</li>'
        '<li><i>✓</i>Chiffres déterministes, aucun généré par un LLM</li>'
        "</ul>"
        "</div>"
        "</div>"
        "</section>"
    )


def values_html() -> str:
    """Trois valeurs en cartes à cocher, comme Humain / Efficience / Adaptabilité."""
    values = [
        ("Transparence", "Chaque chiffre est relié à sa source, sa licence et son niveau de preuve dans le graphe.",
         "transparence"),
        ("Autonomie", "L'agent de supervision contrôle la fraîcheur et l'impact du lineage sans intervention humaine.",
         "autonomie"),
        ("Fiabilité", "Les formules sont déterministes et documentées ; le certificat de données dit ce qui est prouvé.",
         "fiabilite"),
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
        '<div class="site-kicker-row"><span class="site-eyebrow">NOS VALEURS</span>'
        "<h2>Trois engagements pour chaque décision</h2></div>"
        f'<div class="site-value-grid">{cards}</div>'
        "</section>"
    )


def expertise_html() -> str:
    """Trois cartes d'expertise illustrées, comme Restructuration / Transaction / Stratégie."""
    cards = [
        ("Parcelle & sol", "Le RPG public, la géométrie réelle des parcelles et le sol (SoilGrids ou analyse déclarée).",
         _PARCEL_SVG, "donnees"),
        ("Eau & climat", "Les stations Hub'Eau en service, la réserve utile, la fenêtre de tension et les prévisions.",
         _WATER_SVG, "application"),
        ("Économie & marchés", "Prix, charges et aides à remplacer par les valeurs de l'exploitation, marge recalculée.",
         _ECONOMY_SVG, "application"),
    ]
    items = "".join(
        '<article class="site-expertise-card">'
        f'<div class="site-expertise-media">{media}</div>'
        '<div class="site-expertise-body">'
        f"<h3>{name}</h3><p>{text}</p>"
        f'<a class="site-expertise-link" href="?view={nav}">Explorer <b>→</b></a>'
        "</div></article>"
        for name, text, media, nav in cards
    )
    return (
        '<section class="site-section" id="expertise">'
        '<div class="site-kicker-row"><span class="site-eyebrow">NOS DOMAINES D\'EXPERTISE</span>'
        "<h2>Trois piliers de données, un seul graphe</h2></div>"
        f'<div class="site-expertise-grid">{items}</div>'
        "</section>"
    )


def approach_html() -> str:
    """Approche numérotée, comme « Notre approche » du site de référence."""
    steps = [
        ("Une expertise pointue", "Maîtrise des rouages de la donnée agricole : chaque source est qualifiée par son niveau de preuve (mesure, modélisation, dire d'expert)."),
        ("Une approche orientée résultats", "Les recommandations sont directement applicables : calendrier, eau, marge — avec un impact mesurable sur la décision de semis."),
        ("Un accompagnement immersif", "L'agent de supervision travaille dans votre graphe DataHub : fraîcheur, lineage, incidents et runs y sont tracés en continu."),
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
        '<div class="site-kicker-row"><span class="site-eyebrow">NOTRE APPROCHE</span>'
        "<h2>Une méthode différenciante, techniquement documentée</h2></div>"
        f'<div class="site-steps">{items}</div>'
        "</section>"
    )


def cta_html() -> str:
    """Bandeau d'appel à l'action."""
    return (
        '<section class="site-cta">'
        '<div class="site-cta-inner">'
        "<h2>Prêt à comparer vos cultures sur votre parcelle ?</h2>"
        "<p>Entrez votre commune, chargez les parcelles réelles du RPG et recevez une comparaison sourcée, "
        "avec le certificat de données et les KPIs de confiance.</p>"
        '<a class="site-btn site-btn-primary site-btn-lg" href="?view=application">Lancer l\'application →</a>'
        "</div>"
        "</section>"
    )


def footer_html() -> str:
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
        "<p>Partenaire de la décision agricole : données ouvertes, graphe DataHub et agent MCP "
        "de supervision. Projet du hackathon Build with DataHub.</p>"
        "</div>"
        '<div class="site-footer-col">'
        "<h4>Contact</h4>"
        "<p>Hackathon Devpost — Build with DataHub: The Agent Hackathon<br/>"
        '<a href="https://github.com/faten-elouta/Agriculteur">github.com/faten-elouta/Agriculteur</a></p>'
        '<p class="site-live"><i></i>Application en ligne : '
        '<a href="https://terroir-context-agents.vercel.app">terroir-context-agents.vercel.app</a></p>'
        "</div>"
        '<div class="site-footer-col">'
        "<h4>Liens utiles</h4>"
        '<a class="site-foot-link" href="?view=accueil">Vision</a>'
        '<a class="site-foot-link" href="?view=application">Application</a>'
        '<a class="site-foot-link" href="?view=donnees">Graphe &amp; IA</a>'
        '<a class="site-foot-link" href="?view=contact">Contact</a>'
        "</div>"
        "</div>"
        '<div class="site-footer-legal">© 2026 Terroir Context Agents — Apache 2.0 · données : Licence Ouverte / Etalab 2.0 · '
        'format inspiré de consilium-bsf.fr/vision</div>'
        "</footer>"
    )


def render_landing_html() -> str:
    """La page Vision complète (sans la navbar, gérée par l'application)."""
    return "".join(
        [
            hero_html(),
            stats_band_html(),
            about_html(),
            values_html(),
            expertise_html(),
            approach_html(),
            cta_html(),
            footer_html(),
        ]
    )
