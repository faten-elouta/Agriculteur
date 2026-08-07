# Refonte de l'écran de décision (Spec 1)

## Contexte

Test du parcours agriculteur complet (via `streamlit.testing.v1.AppTest`, commune réelle
Vierzon, données RPG/SoilGrids/Hub'Eau en direct) : le calcul et les données sont bons,
mais le chemin pour arriver à la réponse est long (4 écrans avant "Comment éviter", puis
2 étapes de plus pour le détail), et l'écran de réponse mélange décision et jargon data
("SLA", "certificat", "garanties élevées 3/7") au même niveau de lecture.

Retour agriculteur détaillé : voir la conversation du 2026-08-07. Point important tranché
avec l'utilisatrice : la comparaison climatique 2035/2050 (mentionnée dans ce retour)
nécessite une vraie source de données pluriannuelle (Open-Meteo Climate API, vérifiée
disponible, gratuite, sans clé, CMIP6, 1950-2050) — c'est un chantier séparé (Spec 2),
volontairement hors de cette spec pour ne fabriquer aucun chiffre.

## Objectif

Restructurer l'écran de résultat en pyramide de décision (décision → pourquoi → preuve),
sans toucher au moteur de calcul (`services/recommendation_service.py`), à la liste des
3 cultures (`data/cultures_reference.json`), ni ajouter de donnée non réelle.

## Changements

### 1. Navigation

`ASSOLEMENT_SCREEN_COUNT` passe de 4 à 2 :
- Écran 1 — Parcelle (inchangé).
- Écran 2 — Résultat (nouveau, fusionne les anciens écrans réponse + comment éviter +
  provenance).

Les étapes 2 (scénario météo) et 3 (audit technique) du parcours principal restent
inchangées et toujours accessibles, mais ne sont plus dans le chemin obligatoire pour
obtenir une réponse.

### 2. Écran Résultat — 3 niveaux

**Niveau 1 — Décision** (toujours visible en premier)
- Tableau des 3 cultures classées : Culture · État · Marge €/ha · Eau (mm) · Risque
  principal — à partir des champs déjà calculés (`rang`, `etat`, `marge_brute_eur_ha`,
  `besoin_irrigation_mm`, `stade_critique`).
- Phrase de synthèse à l'affirmative, dérivée de `retain_sentence`/`analysis_article`.
- Comparateur "remplacer X par Y" : deux sélecteurs de culture (par défaut culture
  actuelle de la parcelle vs mieux classée), affichage côte à côte Eau/Risque/Marge,
  phrase de conclusion générée sur le même modèle que `analysis_article`. Aucune
  nouvelle donnée — second angle de lecture sur `result["cultures"]`.

**Niveau 2 — Pourquoi** (déplié par défaut)
- Phrase causale déjà calculée pour la culture la plus à risque (dates stade critique
  vs fenêtre de tension).
- Leviers déjà calculés (`levers_panel`), inchangés.
- Une ligne courte par culture (y compris les cultures sûres), généralisation de
  `retain_sentence` à toutes les cultures.

**Niveau 3 — Preuve** (expander fermé par défaut, contenu inchangé, juste déplacé)
- Certificat de données + tableau de bord KPI Confiance (SLA, garanties, traçabilité).
- Graphe de lineage et provenance (ancien écran 4).

### 3. CTA

- `hero_html()` : "Lancer l'application" → "Analyser ma parcelle"
- `cta_html()` : "Lancer l'application →" → "Analyser ma parcelle →"
- Bouton de calcul dans l'écran Parcelle : "Comparer les cultures pour cette parcelle" →
  "Analyser ma parcelle"
- Le lead de la page d'accueil ne mentionne pas le climat futur (ça reste la promesse de
  la Spec 2, pas encore livrée).

## Hors scope

Moteur de calcul, liste des cultures, scénario météo, audit technique, toute donnée
climatique pluriannuelle (Spec 2, séparée).

## Vérification

- `pytest` (suite existante) doit rester au vert.
- Parcours agriculteur complet rejoué via `AppTest` (commune réelle, calcul, écran
  résultat, comparateur, expander preuve) sans exception.
