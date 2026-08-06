# Terroir Context Agents

Terroir Context Agents aide à comparer trois cultures **avant le semis** en
positionnant leur stade de besoin critique face à une tension saisonnière sur
l'eau. Les chiffres sont calculés en Python, datés, puis reliés à leur provenance.
Cette version est une démonstration hors ligne, pas un conseil agronomique ou
financier.

## Démarrage rapide

```bash
make install
make demo
```

L'interface Streamlit est alors disponible sur `http://localhost:8501`.

## Architecture

Trois agents forment une boucle autour de DataHub :

- **Cartographe** (`catalog/`) décrit sources, schémas, ownership, vocabulaire et
  lineage. Il peut émettre le graphe vers DataHub ou construire la fixture locale.
- **Conseiller** (`services/recommendation_service.py`) contrôle d'abord la porte
  de confiance, date les stades par degrés-jours, calcule eau, coût et marge, puis
  produit le contrat O1.
- **Sentinelle** (`agents/sentinelle.py`) détecte une source périmée, parcourt tout
  son lineage descendant, marque les assets et écrit un rapport d'impact.

DataHub est le runtime de contexte central : les services découvrent les assets et
vérifient le lineage depuis le graphe; la recommandation est refusée si la chaîne
est rompue. Le mode agriculture utilise `fixtures/graph.json` sans serveur, ou les
API publiques IGN RPG, geo.api.gouv.fr et Hub'Eau pour charger un territoire réel
anonymisé. Le mode
générique conserve le backend DataHub et analyse les datapacks officiels.

Les champs manquants suivent une chaîne explicite : source principale, source
publique secondaire, puis interpolation IDW en dernier recours. Chaque valeur
conserve sa méthode, sa source et son niveau de confiance; une interpolation n'est
jamais présentée comme une mesure.

## Prérequis et commandes

Python 3.9 ou ultérieur et GNU Make sont requis. `make install` crée `.venv` à la
racine. DataHub n'est requis que pour le
mode générique ou l'émission du catalogue.

```bash
make install       # installe Streamlit, pytest et le SDK DataHub
make run           # lance l'application
make fixture       # valide et normalise la fixture hors ligne
make demo          # construit la fixture et lance la démo agricole
make test          # exécute les tests unitaires
make clean         # retire rapports et caches Python
```

Mode DataHub générique :

```bash
datahub docker quickstart
datahub datapack load nyc-taxi
make demo-generic
```

`make quickstart` et `make graph` restent disponibles pour démarrer DataHub et
émettre le catalogue agricole complet. `DATAHUB_GMS` et `DATAHUB_TOKEN` configurent
le serveur; aucune clé n'est nécessaire hors ligne.

## Structure

`app.py` contient uniquement l'orchestration UI. `services/` porte les calculs et
les contrôles. `ui/` produit le seul graphique, un SVG accessible, et l'épine de
provenance. `agents/` et `catalog/` conservent les interfaces DataHub. `data/`
contient les données synthétiques, `fixtures/` le graphe, `tests/` les tests et
`reports/` les impacts générés.

## Porte de confiance

- **Haute** : SLA respectés, lineage complet et aucun risque critique.
- **Dégradée** : source hors SLA ou référence critique `dire_d_expert`; les chiffres
  restent visibles avec la cause exacte.
- **Insuffisante** : source critique au-delà de deux fois son SLA ou lineage rompu;
  la liste des cultures est vide et aucun chiffre décisionnel n'est rendu.

Le contrôle utilise `last_updated`, `freshness_sla_days`, `niveau_de_preuve`,
`spatial_coverage` et `licence` de chaque dataset.

## Simulation de panne

Le bouton de l'interface force l'obsolescence de `hubeau_hydrometrie`, appelle la
même classe `Sentinelle` que le mode DataHub, parcourt les descendants, invalide les
recommandations visibles et écrit `reports/impact_…_station.json`. Le nombre affiché
est dérivé des recommandations présentes et de la présence réelle de l'asset final
dans le lineage.

## Limites, licences et sources

Les modèles sont volontairement simplifiés : normales thermiques sinusoïdales,
bilan hydrique agrégé et coûts indicatifs. Ils ne remplacent ni une prévision météo,
ni un modèle hydrologique opérationnel, ni un conseil professionnel. Les données
sont synthétiques, sans données personnelles; leur statut est détaillé dans
`data/SOURCES.md`. Le code est distribué sous Apache License 2.0.
