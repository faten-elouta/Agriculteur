import copy
from datetime import date

from services.confidence_service import evaluate_confidence
from services.provenance_service import load_graph, urn_for


def test_expert_source_degrades_confidence():
    result = evaluate_confidence(load_graph("fixtures/graph.json"), date(2026, 7, 30), 3)
    assert result.niveau == "degradee"
    assert any("dire_d_expert" in reason for reason in result.motifs)


def test_twice_sla_hides_numbers():
    graph = copy.deepcopy(load_graph("fixtures/graph.json"))
    graph["datasets"][urn_for(graph, "hubeau_hydrometrie")]["last_updated"] = "2026-07-01"
    result = evaluate_confidence(graph, date(2026, 7, 30), 3)
    assert result.niveau == "insuffisante"
    assert "SLA de 5 j" in " ".join(result.motifs)


def test_broken_lineage_is_insufficient():
    graph = copy.deepcopy(load_graph("fixtures/graph.json"))
    graph["lineage"].pop(urn_for(graph, "scenarios_cultures"))
    assert evaluate_confidence(graph, date(2026, 7, 30), 3).niveau == "insuffisante"
