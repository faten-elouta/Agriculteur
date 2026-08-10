"""Console de supervision live : rejoue la boucle de l'agent sur le graphe.

L'agent lit les skills, vérifie la fraîcheur des sources, propage l'impact
le long du lineage, crée un incident DataHub, trace un run, puis résout
l'incident. En mode réel (DATAHUB_GMS_URL défini) les écritures partent
vraiment vers le graphe ; sinon la même boucle est rejouée en simulation
avec la fraîcheur recalculée depuis les métadonnées de la fixture.

Le rendu séquentiel (une étape toutes les ~0,4 s) donne l'effet « live »,
chacune apparaissant avec une petite entrée animée ; `st.empty` est
réécrit à chaque étape, ce qui fonctionne aussi sous AppTest.
"""

from __future__ import annotations

import html
import time
from typing import Any

import streamlit as st

from ui.i18n import MS, t

from ui.lineage_graph import _short_name

_SIMULATED_SKILLS = [
    {"name": "freshness-sla-monitoring", "id": "freshness-sla-monitoring"},
    {"name": "recommandations-contexte", "id": "recommandations-contexte"},
    {"name": "codegen-scenarios", "id": "codegen-scenarios"},
]

_STEP_TIME = 0.4


def replay_supervision(client: Any | None, graph: dict[str, Any], lang: str = MS) -> list[dict[str, str]]:
    """Rejoue la boucle de supervision et renvoie le journal des étapes."""
    datasets = graph.get("datasets", {})
    edges = graph.get("lineage", {})
    targets = {t for upstream in edges.values() for t in upstream}
    sources = [urn for urn in datasets if urn not in targets]
    live = bool(client) and getattr(client, "connected", lambda: False)()

    steps: list[dict[str, str]] = []

    # 1 — Skills de l'agent.
    if live:
        try:
            skills = client.list_skills()
            names = [s.get("name") or _short_name(s.get("id", "")) for s in skills]
        except Exception:
            names = []
    else:
        skills = _SIMULATED_SKILLS
        names = [s["name"] for s in skills]
    shown = ", ".join(names[:3]) + ("…" if len(names) > 3 else "")
    suffix = t(lang, "sup.sim_suffix") if not live else ""
    steps.append(
        {
            "icon": "✓",
            "state": "ok",
            "title": t(lang, "sup.title.skills"),
            "detail": f"{len(names)} skills actifs : {shown}{suffix}",
        }
    )

    # 2 — Fraîcheur des sources.
    if live:
        try:
            fresh = client.freshness_summary(sources)
            stale_urns = [u for u, s in fresh["sources"].items() if s["status"] == "stale"]
            detail = (
                t(lang, "sup.fresh_ok", n=fresh["ok"], stale=fresh["stale"], unknown=fresh["unknown"])
                + t(lang, "sup.fresh_total", n=len(sources))
            )
        except Exception:
            fresh, stale_urns, detail = {}, [], t(lang, "sup.fresh_unavailable")
    else:
        from ui.lineage_graph import build_statuses

        statuses = build_statuses(datasets, set())
        stale_urns = [urn for urn, (status, _) in statuses.items() if status == "stale"]
        total = len(sources)
        detail = (
            t(lang, "sup.fresh_ok", n=sum(1 for urn, (s, _) in statuses.items() if s == "ok"), stale=len(stale_urns), unknown=sum(1 for urn, (s, _) in statuses.items() if s == "unknown"))
            + t(lang, "sup.fresh_total_local", n=total)
        )
    steps.append(
        {
            "icon": "⚠" if stale_urns else "✓",
            "state": "warn" if stale_urns else "ok",
            "title": t(lang, "sup.title.fresh"),
            "detail": detail,
        }
    )

    # 3 — Propagation le long du lineage.
    impacted: list[str] = []
    first_stale: str | None = None
    if stale_urns:
        first_stale = stale_urns[0]
        frontier = [first_stale]
        visited: set[str] = set()
        while frontier:
            node = frontier.pop()
            for downstream in edges.get(node, []):
                if downstream not in visited:
                    visited.add(downstream)
                    frontier.append(downstream)
        impacted = sorted(visited)
    if impacted and first_stale:
        chain = " → ".join(
            [_short_name(first_stale), *[_short_name(u) for u in impacted[:2]]]
        )
        detail = t(lang, "sup.stale_detail", source=_short_name(first_stale), n=len(impacted), chain=chain)
    else:
        detail = t(lang, "sup.no_stale")
    steps.append(
        {
            "icon": "→" if impacted else "✓",
            "state": "action" if impacted else "ok",
            "title": t(lang, "sup.title.propagate"),
            "detail": detail,
        }
    )

    # 4 — Incident DataHub.
    incident_urn: str | None = None
    target = impacted[0] if impacted else None
    if live and target:
        try:
            incident_urn = client.create_incident(
                t(lang, "sup.stale_target", source=_short_name(target)),
                t(lang, "sup.stale_incident", source=_short_name(first_stale or ""), n=len(impacted)),
                target,
            )
        except Exception:
            incident_urn = None
    if live and incident_urn:
        detail = t(lang, "sup.incident_created", source=_short_name(target), urn=incident_urn[-10:])
    else:
        suffix = t(lang, "sup.simulated") if not live else t(lang, "sup.read_only")
        detail = t(lang, "sup.incident_sim", suffix=suffix, source=_short_name(target or "recommandations_parcelle"))
    steps.append(
        {
            "icon": "✗",
            "state": "action" if live and incident_urn else ("ok" if not live else "warn"),
            "title": t(lang, "sup.title.incident"),
            "detail": detail,
        }
    )

    # 5 — Run tracé sur la recommandation.
    if live:
        try:
            ok = client.emit_run(
                "urn:li:dataset:(urn:li:dataPlatform:duckdb,recommandations_parcelle,PROD)",
                "SUCCESS",
                "Supervision : fraîcheur et incident",
            )
            detail = t(lang, "sup.run_ok") + (" · ✓" if ok else "")
        except Exception:
            ok, detail = False, t(lang, "sup.run_failed")
    else:
        ok, detail = True, t(lang, "sup.run_sim")
    steps.append(
        {
            "icon": "✓" if ok else "✗",
            "state": "ok" if ok else "warn",
            "title": t(lang, "sup.title.run"),
            "detail": detail,
        }
    )

    # 6 — Résolution.
    if live and incident_urn:
        try:
            closed = client.resolve_incident(incident_urn)
            detail = t(lang, "sup.incident_resolved") if closed else t(lang, "sup.incident_open")
        except Exception:
            closed, detail = False, t(lang, "sup.resolve_failed")
    else:
        closed, detail = True, t(lang, "sup.cycle_done")
    steps.append(
        {
            "icon": "✓",
            "state": "ok" if closed else "warn",
            "title": t(lang, "sup.title.resolve"),
            "detail": detail,
        }
    )
    return steps


def _console_html(steps: list[dict[str, str]], lang: str = MS) -> str:
    rows = []
    for i, step in enumerate(steps):
        rows.append(
            f'<div class="console-step {step["state"]}" style="--cs-i:{i};">'
            f'<span class="console-icon">{step["icon"]}</span>'
            f"<div><b>{html.escape(step['title'])}</b>"
            f"<small>{html.escape(step['detail'])}</small></div>"
            f'<span class="console-time">t+{i * _STEP_TIME:.1f}s</span>'
            "</div>"
        )
    return (
        '<div class="supervision-console">'
        f'<div class="console-head"><span>{html.escape(t(lang, "sup.head"))}</span>'
        f"<small>{html.escape(t(lang, 'sup.head2'))}</small></div>"
        f'<div class="console-steps">{"".join(rows)}</div>'
        "</div>"
    )


def render_supervision_console(client: Any | None, graph: dict[str, Any], lang: str = MS) -> None:
    """Bouton de rejeu + affichage séquentiel « live » des étapes."""
    if st.button(
        t(lang, "sup.replay"),
        key="replay_console",
        width="stretch",
    ):
        st.session_state["console_steps"] = replay_supervision(client, graph, lang)
        st.session_state["console_play"] = True

    steps = st.session_state.get("console_steps")
    if not steps:
        return

    container = st.empty()
    if st.session_state.pop("console_play", False):
        for index in range(1, len(steps) + 1):
            container.markdown(_console_html(steps[:index], lang), unsafe_allow_html=True)
            time.sleep(_STEP_TIME)
    else:
        container.markdown(_console_html(steps, lang), unsafe_allow_html=True)
