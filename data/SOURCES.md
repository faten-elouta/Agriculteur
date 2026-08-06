# Sources et statut des données

Le dépôt ne contient aucune donnée synthétique de parcelle : les parcelles affichées
sont chargées à la demande depuis le RPG public anonymisé de l'IGN (API Carto), les
communes depuis `geo.api.gouv.fr`, et les stations d'eau depuis Hub'Eau. Le seul
fichier de données embarqué est le référentiel agro-économique
(`cultures_reference.json`), construit à partir de sources publiques : FAO-56 pour
les coefficients culturaux, statistiques Agreste pour les rendements, barèmes
publics des chambres d'agriculture et redevances des agences de l'eau. Il s'agit de
valeurs de référence indicatives et datées, pas de mesures.

Aucune observation tierce n'est redistribuée dans ce dépôt. Aucune donnée nominative
d'exploitant n'est collectée ni conservée. Le code est sous licence Apache 2.0. Les
polices IBM Plex (`static/fonts/`) sont distribuées sous licence SIL Open Font
License 1.1, auto-hébergées pour fonctionner hors ligne, sans CDN.

## Résolution des données en cascade

- **Communes** : `geo.api.gouv.fr`, référentiel officiel de l'État.
- **Parcelles** : RPG IGN via l'API Carto, plusieurs millésimes essayés du plus
  récent au plus ancien.
- **Eau disponible** : référentiel des stations hydrométriques Hub'Eau, complété par
  les stations piézométriques si nécessaire.
- **Sol et réserve utile** : le RPG ne fournit ni type de sol ni réserve utile.
  L'application tente d'abord la source secondaire ISRIC SoilGrids. Si elle est
  indisponible ou incomplète, elle utilise une interpolation spatiale IDW de points
  de référence régionaux, annoncée comme une estimation de confiance faible. Une
  analyse renseignée par l'utilisateur reste prioritaire.
- **Scénarios climatiques futurs et valeurs économiques** restent modélisés et sont
  toujours signalés comme tels.

Chaque source essayée, retenue ou rejetée est journalisée et visible dans
l'interface (« Sources de secours essayées »), avec sa méthode et son niveau de
confiance. Si aucune source pertinente ne répond, la valeur reste absente ;
l'interpolation n'est utilisée que pour les champs où elle est méthodologiquement
défendable.
