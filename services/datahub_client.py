"""Client DataHub (GMS REST v3) avec repli local silencieux.

Permet à l'application de :
- lire le contexte des sources (fraîcheur, lineage) depuis le graphe DataHub,
- écrire ses résultats dans le graphe (état du dernier run, incidents),
- sans jamais casser le fonctionnement local quand DataHub est absent.

Contrat REST (OpenAPI v3 de DataHub GMS) :
- GET  /health                                        → contrôle de connexion
- GET  /openapi/v3/entity/dataset/{urn}?aspects=...    → propriétés d'un dataset
- GET  /openapi/v3/entity/dataset/{urn}/lineage        → lineage d'un dataset
- POST /openapi/v3/entity/dataset                      → upsert d'aspects
- POST /openapi/v3/entity/incident                     → création d'incident
- POST /openapi/v3/entity/incident/{urn}               → mise à jour d'incident

Toutes les méthodes renvoient None (jamais d'exception) quand DataHub est
injoignable ou que la réponse est inattendue.
"""

from __future__ import annotations

import itertools
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class DataHubClient:
    """Client minimaliste et défensif vers le GMS de DataHub."""

    def __init__(self, gms_url: str | None = None, token: str | None = None, timeout: float = 4.0) -> None:
        self.gms_url = (gms_url or os.getenv("DATAHUB_GMS_URL") or "").rstrip("/")
        self.token = token if token is not None else os.getenv("DATAHUB_TOKEN", "")
        self.timeout = timeout
        self.enabled = bool(self.gms_url)
        self._sdk_graph: Any = None

    # ------------------------------------------------------------------ HTTP
    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        if not self.enabled:
            return None
        url = f"{self.gms_url}{path}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Accept", "application/json")
        if body is not None:
            req.add_header("Content-Type", "application/json")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                payload = resp.read().decode("utf-8", errors="replace")
                return json.loads(payload) if payload else None
        except Exception:
            return None

    # ------------------------------------------------------------------- SDK
    def _graph(self) -> Any:
        """Instance SDK DataHub (acryl-datahub), pour la recherche et la lecture
        d'aspects que le sous-ensemble REST maison n'expose pas. Import tardif :
        une app qui ne fait ni recherche ni lecture d'entité n'a jamais besoin
        du SDK complet."""
        if self._sdk_graph is None:
            from datahub.ingestion.graph.client import DatahubClientConfig, DataHubGraph

            self._sdk_graph = DataHubGraph(DatahubClientConfig(server=self.gms_url, token=self.token or None))
        return self._sdk_graph

    # ---------------------------------------------------------------- lecture
    def connected(self) -> bool:
        """True si le GMS répond."""
        if not self.enabled:
            return False
        result = self._request("GET", "/health")
        return result is not None

    def dataset_properties(self, urn: str) -> dict[str, Any] | None:
        """Propriétés (customProperties incluses) d'un dataset, ou None."""
        path = f"/openapi/v3/entity/dataset/{urllib.parse.quote(urn, safe='')}?aspects=datasetProperties,status"
        result = self._request("GET", path)
        if not result:
            return None
        results = result.get("results") or []
        if not results:
            return None
        entity = results[0]
        properties = (entity.get("aspects") or {}).get("datasetProperties") or {}
        return {
            "urn": entity.get("urn") or urn,
            "name": properties.get("name"),
            "description": properties.get("description", ""),
            "custom_properties": properties.get("customProperties") or {},
        }

    def dataset_lineage(self, urn: str) -> list[dict[str, str]] | None:
        """Relations de lineage (amont et aval) d'un dataset."""
        path = f"/openapi/v3/entity/dataset/{urllib.parse.quote(urn, safe='')}/lineage"
        result = self._request("GET", path)
        if not result:
            return None
        results = result.get("results") or []
        if not results:
            return None
        entity = results[0]
        relationships = (entity.get("relationships") or []) if isinstance(entity, dict) else []
        edges: list[dict[str, str]] = []
        for relation in relationships:
            target = relation.get("entity") or relation.get("target")
            if not target:
                continue
            direction = (relation.get("type") or "").upper()
            edges.append({"urn": target, "direction": "UPSTREAM" if "UPSTREAM" in direction else "DOWNSTREAM"})
        return edges

    def search_entities(
        self,
        query: str = "*",
        entity_type: str = "DATASET",
        platform: str | None = None,
        count: int = 100,
    ) -> list[dict[str, Any]]:
        """Recherche d'URNs par type/plateforme (SDK `get_urns_by_filter`)."""
        if not self.enabled:
            return []
        try:
            urns = self._graph().get_urns_by_filter(
                entity_types=[entity_type.lower()] if entity_type else None,
                platform=platform,
                query=query,
            )
            return [{"urn": urn} for urn in itertools.islice(urns, count)]
        except Exception:
            return []

    def get_entity(self, urn: str, aspects: list[str] | None = None) -> dict[str, Any] | None:
        """Aspects bruts (dict) d'une entité, ou None si absente/injoignable.

        Utilise `get_entities_v2` du SDK DataHub et déballe chaque aspect de son
        enveloppe `{"value": ...}` pour renvoyer directement les champs attendus
        par les appelants (ex. `props["datasetProperties"]["name"]`).
        """
        if not self.enabled:
            return None
        parts = urn.split(":")
        if len(parts) < 3:
            return None
        entity_name = parts[2]
        try:
            result = self._graph().get_entities_v2(entity_name, [urn], aspects=aspects or [])
        except Exception:
            return None
        raw = result.get(urn)
        if not raw:
            return None
        return {name: (value.get("value", value) if isinstance(value, dict) else value) for name, value in raw.items()}

    # ---------------------------------------------------------------- écriture
    def upsert_dataset_properties(self, urn: str, custom_properties: dict[str, str], description: str | None = None) -> bool:
        """Écrit les propriétés d'un dataset (retour au graphe)."""
        if not self.enabled:
            return False
        aspects: dict[str, Any] = {"datasetProperties": {"customProperties": custom_properties}}
        if description is not None:
            aspects["datasetProperties"]["description"] = description
        result = self._request("POST", "/openapi/v3/entity/dataset", {"urn": urn, "aspects": aspects})
        return result is not None

    def emit_run(self, urn: str, status: str, summary: str, started_at: str | None = None) -> bool:
        """Trace l'exécution d'un calcul en écrivant l'état du run sur le dataset."""
        return self.upsert_dataset_properties(
            urn,
            {
                "last_run_status": status,
                "last_run_at": _now_iso(),
                "last_run_started_at": started_at or _now_iso(),
                "last_run_summary": summary,
            },
        )

    def create_incident(self, title: str, description: str, entity_urn: str) -> str | None:
        """Crée un incident DataHub sur une entité ; renvoie l'URN de l'incident."""
        if not self.enabled:
            return None
        body = {
            "aspects": {
                "incidentInfo": {
                    "incidentType": "OPERATIONAL",
                    "title": title,
                    "description": description,
                    "status": {"state": "ACTIVE"},
                    "createdAt": int(datetime.now(timezone.utc).timestamp() * 1000),
                }
            },
            "entityUrns": [entity_urn],
        }
        result = self._request("POST", "/openapi/v3/entity/incident", body)
        if not result:
            return None
        results = result.get("results") or []
        if results:
            incident = results[0]
            return incident.get("urn") or incident.get("id")
        return None

    def resolve_incident(self, incident_urn: str) -> bool:
        """Passe un incident à l'état RESOLVED."""
        if not self.enabled:
            return False
        body = {
            "aspects": {
                "incidentInfo": {
                    "status": {"state": "RESOLVED"},
                    "resolvedAt": int(datetime.now(timezone.utc).timestamp() * 1000),
                }
            }
        }
        result = self._request("POST", f"/openapi/v3/entity/incident/{urllib.parse.quote(incident_urn, safe='')}", body)
        return result is not None

    def list_incidents(self) -> list[dict[str, Any]]:
        """Liste des incidents (actifs et résolus) écrits dans le graphe."""
        if not self.enabled:
            return []
        result = self._request("GET", "/openapi/v3/entity/incident")
        if not result:
            return []
        incidents: list[dict[str, Any]] = []
        for item in result.get("results") or []:
            info = (item.get("aspects") or {}).get("incidentInfo") or {}
            incidents.append(
                {
                    "urn": item.get("urn", ""),
                    "title": info.get("title", ""),
                    "description": info.get("description", ""),
                    "status": (info.get("status") or {}).get("state", ""),
                    "createdAt": info.get("createdAt"),
                }
            )
        return incidents

    # ---------------------------------------------------------------- skills
    # Entités AgentSkill (urn:li:agentSkill:<id>, aspect agentSkillInfo) et
    # AIAgent (urn:li:aiAgent:<id>, aspect aiAgentInfo) — le contrat OpenAPI v3
    # générique est identique à celui des datasets, aucun SDK spécifique requis.

    def upsert_skill(
        self,
        skill_id: str,
        name: str,
        description: str | None = None,
        instructions: str | None = None,
        source_url: str | None = None,
        source_path: str | None = None,
    ) -> bool:
        """Enregistre un AgentSkill dans le graphe (création ou mise à jour)."""
        if not self.enabled:
            return False
        urn = skill_id if skill_id.startswith("urn:li:agentSkill:") else f"urn:li:agentSkill:{skill_id}"
        info: dict[str, Any] = {"name": name}
        if description is not None:
            info["description"] = description
        if instructions is not None:
            info["instructions"] = instructions
        if source_url or source_path:
            info["sourceRepository"] = {"url": source_url or "", "path": source_path}
        result = self._request("POST", "/openapi/v3/entity/agentSkill", {"urn": urn, "aspects": {"agentSkillInfo": info}})
        return result is not None

    def get_skill(self, skill_id: str) -> dict[str, Any] | None:
        """Instructions et métadonnées d'un AgentSkill, ou None."""
        if not self.enabled:
            return None
        urn = skill_id if skill_id.startswith("urn:li:agentSkill:") else f"urn:li:agentSkill:{skill_id}"
        path = f"/openapi/v3/entity/agentSkill/{urllib.parse.quote(urn, safe='')}?aspects=agentSkillInfo"
        result = self._request("GET", path)
        if not result:
            return None
        results = result.get("results") or []
        if not results:
            return None
        entity = results[0]
        info = (entity.get("aspects") or {}).get("agentSkillInfo") or {}
        return {
            "urn": entity.get("urn") or urn,
            "id": (entity.get("urn") or urn).removeprefix("urn:li:agentSkill:"),
            "name": info.get("name"),
            "description": info.get("description", ""),
            "instructions": info.get("instructions", ""),
            "sourceRepository": info.get("sourceRepository"),
            "requiredTools": info.get("requiredTools") or [],
        }

    def list_skills(self) -> list[dict[str, Any]]:
        """Tous les AgentSkill catalogués dans le graphe."""
        if not self.enabled:
            return []
        urns = self.search_entities(query="*", entity_type="AGENTSKILL", count=200)
        skills = []
        for hit in urns:
            skill = self.get_skill(hit["urn"])
            if skill:
                skills.append(skill)
        return sorted(skills, key=lambda skill: skill.get("id") or "")

    def upsert_agent(
        self,
        agent_id: str,
        name: str,
        description: str | None = None,
        instructions: str | None = None,
        framework: str | None = None,
    ) -> bool:
        """Enregistre un AIAgent (framework, instructions) dans le graphe."""
        if not self.enabled:
            return False
        urn = agent_id if agent_id.startswith("urn:li:aiAgent:") else f"urn:li:aiAgent:{agent_id}"
        info: dict[str, Any] = {"name": name}
        if description is not None:
            info["description"] = description
        if instructions is not None:
            info["instructions"] = instructions
        result = self._request("POST", "/openapi/v3/entity/aiAgent", {"urn": urn, "aspects": {"aiAgentInfo": info}})
        return result is not None

    # ------------------------------------------------------------ commodités
    def freshness_summary(self, dataset_urns: list[str]) -> dict[str, Any]:
        """Résume la fraîcheur locale vs le SLA annoncé, source par source."""
        summary: dict[str, Any] = {"sources": {}, "ok": 0, "stale": 0, "unknown": 0}
        for urn in dataset_urns:
            properties = self.dataset_properties(urn)
            if properties is None:
                summary["sources"][urn] = {"status": "unknown"}
                summary["unknown"] += 1
                continue
            custom = properties["custom_properties"]
            last_updated = custom.get("last_updated") or ""
            sla_days = custom.get("freshness_sla_days")
            try:
                from datetime import date

                delta = (date.today() - date.fromisoformat(last_updated)).days
                stale = sla_days is not None and delta > int(sla_days)
            except ValueError:
                stale = False
                delta = None
            summary["sources"][urn] = {
                "status": "stale" if stale else "ok",
                "last_updated": last_updated,
                "sla_days": sla_days,
                "delta_days": delta,
            }
            summary["stale" if stale else "ok"] += 1
        return summary
