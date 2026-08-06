"""Interface Streamlit guidée de Terroir Context Agents."""

from __future__ import annotations

import json
import tempfile
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from services.datahub_client import DataHubClient
from services.provenance_service import load_graph, short_name
from services.data_quality_service import build_quality_certificate
from services.expert_report_service import build_expert_report
from services.real_data_service import PublicDataError, fetch_real_territory, resolve_soil
from services.recommendation_service import build_recommendation, recompute_margin
from services.report_service import build_comparison_report, report_to_csv, save_report
from services.simulation_service import simulate_station_failure
from ui.assolement import (
    INTRO_SLIDES,
    analysis_article,
    intro_slide_html,
    levers_panel,
    no_risk_panel_html,
    render_timeline,
    retain_sentence,
    screen_kicker_html,
    simulation_recap_html,
    tunnel_header_html,
)
from ui.calendar_svg import calendar_svg
from ui.provenance_spine import render_spine
from ui.scenario_timeline import render_crop_scenario
from ui.step_nav import render_step_indicator
from ui.styles import CSS
from ui.weather_scene import compute_header_state, render_header_scene, render_grass_band

ROOT = Path(__file__).resolve().parent
STEP_LABELS = ["Parcelle & résultat", "Scénario météo", "Détails techniques"]
ASSOLEMENT_SCREEN_COUNT = 4
HYDRO_URN = "urn:li:dataset:(urn:li:dataPlatform:duckdb,hubeau_hydrometrie,PROD)"
RECO_URN = "urn:li:dataset:(urn:li:dataPlatform:duckdb,recommandations_parcelle,PROD)"


@st.cache_resource
def get_datahub_client() -> DataHubClient:
    """Client GMS DataHub unique par processus (lecture DATAHUB_GMS_URL/DATAHUB_TOKEN)."""
    return DataHubClient()


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
    """Réinitialise immédiatement l'état visuel de la panne et résout l'incident DataHub."""
    incident_urn = st.session_state.pop("incident_urn", None)
    if incident_urn:
        get_datahub_client().resolve_incident(incident_urn)
    st.session_state.impacted = []
    st.session_state.failure_message = ""
    st.session_state.pop("last_simulation", None)


def go_to_step(step: int) -> None:
    st.session_state.step = step


def go_to_assolement_screen(screen: int) -> None:
    st.session_state.assolement_screen = screen


def assolement_nav() -> None:
    """Navigation du tunnel : écran → écran, puis écran 4 → étape 2 du tunnel principal."""
    screen = st.session_state.assolement_screen
    next_by_screen = {
        1: ("Suivant — La réponse →", 2),
        2: ("Suivant — Comment éviter →", 3),
        3: ("Suivant — D'où viennent ces chiffres →", 4),
    }
    left, right = st.columns(2)
    with left:
        if screen > 1:
            st.button("‹ Précédent", key="tunnel_prev", width="stretch", on_click=go_to_assolement_screen, args=(screen - 1,))
    with right:
        if screen in next_by_screen:
            label, target = next_by_screen[screen]
            st.button(
                label,
                key="tunnel_next",
                type="primary",
                width="stretch",
                disabled=screen == 1 and not bool(st.session_state.get("result", {}).get("cultures")),
                on_click=go_to_assolement_screen,
                args=(target,),
            )
        else:
            st.button("Voir le scénario météo →", key="tunnel_to_step_2", type="primary", width="stretch", on_click=go_to_step, args=(2,))


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
    components = [
        ("Parcelle", "élevée", result.get("parcelle_source", "RPG public anonymisé")),
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
    if soil.get("method") != "mesure_utilisateur":
        missing.append("renseigner une analyse de sol mesurée")
    if result.get("hydro_confidence") != "élevée":
        missing.append("obtenir une mesure récente de la rivière ou de la nappe")
    missing.append("remplacer les prix moyens par vos prix et vos charges")
    st.markdown('<div class="confidence-actions"><strong>Pour atteindre une confiance élevée</strong><ol>' + "".join(f"<li>{item}</li>" for item in missing) + '</ol><p>Le niveau augmente uniquement lorsque ces preuves sont disponibles.</p></div>', unsafe_allow_html=True)


def render_question_screen(graph: dict, culture_specs: list[dict]) -> None:
    """Écran 1 — La question : la parcelle et ses conditions d'accès à l'eau."""
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

    st.markdown('<div class="report-section-kicker">VOTRE PARCELLE</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:16px;font-weight:600;margin-bottom:.9rem;">Ce que vous vous apprêtez à semer aura-t-il soif au moment où il n\'y aura plus d\'eau ?</div>', unsafe_allow_html=True)

    commune_query = st.text_input("Commune", value="Vierzon", help="Saisissez la commune où se trouve votre parcelle.")
    load_real = st.button("Chercher les parcelles", width="stretch")
    if load_real:
        try:
            with st.spinner("Recherche des parcelles et des stations d’eau…"):
                st.session_state.real_territory = fetch_real_territory(commune_query)
            st.success(f"{len(st.session_state.real_territory.parcels)} parcelle(s) trouvée(s).")
        except PublicDataError as exc:
            st.error(f"Impossible de charger les données publiques. {exc}")

    territory = st.session_state.get("real_territory")
    if territory is None:
        st.info("Saisissez une commune puis cliquez sur « Chercher les parcelles » pour charger les parcelles réelles du RPG.")
        return
    st.caption(f"RPG {territory.rpg_year} · INSEE {territory.commune['code']}")

    selected_label = st.selectbox("Parcelle", [p["label"] for p in territory.parcels])
    sowing = st.date_input("Date de semis envisagée", value=date(2027, 4, 15))
    horizon = st.segmented_control("Durée étudiée", [3, 6, 12], default=3, format_func=lambda value: f"{value} mois") or 3
    st.caption("3 mois : le plus fiable · 6 mois : plus incertain · 12 mois : tendance climatique")
    parcel = next(p for p in territory.parcels if p["label"] == selected_label)

    with st.spinner("Recherche des informations de sol…"):
        resolved_soil = cached_resolve_soil(parcel)
    parcel = dict(parcel, sol=resolved_soil.soil_type, reserve_utile_mm=resolved_soil.reserve_utile_mm, soil_resolution={"method": resolved_soil.method, "source": resolved_soil.source, "confidence": resolved_soil.confidence, "detail": resolved_soil.detail})
    st.markdown(
        '<div class="om-soil-card">'
        '<div class="om-soil-kicker">Analyse de sol de la parcelle</div>'
        '<div class="om-soil-grid">'
        f'<div><span>Sol</span><strong>{resolved_soil.soil_type}</strong></div>'
        f'<div><span>Réserve utile</span><strong>{resolved_soil.reserve_utile_mm} mm</strong></div>'
        f'<div><span>Confiance</span><strong class="lvl-{resolved_soil.confidence}">{resolved_soil.confidence}</strong></div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    with st.expander("J’ai une analyse de sol plus précise"):
        known_soil = st.selectbox("Type de sol mesuré", [resolved_soil.soil_type, "limono-argileux", "limoneux", "argileux", "sableux", "autre / inconnu"])
        known_ru = st.number_input("Réserve utile mesurée (mm)", 30, 250, resolved_soil.reserve_utile_mm, 5)
        if st.checkbox("Utiliser mon analyse"):
            parcel = dict(parcel, sol=known_soil, reserve_utile_mm=int(known_ru), soil_resolution={"method": "mesure_utilisateur", "source": "analyse utilisateur", "confidence": "haute", "detail": "Analyse déclarée comme mesurée."})

    parcel_line_facts = f'<span>{parcel["commune"]}</span><span>{parcel["surface_ha"]} ha</span><span>{parcel["sol"]}</span><span>RU {parcel["reserve_utile_mm"]} mm</span>'
    st.markdown(f'<div class="parcel-line">{parcel_line_facts}</div>', unsafe_allow_html=True)
    calculate = st.button("Comparer les cultures pour cette parcelle", type="primary", width="stretch")
    if calculate:
        result = build_recommendation(graph, parcel, culture_specs, sowing, horizon, date(2026, 7, 30))
        result["mode_donnees"] = "reel_hybride"
        result["parcelle_source"] = parcel.get("source", "RPG public anonymisé")
        result["soil_resolution"] = parcel.get("soil_resolution")
        stations = territory.hydro_stations
        result["hydro_confidence"] = "moyenne" if stations else "faible"
        result["hydro_detail"] = f"Station {stations[0].get('code_station')} identifiée." if stations else "Aucune station en service associée."
        result["resolution_log"] = territory.resolution_log
        st.session_state.result = result
        st.session_state.impacted = []
        st.session_state.failure_message = ""
        crops = result["cultures"]
        best = crops[0] if crops else None
        summary = f"{len(crops)} culture(s) comparée(s) pour {result['parcelle_id']}"
        if best:
            summary += f" — {best['culture']} recommandée (marge {best['marge_brute_eur_ha']:.0f} €/ha, état {best['etat']})"
        get_datahub_client().emit_run(RECO_URN, "SUCCESS", summary)


def archive_report(result: dict, simulated_by_culture: dict) -> None:
    """Génère et archive le rapport (callback on_click : exécuté avant le rerun)."""
    report = build_comparison_report(result, simulated_by_culture)
    try:
        report_path = save_report(report, ROOT / "reports", date(2026, 7, 30))
        archive_dir = ROOT / "reports"
    except OSError:
        report_path = save_report(report, tempfile.gettempdir(), date(2026, 7, 30))
        archive_dir = Path(tempfile.gettempdir())
    st.session_state.last_report = report
    st.session_state.last_report_path = str(report_path)
    st.session_state.last_report_dir = str(archive_dir)


def render_answer_screen(result: dict) -> None:
    """Écran 2 — La réponse : confiance, calendrier, analyse et chiffrage."""
    st.markdown(screen_kicker_html("LA RÉPONSE"), unsafe_allow_html=True)
    confidence_notice(result)
    quality = build_quality_certificate(result)
    st.markdown(f'<section class="trust-banner"><div><span>CERTIFICAT DES DONNÉES</span><strong>{quality["statement"]}</strong><p>Traçabilité vérifiée : <b>{"oui" if quality["lineage_verified"] else "non"}</b> · garanties élevées : <b>{quality["verified_count"]}/{quality["total_count"]}</b>.</p></div><div class="trust-seal">{quality["verified_count"]}/{quality["total_count"]}<small>preuves fortes</small></div></section>', unsafe_allow_html=True)
    if not result["cultures"]:
        st.info("Aucune culture ne peut être chiffrée avec ce niveau de confiance.")
        return

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
    edited_df = st.data_editor(pd.DataFrame(sim_input_rows), hide_index=True, width="stretch", key="simulation_editor")
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
        if st.session_state.get("last_report"):
            st.success("Rapport archivé — le CSV est prêt à droite.")
        else:
            st.button("Générer et archiver le rapport", width="stretch", on_click=archive_report, args=(result, simulated_by_culture))
    with report_download_col:
        if st.session_state.get("last_report"):
            st.download_button(
                "Télécharger le rapport (CSV)",
                data=report_to_csv(st.session_state.last_report),
                file_name=f"comparaison_{result['parcelle_id']}.csv",
                mime="text/csv",
                width="stretch",
            )
    st.markdown('</div>', unsafe_allow_html=True)


def render_avoid_screen(result: dict) -> None:
    """Écran 3 — Comment éviter : les leviers d'action et le panneau « pas de risque »."""
    st.markdown(screen_kicker_html("COMMENT ÉVITER"), unsafe_allow_html=True)
    if not result["cultures"]:
        st.info("Aucune culture à analyser.")
        return
    at_risk_crops = [c for c in result["cultures"] if c["etat"] != "sûr"]
    risky = max(at_risk_crops, key=lambda c: c["recouvrement_avec_tension_j"]) if at_risk_crops else None
    if risky:
        st.markdown(levers_panel(risky), unsafe_allow_html=True)
    else:
        st.markdown(no_risk_panel_html(), unsafe_allow_html=True)


def datahub_banner_html(graph: dict) -> str:
    """Bandeau DataHub de l'écran 4 : connexion GMS + fraîcheur des sources lue dans le graphe."""
    client = get_datahub_client()
    source_urns = [urn for urn in graph["datasets"] if urn not in {t for v in graph["lineage"].values() for t in v}]
    edges = sum(len(targets) for targets in graph["lineage"].values())
    if not client.enabled:
        return (
            '<div class="datahub-banner datahub-off"><span class="datahub-dot"></span><div>'
            "<strong>Graphe de contexte DataHub — mode démonstration locale</strong>"
            f"<p>L'agent fonctionne sur <code>fixtures/graph.json</code> ({len(source_urns)} sources, {edges} relations de lineage). Définissez <code>DATAHUB_GMS_URL</code> pour lire la fraîcheur dans DataHub et écrire runs et incidents dans le graphe.</p>"
            "</div></div>"
        )
    if not client.connected():
        return (
            '<div class="datahub-banner datahub-off"><span class="datahub-dot"></span><div>'
            "<strong>Graphe DataHub injoignable</strong>"
            f"<p>Repli local : les métadonnées de <code>fixtures/graph.json</code> sont utilisées. <code>{client.gms_url}</code> ne répond pas.</p>"
            "</div></div>"
        )
    freshness = client.freshness_summary(source_urns)
    badges = []
    for urn in source_urns:
        info = freshness["sources"].get(urn, {})
        name = short_name(urn)
        if info.get("status") == "stale":
            badges.append(f'<b style="color:var(--vigilance)">{name}</b><span>dépassé de {info["delta_days"]} j (SLA {info["sla_days"]} j)</span>')
        elif info.get("status") == "ok":
            badges.append(f"<b>{name}</b><span>à jour</span>")
        else:
            badges.append(f"<b>{name}</b><span>inconnue</span>")
    badges_html = "".join(f"<div>{badge}</div>" for badge in badges)
    return (
        '<div class="datahub-banner"><span class="datahub-dot"></span><div>'
        f"<strong>Graphe de contexte DataHub — connecté ({client.gms_url})</strong>"
        f"<p>Fraîcheur des {len(source_urns)} sources lue dans DataHub : {freshness['ok']} à jour · {freshness['stale']} en dépassement de SLA · {freshness['unknown']} inconnues · {edges} relations de lineage.</p>"
        f'<div class="datahub-src">{badges_html}</div>'
        "</div></div>"
    )


def render_provenance_screen(result: dict, graph: dict) -> None:
    """Écran 4 — D'où viennent ces chiffres : l'épine de données, le certificat et la vue experte."""
    st.markdown(screen_kicker_html("D'OÙ VIENNENT CES CHIFFRES ?"), unsafe_allow_html=True)
    quality = build_quality_certificate(result)
    confidence_notice(result)
    st.markdown(f'<section class="trust-banner"><div><span>CERTIFICAT DES DONNÉES</span><strong>{quality["statement"]}</strong><p>Traçabilité vérifiée : <b>{"oui" if quality["lineage_verified"] else "non"}</b> · garanties élevées : <b>{quality["verified_count"]}/{quality["total_count"]}</b>.</p></div><div class="trust-seal">{quality["verified_count"]}/{quality["total_count"]}<small>preuves fortes</small></div></section>', unsafe_allow_html=True)
    st.markdown(datahub_banner_html(graph), unsafe_allow_html=True)
    st.markdown('<div class="assolement-spine-full">', unsafe_allow_html=True)
    st.markdown(render_spine(graph, set(st.session_state.get("impacted", []))), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="report-subhead">Détails techniques et vue experte</div>', unsafe_allow_html=True)
    with st.expander("Voir tous les chiffres et la confiance", expanded=False):
        confidence_dashboard(result)
        st.markdown('<div class="quality-list">' + "".join(f'<div class="quality-{item["level"]}"><span>{item["name"]}</span><b>{item["level"]}</b><small>{item["evidence"]}</small></div>' for item in quality["checks"]) + '</div>', unsafe_allow_html=True)
        st.dataframe([{"Culture": crop["culture"], "Jours à risque": crop["recouvrement_avec_tension_j"], "Eau (mm)": crop["besoin_irrigation_mm"], "Budget irrigation (€/ha)": crop["cout_eau_eur_ha"], "Résultat estimé (€/ha)": crop["marge_brute_eur_ha"]} for crop in result["cultures"]], hide_index=True, width="stretch")
    with st.expander("Sources de secours essayées"):
        for attempt in result.get("resolution_log", []):
            symbol = "✓" if "utilisée" in attempt["status"] else "→"
            st.write(f'{symbol} **{attempt["field"].capitalize()}** — {attempt["source"]} : {attempt["status"]}')
    with st.expander("Vue experte : audit des données et des modèles"):
        expert = build_expert_report(result)
        st.markdown(f'<div class="expert-heading"><div><span>SCORE TECHNIQUE MOYEN</span><strong>{expert["overall_score"]}/100</strong></div><p>Ce score résume la qualité technique des entrées. Il ne prédit pas le rendement futur.</p></div>', unsafe_allow_html=True)
        collected_tab, failed_tab, models_tab, scores_tab = st.tabs(["Données collectées", "Sources en échec", "Modèles utilisés", "Scores"])
        with collected_tab:
            st.dataframe(expert["collected"], hide_index=True, width="stretch")
        with failed_tab:
            if expert["failures"]:
                st.dataframe(expert["failures"], hide_index=True, width="stretch")
            else:
                st.success("Aucun échec de source enregistré sur cette exécution.")
        with models_tab:
            st.dataframe(expert["models"], hide_index=True, width="stretch")
            with st.expander("Paramètres du scénario"):
                st.json({"parcelle": result["parcelle_id"], "semis": result["date_semis"], "horizon_mois": result["horizon_mois"], "sol": result["sol"], "fenetre_de_tension": result["fenetre_de_tension"]})
        with scores_tab:
            st.caption("Barème : élevée = 100, moyenne = 65, faible = 30, insuffisante = 0.")
            st.dataframe(expert["scores"], hide_index=True, width="stretch")


st.set_page_config(page_title="Terroir Context Agents", layout="wide", initial_sidebar_state="collapsed")
st.markdown(CSS, unsafe_allow_html=True)

try:
    graph = load_graph(ROOT / "fixtures/graph.json")
    culture_specs = load_json(ROOT / "data/cultures_reference.json")
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
if "assolement_screen" not in st.session_state:
    st.session_state.assolement_screen = 1
if "result" not in st.session_state and st.session_state.assolement_screen > 1:
    st.session_state.assolement_screen = 1

if step > 1:
    st.markdown(render_step_indicator(step, STEP_LABELS), unsafe_allow_html=True)

# --- Étape 1 : tunnel assolement en 4 écrans ------------------------------
if step == 1:
    st.markdown(tunnel_header_html(st.session_state.assolement_screen, ASSOLEMENT_SCREEN_COUNT), unsafe_allow_html=True)
    if st.session_state.assolement_screen == 4:
        with st.container(key="om_wide"):
            render_provenance_screen(st.session_state.result, graph)
    else:
        with st.container(key="om_screen"):
            if st.session_state.assolement_screen == 1:
                render_question_screen(graph, culture_specs)
            elif st.session_state.assolement_screen == 2:
                render_answer_screen(st.session_state.result)
            else:
                render_avoid_screen(st.session_state.result)
    assolement_nav()

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
        st.session_state.incident_urn = get_datahub_client().create_incident(
            "Panne simulée : station hydrométrique hors délai",
            f"{simulation['invalidated']} recommandation(s) invalidée(s) — impact propagé le long du lineage : hubeau_hydrometrie → features_bilan_hydrique → scenarios_cultures → recommandations_parcelle.",
            HYDRO_URN,
        )
        st.rerun()
    if st.session_state.get("failure_message"):
        simulation = st.session_state.get("last_simulation", {})
        st.error(st.session_state.failure_message)
        if st.session_state.get("incident_urn"):
            st.caption(f"Incident ouvert dans le graphe DataHub : {st.session_state['incident_urn']}")
        impacted_names = [urn.split(",")[1] if "," in urn else urn for urn in simulation.get("impacted", [])]
        st.markdown('<div class="failure-flow"><span><b>1</b> hubeau_hydrometrie<br><small>station simulée hors délai</small></span><i>→</i><span><b>2</b> features_bilan_hydrique<br><small>calcul d’eau invalidé</small></span><i>→</i><span><b>3</b> scenarios_cultures<br><small>scénarios invalidés</small></span><i>→</i><span><b>4</b> recommandations<br><small>résultats barrés</small></span></div>', unsafe_allow_html=True)
        st.write("**Éléments touchés :** " + ", ".join(impacted_names))
        if simulation.get("report_path"):
            st.code(simulation["report_path"], language=None)
        st.button("Rétablir la station et recalculer", type="primary", width="stretch", on_click=restore_station)

    st.markdown(render_grass_band(), unsafe_allow_html=True)
    st.markdown('<div class="final-warning"><strong>Avant de décider</strong><p>Confirmez l’analyse de sol, vos prix, vos charges, votre accès à l’eau et la place de la culture dans votre rotation avec votre conseiller.</p></div>', unsafe_allow_html=True)

    step_nav(prev_step=2, prev_label="← Retour au scénario météo")
