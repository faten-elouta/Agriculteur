# Modernisation de l'interface — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer l'habillage visuel sobre actuel par une interface moderne, épurée et professionnelle, avec une scène météo animée (soleil, nuages, pluie, herbe qui pousse) qui réagit aux données réelles, sans toucher à la logique métier.

**Architecture:** Nouveau module pur `ui/weather_scene.py` (état météo calculé à partir de `st.session_state`/`result`, rendu HTML/CSS) + réécriture de `ui/styles.py` (nouvelle palette sur les mêmes noms de variables CSS, cards, keyframes) + intégration ciblée dans `app.py` (en-tête, bande d'herbe) et `ui/assolement.py` (badge météo par culture). Le calendrier SVG (`ui/calendar_svg.py`) reste sobre, seul son fond change pour s'intégrer à une carte blanche.

**Tech Stack:** Python 3.9, Streamlit, CSS/HTML injecté (aucune nouvelle dépendance, aucun CDN), pytest.

## Global Constraints

- Aucune nouvelle dépendance Python (`requirements.txt` inchangé).
- Aucune requête réseau/CDN — tout doit fonctionner hors ligne.
- Logique métier, calculs et contrats de données strictement inchangés — seule la présentation change.
- Couleurs d'état métier conservées : `--sur` `#3F7A5A`, `--vigilance` `#C08A2E`, `--rupture` `#A63D2F`.
- Chaque effet météo doit être redondant avec un texte/pastille déjà existant (jamais le seul vecteur d'information) — ajouter `aria-hidden="true"` sur les éléments purement décoratifs.
- `prefers-reduced-motion: reduce` coupe toutes les animations ajoutées.
- Densité plafonnée : max 40 gouttes de pluie, max 15 brins d'herbe simultanés.

---

### Task 1: Module `ui/weather_scene.py` (état météo + rendu)

**Files:**
- Create: `ui/weather_scene.py`
- Test: `tests/test_weather_scene.py`

**Interfaces:**
- Produces: `compute_header_state(session_state: Mapping[str, Any]) -> dict` (clés: `rain: float[0..1]`, `clouds: int[0..4]`, `sun: bool`, `storm: bool`), `render_header_scene(state: Mapping, eyebrow: str, title: str) -> str`, `crop_badge_html(etat: str) -> str`, `render_grass_band() -> str`. Consommés par Task 2 (`app.py`) et Task 3 (`ui/assolement.py`).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_weather_scene.py
from ui.weather_scene import compute_header_state, render_header_scene, crop_badge_html, render_grass_band


def test_compute_header_state_default_calm_without_result():
    assert compute_header_state({}) == {"rain": 0.0, "clouds": 1, "sun": True, "storm": False}


def test_compute_header_state_storm_on_failure_message():
    state = compute_header_state({"failure_message": "3 recommandations invalidées."})
    assert state["storm"] is True
    assert state["rain"] > 0.5


def test_compute_header_state_scales_with_at_risk_ratio():
    result = {"cultures": [{"etat": "sûr"}, {"etat": "rupture"}], "confiance": {"niveau": "haute"}}
    state = compute_header_state({"result": result})
    assert 0.0 < state["rain"] < 1.0
    assert state["sun"] is False


def test_compute_header_state_insuffisante_confidence_forces_rain():
    result = {"cultures": [], "confiance": {"niveau": "insuffisante"}}
    state = compute_header_state({"result": result})
    assert state["rain"] >= 0.8
    assert state["sun"] is False


def test_render_header_scene_returns_valid_html_for_extreme_states():
    calm = render_header_scene({"rain": 0.0, "clouds": 0, "sun": True, "storm": False}, "EYEBROW", "Titre")
    assert "<h1>Titre</h1>" in calm
    assert 'class="sun"' in calm
    stormy = render_header_scene({"rain": 1.0, "clouds": 4, "sun": False, "storm": True}, "E", "T")
    assert stormy.count('class="drop"') <= 40
    assert 'class="flash"' in stormy


def test_render_header_scene_escapes_title():
    out = render_header_scene({"rain": 0, "clouds": 0, "sun": False, "storm": False}, "<x>", "<y>")
    assert "<x>" not in out
    assert "<y>" not in out


def test_crop_badge_html_variants_render_without_error():
    for etat in ["sûr", "vigilance", "rupture"]:
        assert "crop-badge" in crop_badge_html(etat)


def test_render_grass_band_caps_blade_count():
    assert render_grass_band().count('class="blade"') == 15
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_weather_scene.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'ui.weather_scene'`

- [ ] **Step 3: Write the implementation**

```python
# ui/weather_scene.py
"""Scène météo animée : état dérivé des données, rendu en CSS/HTML pur.

Chaque effet visuel double une information déjà écrite ailleurs (pastille
d'état, texte de confiance) — jamais le seul vecteur du sens.
"""

from __future__ import annotations

import html
from typing import Any, Mapping

RAIN_DROPS_MAX = 40
GRASS_BLADES_MAX = 15


def compute_header_state(session_state: Mapping[str, Any]) -> dict[str, Any]:
    """Dérive l'état météo de l'en-tête à partir du session_state Streamlit."""
    if session_state.get("failure_message"):
        return {"rain": 0.9, "clouds": 3, "sun": False, "storm": True}
    result = session_state.get("result")
    if not result:
        return {"rain": 0.0, "clouds": 1, "sun": True, "storm": False}
    cultures = result.get("cultures", [])
    confidence = result.get("confiance", {}).get("niveau", "haute")
    if confidence == "insuffisante":
        return {"rain": 0.85, "clouds": 3, "sun": False, "storm": False}
    at_risk = [c for c in cultures if c.get("etat") != "sûr"]
    ratio = len(at_risk) / len(cultures) if cultures else 0.0
    return {
        "rain": round(0.15 + 0.55 * ratio, 2),
        "clouds": 1 + round(2 * ratio),
        "sun": ratio < 0.5,
        "storm": False,
    }


def render_header_scene(state: Mapping[str, Any], eyebrow: str, title: str) -> str:
    """Rend la scène d'en-tête (ciel, soleil/nuages, pluie) avec le titre en surimpression."""
    n_drops = max(0, min(RAIN_DROPS_MAX, round(state.get("rain", 0.0) * RAIN_DROPS_MAX)))
    drops = "".join(_drop_html(i) for i in range(n_drops))
    n_clouds = max(0, min(4, int(state.get("clouds", 0))))
    clouds = "".join(_cloud_html(i) for i in range(n_clouds))
    sun = '<div class="sun" style="width:46px;height:46px;top:18px;right:36px;" aria-hidden="true"></div>' if state.get("sun") else ""
    flash = '<div class="flash" aria-hidden="true"></div>' if state.get("storm") else ""
    return (
        '<div class="weather-hero">'
        f'{sun}{clouds}{drops}{flash}'
        '<div class="hero-title">'
        f'<span class="eyebrow">{html.escape(eyebrow)}</span>'
        f'<h1>{html.escape(title)}</h1>'
        "</div>"
        "</div>"
    )


def _drop_html(index: int) -> str:
    left = (index * 37) % 100
    delay = (index * 0.13) % 2.0
    duration = 1.1 + (index % 5) * 0.15
    height = 14 + (index % 4) * 4
    return (
        f'<div class="drop" aria-hidden="true" style="left:{left}%;height:{height}px;'
        f'animation-duration:{duration:.2f}s;animation-delay:-{delay:.2f}s;"></div>'
    )


def _cloud_html(index: int) -> str:
    top = 14 + (index % 3) * 22
    width = 60 + (index % 3) * 20
    duration = 26 + (index % 3) * 8
    delay = index * 6
    return (
        f'<div class="cloud" aria-hidden="true" style="top:{top}px;width:{width}px;height:{width * 0.4:.0f}px;'
        f'animation-duration:{duration}s;animation-delay:-{delay}s;"></div>'
    )


def crop_badge_html(etat: str) -> str:
    """Pastille météo à côté d'une culture — décorative, redondante avec l'état écrit."""
    if etat == "sûr":
        return '<span class="crop-badge" aria-hidden="true"><span class="mini-sun"></span></span>'
    if etat == "vigilance":
        return '<span class="crop-badge" aria-hidden="true"><span class="mini-cloud"></span></span>'
    return '<span class="crop-badge" aria-hidden="true"><span class="mini-cloud"></span><span class="mini-drop"></span></span>'


def render_grass_band() -> str:
    """Bande d'herbe animée, séparateur avant l'avertissement final."""
    blades = "".join(_blade_html(i) for i in range(GRASS_BLADES_MAX))
    return f'<div class="grass-band" aria-hidden="true">{blades}</div>'


def _blade_html(index: int) -> str:
    left = index * (100 / GRASS_BLADES_MAX) + (index % 3)
    height = 18 + (index % 4) * 4
    delay = (index % 5) * 0.08
    return (
        f'<div class="blade" style="left:{left:.1f}%;height:{height}px;'
        f'animation-delay:{delay:.2f}s;"></div>'
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_weather_scene.py -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add ui/weather_scene.py tests/test_weather_scene.py
git commit -m "feat: add data-reactive weather scene module"
```

---

### Task 2: Nouvelle palette, cards et keyframes dans `ui/styles.py`

**Files:**
- Modify: `ui/styles.py` (réécriture complète du bloc `CSS`, mêmes noms de variables Python/CSS consommés ailleurs)

**Interfaces:**
- Consumes: rien (CSS pur).
- Produces: variables CSS `--papier --encre --craie --eau --sur --vigilance --rupture --card --radius --shadow --sky-top --sky-bottom --grass --grass-dark`, classes `.weather-hero .sun .cloud .drop .flash .hero-title`, `.crop-badge .mini-sun .mini-cloud .mini-drop`, `.grass-band .blade`. Consommées par Task 1 (déjà écrit), Task 3, `app.py`.

- [ ] **Step 1: Remplacer `:root` et ajouter les nouvelles variables**

Dans `ui/styles.py`, remplacer la ligne :
```
:root { --papier:#F7F6F3; --encre:#1B2430; --craie:#E2E0DA; --eau:#2E6F8E; --sur:#3F7A5A; --vigilance:#C08A2E; --rupture:#A63D2F; }
```
par :
```
:root {
  --papier:#F6F7F5; --encre:#1F2A24; --craie:#E4E7E2; --eau:#2E6F8E;
  --sur:#3F7A5A; --vigilance:#C08A2E; --rupture:#A63D2F;
  --card:#FFFFFF; --radius:14px; --radius-sm:10px; --shadow:0 4px 20px rgba(15,23,20,.08);
  --sky-top:#4A90D9; --sky-bottom:#FFD37A; --grass:#3F7A5A; --grass-dark:#2E5940;
}
```
(`--sur`, `--vigilance`, `--rupture` gardent exactement leur valeur actuelle — aucune régression sur le code couleur d'état.)

- [ ] **Step 2: Adoucir les rayons de bordure existants**

Remplacer `border-radius: 2px !important;` (règle `button, input, select, [data-baseweb="select"] > div`) par `border-radius: var(--radius-sm) !important;`.

Remplacer chaque `border-radius:2px;` restant dans le fichier (classes `.confidence-banner`, `.trust-banner`... — présentes dans les règles CSS de `styles.py`, pas dans `assolement.py`) par `border-radius:var(--radius);` et ajouter `box-shadow:var(--shadow);` sur les mêmes règles : `.confidence-banner`, `.trust-banner`, `.expert-heading`, `.confidence-title`, `.confidence-actions`, `.failure-flow span`, `.spine`, `.waiting-story`, `.sentinel-box`.

- [ ] **Step 3: Ajouter les styles de la scène météo, des badges et de l'herbe**

Ajouter à la fin du bloc `<style>` (avant `</style>`) :

```css
.weather-hero { position:relative; overflow:hidden; border-radius:var(--radius); height:150px; margin:0 0 1rem; background:linear-gradient(180deg,var(--sky-top),var(--sky-bottom)); box-shadow:var(--shadow); }
.weather-hero .sun { position:absolute; border-radius:50%; background:#FFDE7A; box-shadow:0 0 40px 10px rgba(255,222,122,.55); animation:sunPulse 6s ease-in-out infinite; }
.weather-hero .cloud { position:absolute; background:#FFFFFF; opacity:.92; border-radius:40px; animation:cloudDrift linear infinite; }
.weather-hero .drop { position:absolute; width:2px; top:-10%; background:rgba(255,255,255,.7); border-radius:1px; animation:rainFall linear infinite; }
.weather-hero .flash { position:absolute; inset:0; background:#fff; opacity:0; animation:lightning 2.4s ease-in-out infinite; }
.weather-hero .hero-title { position:absolute; left:1.3rem; bottom:1rem; }
.weather-hero .hero-title .eyebrow { color:#fff; opacity:.92; text-shadow:0 1px 6px rgba(0,0,0,.25); }
.weather-hero .hero-title h1 { color:#fff; margin:.15rem 0 0; font-size:22px; text-shadow:0 1px 6px rgba(0,0,0,.25); }
@keyframes sunPulse { 0%,100% { transform:scale(1); } 50% { transform:scale(1.06); } }
@keyframes cloudDrift { from { transform:translateX(-20%); } to { transform:translateX(340%); } }
@keyframes rainFall { from { transform:translateY(0); opacity:.9; } to { transform:translateY(160px); opacity:.15; } }
@keyframes lightning { 0%,92%,100% { opacity:0; } 94% { opacity:.55; } 96% { opacity:0; } }

.crop-badge { display:inline-flex; align-items:center; gap:3px; margin-left:8px; vertical-align:middle; }
.crop-badge .mini-sun { width:11px; height:11px; border-radius:50%; background:#FFB020; box-shadow:0 0 6px 2px rgba(255,176,32,.4); display:inline-block; }
.crop-badge .mini-cloud { width:15px; height:9px; border-radius:8px; background:#B9C4CC; display:inline-block; }
.crop-badge .mini-drop { width:2px; height:6px; background:var(--eau); border-radius:1px; display:inline-block; animation:dropBlink 1.1s linear infinite; }
@keyframes dropBlink { 0%,100% { opacity:.3; } 50% { opacity:1; } }

.grass-band { position:relative; height:34px; margin:1.4rem 0 .8rem; overflow:hidden; }
.grass-band .blade { position:absolute; bottom:0; width:3px; background:var(--grass); border-radius:3px 3px 0 0; transform-origin:bottom; animation:growBlade .6s ease-out both; }
@keyframes growBlade { from { transform:scaleY(0); } to { transform:scaleY(1); } }

[data-testid="stVerticalBlockBorderWrapper"] { border:1px solid var(--craie) !important; border-radius:var(--radius) !important; background:var(--card) !important; box-shadow:var(--shadow) !important; }

@media (prefers-reduced-motion:reduce) {
  .weather-hero .sun, .weather-hero .cloud, .weather-hero .drop, .weather-hero .flash,
  .grass-band .blade, .crop-badge .mini-drop { animation:none !important; }
  .grass-band .blade { transform:scaleY(1); }
}
```

- [ ] **Step 4: Vérifier que l'app démarre sans erreur CSS**

Run: `.venv/bin/python -m pytest tests/test_weather_scene.py -v` (aucune régression attendue, ce fichier ne teste pas le CSS mais confirme que rien n'est cassé côté Python)
Puis lancer manuellement `make run` et vérifier dans le navigateur qu'aucune erreur ne s'affiche (voir Task 5).

- [ ] **Step 5: Commit**

```bash
git add ui/styles.py
git commit -m "style: modern palette, cards and weather keyframes"
```

---

### Task 3: Badges météo par culture dans `ui/assolement.py`

**Files:**
- Modify: `ui/assolement.py:149` (ligne du nom de culture dans `render_timeline`)

**Interfaces:**
- Consumes: `crop_badge_html(etat: str) -> str` (Task 1).

- [ ] **Step 1: Importer la fonction**

En haut de `ui/assolement.py`, ajouter :
```python
from ui.weather_scene import crop_badge_html
```

- [ ] **Step 2: Insérer le badge à côté du nom de la culture**

Remplacer :
```python
            f'<div style="font-family:\'IBM Plex Serif\',serif;font-weight:600;font-size:16px;padding-right:8px;">{html.escape(c["culture"].capitalize())}</div>'
```
par :
```python
            f'<div style="font-family:\'IBM Plex Serif\',serif;font-weight:600;font-size:16px;padding-right:8px;">{html.escape(c["culture"].capitalize())}{crop_badge_html(c["etat"])}</div>'
```

- [ ] **Step 3: Vérifier manuellement**

Run: `.venv/bin/python -m pytest tests/ -q` (suite complète, doit rester verte)

- [ ] **Step 4: Commit**

```bash
git add ui/assolement.py
git commit -m "feat: show weather badge next to each crop row"
```

---

### Task 4: Intégration de la scène météo et de l'herbe dans `app.py`

**Files:**
- Modify: `app.py` (imports, bloc d'en-tête, séparateur avant l'avertissement final)

**Interfaces:**
- Consumes: `compute_header_state`, `render_header_scene`, `render_grass_band` (Task 1).

- [ ] **Step 1: Ajouter l'import**

Dans le bloc d'imports `ui.*` de `app.py`, ajouter :
```python
from ui.weather_scene import compute_header_state, render_header_scene, render_grass_band
```

- [ ] **Step 2: Remplacer l'en-tête statique par la scène météo**

Remplacer :
```python
st.markdown(
    '<div class="compact-header"><span class="eyebrow">PRÉPARER MON PROCHAIN SEMIS</span>'
    "<h1>Quelle culture choisir pour ma parcelle ?</h1></div>",
    unsafe_allow_html=True,
)
```
par :
```python
weather_state = compute_header_state(st.session_state)
st.markdown(
    render_header_scene(weather_state, "PRÉPARER MON PROCHAIN SEMIS", "Quelle culture choisir pour ma parcelle ?"),
    unsafe_allow_html=True,
)
```

- [ ] **Step 3: Ajouter la bande d'herbe avant l'avertissement final**

Remplacer :
```python
st.markdown('<div class="final-warning"><strong>Avant de décider</strong><p>Confirmez l'analyse de sol, vos prix, vos charges, votre accès à l'eau et la place de la culture dans votre rotation avec votre conseiller.</p></div>', unsafe_allow_html=True)
```
par :
```python
st.markdown(render_grass_band(), unsafe_allow_html=True)
st.markdown('<div class="final-warning"><strong>Avant de décider</strong><p>Confirmez l'analyse de sol, vos prix, vos charges, votre accès à l'eau et la place de la culture dans votre rotation avec votre conseiller.</p></div>', unsafe_allow_html=True)
```

- [ ] **Step 4: Fond blanc du calendrier SVG pour s'intégrer aux cartes**

Dans `ui/calendar_svg.py`, remplacer :
```python
'<rect width="1080" height="100%" fill="#F7F6F3"/>'
```
par :
```python
'<rect width="1080" height="100%" fill="#FFFFFF"/>'
```

- [ ] **Step 5: Test manuel de bout en bout**

Run: `.venv/bin/python -m pytest tests/ -q` (suite complète verte)
Puis : `make demo` (ou réutiliser le serveur déjà lancé) et vérifier dans le navigateur :
1. En-tête affiche un ciel dégagé avec soleil tant qu'aucun résultat n'est calculé.
2. Après « Comparer les cultures », l'en-tête reflète la tension (pluie/nuages) si une culture est à risque.
3. Après « Simuler une panne de station », l'en-tête passe en orage (éclair + pluie dense).
4. Après « Rétablir la station et recalculer », l'en-tête revient à l'état basé sur le résultat.
5. Chaque ligne de culture affiche son badge météo à côté du nom.
6. La bande d'herbe s'anime juste avant l'avertissement final.
7. Activer "Réduire les animations" dans les DevTools (emulate `prefers-reduced-motion: reduce`) et vérifier que tout redevient statique.

- [ ] **Step 6: Commit**

```bash
git add app.py ui/calendar_svg.py
git commit -m "feat: wire reactive weather scene and grass band into app.py"
```
