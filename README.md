# Terroir Context Agents

[![CI](https://github.com/faten-elouta/Agriculteur/actions/workflows/ci.yml/badge.svg)](https://github.com/faten-elouta/Agriculteur/actions/workflows/ci.yml)

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

## Site vitrine

L'application s'ouvre sur une landing page (format consilium-bsf.fr/vision) avec
des onglets de navigation en haut :

- **Vision** (accueil) : hero avec collage de photos de cultures, chiffres clés,
  présentation « un conseil fondé sur les données », valeurs, expertises
  illustrées et approche en trois étapes (`ui/site_sections.py`).
- **Application** : le tunnel décisionnel complet (parcelle → comparaison →
  scénario météo → provenance des chiffres).
- **Graphe & IA** : vue DataHub — graphe connecté, KPIs Confiance/Produit/IA,
  console de supervision de l'agent et lineage interactif.
- **Contact** : cartes équipe, code et live.

La navigation par onglets et les boutons d'action passent par des attributs
`data-nav` câblés en JavaScript (`ui/animations.py`) qui changent l'URL
(`?view=...`) — chaque vue est directement partageable. Les photos du collage
sont des versions web optimisées (`assets/cultures/web/`) embarquées en base64.

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
.venv/bin/python catalog/ingest_skills.py      # enregistre Skills + agent (Agent Context Kit)
.venv/bin/python catalog/ingest_skills.py --dry-run   # affiche les payloads sans appel réseau
```

## Serveur MCP (Model Context Protocol)

Le serveur GMS expose le même graphe de contexte via **MCP** (streamable HTTP) à
`https://terroir-context-gms.onrender.com/mcp` — l'agent peut lire le contexte
(fraîcheur, SLA, lineage) et **écrire** dans le graphe (runs, incidents) :

- 12 outils : `list_datasets`, `get_dataset`, `get_lineage`, `freshness_summary`,
  `emit_run`, `create_incident`, `resolve_incident`, `list_incidents`,
  `list_skills`, `get_skill`, `register_skill`, `agent_context`
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

## DataHub Skills et Agent Context Kit

Les agents ne devinent pas : leurs instructions et leur contexte viennent du
graphe, catalogués comme entités DataHub.

- **Skills** (`urn:li:agentSkill:<id>`, aspect `agentSkillInfo`) : 3 skills
  opérationnels définis en git au format agentskills.io —
  `catalog/skills/freshness_sla/SKILL.md` (surveillance fraîcheur/SLA),
  `catalog/skills/recommandations/SKILL.md` (fiche modèle) et
  `catalog/skills/codegen/SKILL.md` (génération de code metadata-aware) ;
  `catalog/ingest_skills.py --dry-run` affiche les payloads,
  `catalog/ingest_skills.py` les enregistre dans le GMS.
- **Agent Context Kit** : l'agent lui-même est catalogué
  (`urn:li:aiAgent:terroir-context-agents`, aspect `aiAgentInfo`) et l'outil MCP
  `agent_context(datasets)` assemble en un seul objet le bundle de contexte
  (skills + fraîcheur + lineage) à injecter dans le prompt d'un agent.
- Interopérabilité vérifiée avec le SDK acryl-datahub ≥ 1.7
  (`datahub.api.entities.agent.agent_skill.AgentSkill`, `Agent`, CLI
  `datahub agent-skill register`) : les skills écrits via REST sont lus par le
  SDK et inversement (tests dédiés).

Contribution OSS au repo DataHub (bonus du hackathon) : voir
`contrib/datahub/README.md` — un skill « Freshness & SLA Monitoring » prêt à
soumettre au dossier `.agent-skills/` de datahub-project/datahub.

Le serveur MCP partage l'état en mémoire du GMS : un incident créé par l'agent
apparaît dans l'API OpenAPI (`/openapi/v3/entity/incident`) et inversement.

### Mode réel (graphe DataHub, pas le graphe de démonstration)

Si `DATAHUB_GMS_URL` est défini **dans l'environnement du serveur MCP**, chaque
outil lit et écrit dans un vrai GMS DataHub via `services/datahub_client.py`
(SDK `acryl-datahub` + REST OpenAPI) au lieu du graphe mémoire : fraîcheur,
lineage, runs et incidents sont ceux de l'instance DataHub réelle. Le serveur
MCP devient la passerelle d'agent vers le graphe réel.

```bash
DATAHUB_GMS_URL=https://votre-instance-datahub.example.com \
DATAHUB_TOKEN= \
uvicorn gms.main:app --port 8000        # MCP réel sur /mcp
```

Sans `DATAHUB_GMS_URL`, le serveur retombe sur le graphe mémoire seedé depuis
`fixtures/graph.json` (mode démonstration, idéal en développement local).

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
dans le lineage. La cascade d'impact est jouée en cinématique (nœuds qui passent au
rouge en séquence) avec compteur d'entités invalidées.

## Visuels de la décision (hackathon)

Six mises en scène complètent le tunnel, toutes alimentées par les données déjà
calculées (aucune source externe ajoutée) :

- **Graphe de lineage interactif** — DAG SVG des 8 sources jusqu'aux
  recommandations ; chaque nœud est coloré par sa fraîcheur réelle (SLA vs
  dernière mise à jour), une fiche `<details>` par entité (SLA, licence, niveau
  de preuve) et les arêtes « coulent » au défilement.
- **Console de supervision live** — bouton « Rejouer la supervision de l'agent » :
  la boucle complète (skills → fraîcheur → propagation du lineage → incident →
  run → résolution) se rejoue pas à pas ; en mode réel les écritures partent
  vraiment vers le graphe, sinon en simulation locale.
- **Carte parcellaire** — parcelles RPG réelles (géométries WGS84) reprojetées en
  SVG avec les stations Hub'Eau ; parcelle sélectionnée mise en évidence, fiches
  au clic.
- **Lame d'eau mensuelle** — graphique SVG des besoins d'irrigation par culture,
  barres qui poussent au défilement, fenêtre de tension hydrique signalée.
- **Cascade de panne cinématique** — propagation séquentielle de l'impact.
- **Mode démo auto** — bouton « ▶ Démo auto (vidéo) » qui enchaîne seul les six
  écrans du parcours (parcelle → résultat → météo → levers → provenance →
  détails techniques) avec une parcelle de démonstration hors réseau : idéal
  pour filmer la soumission Devpost.

Tous les modules vivent dans `ui/` (`lineage_graph.py`, `supervision_console.py`,
`parcel_map.py`, `water_chart.py`) et sont couverts par des tests.

## KPIs : Confiance, Produit, IA

Un tableau de bord de 18 indicateurs (3 familles × 6), calculés uniquement à
partir des données déjà produites par l'application — aucun chiffre inventé :

- **Confiance** — conformité SLA des sources (à jour / périmées / inconnues),
  part de sources en mesure directe, garanties élevées du certificat,
  fiabilité annoncée de la prévision, cultures au verdict sûr, traçabilité.
- **Produit** — cultures comparées, écart de marge (€/ha), besoin en eau
  cumulé (mm), jours de tension moyens, origine de la parcelle, étapes du
  parcours décisionnel.
- **IA & Agents** — score technique expert (/100), outils MCP exposés (12),
  skills chargés, incidents ouverts dans le graphe, modèle GR4J et version,
  runs tracés par exécution.

En mode connecté (`DATAHUB_GMS_URL`), les valeurs de graphe (fraîcheur,
skills, incidents) sont lues dans DataHub ; sinon le calcul local reproduit
les mêmes formules et la légende du tableau de bord le précise. Source :
`services/kpi_service.py` + `ui/kpis.py`.

## Limites, licences et sources

Les modèles sont volontairement simplifiés : normales thermiques sinusoïdales,
bilan hydrique agrégé et coûts indicatifs. Ils ne remplacent ni une prévision météo,
ni un modèle hydrologique opérationnel, ni un conseil professionnel. Les parcelles
et stations sont réelles et publiques, sans donnée personnelle; le statut détaillé
de chaque source est documenté dans `data/SOURCES.md`. Le code est distribué sous
Apache License 2.0.
