"""Scène météo animée : état dérivé des données, rendu en CSS/HTML pur.

Lecture agronome : la tension sur l'eau se traduit par un soleil qui tape
(sécheresse), jamais par de la pluie. La pluie n'apparaît que pour l'alarme
système (panne de station), un événement distinct de la météo réelle.
Chaque effet visuel double une information déjà écrite ailleurs (pastille
d'état, texte de confiance) — jamais le seul vecteur du sens.
"""

from __future__ import annotations

import html
from typing import Any, Mapping

RAIN_DROPS_MAX = 40
GRASS_BLADES_MAX = 15

_SUN_COLOR = {"calme": "#FFDE7A", "voile": "#F2C879", "chaud": "#FF9B4A"}


def compute_header_state(session_state: Mapping[str, Any]) -> dict[str, Any]:
    """Dérive l'état météo de l'en-tête à partir du session_state Streamlit."""
    if session_state.get("failure_message"):
        return {"sun": "none", "clouds": 3, "storm": True}
    result = session_state.get("result")
    if not result:
        return {"sun": "calme", "clouds": 0, "storm": False}
    cultures = result.get("cultures", [])
    confidence = result.get("confiance", {}).get("niveau", "haute")
    if confidence == "insuffisante":
        return {"sun": "chaud", "clouds": 2, "storm": False}
    at_risk = [c for c in cultures if c.get("etat") != "sûr"]
    ratio = len(at_risk) / len(cultures) if cultures else 0.0
    if ratio == 0:
        return {"sun": "calme", "clouds": 0, "storm": False}
    if ratio < 0.5:
        return {"sun": "voile", "clouds": 1, "storm": False}
    return {"sun": "chaud", "clouds": 2, "storm": False}


def render_header_scene(state: Mapping[str, Any], eyebrow: str, title: str) -> str:
    """Rend la scène d'en-tête (ciel, soleil, nuages ou orage) avec le titre en surimpression."""
    storm = bool(state.get("storm"))
    sun_state = state.get("sun", "calme")
    sun_html = ""
    if sun_state != "none":
        color = _SUN_COLOR.get(sun_state, _SUN_COLOR["calme"])
        heat = '<span class="heat-line"></span><span class="heat-line"></span>' if sun_state == "chaud" else ""
        sun_html = (
            f'<div class="sun {sun_state}" style="width:46px;height:46px;top:18px;right:36px;'
            f'background:{color};" aria-hidden="true">{heat}</div>'
        )
    n_clouds = max(0, min(4, int(state.get("clouds", 0))))
    clouds = "".join(_cloud_html(i) for i in range(n_clouds))
    n_drops = RAIN_DROPS_MAX if storm else 0
    drops = "".join(_drop_html(i) for i in range(n_drops))
    flash = '<div class="flash" aria-hidden="true"></div>' if storm else ""
    return (
        '<div class="weather-hero">'
        f'{sun_html}{clouds}{drops}{flash}'
        '<div class="hero-title">'
        f'<span class="eyebrow">{html.escape(eyebrow)}</span>'
        f'<h1>{html.escape(title)}</h1>'
        "</div>"
        "</div>"
    )


def _drop_html(index: int) -> str:
    left = (index * 37) % 100
    delay = (index * 0.13) % 2.0
    duration = 1.1 + (index % 5) * 0.15
    height = 14 + (index % 4) * 4
    return (
        f'<div class="drop" aria-hidden="true" style="left:{left}%;height:{height}px;'
        f'animation-duration:{duration:.2f}s;animation-delay:-{delay:.2f}s;"></div>'
    )


def _cloud_html(index: int) -> str:
    top = 14 + (index % 3) * 22
    width = 60 + (index % 3) * 20
    duration = 26 + (index % 3) * 8
    delay = index * 6
    return (
        f'<div class="cloud" aria-hidden="true" style="top:{top}px;width:{width}px;height:{width * 0.4:.0f}px;'
        f'animation-duration:{duration}s;animation-delay:-{delay}s;"></div>'
    )


def crop_badge_html(etat: str) -> str:
    """Pastille météo à côté d'une culture — décorative, redondante avec l'état écrit."""
    if etat == "sûr":
        return '<span class="crop-badge" aria-hidden="true"><span class="mini-sun calme"></span></span>'
    if etat == "vigilance":
        return '<span class="crop-badge" aria-hidden="true"><span class="mini-sun voile"></span></span>'
    return '<span class="crop-badge" aria-hidden="true"><span class="mini-sun chaud"></span></span>'


def render_grass_band() -> str:
    """Bande d'herbe animée, séparateur avant l'avertissement final."""
    blades = "".join(_blade_html(i) for i in range(GRASS_BLADES_MAX))
    return f'<div class="grass-band" aria-hidden="true">{blades}</div>'


def _blade_html(index: int) -> str:
    left = index * (100 / GRASS_BLADES_MAX) + (index % 3)
    height = 18 + (index % 4) * 4
    delay = (index % 5) * 0.08
    return (
        f'<div class="blade" style="left:{left:.1f}%;height:{height}px;'
        f'animation-delay:{delay:.2f}s;"></div>'
    )
