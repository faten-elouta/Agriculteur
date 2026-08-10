"""Lame d'eau mensuelle : besoins d'irrigation des cultures comparés mois par mois.

Graphique SVG unique pour les trois cultures : chaque barre représente la
lame d'eau (mm) rapportée par mois de cycle, colorée par l'état de la
culture (mêmes couleurs que le calendrier). Les mois de la fenêtre de
tension sont signalés par un bandeau et une flammèche. Les barres poussent
en séquence au défilement (animation `waterGrow`, décalage `--wc-i`) ;
le conteneur est révélé par l'appelant via `animate-fade-up`.

Aucune nouvelle source de données : les mois viennent des calendriers de
semis/récolte et la tension de `fenetre_de_tension`, déjà calculés.
"""

from __future__ import annotations

import html
from datetime import date
from typing import Any

from ui.i18n import MS, t

STATE_COLORS = {"sûr": "#3F7A5A", "vigilance": "#C08A2E", "rupture": "#A63D2F"}

WIDTH, HEIGHT = 900, 296
HEADER_H = 26
TENSION_H = 26
PLOT_TOP = HEADER_H + TENSION_H
PLOT_H = 200
AXIS_H = 22


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


def _series(crops: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    month_list: list[str] = []
    seen: set[str] = set()
    for crop in crops:
        for year, month in _crop_months(crop):
            key = _month_key(year, month)
            if key not in seen:
                seen.add(key)
                month_list.append(key)
    month_list.sort()
    series = []
    for crop in crops:
        cycle = _crop_months(crop)
        per = crop["besoin_irrigation_mm"] / max(1, len(cycle))
        by_month = {_month_key(y, m): round(per, 1) for y, m in cycle}
        series.append(
            {
                "culture": crop["culture"],
                "etat": crop["etat"],
                "total": crop["besoin_irrigation_mm"],
                "months": by_month,
            }
        )
    return series, month_list


def render_water_chart(crops: list[dict[str, Any]], tension_months: list[str], lang: str = MS) -> str:
    """SVG animé des lames d'eau mensuelles (déjà calculées, aucune source externe)."""
    series, month_list = _series(crops)
    if not month_list:
        return ""
    tension = {m["mois"] for m in tension_months}

    n = len(month_list)
    slot = (WIDTH - 40) / n
    month_w = slot * 0.86
    n_series = len(series)
    bar_w = month_w * 0.8 / max(1, n_series)
    max_share = max((s["months"].get(m, 0) for s in series for m in month_list), default=1) or 1
    scale = (PLOT_H - 12) / max_share

    out: list[str] = []
    out.append(
        f'<svg viewBox="0 0 {WIDTH} {HEIGHT}" role="img" '
        f'aria-label="{html.escape(t(lang, "tl.water_aria"))}" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;height:auto;display:block;">'
    )

    # Titre et légende.
    legend = "".join(
        f'<rect x="{380 + i * 170}" y="8" width="12" height="12" rx="2" '
        f'fill="{STATE_COLORS.get(s["etat"], "#888888")}"/>'
        f'<text x="{396 + i * 170}" y="18" fill="#1C2620" font-family="system-ui" font-size="11.5">'
        f'{html.escape(s["culture"].capitalize())} · {s["total"]:.0f} mm</text>'
        for i, s in enumerate(series)
    )
    out.append(
        f'<text x="18" y="18" fill="#1C2620" font-family="system-ui" font-size="12" '
        f'font-weight="600">{html.escape(t(lang, "tl.water_title"))}</text>{legend}'
    )

    # Bandeau de tension + flammèches par mois.
    for i, key in enumerate(month_list):
        cx = 20 + i * slot + slot / 2
        if key in tension:
            out.append(
                f'<rect x="{20 + i * slot:.1f}" y="{HEADER_H}" width="{slot:.1f}" height="{TENSION_H}" '
                f'fill="#C08A2E" opacity="0.14"/>'
                f'<path d="M {cx:.0f} {HEADER_H + TENSION_H - 2} l 6 7 l -12 0 z" fill="#C08A2E" opacity="0.85"/>'
            )
    out.append(
        f'<rect x="18" y="{HEADER_H}" width="{WIDTH - 36}" height="{TENSION_H}" fill="none" '
        f'stroke="#C08A2E" stroke-dasharray="4 4" opacity="0.5"/>'
        f'<text x="24" y="{HEADER_H + 17}" fill="#8A6213" font-family="system-ui" font-size="10.5" '
        f'font-weight="600">{html.escape(t(lang, "tl.water_stress"))}</text>'
    )

    # Axe Y.
    for tick in (0, max_share / 2, max_share):
        yy = PLOT_TOP + PLOT_H - tick * scale
        out.append(
            f'<line x1="18" y1="{yy:.1f}" x2="{WIDTH - 22}" y2="{yy:.1f}" '
            f'stroke="#E1E4DD" stroke-width="1"/>'
            f'<text x="14" y="{yy + 3.5:.0f}" fill="#1C2620" opacity="0.55" '
            f'font-family="ui-monospace,monospace" font-size="10" text-anchor="end">'
            f"{tick:.1f}</text>"
        )

    # Barres par culture et par mois.
    bar_index = 0
    for i, key in enumerate(month_list):
        left = 20 + i * slot + (slot - month_w) / 2
        for j, s in enumerate(series):
            value = s["months"].get(key, 0)
            if value <= 0:
                continue
            h = value * scale
            x = left + j * bar_w + (month_w - n_series * bar_w) / 2 + bar_w * 0.14
            y = PLOT_TOP + PLOT_H - h
            out.append(
                f'<g class="water-bar" style="--wc-i:{bar_index};" '
                f'transform="translate({x:.1f}, {y:.1f})">'
                f'<rect width="{bar_w * 0.72:.1f}" height="{h:.1f}" rx="2" '
                f'fill="{STATE_COLORS.get(s["etat"], "#888888")}" opacity="0.85"/>'
                f'</g>'
            )
            bar_index += 1

    # Axe X : libellés de mois.
    for i, key in enumerate(month_list):
        y, m = int(key[:4]), int(key[5:7])
        out.append(
            f'<text x="{20 + i * slot + slot / 2:.0f}" y="{PLOT_TOP + PLOT_H + 16}" '
            f'fill="#1C2620" opacity="0.7" font-family="ui-monospace,monospace" font-size="10.5" '
            f'text-anchor="middle">{y % 100:02d}/{m:02d}</text>'
        )

    out.append("</svg>")
    return "".join(out)
