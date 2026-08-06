# Modernisation de l'interface — scène météo animée réactive

Date : 2026-08-03

## Contexte

L'application (`app.py`, Streamlit) suit aujourd'hui un brief de design très
strict (`brief.md`) : palette encre/papier, une seule couleur d'accent
réservée à la confiance des données, et une règle explicite d'absence
d'animation ("Pas d'animation d'apparition [...] Rien d'autre ne bouge").

Décision validée avec l'utilisateur : on **remplace** cette charte par une
interface moderne et vivante (scène météo animée : soleil, nuages, pluie,
herbe qui pousse), tout en gardant **toute la logique et les fonctionnalités
existantes strictement inchangées** — seule la couche de présentation change.

Contrainte explicite de l'utilisateur, ajoutée après la première validation :
**rester professionnel et épuré**. La scène météo est une couche
d'information supplémentaire pour un public d'agriculteurs, pas une
décoration ludique. Priorité constante : la clarté de la réponse
("quelle culture choisir et pourquoi") ne doit jamais être diluée par
l'habillage visuel.

## Objectif

Une interface qui reste lisible et sérieuse pour un usage professionnel,
mais dont l'ambiance visuelle (ciel, météo, végétation) reflète les données
réelles affichées — rendant l'état des cultures et la tension sur l'eau
intuitivement perceptibles avant même de lire les chiffres.

## Approche technique

Tout en **CSS/HTML pur**, injecté comme aujourd'hui via
`st.markdown(unsafe_allow_html=True)`. Pas de nouvelle dépendance, pas de
CDN — l'app doit continuer à fonctionner hors ligne.

- **Pluie** : fines lignes (`div`) positionnées en absolu avec
  `@keyframes fall` en boucle ; nombre d'éléments généré selon l'intensité
  calculée côté Python.
- **Soleil / nuages** : formes CSS (cercle + ombres radiales), dérive lente
  des nuages (`@keyframes drift`), légère pulsation du soleil. Traits fins,
  pas d'iconographie "cartoon" — cohérent avec un usage professionnel.
- **Herbe qui pousse** : bande de brins fins (`transform-origin: bottom`,
  `scaleY` animé une fois au chargement), densité/hauteur variables.
- Nouveau module `ui/weather_scene.py` : fonction pure qui prend un état
  météo calculé (ex. `{"pluie": 0.6, "soleil": True, "nuages": 2}`) et
  retourne le HTML/CSS inline correspondant. Aucune logique métier dedans —
  seulement du rendu à partir d'un état déjà décidé par `app.py`.
- `prefers-reduced-motion: reduce` coupe toutes les animations ; les formes
  restent visibles à l'état statique.

Alternative écartée : `components.html` avec canvas/JS pour un rendu plus
réaliste — rejetée : isole l'animation dans un iframe difficile à
resynchroniser avec les re-runs Streamlit, plus lourd, sans bénéfice net vu
le style plat et sobre retenu.

## Système visuel

- **Palette** : ciel en dégradé doux `#4A90D9 → #FFD37A` (jour → doré),
  jamais saturé ; herbe `#3F7A5A` / `#2E5940` ; cartes blanches `#FFFFFF`,
  ombre discrète `0 4px 20px rgba(0,0,0,.08)`, coins arrondis `14px`. Les
  couleurs d'état métier existantes sont conservées telles quelles :
  vert `--sur` (sûr), ambre `--vigilance` (à surveiller), rouge `--rupture`
  (risque/rupture) — la scène météo vient renforcer ce code couleur, jamais
  le remplacer ni le contredire.
- **Typographie** : IBM Plex conservée (auto-hébergée, déjà en place,
  lisible). Titres en Plex Serif, corps en Plex Sans, chiffres en Plex Mono
  — cette dernière règle du brief reste : elle aide justement à distinguer
  ce qui est mesuré de ce qui est écrit, utile pour un public professionnel.
- **Densité de l'animation** : plafonnée et discrète — but : donner une
  impression d'ambiance vivante en périphérie du regard, jamais capter
  l'attention au détriment des chiffres. Maximum ~40 gouttes de pluie et
  ~15 brins d'herbe visibles simultanément ; aucune animation en boucle sur
  les zones de texte ou de données.
- **Layout** : scène météo fixe en en-tête (~140px, ciel + soleil/nuages/
  pluie), contenu en cartes blanches sur fond clair uni sous la scène. Une
  bande d'herbe animée sert de séparateur avant l'avertissement final —
  pas d'illustration ailleurs sur la page.

## Réactivité aux données

| Donnée source | Effet visuel |
|---|---|
| Bande "tension eau" du calendrier — mois en tension forte affiché | Pluie plus dense dans la scène d'en-tête |
| Culture à l'état "sûr" | Petit soleil + brin d'herbe animé à côté de sa carte |
| Culture à risque / rupture | Nuage + gouttes discrètes à côté de sa carte |
| Confiance haute / dégradée / insuffisante | Ciel dégagé / nuageux / orageux dans la scène d'en-tête |
| Panne de station simulée | Bref épisode orageux (éclair CSS + pluie dense) accompagnant la propagation sur l'épine |
| Après "Rétablir la station" | Retour progressif à un ciel dégagé |

Chaque effet visuel est **redondant avec une information déjà écrite**
(texte, pastille, chiffre) — jamais le seul vecteur du sens, pour rester
accessible et pour qu'un agriculteur pressé puisse ignorer l'animation sans
rien perdre.

## Écrans concernés

Fonctionnalités et logique Python **inchangées** dans tous les cas
(`services/`, contrats de données, calculs) — seule la présentation change,
fichier par fichier :

- **En-tête** (`app.py` haut de page) : scène météo animée remplace le
  bandeau plat ; titre dans une carte flottante.
- **Formulaire parcelle/semis** : regroupé en une carte blanche unique,
  contrôles Streamlit restylés (arrondis, focus visible net — accessibilité
  clavier conservée).
- **Résultat** (calendrier de recouvrement, "ce qu'il faut retenir",
  leviers, simulation) : cartes par culture avec micro-météo contextuelle.
  Le calendrier SVG (`ui/calendar_svg.py`) reste un tracé sobre, sans
  animation — c'est la pièce de lecture technique au centre d'une interface
  vivante autour, et sa lisibilité prime.
- **Épine de provenance** (`ui/provenance_spine.py`) : même fonction, redessinée
  en carte verticale arrondie, même code couleur qu'aujourd'hui.
- **Vue experte / rapport / sentinelle** : mêmes contenus et structure de
  cartes ; scène météo minimale ou absente ici pour ne pas gêner la lecture
  de tableaux de données denses.

## Accessibilité

- `prefers-reduced-motion: reduce` → animations coupées, formes statiques
  conservées.
- Aucun état porté uniquement par la couleur ou l'animation : chaque
  pastille garde son libellé texte (règle héritée du brief original).
- Focus clavier visible sur tous les contrôles.
- Contraste AA maintenu sur fond clair (vérifié sur les nouvelles couleurs
  de cartes/texte, pas seulement sur l'ancien papier/encre).

## Hors périmètre

- Aucun changement de logique métier, de calculs, de contrats de données
  (`O1`, DataHub, etc.).
- Aucune nouvelle dépendance Python.
- Le calendrier de recouvrement (`ui/calendar_svg.py`) garde son tracé
  actuel — seul son cadre visuel (carte, marges) change.

## Tests / vérification

- Vérification manuelle via `make run` : parcourir le parcours complet
  (sélection parcelle → comparaison → panne simulée → restauration) et
  confirmer que chaque état de donnée déclenche le bon état météo.
- Test `prefers-reduced-motion` via les DevTools navigateur (émulation).
- Aucun test automatisé existant ne couvre le rendu HTML/CSS — pas de
  nouveau test unitaire requis pour `ui/weather_scene.py` au-delà d'un test
  simple vérifiant que la fonction ne lève pas d'exception et renvoie du
  HTML valide pour les états limites (aucune pluie, pluie max, etc.), pour
  rester cohérent avec la couverture existante de `ui/`.
