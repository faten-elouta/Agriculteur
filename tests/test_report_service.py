import json
from datetime import date

from services.provenance_service import load_graph
from services.recommendation_service import build_recommendation, recompute_margin
from services.report_service import build_comparison_report, report_to_csv, save_report


def build_result():
    parcel = json.load(open("data/demo_parcels.json", encoding="utf-8"))[0]
    cultures = json.load(open("data/demo_cultures.json", encoding="utf-8"))
    graph = load_graph("fixtures/graph.json")
    return build_recommendation(graph, parcel, cultures, date(2027, 4, 15), 3, date(2026, 7, 30))


def test_report_includes_every_culture_without_simulation():
    result = build_result()
    report = build_comparison_report(result)
    assert [c["culture"] for c in report["cultures"]] == [c["culture"] for c in result["cultures"]]
    assert all("marge_simulee_eur_ha" not in c for c in report["cultures"])


def test_report_attaches_simulated_margin_when_provided():
    result = build_result()
    crop = result["cultures"][0]
    d = crop["decomposition_marge"]
    simulated = recompute_margin(
        crop["besoin_irrigation_mm"], d["perte_si_restriction_eur_ha"],
        rendement_qx_ha=d["rendement_qx_ha"] + 5, prix_eur_qx=d["prix_eur_qx"], aides_primes_eur_ha=d["aides_primes_eur_ha"],
        semences_eur_ha=d["semences_eur_ha"], fertilisation_eur_ha=d["fertilisation_eur_ha"], protection_eur_ha=d["protection_eur_ha"],
        travaux_carburant_eur_ha=d["travaux_carburant_eur_ha"], sechage_eur_ha=d["sechage_eur_ha"], prestation_eur_ha=0,
        cout_eau_eur_m3=d["cout_eau_eur_m3"],
    )
    report = build_comparison_report(result, {crop["culture"]: simulated})
    entry = next(c for c in report["cultures"] if c["culture"] == crop["culture"])
    assert entry["marge_simulee_eur_ha"] == simulated["marge_eur_ha"]


def test_save_report_writes_json_file(tmp_path):
    result = build_result()
    report = build_comparison_report(result)
    path = save_report(report, tmp_path, date(2026, 7, 30))
    assert path.exists()
    assert json.loads(path.read_text(encoding="utf-8"))["parcelle_id"] == result["parcelle_id"]


def test_report_to_csv_has_one_row_per_culture():
    result = build_result()
    report = build_comparison_report(result)
    csv_text = report_to_csv(report)
    lines = [line for line in csv_text.splitlines() if line]
    assert len(lines) == 1 + len(result["cultures"])
