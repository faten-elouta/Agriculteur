#!/usr/bin/env python3
"""Agent de supervision qui travaille sur le graphe de contexte via MCP.

L'agent se connecte au serveur MCP public (gms/mcp_server.py, monté à /mcp sur
le serveur GMS) et exécute une boucle de travail réelle sur le graphe :

1. lit l'état de fraîcheur des sources (freshness_summary),
2. détecte les sources en dépassement de SLA,
3. pour la première source périmée, parcourt son lineage aval,
4. écrit dans le graphe : crée un incident sur les assets impactés,
5. trace son propre run sur le dataset de recommandation,
6. résout l'incident une fois l'alerte traitée, puis réaffiche l'état final.

Chaque étape est un appel d'outil MCP : le script n'accède jamais au graphe
autrement que par le protocole MCP.

Usage :
    pip install "mcp>=2"
    python examples/mcp_agent_demo.py
    MCP_URL=http://127.0.0.1:8000/mcp python examples/mcp_agent_demo.py   # serveur local
"""

from __future__ import annotations

import asyncio
import os
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

MCP_URL = os.getenv("MCP_URL", "https://terroir-context-gms.onrender.com/mcp")


async def call(session: ClientSession, tool: str, arguments: dict) -> str:
    """Appelle un outil MCP et renvoie le contenu texte de la réponse."""
    result = await session.call_tool(tool, arguments)
    parts = [c.text for c in result.content if getattr(c, "type", "") == "text"]
    return "\n".join(parts) if parts else str(result)


def parse_json(text: str) -> dict:
    import json

    return json.loads(text)


async def main() -> int:
    print(f"Agent de supervision — connexion MCP : {MCP_URL}\n")
    # mcp >= 2.0 ne renvoie plus l'id de session dans le contexte
    # (streamable HTTP : l'id est géré par la session) ; mcp 1.x en renvoie un 3e.
    async with streamable_http_client(MCP_URL) as streams:
        read, write = streams[0], streams[1]
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [t.name for t in tools.tools]
            print(f"Outils MCP disponibles ({len(names)}) : {', '.join(names)}\n")

            print("ÉTAPE 1 — l'agent lit la fraîcheur des 8 sources")
            freshness = parse_json(await call(session, "freshness_summary", {}))
            stale = [name for name, info in freshness["sources"].items() if info["status"] == "stale"]
            print(f"  à jour : {freshness['ok']} · périmées : {freshness['stale']} · inconnues : {freshness['unknown']}")
            if stale:
                print(f"  sources en dépassement de SLA : {', '.join(stale)}")
            else:
                print("  aucune source périmée — travail terminé.")
                return 0

            target = stale[0]
            print(f"\nÉTAPE 2 — lineage aval de la source périmée « {target} »")
            lineage = parse_json(await call(session, "get_lineage", {"name": target}))
            downstream = lineage.get("downstream", [])
            print(f"  amont : {lineage.get('upstream', [])}")
            print(f"  aval  : {downstream}")
            impacted = downstream[0] if downstream else target
            print(f"  asset impacté retenu : {impacted}")

            print(f"\nÉTAPE 3 — l'agent écrit dans le graphe : incident sur « {impacted} »")
            incident = parse_json(
                await call(
                    session,
                    "create_incident",
                    {
                        "dataset_name": impacted,
                        "title": f"Source « {target} » en dépassement de SLA",
                        "description": "Détecté par l'agent de supervision (examples/mcp_agent_demo.py) : la source amont n'a pas été mise à jour dans les délais annoncés.",
                    },
                )
            )
            incident_urn = incident.get("incident_urn")
            print(f"  incident créé : {incident_urn}")

            print("\nÉTAPE 4 — l'agent trace son propre run sur le dataset de recommandation")
            run = parse_json(
                await call(
                    session,
                    "emit_run",
                    {
                        "dataset_name": "recommandations_parcelle",
                        "status": "SUCCESS",
                        "summary": f"Supervision MCP : incident {incident_urn} ouvert sur {impacted} (source {target} périmée).",
                    },
                )
            )
            print(f"  run : {run['status']} sur {run['urn']}")

            print(f"\nÉTAPE 5 — la station est rétablie : résolution de l'incident")
            resolved = parse_json(await call(session, "resolve_incident", {"incident_urn": incident_urn}))
            print(f"  {resolved.get('status')} : {resolved.get('incident_urn')}")

            print("\nÉTAPE 6 — état final du graphe")
            incidents = parse_json(await call(session, "list_incidents", {}))
            for inc in incidents:
                print(f"  [{inc['status']}] {inc['urn']} — {inc['title']} (dataset {inc['dataset']})")

            print("\nBoucle de supervision terminée : le graphe garde la trace de l'alerte, du run et de la résolution.")
            return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
