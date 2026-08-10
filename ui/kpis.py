"""Tableau de bord KPI : Confiance, Produit, IA.

Trois groupes de tuiles animées (compteurs `count-up`, entrée en cascade).
Les valeurs viennent de `services/kpi_service.build_kpis` — les mêmes
formules que l'application, aucun chiffre inventé : la légende précise
si les valeurs de graphe viennent de DataHub ou d'un calcul local.
"""

from __future__ import annotations

import html
from typing import Any

from ui.i18n import MS, t

GROUP_LABELS = {
    "confiance": ("CONFIANCE", "Ce que les données garantissent", "var(--sur)"),
    "produit": ("PRODUIT", "Le parcours décisionnel en chiffres", "var(--eau)"),
    "ia": ("IA & AGENTS", "Ce que le système calcule et expose", "var(--vigilance)"),
}


def _group_text(key: str, lang: str) -> tuple[str, str]:
    titles = {"confiance": t(lang, "kpi.confiance"), "produit": t(lang, "kpi.produit"), "ia": t(lang, "kpi.ia")}
    subtitles = {"confiance": t(lang, "kpi.confiance.sub"), "produit": t(lang, "kpi.produit.sub"), "ia": t(lang, "kpi.ia.sub")}
    return titles.get(key, key.upper()), subtitles.get(key, "")

_TONE_COLORS = {
    "sur": "var(--sur)",
    "vigilance": "var(--vigilance)",
    "rupture": "var(--rupture)",
    "eau": "var(--eau)",
    "neutre": "var(--encre)",
}


def _kpi_tile(kpi: Any, index: int, group_index: int) -> str:
    tone = _TONE_COLORS.get(kpi.tone, "var(--encre)")
    if kpi.display is not None:
        value_html = f'<b class="kpi-static">{html.escape(kpi.display)}</b>'
    else:
        decimals = 1 if kpi.value % 1 else 0
        value_text = f"{kpi.value:.{decimals}f}"
        unit_html = f'<span class="kpi-unit">{html.escape(kpi.unit)}</span>' if kpi.unit else ""
        value_html = (
            f'<b class="animate-count-up" data-target="{kpi.value:.2f}">0</b>{unit_html}'
        )
    return (
        f'<div class="kpi-tile {kpi.tone}" style="--kpi-i:{index}; --kpi-g:{group_index};" '
        f'title="{html.escape(kpi.caption)}">'
        f'<span class="kpi-label">{html.escape(kpi.label)}</span>'
        f'<div class="kpi-value">{value_html}</div>'
        f'<small class="kpi-caption">{html.escape(kpi.caption)}</small>'
        f'<i class="kpi-accent" style="background:{tone};"></i>'
        f"</div>"
    )


def render_kpi_dashboard(
    groups: dict[str, list[Any]],
    *,
    live: bool = False,
    mode_donnees: str = "inconnu",
    lang: str = MS,
) -> str:
    """HTML du tableau de bord KPI (3 familles), valeurs prêtes à compter."""
    blocks = []
    for group_index, (key, kpis) in enumerate(groups.items()):
        label, subtitle = _group_text(key, lang)
        accent = GROUP_LABELS.get(key, (key.upper(), "", "var(--encre)"))[2]
        tiles = "".join(
            _kpi_tile(kpi, index, group_index)
            for index, kpi in enumerate(kpis)
        )
        blocks.append(
            f'<section class="kpi-group" style="--kpi-accent:{accent};">'
            f'<header class="kpi-group-head">'
            f'<div><span class="kpi-kicker">{label}</span>'
            f"<p>{html.escape(subtitle)}</p></div>"
            f'<i class="kpi-group-badge"></i>'
            f"</header>"
            f'<div class="kpi-grid">{tiles}</div>'
            f"</section>"
        )
    origin = t(lang, "kpi.origin.live") if live else t(lang, "kpi.origin.local")
    note = t(lang, "kpi.note", origin=origin, mode=html.escape(mode_donnees))
    return (
        f'<div class="kpi-dashboard">'
        f'{"".join(blocks)}'
        f'<footer class="kpi-note"><span>◈</span>{html.escape(note)}</footer>'
        f"</div>"
    )


def kpis_html(graph: dict[str, Any], result: dict[str, Any], client: Any | None = None, lang: str = MS) -> str:
    """API courte : calcule et rend le tableau de bord."""
    from services.kpi_service import build_kpis

    groups = build_kpis(graph, result, client)
    live = bool(client) and getattr(client, "connected", lambda: False)()
    return render_kpi_dashboard(groups, live=live, mode_donnees=result.get("mode_donnees", "inconnu"), lang=lang)
