"""Frise animée du scénario : semis → récolte, météo mensuelle, curseur de lecture.

Une frise par culture comparée. Chaque mois porte l'icône météo dérivée de la
même fenêtre de tension que le calendrier de recouvrement (aucune nouvelle
donnée) : soleil calme hors tension, voilé à proximité, chaud dans la
tension. Le curseur anime la lecture de gauche à droite ; `play_token`
change à chaque clic sur « Lecture » pour forcer le redémarrage visuel.
"""

from __future__ import annotations

import html
from datetime import date
from typing import Any

from ui.i18n import MS, t


def _add_month(year: int, month: int, delta: int) -> tuple[int, int]:
    total = year * 12 + (month - 1) + delta
    return total // 12, total % 12 + 1


def _month_key(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"


def _crop_months(crop: dict[str, Any]) -> list[tuple[int, int]]:
    cal = crop["calendrier"]
    start = date.fromisoformat(cal["semis"])
    end = date.fromisoformat(cal["recolte_estimee"])
    months = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        months.append((year, month))
        year, month = _add_month(year, month, 1)
    return months


def render_crop_scenario(crop: dict[str, Any], tension_months: set[str], play_token: int, lang: str = MS) -> str:
    """Frise mensuelle d'une culture : icône météo par mois, curseur animé, repère de risque."""
    months = _crop_months(crop)
    n = len(months)
    crit = crop["calendrier"]["stade_critique"]
    crit_start_key, crit_end_key = crit["debut"][:7], crit["fin"][:7]

    cells = []
    risk_left = None
    for i, (y, m) in enumerate(months):
        key = _month_key(y, m)
        prev_key = _month_key(*_add_month(y, m, -1))
        next_key = _month_key(*_add_month(y, m, 1))
        if key in tension_months:
            sun_state = "chaud"
        elif prev_key in tension_months or next_key in tension_months:
            sun_state = "voile"
        else:
            sun_state = "calme"
        is_critical = crit_start_key <= key <= crit_end_key
        if is_critical and crop["etat"] != "sûr" and risk_left is None:
            risk_left = i / n * 100 + (100 / n) / 2
        cells.append(
            f'<div class="frise-month{" critical" if is_critical else ""}">'
            f'<span class="frise-sun {sun_state}"></span>'
            f'<span class="frise-label">{y % 100:02d}/{m:02d}</span>'
            "</div>"
        )

    cursor_duration = max(1.6, n * 0.5)
    risk_marker = f'<div class="frise-risk" style="left:{risk_left:.1f}%;">{html.escape(t(lang, "tl.risk_marker"))}</div>' if risk_left is not None else ""

    return (
        f'<div class="frise" data-play="{play_token}">'
        f'<div class="frise-crop">{html.escape(crop["culture"].capitalize())}</div>'
        '<div class="frise-track">'
        f'{"".join(cells)}'
        f'<div class="frise-cursor" style="animation-duration:{cursor_duration:.2f}s;" aria-hidden="true"></div>'
        f"{risk_marker}"
        "</div>"
        "</div>"
    )
