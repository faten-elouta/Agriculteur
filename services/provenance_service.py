"""Lecture et validation du graphe de provenance hors ligne."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def short_name(urn: str) -> str:
    """Retourne le nom lisible d'un URN DataHub."""
    try:
        return urn.split(",")[1]
    except IndexError:
        return urn.rsplit(":", 1)[-1]


def load_graph(path: str | Path) -> dict[str, Any]:
    """Charge une fixture et rejette les structures incomplètes."""
    file_path = Path(path)
    try:
        graph = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Fixture de provenance illisible: {file_path}") from exc
    if not isinstance(graph, dict) or not isinstance(graph.get("datasets"), dict):
        raise ValueError("La fixture doit contenir un objet 'datasets'.")
    if not isinstance(graph.get("lineage"), dict):
        raise ValueError("La fixture doit contenir un objet 'lineage'.")
    required = {"last_updated", "freshness_sla_days", "niveau_de_preuve", "spatial_coverage", "licence"}
    for urn, props in graph["datasets"].items():
        if not isinstance(props, dict) or not required.issubset(props):
            missing = required - set(props if isinstance(props, dict) else {})
            raise ValueError(f"Métadonnées incomplètes pour {urn}: {sorted(missing)}")
    return graph


def urn_for(graph: dict[str, Any], name: str) -> str:
    """Résout un nom court depuis le catalogue, sans chemin métier codé en dur."""
    matches = [urn for urn in graph["datasets"] if short_name(urn) == name]
    if len(matches) != 1:
        raise ValueError(f"Asset introuvable ou ambigu: {name}")
    return matches[0]


def descendants(graph: dict[str, Any], source_urn: str) -> list[str]:
    """Parcourt tout le lineage descendant, cycles compris."""
    seen: list[str] = []
    stack = list(graph["lineage"].get(source_urn, []))
    while stack:
        urn = stack.pop(0)
        if urn in seen:
            continue
        seen.append(urn)
        stack.extend(graph["lineage"].get(urn, []))
    return seen


def upstream_closure(graph: dict[str, Any], target_urn: str) -> set[str]:
    """Retourne tous les datasets amont d'une cible."""
    reverse: dict[str, list[str]] = {}
    for source, targets in graph["lineage"].items():
        for target in targets:
            reverse.setdefault(target, []).append(source)
    seen: set[str] = set()
    stack = list(reverse.get(target_urn, []))
    while stack:
        urn = stack.pop()
        if urn in seen:
            continue
        seen.add(urn)
        stack.extend(reverse.get(urn, []))
    return seen
