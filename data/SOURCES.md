# Sources et statut des données

Les parcelles, séries climatiques et valeurs agronomiques livrées sont entièrement
synthétiques. Elles servent uniquement à rendre la démonstration reproductible.
Elles s'inspirent de méthodes et ordres de grandeur publics : FAO-56 pour le bilan
hydrique, statistiques Agreste pour les rendements, normales climatiques publiques
et barèmes publics des chambres d'agriculture.

Les noms de services HubEau décrivent des sources publiques sous Licence Ouverte
Etalab 2.0, mais aucune observation tierce n'est redistribuée dans ce dépôt. Les
parcelles sont fictives et ne contiennent aucune donnée personnelle. Le code est
sous licence Apache 2.0.

## Mode données réelles

L'interface peut interroger directement, sans clé, `geo.api.gouv.fr` pour les
communes, l'API Carto RPG de l'IGN pour des parcelles agricoles publiques
anonymisées, et Hub'Eau pour le référentiel des stations hydrométriques.

Le RPG ne fournit ni type de sol ni réserve utile. L'application tente d'abord la
source secondaire ISRIC SoilGrids. Si elle est indisponible ou incomplète, elle
utilise une interpolation spatiale IDW de points de référence régionaux, annoncée
comme une estimation de confiance faible. Une analyse renseignée par l'utilisateur
reste prioritaire. Les scénarios climatiques futurs et valeurs économiques restent
modélisés et sont toujours signalés comme tels. Aucune donnée nominative
d'exploitant n'est collectée ou conservée.

Pour les autres champs, la résolution suit aussi une cascade journalisée : plusieurs
millésimes RPG sont essayés, puis les stations hydrométriques Hub'Eau sont complétées
par les stations piézométriques si nécessaire. Si aucune source pertinente ne
répond, la valeur reste absente; l'interpolation n'est utilisée que pour les champs
où elle est méthodologiquement défendable.
