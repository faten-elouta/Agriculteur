"""Rendu HTML du tableau de bord « Choisir sa culture ».

Traduit en HTML statique (généré côté serveur à partir de `result`) la maquette
Claude Design `Assolement.dc.html` — dont le runtime `<x-dc>` n'est pas
exécutable dans Streamlit. Les couleurs reprennent les tokens déjà définis
dans `ui/styles.py` (--papier/--encre/--craie/--eau/--sur/--vigilance/--rupture),
identiques à la maquette.
"""

from __future__ import annotations

import html
from datetime import date
from typing import Any

from ui.weather_scene import crop_badge_html

MONTH_LABELS = {
    1: "Janv", 2: "Févr", 3: "Mars", 4: "Avr", 5: "Mai", 6: "Juin",
    7: "Juil", 8: "Août", 9: "Sept", 10: "Oct", 11: "Nov", 12: "Déc",
}

STATE_COLOR = {"sûr": "var(--encre)", "vigilance": "var(--vigilance)", "rupture": "var(--rupture)"}

INTRO_SLIDES = [
    (
        "Ce que fait cet outil",
        "Compare le calendrier de vos cultures à la tension en eau prévue sur la parcelle, pour repérer une soif au mauvais moment avant de semer.",
    ),
    (
        "Ce qu'il ne fait pas",
        "Ne remplace pas une expertise agronomique, ne garantit pas un rendement, ne déclenche aucune irrigation.",
    ),
]


def intro_slide_html(index: int) -> str:
    """Un slide du carrousel d'intro (navigation par boutons ‹ › gérée côté app.py)."""
    title, text = INTRO_SLIDES[index % len(INTRO_SLIDES)]
    dots = "".join(
        f'<span style="width:5px;height:5px;border-radius:50%;display:inline-block;'
        f'background:{"var(--encre)" if i == index % len(INTRO_SLIDES) else "var(--craie)"};"></span>'
        for i in range(len(INTRO_SLIDES))
    )
    return f"""
    <div style="border:1px solid var(--craie);border-radius:2px;padding:8px 14px;background:#F2F1EC;">
      <div style="display:flex;align-items:baseline;justify-content:space-between;gap:10px;">
        <span style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.02em;opacity:.6;">{html.escape(title)}</span>
        <span style="display:flex;gap:4px;">{dots}</span>
      </div>
      <div style="font-size:12.5px;margin-top:2px;opacity:.85;">{html.escape(text)}</div>
    </div>
    """


def tunnel_header_html(screen_index: int, screen_count: int) -> str:
    """En-tête persistant du tunnel « Choisir sa culture » : titre, étape, progression."""
    segments = "".join(
        f'<div class="om-progress-seg{" done" if i <= screen_index else ""}"></div>'
        for i in range(1, screen_count + 1)
    )
    return (
        '<div class="om-tunnel-header">'
        '<div class="om-tunnel-title-row">'
        '<h1>Choisir sa culture</h1>'
        f'<span class="om-step-count">Étape {screen_index} / {screen_count}</span>'
        '</div>'
        f'<div class="om-progress">{segments}</div>'
        '</div>'
    )


def screen_kicker_html(label: str) -> str:
    """Petit intitulé en tête de chaque écran du tunnel (« La question », « La réponse »…)."""
    return f'<div class="om-kicker">{html.escape(label)}</div>'


def _fmt(iso_date: str) -> str:
    return date.fromisoformat(iso_date).strftime("%d/%m/%Y")


def _add_month(year: int, month: int, delta: int) -> tuple[int, int]:
    total = year * 12 + (month - 1) + delta
    return total // 12, total % 12 + 1


def _month_key(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"


def _month_axis(result: dict[str, Any]) -> list[tuple[int, int]]:
    """Couvre semis, récoltes et fenêtre de tension — pas de mois fixes."""
    cultures = result["cultures"]
    dates = [date.fromisoformat(c["calendrier"]["semis"]) for c in cultures]
    dates += [date.fromisoformat(c["calendrier"]["recolte_estimee"]) for c in cultures]
    dates += [date.fromisoformat(m["mois"] + "-01") for m in result["fenetre_de_tension"]]
    start, end = min(dates).replace(day=1), max(dates).replace(day=1)
    axis = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        axis.append((year, month))
        year, month = _add_month(year, month, 1)
    return axis


def _frac(d: date, axis_start: date, total_days: int) -> float:
    return max(0.0, min(1.0, (d - axis_start).days / total_days))


def render_timeline(result: dict[str, Any]) -> str:
    """Bande de tension mensuelle + une ligne par culture, positions calculées en jours réels."""
    axis = _month_axis(result)
    axis_start = date(axis[0][0], axis[0][1], 1)
    axis_end = date(*_add_month(*axis[-1], 1), 1)
    total_days = (axis_end - axis_start).days
    tension_set = {m["mois"] for m in result["fenetre_de_tension"]}
    n = len(axis)

    months_html = "".join(
        f'<div style="position:absolute;left:{i / n * 100:.3f}%;width:{100 / n:.3f}%;'
        f'font-family:\'IBM Plex Mono\',monospace;font-size:12px;color:var(--encre);opacity:.55;'
        f'text-align:center;text-transform:uppercase;">{MONTH_LABELS[m]}</div>'
        for i, (y, m) in enumerate(axis)
    )

    tension_cells = []
    for y, m in axis:
        key, prev_key, next_key = _month_key(y, m), _month_key(*_add_month(y, m, -1)), _month_key(*_add_month(y, m, 1))
        if key in tension_set:
            level, color, opacity = "rouge", "var(--rupture)", 0.85
        elif prev_key in tension_set or next_key in tension_set:
            level, color, opacity = "ambre", "var(--vigilance)", 0.85
        else:
            level, color, opacity = "neutre", "var(--craie)", 0.5
        tension_cells.append(f'<div title="{level}" style="flex:1;height:100%;border-radius:2px;background:{color};opacity:{opacity};"></div>')

    band_html = ""
    if tension_set:
        win_start = date.fromisoformat(min(tension_set) + "-01")
        wy, wm = int(max(tension_set)[:4]), int(max(tension_set)[5:7])
        win_end = date(*_add_month(wy, wm, 1), 1)
        band_left = _frac(win_start, axis_start, total_days) * 100
        band_width = (_frac(win_end, axis_start, total_days)) * 100 - band_left
        band_html = (
            f'<div style="position:absolute;left:{band_left:.3f}%;width:{band_width:.3f}%;top:0;bottom:0;'
            f'background:var(--rupture);opacity:.06;border-radius:2px;"></div>'
        )

    crop_rows = []
    for c in result["cultures"]:
        cal = c["calendrier"]
        sow, harvest = date.fromisoformat(cal["semis"]), date.fromisoformat(cal["recolte_estimee"])
        crit_start, crit_end = date.fromisoformat(cal["stade_critique"]["debut"]), date.fromisoformat(cal["stade_critique"]["fin"])
        left, right = _frac(sow, axis_start, total_days) * 100, _frac(harvest, axis_start, total_days) * 100
        width = right - left
        crit_left = _frac(crit_start, axis_start, total_days) * 100
        crit_width = max(0.6, _frac(crit_end, axis_start, total_days) * 100 - crit_left)
        color = STATE_COLOR[c["etat"]]
        margin = c["marge_brute_eur_ha"]
        margin_color = "var(--sur)" if margin >= 0 else "var(--rupture)"
        margin_text = f'{"+" if margin >= 0 else "−"}{abs(margin):.0f} €/ha'
        annotation = ""
        if c["etat"] == "rupture":
            ann_left = min(max(crit_left + crit_width / 2, 20), 78)
            annotation = (
                f'<div style="position:absolute;left:{ann_left:.3f}%;top:44px;transform:translateX(-50%);'
                f'white-space:nowrap;font-family:\'IBM Plex Sans\',sans-serif;font-size:12px;font-weight:600;'
                f'color:var(--rupture);">Collision — soif en pleine tension</div>'
            )
        crop_rows.append(
            '<div class="om-row" style="display:grid;grid-template-columns:150px 1fr 92px;align-items:center;'
            'padding:14px 8px;margin:0 -8px;border-top:1px solid var(--craie);border-radius:2px;">'
            f'<div style="font-family:\'IBM Plex Serif\',serif;font-weight:600;font-size:16px;padding-right:8px;">{html.escape(c["culture"].capitalize())}{crop_badge_html(c["etat"])}</div>'
            '<div style="position:relative;height:62px;">'
            f'{band_html}'
            f'<div style="position:absolute;left:{left:.3f}%;width:{width:.3f}%;top:9px;height:12px;background:var(--papier);border:1px solid var(--craie);border-radius:2px;"></div>'
            f'<div style="position:absolute;left:{crit_left:.3f}%;width:{crit_width:.3f}%;top:6px;height:18px;background:{color};border-radius:2px;"></div>'
            f'<div style="position:absolute;left:{left:.3f}%;top:26px;transform:translateX(-2%);font-family:\'IBM Plex Mono\',monospace;font-size:12px;color:var(--encre);opacity:.6;">{sow.strftime("%d/%m")}</div>'
            f'<div style="position:absolute;left:{right:.3f}%;top:26px;transform:translateX(-98%);font-family:\'IBM Plex Mono\',monospace;font-size:12px;color:var(--encre);opacity:.6;">{harvest.strftime("%d/%m")}</div>'
            f'{annotation}'
            '</div>'
            f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:15px;text-align:right;color:{margin_color};font-weight:500;">{margin_text}</div>'
            '</div>'
        )

    return f"""
    <div style="margin-bottom:8px;">
      <div style="display:grid;grid-template-columns:150px 1fr 92px;align-items:end;padding-bottom:8px;">
        <div></div>
        <div style="position:relative;height:16px;">{months_html}</div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:12px;color:var(--encre);opacity:.55;text-align:right;text-transform:uppercase;">Marge/ha</div>
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:18px;align-items:center;padding:2px 0 14px;font-size:12px;color:var(--encre);opacity:.7;">
        <span style="opacity:.9;">Comment lire :</span>
        <span style="display:flex;align-items:center;gap:5px;"><span style="width:9px;height:9px;border-radius:2px;background:var(--craie);display:inline-block;"></span>Tension neutre</span>
        <span style="display:flex;align-items:center;gap:5px;"><span style="width:9px;height:9px;border-radius:2px;background:var(--vigilance);display:inline-block;"></span>Ambre — sécheresse probable</span>
        <span style="display:flex;align-items:center;gap:5px;"><span style="width:9px;height:9px;border-radius:2px;background:var(--rupture);display:inline-block;"></span>Rouge — restriction probable</span>
        <span style="display:flex;align-items:center;gap:5px;"><span style="width:16px;height:6px;border-radius:2px;background:var(--encre);display:inline-block;"></span>Stade critique</span>
        <span style="display:flex;align-items:center;gap:5px;"><span style="width:16px;height:6px;border-radius:2px;background:var(--rupture);display:inline-block;"></span>Stade critique sous tension forte</span>
      </div>
      <div style="display:grid;grid-template-columns:150px 1fr 92px;align-items:center;margin-bottom:6px;">
        <div style="font-size:13px;color:var(--encre);opacity:.7;">Tension eau</div>
        <div style="position:relative;height:26px;display:flex;gap:2px;">{"".join(tension_cells)}</div>
        <div></div>
      </div>
      {"".join(crop_rows)}
    </div>
    """


def retain_sentence(result: dict[str, Any]) -> str:
    at_risk = [c for c in result["cultures"] if c["etat"] != "sûr"]
    if not at_risk:
        return "Aucune des cultures comparées ne croise la tension en eau prévue sur cette fenêtre."
    worst = max(at_risk, key=lambda c: c["recouvrement_avec_tension_j"])
    if worst["etat"] == "rupture":
        return (
            f'Le {worst["culture"]} traverse son stade critique en pleine tension — '
            f'{worst["recouvrement_avec_tension_j"]} jours de recouvrement. Vous voulez le garder ?'
        )
    return f'Le {worst["culture"]} chevauche partiellement la tension en eau — {worst["recouvrement_avec_tension_j"]} jours à surveiller.'


def analysis_article(result: dict[str, Any]) -> str:
    cultures = result["cultures"]
    at_risk = [c for c in cultures if c["etat"] != "sûr"]
    safe = [c for c in cultures if c["etat"] == "sûr"]
    commune = result["commune"]

    if not at_risk:
        headline = "Aucune collision entre les cultures et la tension en eau"
        body = (
            f'<p style="margin:0;">Sur {html.escape(commune)}, les {len(cultures)} cultures comparées traversent '
            "leur stade critique en dehors de la période de tension prévue sur l'eau. Aucun ajustement du calendrier "
            "n'est nécessaire dans ce scénario.</p>"
        )
    else:
        worst = max(at_risk, key=lambda c: c["recouvrement_avec_tension_j"])
        crit = worst["calendrier"]["stade_critique"]
        headline = f'Le {worst["culture"]} rejoue le même pari sur l\'eau'
        p1 = (
            f'Sur {html.escape(commune)}, {crit["nom"]} du {worst["culture"]} semé au {_fmt(worst["calendrier"]["semis"])} '
            f'tombe du {_fmt(crit["debut"])} au {_fmt(crit["fin"])} — '
            f'{"exactement" if worst["etat"] == "rupture" else "en partie"} dans la fenêtre où le modèle prévoit '
            "la tension en eau la plus forte."
        )
        p2 = ""
        if safe:
            diffs = sorted(round(c["marge_brute_eur_ha"] - worst["marge_brute_eur_ha"]) for c in safe)
            margin_phrase = f"{diffs[0]}" if diffs[0] == diffs[-1] else f"{diffs[0]} à {diffs[-1]}"
            names = " et ".join(html.escape(c["culture"]) for c in safe)
            verb = "traverse" if len(safe) == 1 else "traversent"
            p2 = (
                f'{names.capitalize()} {verb} son stade critique en dehors de la tension, avec une marge supérieure '
                f'de {margin_phrase} €/ha à celle du {worst["culture"]}.'
            )
            if worst["leviers"]:
                p2 += f' Si le {worst["culture"]} est maintenu, les leviers ci-dessous permettent de réduire son exposition.'
        body = f'<p style="margin:0 0 10px;">{p1}</p>' + (f'<p style="margin:0;">{p2}</p>' if p2 else "")

    return f"""
    <div style="margin-top:8px;padding:20px 0;border-top:1px solid var(--craie);">
      <div style="font-family:'IBM Plex Mono',monospace;font-size:12px;opacity:.55;margin-bottom:6px;">Analyse — {html.escape(commune)} — {_fmt(result["genere_le"])}</div>
      <div style="font-family:'IBM Plex Serif',serif;font-weight:600;font-size:17px;margin-bottom:8px;">{headline}</div>
      <div style="max-width:640px;font-size:15px;opacity:.9;">{body}</div>
    </div>
    """


def simulation_recap_html(cultures: list[dict[str, Any]], simulated_by_culture: dict[str, dict[str, float]]) -> str:
    """Compare, pour chaque culture, la marge du scénario à celle recalculée à partir des chiffres saisis."""
    rows = []
    for c in cultures:
        simulated = simulated_by_culture.get(c["culture"])
        if simulated is None:
            continue
        scenario_margin = c["marge_brute_eur_ha"]
        delta = simulated["marge_eur_ha"] - scenario_margin
        color = "var(--sur)" if simulated["marge_eur_ha"] >= 0 else "var(--rupture)"
        delta_txt = "identique au scénario" if round(delta) == 0 else f'{"+" if delta >= 0 else "−"}{abs(delta):.0f} €/ha vs scénario'
        rows.append(
            '<div style="display:grid;grid-template-columns:140px 1fr 1fr 1fr;align-items:center;gap:8px;'
            'padding:8px 0;border-top:1px solid var(--craie);font-family:\'IBM Plex Mono\',monospace;font-size:13px;">'
            f'<div style="font-family:\'IBM Plex Serif\',serif;font-size:15px;">{html.escape(c["culture"].capitalize())}</div>'
            f'<div><span style="opacity:.55;">Marge scénario</span><br>{scenario_margin:+.0f} €/ha</div>'
            f'<div><span style="opacity:.55;">Marge simulée</span><br><strong style="color:{color};">{simulated["marge_eur_ha"]:+.0f} €/ha</strong></div>'
            f'<div style="font-size:12px;opacity:.7;">{delta_txt}</div>'
            "</div>"
        )
    return f'<div style="margin-top:4px;">{"".join(rows)}</div>'


def levers_panel(risky: dict[str, Any] | None) -> str:
    """Panneau des leviers d'une culture à risque. Jamais vide : si aucun levier
    n'est calculable, un message l'explique au lieu d'une page blanche."""
    if risky is None:
        return (
            '<div style="margin-top:24px;border:1px solid var(--craie);border-radius:2px;'
            'padding:20px;background:#F2F1EC;font-size:15px;opacity:.85;">'
            "Aucune culture à risque : rien à corriger."
            "</div>"
        )
    leviers = risky.get("leviers") or []
    if not leviers:
        return (
            f'<div style="margin-top:24px;border:1px solid var(--craie);border-radius:2px;'
            f'padding:20px;background:#F2F1EC;">'
            f'<div style="font-size:13px;font-weight:600;text-transform:uppercase;letter-spacing:.02em;color:var(--encre);opacity:.6;">'
            f'Comment éviter — {html.escape(risky["culture"].capitalize())}</div>'
            f'<div style="font-size:15px;opacity:.85;margin-top:8px;">'
            f'Aucun levier calculable pour cette culture sur cette parcelle. Le plus sûr reste de '
            f'comparer avec une culture dont le stade critique tombe hors tension.</div>'
            "</div>"
        )
    overlap = risky["recouvrement_avec_tension_j"]
    rows = []
    for lv in leviers:
        rows.append(
            '<div style="display:block;width:100%;text-align:left;border-top:1px solid var(--craie);padding:14px 20px;">'
            '<div style="font-size:15px;font-weight:500;display:flex;justify-content:space-between;">'
            f'<span>{html.escape(lv["action"])}</span>'
            f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:14px;color:var(--encre);opacity:.75;">{overlap} j → {lv["recouvrement_apres_j"]} j</span>'
            "</div>"
            '<div style="font-size:13px;color:var(--encre);opacity:.65;display:flex;justify-content:space-between;margin-top:4px;">'
            f'<span style="font-family:\'IBM Plex Mono\',monospace;">{html.escape(lv["reserve"])}</span>'
            f'<span style="font-family:\'IBM Plex Mono\',monospace;color:var(--sur);">+{lv["gain_marge_eur_ha"]:.0f} €/ha</span>'
            "</div>"
            "</div>"
        )
    return f"""
    <div style="margin-top:24px;border:1px solid var(--craie);border-radius:2px;padding:4px 0;background:#F2F1EC;">
      <div style="padding:16px 20px 4px;font-size:13px;font-weight:600;text-transform:uppercase;letter-spacing:.02em;color:var(--encre);opacity:.6;">Comment éviter — {html.escape(risky["culture"].capitalize())}</div>
      {"".join(rows)}
    </div>
    """


def no_risk_panel_html() -> str:
    """Contenu de l'écran « Comment éviter » quand aucune culture ne croise la tension en eau."""
    return (
        '<div style="margin-top:24px;border:1px solid var(--craie);border-radius:2px;'
        'padding:20px;background:#F2F1EC;font-size:16px;opacity:.85;">'
        "Aucune culture ne nécessite d'ajustement : aucune ne croise la tension en eau prévue sur cette fenêtre."
        "</div>"
    )
