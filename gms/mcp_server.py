"""Serveur MCP (Model Context Protocol) du graphe de contexte Terroir.

Expose le même graphe que l'API GMS via le protocole MCP, pour qu'un agent
(Claude Desktop, MCP Inspector, script, ...) puisse :

- lire le contexte : datasets, fraîcheur vs SLA, lineage amont/aval,
- agir : tracer un run, créer/résoudre un incident sur les assets,
- écrire le résultat dans le graphe pour les agents suivants.

Deux modes de fonctionnement (sélectionnés à chaque appel d'outil) :

- Mode réel : si DATAHUB_GMS_URL est défini, chaque outil lit et écrit dans un
  vrai GMS DataHub via services.datahub_client.DataHubClient (REST + SDK
  acryl-datahub). Le serveur MCP devient la passerelle d'agent vers le graphe
  réel : fraîcheur, lineage, runs et incidents sont ceux de l'instance DataHub.
- Mode démo : sinon, le graphe seedé depuis fixtures/graph.json (gms.main),
  stocké en mémoire. Idéal pour le développement local sans DataHub.

Transport : streamable HTTP, monté dans l'application FastAPI à /mcp.

Connexion depuis un client MCP :

    mcpServers:
      terroir:
        url: https://terroir-context-gms.onrender.com/mcp
        transport: streamable-http
"""

from __future__ import annotations

import json
import os
import time
from datetime import date
from typing import Any

from fastmcp import FastMCP

import gms.main as gm
from services.datahub_client import DataHubClient

mcp = FastMCP("terroir-context")


def _short_name(urn: str) -> str:
    return urn.split(",")[1] if "," in urn else urn


class _InMemoryBackend:
    """Graphe de démonstration seedé depuis fixtures/graph.json (gms.main)."""

    def _name_to_urn(self, name: str) -> str | None:
        for urn in gm._STORE:
            if gm._STORE[urn].get("name") == name:
                return urn
        return None

    def list_datasets(self) -> list[dict[str, Any]]:
        return [
            {
                "urn": urn,
                "name": entry["name"],
                "description": entry["description"],
                "customProperties": entry["customProperties"],
            }
            for urn, entry in sorted(gm._STORE.items(), key=lambda kv: kv[1].get("name", ""))
        ]

    def get_dataset(self, name: str) -> dict[str, Any] | None:
        urn = self._name_to_urn(name)
        entry = gm._STORE.get(urn) if urn else None
        if entry is None:
            return None
        return {"urn": urn, "name": entry["name"], "description": entry["description"], "customProperties": entry["customProperties"]}

    def get_lineage(self, name: str) -> dict[str, Any] | None:
        urn = self._name_to_urn(name)
        if urn is None:
            return None
        upstream, downstream = [], []
        for relation in gm._RELATIONSHIPS.get(urn, []):
            target = relation["entity"]
            target_name = _short_name(target)
            if relation["type"] == "UPSTREAM":
                upstream.append(target_name)
            else:
                downstream.append(target_name)
        return {"dataset": name, "upstream": upstream, "downstream": downstream}

    def freshness_summary(self) -> dict[str, Any]:
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

    def emit_run(self, dataset_name: str, status: str, summary: str) -> dict[str, Any]:
        urn, entry = self._name_to_urn(dataset_name), None
        if urn:
            entry = gm._STORE.get(urn)
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

    def create_incident(self, dataset_name: str, title: str, description: str) -> dict[str, Any]:
        urn, entry = self._name_to_urn(dataset_name), None
        if urn:
            entry = gm._STORE.get(urn)
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

    def resolve_incident(self, incident_urn: str) -> dict[str, Any]:
        incident = gm._INCIDENTS.get(incident_urn)
        if incident is None:
            return {"ok": False, "error": f"incident inconnu : {incident_urn}"}
        incident["status"] = "RESOLVED"
        incident["resolvedAt"] = int(time.time() * 1000)
        return {"ok": True, "incident_urn": incident_urn, "status": "RESOLVED"}

    def list_incidents(self) -> list[dict[str, Any]]:
        return [
            {
                "urn": urn,
                "title": incident["title"],
                "description": incident["description"],
                "dataset": _short_name((incident.get("entityUrns") or [""])[0]) if incident.get("entityUrns") else None,
                "status": incident["status"],
            }
            for urn, incident in gm._INCIDENTS.items()
        ]


class _RealHubBackend:
    """Graphe réel d'un GMS DataHub, lu et écrit via DataHubClient (REST + SDK)."""

    def __init__(self) -> None:
        self.client = DataHubClient()

    def _datasets(self, count: int = 200) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for hit in self.client.search_entities(query="*", entity_type="DATASET", count=count):
            urn = hit.get("urn")
            if not urn:
                continue
            props = self.client.get_entity(urn, aspects=["datasetProperties"])
            if not props:
                continue
            dp = props.get("datasetProperties", {})
            entries.append(
                {
                    "urn": urn,
                    "name": dp.get("name") or _short_name(urn),
                    "description": dp.get("description", ""),
                    "customProperties": dp.get("customProperties", {}),
                }
            )
        return entries

    def _find_urn(self, name: str) -> str | None:
        for hit in self.client.search_entities(query=name, entity_type="DATASET", count=50):
            urn = hit.get("urn")
            if not urn:
                continue
            props = self.client.get_entity(urn, aspects=["datasetProperties"])
            if props and (props.get("datasetProperties") or {}).get("name") == name:
                return urn
        hits = self.client.search_entities(query=name, entity_type="DATASET", count=1)
        return hits[0]["urn"] if hits else None

    def list_datasets(self) -> list[dict[str, Any]]:
        return sorted(self._datasets(), key=lambda entry: entry["name"])

    def get_dataset(self, name: str) -> dict[str, Any] | None:
        urn = self._find_urn(name)
        if urn is None:
            return None
        for entry in self._datasets():
            if entry["urn"] == urn:
                return entry
        return None

    def get_lineage(self, name: str) -> dict[str, Any] | None:
        urn = self._find_urn(name)
        if urn is None:
            return None
        upstream, downstream = [], []
        for edge in self.client.dataset_lineage(urn) or []:
            target = _short_name(edge["urn"])
            if edge["direction"] == "UPSTREAM":
                upstream.append(target)
            else:
                downstream.append(target)
        return {"dataset": name, "upstream": upstream, "downstream": downstream}

    def freshness_summary(self) -> dict[str, Any]:
        entries = self._datasets()
        names = {entry["urn"]: entry["name"] for entry in entries}
        summary = self.client.freshness_summary(list(names))
        sources: dict[str, Any] = {}
        ok = stale = unknown = 0
        for urn, info in summary["sources"].items():
            name = names.get(urn, urn)
            sources[name] = {"urn": urn, **{k: info.get(k) for k in ("status", "last_updated", "sla_days", "delta_days")}}
            ok += info["status"] == "ok"
            stale += info["status"] == "stale"
            unknown += info["status"] == "unknown"
        return {"sources": sources, "ok": ok, "stale": stale, "unknown": unknown}

    def emit_run(self, dataset_name: str, status: str, summary: str) -> dict[str, Any]:
        urn = self._find_urn(dataset_name)
        if urn is None:
            return {"ok": False, "error": f"dataset inconnu : {dataset_name}"}
        if not self.client.emit_run(urn, status, summary):
            return {"ok": False, "error": f"GMS injoignable : {self.client.gms_url}"}
        return {"ok": True, "urn": urn, "status": status}

    def create_incident(self, dataset_name: str, title: str, description: str) -> dict[str, Any]:
        urn = self._find_urn(dataset_name)
        if urn is None:
            return {"ok": False, "error": f"dataset inconnu : {dataset_name}"}
        incident_urn = self.client.create_incident(title, description, urn)
        if not incident_urn:
            return {"ok": False, "error": f"GMS injoignable : {self.client.gms_url}"}
        return {"ok": True, "incident_urn": incident_urn, "dataset": dataset_name, "status": "ACTIVE"}

    def resolve_incident(self, incident_urn: str) -> dict[str, Any]:
        if not self.client.resolve_incident(incident_urn):
            return {"ok": False, "error": f"incident injoignable ou inconnu : {incident_urn}"}
        return {"ok": True, "incident_urn": incident_urn, "status": "RESOLVED"}

    def list_incidents(self) -> list[dict[str, Any]]:
        incidents = []
        for incident in self.client.list_incidents():
            incidents.append(
                {
                    "urn": incident["urn"],
                    "title": incident["title"],
                    "description": incident["description"],
                    "dataset": None,  # le REST de DataHub n'expose pas l'URN d'entité liée
                    "status": incident["status"],
                }
            )
        return incidents


def _backend() -> _InMemoryBackend | _RealHubBackend:
    """Mode réel (vrai GMS DataHub) si DATAHUB_GMS_URL est défini, sinon démo mémoire."""
    if os.getenv("DATAHUB_GMS_URL"):
        return _RealHubBackend()
    return _InMemoryBackend()


@mcp.tool()
def list_datasets() -> list[dict[str, Any]]:
    """Liste les datasets du graphe de contexte avec leur fraîcheur déclarée."""
    return _backend().list_datasets()


@mcp.tool()
def get_dataset(name: str) -> dict[str, Any] | None:
    """Détails d'un dataset par son nom court (ex. 'sol_rrp', 'hubeau_hydrometrie')."""
    return _backend().get_dataset(name)


@mcp.tool()
def get_lineage(name: str) -> dict[str, Any] | None:
    """Relations de lineage (amont et aval) d'un dataset nommé."""
    return _backend().get_lineage(name)


@mcp.tool()
def freshness_summary() -> dict[str, Any]:
    """État de fraîcheur de chaque source vs son SLA annoncé (à jour / périmée / inconnue)."""
    return _backend().freshness_summary()


@mcp.tool()
def emit_run(dataset_name: str, status: str, summary: str) -> dict[str, Any]:
    """Trace l'exécution d'un calcul : écrit l'état du run sur le dataset (retour au graphe)."""
    return _backend().emit_run(dataset_name, status, summary)


@mcp.tool()
def create_incident(dataset_name: str, title: str, description: str) -> dict[str, Any]:
    """Crée un incident DataHub actif sur le dataset nommé ; renvoie son URN."""
    return _backend().create_incident(dataset_name, title, description)


@mcp.tool()
def resolve_incident(incident_urn: str) -> dict[str, Any]:
    """Passe un incident à l'état RESOLVED."""
    return _backend().resolve_incident(incident_urn)


@mcp.tool()
def list_incidents() -> list[dict[str, Any]]:
    """Liste des incidents (actifs et résolus) écrits dans le graphe."""
    return _backend().list_incidents()


def graph_fixture_dump() -> None:
    """Pour débogage : état du graphe au format JSON."""
    print(json.dumps({"datasets": gm._STORE, "incidents": gm._INCIDENTS}, indent=2, ensure_ascii=False))
