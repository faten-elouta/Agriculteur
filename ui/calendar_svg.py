"""Unique graphique de l'application: calendrier SVG accessible."""

from __future__ import annotations

import html
from datetime import date
from typing import Any


def _x(day: date, start: date, end: date, left: float, width: float) -> float:
    return left + max(0, min(1, (day - start).days / max(1, (end - start).days))) * width


def calendar_svg(result: dict[str, Any]) -> tuple[str, str]:
    cultures = result["cultures"]
    if not cultures:
        return "", "Aucun calendrier: confiance insuffisante."
    dates = [date.fromisoformat(c["calendrier"]["semis"]) for c in cultures] + [date.fromisoformat(c["calendrier"]["recolte_estimee"]) for c in cultures]
    start, end = min(dates), max(dates)
    left, plot_width, width = 160.0, 760.0, 1080
    height = 150 + 92 * len(cultures)
    tension_months = {item["mois"] for item in result["fenetre_de_tension"]}
    month = date(start.year, start.month, 1)
    month_starts: list[date] = []
    while month <= end:
        month_starts.append(month)
        month = date(month.year + (month.month == 12), 1 if month.month == 12 else month.month + 1, 1)
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="cal-title cal-desc" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto">', '<title id="cal-title">Calendrier de recouvrement</title>', f'<desc id="cal-desc">{html.escape(_alternative(cultures))}</desc>', '<rect width="1080" height="100%" fill="#FFFFFF"/>']
    for m in month_starts:
        mx = _x(m, start, end, left, plot_width)
        out.append(f'<line x1="{mx:.1f}" y1="38" x2="{mx:.1f}" y2="{height-25}" stroke="#E2E0DA"/><text x="{mx+5:.1f}" y="25" fill="#1B2430" font-family="ui-monospace,monospace" font-size="13">{m.strftime("%m/%Y")}</text>')
        next_m = date(m.year + (m.month == 12), 1 if m.month == 12 else m.month + 1, 1)
        if m.strftime("%Y-%m") in tension_months:
            x2 = _x(min(next_m, end), start, end, left, plot_width)
            color = "#C08A2E" if result["horizon_mois"] != 3 else "#A63D2F"
            out.append(f'<rect x="{mx:.1f}" y="44" width="{max(2,x2-mx):.1f}" height="28" fill="{color}" opacity="0.82"/>')
    out.append('<text x="10" y="63" fill="#1B2430" font-family="system-ui" font-size="14">Tension sur l’eau</text>')
    for i, crop in enumerate(cultures):
        y = 112 + i * 92
        cal = crop["calendrier"]
        sow, harvest = date.fromisoformat(cal["semis"]), date.fromisoformat(cal["recolte_estimee"])
        cs, ce = date.fromisoformat(cal["stade_critique"]["debut"]), date.fromisoformat(cal["stade_critique"]["fin"])
        sx, hx, cx1, cx2 = (_x(d, start, end, left, plot_width) for d in (sow, harvest, cs, ce))
        state_color = {"sûr":"#3F7A5A", "vigilance":"#C08A2E", "rupture":"#A63D2F"}[crop["etat"]]
        out.extend([f'<text x="10" y="{y+6}" fill="#1B2430" font-family="Georgia,serif" font-size="17">{html.escape(crop["culture"])}</text>', f'<rect x="{sx:.1f}" y="{y-10}" width="{hx-sx:.1f}" height="18" fill="#1B2430"/>', f'<rect x="{cx1:.1f}" y="{y-16}" width="{max(3,cx2-cx1):.1f}" height="30" fill="{state_color}"/>', f'<text x="{sx:.1f}" y="{y+31}" fill="#1B2430" font-family="ui-monospace,monospace" font-size="12">{sow.strftime("%d/%m")}</text>', f'<text x="{hx-34:.1f}" y="{y+31}" fill="#1B2430" font-family="ui-monospace,monospace" font-size="12">{harvest.strftime("%d/%m")}</text>', f'<text x="940" y="{y+3}" fill="#1B2430" font-family="ui-monospace,monospace" font-size="13">{crop["marge_brute_eur_ha"]:.0f} €/ha</text>', f'<circle cx="1030" cy="{y-2}" r="5" fill="{state_color}"/><text x="1040" y="{y+3}" fill="{state_color}" font-family="system-ui" font-size="12">{crop["etat"]}</text>'])
    if result["horizon_mois"] == 12:
        out.append(f'<text x="160" y="{height-5}" fill="#1B2430" font-family="system-ui" font-size="14">Tendance climatologique, pas une prévision individuelle.</text>')
    out.append("</svg>")
    return "".join(out), _alternative(cultures)


def _alternative(cultures: list[dict[str, Any]]) -> str:
    return " ".join(f'{c["culture"]}: semis {c["calendrier"]["semis"]}, récolte {c["calendrier"]["recolte_estimee"]}, stade critique {c["calendrier"]["stade_critique"]["debut"]} au {c["calendrier"]["stade_critique"]["fin"]}, {c["recouvrement_avec_tension_j"]} jours de recouvrement, état {c["etat"]}.' for c in cultures)
