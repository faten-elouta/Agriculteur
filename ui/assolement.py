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

from ui.i18n import MS, month_labels, t
from ui.weather_scene import crop_badge_html

STATE_COLOR = {"sûr": "var(--encre)", "vigilance": "var(--vigilance)", "rupture": "var(--rupture)"}


def intro_slides(lang: str = MS) -> list[tuple[str, str]]:
    """Le carrousel d'intro de l'écran question, traduit selon la langue."""
    return [
        (t(lang, "tunnel.intro1.title"), t(lang, "tunnel.intro1.text")),
        (t(lang, "tunnel.intro2.title"), t(lang, "tunnel.intro2.text")),
    ]


def intro_slide_html(index: int, lang: str = MS) -> str:
    """Un slide du carrousel d'intro (navigation par boutons ‹ › gérée côté app.py)."""
    slides = intro_slides(lang)
    title, text = slides[index % len(slides)]
    dots = "".join(
        f'<span style="width:5px;height:5px;border-radius:50%;display:inline-block;'
        f'background:{"var(--encre)" if i == index % len(slides) else "var(--craie)"};"></span>'
        for i in range(len(slides))
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


def tunnel_header_html(screen_index: int, screen_count: int, lang: str = MS) -> str:
    """En-tête persistant du tunnel « Choisir sa culture » : titre, étape, progression."""
    segments = "".join(
        f'<div class="om-progress-seg{" done" if i <= screen_index else ""}"></div>'
        for i in range(1, screen_count + 1)
    )
    return (
        '<div class="om-tunnel-header">'
        '<div class="om-tunnel-title-row">'
        f'<h1>{t(lang, "tunnel.title")}</h1>'
        f'<span class="om-step-count">{t(lang, "tunnel.step", current=screen_index, total=screen_count)}</span>'
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


def render_timeline(result: dict[str, Any], lang: str = MS) -> str:
    """Bande de tension mensuelle + une ligne par culture, positions calculées en jours réels."""
    labels = month_labels(lang)
    axis = _month_axis(result)
    axis_start = date(axis[0][0], axis[0][1], 1)
    axis_end = date(*_add_month(*axis[-1], 1), 1)
    total_days = (axis_end - axis_start).days
    tension_set = {m["mois"] for m in result["fenetre_de_tension"]}
    n = len(axis)

    months_html = "".join(
        f'<div style="position:absolute;left:{i / n * 100:.3f}%;width:{100 / n:.3f}%;'
        f'font-family:\'IBM Plex Mono\',monospace;font-size:12px;color:var(--encre);opacity:.55;'
        f'text-align:center;text-transform:uppercase;">{labels[m]}</div>'
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
                f'color:var(--rupture);">{html.escape(t(lang, "tl.collision"))}</div>'
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
        <div style="font-family:'IBM Plex Mono',monospace;font-size:12px;color:var(--encre);opacity:.55;text-align:right;text-transform:uppercase;">{html.escape(t(lang, "tl.margin_ha"))}</div>
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:18px;align-items:center;padding:2px 0 14px;font-size:12px;color:var(--encre);opacity:.7;">
        <span style="opacity:.9;">{html.escape(t(lang, "tl.legend.how"))}</span>
        <span style="display:flex;align-items:center;gap:5px;"><span style="width:9px;height:9px;border-radius:2px;background:var(--craie);display:inline-block;"></span>{html.escape(t(lang, "tl.legend.neutral"))}</span>
        <span style="display:flex;align-items:center;gap:5px;"><span style="width:9px;height:9px;border-radius:2px;background:var(--vigilance);display:inline-block;"></span>{html.escape(t(lang, "tl.legend.amber"))}</span>
        <span style="display:flex;align-items:center;gap:5px;"><span style="width:9px;height:9px;border-radius:2px;background:var(--rupture);display:inline-block;"></span>{html.escape(t(lang, "tl.legend.red"))}</span>
        <span style="display:flex;align-items:center;gap:5px;"><span style="width:16px;height:6px;border-radius:2px;background:var(--encre);display:inline-block;"></span>{html.escape(t(lang, "tl.legend.critical"))}</span>
        <span style="display:flex;align-items:center;gap:5px;"><span style="width:16px;height:6px;border-radius:2px;background:var(--rupture);display:inline-block;"></span>{html.escape(t(lang, "tl.legend.critical_tension"))}</span>
      </div>
      <div style="display:grid;grid-template-columns:150px 1fr 92px;align-items:center;margin-bottom:6px;">
        <div style="font-size:13px;color:var(--encre);opacity:.7;">{html.escape(t(lang, "tl.tension"))}</div>
        <div style="position:relative;height:26px;display:flex;gap:2px;">{"".join(tension_cells)}</div>
        <div></div>
      </div>
      {"".join(crop_rows)}
    </div>
    """


def analysis_article(result: dict[str, Any], lang: str = MS) -> str:
    cultures = result["cultures"]
    at_risk = [c for c in cultures if c["etat"] != "sûr"]
    safe = [c for c in cultures if c["etat"] == "sûr"]
    commune = result["commune"]

    if not at_risk:
        headline = t(lang, "an.no_risk.title")
        body = (
            f'<p style="margin:0;">{html.escape(t(lang, "an.no_risk.body", commune=commune, n=len(cultures)))}</p>'
        )
    else:
        worst = max(at_risk, key=lambda c: c["recouvrement_avec_tension_j"])
        crit = worst["calendrier"]["stade_critique"]
        headline = t(lang, "an.worst.title", crop=worst["culture"].capitalize())
        relation = t(lang, "an.exactly") if worst["etat"] == "rupture" else t(lang, "an.partially")
        p1 = (
            f'<p style="margin:0 0 10px;">{html.escape(t(lang, "an.worst.p1", commune=commune, stage=crit["nom"], crop=worst["culture"], sow=_fmt(worst["calendrier"]["semis"]), start=_fmt(crit["debut"]), end=_fmt(crit["fin"]), relation=relation))}</p>'
        )
        p2 = ""
        if safe:
            diffs = sorted(round(c["marge_brute_eur_ha"] - worst["marge_brute_eur_ha"]) for c in safe)
            margin_phrase = t(lang, "an.to", a=diffs[0], b=diffs[-1]) if diffs[0] != diffs[-1] else f"{diffs[0]}"
            names = " et ".join(html.escape(c["culture"]) for c in safe)
            key = "an.safe" if len(safe) == 1 else "an.safe.plural"
            p2 = html.escape(t(lang, key, names=names, margin=margin_phrase, crop=worst["culture"]))
            if worst["leviers"]:
                p2 += html.escape(t(lang, "an.leviers", crop=worst["culture"]))
        body = p1 + (f'<p style="margin:0;">{p2}</p>' if p2 else "")

    return f"""
    <div style="margin-top:8px;padding:20px 0;border-top:1px solid var(--craie);">
      <div style="font-family:'IBM Plex Mono',monospace;font-size:12px;opacity:.55;margin-bottom:6px;">{html.escape(t(lang, "an.analysis", commune=commune, date=_fmt(result["genere_le"])))}</div>
      <div style="font-family:'IBM Plex Serif',serif;font-weight:600;font-size:17px;margin-bottom:8px;">{html.escape(headline)}</div>
      <div style="max-width:640px;font-size:15px;opacity:.9;">{body}</div>
    </div>
    """


def simulation_recap_html(cultures: list[dict[str, Any]], simulated_by_culture: dict[str, dict[str, float]], lang: str = MS) -> str:
    """Compare, pour chaque culture, la marge du scénario à celle recalculée à partir des chiffres saisis."""
    rows = []
    for c in cultures:
        simulated = simulated_by_culture.get(c["culture"])
        if simulated is None:
            continue
        scenario_margin = c["marge_brute_eur_ha"]
        delta = simulated["marge_eur_ha"] - scenario_margin
        color = "var(--sur)" if simulated["marge_eur_ha"] >= 0 else "var(--rupture)"
        if round(delta) == 0:
            delta_txt = t(lang, "rc.identical")
        else:
            delta_txt = t(lang, "rc.vs", delta=f'{"+" if delta >= 0 else "−"}{abs(delta):.0f}')
        rows.append(
            '<div style="display:grid;grid-template-columns:140px 1fr 1fr 1fr;align-items:center;gap:8px;'
            'padding:8px 0;border-top:1px solid var(--craie);font-family:\'IBM Plex Mono\',monospace;font-size:13px;">'
            f'<div style="font-family:\'IBM Plex Serif\',serif;font-size:15px;">{html.escape(c["culture"].capitalize())}</div>'
            f'<div><span style="opacity:.55;">{html.escape(t(lang, "rc.scenario"))}</span><br>{scenario_margin:+.0f} €/ha</div>'
            f'<div><span style="opacity:.55;">{html.escape(t(lang, "rc.simulated"))}</span><br><strong style="color:{color};">{simulated["marge_eur_ha"]:+.0f} €/ha</strong></div>'
            f'<div style="font-size:12px;opacity:.7;">{html.escape(delta_txt)}</div>'
            "</div>"
        )
    return f'<div style="margin-top:4px;">{"".join(rows)}</div>'


def levers_panel(risky: dict[str, Any] | None, lang: str = MS) -> str:
    """Panneau des leviers d'une culture à risque. Jamais vide : si aucun levier
    n'est calculable, un message l'explique au lieu d'une page blanche."""
    if risky is None:
        return (
            '<div style="margin-top:24px;border:1px solid var(--craie);border-radius:2px;'
            'padding:20px;background:#F2F1EC;font-size:15px;opacity:.85;">'
            f"{html.escape(t(lang, 'lv.no_risk'))}"
            "</div>"
        )
    leviers = risky.get("leviers") or []
    if not leviers:
        return (
            f'<div style="margin-top:24px;border:1px solid var(--craie);border-radius:2px;'
            f'padding:20px;background:#F2F1EC;">'
            f'<div style="font-size:13px;font-weight:600;text-transform:uppercase;letter-spacing:.02em;color:var(--encre);opacity:.6;">'
            f'{html.escape(t(lang, "lv.title", crop=risky["culture"].capitalize()))}</div>'
            f'<div style="font-size:15px;opacity:.85;margin-top:8px;">'
            f'{html.escape(t(lang, "lv.none"))}</div>'
            "</div>"
        )
    overlap = risky["recouvrement_avec_tension_j"]
    rows = []
    for lv in leviers:
        rows.append(
            '<div style="display:block;width:100%;text-align:left;border-top:1px solid var(--craie);padding:14px 20px;">'
            '<div style="font-size:15px;font-weight:500;display:flex;justify-content:space-between;">'
            f'<span>{html.escape(lv["action"])}</span>'
            f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:14px;color:var(--encre);opacity:.75;">{html.escape(t(lang, "lv.days", days=overlap, after=lv["recouvrement_apres_j"]))}</span>'
            "</div>"
            '<div style="font-size:13px;color:var(--encre);opacity:.65;display:flex;justify-content:space-between;margin-top:4px;">'
            f'<span style="font-family:\'IBM Plex Mono\',monospace;">{html.escape(lv["reserve"])}</span>'
            f'<span style="font-family:\'IBM Plex Mono\',monospace;color:var(--sur);">+{lv["gain_marge_eur_ha"]:.0f} €/ha</span>'
            "</div>"
            "</div>"
        )
    return f"""
    <div style="margin-top:24px;border:1px solid var(--craie);border-radius:2px;padding:4px 0;background:#F2F1EC;">
      <div style="padding:16px 20px 4px;font-size:13px;font-weight:600;text-transform:uppercase;letter-spacing:.02em;color:var(--encre);opacity:.6;">{html.escape(t(lang, "lv.title", crop=risky["culture"].capitalize()))}</div>
      {"".join(rows)}
    </div>
    """


def verdict_sentence(result: dict[str, Any], lang: str = MS) -> str:
    """Phrase de synthèse à l'affirmative pour le niveau 1 (décision) de l'écran résultat."""
    cultures = result["cultures"]
    if not cultures:
        return t(lang, "verdict.empty")
    best = min(cultures, key=lambda c: c["rang"])
    worst = max(cultures, key=lambda c: c["rang"])
    if best["etat"] == "sûr":
        risk_phrase = t(lang, "verdict.no_risk")
    else:
        risk_phrase = t(lang, "verdict.days", days=best["recouvrement_avec_tension_j"])
    diff = round(best["marge_brute_eur_ha"] - worst["marge_brute_eur_ha"])
    if len(cultures) == 1 or diff <= 0:
        return t(lang, "verdict.single", crop=best["culture"], risk=risk_phrase)
    return t(lang, "verdict.multi", crop=best["culture"], diff=diff, worst=worst["culture"], risk=risk_phrase)


def ranking_table_html(result: dict[str, Any], lang: str = MS) -> str:
    """Tableau de classement des cultures — niveau 1 (décision) de l'écran résultat."""
    tone = {"sûr": "var(--sur)", "vigilance": "var(--vigilance)", "rupture": "var(--rupture)"}
    header = (
        '<div style="display:grid;grid-template-columns:28px 1.4fr 1fr 1fr 1fr 1.8fr;gap:10px;padding:0 4px 8px;'
        'font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.02em;opacity:.55;">'
        '<div></div>'
        f'<div>{html.escape(t(lang, "rk.culture"))}</div>'
        f'<div>{html.escape(t(lang, "rk.state"))}</div>'
        f'<div>{html.escape(t(lang, "rk.margin"))}</div>'
        f'<div>{html.escape(t(lang, "rk.water"))}</div>'
        f'<div>{html.escape(t(lang, "rk.main_risk"))}</div></div>'
    )
    rows = []
    for c in sorted(result["cultures"], key=lambda c: c["rang"]):
        crit = c["calendrier"]["stade_critique"]
        if c["etat"] == "sûr":
            risk = t(lang, "rk.none")
        else:
            risk = t(lang, "rk.risk", stage=crit["nom"], days=c["recouvrement_avec_tension_j"])
        rows.append(
            '<div style="display:grid;grid-template-columns:28px 1.4fr 1fr 1fr 1fr 1.8fr;align-items:center;'
            'gap:10px;padding:12px 4px;border-top:1px solid var(--craie);font-size:14px;">'
            f'<div style="font-family:\'IBM Plex Mono\',monospace;opacity:.55;">#{c["rang"]}</div>'
            f'<div style="font-family:\'IBM Plex Serif\',serif;font-weight:600;font-size:15px;">{html.escape(c["culture"].capitalize())}</div>'
            f'<div><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{tone[c["etat"]]};margin-right:6px;"></span>{html.escape(c["etat"].capitalize())}</div>'
            f'<div style="font-family:\'IBM Plex Mono\',monospace;">{c["marge_brute_eur_ha"]:+.0f} €/ha</div>'
            f'<div style="font-family:\'IBM Plex Mono\',monospace;">{c["besoin_irrigation_mm"]:.0f} mm</div>'
            f'<div style="opacity:.8;">{html.escape(risk)}</div>'
            "</div>"
        )
    return f'<div style="margin-top:8px;">{header}{"".join(rows)}</div>'


_CROP_IMAGE_KEYS = {"maïs": "mais", "tournesol": "tournesol", "orge de printemps": "orge"}


def front_page_html(result: dict[str, Any]) -> str:
    """Écran résultat, niveau 1, mis en page façon « une » de journal : chapô,
    image légendée en habillage, attaque (qui/quoi/où/quand), corps en
    colonnes (classement + raisons) et chute — toute l'info essentielle
    tient sur un seul écran, le reste passe en boutons/onglets."""
    from ui.site_sections import _img_data_uri  # import tardif : évite un cycle avec ui.site_sections

    cultures = result["cultures"]
    commune = result["commune"]
    best = min(cultures, key=lambda c: c["rang"])
    at_risk = [c for c in cultures if c["etat"] != "sûr"]

    if best["etat"] == "sûr":
        chapo = (
            f'{best["culture"].capitalize()} traverse son stade critique sans croiser la tension en eau prévue '
            f'sur {html.escape(commune)} : c\'est l\'option la plus sûre des {len(cultures)} comparées.'
        )
    else:
        chapo = (
            f'Sur {html.escape(commune)}, {best["culture"]} reste la meilleure option malgré '
            f'{best["recouvrement_avec_tension_j"]} jours de recouvrement avec la tension en eau prévue.'
        )

    tension_debut = ""
    if result.get("fenetre_de_tension"):
        first_mois = min(m["mois"] for m in result["fenetre_de_tension"])
        year, month = int(first_mois[:4]), int(first_mois[5:7])
        tension_debut = f" à partir de {month_labels(MS)[month]} {year}"
    attaque = (
        f'<p style="margin:0 0 12px;">Sur une parcelle de {html.escape(commune)}, {len(cultures)} cultures — '
        f'{", ".join(html.escape(c["culture"]) for c in cultures)} — sont comparées à partir d\'un semis prévu au '
        f'{_fmt(best["calendrier"]["semis"])}. Le modèle date le stade critique de chacune et le confronte à la '
        f'fenêtre de tension en eau{html.escape(tension_debut)}.</p>'
    )

    image_html = ""
    img_key = _CROP_IMAGE_KEYS.get(best["culture"], "")
    if img_key:
        uri = _img_data_uri(img_key)
        if uri:
            image_html = (
                '<figure style="float:right;width:34%;max-width:280px;margin:0 0 12px 20px;">'
                f'<img src="{uri}" alt="{html.escape(best["culture"])}" style="width:100%;height:auto;border-radius:2px;display:block;"/>'
                '<figcaption style="font-size:12px;opacity:.6;margin-top:6px;font-family:\'IBM Plex Mono\',monospace;">'
                f'{html.escape(best["culture"].capitalize())} — option recommandée sur cette parcelle</figcaption>'
                "</figure>"
            )

    reason_lines = "".join(
        f'<div style="font-size:14px;padding:5px 0;opacity:.85;">{html.escape(crop_reason_line(c))}</div>'
        for c in sorted(cultures, key=lambda c: c["rang"])
    )
    corps = (
        '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:11px;font-weight:600;text-transform:uppercase;'
        'letter-spacing:.02em;opacity:.55;margin:14px 0 4px;">Le classement</div>'
        f'{ranking_table_html(result)}'
        '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:11px;font-weight:600;text-transform:uppercase;'
        'letter-spacing:.02em;opacity:.55;margin:18px 0 4px;">Pourquoi</div>'
        f'<div>{reason_lines}</div>'
    )

    if at_risk:
        chute = (
            f'Reste à décider : sécuriser {at_risk[0]["culture"]} avec les leviers ci-dessous, ou partir '
            f'directement sur {best["culture"]}.'
        )
    else:
        chute = "Aucun arbitrage à faire cette année sur l'eau : le calendrier passe partout."

    return f"""
    <article style="margin-top:6px;">
      <div style="font-family:'IBM Plex Serif',serif;font-weight:700;font-size:18px;line-height:1.4;margin-bottom:14px;">{chapo}</div>
      <div style="overflow:hidden;">
        {image_html}
        {attaque}
        {corps}
      </div>
      <div style="clear:both;margin-top:16px;padding-top:14px;border-top:1px solid var(--craie);font-family:'IBM Plex Serif',serif;font-style:italic;font-size:14px;opacity:.85;">{html.escape(chute)}</div>
    </article>
    """


def crop_reason_line(c: dict[str, Any], lang: str = MS) -> str:
    """Une ligne de raison par culture (y compris sûre) — niveau 2 (pourquoi)."""
    crit = c["calendrier"]["stade_critique"]
    if c["etat"] == "sûr":
        return t(lang, "reason.safe", crop=c["culture"].capitalize(), stage=crit["nom"])
    if c["etat"] == "rupture":
        return t(lang, "reason.full", crop=c["culture"].capitalize(), stage=crit["nom"],
                  start=_fmt(crit["debut"]), end=_fmt(crit["fin"]), days=c["recouvrement_avec_tension_j"])
    return t(lang, "reason.partial", crop=c["culture"].capitalize(), stage=crit["nom"],
              start=_fmt(crit["debut"]), end=_fmt(crit["fin"]), days=c["recouvrement_avec_tension_j"])


def comparator_html(a: dict[str, Any], b: dict[str, Any], lang: str = MS) -> str:
    """« Et si je remplace X par Y ? » — compare deux cultures déjà calculées, aucune nouvelle donnée."""
    def risk_txt(c: dict[str, Any]) -> str:
        if c["etat"] == "sûr":
            return t(lang, "cmp.risk.none")
        return t(lang, "cmp.risk.days", days=c["recouvrement_avec_tension_j"])

    def col(c: dict[str, Any]) -> str:
        return (
            '<div style="flex:1;min-width:180px;">'
            f'<div style="font-family:\'IBM Plex Serif\',serif;font-weight:600;font-size:16px;margin-bottom:8px;">{html.escape(c["culture"].capitalize())}</div>'
            f'<div style="font-size:13px;padding:6px 0;border-top:1px solid var(--craie);display:flex;justify-content:space-between;"><span style="opacity:.6;">{html.escape(t(lang, "cmp.label.water"))}</span><b>{c["besoin_irrigation_mm"]:.0f} mm</b></div>'
            f'<div style="font-size:13px;padding:6px 0;border-top:1px solid var(--craie);display:flex;justify-content:space-between;"><span style="opacity:.6;">{html.escape(t(lang, "cmp.label.risk"))}</span><b>{html.escape(risk_txt(c))}</b></div>'
            f'<div style="font-size:13px;padding:6px 0;border-top:1px solid var(--craie);display:flex;justify-content:space-between;"><span style="opacity:.6;">{html.escape(t(lang, "cmp.label.margin"))}</span><b>{c["marge_brute_eur_ha"]:+.0f} €/ha</b></div>'
            "</div>"
        )

    diff = round(b["marge_brute_eur_ha"] - a["marge_brute_eur_ha"])
    if a["culture"] == b["culture"]:
        verdict = t(lang, "cmp.same")
    elif diff > 0:
        water_gain = t(lang, "cmp.water_gain") if b["besoin_irrigation_mm"] < a["besoin_irrigation_mm"] else ""
        verdict = t(lang, "cmp.gain", a=a["culture"], b=b["culture"], diff=diff, water=water_gain)
    elif diff < 0:
        verdict = t(lang, "cmp.cost", a=a["culture"], b=b["culture"], diff=abs(diff))
    else:
        verdict = t(lang, "cmp.equal", a=a["culture"].capitalize(), b=b["culture"])

    return (
        '<div style="display:flex;gap:24px;align-items:flex-start;margin-top:12px;flex-wrap:wrap;">'
        f'{col(a)}<div style="font-size:20px;opacity:.4;padding-top:22px;">→</div>{col(b)}'
        "</div>"
        f'<div style="margin-top:14px;padding-top:12px;border-top:1px solid var(--craie);font-size:14px;font-weight:500;">{html.escape(verdict)}</div>'
    )


def no_risk_panel_html(lang: str = MS) -> str:
    """Contenu de l'écran « Comment éviter » quand aucune culture ne croise la tension en eau."""
    return (
        '<div style="margin-top:24px;border:1px solid var(--craie);border-radius:2px;'
        'padding:20px;background:#F2F1EC;font-size:16px;opacity:.85;">'
        f"{html.escape(t(lang, 'no_risk.text'))}"
        "</div>"
    )
