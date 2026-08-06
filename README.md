# Terroir Context Agents

Terroir Context Agents aide à comparer trois cultures **avant le semis** en
positionnant leur stade de besoin critique face à une tension saisonnière sur
l'eau. Les chiffres sont calculés en Python, datés, puis reliés à leur provenance.
Les parcelles sont des parcelles RPG réelles (IGN, anonymisées), les communes
proviennent du référentiel officiel et les stations d'eau de Hub'Eau. Cet outil
est une démonstration technique, pas un conseil agronomique ou financier.

## Démarrage rapide

```bash
make install
make run
```

L'interface Streamlit est alors disponible sur `http://localhost:8501`. Saisissez
une commune puis cliquez sur « Chercher les parcelles » : le RPG, le sol
(SoilGrids) et les stations Hub'Eau sont chargés en direct, sans clé API.

## Démo en ligne

- **Application** : https://terroir-context-agents.vercel.app (Streamlit, Vercel
  Fluid Compute, proxy HTTP + WebSocket)
- **Graphe de contexte DataHub** : https://terroir-context-gms.onrender.com
  (serveur GMS-compatible, conteneurisé, qui expose le graphe d'exemple de 11
  datasets — voir `render.yaml` et `gms/Dockerfile`)
- **Exemple autonome** : `python examples/gms_demo.py` interroge le GMS public
  (lecture, lineage, écriture de runs et d'incidents) avec la bibliothèque standard.

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
est rompue. Le mode agriculture utilise `fixtures/graph.json` sans serveur, et les
API publiques IGN RPG, geo.api.gouv.fr et Hub'Eau pour charger un territoire réel
anonymisé. Le mode générique conserve le backend DataHub et analyse les datapacks
officiels.

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
make run           # lance l'application (données réelles, sans clé API)
make fixture       # valide et normalise la fixture hors ligne
make demo          # lance l'application en mode serveur headless (démo)
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

## Connexion réelle à DataHub

L'application fonctionne par défaut sur la fixture locale, mais l'agent est conçu
pour s'appuyer sur un graphe DataHub lorsqu'un GMS est joignable :

```bash
export DATAHUB_GMS_URL=http://localhost:8080   # ou votre instance hébergée
export DATAHUB_TOKEN=                          # token DataHub Platform (facultatif)
.venv/bin/python catalog/ingest_datahub.py     # ingère datasets + lineage depuis fixtures/graph.json
.venv/bin/python catalog/ingest_datahub.py --dry-run   # affiche les payloads sans appel réseau
```

## Serveur MCP (Model Context Protocol)

Le serveur GMS expose le même graphe de contexte via **MCP** (streamable HTTP) à
`https://terroir-context-gms.onrender.com/mcp` — l'agent peut lire le contexte
(fraîcheur, SLA, lineage) et **écrire** dans le graphe (runs, incidents) :

- 8 outils : `list_datasets`, `get_dataset`, `get_lineage`, `freshness_summary`,
  `emit_run`, `create_incident`, `resolve_incident`, `list_incidents`
- Agent autonome : `python examples/mcp_agent_demo.py` (boucle supervision :
  source périmée → lineage aval → incident → run → résolution)
- Brancher dans Claude Desktop / MCP Inspector :

```json
{
  "mcpServers": {
    "terroir": {
      "url": "https://terroir-context-gms.onrender.com/mcp",
      "transport": "streamable-http"
    }
  }
}
```

Le serveur MCP partage l'état en mémoire du GMS : un incident créé par l'agent
apparaît dans l'API OpenAPI (`/openapi/v3/entity/incident`) et inversement.

Une fois connecté :

- l'écran « D'où viennent ces chiffres ? » lit la **fraîcheur réelle des sources
  dans DataHub** (SLA vs `last_updated`) et affiche l'état de chaque source ;
- chaque calcul écrit **l'état du run** sur `recommandations_parcelle`
  (`last_run_status`, `last_run_summary`, `last_run_at`) ;
- la simulation de panne de station crée un **incident DataHub** sur
  `hubeau_hydrometrie` ; « Rétablir la station » le résout.

Sans `DATAHUB_GMS_URL`, toutes ces étapes sont ignorées en silence : l'application
reste utilisable hors ligne, avec le bandeau « mode démonstration locale ».

## Structure

`app.py` contient uniquement l'orchestration UI. `services/` porte les calculs et
les contrôles. `ui/` produit le seul graphique, un SVG accessible, et l'épine de
provenance. `agents/` et `catalog/` conservent les interfaces DataHub. `data/`
contient le référentiel agro-économique et la documentation des sources,
`fixtures/` le graphe, `tests/` les tests et `reports/` les impacts générés.

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
ni un modèle hydrologique opérationnel, ni un conseil professionnel. Les parcelles
et stations sont réelles et publiques, sans donnée personnelle; le statut détaillé
de chaque source est documenté dans `data/SOURCES.md`. Le code est distribué sous
Apache License 2.0.
