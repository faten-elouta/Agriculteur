"""Ingestion des Skills et de l'agent Terroir dans DataHub.

Suit le standard « agentskills.io » : un skill est défini en git (un dossier
`catalog/skills/<id>/SKILL.md` avec frontmatter YAML `name`/`description` et un
corps Markdown) et catalogué dans DataHub comme entité AgentSkill
(`urn:li:agentSkill:<id>`, aspect `agentSkillInfo`).

Enregistre aussi le serveur MCP lui-même comme entité AIAgent
(`urn:li:aiAgent:terroir-context-agents`) — c'est l'étape « Agent Context Kit »
du workflow DataHub (`datahub agent-skill register`, `datahub agent register`).

Usage :
    .venv/bin/python catalog/ingest_skills.py --dry-run   # affiche les payloads
    DATAHUB_GMS_URL=http://localhost:8080 .venv/bin/python catalog/ingest_skills.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.agent_context_service import AgentContextService  # noqa: E402
from services.datahub_client import DataHubClient  # noqa: E402

SKILLS_DIR = ROOT / "catalog" / "skills"
GIT_URL = "https://github.com/faten-elouta/Agriculteur"


def parse_skill_file(path: Path) -> dict:
    """Lit un SKILL.md : frontmatter YAML minimal (name, description) + corps."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path} : frontmatter YAML manquant")
    _, frontmatter, body = text.split("---", 2)
    meta: dict[str, str] = {}
    for line in frontmatter.strip().splitlines():
        if ":" in line and not line.lstrip().startswith((">", "#")):
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"').strip("'")
    return {
        "id": path.parent.name,
        "name": meta["name"],
        "description": meta.get("description", ""),
        "instructions": body.strip(),
    }


def discover_skills() -> list[dict]:
    """Tous les skills de catalog/skills/*/SKILL.md."""
    skills = []
    for path in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        skill = parse_skill_file(path)
        skill["source_path"] = f"catalog/skills/{skill['id']}/SKILL.md"
        skills.append(skill)
    return skills


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dry-run", action="store_true", help="affiche les payloads sans appel réseau")
    args = parser.parse_args()

    skills = discover_skills()
    if not skills:
        print(f"Aucun skill trouvé dans {SKILLS_DIR}")
        sys.exit(1)

    agent_urn = "urn:li:aiAgent:terroir-context-agents"
    if args.dry_run:
        for skill in skills:
            print(
                json.dumps(
                    {
                        "urn": f"urn:li:agentSkill:{skill['id']}",
                        "aspects": {
                            "agentSkillInfo": {
                                "name": skill["name"],
                                "description": skill["description"],
                                "instructions": skill["instructions"][:120] + "…",
                                "sourceRepository": {"url": GIT_URL, "path": skill["source_path"]},
                            }
                        },
                    },
                    ensure_ascii=False,
                    indent=1,
                )
            )
        print(json.dumps({"urn": agent_urn, "aspects": {"aiAgentInfo": {"name": "Terroir Context Agents", "description": "Agent de supervision du graphe de contexte (via /mcp)."}}}, ensure_ascii=False, indent=1))
        print(f"# skills : {len(skills)} · agent : 1")
        return

    client = DataHubClient()
    if not client.enabled:
        print("DATAHUB_GMS_URL non défini — rien à faire. Passez --dry-run pour voir les payloads.")
        sys.exit(1)
    if not client.connected():
        print(f"GMS injoignable : {client.gms_url} — vérifiez DATAHUB_GMS_URL et DATAHUB_TOKEN.")
        sys.exit(1)

    service = AgentContextService(client)
    ok = 0
    for skill in skills:
        urn = service.register_skill(
            skill["id"], skill["name"], skill["description"], skill["instructions"],
            source_url=GIT_URL, source_path=skill["source_path"],
        )
        if urn:
            ok += 1
            print(f"skill  {urn}")
    agent_urn_result = service.register_agent(
        description="Agent de supervision du graphe de contexte Terroir (serveur MCP /mcp).",
        instructions="Règles de surveillance : lire la fraîcheur, créer/résoudre des incidents, tracer ses runs (voir les skills freshness_sla).",
        framework="python-fastmcp",
    )
    if agent_urn_result:
        ok += 1
        print(f"agent  {agent_urn_result}")
    print(f"Ingestion terminée : {ok}/{len(skills) + 1} entités écrites dans {client.gms_url}.")


if __name__ == "__main__":
    main()
