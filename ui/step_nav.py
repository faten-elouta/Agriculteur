"""Indicateur visuel de progression pour la navigation par étapes."""

from __future__ import annotations

import html


def render_step_indicator(current: int, labels: list[str]) -> str:
    """Rend la piste d'étapes (fait / en cours / à venir)."""
    items = []
    for i, label in enumerate(labels, start=1):
        if i > 1:
            items.append(f'<div class="step-sep{" done" if i - 1 < current else ""}"></div>')
        state = "done" if i < current else ("active" if i == current else "todo")
        items.append(
            f'<div class="step-item {state}"><span class="step-dot">{i}</span>'
            f'<span class="step-label">{html.escape(label)}</span></div>'
        )
    return f'<div class="step-indicator">{"".join(items)}</div>'
