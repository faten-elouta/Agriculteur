"""Interface Streamlit guidée de Terroir Context Agents."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from services.provenance_service import load_graph
from services.data_quality_service import build_quality_certificate
from services.expert_report_service import build_expert_report
from services.real_data_service import PublicDataError, fetch_real_territory, resolve_soil
from services.recommendation_service import build_recommendation, recompute_margin
from services.report_service import build_comparison_report, report_to_csv, save_report
from services.simulation_service import simulate_station_failure
from ui.assolement import INTRO_SLIDES, analysis_article, intro_slide_html, levers_panel, render_timeline, retain_sentence, simulation_recap_html
from ui.calendar_svg import calendar_svg
from ui.provenance_spine import render_spine
from ui.scenario_timeline import render_crop_scenario
from ui.step_nav import render_step_indicator
from ui.styles import CSS
from ui.weather_scene import compute_header_state, render_header_scene, render_grass_band

ROOT = Path(__file__).resolve().parent
STEP_LABELS = ["Parcelle & résultat", "Scénario météo", "Détails techniques"]


@st.cache_data(ttl=86_400, show_spinner=False)
def cached_resolve_soil(parcel: dict):
    """Évite de rappeler les sources pédologiques à chaque rerun Streamlit."""
    return resolve_soil(parcel)


def load_json(path: Path) -> list[dict]:
    """Charge une liste JSON de démonstration avec une erreur compréhensible."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Données illisibles : {path.name}") from exc
    if not isinstance(value, list) or not value:
        raise RuntimeError(f"Données invalides : {path.name}")
    return value


def restore_station() -> None:
    """Réinitialise immédiatement l'état visuel de la panne."""
    st.session_state.impacted = []
    st.session_state.failure_message = ""
    st.session_state.pop("last_simulation", None)


def go_to_step(step: int) -> None:
    st.session_state.step = step


def step_nav(prev_step: int | None = None, prev_label: str = "← Précédent", next_step: int | None = None, next_label: str = "Suivant →", next_disabled: bool = False) -> None:
    """Boutons Précédent/Suivant en bas d'une étape."""
    left, right = st.columns(2)
    with left:
        if prev_step is not None:
            st.button(prev_label, key=f"nav_prev_{prev_step}", width="stretch", on_click=go_to_step, args=(prev_step,))
    with right:
        if next_step is not None:
            st.button(next_label, key=f"nav_next_{next_step}", type="primary", width="stretch", disabled=next_disabled, on_click=go_to_step, args=(next_step,))


def confidence_notice(result: dict) -> None:
    """Explique la confiance en langage courant."""
    level = result["confiance"]["niveau"]
    if level == "haute":
        st.success("Confiance haute — toutes les données sont à jour et traçables.")
    elif level == "degradee":
        st.markdown(
            '<div class="confidence-banner degradee"><strong>À confirmer avec vos chiffres.</strong> '
            "Nous utilisons des prix et des charges moyens. Remplacez-les par vos données avant de décider.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="confidence-banner insuffisante"><strong>Calcul impossible.</strong> '
            + " ".join(result["confiance"]["motifs"])
            + "</div>",
            unsafe_allow_html=True,
        )


def confidence_dashboard(result: dict) -> None:
    """Détaille la confiance sans jamais la gonfler artificiellement."""
    soil = result.get("soil_resolution") or {}
    real = result.get("mode_donnees") == "reel_hybride"
    components = [
        ("Parcelle", "élevée" if real else "faible", "RPG public anonymisé" if real else "Parcelle synthétique"),
        ("Sol", {"mesure_utilisateur": "élevée", "source_secondaire": "moyenne", "interpolation_idw": "faible"}.get(soil.get("method"), "faible"), soil.get("detail", "Aucune analyse associée.")),
        ("Eau disponible", result.get("hydro_confidence", "faible"), result.get("hydro_detail", "Aucune observation récente associée.")),
        ("Météo à venir", "moyenne" if result["horizon_mois"] == 3 else "faible", "Plus on regarde loin, moins la tendance est précise."),
        ("Prix et charges", "moyenne", "Valeurs moyennes à confirmer avec vos propres prix."),
    ]
    order = {"élevée": 3, "moyenne": 2, "faible": 1}
    global_level = min((item[1] for item in components), key=lambda value: order[value])
    st.markdown(f'<div class="confidence-title"><span>CONFIANCE DES DONNÉES</span><strong class="level-{global_level}">{global_level}</strong><p>Le niveau global suit la composante la moins fiable.</p></div>', unsafe_allow_html=True)
    cards = ['<div class="confidence-grid">']
    for name, level, detail in components:
        cards.append(f'<div class="confidence-component level-{level}"><span>{name}</span><strong>{level}</strong><small>{detail}</small></div>')
    cards.append("</div>")
    st.markdown("".join(cards), unsafe_allow_html=True)
    missing = []
    if not real:
        missing.append("charger une parcelle réelle depuis le RPG")
    if soil.get("method") != "mesure_utilisateur":
        missing.append("renseigner une analyse de sol mesurée")
    if result.get("hydro_confidence") != "élevée":
        missing.append("obtenir une mesure récente de la rivière ou de la nappe")
    missing.append("remplacer les prix moyens par vos prix et vos charges")
    st.markdown('<div class="confidence-actions"><strong>Pour atteindre une confiance élevée</strong><ol>' + "".join(f"<li>{item}</li>" for item in missing) + '</ol><p>Le niveau augmente uniquement lorsque ces preuves sont disponibles.</p></div>', unsafe_allow_html=True)


def render_result(result: dict, graph: dict) -> dict | None:
    """Rend le résultat (certificat, calendrier, leviers, simulation, épine) et renvoie les marges simulées."""
    quality = build_quality_certificate(result)
    confidence_notice(result)
    st.markdown(f'<section class="trust-banner"><div><span>CERTIFICAT DES DONNÉES</span><strong>{quality["statement"]}</strong><p>Traçabilité vérifiée : <b>{"oui" if quality["lineage_verified"] else "non"}</b> · garanties élevées : <b>{quality["verified_count"]}/{quality["total_count"]}</b>.</p></div><div class="trust-seal">{quality["verified_count"]}/{quality["total_count"]}<small>preuves fortes</small></div></section>', unsafe_allow_html=True)

    if not result["cultures"]:
        st.info("Aucune culture ne peut être chiffrée avec ce niveau de confiance.")
        return None

    at_risk_crops = [c for c in result["cultures"] if c["etat"] != "sûr"]
    risky = max(at_risk_crops, key=lambda c: c["recouvrement_avec_tension_j"]) if at_risk_crops else None

    dashboard_col, spine_col = st.columns([5, 1.3])
    with dashboard_col:
        st.markdown('<h1 style="font-size:17px;margin:0 0 .3rem;">Choisir sa culture</h1>', unsafe_allow_html=True)
        st.markdown(render_timeline(result), unsafe_allow_html=True)

        st.markdown('<div class="report-section">', unsafe_allow_html=True)
        st.markdown('<div class="report-section-kicker">RAPPORT</div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="margin-bottom:.4rem;">'
            '<div style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.02em;opacity:.55;margin-bottom:4px;">Ce qu\'il faut retenir</div>'
            f'<div style="font-size:15px;font-weight:600;">{retain_sentence(result)}</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown(analysis_article(result), unsafe_allow_html=True)
        st.markdown(levers_panel(risky), unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.02em;opacity:.55;margin:.7rem 0 .2rem;">Simulez avec vos propres chiffres</div>',
            unsafe_allow_html=True,
        )
        st.caption("Remplacez ces valeurs par les vôtres pour les trois cultures d'un coup. Le calendrier et le classement plus haut restent ceux du scénario ; seule la marge simulée change.")
        sim_input_rows = [
            {
                "Culture": crop["culture"].capitalize(),
                "Rendement (q/ha)": float(crop["decomposition_marge"]["rendement_qx_ha"]),
                "Prix (€/q)": float(crop["decomposition_marge"]["prix_eur_qx"]),
                "Aides (€/ha)": float(crop["decomposition_marge"]["aides_primes_eur_ha"]),
                "Semences (€/ha)": float(crop["decomposition_marge"]["semences_eur_ha"]),
                "Fertilisation (€/ha)": float(crop["decomposition_marge"]["fertilisation_eur_ha"]),
                "Protection (€/ha)": float(crop["decomposition_marge"]["protection_eur_ha"]),
                "Travaux/carburant (€/ha)": float(crop["decomposition_marge"]["travaux_carburant_eur_ha"]),
                "Séchage (€/ha)": float(crop["decomposition_marge"]["sechage_eur_ha"]),
                "Prestation (€/ha)": 0.0,
                "Eau (€/m³)": float(crop["decomposition_marge"]["cout_eau_eur_m3"]),
            }
            for crop in result["cultures"]
        ]
        edited_df = st.data_editor(pd.DataFrame(sim_input_rows), hide_index=True, width="stretch", disabled=["Culture"], key="simulation_editor")
        simulated_by_culture = {}
        for crop, row in zip(result["cultures"], edited_df.to_dict("records")):
            d = crop["decomposition_marge"]
            simulated_by_culture[crop["culture"]] = recompute_margin(
                crop["besoin_irrigation_mm"],
                d["perte_si_restriction_eur_ha"],
                rendement_qx_ha=row["Rendement (q/ha)"],
                prix_eur_qx=row["Prix (€/q)"],
                aides_primes_eur_ha=row["Aides (€/ha)"],
                semences_eur_ha=row["Semences (€/ha)"],
                fertilisation_eur_ha=row["Fertilisation (€/ha)"],
                protection_eur_ha=row["Protection (€/ha)"],
                travaux_carburant_eur_ha=row["Travaux/carburant (€/ha)"],
                sechage_eur_ha=row["Séchage (€/ha)"],
                prestation_eur_ha=row["Prestation (€/ha)"],
                cout_eau_eur_m3=row["Eau (€/m³)"],
            )
        st.markdown(simulation_recap_html(result["cultures"], simulated_by_culture), unsafe_allow_html=True)

        st.markdown('<div class="report-subhead">Rapport de comparaison</div>', unsafe_allow_html=True)
        report_action_col, report_download_col = st.columns(2)
        with report_action_col:
            if st.button("Générer et archiver le rapport", width="stretch"):
                report = build_comparison_report(result, simulated_by_culture)
                report_path = save_report(report, ROOT / "reports", date(2026, 7, 30))
                st.session_state.last_report = report
                st.session_state.last_report_path = str(report_path)
        with report_download_col:
            if st.session_state.get("last_report"):
                st.download_button(
                    "Télécharger le rapport (CSV)",
                    data=report_to_csv(st.session_state.last_report),
                    file_name=f"comparaison_{result['parcelle_id']}.csv",
                    mime="text/csv",
                    width="stretch",
                )
        if st.session_state.get("last_report_path"):
            st.caption(f"Dernier rapport archivé : {st.session_state.last_report_path}")
        st.markdown('</div>', unsafe_allow_html=True)
    with spine_col:
        st.markdown('<div class="assolement-spine">', unsafe_allow_html=True)
        st.markdown('<div class="report-section-kicker">SOURCES DE DONNÉES</div>', unsafe_allow_html=True)
        st.markdown(render_spine(graph, set(st.session_state.get("impacted", []))), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    return simulated_by_culture


st.set_page_config(page_title="Terroir Context Agents", layout="wide", initial_sidebar_state="collapsed")
st.markdown(CSS, unsafe_allow_html=True)

try:
    graph = load_graph(ROOT / "fixtures/graph.json")
    parcels = load_json(ROOT / "data/demo_parcels.json")
    culture_specs = load_json(ROOT / "data/demo_cultures.json")
except (ValueError, RuntimeError) as exc:
    st.error(str(exc))
    st.stop()

weather_state = compute_header_state(st.session_state)
st.markdown(
    render_header_scene(weather_state, "PRÉPARER MON PROCHAIN SEMIS", "Quelle culture choisir pour ma parcelle ?"),
    unsafe_allow_html=True,
)

if "step" not in st.session_state:
    st.session_state.step = 1
if st.session_state.step > 1 and "result" not in st.session_state:
    st.session_state.step = 1
step = st.session_state.step

st.markdown(render_step_indicator(step, STEP_LABELS), unsafe_allow_html=True)

# --- Étape 1 : parcelle (gauche) & résultat (droite) ----------------------
if step == 1:
    query_col, result_col = st.columns([0.38, 0.62])
    with query_col:
        if "intro_slide" not in st.session_state:
            st.session_state.intro_slide = 0
        nav_prev, nav_body, nav_next = st.columns([0.12, 0.76, 0.12], vertical_alignment="center")
        with nav_prev:
            if st.button("‹", key="intro_prev", width="stretch"):
                st.session_state.intro_slide = (st.session_state.intro_slide - 1) % len(INTRO_SLIDES)
        with nav_next:
            if st.button("›", key="intro_next", width="stretch"):
                st.session_state.intro_slide = (st.session_state.intro_slide + 1) % len(INTRO_SLIDES)
        with nav_body:
            st.markdown(intro_slide_html(st.session_state.intro_slide), unsafe_allow_html=True)

        data_mode = st.radio(
            "Quelle parcelle voulez-vous utiliser ?",
            ["Réelles", "Démonstration"],
            horizontal=True,
            format_func=lambda value: "Une parcelle réelle" if value == "Réelles" else "Un exemple",
        )
        if data_mode == "Réelles":
            commune_query = st.text_input("Commune", value="Vierzon", help="Saisissez la commune où se trouve votre parcelle.")
            load_real = st.button("Chercher les parcelles", width="stretch")
            if load_real:
                try:
                    with st.spinner("Recherche des parcelles et des stations d’eau…"):
                        st.session_state.real_territory = fetch_real_territory(commune_query)
                    st.success(f"{len(st.session_state.real_territory.parcels)} parcelle(s) trouvée(s).")
                except PublicDataError as exc:
                    st.error(f"Impossible de charger les données publiques. {exc}")
            if "real_territory" in st.session_state:
                territory = st.session_state.real_territory
                available_parcels = territory.parcels
                st.caption(f"RPG {territory.rpg_year} · INSEE {territory.commune['code']}")
            else:
                available_parcels = parcels
                st.caption("Cliquez sur « Chercher les parcelles ». L’exemple de Vierzon reste disponible.")
        else:
            available_parcels = parcels

        selected_label = st.selectbox("Parcelle", [p["label"] for p in available_parcels])
        sowing = st.date_input("Date de semis envisagée", value=date(2027, 4, 15))
        horizon = st.segmented_control("Durée étudiée", [3, 6, 12], default=3, format_func=lambda value: f"{value} mois") or 3
        st.caption("3 mois : le plus fiable · 6 mois : plus incertain · 12 mois : tendance climatique")
        parcel = next(p for p in available_parcels if p["label"] == selected_label)

        if parcel.get("source"):
            with st.spinner("Recherche des informations de sol…"):
                resolved_soil = cached_resolve_soil(parcel)
            parcel = dict(parcel, sol=resolved_soil.soil_type, reserve_utile_mm=resolved_soil.reserve_utile_mm, soil_resolution={"method": resolved_soil.method, "source": resolved_soil.source, "confidence": resolved_soil.confidence, "detail": resolved_soil.detail})
            st.markdown(f'<div class="soil-compact"><span>Sol <b>{resolved_soil.soil_type}</b></span><span>RU <b>{resolved_soil.reserve_utile_mm} mm</b></span><span>Confiance <b>{resolved_soil.confidence}</b></span></div>', unsafe_allow_html=True)
            with st.expander("J’ai une analyse de sol plus précise"):
                known_soil = st.selectbox("Type de sol mesuré", [resolved_soil.soil_type, "limono-argileux", "limoneux", "argileux", "sableux", "autre / inconnu"])
                known_ru = st.number_input("Réserve utile mesurée (mm)", 30, 250, resolved_soil.reserve_utile_mm, 5)
                if st.checkbox("Utiliser mon analyse"):
                    parcel = dict(parcel, sol=known_soil, reserve_utile_mm=int(known_ru), soil_resolution={"method": "mesure_utilisateur", "source": "analyse utilisateur", "confidence": "haute", "detail": "Analyse déclarée comme mesurée."})

        parcel_line_facts = (
            f'<span>{parcel["commune"]}</span><span>{parcel["surface_ha"]} ha</span>'
            if parcel.get("source")
            else f'<span>{parcel["commune"]}</span><span>{parcel["surface_ha"]} ha</span><span>{parcel["sol"]}</span><span>RU {parcel["reserve_utile_mm"]} mm</span>'
        )
        st.markdown(f'<div class="parcel-line">{parcel_line_facts}</div>', unsafe_allow_html=True)
        calculate = st.button("Comparer les cultures pour cette parcelle", type="primary", width="stretch")
        if calculate:
            result = build_recommendation(graph, parcel, culture_specs, sowing, horizon, date(2026, 7, 30))
            result["mode_donnees"] = "reel_hybride" if parcel.get("source") else "demonstration"
            result["parcelle_source"] = parcel.get("source", "synthétique")
            result["soil_resolution"] = parcel.get("soil_resolution")
            territory = st.session_state.get("real_territory") if parcel.get("source") else None
            stations = territory.hydro_stations if territory else []
            result["hydro_confidence"] = "moyenne" if stations else "faible"
            result["hydro_detail"] = f"Station {stations[0].get('code_station')} identifiée." if stations else "Aucune station en service associée."
            result["resolution_log"] = territory.resolution_log if territory else [{"field": "mode", "source": "fixture locale", "status": "utilisée"}]
            st.session_state.result = result
            st.session_state.impacted = []
            st.session_state.failure_message = ""

    with result_col:
        if "result" not in st.session_state:
            st.markdown('<div class="waiting-story"><strong>Votre résultat apparaîtra ici</strong><p>Renseignez votre parcelle à gauche puis cliquez sur « Comparer les cultures ».</p></div>', unsafe_allow_html=True)
        else:
            render_result(st.session_state.result, graph)

    has_cultures = bool(st.session_state.get("result", {}).get("cultures"))
    step_nav(next_step=2, next_label="Voir le scénario météo →", next_disabled=not has_cultures)

# --- Étape 2 : scénario météo dans le temps ------------------------------
elif step == 2:
    result = st.session_state.result
    st.markdown('<div class="article-divider"><span>SCÉNARIO — DU SEMIS À LA RÉCOLTE</span></div>', unsafe_allow_html=True)
    st.caption("Une frise par culture : la météo prévue mois par mois, avec le repère du moment où la culture est la plus exposée.")
    if st.button("▶ Lecture", key="play_timeline"):
        st.session_state.timeline_play_token = st.session_state.get("timeline_play_token", 0) + 1
    play_token = st.session_state.get("timeline_play_token", 0)
    tension_months = {m["mois"] for m in result["fenetre_de_tension"]}
    for crop in result["cultures"]:
        st.markdown(render_crop_scenario(crop, tension_months, play_token), unsafe_allow_html=True)

    with st.expander("Voir le calendrier détaillé"):
        svg, alternative = calendar_svg(result)
        st.markdown(svg, unsafe_allow_html=True)
        st.caption(alternative)

    step_nav(prev_step=1, prev_label="← Retour au résultat", next_step=3, next_label="Voir les détails techniques →")

# --- Étape 3 : détails techniques ----------------------------------------
elif step == 3:
    result = st.session_state.result
    quality = build_quality_certificate(result)

    with st.expander("Voir tous les chiffres et la confiance", expanded=True):
        confidence_dashboard(result)
        st.markdown('<div class="quality-list">' + "".join(f'<div class="quality-{item["level"]}"><span>{item["name"]}</span><b>{item["level"]}</b><small>{item["evidence"]}</small></div>' for item in quality["checks"]) + '</div>', unsafe_allow_html=True)
        st.dataframe([{"Culture": crop["culture"], "Jours à risque": crop["recouvrement_avec_tension_j"], "Eau (mm)": crop["besoin_irrigation_mm"], "Budget irrigation (€/ha)": crop["cout_eau_eur_ha"], "Résultat estimé (€/ha)": crop["marge_brute_eur_ha"]} for crop in result["cultures"]], hide_index=True, width="stretch")
    with st.expander("D’où viennent les données ?"):
        st.markdown(render_spine(graph, set(st.session_state.get("impacted", []))), unsafe_allow_html=True)
        st.markdown("#### Sources de secours essayées")
        for attempt in result.get("resolution_log", []):
            symbol = "✓" if "utilisée" in attempt["status"] else "→"
            st.write(f'{symbol} **{attempt["field"].capitalize()}** — {attempt["source"]} : {attempt["status"]}')

    st.markdown('<div class="expert-divider"><span>VUE EXPERTE</span><h2>Audit des données et des modèles</h2><p>Cette section reste visible pour contrôler exactement ce qui a été collecté, rejeté et calculé.</p></div>', unsafe_allow_html=True)
    expert = build_expert_report(result)
    st.markdown(f'<div class="expert-heading"><div><span>SCORE TECHNIQUE MOYEN</span><strong>{expert["overall_score"]}/100</strong></div><p>Ce score résume la qualité technique des entrées. Il ne prédit pas le rendement futur.</p></div>', unsafe_allow_html=True)
    collected_tab, failed_tab, models_tab, scores_tab = st.tabs(["Données collectées", "Sources en échec", "Modèles utilisés", "Scores"])
    with collected_tab:
        st.write("Valeurs et métadonnées effectivement utilisées dans ce calcul.")
        st.dataframe(expert["collected"], hide_index=True, width="stretch")
    with failed_tab:
        st.write("Sources essayées mais non retenues avant le passage à la source suivante.")
        if expert["failures"]:
            st.dataframe(expert["failures"], hide_index=True, width="stretch")
        else:
            st.success("Aucun échec de source enregistré sur cette exécution.")
    with models_tab:
        st.write("Modèles et formules utilisés pour produire les chiffres.")
        st.dataframe(expert["models"], hide_index=True, width="stretch")
        with st.expander("Paramètres du scénario"):
            st.json({"parcelle": result["parcelle_id"], "semis": result["date_semis"], "horizon_mois": result["horizon_mois"], "sol": result["sol"], "fenetre_de_tension": result["fenetre_de_tension"]})
    with scores_tab:
        st.write("Barème : élevée = 100, moyenne = 65, faible = 30, insuffisante = 0.")
        st.dataframe(expert["scores"], hide_index=True, width="stretch")
        st.caption("Le score moyen ne remplace pas la porte de confiance : une source critique peut bloquer tous les résultats.")

    st.markdown('<section class="sentinel-box"><div><div class="section-kicker">TEST DE SÉCURITÉ</div><h3>Que se passe-t-il si une station ne répond plus ?</h3><p>La Sentinelle suit les calculs dépendants et barre automatiquement les recommandations devenues fragiles.</p></div></section>', unsafe_allow_html=True)
    if st.button("Simuler une panne de station", width="stretch"):
        simulation = simulate_station_failure(ROOT / "fixtures/graph.json", ROOT / "reports", len(result["cultures"]), date(2026, 7, 30))
        st.session_state.impacted = simulation["impacted"]
        st.session_state.failure_message = f"{simulation['invalidated']} recommandations invalidées. Rapport d’impact enregistré."
        st.session_state.last_simulation = simulation
        st.rerun()
    if st.session_state.get("failure_message"):
        simulation = st.session_state.get("last_simulation", {})
        st.error(st.session_state.failure_message)
        impacted_names = [urn.split(",")[1] if "," in urn else urn for urn in simulation.get("impacted", [])]
        st.markdown('<div class="failure-flow"><span><b>1</b> hubeau_hydrometrie<br><small>station simulée hors délai</small></span><i>→</i><span><b>2</b> features_bilan_hydrique<br><small>calcul d’eau invalidé</small></span><i>→</i><span><b>3</b> scenarios_cultures<br><small>scénarios invalidés</small></span><i>→</i><span><b>4</b> recommandations<br><small>résultats barrés</small></span></div>', unsafe_allow_html=True)
        st.write("**Éléments touchés :** " + ", ".join(impacted_names))
        if simulation.get("report_path"):
            st.code(simulation["report_path"], language=None)
        st.button("Rétablir la station et recalculer", type="primary", width="stretch", on_click=restore_station)

    st.markdown(render_grass_band(), unsafe_allow_html=True)
    st.markdown('<div class="final-warning"><strong>Avant de décider</strong><p>Confirmez l’analyse de sol, vos prix, vos charges, votre accès à l’eau et la place de la culture dans votre rotation avec votre conseiller.</p></div>', unsafe_allow_html=True)

    step_nav(prev_step=2, prev_label="← Retour au scénario météo")
