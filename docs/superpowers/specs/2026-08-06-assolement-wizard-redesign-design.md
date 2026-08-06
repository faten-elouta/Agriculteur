# Refonte de l'étape 1 en tunnel séquentiel — maquette Claude Design `Assolement.dc.html`

Date : 2026-08-06

## Contexte

La maquette Claude Design du projet « Site explications et légende »
(`Assolement.dc.html`, `support.js`) propose, pour l'outil « Choisir sa
culture », un parcours en **4 écrans successifs** — un à la fois, avec
navigation ‹ Précédent / Suivant › et une barre de progression à 4
segments : *La question* → *La réponse* → *Comment éviter* → *D'où
viennent ces chiffres*.

L'application actuelle (`app.py`) traite déjà ce contenu, mais dans
l'étape 1 de son propre tunnel à 3 étapes (« Parcelle & résultat »,
« Scénario météo », « Détails techniques ») : le formulaire de saisie et
le tableau de bord de résultat sont affichés **côte à côte en deux
colonnes**, et non l'un après l'autre.

Décision validée avec l'utilisateur :
- L'étape 1 actuelle est **remplacée** par ce tunnel séquentiel à 4
  écrans. Les étapes 2 (Scénario météo) et 3 (Détails techniques) du
  tunnel principal ne changent pas.
- **Toute la fonctionnalité existante est conservée** — aucune logique
  de `services/*` ni contrat de données ne change, seule la présentation
  et l'agencement de l'étape 1 changent.
- Tous les contrôles du formulaire actuel (bascule Réelles/Démonstration,
  recherche de commune, expander d'analyse de sol, horizon 3/6/12 mois,
  carrousel d'intro) restent réunis sur le premier écran (« La
  question »), réagencés au style de la maquette plutôt que déplacés
  dans un menu séparé.
- Le tableau de simulation (`data_editor`) et la génération/téléchargement
  du rapport CSV rejoignent l'écran « La réponse », à la suite de la
  phrase de synthèse — emplacement logique le plus proche de l'actuel.
- Le bandeau de confiance et le certificat de qualité des données restent
  en haut de l'écran « La réponse », juste avant le calendrier.

## Objectif

Remplacer la disposition en deux colonnes de l'étape 1 par un parcours
guidé, un écran à la fois, fidèle à la maquette (typographie, couleurs,
barre de progression, animation d'entrée `omFadeUp`), sans rien retirer
de ce que l'utilisateur peut faire aujourd'hui à cette étape.

## Modèle de navigation

Nouvel état de session `st.session_state.assolement_screen` (entier,
1 à 4), actif uniquement pendant que le tunnel principal est à
`step == 1`. Initialisé à `1` à la première visite. Remis à `1`
uniquement dans le même cas où `step` est déjà forcé à `1` aujourd'hui
(absence de `result` en session) — sinon il conserve le dernier écran
visité. Ainsi, revenir à l'étape 1 depuis l'étape 2 via
« ← Retour au résultat » republie l'écran interne où l'utilisateur se
trouvait (typiquement l'écran 4, « D'où viennent ces chiffres », d'où
il a quitté le tunnel), sans jamais forcer un nouveau passage par le
formulaire « La question » tant qu'un résultat existe déjà — condition
nécessaire pour ne rien retirer du confort actuel (aujourd'hui, revenir
à l'étape 1 réaffiche directement le résultat, jamais le formulaire
vide).

En-tête propre à ces 4 écrans (remplace le fil d'Ariane à 3 puces
existant tant qu'on est sur l'étape 1) :
- Titre « Choisir sa culture » + libellé mono « Étape X / 4 », comme la
  maquette.
- Barre de progression à 4 segments fins (nouvelle classe CSS
  `.om-progress`), plutôt que le composant `.step-indicator` à puces
  numérotées déjà utilisé pour le tunnel principal — pour rester fidèle
  au langage visuel spécifique de cette maquette. Le fil d'Ariane à 3
  puces réapparaît normalement aux étapes 2 et 3.

Navigation bas de chaque écran : deux boutons ‹ Précédent / Suivant ›
(même helper `step_nav` que le reste de l'app, réutilisé avec les mêmes
conventions de `key=`). Règles de garde :
- Écran 1 (« La question ») : pas de bouton Précédent (premier écran du
  tunnel interne) ; bouton Suivant désactivé tant qu'aucun résultat n'a
  été calculé (même garde que le `next_disabled=not has_cultures`
  actuel).
- Écrans 2 et 3 : Précédent / Suivant classiques entre écrans internes.
- Écran 4 (« D'où viennent ces chiffres ») : le bouton Suivant sort du
  tunnel interne et va à l'étape 2 du tunnel principal (Scénario météo)
  — reprend le comportement de l'actuel bouton « Voir le scénario
  météo → ».

Le calcul du résultat (`build_recommendation` et tout l'enrichissement
qui suit dans `app.py`) reste déclenché par le même bouton « Comparer
les cultures pour cette parcelle », sur l'écran 1, sans navigation
automatique — l'utilisateur avance explicitly avec « Suivant ».

## Écrans

### 1. La question

Contenu identique à l'actuel panneau de gauche de l'étape 1, dans
l'ordre existant, sur une colonne centrée `max-width:760px` (au lieu de
`st.columns([0.38, 0.62])`) :
1. Carrousel d'intro (`INTRO_SLIDES`, boutons ‹ ›).
2. Bascule Réelles / Démonstration (`st.radio`).
3. Si Réelles : recherche de commune + bouton de recherche + résultats
   (`fetch_real_territory`) ; sinon parcelles de démonstration.
4. Sélecteur de parcelle, date de semis, horizon d'étude — reste un
   `st.segmented_control` (aucun widget interactif ne peut être remplacé
   par du HTML statique sans perdre la liaison à l'état Python) ; son
   CSS actuel (`ui/styles.py`, règles `[data-baseweb="button-group"]`)
   donne déjà le rendu « bouton plein encre sur l'actif » de la maquette
   — aucun changement de style nécessaire ici.
5. Ligne de faits sol/parcelle + expander « J'ai une analyse de sol plus
   précise » (inchangé).
6. Bouton « Comparer les cultures pour cette parcelle ».

Aucune donnée ni service ne change ; uniquement la mise en page (une
colonne au lieu de deux) et le style des boutons d'horizon.

### 2. La réponse

Reprend l'actuel `render_result`, sans la colonne épine (déplacée à
l'écran 4) :
1. `confidence_notice` puis bandeau `trust-banner` (certificat qualité) —
   identiques à aujourd'hui.
2. `render_timeline(result)` — déjà quasiment au pixel près la maquette
   (le docstring de `ui/assolement.py` le confirme), inchangé.
3. Bloc « Ce qu'il faut retenir » (`retain_sentence`) et
   `analysis_article`.
4. Tableau de simulation (`st.data_editor` sur les 10 colonnes de coûts)
   et `simulation_recap_html`.
5. Génération et téléchargement du rapport (boutons + `st.caption` du
   chemin archivé).

Le panneau des leviers (`levers_panel`) n'est **plus** affiché ici : il
devient le contenu propre de l'écran 3, pour correspondre à l'écran
dédié « Comment éviter » de la maquette (évite la redite).

### 3. Comment éviter

- S'il existe une culture à risque (`risky` non nul, même calcul que
  l'actuel `max(at_risk_crops, ...)`) : réutilise `levers_panel(risky)`
  tel quel.
- Sinon : message repris de la maquette (état `noRisk`), formulé de façon
  cohérente avec `analysis_article` côté « aucune collision » — par
  exemple « Aucune culture ne nécessite d'ajustement : aucune ne croise
  la tension en eau prévue sur cette fenêtre. »

### 4. D'où viennent ces chiffres

Réutilise `render_spine(graph, impacted)` (aucun changement de
`ui/provenance_spine.py`), affiché en pleine largeur de l'écran plutôt
qu'en colonne latérale collante (`position: sticky`) — nouvelle classe
CSS de wrapper sans `sticky` ni largeur contrainte, mais en gardant la
carte (bordure, ombre) cohérente avec le reste de l'app plutôt que le
fond transparent de la maquette, pour rester visuellement homogène avec
les autres écrans de l'app.

## Système visuel

- Réutilise les jetons de couleur déjà définis (`--papier/--encre/
  --craie/--sur/--vigilance/--rupture` dans `ui/styles.py`), déjà
  alignés sur la maquette.
- Ajoute l'animation d'entrée `omFadeUp` (déjà présente dans la maquette,
  à porter dans `ui/styles.py`) sur le conteneur de chaque écran du
  tunnel, coupée sous `prefers-reduced-motion: reduce` (cohérent avec la
  règle déjà appliquée aux autres animations de l'app).
- Nouvelle classe `.om-progress` (4 segments fins, actif = encre, à
  venir = craie) + libellé mono « Étape X / 4 », visible seulement
  pendant le tunnel interne de l'étape 1.

## Fichiers impactés

- `app.py` — remplacement du bloc `if step == 1:` par la logique du
  tunnel interne à 4 écrans (nouvel état `assolement_screen`, routage
  des 4 écrans, garde de navigation). Les blocs `elif step == 2:` et
  `elif step == 3:` ne changent pas.
- `ui/assolement.py` — nouvelles fonctions de rendu : en-tête du tunnel
  interne (barre de progression + « Étape X / 4 »), écran « Comment
  éviter » côté « aucun risque ». `render_timeline`,
  `simulation_recap_html`, `levers_panel`, `analysis_article`,
  `retain_sentence`, `intro_slide_html` sont réutilisées sans
  modification.
- `ui/styles.py` — ajout des classes `.om-progress`, du conteneur
  centré à 760px, de l'animation `omFadeUp`, du style des boutons
  d'horizon, et de la variante non collante de `.assolement-spine` pour
  l'écran 4.
- `ui/provenance_spine.py`, `services/*`, `ui/step_nav.py` — inchangés.

## Hors périmètre

- Aucun changement de logique métier, de calculs ou de contrats de
  données.
- Aucune nouvelle dépendance Python ni JavaScript (le runtime `<x-dc>` /
  `support.js` de la maquette n'est pas exécutable dans Streamlit — il
  ne sert que de référence visuelle, comme le confirme déjà le docstring
  de `ui/assolement.py` pour `render_timeline`).
- Le comportement des étapes 2 (Scénario météo) et 3 (Détails
  techniques) du tunnel principal ne change pas.
- Pas de fonctionnalité « appliquer un levier et recalculer le
  scénario » : la maquette simule ce comportement côté JS (`MAIZE_
  SIMULATED`) à titre de démonstration, mais l'app actuelle n'a pas
  cette fonctionnalité et elle n'est pas demandée — `levers_panel` reste
  purement informatif, comme aujourd'hui.

## Tests / vérification

- Vérification manuelle via `make run` : parcourir le tunnel interne
  complet (question → réponse → comment éviter → d'où viennent ces
  chiffres → scénario météo), avec une parcelle de démonstration et une
  recherche réelle, pour confirmer qu'aucune donnée ni action n'a
  disparu par rapport à l'étape 1 actuelle.
- Vérifier le cas « aucune culture à risque » sur l'écran 3 (ex. en
  ajustant temporairement les données de démonstration si aucun cas
  réel n'est disponible).
- Vérifier `prefers-reduced-motion` (émulation DevTools) sur l'animation
  d'entrée des écrans.
- Aucun test automatisé existant ne couvre le rendu HTML de `ui/` ; pas
  de nouveau test unitaire requis au-delà de la couverture actuelle,
  sauf si une fonction Python testable isolément (ex. le calcul du texte
  « aucun risque ») est extraite — à trancher dans le plan
  d'implémentation.
