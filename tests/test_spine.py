from services.provenance_service import load_graph, upstream_closure, urn_for
from ui.provenance_spine import ORDER, render_spine


def test_spine_covers_every_upstream_dataset():
    graph = load_graph("fixtures/graph.json")
    target = urn_for(graph, "recommandations_parcelle")
    upstream = {urn.split(",")[1] for urn in upstream_closure(graph, target)}
    assert upstream.issubset(set(ORDER))
    assert {"parcelles", "sol_rrp", "ref_agro_economique"} <= set(ORDER)


def test_spine_renders_new_datasets():
    graph = load_graph("fixtures/graph.json")
    out = render_spine(graph)
    for name in ["parcelles", "sol_rrp", "ref_agro_economique", "recommandations_parcelle"]:
        assert f"<strong>{name}</strong>" in out


def test_spine_flags_dire_d_expert_source_as_vigilance():
    graph = load_graph("fixtures/graph.json")
    out = render_spine(graph)
    segment = out.split("ref_agro_economique")[1]
    assert "vigilance" in segment


def test_spine_marks_impacted_assets_as_rupture():
    graph = load_graph("fixtures/graph.json")
    impacted = {"urn:li:dataset:(urn:li:dataPlatform:duckdb,hubeau_hydrometrie,PROD)"}
    out = render_spine(graph, impacted)
    segment = out.split("hubeau_hydrometrie")[1]
    assert "rupture" in segment
