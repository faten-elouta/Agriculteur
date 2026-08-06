"""Orchestration de la panne hors ligne via l'agent Sentinelle existant."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from agents.sentinelle import OfflineBackend, Sentinelle
from .provenance_service import short_name


def simulate_station_failure(fixture: str | Path, reports: str | Path, recommendation_count: int, today: date) -> dict[str, Any]:
    backend = OfflineBackend(str(fixture), apply_writes=True)
    agent = Sentinelle(backend, today=today)
    findings = agent.scan(simulate_stale="hubeau_hydrometrie")
    finding = next((item for item in findings if "hubeau_hydrometrie" in item.asset_urn), None)
    if finding is None:
        raise RuntimeError("La Sentinelle n'a pas détecté la panne simulée.")
    report = agent.act(finding)
    report.impact["recommandations_invalidees"] = recommendation_count
    out_dir = Path(reports)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"impact_{today.isoformat()}_station.json"
    path.write_text(report.to_json(), encoding="utf-8")
    impacted = [finding.asset_urn, *finding.downstream]
    return {"report_path": str(path), "invalidated": recommendation_count if any(short_name(u) == "recommandations_parcelle" for u in finding.downstream) else 0, "impacted": impacted, "finding": finding}
