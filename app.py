"""Interface Streamlit guidée de Terroir Context Agents."""

from __future__ import annotations

import html
import json
import tempfile
import time
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from services.datahub_client import DataHubClient
from services.provenance_service import load_graph, short_name
from services.data_quality_service import build_quality_certificate
from services.expert_report_service import build_expert_report
from services.real_data_service import (
    PublicDataError,
    RealTerritory,
    fetch_real_territory,
    resolve_soil,
)
from services.recommendation_service import build_recommendation, recompute_margin
from services.report_service import build_comparison_report, report_to_csv, save_report
from services.simulation_service import simulate_station_failure
from ui.assolement import (
    comparator_html,
    front_page_html,
    intro_slide_html,
    intro_slides,
    levers_panel,
    render_timeline,
    screen_kicker_html,
    simulation_recap_html,
    tunnel_header_html,
    verdict_sentence,
)
from ui.calendar_svg import calendar_svg
from ui.i18n import MS, T
from ui.kpis import kpis_html
from ui.lineage_graph import lineage_html
from ui.parcel_map import render_parcel_map
from ui.provenance_spine import render_spine
from ui.scenario_timeline import render_crop_scenario
from ui.step_nav import render_step_indicator
from ui.supervision_console import render_supervision_console
from ui.water_chart import render_water_chart
from ui.site_sections import (
    approach_html,
    about_html,
    cta_html,
    expertise_html,
    footer_html,
    hero_html,
    navbar_html,
    section_header_html,
    stats_band_html,
    values_html,
)
from ui.styles import CSS
from ui.weather_scene import render_grass_band
from ui import animations as anim

ROOT = Path(__file__).resolve().parent
ASSOLEMENT_SCREEN_COUNT = 2
HYDRO_URN = "urn:li:dataset:(urn:li:dataPlatform:duckdb,hubeau_hydrometrie,PROD)"
RECO_URN = "urn:li:dataset:(urn:li:dataPlatform:duckdb,recommandations_parcelle,PROD)"

# Mode démo auto : séquence des écrans rejoués pour la vidéo de soumission.
DEMO_SEQUENCE = [
    ("assolement_screen", 1),
    ("assolement_screen", 2),
    ("step", 2),
    ("step", 3),
]
DEMO_STEP_SECONDS = 3.2


def step_labels() -> list[str]:
    """Libellés des étapes du tunnel principal, traduits selon la langue de session."""
    return [T("steps.label1"), T("steps.label2"), T("steps.label3")]


def _demo_parcel() -> dict:
    """Parcelle de démonstration autonome (géométrie locale, aucune API externe)."""
    return {
        "id": "RPG-2025-DEMO",
        "label": "La Mare au Loup — démonstration",
        "commune": "Vierzon",
        "surface_ha": 12.5,
        "sol": "limono-argileux",
        "reserve_utile_mm": 92,
        "culture_actuelle": "blé tendre",
        "source": "parcelle de démonstration (hors réseau)",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[2.05, 47.22], [2.062, 47.22], [2.062, 47.212], [2.05, 47.212], [2.05, 47.22]]],
        },
    }


def _demo_territory() -> RealTerritory:
    """Territoire de démo : 1 parcelle + 2 stations fictives, sans réseau."""
    return RealTerritory(
        commune={"code": "18279", "nom": "Vierzon", "centre": {"type": "Point", "coordinates": [2.05, 47.22]}},
        parcels=[_demo_parcel()],
        hydro_stations=[
            {"code_station": "K5210010", "libelle_station": "Cher à Vierzon", "longitude": 2.0506, "latitude": 47.2212, "source_type": "hydrometrie"},
            {"code_station": "BSS004QVEA", "libelle_station": "Puits de démonstration", "longitude": 2.0565, "latitude": 47.2155, "source_type": "piezometrie"},
        ],
        fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        rpg_year=2025,
        resolution_log=[{"field": "commune", "source": "territoire de démonstration", "status": "utilisée"}],
    )


def _start_demo(graph: dict, culture_specs: list[dict]) -> None:
    """Prépare la démo : territoire par défaut, résultat calculé, séquence lancée."""
    if "real_territory" not in st.session_state:
        st.session_state.real_territory = _demo_territory()
    _ensure_result(graph, culture_specs)
    st.session_state.impacted = []
    st.session_state.demo = {"idx": 0}
    st.session_state.step = 1
    st.session_state.assolement_screen = 1


def _ensure_result(graph: dict, culture_specs: list[dict]) -> dict:
    """Résultat de démonstration hors réseau si aucun calcul n'a encore été fait."""
    if "result" not in st.session_state:
        result = build_recommendation(
            graph, _demo_parcel(), culture_specs, date(2027, 4, 15), 3, date(2026, 7, 30)
        )
        result["mode_donnees"] = "demo"
        result["parcelle_source"] = "parcelle de démonstration (hors réseau)"
        result["resolution_log"] = [
            {"field": "commune", "source": "territoire de démonstration", "status": "utilisée"}
        ]
        st.session_state.result = result
    return st.session_state.result


def _apply_demo_position() -> None:
    """Applique la position courante de la séquence démo (avant le rendu)."""
    demo = st.session_state.get("demo")
    if not demo:
        return
    kind, value = DEMO_SEQUENCE[demo["idx"]]
    if kind == "assolement_screen":
        st.session_state.step = 1
        st.session_state.assolement_screen = value
    else:
        st.session_state.step = value


def _advance_demo() -> None:
    """Pause, puis écran suivant de la séquence (dernier écran : arrêt)."""
    demo = st.session_state.get("demo")
    if not demo:
        return
    time.sleep(DEMO_STEP_SECONDS)
    demo["idx"] += 1
    if demo["idx"] >= len(DEMO_SEQUENCE):
        st.session_state.pop("demo", None)
    else:
        st.rerun()


def _maybe_auto_demo(graph: dict, culture_specs: list[dict]) -> None:
    """Lance la démo automatiquement si l'URL porte ?view=application&demo=1 (tournage, juges)."""
    if st.query_params.get("demo") == "1" and st.session_state.get("view") == "application" and "demo" not in st.session_state:
        _start_demo(graph, culture_specs)
        st.query_params.clear()


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


def maybe_transition(content: str, key: str) -> str:
    """Enveloppe le contenu d'une transition de page (15) uniquement quand on
    change d'étape/écran — les reruns liés aux widgets ne refont pas le fondu."""
    previous = st.session_state.get("_fade_key")
    st.session_state._fade_key = key
    if previous != key:
        return anim.page_transition(content)
    return content


def assolement_nav(lang: str = MS) -> None:
    """Navigation du tunnel : écran → écran, puis écran 4 → étape 2 du tunnel principal."""
    screen = st.session_state.assolement_screen
    next_by_screen = {
        1: (T("nav.tunnel_result"), 2),
    }
    left, right = st.columns(2)
    with left:
        if screen > 1:
            st.button(T("nav.tunnel_prev"), key="tunnel_prev", width="stretch", on_click=go_to_assolement_screen, args=(screen - 1,))
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


def step_nav(prev_step: int | None = None, prev_label: str = "← Précédent", next_step: int | None = None, next_label: str = "Suivant →", next_disabled: bool = False) -> None:
    """Boutons Précédent/Suivant en bas d'une étape."""
    left, right = st.columns(2)
    with left:
        if prev_step is not None:
            st.button(prev_label, key=f"nav_prev_{prev_step}", width="stretch", on_click=go_to_step, args=(prev_step,))
    with right:
        if next_step is not None:
            st.button(next_label, key=f"nav_next_{next_step}", type="primary", width="stretch", disabled=next_disabled, on_click=go_to_step, args=(next_step,))


def confidence_notice(result: dict, lang: str = MS) -> None:
    """Explique la confiance en langage courant."""
    level = result["confiance"]["niveau"]
    if level == "haute":
        st.success(T("res.confidence.high"))
    elif level == "degradee":
        st.markdown(
            '<div class="confidence-banner degradee"><strong>' + T("res.confidence.degraded.title") + '</strong> '
            + T("res.confidence.degraded.text") + "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="confidence-banner insuffisante"><strong>' + T("res.confidence.impossible") + '</strong> '
            + " ".join(result["confiance"]["motifs"])
            + "</div>",
            unsafe_allow_html=True,
        )


def confidence_dashboard(result: dict, lang: str = MS) -> None:
    """Détaille la confiance sans jamais la gonfler artificiellement."""
    level_word = {"élevée": T("lvl.high"), "moyenne": T("lvl.medium"), "faible": T("lvl.low")}
    soil = result.get("soil_resolution") or {}
    components = [
        (T("conf.parcel"), "élevée", result.get("parcelle_source", T("conf.parcel.detail"))),
        (T("conf.soil"), {"mesure_utilisateur": "élevée", "source_secondaire": "moyenne", "interpolation_idw": "faible"}.get(soil.get("method"), "faible"), soil.get("detail", T("conf.soil.detail"))),
        (T("conf.water"), result.get("hydro_confidence", "faible"), result.get("hydro_detail", T("conf.water.detail"))),
        (T("conf.weather"), "moyenne" if result["horizon_mois"] == 3 else "faible", T("conf.weather.detail")),
        (T("conf.prices"), "moyenne", T("conf.prices.detail")),
    ]
    order = {"élevée": 3, "moyenne": 2, "faible": 1}
    global_level = min((item[1] for item in components), key=lambda value: order[value])
    st.markdown(f'<div class="confidence-title"><span>{T("conf.title")}</span><strong class="level-{global_level}">{level_word[global_level]}</strong><p>{T("conf.note")}</p></div>', unsafe_allow_html=True)
    cards = ['<div class="confidence-grid">']
    for name, level, detail in components:
        cards.append(f'<div class="confidence-component level-{level}"><span>{name}</span><strong>{level_word[level]}</strong><small>{detail}</small></div>')
    cards.append("</div>")
    st.markdown("".join(cards), unsafe_allow_html=True)
    missing = []
    if soil.get("method") != "mesure_utilisateur":
        missing.append(T("conf.missing.soil"))
    if result.get("hydro_confidence") != "élevée":
        missing.append(T("conf.missing.water"))
    missing.append(T("conf.missing.prices"))
    st.markdown('<div class="confidence-actions"><strong>' + T("conf.actions") + '</strong><ol>' + "".join(f"<li>{item}</li>" for item in missing) + '</ol><p>' + T("conf.note2") + '</p></div>', unsafe_allow_html=True)


def render_question_screen(graph: dict, culture_specs: list[dict], lang: str = MS) -> None:
    """Écran 1 — La question : la parcelle et ses conditions d'accès à l'eau."""
    if "intro_slide" not in st.session_state:
        st.session_state.intro_slide = 0
    nav_prev, nav_body, nav_next = st.columns([0.12, 0.76, 0.12], vertical_alignment="center")
    with nav_prev:
        if st.button("‹", key="intro_prev", width="stretch"):
            st.session_state.intro_slide = (st.session_state.intro_slide - 1) % len(intro_slides(lang))
    with nav_next:
        if st.button("›", key="intro_next", width="stretch"):
            st.session_state.intro_slide = (st.session_state.intro_slide + 1) % len(intro_slides(lang))
    with nav_body:
        st.markdown(intro_slide_html(st.session_state.intro_slide, lang), unsafe_allow_html=True)

    st.markdown(anim.mask_reveal('<div class="report-section-kicker">' + T("q.kicker") + '</div>', tag="div"), unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:16px;font-weight:600;margin-bottom:.9rem;">'
        + anim.split_line_reveal(
            [T("q.hook1"), T("q.hook2"), T("q.hook3")],
            tag="span",
        )
        + "</div>",
        unsafe_allow_html=True,
    )

    commune_query = st.text_input(T("q.commune"), value="Vierzon", help=T("q.commune.help"))
    load_real = st.button(T("q.search"), width="stretch")
    if load_real:
        try:
            with st.spinner(T("q.search.spinner")):
                st.session_state.real_territory = fetch_real_territory(commune_query)
            st.success(T("q.found", n=len(st.session_state.real_territory.parcels)))
        except PublicDataError as exc:
            st.error(T("q.error", exc=exc))

    territory = st.session_state.get("real_territory")
    if territory is None:
        st.info(T("q.info"))
        return
    st.caption(T("q.caption_rpg", year=territory.rpg_year, code=territory.commune["code"]))

    selected_label = st.selectbox(T("q.parcel"), [p["label"] for p in territory.parcels])
    sowing = st.date_input(T("q.sowing"), value=date(2027, 4, 15))
    horizon = st.segmented_control(T("q.horizon"), [3, 6, 12], default=3, format_func=lambda value: T("q.horizon.fmt", value=value)) or 3
    st.caption(T("q.horizon.caption"))
    parcel = next(p for p in territory.parcels if p["label"] == selected_label)

    with st.spinner(T("q.soil.spinner")):
        resolved_soil = cached_resolve_soil(parcel)
    parcel = dict(parcel, sol=resolved_soil.soil_type, reserve_utile_mm=resolved_soil.reserve_utile_mm, soil_resolution={"method": resolved_soil.method, "source": resolved_soil.source, "confidence": resolved_soil.confidence, "detail": resolved_soil.detail})
    soil_card = (
        '<div class="om-soil-card">'
        f'<div class="om-soil-kicker">{T("q.soil.kicker")}</div>'
        '<div class="om-soil-grid">'
        f'<div><span>{T("q.soil.type")}</span><strong>{resolved_soil.soil_type}</strong></div>'
        f'<div><span>{T("q.soil.ru")}</span><strong>{anim.count_up_number(int(resolved_soil.reserve_utile_mm), suffix=" mm")}</strong></div>'
        '</div>'
        '</div>'
    )
    st.markdown(anim.fade_up(anim.card_hover(soil_card)), unsafe_allow_html=True)
    with st.expander(T("q.soil.details")):
        st.markdown(
            f'<div style="font-size:13px;opacity:.8;">{T("q.soil.confidence")} : <b class="lvl-{resolved_soil.confidence}">{resolved_soil.confidence}</b> · {resolved_soil.detail}</div>',
            unsafe_allow_html=True,
        )
        with st.container():
            known_soil = st.selectbox(T("q.soil.known_type"), [resolved_soil.soil_type, "limono-argileux", "limoneux", "argileux", "sableux", "autre / inconnu"], key="known_soil_sel")
            known_ru = st.number_input(T("q.soil.known_ru"), 30, 250, resolved_soil.reserve_utile_mm, 5, key="known_ru_num")
            if st.checkbox(T("q.soil.use_mine"), key="use_my_soil"):
                parcel = dict(parcel, sol=known_soil, reserve_utile_mm=int(known_ru), soil_resolution={"method": "mesure_utilisateur", "source": "analyse utilisateur", "confidence": "haute", "detail": "Analyse déclarée comme mesurée."})

    parcel_line_facts = f'<span>{parcel["commune"]}</span><span>{parcel["surface_ha"]} ha</span><span>{parcel["sol"]}</span><span>RU {parcel["reserve_utile_mm"]} mm</span>'
    st.markdown(anim.fade_up(f'<div class="parcel-line">{parcel_line_facts}</div>', delay=1), unsafe_allow_html=True)
    st.session_state.parcelle_id = parcel.get("id", selected_label)
    with st.expander(T("q.map")):
        st.markdown(
            anim.fade_up(
                f'<div class="parcel-map">{render_parcel_map(territory.parcels, territory.hydro_stations, selected_id=st.session_state.parcelle_id, lang=lang)}</div>',
                delay=2,
            ),
            unsafe_allow_html=True,
        )
    calculate = st.button(T("q.analyze"), type="primary", width="stretch")
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
        summary = T("res.summary.crops", n=len(crops), id=result["parcelle_id"])
        if best:
            summary += T("res.summary.best", crop=best["culture"], margin=f"{best['marge_brute_eur_ha']:.0f}", state=best["etat"])
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


def datahub_banner_html(graph: dict, lang: str = MS) -> str:
    """Bandeau DataHub de l'écran 4 : connexion GMS + fraîcheur des sources lue dans le graphe."""
    client = get_datahub_client()
    source_urns = [urn for urn in graph["datasets"] if urn not in {t for v in graph["lineage"].values() for t in v}]
    edges = sum(len(targets) for targets in graph["lineage"].values())
    if not client.enabled:
        banner = (
            '<div class="datahub-banner datahub-off"><span class="datahub-dot"></span><div>'
            "<strong>" + T("datah.banner.local.title") + "</strong>"
            f"<p>{T('datah.banner.local.text', file='<code>fixtures/graph.json</code>', sources=len(source_urns), edges=edges, env='<code>DATAHUB_GMS_URL</code>')}</p>"
            "</div></div>"
        )
    elif not client.connected():
        banner = (
            '<div class="datahub-banner datahub-off"><span class="datahub-dot"></span><div>'
            "<strong>" + T("datah.banner.unreachable.title") + "</strong>"
            f"<p>{T('datah.banner.unreachable.text', file='<code>fixtures/graph.json</code>', url='<code>' + client.gms_url + '</code>')}</p>"
            "</div></div>"
        )
    else:
        freshness = client.freshness_summary(source_urns)
        badges = []
        for urn in source_urns:
            info = freshness["sources"].get(urn, {})
            name = short_name(urn)
            if info.get("status") == "stale":
                badges.append(f'<b style="color:var(--vigilance)">{name}</b><span>' + T("datah.fresh.stale", days=info["delta_days"], sla=info["sla_days"]) + '</span>')
            elif info.get("status") == "ok":
                badges.append(f"<b>{name}</b><span>" + T("datah.fresh.ok") + "</span>")
            else:
                badges.append(f"<b>{name}</b><span>" + T("datah.fresh.unknown") + "</span>")
        badges_html = "".join(f"<div>{badge}</div>" for badge in badges)
        banner = (
            '<div class="datahub-banner"><span class="datahub-dot"></span><div>'
            f"<strong>" + T("datah.banner.connected", url=client.gms_url) + "</strong>"
            f"<p>{T('datah.banner.summary', sources=len(source_urns), ok=freshness['ok'], stale=freshness['stale'], unknown=freshness['unknown'], edges=edges)}</p>"
            f'<div class="datahub-src">{badges_html}</div>'
            "</div></div>"
        )
    return anim.fade_up(anim.card_hover(banner))


def render_result_screen(result: dict, graph: dict, lang: str = MS) -> None:
    """Écran 2 — Le résultat, en pyramide de décision : décision d'abord, pourquoi ensuite,
    preuve technique repliée en dernier (jamais supprimée, juste pas prioritaire)."""
    st.markdown(anim.mask_reveal(screen_kicker_html(T("res.kicker"))), unsafe_allow_html=True)
    confidence_notice(result, lang)
    if not result["cultures"]:
        st.info(T("res.no_crops"))
        return

    # --- Niveau 1 : décision, en une seule page façon « une » de journal ----
    # Titraille + chapô + image légendée + attaque + corps en colonnes + chute :
    # tout ce qu'il faut pour décider tient sur cet unique écran, sans clic.
    st.markdown(
        anim.fade_up(
            '<div class="answer-verdict">'
            f'<div class="answer-verdict-kicker">{T("res.verdict_kicker")}</div>'
            f'<div class="answer-verdict-text">{verdict_sentence(result, lang)}</div>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )
    st.markdown(anim.fade_up(front_page_html(result, lang)), unsafe_allow_html=True)

    at_risk_crops = sorted(
        (c for c in result["cultures"] if c["etat"] != "sûr"),
        key=lambda c: c["recouvrement_avec_tension_j"],
        reverse=True,
    )
    if at_risk_crops:
        with st.popover("🛡️ " + T("res.protect")):
            if len(at_risk_crops) == 1:
                crop = at_risk_crops[0]
                st.markdown(f"**{T('res.levers', crop=crop['culture'])}**")
                st.markdown(anim.fade_up(anim.card_hover(levers_panel(crop, lang))), unsafe_allow_html=True)
            else:
                lever_tabs = st.tabs([c["culture"].capitalize() for c in at_risk_crops])
                for tab, crop in zip(lever_tabs, at_risk_crops):
                    with tab:
                        st.markdown(anim.fade_up(anim.card_hover(levers_panel(crop, lang))), unsafe_allow_html=True)

    crops_by_name = {c["culture"]: c for c in result["cultures"]}
    names = list(crops_by_name.keys())

    sim_input_rows = [
        {
            T("res.sim.col.culture"): crop["culture"].capitalize(),
            T("res.sim.col.rendement"): float(crop["decomposition_marge"]["rendement_qx_ha"]),
            T("res.sim.col.prix"): float(crop["decomposition_marge"]["prix_eur_qx"]),
            T("res.sim.col.aides"): float(crop["decomposition_marge"]["aides_primes_eur_ha"]),
            T("res.sim.col.semences"): float(crop["decomposition_marge"]["semences_eur_ha"]),
            T("res.sim.col.ferti"): float(crop["decomposition_marge"]["fertilisation_eur_ha"]),
            T("res.sim.col.protection"): float(crop["decomposition_marge"]["protection_eur_ha"]),
            T("res.sim.col.travaux"): float(crop["decomposition_marge"]["travaux_carburant_eur_ha"]),
            T("res.sim.col.sechage"): float(crop["decomposition_marge"]["sechage_eur_ha"]),
            T("res.sim.col.prestation"): 0.0,
            T("res.sim.col.eau"): float(crop["decomposition_marge"]["cout_eau_eur_m3"]),
        }
        for crop in result["cultures"]
    ]

    def _simulate(rows: pd.DataFrame) -> dict:
        computed = {}
        for crop, row in zip(result["cultures"], rows.to_dict("records")):
            d = crop["decomposition_marge"]
            computed[crop["culture"]] = recompute_margin(
                crop["besoin_irrigation_mm"],
                d["perte_si_restriction_eur_ha"],
                rendement_qx_ha=row[T("res.sim.col.rendement")],
                prix_eur_qx=row[T("res.sim.col.prix")],
                aides_primes_eur_ha=row[T("res.sim.col.aides")],
                semences_eur_ha=row[T("res.sim.col.semences")],
                fertilisation_eur_ha=row[T("res.sim.col.ferti")],
                protection_eur_ha=row[T("res.sim.col.protection")],
                travaux_carburant_eur_ha=row[T("res.sim.col.travaux")],
                sechage_eur_ha=row[T("res.sim.col.sechage")],
                prestation_eur_ha=row[T("res.sim.col.prestation")],
                cout_eau_eur_m3=row[T("res.sim.col.eau")],
            )
        return computed

    simulated_by_culture = _simulate(pd.DataFrame(sim_input_rows))

    # --- Niveau 2 : le reste, en boutons — chacun ouvre un panneau, parfois
    # lui-même divisé en sous-onglets. Rien n'est perdu, juste pas prioritaire.
    action_col_a, action_col_b = st.columns(2)
    with action_col_a:
        with st.popover("🔍 " + T("res.tab.compare"), width="stretch"):
            current_name = next((c["culture"] for c in result["cultures"] if c.get("deja_cultivee_sur_parcelle")), names[0])
            best_name = min(result["cultures"], key=lambda c: c["rang"])["culture"]
            default_b_name = best_name if best_name != current_name else next((n for n in names if n != current_name), current_name)
            compare_col_a, compare_col_b = st.columns(2)
            with compare_col_a:
                crop_a_name = st.selectbox(T("res.crop_a"), names, index=names.index(current_name), key="cmp_a")
            with compare_col_b:
                crop_b_name = st.selectbox(T("res.crop_b"), names, index=names.index(default_b_name), key="cmp_b")
            st.markdown(comparator_html(crops_by_name[crop_a_name], crops_by_name[crop_b_name], lang), unsafe_allow_html=True)
            st.caption(T("res.compare.caption"))

    with action_col_b:
        with st.popover("🧰 " + T("res.tools"), width="stretch"):
            calendar_tab, simulate_tab, report_tab = st.tabs([T("res.tab.calendar"), T("res.tab.simulate"), T("res.tab.report")])

            with calendar_tab:
                st.markdown(anim.fade_up(render_timeline(result, lang)), unsafe_allow_html=True)
                st.markdown(anim.fade_up(render_water_chart(result["cultures"], result["fenetre_de_tension"], lang)), unsafe_allow_html=True)
                st.caption(T("res.calendar.caption"))

            with simulate_tab:
                st.markdown(
                    f'<div style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.02em;opacity:.55;margin:.7rem 0 .2rem;">{T("res.sim.heading")}</div>',
                    unsafe_allow_html=True,
                )
                st.caption(T("res.sim.caption"))
                edited_df = st.data_editor(pd.DataFrame(sim_input_rows), hide_index=True, width="stretch", key="simulation_editor")
                simulated_by_culture = _simulate(edited_df)
                st.markdown(simulation_recap_html(result["cultures"], simulated_by_culture, lang), unsafe_allow_html=True)

            with report_tab:
                st.markdown(f'<div class="report-subhead">{T("res.report.subhead")}</div>', unsafe_allow_html=True)
                report_action_col, report_download_col = st.columns(2)
                with report_action_col:
                    if st.session_state.get("last_report"):
                        st.success(T("res.report.done"))
                    else:
                        st.button(T("res.report.btn"), width="stretch", on_click=archive_report, args=(result, simulated_by_culture))
                with report_download_col:
                    if st.session_state.get("last_report"):
                        st.download_button(
                            T("res.report.dl"),
                            data=report_to_csv(st.session_state.last_report),
                            file_name=f"comparaison_{result['parcelle_id']}.csv",
                            mime="text/csv",
                            width="stretch",
                        )

    # --- Niveau 3 : preuve (repliée, contenu technique inchangé) ------------
    st.markdown(anim.animated_divider("var(--craie)"), unsafe_allow_html=True)
    with st.expander(T("res.proof")):
        quality = build_quality_certificate(result)
        seal = anim.count_up_number(quality["verified_count"], suffix="/" + str(quality["total_count"]))
        st.markdown(
            anim.fade_up(
                anim.card_hover(
                    f'<section class="trust-banner"><div><span>{T("res.proof.cert")}</span><strong>{quality["statement"]}</strong><p>{T("res.proof.tracability")} : <b>{"oui" if quality["lineage_verified"] else "non"}</b> · {T("res.proof.strong")} : <b>{quality["verified_count"]}/{quality["total_count"]}</b>.</p></div>'
                    f'<div class="trust-seal">{seal}<small>{T("res.proof.strong")}</small></div></section>'
                )
            ),
            unsafe_allow_html=True,
        )
        st.markdown(datahub_banner_html(graph, lang), unsafe_allow_html=True)
        st.markdown(anim.fade_up(kpis_html(graph, result, get_datahub_client(), lang)), unsafe_allow_html=True)
        render_supervision_console(get_datahub_client(), graph, lang)
        st.markdown('<div class="assolement-spine-full">', unsafe_allow_html=True)
        st.markdown(render_spine(graph, set(st.session_state.get("impacted", [])), lang), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        impacted = set(st.session_state.get("impacted", []))
        st.markdown(
            anim.fade_up(f'<div class="report-subhead">{T("res.proof.subhead")}</div>'),
            unsafe_allow_html=True,
        )
        st.markdown(lineage_html(graph, impacted_urns=impacted, lang=lang), unsafe_allow_html=True)

        with st.expander(T("res.proof.all")):
            confidence_dashboard(result, lang)
            st.markdown('<div class="quality-list animate-stagger">' + "".join(f'<div class="quality-{item["level"]}"><span>{item["name"]}</span><b>{item["level"]}</b><small>{item["evidence"]}</small></div>' for item in quality["checks"]) + '</div>', unsafe_allow_html=True)
            st.dataframe([{T("step3.table.col.culture"): crop["culture"], T("step3.table.col.days"): crop["recouvrement_avec_tension_j"], T("step3.table.col.water"): crop["besoin_irrigation_mm"], T("step3.table.col.budget"): crop["cout_eau_eur_ha"], T("step3.table.col.margin"): crop["marge_brute_eur_ha"]} for crop in result["cultures"]], hide_index=True, width="stretch")
        with st.expander(T("res.proof.attempts")):
            for attempt in result.get("resolution_log", []):
                symbol = "✓" if "utilisée" in attempt["status"] else "→"
                st.write(f'{symbol} **{attempt["field"].capitalize()}** — {attempt["source"]} : {attempt["status"]}')
        with st.expander(T("res.proof.expert")):
            expert = build_expert_report(result)
            st.markdown(f'<div class="expert-heading"><div><span>{T("res.proof.expert.score")}</span><strong>{anim.count_up_number(expert["overall_score"])}<span style="opacity:.6">/100</span></strong></div><p>{T("res.proof.expert.score.note")}</p></div>', unsafe_allow_html=True)
            collected_tab, failed_tab, models_tab, scores_tab = st.tabs([T("res.proof.expert.collected"), T("res.proof.expert.failed"), T("res.proof.expert.models"), T("res.proof.expert.scores")])
            with collected_tab:
                st.dataframe(expert["collected"], hide_index=True, width="stretch")
            with failed_tab:
                if expert["failures"]:
                    st.dataframe(expert["failures"], hide_index=True, width="stretch")
                else:
                    st.success(T("res.proof.expert.nofailed"))
            with models_tab:
                st.dataframe(expert["models"], hide_index=True, width="stretch")
                with st.expander(T("res.proof.expert.params")):
                    st.json({"parcelle": result["parcelle_id"], "semis": result["date_semis"], "horizon_mois": result["horizon_mois"], "sol": result["sol"], "fenetre_de_tension": result["fenetre_de_tension"]})
            with scores_tab:
                st.caption(T("res.proof.expert.bar"))
                st.dataframe(expert["scores"], hide_index=True, width="stretch")


def render_datahub_view(graph: dict, culture_specs: list[dict], lang: str = MS) -> None:
    """Vue « Données & IA » du site vitrine : graphe connecté, KPIs, supervision, lineage."""
    result = _ensure_result(graph, culture_specs)
    client = get_datahub_client()
    st.markdown(
        anim.mask_reveal(
            '<div class="site-view-head"><h1>' + T("datah.head.title") + '</h1>'
            '<p>' + T("datah.head.lead") + '</p></div>'
        ),
        unsafe_allow_html=True,
    )
    st.markdown(datahub_banner_html(graph, lang), unsafe_allow_html=True)

    kpi_tab, supervision_tab, provenance_tab, lineage_tab = st.tabs(
        [T("datah.tab.kpis"), T("datah.tab.supervision"), T("datah.tab.provenance"), T("datah.tab.lineage")]
    )
    with kpi_tab:
        st.markdown(anim.fade_up(kpis_html(graph, result, client, lang)), unsafe_allow_html=True)
    with supervision_tab:
        render_supervision_console(client, graph, lang)
    with provenance_tab:
        st.markdown('<div class="assolement-spine-full">', unsafe_allow_html=True)
        st.markdown(render_spine(graph, set(st.session_state.get("impacted", [])), lang), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with lineage_tab:
        st.markdown(
            anim.fade_up(f'<div class="report-subhead">{T("res.proof.subhead")}</div>'),
            unsafe_allow_html=True,
        )
        st.markdown(lineage_html(graph, impacted_urns=set(st.session_state.get("impacted", [])), lang=lang), unsafe_allow_html=True)

    st.markdown(cta_html(lang), unsafe_allow_html=True)
    st.markdown(footer_html(lang), unsafe_allow_html=True)


def _resolve_view() -> str:
    """Vue courante du site : accueil par défaut, bascule via l'URL ?view=..."""
    param = st.query_params.get("view")
    if param in {"accueil", "application", "donnees", "contact"}:
        st.session_state.view = param
        st.query_params.pop("view")
    return st.session_state.get("view", "accueil")


def _maybe_restart_tunnel() -> None:
    """Un lien « Analyser ma parcelle » (?start=1) ramène toujours au premier
    écran du tunnel, même si un résultat précédent traîne encore en session."""
    if st.query_params.get("start") == "1":
        st.session_state.step = 1
        st.session_state.assolement_screen = 1
        st.query_params.pop("start")


def _resolve_lang() -> str:
    """Langue de l'interface : bascule via l'URL ?lang=fr|en, persistée en session."""
    param = st.query_params.get("lang")
    if param in {"fr", "en"}:
        st.session_state.lang = param
        st.query_params.pop("lang")
        return param
    return st.session_state.get("lang", MS)


st.set_page_config(page_title="Terroir Context Agents", layout="wide", initial_sidebar_state="collapsed")
st.markdown(CSS, unsafe_allow_html=True)
anim.inject_scroll_animations()

try:
    graph = load_graph(ROOT / "fixtures/graph.json")
    culture_specs = load_json(ROOT / "data/cultures_reference.json")
except (ValueError, RuntimeError) as exc:
    st.error(str(exc))
    st.stop()

view = _resolve_view()
lg = _resolve_lang()
_maybe_restart_tunnel()
_maybe_auto_demo(graph, culture_specs)
st.markdown(navbar_html(view, lg), unsafe_allow_html=True)

if view == "accueil":
    st.markdown(hero_html(lg), unsafe_allow_html=True)
    st.markdown(stats_band_html(lg), unsafe_allow_html=True)
    story_tabs = st.tabs([T("lp.tab.mission"), T("lp.tab.values"), T("lp.tab.expertise"), T("lp.tab.approach")])
    with story_tabs[0]:
        st.markdown(about_html(lg), unsafe_allow_html=True)
    with story_tabs[1]:
        st.markdown(values_html(lg), unsafe_allow_html=True)
    with story_tabs[2]:
        st.markdown(expertise_html(lg), unsafe_allow_html=True)
    with story_tabs[3]:
        st.markdown(approach_html(lg), unsafe_allow_html=True)
    st.markdown(cta_html(lg), unsafe_allow_html=True)
    st.markdown(footer_html(lg), unsafe_allow_html=True)
    st.stop()

if view == "donnees":
    render_datahub_view(graph, culture_specs, lg)
    st.stop()

if view == "contact":
    st.markdown(
        '<div class="site-contact"><h1>' + T("contact.title") + '</h1>'
        '<p>' + T("contact.lead") + '</p>'
        '<div class="site-contact-grid">'
        '<div class="site-contact-card"><span>' + T("contact.team") + '</span><h3>Terroir Context Agents</h3><p>' + T("contact.hackathon") + '</p></div>'
        '<div class="site-contact-card"><span>' + T("contact.code") + '</span><h3>github.com/faten-elouta/Agriculteur</h3><p>' + T("contact.gh_desc") + '</p></div>'
        '<div class="site-contact-card"><span>' + T("contact.live") + '</span><h3>terroir-context-agents.vercel.app</h3><p>' + T("contact.app") + '</p></div>'
        '</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(footer_html(lg), unsafe_allow_html=True)
    st.stop()

# --- Vue Application : droit au tunnel, sans hero/stats redondants ---------
if "step" not in st.session_state:
    st.session_state.step = 1
if st.session_state.step > 1 and "result" not in st.session_state:
    st.session_state.step = 1
step = st.session_state.step
if "assolement_screen" not in st.session_state:
    st.session_state.assolement_screen = 1
if "result" not in st.session_state and st.session_state.assolement_screen > 1:
    st.session_state.assolement_screen = 1
_apply_demo_position()

if step > 1:
    st.markdown(anim.fade_up(render_step_indicator(step, step_labels())), unsafe_allow_html=True)

# --- Étape 1 : tunnel assolement en 2 écrans ------------------------------
if step == 1:
    st.markdown(
        section_header_html(
            T("step1.header"),
            T("step1.title"),
            T("step1.lead"),
        ),
        unsafe_allow_html=True,
    )
    tunnel_content = anim.fade_up(tunnel_header_html(st.session_state.assolement_screen, ASSOLEMENT_SCREEN_COUNT))
    if st.session_state.assolement_screen == 2:
        with st.container(key="om_wide"):
            render_result_screen(st.session_state.result, graph, lg)
    else:
        with st.container(key="om_screen"):
            render_question_screen(graph, culture_specs, lg)
    st.markdown(anim.animated_divider("var(--craie)"), unsafe_allow_html=True)
    assolement_nav(lg)

# --- Étape 2 : scénario météo dans le temps ------------------------------
elif step == 2:
    result = st.session_state.result
    st.markdown(
        section_header_html(
            T("step2.header"),
            T("step2.title"),
            T("step2.lead"),
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        maybe_transition(
            anim.animated_divider("var(--encre)"),
            key="step2",
        ),
        unsafe_allow_html=True,
    )
    if st.button(T("step2.play"), key="play_timeline"):
        st.session_state.timeline_play_token = st.session_state.get("timeline_play_token", 0) + 1
    play_token = st.session_state.get("timeline_play_token", 0)
    tension_months = {m["mois"] for m in result["fenetre_de_tension"]}
    for index, crop in enumerate(result["cultures"]):
        st.markdown(anim.fade_up(render_crop_scenario(crop, tension_months, play_token, lg), delay=index % 4), unsafe_allow_html=True)

    st.markdown(anim.fade_up(render_water_chart(result["cultures"], result["fenetre_de_tension"], lg)), unsafe_allow_html=True)
    st.caption(T("step2.scroll.caption"))

    with st.expander(T("step2.calendar")):
        svg, alternative = calendar_svg(result, lg)
        st.markdown(f'<div class="animate-vertical-mask animate-zoom-hover">{svg}</div>', unsafe_allow_html=True)
        st.caption(alternative)

    step_nav(prev_step=1, prev_label=T("nav.back_result"), next_step=3, next_label=T("nav.to_details"))

# --- Étape 3 : détails techniques ----------------------------------------
elif step == 3:
    result = st.session_state.result
    quality = build_quality_certificate(result)

    st.markdown(
        section_header_html(
            T("step3.header"),
            T("step3.title"),
            T("step3.lead"),
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        maybe_transition(
            anim.animated_divider("var(--eau)"),
            key="step3",
        ),
        unsafe_allow_html=True,
    )

    numbers_tab, provenance_tab, expert_tab, security_tab = st.tabs(
        [T("step3.tab.numbers"), T("step3.tab.provenance"), T("step3.tab.expert"), T("step3.tab.security")]
    )

    with numbers_tab:
        confidence_dashboard(result, lg)
        st.markdown('<div class="quality-list animate-stagger">' + "".join(f'<div class="quality-{item["level"]}"><span>{item["name"]}</span><b>{item["level"]}</b><small>{item["evidence"]}</small></div>' for item in quality["checks"]) + '</div>', unsafe_allow_html=True)
        st.dataframe([{T("step3.table.col.culture"): crop["culture"], T("step3.table.col.days"): crop["recouvrement_avec_tension_j"], T("step3.table.col.water"): crop["besoin_irrigation_mm"], T("step3.table.col.budget"): crop["cout_eau_eur_ha"], T("step3.table.col.margin"): crop["marge_brute_eur_ha"]} for crop in result["cultures"]], hide_index=True, width="stretch")

    with provenance_tab:
        st.markdown(render_spine(graph, set(st.session_state.get("impacted", [])), lg), unsafe_allow_html=True)
        st.markdown("#### " + T("step3.provenance.sub"))
        for attempt in result.get("resolution_log", []):
            symbol = "✓" if "utilisée" in attempt["status"] else "→"
            st.write(f'{symbol} **{attempt["field"].capitalize()}** — {attempt["source"]} : {attempt["status"]}')

    with expert_tab:
        expert = build_expert_report(result)
        st.markdown(f'<div class="expert-heading"><div><span>{T("res.proof.expert.score")}</span><strong>{anim.count_up_number(expert["overall_score"])}<span style="opacity:.6">/100</span></strong></div><p>{T("res.proof.expert.score.note")}</p></div>', unsafe_allow_html=True)
        collected_tab, failed_tab, models_tab, scores_tab = st.tabs([T("res.proof.expert.collected"), T("res.proof.expert.failed"), T("res.proof.expert.models"), T("res.proof.expert.scores")])
        with collected_tab:
            st.write(T("step3.expert.collected_lead"))
            st.dataframe(expert["collected"], hide_index=True, width="stretch")
        with failed_tab:
            st.write(T("step3.expert.failed_lead"))
            if expert["failures"]:
                st.dataframe(expert["failures"], hide_index=True, width="stretch")
            else:
                st.success(T("res.proof.expert.nofailed"))
        with models_tab:
            st.write(T("step3.expert.models_lead"))
            st.dataframe(expert["models"], hide_index=True, width="stretch")
            with st.expander(T("res.proof.expert.params")):
                st.json({"parcelle": result["parcelle_id"], "semis": result["date_semis"], "horizon_mois": result["horizon_mois"], "sol": result["sol"], "fenetre_de_tension": result["fenetre_de_tension"]})
        with scores_tab:
            st.write(T("res.proof.expert.bar"))
            st.dataframe(expert["scores"], hide_index=True, width="stretch")
            st.caption(T("res.proof.expert.bar.note"))

    with security_tab:
        st.markdown(anim.fade_up(anim.card_hover('<section class="sentinel-box"><div><div class="section-kicker">' + T("step3.frontier.title") + '</div><h3>' + T("step3.frontier.h") + '</h3><p>' + T("step3.frontier.p") + '</p></div></section>')), unsafe_allow_html=True)
        if st.button(T("step3.fail.btn"), width="stretch"):
            simulation = simulate_station_failure(ROOT / "fixtures/graph.json", ROOT / "reports", len(result["cultures"]), date(2026, 7, 30))
            st.session_state.impacted = simulation["impacted"]
            st.session_state.failure_message = T("step3.fail.msg", invalidated=simulation["invalidated"])
            st.session_state.last_simulation = simulation
            st.session_state.incident_urn = get_datahub_client().create_incident(
                T("step3.fail.incident.title"),
                T("step3.fail.incident.body", invalidated=simulation["invalidated"]),
                HYDRO_URN,
            )
            st.rerun()
        if st.session_state.get("failure_message"):
            simulation = st.session_state.get("last_simulation", {})
            st.error(st.session_state.failure_message)
            if st.session_state.get("incident_urn"):
                st.caption(T("step3.fail.incident", urn=st.session_state["incident_urn"]))
            impacted_names = [urn.split(",")[1] if "," in urn else urn for urn in simulation.get("impacted", [])]
            flow_items = [
                '<span class="cascade-node" style="--fc-i:0;"><b>1</b> hubeau_hydrometrie<br><small>' + T("sec.station_late") + '</small></span>',
                '<i class="cascade-arrow" style="--fc-i:1;">→</i>',
                '<span class="cascade-node" style="--fc-i:2;"><b>2</b> features_bilan_hydrique<br><small>' + T("sec.water_invalid") + '</small></span>',
                '<i class="cascade-arrow" style="--fc-i:3;">→</i>',
                '<span class="cascade-node" style="--fc-i:4;"><b>3</b> scenarios_cultures<br><small>' + T("sec.scenarios_invalid") + '</small></span>',
                '<i class="cascade-arrow" style="--fc-i:5;">→</i>',
                '<span class="cascade-node" style="--fc-i:6;"><b>4</b> recommandations<br><small>' + T("sec.results_barred") + '</small></span>',
            ]
            cascade_total = 4
            st.markdown(
                f'<div class="failure-cascade">'
                f'<div class="cascade-impact">{T("sec.impact_line")} : <b class="animate-count-up" data-target="{cascade_total}">0</b> {T("sec.entities")}</div>'
                f'<div class="failure-flow">{"".join(flow_items)}</div></div>',
                unsafe_allow_html=True,
            )
            st.write("**" + T("step3.fail.touched") + " :** " + ", ".join(impacted_names))
            if simulation.get("report_path"):
                st.code(simulation["report_path"], language=None)
            st.button(T("step3.fail.restore"), type="primary", width="stretch", on_click=restore_station)

    st.markdown(render_grass_band(lg), unsafe_allow_html=True)
    st.markdown('<div class="final-warning"><strong>' + T("step3.final.title") + '</strong><p>' + T("step3.final.text") + '</p>' + anim.arrow_slide(T("step3.final.link"), href="https://github.com/faten-elouta/Agriculteur#readme") + '</div>', unsafe_allow_html=True)

    step_nav(prev_step=2, prev_label=T("nav.to_weather"))

st.markdown(footer_html(lg), unsafe_allow_html=True)

_advance_demo()
