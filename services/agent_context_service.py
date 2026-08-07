"""Agent Context Kit : contexte prêt à l'emploi pour les agents.

Un agent qui travaille sur le graphe de contexte Terroir a besoin, pour agir
sans halluciner, de savoir :

- quels Skills DataHub lui donnent la procédure à suivre (instructions),
- quel est l'état réel des sources (fraîcheur vs SLA, lineage),
- qui il est lui-même dans le graphe (entité AIAgent cataloguée).

Ce service assemble ces morceaux — l'équivalent applicatif de l'Agent Context
Kit de DataHub (`datahub agent` / `datahub agent-skill`, qui cataloguent ces
entités) — en un bundle de contexte unique que le serveur MCP expose et que
l'application injecte dans la boucle d'un agent.

Toutes les méthodes renvoient None/listes vides quand le GMS est injoignable
(le service ne lève jamais).
"""

from __future__ import annotations

from typing import Any

from services.datahub_client import DataHubClient

DEFAULT_AGENT_ID = "terroir-context-agents"


class AgentContextService:
    """Lecture et écriture des Skills et agents, plus bundle de contexte."""

    def __init__(self, client: DataHubClient):
        self.client = client

    # ------------------------------------------------------------------ skills
    def list_skills(self) -> list[dict[str, Any]]:
        """Tous les Skills catalogués dans le graphe."""
        return self.client.list_skills()

    def get_skill(self, skill_id: str) -> dict[str, Any] | None:
        """Un Skill par son id (court ou URN complète)."""
        return self.client.get_skill(skill_id)

    def register_skill(
        self,
        skill_id: str,
        name: str,
        description: str,
        instructions: str,
        source_url: str | None = None,
        source_path: str | None = None,
    ) -> str | None:
        """Enregistre un Skill dans le graphe ; renvoie son URN ou None."""
        if not self.client.upsert_skill(
            skill_id, name, description=description, instructions=instructions,
            source_url=source_url, source_path=source_path,
        ):
            return None
        urn = skill_id if skill_id.startswith("urn:li:agentSkill:") else f"urn:li:agentSkill:{skill_id}"
        return urn

    # ------------------------------------------------------------------ agents
    def register_agent(
        self,
        agent_id: str = DEFAULT_AGENT_ID,
        name: str = "Terroir Context Agents",
        description: str | None = None,
        instructions: str | None = None,
        framework: str = "python-fastmcp",
    ) -> str | None:
        """Catalog le serveur MCP lui-même comme AIAgent dans le graphe."""
        if not self.client.upsert_agent(agent_id, name, description=description, instructions=instructions, framework=framework):
            return None
        urn = agent_id if agent_id.startswith("urn:li:aiAgent:") else f"urn:li:aiAgent:{agent_id}"
        return urn

    # ------------------------------------------------------------------ bundle
    def context_for(
        self,
        skill_ids: list[str] | None = None,
        dataset_urns: list[str] | None = None,
    ) -> dict[str, Any]:
        """Bundle de contexte complet pour un agent : skills + fraîcheur + lineage.

        C'est le « kit » : un seul objet à injecter dans le prompt d'un agent
        pour qu'il dispose de tout le contexte du graphe.
        """
        bundle: dict[str, Any] = {
            "agent": {"id": DEFAULT_AGENT_ID, "urn": f"urn:li:aiAgent:{DEFAULT_AGENT_ID}"},
            "skills": [],
            "freshness": None,
            "lineage": {},
        }
        for skill_id in skill_ids or []:
            skill = self.get_skill(skill_id)
            if skill:
                bundle["skills"].append(skill)
        if dataset_urns:
            bundle["freshness"] = self.client.freshness_summary(dataset_urns)
            for urn in dataset_urns:
                edges = self.client.dataset_lineage(urn) or []
                bundle["lineage"][urn] = {
                    "upstream": [e["urn"] for e in edges if e["direction"] == "UPSTREAM"],
                    "downstream": [e["urn"] for e in edges if e["direction"] == "DOWNSTREAM"],
                }
        return bundle
