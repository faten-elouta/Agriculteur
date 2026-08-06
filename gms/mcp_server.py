"""Serveur MCP (Model Context Protocol) du graphe de contexte Terroir.

Expose le même graphe que l'API GMS via le protocole MCP, pour qu'un agent
(Claude Desktop, MCP Inspector, script, ...) puisse :

- lire le contexte : datasets, fraîcheur vs SLA, lineage amont/aval,
- agir : tracer un run, créer/résoudre un incident sur les assets,
- écrire le résultat dans le graphe pour les agents suivants.

Transport : streamable HTTP, monté dans l'application FastAPI à /mcp.

Connexion depuis un client MCP :

    mcpServers:
      terroir:
        url: https://terroir-context-gms.onrender.com/mcp
        transport: streamable-http
"""

from __future__ import annotations

import json
import time
from datetime import date
from typing import Any

from fastmcp import FastMCP

import gms.main as gm

mcp = FastMCP("terroir-context")


def _name_to_urn(name: str) -> str | None:
    for urn in gm._STORE:
        if gm._STORE[urn].get("name") == name:
            return urn
    return None


def _entry(name: str) -> tuple[str | None, dict[str, Any] | None]:
    urn = _name_to_urn(name)
    return urn, (gm._STORE[urn] if urn else None)


@mcp.tool()
def list_datasets() -> list[dict[str, Any]]:
    """Liste les datasets du graphe de contexte avec leur fraîcheur déclarée."""
    return [
        {
            "urn": urn,
            "name": entry["name"],
            "description": entry["description"],
            "customProperties": entry["customProperties"],
        }
        for urn, entry in sorted(gm._STORE.items(), key=lambda kv: kv[1].get("name", ""))
    ]


@mcp.tool()
def get_dataset(name: str) -> dict[str, Any] | None:
    """Détails d'un dataset par son nom court (ex. 'sol_rrp', 'hubeau_hydrometrie')."""
    urn, entry = _entry(name)
    if entry is None:
        return None
    return {"urn": urn, "name": entry["name"], "description": entry["description"], "customProperties": entry["customProperties"]}


@mcp.tool()
def get_lineage(name: str) -> dict[str, Any] | None:
    """Relations de lineage (amont et aval) d'un dataset nommé."""
    urn, _ = _entry(name)
    if urn is None:
        return None
    upstream, downstream = [], []
    for relation in gm._RELATIONSHIPS.get(urn, []):
        target = relation["entity"]
        target_name = target.split(",")[1] if "," in target else target
        if relation["type"] == "UPSTREAM":
            upstream.append(target_name)
        else:
            downstream.append(target_name)
    return {"dataset": name, "upstream": upstream, "downstream": downstream}


@mcp.tool()
def freshness_summary() -> dict[str, Any]:
    """État de fraîcheur de chaque source vs son SLA annoncé (à jour / périmée / inconnue)."""
    summary: dict[str, Any] = {"sources": {}, "ok": 0, "stale": 0, "unknown": 0}
    for urn, entry in gm._STORE.items():
        custom = entry["customProperties"]
        name = entry["name"]
        last_updated = custom.get("last_updated", "")
        sla_days = custom.get("freshness_sla_days", "")
        try:
            delta = (date.today() - date.fromisoformat(last_updated)).days
            stale = bool(sla_days) and delta > int(sla_days)
        except (ValueError, TypeError):
            stale = False
            delta = None
        status = "stale" if stale else "ok"
        if not last_updated:
            status = "unknown"
        summary["sources"][name] = {
            "status": status,
            "last_updated": last_updated,
            "sla_days": sla_days or None,
            "delta_days": delta,
        }
        summary[status] += 1
    return summary


@mcp.tool()
def emit_run(dataset_name: str, status: str, summary: str) -> dict[str, Any]:
    """Trace l'exécution d'un calcul : écrit l'état du run sur le dataset (retour au graphe)."""
    urn, entry = _entry(dataset_name)
    if entry is None:
        return {"ok": False, "error": f"dataset inconnu : {dataset_name}"}
    entry.setdefault("customProperties", {}).update(
        {
            "last_run_status": status,
            "last_run_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "last_run_summary": summary,
        }
    )
    return {"ok": True, "urn": urn, "status": status}


@mcp.tool()
def create_incident(dataset_name: str, title: str, description: str) -> dict[str, Any]:
    """Crée un incident DataHub actif sur le dataset nommé ; renvoie son URN."""
    urn, entry = _entry(dataset_name)
    if entry is None:
        return {"ok": False, "error": f"dataset inconnu : {dataset_name}"}
    gm._INCIDENT_COUNTER += 1
    incident_urn = f"urn:li:incident:(demo,{gm._INCIDENT_COUNTER})"
    gm._INCIDENTS[incident_urn] = {
        "title": title,
        "description": description,
        "entityUrns": [urn],
        "status": "ACTIVE",
        "createdAt": int(time.time() * 1000),
    }
    return {"ok": True, "incident_urn": incident_urn, "dataset": dataset_name, "status": "ACTIVE"}


@mcp.tool()
def resolve_incident(incident_urn: str) -> dict[str, Any]:
    """Passe un incident à l'état RESOLVED."""
    incident = gm._INCIDENTS.get(incident_urn)
    if incident is None:
        return {"ok": False, "error": f"incident inconnu : {incident_urn}"}
    incident["status"] = "RESOLVED"
    incident["resolvedAt"] = int(time.time() * 1000)
    return {"ok": True, "incident_urn": incident_urn, "status": "RESOLVED"}


@mcp.tool()
def list_incidents() -> list[dict[str, Any]]:
    """Liste des incidents (actifs et résolus) écrits dans le graphe."""
    return [
        {
            "urn": urn,
            "title": incident["title"],
            "description": incident["description"],
            "dataset": (incident.get("entityUrns") or [""])[0].split(",")[1] if incident.get("entityUrns") else None,
            "status": incident["status"],
        }
        for urn, incident in gm._INCIDENTS.items()
    ]


def graph_fixture_dump() -> None:
    """Pour débogage : état du graphe au format JSON."""
    print(json.dumps({"datasets": gm._STORE, "incidents": gm._INCIDENTS}, indent=2, ensure_ascii=False))
