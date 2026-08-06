import json
from datetime import date

from services.provenance_service import load_graph
from services.recommendation_service import build_recommendation, recompute_margin


def real_parcel():
    """Structure d'une parcelle RPG réelle (IGN API Carto), anonymisée."""
    return {
        "id": "RPG-2023-142",
        "label": "RPG 142 — 18.40 ha — culture inconnue",
        "commune": "Vierzon",
        "code_insee": "18279",
        "surface_ha": 18.4,
        "sol": "limono-argileux",
        "reserve_utile_mm": 140,
        "culture_actuelle": "orge de printemps",
        "source": "IGN API Carto — RPG anonymisé",
    }


def inputs():
    parcel = real_parcel()
    cultures = json.load(open("data/cultures_reference.json", encoding="utf-8"))
    return load_graph("fixtures/graph.json"), parcel, cultures


def test_three_ranked_deterministic_cultures():
    graph, parcel, cultures = inputs()
    first = build_recommendation(graph, parcel, cultures, date(2027, 4, 15), 3, date(2026, 7, 30))
    second = build_recommendation(graph, parcel, cultures, date(2027, 4, 15), 3, date(2026, 7, 30))
    assert first == second
    assert len(first["cultures"]) == 3
    assert [c["rang"] for c in first["cultures"]] == [1, 2, 3]
    assert all(c["besoin_irrigation_mm"] >= 0 for c in first["cultures"])


def test_twelve_months_is_climatological():
    graph, parcel, cultures = inputs()
    result = build_recommendation(graph, parcel, cultures, date(2027, 4, 15), 12, date(2026, 7, 30))
    assert result["confiance"]["fiabilite_prevision"] == "climatologique"
    assert all(item["probabilite"] is None for item in result["fenetre_de_tension"])


def test_insufficient_confidence_empties_cultures():
    graph, parcel, cultures = inputs()
    graph["lineage"] = {}
    result = build_recommendation(graph, parcel, cultures, date(2027, 4, 15), 3, date(2026, 7, 30))
    assert result["cultures"] == []


def test_decomposition_marge_matches_marge_brute():
    graph, parcel, cultures = inputs()
    result = build_recommendation(graph, parcel, cultures, date(2027, 4, 15), 3, date(2026, 7, 30))
    for crop in result["cultures"]:
        d = crop["decomposition_marge"]
        recomputed = recompute_margin(
            crop["besoin_irrigation_mm"],
            d["perte_si_restriction_eur_ha"],
            rendement_qx_ha=d["rendement_qx_ha"],
            prix_eur_qx=d["prix_eur_qx"],
            aides_primes_eur_ha=d["aides_primes_eur_ha"],
            semences_eur_ha=d["semences_eur_ha"],
            fertilisation_eur_ha=d["fertilisation_eur_ha"],
            protection_eur_ha=d["protection_eur_ha"],
            travaux_carburant_eur_ha=d["travaux_carburant_eur_ha"],
            sechage_eur_ha=d["sechage_eur_ha"],
            prestation_eur_ha=0,
            cout_eau_eur_m3=d["cout_eau_eur_m3"],
        )
        assert recomputed["marge_eur_ha"] == crop["marge_brute_eur_ha"]


def test_recompute_margin_adds_prestation_cost():
    base = recompute_margin(100, 0, rendement_qx_ha=30, prix_eur_qx=40, aides_primes_eur_ha=0, semences_eur_ha=50, fertilisation_eur_ha=50, protection_eur_ha=50, travaux_carburant_eur_ha=50, sechage_eur_ha=0, prestation_eur_ha=0, cout_eau_eur_m3=0.1)
    with_prestation = recompute_margin(100, 0, rendement_qx_ha=30, prix_eur_qx=40, aides_primes_eur_ha=0, semences_eur_ha=50, fertilisation_eur_ha=50, protection_eur_ha=50, travaux_carburant_eur_ha=50, sechage_eur_ha=0, prestation_eur_ha=80, cout_eau_eur_m3=0.1)
    assert with_prestation["marge_eur_ha"] == base["marge_eur_ha"] - 80
