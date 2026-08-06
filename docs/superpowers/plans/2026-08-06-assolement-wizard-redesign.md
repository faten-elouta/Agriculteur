# Refonte de l'étape 1 en tunnel séquentiel — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer la disposition en deux colonnes de l'étape 1 (« Parcelle & résultat ») par un tunnel interne de 4 écrans successifs (La question → La réponse → Comment éviter → D'où viennent ces chiffres), fidèle à la maquette Claude Design `Assolement.dc.html`, sans retirer aucune fonctionnalité existante.

**Architecture:** Deux nouvelles fonctions pures dans `ui/assolement.py` (en-tête de tunnel, panneau « aucun risque ») + nouvelles classes CSS dans `ui/styles.py` (progression, écran centré, animation d'entrée) + réécriture du bloc `if step == 1:` de `app.py` en 4 fonctions de rendu (une par écran) routées par un nouvel état `st.session_state.assolement_screen`. Aucun changement à `services/*`, `ui/provenance_spine.py`, `ui/step_nav.py`, ni aux étapes 2/3 du tunnel principal.

**Tech Stack:** Python 3.9, Streamlit, CSS/HTML injecté (aucune nouvelle dépendance), pytest.

**Spec:** `docs/superpowers/specs/2026-08-06-assolement-wizard-redesign-design.md`

## Global Constraints

- Aucune nouvelle dépendance Python (`requirements.txt` inchangé).
- Aucun changement de logique métier, de calculs ou de contrats de données (`services/*` inchangé).
- Les étapes 2 (Scénario météo) et 3 (Détails techniques) du tunnel principal ne changent pas.
- Toutes les actions déjà possibles à l'étape 1 (bascule Réelles/Démonstration, recherche de commune, analyse de sol, horizon, simulation, génération/téléchargement du rapport) restent possibles, sans donnée ni contrôle perdu.
- `levers_panel` reste purement informatif — aucune fonctionnalité « appliquer un levier et recalculer » n'est ajoutée.
- `prefers-reduced-motion: reduce` coupe l'animation d'entrée des écrans.
- Le dépôt n'est pas initialisé en git (`git status` → « not a git repository ») : les étapes de commit habituelles sont remplacées par une simple vérification de fin de tâche ; ne pas lancer `git init` sans validation explicite de l'utilisateur.

---

### Task 1: En-tête de tunnel et kicker d'écran dans `ui/assolement.py`

**Files:**
- Modify: `ui/assolement.py` (ajouter les fonctions après `intro_slide_html`, avant `_fmt`)
- Test: `tests/test_assolement_tunnel.py`

**Interfaces:**
- Produces: `tunnel_header_html(screen_index: int, screen_count: int) -> str`, `screen_kicker_html(label: str) -> str`. Consommées par Task 4 (`app.py`).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_assolement_tunnel.py
from ui.assolement import tunnel_header_html, screen_kicker_html, no_risk_panel_html


def test_tunnel_header_shows_step_count():
    out = tunnel_header_html(2, 4)
    assert "Étape 2 / 4" in out
    assert "Choisir sa culture" in out


def test_tunnel_header_marks_segments_done_up_to_current():
    out = tunnel_header_html(3, 4)
    assert out.count('om-progress-seg') == 4 + out.count('om-progress-seg done')
    assert out.count('om-progress-seg done') == 3


def test_tunnel_header_first_screen_has_no_done_segment():
    out = tunnel_header_html(1, 4)
    assert out.count('om-progress-seg done') == 1


def test_screen_kicker_escapes_label():
    out = screen_kicker_html("<x>")
    assert "<x>" not in out
    assert "&lt;x&gt;" in out


def test_screen_kicker_contains_label():
    assert "La question" in screen_kicker_html("La question")
```

Note : `test_no_risk_panel_html` sera ajouté à ce même fichier en Task 2 — ne pas s'inquiéter si l'import échoue tant que Task 2 n'est pas fait ; à cette étape, seuls `tunnel_header_html` et `screen_kicker_html` doivent exister pour que ces 5 tests passent (l'import de `no_risk_panel_html` sera ajouté en Task 2, pas ici).

Pour cette étape, importez uniquement les deux fonctions déjà visées :

```python
# tests/test_assolement_tunnel.py (état après Task 1)
from ui.assolement import tunnel_header_html, screen_kicker_html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_assolement_tunnel.py -v`
Expected: FAIL with `ImportError: cannot import name 'tunnel_header_html'`

- [ ] **Step 3: Write the implementation**

Dans `ui/assolement.py`, juste après la fonction `intro_slide_html` (avant `def _fmt`), ajouter :

```python
def tunnel_header_html(screen_index: int, screen_count: int) -> str:
    """En-tête persistant du tunnel « Choisir sa culture » : titre, étape, progression."""
    segments = "".join(
        f'<div class="om-progress-seg{" done" if i <= screen_index else ""}"></div>'
        for i in range(1, screen_count + 1)
    )
    return (
        '<div class="om-tunnel-header">'
        '<div class="om-tunnel-title-row">'
        '<h1>Choisir sa culture</h1>'
        f'<span class="om-step-count">Étape {screen_index} / {screen_count}</span>'
        '</div>'
        f'<div class="om-progress">{segments}</div>'
        '</div>'
    )


def screen_kicker_html(label: str) -> str:
    """Petit intitulé en tête de chaque écran du tunnel (« La question », « La réponse »…)."""
    return f'<div class="om-kicker">{html.escape(label)}</div>'
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_assolement_tunnel.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: End-of-task check (no git repo — skip commit)**

Confirm `git status` still reports "not a git repository" (unchanged from session start); no commit to make.

---

### Task 2: Panneau « aucun risque » de l'écran « Comment éviter »

**Files:**
- Modify: `ui/assolement.py` (ajouter après `levers_panel`)
- Test: `tests/test_assolement_tunnel.py` (compléter)

**Interfaces:**
- Produces: `no_risk_panel_html() -> str`. Consommée par Task 4 (`app.py`).

- [ ] **Step 1: Write the failing test**

Compléter `tests/test_assolement_tunnel.py` : remplacer la ligne d'import par la version finale (les deux fonctions de Task 1 + celle-ci), et ajouter le test :

```python
from ui.assolement import tunnel_header_html, screen_kicker_html, no_risk_panel_html


def test_no_risk_panel_mentions_no_collision():
    out = no_risk_panel_html()
    assert "aucune" in out.lower()
    assert "<div" in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_assolement_tunnel.py -v`
Expected: FAIL with `ImportError: cannot import name 'no_risk_panel_html'`

- [ ] **Step 3: Write the implementation**

Dans `ui/assolement.py`, juste après la fonction `levers_panel` (fin de fichier), ajouter :

```python
def no_risk_panel_html() -> str:
    """Contenu de l'écran « Comment éviter » quand aucune culture ne croise la tension en eau."""
    return (
        '<div style="margin-top:24px;border:1px solid var(--craie);border-radius:2px;'
        'padding:20px;background:#F2F1EC;font-size:16px;opacity:.85;">'
        "Aucune culture ne nécessite d'ajustement : aucune ne croise la tension en eau prévue sur cette fenêtre."
        "</div>"
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_assolement_tunnel.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: End-of-task check (no git repo — skip commit)**

No commit; move to Task 3.

---

### Task 3: Styles du tunnel dans `ui/styles.py`

**Files:**
- Modify: `ui/styles.py` (ajouter à la fin du bloc `<style>`, avant `</style>`)
- Test: `tests/test_styles.py`

**Interfaces:**
- Consumes: rien.
- Produces: classes CSS `.om-tunnel-header`, `.om-tunnel-title-row`, `.om-step-count`, `.om-progress`, `.om-progress-seg` (+ `.done`), `.om-kicker`, `.om-screen`, `.assolement-spine-full`, keyframe `omFadeUp`. Consommées par Task 4 (`app.py`, via les classes générées par Task 1/2 et par le HTML écrit directement dans `app.py`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_styles.py
from ui.styles import CSS


def test_css_defines_tunnel_classes():
    for selector in [".om-tunnel-header", ".om-progress-seg", ".om-kicker", ".om-screen", ".assolement-spine-full"]:
        assert selector in CSS


def test_css_defines_fade_up_keyframe():
    assert "@keyframes omFadeUp" in CSS


def test_css_respects_reduced_motion_for_om_screen():
    idx_media = CSS.index("prefers-reduced-motion:reduce) {\n  .weather-hero")
    idx_om_screen_anim = CSS.index(".om-screen { max-width:760px")
    assert idx_om_screen_anim < idx_media
    assert ".om-screen { animation:none !important; }" in CSS
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_styles.py -v`
Expected: FAIL (`.om-tunnel-header` absent de `CSS`, et la dernière assertion échoue faute de règle `reduced-motion` dédiée)

- [ ] **Step 3: Write the implementation**

Dans `ui/styles.py`, juste avant la ligne `</style>` (fin du bloc CSS, avant le triple-guillemet de fermeture), ajouter :

```css
/* Tunnel interne "Choisir sa culture" (Assolement.dc.html) */
.om-tunnel-header { max-width:760px; margin:0 auto .7rem; }
.om-tunnel-title-row { display:flex; align-items:center; justify-content:space-between; margin-bottom:10px; }
.om-tunnel-title-row h1 { margin:0; }
.om-step-count { font-family:"IBM Plex Mono",monospace; font-size:13px; opacity:.55; }
.om-progress { display:flex; gap:4px; }
.om-progress-seg { flex:1; height:3px; border-radius:2px; background:var(--craie); transition:background .3s ease; }
.om-progress-seg.done { background:var(--encre); }
.om-kicker { font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:.03em; opacity:.55; margin-bottom:10px; }
.om-screen { max-width:760px; margin:0 auto; animation:omFadeUp .4s ease; }
@keyframes omFadeUp { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
.assolement-spine-full .spine { border:none; box-shadow:none; padding:0; position:static; }
.assolement-spine-full .spine h2 { display:none; }
```

Puis, dans la règle existante `@media (prefers-reduced-motion:reduce) { ... }` (celle qui commence par `.weather-hero .sun, .weather-hero .cloud, ...`), ajouter `.om-screen` à la liste des sélecteurs coupés et une ligne dédiée, pour obtenir :

```css
@media (prefers-reduced-motion:reduce) {
  .weather-hero .sun, .weather-hero .cloud, .weather-hero .drop, .weather-hero .flash, .weather-hero .sun .heat-line,
  .grass-band .blade, .frise-cursor { animation:none !important; }
  .grass-band .blade { transform:scaleY(1); }
  .frise-cursor { left:100%; }
  .om-screen { animation:none !important; }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_styles.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: End-of-task check (no git repo — skip commit)**

No commit; move to Task 4.

---

### Task 4: Tunnel interne à 4 écrans dans `app.py`

**Files:**
- Modify: `app.py`

**Interfaces:**
- Consumes: `tunnel_header_html`, `screen_kicker_html`, `no_risk_panel_html` (Task 1/2), classes CSS de Task 3.
- Produces: fonctions `render_question_screen`, `render_answer_screen`, `render_levers_screen`, `render_provenance_screen`, `go_to_assolement_screen`, `assolement_nav` dans `app.py` — internes à ce fichier, aucun autre module n'en dépend.

Pas de test automatisé pour `app.py` (aucun `test_app.py` n'existe dans le projet — les scripts Streamlit ne sont pas testés unitairement ici, seuls les modules `ui/*.py` et `services/*.py` le sont). Vérification par lancement manuel de l'app (`make run`), détaillée au Step 6.

- [ ] **Step 1: Mettre à jour l'import de `ui.assolement`**

Dans `app.py`, remplacer la ligne d'import (actuellement) :

```python
from ui.assolement import INTRO_SLIDES, analysis_article, intro_slide_html, levers_panel, render_timeline, retain_sentence, simulation_recap_html
```

par :

```python
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
```

- [ ] **Step 2: Ajouter la constante d'écrans et les helpers de navigation interne**

Juste après la ligne `STEP_LABELS = ["Parcelle & résultat", "Scénario météo", "Détails techniques"]`, ajouter :

```python
ASSOLEMENT_SCREEN_COUNT = 4
```

Juste après la fonction `go_to_step` (avant `def step_nav`), ajouter :

```python
def go_to_assolement_screen(screen: int) -> None:
    st.session_state.assolement_screen = screen


def assolement_nav(
    prev_screen: int | None = None,
    next_screen: int | None = None,
    next_label: str = "Suivant →",
    next_disabled: bool = False,
    next_to_outer_step: int | None = None,
) -> None:
    """Boutons Précédent/Suivant du tunnel interne « Choisir sa culture »."""
    left, right = st.columns(2)
    with left:
        if prev_screen is not None:
            st.button("← Précédent", key=f"om_prev_{prev_screen}", width="stretch", on_click=go_to_assolement_screen, args=(prev_screen,))
    with right:
        if next_to_outer_step is not None:
            st.button(next_label, key="om_next_outer", type="primary", width="stretch", disabled=next_disabled, on_click=go_to_step, args=(next_to_outer_step,))
        elif next_screen is not None:
            st.button(next_label, key=f"om_next_{next_screen}", type="primary", width="stretch", disabled=next_disabled, on_click=go_to_assolement_screen, args=(next_screen,))
```

- [ ] **Step 3: Remplacer `render_result` par les 4 fonctions de rendu d'écran**

Supprimer entièrement la fonction `render_result` actuelle (de `def render_result(result: dict, graph: dict) -> dict | None:` jusqu'à son `return simulated_by_culture` inclus, juste avant la ligne `st.set_page_config(...)`).

La remplacer par les 4 fonctions suivantes, dans cet ordre :

```python
def render_question_screen(graph: dict, parcels: list[dict], culture_specs: list[dict]) -> None:
    """Écran « La question » : formulaire complet de sélection de parcelle et de semis."""
    st.markdown(screen_kicker_html("La question"), unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:18px;margin-bottom:20px;max-width:640px;">'
        "Ce que vous vous apprêtez à semer aura-t-il soif au moment où il n'y aura plus d'eau ?"
        "</div>",
        unsafe_allow_html=True,
    )

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
                with st.spinner("Recherche des parcelles et des stations d'eau…"):
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
            st.caption("Cliquez sur « Chercher les parcelles ». L'exemple de Vierzon reste disponible.")
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
        with st.expander("J'ai une analyse de sol plus précise"):
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


def render_answer_screen(result: dict) -> None:
    """Écran « La réponse » : confiance, certificat, calendrier, analyse, simulation, rapport."""
    quality = build_quality_certificate(result)
    st.markdown(screen_kicker_html("La réponse"), unsafe_allow_html=True)
    confidence_notice(result)
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


def render_levers_screen(result: dict) -> None:
    """Écran « Comment éviter » : leviers pour la culture la plus à risque, ou message si aucune."""
    st.markdown(screen_kicker_html("Comment éviter"), unsafe_allow_html=True)
    at_risk_crops = [c for c in result["cultures"] if c["etat"] != "sûr"]
    risky = max(at_risk_crops, key=lambda c: c["recouvrement_avec_tension_j"]) if at_risk_crops else None
    if risky:
        st.markdown(levers_panel(risky), unsafe_allow_html=True)
    else:
        st.markdown(no_risk_panel_html(), unsafe_allow_html=True)


def render_provenance_screen(graph: dict) -> None:
    """Écran « D'où viennent ces chiffres » : épine de provenance en pleine largeur."""
    st.markdown(screen_kicker_html("D'où viennent ces chiffres"), unsafe_allow_html=True)
    st.markdown('<div class="assolement-spine-full">', unsafe_allow_html=True)
    st.markdown(render_spine(graph, set(st.session_state.get("impacted", []))), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
```

- [ ] **Step 4: Initialiser `assolement_screen` et réinitialiser au bon moment**

Remplacer le bloc :

```python
if "step" not in st.session_state:
    st.session_state.step = 1
if st.session_state.step > 1 and "result" not in st.session_state:
    st.session_state.step = 1
step = st.session_state.step
```

par :

```python
if "step" not in st.session_state:
    st.session_state.step = 1
if "assolement_screen" not in st.session_state:
    st.session_state.assolement_screen = 1
if st.session_state.step > 1 and "result" not in st.session_state:
    st.session_state.step = 1
    st.session_state.assolement_screen = 1
step = st.session_state.step
```

- [ ] **Step 5: Masquer le fil d'Ariane à 3 puces sur l'étape 1 et router les 4 écrans**

Remplacer :

```python
st.markdown(render_step_indicator(step, STEP_LABELS), unsafe_allow_html=True)

# --- Étape 1 : parcelle (gauche) & résultat (droite) ----------------------
if step == 1:
    query_col, result_col = st.columns([0.38, 0.62])
    with query_col:
```

et tout le reste du bloc `if step == 1:` jusqu'à (et y compris) la ligne :

```python
    step_nav(next_step=2, next_label="Voir le scénario météo →", next_disabled=not has_cultures)
```

par :

```python
if step != 1:
    st.markdown(render_step_indicator(step, STEP_LABELS), unsafe_allow_html=True)

# --- Étape 1 : tunnel « Choisir sa culture » (4 écrans) --------------------
if step == 1:
    screen = st.session_state.assolement_screen
    st.markdown(tunnel_header_html(screen, ASSOLEMENT_SCREEN_COUNT), unsafe_allow_html=True)
    st.markdown('<div class="om-screen">', unsafe_allow_html=True)

    if screen == 1:
        render_question_screen(graph, parcels, culture_specs)
        has_cultures = bool(st.session_state.get("result", {}).get("cultures"))
        nav_kwargs = dict(next_screen=2, next_label="Suivant — La réponse →", next_disabled=not has_cultures)
    elif screen == 2:
        render_answer_screen(st.session_state.result)
        nav_kwargs = dict(prev_screen=1, next_screen=3, next_label="Suivant — Comment éviter →")
    elif screen == 3:
        render_levers_screen(st.session_state.result)
        nav_kwargs = dict(prev_screen=2, next_screen=4, next_label="Suivant — D'où viennent ces chiffres →")
    else:
        render_provenance_screen(graph)
        nav_kwargs = dict(prev_screen=3, next_to_outer_step=2, next_label="Voir le scénario météo →")

    st.markdown('</div>', unsafe_allow_html=True)
    assolement_nav(**nav_kwargs)
```

Points d'attention pendant l'édition :
- La ligne `st.markdown('<div class="waiting-story">...` (ancien état « pas encore de résultat » du panneau de droite) disparaît : elle n'a plus de raison d'être, l'écran 2 n'est atteignable que lorsque `has_cultures` est vrai (bouton Suivant désactivé sinon).
- Ne pas toucher aux blocs `elif step == 2:` et `elif step == 3:` qui suivent : ils restent identiques à aujourd'hui.

- [ ] **Step 6: Vérification manuelle de bout en bout**

Run: `.venv/bin/python -m pytest tests/ -q`
Expected: suite complète verte (aucune régression sur les tests existants — `app.py` n'a pas de test dédié).

Puis lancer `make run` et, dans le navigateur, dérouler le tunnel avec une parcelle de démonstration :
1. Écran 1 (« La question », Étape 1/4) : intro, bascule Réelles/Démonstration, recherche de commune fonctionnent comme avant ; le bouton Suivant est grisé tant qu'aucun clic sur « Comparer les cultures ».
2. Cliquer « Comparer les cultures » puis « Suivant » → écran 2 (« La réponse », Étape 2/4) : bandeau de confiance, certificat, calendrier, analyse, tableau de simulation modifiable, génération + téléchargement du rapport — tout fonctionne comme avant.
3. « Suivant » → écran 3 (« Comment éviter », Étape 3/4) : les leviers de la culture la plus à risque s'affichent (ou le message « aucune culture ne nécessite d'ajustement » si aucune n'est à risque).
4. « Suivant » → écran 4 (« D'où viennent ces chiffres », Étape 4/4) : l'épine de provenance s'affiche en pleine largeur.
5. « Voir le scénario météo → » → passe bien à l'étape 2 du tunnel principal (fil d'Ariane à 3 puces réapparaît).
6. Sur l'étape 2, cliquer « ← Retour au résultat » → revient à l'étape 1 sur l'écran 4 (pas sur le formulaire vide).
7. Vérifier `prefers-reduced-motion` (émulation DevTools) : l'animation d'entrée des écrans est coupée.

- [ ] **Step 7: End-of-task check (no git repo — skip commit)**

No commit; move to Task 5.

---

### Task 5: Nettoyage final et vérification globale

**Files:**
- Modify: `app.py` (suppression de code mort résiduel s'il y en a)

- [ ] **Step 1: Rechercher les usages résiduels de `render_result`**

Run: `grep -rn "render_result" app.py ui/ tests/`
Expected: aucune occurrence (la fonction a été entièrement supprimée en Task 4, Step 3, et son seul appelant a été remplacé par le routage à 4 écrans).

- [ ] **Step 2: Suite de tests complète**

Run: `.venv/bin/python -m pytest tests/ -q`
Expected: PASS, tous tests verts, y compris `tests/test_assolement_tunnel.py` et `tests/test_styles.py` ajoutés dans ce plan.

- [ ] **Step 3: Lancer l'app et fournir le lien de test**

Run: `make run` (ou `.venv/bin/python -m streamlit run app.py`)
Relever l'URL locale affichée dans la sortie (typiquement `http://localhost:8501`) et la transmettre à l'utilisateur pour test manuel.

- [ ] **Step 4: End-of-task check (no git repo — skip commit)**

No commit — informer l'utilisateur que le dépôt n'est pas versionné avec git si un suivi de version est souhaité pour ce travail.
