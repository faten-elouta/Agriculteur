"""Graphe de lineage interactif : DAG SVG animé des sources jusqu'aux recommandations.

Chaque nœud est coloré selon la fraîcheur réelle (à jour / périmé / inconnu)
et porte son niveau de preuve. Les arêtes se dessinent au défilement ; un clic
sur un nœud amène à sa fiche détaillée (SLA, dernière mise à jour, licence).
Le graphe reproduit l'information du graphe DataHub (fixture ou API) sans
nouvelle source de données : la même qui alimente les badges de fraîcheur.
"""

from __future__ import annotations

import html
from datetime import date, datetime
from typing import Any

STATUS_OK = "ok"
STATUS_STALE = "stale"
STATUS_UNKNOWN = "unknown"

PROOF_LABELS = {
    "mesure": "Mesure",
    "modelisation": "Modélisation",
    "dire_d_expert": "Dire d'expert",
}

_STATUS_COLORS = {
    STATUS_OK: "ok",
    STATUS_STALE: "stale",
    STATUS_UNKNOWN: "unknown",
}

LAYER_LABELS = {
    0: "Sources ouvertes",
    1: "Assemblage",
    2: "Scénarios & modèles",
    3: "Décision",
}


def _short_name(urn: str) -> str:
    if "," in urn:
        return urn.split(",")[1].strip()
    return urn.rsplit(":", 1)[-1]


def _status_from_meta(
    dataset: dict[str, Any], today: date, impacted: bool
) -> tuple[str, str]:
    if impacted:
        return STATUS_STALE, "Impacté par l'incident"
    sla_raw = dataset.get("freshness_sla_days")
    last_raw = dataset.get("last_updated")
    try:
        sla_days = float(sla_raw)
        last = datetime.fromisoformat(last_raw).date()
    except (TypeError, ValueError):
        return STATUS_UNKNOWN, "Fraîcheur inconnue"
    age = (today - last).days
    if age <= sla_days:
        return STATUS_OK, f"À jour · {age:g} j / {sla_days:g} j SLA"
    return STATUS_STALE, f"Périmé · {age:g} j / {sla_days:g} j SLA"


def _layer_of(urn: str, edges: dict[str, list[str]], layer: dict[str, int]) -> int:
    if urn in layer:
        return layer[urn]
    upstream = [u for u, targets in edges.items() if urn in targets]
    if not upstream:
        layer[urn] = 0
        return 0
    depth = 1 + max(_layer_of(u, edges, layer) for u in upstream)
    layer[urn] = depth
    return depth


def build_statuses(
    datasets: dict[str, dict[str, Any]], impacted_urns: set[str], today: date | None = None
) -> dict[str, tuple[str, str]]:
    """Statut (couleur, libellé) par URN, calculé localement comme l'app le fait."""
    today = today or date.today()
    return {
        urn: _status_from_meta(meta, today, urn in impacted_urns)
        for urn, meta in datasets.items()
    }


def render_lineage_graph(
    graph: dict[str, Any],
    statuses: dict[str, tuple[str, str]] | None = None,
    impacted_urns: set[str] | None = None,
    *,
    animate: bool = True,
) -> str:
    """HTML/SVG du graphe de lineage + fiches détaillées sous chaque nœud."""
    datasets = graph.get("datasets", {})
    edges = graph.get("lineage", {})
    impacted_urns = impacted_urns or set()
    statuses = statuses or build_statuses(datasets, impacted_urns)
    if not datasets and not edges:
        return ""

    layer: dict[str, int] = {}
    known = set(datasets)
    for urn in {u for targets in edges.values() for u in targets} | set(edges):
        known.add(urn)
    nodes = [
        {"urn": urn, "short": _short_name(urn), "layer": _layer_of(urn, edges, layer)}
        for urn in sorted(known)
    ]
    max_layer = max(n["layer"] for n in nodes)

    # Colonnes par couche ; chaque nœud reçoit une position (col, rang).
    columns: dict[int, list[dict[str, Any]]] = {}
    for n in nodes:
        columns.setdefault(n["layer"], []).append(n)
    for col in columns.values():
        col.sort(key=lambda n: n["short"])

    cell_w, cell_h = 168, 44
    gap_x, gap_y = 46, 18
    node_w = cell_w - gap_x
    width = (max_layer + 1) * cell_w + 40
    rows = max(len(col) for col in columns.values())
    height = rows * cell_h + 70

    positions: dict[str, tuple[float, float]] = {}
    reveal_index = 0
    for col_idx, layer_nodes in sorted(columns.items()):
        for row_idx, node in enumerate(layer_nodes):
            x = 20 + col_idx * cell_w
            y = 24 + row_idx * cell_h
            positions[node["urn"]] = (x, y)
            node["reveal"] = reveal_index
            reveal_index += 1

    node_html: list[str] = []
    edge_html: list[str] = []
    detail_html: list[str] = []
    seen_edges: set[tuple[str, str]] = set()

    for source, targets in edges.items():
        if source not in positions:
            continue
        for target in targets:
            if target not in positions:
                continue
            key = (source, target)
            if key in seen_edges:
                continue
            seen_edges.add(key)
            sx, sy = positions[source]
            tx, ty = positions[target]
            cx = (sx + node_w + tx) / 2
            edge_html.append(
                f'<path class="lineage-edge" d="M {sx + node_w:.0f} {sy + cell_h / 2:.0f} '
                f'C {cx:.0f} {sy + cell_h / 2:.0f}, {cx:.0f} {ty + cell_h / 2:.0f}, '
                f'{tx:.0f} {ty + cell_h / 2:.0f}" />'
            )

    for node in nodes:
        urn = node["urn"]
        x, y = positions[urn]
        status, label = statuses.get(urn, (STATUS_UNKNOWN, "Fraîcheur inconnue"))
        color = _STATUS_COLORS[status]
        meta = datasets.get(urn, {})
        proof = PROOF_LABELS.get(meta.get("niveau_de_preuve", ""), meta.get("niveau_de_preuve", ""))
        slug = f"ln-{html.escape(node['short'].replace('_', '-'))}"
        pulse = ' pulse' if status == STATUS_STALE else ''
        pct_x = x / width * 100
        pct_y = y / height * 100
        pct_w = node_w / width * 100
        node_html.append(
            f'<a href="#{slug}" class="lineage-node {color}{pulse}" '
            f'style="left:{pct_x:.3f}%; top:{pct_y:.3f}%; width:{pct_w:.3f}%; '
            f'--lg-i:{node["reveal"]};" aria-label="{html.escape(node["short"])}">'
            f'<span class="lineage-dot"></span>'
            f'<span class="lineage-name">{html.escape(node["short"])}</span>'
            f'<span class="lineage-proof">{html.escape(proof)}</span>'
            f"</a>"
        )
        details = [
            ("Statut", label),
            ("SLA", f'{meta.get("freshness_sla_days", "—")} j'),
            ("Dernière mise à jour", meta.get("last_updated", "—")),
            ("Niveau de preuve", proof),
            ("Couverture", meta.get("spatial_coverage", "—")),
            ("Licence", meta.get("licence", "—")),
            ("Redistribuable", meta.get("redistribuable", "—")),
        ]
        rows_detail = "".join(
            f"<dt>{html.escape(k)}</dt><dd>{html.escape(str(v))}</dd>" for k, v in details
        )
        layer_name = LAYER_LABELS.get(node["layer"], f"Couche {node['layer']}")
        detail_html.append(
            f'<details id="{slug}" class="lineage-card">'
            f"<summary>{html.escape(node['short'])}"
            f'<span class="lineage-card-layer">{html.escape(layer_name)}</span></summary>'
            f"<dl>{rows_detail}</dl></details>"
        )

    legend = "".join(
        f'<span class="lineage-legend {color}"><i></i>{label}</span>'
        for color, label in (
            (STATUS_OK, "à jour"),
            (STATUS_STALE, "périmé / impacté"),
            (STATUS_UNKNOWN, "inconnu"),
        )
    )

    stage = ""
    if animate:
        stage = f' style="--lg-layers:{max_layer + 1};"'

    return (
        f'<div class="lineage"' + stage + ">"
        f'<div class="lineage-stage">'
        f"<svg class=\"lineage-svg\" viewBox=\"0 0 {width} {height}\" "
        f'preserveAspectRatio="none" role="img" '
        f'aria-label="Graphe de lineage des données">{ "".join(edge_html) }</svg>'
        f'{"".join(node_html)}'
        f"</div>"
        f'<div class="lineage-legend">{legend}</div>'
        f'<div class="lineage-details">{"".join(detail_html)}</div>'
        f"</div>"
    )


def lineage_html(graph: dict[str, Any], **kwargs: Any) -> str:
    """API courte pour les écrans : graphe + statuts recalculés."""
    return render_lineage_graph(graph, **kwargs)
