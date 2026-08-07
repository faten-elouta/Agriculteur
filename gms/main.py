"""Serveur GMS-compatible pour la démo publique.

Implémente le sous-ensemble de l'API OpenAPI de DataHub GMS utilisé par
l'application (fraîcheur, lineage, runs, incidents), avec les données seedées
depuis fixtures/graph.json. Stockage en mémoire : l'état se réinitialise au
redémarrage — adapté à la démo, pas à la production.

Endpoints (contrat identique à DataHub GMS) :
- GET  /health
- GET  /openapi/v3/entity/dataset/{urn}?aspects=...
- GET  /openapi/v3/entity/dataset/{urn}/lineage
- POST /openapi/v3/entity/dataset
- POST /openapi/v3/entity/mlModel
- POST /openapi/v3/entity/incident
- POST /openapi/v3/entity/incident/{urn}
- GET/POST /openapi/v3/entity/agentSkill (Skills DataHub)
- GET/POST /openapi/v3/entity/aiAgent   (Agent Context Kit)

En plus, le même graphe est exposé en Model Context Protocol (MCP) à /mcp :
https://terroir-context-gms.onrender.com/mcp (voir gms/mcp_server.py).
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

ROOT = Path(__file__).resolve().parent.parent
GRAPH_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "graph.json"

try:
    from gms.mcp_server import mcp as _mcp  # noqa: E402

    _MCP_HTTP = _mcp.http_app(transport="streamable-http", allowed_origins=["*"])
except ModuleNotFoundError:
    _mcp = None
    _MCP_HTTP = None

app = FastAPI(title="Terroir Context Agents — GMS compatible (démo)", lifespan=_MCP_HTTP.lifespan if _MCP_HTTP else None)

_STORE: dict[str, dict[str, Any]] = {}
_RELATIONSHIPS: dict[str, list[dict[str, str]]] = {}
_INCIDENTS: dict[str, dict[str, Any]] = {}
_INCIDENT_COUNTER = 0
_SKILLS: dict[str, dict[str, Any]] = {}
_AGENTS: dict[str, dict[str, Any]] = {}

_DEMO_SKILLS: list[dict[str, Any]] = [
    {
        "urn": "urn:li:agentSkill:freshness_sla",
        "name": "Surveillance de la fraîcheur des sources",
        "description": "Règles de surveillance de la fraîcheur des sources (SLA vs dernière mise à jour) et gestion des incidents.",
        "instructions": "Procédure : (1) appeler freshness_summary, (2) pour chaque source stale lire le lineage aval, (3) créer un incident OPERATIONAL sur le premier asset aval impacté, (4) tracer le run via emit_run. Ne jamais supposer une date de mise à jour : lire last_updated dans le graphe.",
        "sourceRepository": {"url": "https://github.com/faten-elouta/Agriculteur", "path": "catalog/skills/freshness_sla/SKILL.md"},
    },
    {
        "urn": "urn:li:agentSkill:recommandations",
        "name": "Modèle recommandations_parcelle",
        "description": "Fiche modèle du modèle de recommandation de culture : provenance (lineage amont) et règles d'explication.",
        "instructions": "Pour expliquer une recommandation : lire le lineage du modèle via get_lineage, vérifier la fraîcheur des sources amont via freshness_summary, citer la provenance. Les valeurs climatiques futures et économiques sont modélisées : toujours le signaler.",
        "sourceRepository": {"url": "https://github.com/faten-elouta/Agriculteur", "path": "catalog/skills/recommandations/SKILL.md"},
    },
    {
        "urn": "urn:li:agentSkill:codegen",
        "name": "Génération de code metadata-aware",
        "description": "Workflow de génération de recettes d'ingestion, SQL et DAG Airflow à partir des schémas, du lineage et des propriétés réels lus dans DataHub.",
        "instructions": "Découvrir les datasets via la recherche, lire les schémas réels (schemaMetadata), lire le lineage (upstreamLineage) pour les dépendances, reporter les propriétés réelles dans la recette (transformers). Jamais de champ inventé : si le schéma est vide, produire un artefact honnête.",
        "sourceRepository": {"url": "https://github.com/faten-elouta/Agriculteur", "path": "catalog/skills/codegen/SKILL.md"},
    },
]


def short_name(urn: str) -> str:
    parts = urn.split(",")
    return parts[1] if len(parts) > 1 else urn.split(":")[-1]


def _load_graph() -> dict[str, Any]:
    if not GRAPH_PATH.exists():
        raise RuntimeError(f"fixtures/graph.json introuvable : {GRAPH_PATH}")
    return json.loads(GRAPH_PATH.read_text(encoding="utf-8"))


def _seed() -> None:
    graph = _load_graph()
    _STORE.clear()
    _RELATIONSHIPS.clear()
    _INCIDENTS.clear()
    _SKILLS.clear()
    _AGENTS.clear()
    for urn, props in graph.get("datasets", {}).items():
        custom = {
            "niveau_de_preuve": str(props.get("niveau_de_preuve", "")),
            "freshness_sla_days": str(props.get("freshness_sla_days", "")),
            "last_updated": str(props.get("last_updated", "")),
            "spatial_coverage": str(props.get("spatial_coverage", "")),
            "licence": str(props.get("licence", "")),
            "redistribuable": str(props.get("redistribuable", "")),
        }
        _STORE[urn] = {
            "name": short_name(urn),
            "description": "Source de contexte Terroir Context Agents — licence et SLA déclarés par l'ingestion.",
            "customProperties": custom,
        }
    for skill in _DEMO_SKILLS:
        _SKILLS[skill["urn"]] = skill
    lineage = graph.get("lineage", {})
    for urn in list(_STORE):
        upstreams = [k for k, targets in lineage.items() if urn in targets]
        downstreams = lineage.get(urn, [])
        _RELATIONSHIPS[urn] = [{"entity": u, "type": "UPSTREAM"} for u in upstreams] + [
            {"entity": d, "type": "DOWNSTREAM"} for d in downstreams
        ]


_seed()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/")
async def root() -> dict:
    return {
        "service": "Terroir Context Agents — serveur GMS compatible (démo)",
        "datasets": len(_STORE),
        "incidents": len(_INCIDENTS),
        "graph": str(GRAPH_PATH),
    }


@app.get("/openapi/v3/entity/dataset/{urn}")
async def dataset_get(urn: str, aspects: Optional[str] = None) -> dict:
    entity = _STORE.get(urn)
    if entity is None:
        return {"results": []}
    wanted = set((aspects or "").split(",")) if aspects else None
    result_aspects: dict[str, Any] = {}
    if wanted is None or "datasetProperties" in wanted:
        result_aspects["datasetProperties"] = entity
    if wanted is None or "status" in wanted:
        result_aspects["status"] = {"removed": False}
    return {"results": [{"urn": urn, "aspects": result_aspects}]}


@app.get("/openapi/v3/entity/dataset/{urn}/lineage")
async def dataset_lineage(urn: str) -> dict:
    if urn not in _STORE:
        return {"results": []}
    return {"results": [{"urn": urn, "relationships": _RELATIONSHIPS.get(urn, [])}]}


@app.post("/openapi/v3/entity/dataset")
async def dataset_upsert(request: Request) -> dict:
    body = await request.json()
    urn = body.get("urn", "")
    aspects = body.get("aspects", {})
    properties = aspects.get("datasetProperties", {})
    existing = _STORE.get(urn, {"name": short_name(urn), "description": "", "customProperties": {}})
    custom = dict(existing.get("customProperties", {}))
    custom.update(properties.get("customProperties", {}))
    _STORE[urn] = {
        "name": properties.get("name", existing.get("name", short_name(urn))),
        "description": properties.get("description", existing.get("description", "")),
        "customProperties": custom,
    }
    return JSONResponse(status_code=201, content={"results": [{"urn": urn}]})


@app.post("/openapi/v3/entity/mlModel")
async def ml_model_upsert(request: Request) -> dict:
    body = await request.json()
    urn = body.get("urn", "")
    _STORE.setdefault(urn, {"name": short_name(urn), "description": "", "customProperties": {}})
    return JSONResponse(status_code=201, content={"results": [{"urn": urn}]})


@app.post("/openapi/v3/entity/incident")
async def incident_create(request: Request) -> dict:
    global _INCIDENT_COUNTER
    body = await request.json()
    _INCIDENT_COUNTER += 1
    urn = f"urn:li:incident:(demo,{_INCIDENT_COUNTER})"
    info = body.get("aspects", {}).get("incidentInfo", {})
    _INCIDENTS[urn] = {
        "title": info.get("title", ""),
        "description": info.get("description", ""),
        "entityUrns": body.get("entityUrns", []),
        "status": "ACTIVE",
        "createdAt": info.get("createdAt", int(time.time() * 1000)),
    }
    return JSONResponse(status_code=201, content={"results": [{"urn": urn}]})


@app.post("/openapi/v3/entity/incident/{urn}")
async def incident_update(urn: str, request: Request) -> dict:
    body = await request.json()
    info = body.get("aspects", {}).get("incidentInfo", {})
    incident = _INCIDENTS.setdefault(urn, {"title": "", "description": "", "entityUrns": [], "status": "ACTIVE"})
    state = info.get("status", {}).get("state", "ACTIVE")
    if state == "RESOLVED":
        incident["status"] = "RESOLVED"
        incident["resolvedAt"] = info.get("resolvedAt", int(time.time() * 1000))
    else:
        incident["status"] = state
    return {"results": [{"urn": urn}]}


@app.get("/openapi/v3/entity/incident/{urn}")
async def incident_get(urn: str) -> dict:
    incident = _INCIDENTS.get(urn)
    if incident is None:
        return {"results": []}
    return {
        "results": [
            {
                "urn": urn,
                "aspects": {
                    "incidentInfo": {
                        "incidentType": "OPERATIONAL",
                        "title": incident["title"],
                        "description": incident["description"],
                        "status": {"state": incident["status"]},
                        "createdAt": incident.get("createdAt"),
                    }
                },
            }
        ]
    }


# ---------------------------------------------------------------------------
# Contrat SDK acryl-datahub : GraphQL (get_urns_by_filter) + OpenAPI v2 batch
# (get_entities_v2). Ces deux endpoints permettent au mode réel du serveur MCP
# (gms/mcp_server.py, DATAHUB_GMS_URL) de lire ce graphe via le vrai client SDK.
# ---------------------------------------------------------------------------

def _match_urns(entity_types: list[str] | None, query: str) -> list[str]:
    types = {t.upper() for t in (entity_types or ["DATASET"])}
    if types & {"AGENTSKILL", "AGENT_SKILL"}:
        urns = [urn for urn in _SKILLS if urn.startswith("urn:li:agentSkill:")]
        return _filter_by_query(urns, query)
    if types & {"AI_AGENT"}:
        urns = [urn for urn in _AGENTS if urn.startswith("urn:li:aiAgent:")]
        return _filter_by_query(urns, query)
    if types and not types & {"DATASET", "DATASET_PLATFORM"}:
        return []
    urns = [urn for urn in _STORE if urn.startswith("urn:li:dataset:")]
    return _filter_by_query(urns, query)


def _filter_by_query(urns: list[str], query: str) -> list[str]:
    if query and query != "*":
        lowered = query.lower()
        return [urn for urn in urns if lowered in short_name(urn).lower()]
    return urns


@app.post("/api/graphql")
async def graphql(request: Request) -> dict:
    """Sous-ensemble GraphQL utilisé par le SDK : scrollUrnsWithFilters → scrollAcrossEntities."""
    body = await request.json()
    query_text = body.get("query", "")
    variables = body.get("variables") or {}
    if "scrollAcrossEntities" not in query_text:
        return {"data": {}}
    entity_types = variables.get("types")
    search_query = variables.get("query", "*")
    urns = _match_urns(entity_types, search_query)
    batch_size = variables.get("batchSize") or len(urns)
    page = urns[:batch_size]
    return {
        "data": {
            "scrollAcrossEntities": {
                "nextScrollId": None,
                "searchResults": [{"entity": {"urn": urn}} for urn in page],
            }
        }
    }


@app.post("/openapi/v2/entity/batch/{entity_name}")
async def entity_batch_v2(entity_name: str, request: Request) -> dict:
    """Batch v2 du SDK : renvoie les aspects demandés pour chaque URN (dataset)."""
    body = await request.json()
    urns = body.get("urns") or []
    aspect_names = body.get("aspectNames") or []
    entities = []
    for urn in urns:
        entity = _STORE.get(urn)
        if entity is None:
            continue
        aspects: dict[str, Any] = {}
        if not aspect_names or "datasetProperties" in aspect_names:
            aspects["datasetProperties"] = entity
        if not aspect_names or "status" in aspect_names:
            aspects["status"] = {"removed": False}
        entities.append({"urn": urn, "aspects": aspects})
    return {"entities": entities}


@app.get("/openapi/v3/entity/incident")
async def incident_list() -> dict:
    return {
        "results": [
            {
                "urn": urn,
                "aspects": {
                    "incidentInfo": {
                        "incidentType": "OPERATIONAL",
                        "title": incident["title"],
                        "description": incident["description"],
                        "status": {"state": incident["status"]},
                    }
                },
            }
            for urn, incident in _INCIDENTS.items()
        ]
    }


# ---------------------------------------------------------------------------
# Entités AgentSkill et AIAgent (contrat OpenAPI v3, mêmes formes que les
# datasets) : la chaîne réelle du serveur MCP (DataHubClient REST) et le SDK
# acryl-datahub >= 1.7 peuvent lire/écrire ces entités sur ce graphe.
# ---------------------------------------------------------------------------

def _skill_get(urn: str) -> dict:
    skill = _SKILLS.get(urn)
    if skill is None:
        return {"results": []}
    return {"results": [{"urn": urn, "aspects": {"agentSkillInfo": {k: v for k, v in skill.items() if k != "urn"}}}]}


@app.get("/openapi/v3/entity/agentSkill/{urn}")
async def agent_skill_get(urn: str) -> dict:
    return _skill_get(urn)


@app.get("/openapi/v3/entity/aiAgent/{urn}")
async def ai_agent_get(urn: str) -> dict:
    agent = _AGENTS.get(urn)
    if agent is None:
        return {"results": []}
    return {"results": [{"urn": urn, "aspects": {"aiAgentInfo": {k: v for k, v in agent.items() if k != "urn"}}}]}


@app.post("/openapi/v3/entity/agentSkill")
async def agent_skill_upsert(request: Request) -> dict:
    body = await request.json()
    urn = body.get("urn", "")
    info = body.get("aspects", {}).get("agentSkillInfo", {})
    if not urn:
        return JSONResponse(status_code=400, content={"error": "urn requis"})
    skill = dict(info)
    skill["name"] = info.get("name", short_name(urn))
    _SKILLS[urn] = {"urn": urn, **skill}
    return JSONResponse(status_code=201, content={"results": [{"urn": urn}]})


@app.post("/openapi/v3/entity/aiAgent")
async def ai_agent_upsert(request: Request) -> dict:
    body = await request.json()
    urn = body.get("urn", "")
    info = body.get("aspects", {}).get("aiAgentInfo", {})
    if not urn:
        return JSONResponse(status_code=400, content={"error": "urn requis"})
    agent = dict(info)
    agent["name"] = info.get("name", short_name(urn))
    _AGENTS[urn] = {"urn": urn, **agent}
    return JSONResponse(status_code=201, content={"results": [{"urn": urn}]})


@app.post("/aspects")
async def aspects_legacy(request: Request) -> dict:
    """Endpoint legacy du GMS (ingestProposal) : utilisé par le SDK acryl-datahub
    (AgentSkill.emit / Agent.emit, CLI `datahub agent-skill register`)."""
    action = request.query_params.get("action")
    if action != "ingestProposal":
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    body = await request.json()
    body = body.get("proposal") or body  # le SDK enveloppe dans {"proposal": {...}}
    entity_type = body.get("entityType", "")
    urn = body.get("entityUrn", "")
    aspect_name = body.get("aspectName", "")
    try:
        aspect = json.loads((body.get("aspect") or {}).get("value", "{}"))
    except (ValueError, TypeError):
        return JSONResponse(status_code=400, content={"error": "aspect invalide"})
    if entity_type == "agentSkill" and urn.startswith("urn:li:agentSkill:") and aspect_name == "agentSkillInfo":
        _SKILLS[urn] = {"urn": urn, **aspect}
    elif entity_type == "aiAgent" and urn.startswith("urn:li:aiAgent:") and aspect_name == "aiAgentInfo":
        _AGENTS[urn] = {"urn": urn, **aspect}
    elif aspect_name == "status":
        pass  # aspect statut (removed) : accepté sans stockage
    else:
        return JSONResponse(status_code=400, content={"error": f"entité/aspect non supporté : {entity_type}/{aspect_name}"})
    return {"value": "0"}


if _MCP_HTTP is not None:
    app.mount("/", _MCP_HTTP)
