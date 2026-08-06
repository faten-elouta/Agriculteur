"""Rendu HTML de l'épine de provenance."""

from __future__ import annotations

import html
from typing import Any

from services.provenance_service import short_name, urn_for

ORDER = ["hubeau_hydrometrie", "hubeau_piezometrie", "hubeau_onde", "climat_journalier", "prevision_saisonniere", "parcelles", "sol_rrp", "features_bilan_hydrique", "ref_agro_economique", "scenarios_cultures", "recommandations_parcelle"]


def render_spine(graph: dict[str, Any], impacted: set[str] | None = None) -> str:
    impacted = impacted or set()
    rows = ['<aside class="spine" aria-label="Épine de provenance"><h2>Provenance</h2>']
    for index, name in enumerate(ORDER):
        try:
            urn = urn_for(graph, name)
            props = graph["datasets"][urn]
            risk = urn in impacted
            state = "rupture" if risk else ("vigilance" if props["niveau_de_preuve"] == "dire_d_expert" else "sûr")
            css_state = "rupture" if risk else ("vigilance" if state == "vigilance" else "sur")
            rows.append(f'<section class="spine-segment {"risk" if risk else ""}" style="--i:{index}"><div><span class="dot {css_state}" aria-hidden="true"></span><strong>{html.escape(name)}</strong></div><div class="mono">{html.escape(str(props["last_updated"]))}</div><div>{html.escape(str(props["niveau_de_preuve"]))} · <span class="state {css_state}">{state}</span></div><div class="urn">{html.escape(urn)}</div></section>')
        except ValueError:
            rows.append(f'<section class="spine-segment risk"><strong>{html.escape(name)}</strong><div class="state rupture">rupture — absent</div></section>')
    rows.append("</aside>")
    return "".join(rows)
