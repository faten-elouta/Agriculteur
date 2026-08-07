# Exemples

## `gms_demo.py` — démo autonome contre le graphe DataHub public

Interroge le serveur GMS-compatible hébergé sur Render
(`https://terroir-context-gms.onrender.com`, configurable via `DATAHUB_GMS_URL`)
avec la bibliothèque standard uniquement :

1. connecte au GMS et liste les 11 datasets du graphe de contexte (fraîcheur),
2. lit le lineage de `features_bilan_hydrique` (amont : climat, sol, parcelles,
   Hub'Eau… ; aval : scénarios cultures, modèle hydrologique),
3. écrit dans le graphe : trace un run `SUCCESS` sur `recommandations_parcelle`,
   crée puis résout un incident sur `sol_rrp`,
4. résume la fraîcheur des sources vs leur SLA annoncé.

```bash
python examples/gms_demo.py
```

## `generate_from_fixture.py` — génération de code metadata-aware

Exécute la même logique que `services/code_generation_service.py`
(`generate_ingestion_recipe`, `generate_transformation_sql`, `generate_airflow_dag`)
sur les 11 datasets réels du graphe de contexte Terroir (`fixtures/graph.json` —
le même graphe ingéré dans DataHub par `catalog/ingest_datahub.py`), sans
nécessiter d'instance DataHub en cours d'exécution :

```bash
.venv/bin/python examples/generate_from_fixture.py
```

Produit `examples/generated/` : recettes d'ingestion YAML par dataset (licence,
SLA, propriétés réelles), SQL de transformation, et un DAG Airflow avec les
dépendances dérivées du lineage réel (`climat_journalier → … → features_bilan_hydrique
→ … → recommandations_parcelle`). Le schéma de colonnes n'est pas suivi dans ce
graphe et n'est donc pas inventé (`fields=[]`).

Contre un DataHub en direct, `CodeGenerationService` lit en plus les schémas de
colonnes, tags et modèles ML réels via `DataHubClient.search_entities` /
`get_entity` (SDK `acryl-datahub`) :

```bash
DATAHUB_GMS_URL=http://localhost:8080 .venv/bin/python services/code_generation_service.py
```

## `mcp_agent_demo.py` — agent de supervision piloté par MCP

L'agent se connecte au **serveur MCP** du même graphe
(`https://terroir-context-gms.onrender.com/mcp`, protocol MCP streamable HTTP) et
fait un cycle de travail réel, uniquement par appels d'outils MCP :

1. lit `freshness_summary` et détecte les sources en dépassement de SLA,
2. parcourt le lineage aval de la première source périmée,
3. écrit dans le graphe : crée un incident sur les assets impactés,
4. trace son propre run sur `recommandations_parcelle`,
5. résout l'incident et réaffiche l'état final du graphe.

```bash
pip install "mcp>=2"
python examples/mcp_agent_demo.py
```

Le même serveur MCP peut être branché dans un client MCP (Claude Desktop,
MCP Inspector, etc.) :

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
