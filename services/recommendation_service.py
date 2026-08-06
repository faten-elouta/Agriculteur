"""Calculs agronomiques déterministes de la démonstration."""

from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Any

from .confidence_service import evaluate_confidence


def _overlap(a: date, b: date, c: date, d: date) -> int:
    return max(0, (min(b, d) - max(a, c)).days + 1)


def recompute_margin(besoin_irrigation_mm: float, perte_si_restriction_eur_ha: float, *, rendement_qx_ha: float, prix_eur_qx: float, aides_primes_eur_ha: float, semences_eur_ha: float, fertilisation_eur_ha: float, protection_eur_ha: float, travaux_carburant_eur_ha: float, sechage_eur_ha: float, prestation_eur_ha: float, cout_eau_eur_m3: float) -> dict[str, float]:
    """Recalcule la marge à partir de chiffres saisis par l'agriculteur.

    Le stade critique, le recouvrement avec la tension et la perte de restriction
    restent ceux du scénario calculé : seule la partie économique est modifiable ici.
    """
    produit = rendement_qx_ha * prix_eur_qx + aides_primes_eur_ha
    charges = semences_eur_ha + fertilisation_eur_ha + protection_eur_ha + travaux_carburant_eur_ha + sechage_eur_ha + prestation_eur_ha
    irrigation = besoin_irrigation_mm * 10 * cout_eau_eur_m3
    marge = produit - charges - irrigation - perte_si_restriction_eur_ha
    return {"produit_eur_ha": round(produit, 0), "charges_eur_ha": round(charges, 0), "irrigation_eur_ha": round(irrigation, 0), "marge_eur_ha": round(marge, 0)}


def _daily_temperature(day: date, horizon: int) -> float:
    seasonal = 11.8 + 8.9 * math.sin(2 * math.pi * (day.timetuple().tm_yday - 105) / 365)
    return seasonal + {3: 1.2, 6: 0.8, 12: 0.5}[horizon]


def _date_at_degree_days(sowing: date, threshold: int, base: float, horizon: int) -> date:
    total = 0.0
    day = sowing
    for _ in range(400):
        total += max(0.0, _daily_temperature(day, horizon) - base)
        if total >= threshold:
            return day
        day += timedelta(days=1)
    raise ValueError("Seuil de degrés-jours non atteint dans les 400 jours.")


def _tension_window(sowing: date, horizon: int) -> tuple[date, date]:
    year = sowing.year if sowing.month <= 8 else sowing.year + 1
    start = date(year, 7, {3: 1, 6: 6, 12: 10}[horizon])
    return start, start + timedelta(days={3: 61, 6: 55, 12: 49}[horizon])


def _lever_actions(name: str, sowing: date, critical_start: date, critical_end: date, tension: tuple[date, date], harvest: date, overlap: int, irrigation: float) -> list[dict[str, Any]]:
    if overlap == 0:
        return []
    early = sowing - timedelta(days=21)
    early_overlap = _overlap(critical_start - timedelta(days=21), critical_end - timedelta(days=21), *tension)
    short_overlap = _overlap(critical_start - timedelta(days=12), critical_end - timedelta(days=18), *tension)
    items = [
        {"type": "decaler_semis", "action": f"Avancer le semis au {early.strftime('%d/%m')}", "recouvrement_apres_j": early_overlap, "recolte_apres": (harvest - timedelta(days=21)).isoformat(), "gain_marge_eur_ha": round((overlap - early_overlap) * 7.0, 0), "faisabilite": "immediate", "reserve": "Vérifier la portance du sol."},
        {"type": "variete_plus_precoce", "action": "Choisir une variété plus précoce", "recouvrement_apres_j": short_overlap, "recolte_apres": (harvest - timedelta(days=18)).isoformat(), "gain_marge_eur_ha": round((overlap - short_overlap) * 6.0, 0), "faisabilite": "a_verifier", "reserve": "Disponibilité variétale à confirmer."},
        {"type": "securiser_irrigation", "action": f"Sécuriser {round(irrigation * 10):.0f} m³/ha", "recouvrement_apres_j": 0, "recolte_apres": harvest.isoformat(), "gain_marge_eur_ha": round(overlap * 8.0, 0), "faisabilite": "sous_autorisation", "reserve": "Sous autorisation de prélèvement."},
    ]
    return sorted(items, key=lambda x: (x["recouvrement_apres_j"], -x["gain_marge_eur_ha"]))[:3]


def build_recommendation(graph: dict[str, Any], parcel: dict[str, Any], cultures: list[dict[str, Any]], sowing: date, horizon: int, today: date) -> dict[str, Any]:
    """Produit une réponse O1; aucun chiffre n'est généré hors de ces formules."""
    confidence = evaluate_confidence(graph, today, horizon)
    base: dict[str, Any] = {"parcelle_id": parcel["id"], "commune": parcel["commune"], "surface_ha": parcel["surface_ha"], "sol": {"type": parcel["sol"], "reserve_utile_mm": parcel["reserve_utile_mm"], "autonomie_jours_sans_irrigation": round(parcel["reserve_utile_mm"] / 5)}, "date_semis": sowing.isoformat(), "horizon_mois": horizon, "genere_le": today.isoformat(), "fenetre_de_tension": [], "cultures": [], "confiance": {"niveau": confidence.niveau, "motifs": confidence.motifs, "fiabilite_prevision": confidence.fiabilite_prevision}, "provenance": {"datasets_amont": confidence.sources, "modele": {"urn": "urn:li:mlModel:(urn:li:dataPlatform:duckdb,gr4j_cher_v1,PROD)", "version": "1.0.0", "bassin_calibration": "Cher amont"}, "run_urn": f"urn:li:dataProcessInstance:terroir-{today.isoformat()}-{parcel['id']}", "chaine_lineage_verifiee": confidence.niveau != "insuffisante"}}
    if confidence.niveau == "insuffisante":
        return base
    tension = _tension_window(sowing, horizon)
    cursor = date(tension[0].year, tension[0].month, 1)
    while cursor <= tension[1]:
        base["fenetre_de_tension"].append({"mois": cursor.strftime("%Y-%m"), "intensite": "forte", "probabilite": None if horizon == 12 else {3: 0.72, 6: 0.58}[horizon], "origine": "prevision_saisonniere"})
        cursor = date(cursor.year + (cursor.month == 12), 1 if cursor.month == 12 else cursor.month + 1, 1)
    computed = []
    for spec in cultures:
        levee = _date_at_degree_days(sowing, spec["thresholds"][0], spec["t_base"], horizon)
        critical_start = _date_at_degree_days(sowing, spec["thresholds"][1], spec["t_base"], horizon)
        critical_end = _date_at_degree_days(sowing, spec["thresholds"][2], spec["t_base"], horizon)
        maturity = _date_at_degree_days(sowing, spec["thresholds"][3], spec["t_base"], horizon)
        harvest = maturity + timedelta(days=spec["harvest_lag"])
        overlap = _overlap(critical_start, critical_end, *tension)
        cycle = (harvest - sowing).days
        crop_need = spec["etm_mm"]
        effective_rain = {3: 205, 6: 220, 12: 230}[horizon] + parcel["reserve_utile_mm"] * 0.55
        irrigation = max(0.0, crop_need - effective_rain)
        water_cost = irrigation * 10 * spec["water_price"]
        restriction_loss = overlap * spec["loss_day"]
        produit = spec["yield_qx"] * spec["price_qx"] + spec["aides_primes_eur_ha"]
        charges = spec["semences_eur_ha"] + spec["fertilisation_eur_ha"] + spec["protection_eur_ha"] + spec["travaux_carburant_eur_ha"] + spec["sechage_eur_ha"]
        margin = produit - charges - water_cost - restriction_loss
        state = "sûr" if overlap == 0 else "vigilance" if overlap <= 14 else "rupture"
        decomposition_marge = {
            "rendement_qx_ha": spec["yield_qx"],
            "prix_eur_qx": spec["price_qx"],
            "aides_primes_eur_ha": spec["aides_primes_eur_ha"],
            "produit_eur_ha": round(produit, 0),
            "semences_eur_ha": spec["semences_eur_ha"],
            "fertilisation_eur_ha": spec["fertilisation_eur_ha"],
            "protection_eur_ha": spec["protection_eur_ha"],
            "travaux_carburant_eur_ha": spec["travaux_carburant_eur_ha"],
            "sechage_eur_ha": spec["sechage_eur_ha"],
            "irrigation_eur_ha": round(water_cost, 0),
            "cout_eau_eur_m3": spec["water_price"],
            "charges_hors_eau_eur_ha": round(charges, 0),
            "perte_si_restriction_eur_ha": round(restriction_loss, 0),
        }
        item = {"culture": spec["name"], "rang": 0, "deja_cultivee_sur_parcelle": spec["name"] == parcel.get("culture_actuelle"), "calendrier": {"semis": sowing.isoformat(), "levee": levee.isoformat(), "stade_critique": {"nom": spec["critical_name"], "debut": critical_start.isoformat(), "fin": critical_end.isoformat()}, "maturite": maturity.isoformat(), "recolte_estimee": harvest.isoformat(), "duree_cycle_j": cycle, "incertitude_recolte_j": {3: 10, 6: 15, 12: 24}[horizon]}, "recouvrement_avec_tension_j": overlap, "verdict": "cycle_termine_avant" if overlap == 0 else "pic_decale" if overlap <= 14 else "pic_en_pleine_tension", "etat": state, "besoin_irrigation_mm": round(irrigation, 1), "cout_eau_eur_ha": round(water_cost, 0), "marge_brute_eur_ha": round(margin, 0), "perte_si_restriction_eur_ha": round(restriction_loss, 0), "adaptation_au_sol": spec["soil_fit"], "decomposition_marge": decomposition_marge, "leviers": _lever_actions(spec["name"], sowing, critical_start, critical_end, tension, harvest, overlap, irrigation)}
        computed.append(item)
    computed.sort(key=lambda x: (x["recouvrement_avec_tension_j"], -x["marge_brute_eur_ha"]))
    for rank, item in enumerate(computed, 1):
        item["rang"] = rank
    base["cultures"] = computed
    return base
