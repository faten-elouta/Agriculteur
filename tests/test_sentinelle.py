from datetime import date

from agents.sentinelle import OfflineBackend, Sentinelle
from services.provenance_service import short_name


def test_station_failure_reaches_recommendations():
    backend = OfflineBackend("fixtures/graph.json")
    findings = Sentinelle(backend, date(2026, 7, 30)).scan(simulate_stale="hubeau_hydrometrie")
    failure = next(f for f in findings if "hubeau_hydrometrie" in f.asset_urn)
    assert failure.severite == "rupture"
    assert "recommandations_parcelle" in {short_name(u) for u in failure.downstream}


def test_act_logs_writes():
    backend = OfflineBackend("fixtures/graph.json", apply_writes=True)
    agent = Sentinelle(backend, date(2026, 7, 30))
    finding = next(f for f in agent.scan(simulate_stale="hubeau_hydrometrie") if "hubeau_hydrometrie" in f.asset_urn)
    report = agent.act(finding)
    assert report.impact["assets_aval"]
    assert backend.writes
