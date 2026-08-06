#!/usr/bin/env python3
"""
agents/sentinelle.py — Agent Sentinelle v0.

Detecte une degradation sur une source amont, remonte le lineage descendant dans
DataHub, identifie tout ce qui est invalide, et **reecrit dans le graphe** : tags,
description editable, rapport d'impact.

Fonctionne sur deux graphes sans changer une ligne de code :
  - le graphe officiel du hackathon, dont les anomalies de fraicheur sont plantees
  - le graphe agricole Terroir

    python agents/sentinelle.py --scan --platform postgres
    python agents/sentinelle.py --scan --simulate-stale hubeau_hydrometrie --apply
    python agents/sentinelle.py --offline fixtures/graph.json --scan

Licence: Apache-2.0
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from typing import Dict, List, Optional, Protocol

RISK_TAG = "recommandation-a-risque"
STALE_TAG = "donnee-perimee"
DEFAULT_SLA_DAYS = 7
REPORT_DIR = "reports"

DOWNSTREAM_QUERY = """
query($urn: String!, $count: Int!) {
  searchAcrossLineage(input: {
    urn: $urn, direction: DOWNSTREAM, query: "*", start: 0, count: $count
  }) {
    total
    searchResults {
      degree
      entity {
        urn
        type
        ... on Dataset { properties { name description } }
        ... on MLModel  { properties { description } }
      }
    }
  }
}
"""


# --------------------------------------------------------------------------------------
# Modele de resultat
# --------------------------------------------------------------------------------------

@dataclass
class Finding:
    """Une degradation detectee sur un asset amont."""

    type: str            # freshness_breach | schema_drift | calibration_mismatch
    asset_urn: str
    detecte_le: str
    detail: str
    severite: str        # vigilance | rupture
    downstream: List[str] = field(default_factory=list)

    @property
    def tag(self) -> str:
        return STALE_TAG if self.type == "freshness_breach" else RISK_TAG


@dataclass
class ImpactReport:
    declencheur: Dict
    impact: Dict
    actions_ecrites_dans_datahub: Dict

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)


# --------------------------------------------------------------------------------------
# Backends
# --------------------------------------------------------------------------------------

class Backend(Protocol):
    def list_datasets(self, platform: Optional[str]) -> List[str]: ...
    def properties(self, urn: str) -> Dict: ...
    def downstream(self, urn: str) -> List[str]: ...
    def write_tag(self, urn: str, tag: str) -> None: ...
    def write_description(self, urn: str, text: str) -> None: ...


class OfflineBackend:
    """Rejoue un graphe fige. Sert aux tests et a la demo sans serveur."""

    def __init__(self, path: str, apply_writes: bool = False) -> None:
        with open(path, encoding="utf-8") as handle:
            self.graph = json.load(handle)
        self.apply_writes = apply_writes
        self.writes: List[Dict] = []

    def list_datasets(self, platform: Optional[str]) -> List[str]:
        return [u for u in self.graph["datasets"]
                if platform is None or f"dataPlatform:{platform}" in u]

    def properties(self, urn: str) -> Dict:
        return self.graph["datasets"].get(urn, {})

    def downstream(self, urn: str) -> List[str]:
        seen, stack = [], list(self.graph["lineage"].get(urn, []))
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.append(node)
            stack.extend(self.graph["lineage"].get(node, []))
        return seen

    def write_tag(self, urn: str, tag: str) -> None:
        self.writes.append({"op": "add_tag", "urn": urn, "tag": tag})

    def write_description(self, urn: str, text: str) -> None:
        self.writes.append({"op": "update_description", "urn": urn, "text": text})


class LiveBackend:
    """Parle a un DataHub reel : lecture par GraphQL, ecriture par le SDK."""

    def __init__(self, server: str, token: Optional[str], apply_writes: bool) -> None:
        from datahub.ingestion.graph.client import DatahubClientConfig, DataHubGraph

        self.graph = DataHubGraph(DatahubClientConfig(server=server, token=token))
        self.apply_writes = apply_writes
        self.writes: List[Dict] = []

    def list_datasets(self, platform: Optional[str]) -> List[str]:
        return list(self.graph.get_urns_by_filter(entity_types=["dataset"], platform=platform))

    def properties(self, urn: str) -> Dict:
        import datahub.metadata.schema_classes as models

        aspect = self.graph.get_aspect(urn, models.DatasetPropertiesClass)
        if aspect is None:
            return {}
        out = dict(aspect.customProperties or {})
        out["_description"] = aspect.description or ""
        if aspect.lastModified and aspect.lastModified.time:
            out.setdefault(
                "last_updated",
                datetime.fromtimestamp(aspect.lastModified.time / 1000,
                                       tz=timezone.utc).date().isoformat(),
            )
        return out

    def downstream(self, urn: str) -> List[str]:
        result = self.graph.execute_graphql(DOWNSTREAM_QUERY, {"urn": urn, "count": 200})
        hits = result.get("searchAcrossLineage", {}).get("searchResults", [])
        return [h["entity"]["urn"] for h in hits]

    def write_tag(self, urn: str, tag: str) -> None:
        import datahub.metadata.schema_classes as models
        from datahub.emitter.mce_builder import make_tag_urn
        from datahub.emitter.mcp import MetadataChangeProposalWrapper

        tag_urn = make_tag_urn(tag)
        current = self.graph.get_aspect(urn, models.GlobalTagsClass)
        tags = list(current.tags) if current else []
        if any(t.tag == tag_urn for t in tags):
            return
        tags.append(models.TagAssociationClass(tag=tag_urn))
        self.writes.append({"op": "add_tag", "urn": urn, "tag": tag})
        if self.apply_writes:
            self.graph.emit(MetadataChangeProposalWrapper(
                entityUrn=urn, aspect=models.GlobalTagsClass(tags=tags)))

    def write_description(self, urn: str, text: str) -> None:
        import datahub.metadata.schema_classes as models
        from datahub.emitter.mcp import MetadataChangeProposalWrapper

        self.writes.append({"op": "update_description", "urn": urn, "text": text})
        if self.apply_writes:
            # Couche editable : on n'ecrase jamais la description technique d'origine.
            self.graph.emit(MetadataChangeProposalWrapper(
                entityUrn=urn,
                aspect=models.EditableDatasetPropertiesClass(description=text)))


# --------------------------------------------------------------------------------------
# Detection
# --------------------------------------------------------------------------------------

def days_since(iso_date: str, today: date) -> Optional[int]:
    try:
        return (today - date.fromisoformat(iso_date[:10])).days
    except (ValueError, TypeError):
        return None


class Sentinelle:
    def __init__(self, backend: Backend, today: Optional[date] = None) -> None:
        self.backend = backend
        self.today = today or date.today()

    # -- detecteurs ---------------------------------------------------------------

    def check_freshness(self, urn: str, props: Dict) -> Optional[Finding]:
        last = props.get("last_updated")
        if not last:
            return None
        sla = int(props.get("freshness_sla_days", DEFAULT_SLA_DAYS))
        age = days_since(last, self.today)
        if age is None or age <= sla:
            return None
        return Finding(
            type="freshness_breach",
            asset_urn=urn,
            detecte_le=self.today.isoformat(),
            detail=f"Derniere donnee le {last}, soit {age} jours, au-dela du seuil de {sla}.",
            severite="rupture" if age > 2 * sla else "vigilance",
        )

    def check_calibration(self, urn: str, props: Dict, bassin_cible: Optional[str]) -> Optional[Finding]:
        bassin = props.get("bassin_calibration")
        if not bassin or not bassin_cible or bassin == bassin_cible:
            return None
        return Finding(
            type="calibration_mismatch",
            asset_urn=urn,
            detecte_le=self.today.isoformat(),
            detail=f"Modele calibre sur {bassin}, applique sur {bassin_cible}.",
            severite="vigilance",
        )

    # -- balayage -----------------------------------------------------------------

    def scan(self, platform: Optional[str] = None,
             bassin_cible: Optional[str] = None,
             simulate_stale: Optional[str] = None) -> List[Finding]:
        findings: List[Finding] = []
        for urn in self.backend.list_datasets(platform):
            props = dict(self.backend.properties(urn))
            if simulate_stale and simulate_stale in urn:
                # Le bouton "simuler une panne" de l'interface passe par ici.
                props["last_updated"] = "2026-01-01"
            for finding in (self.check_freshness(urn, props),
                            self.check_calibration(urn, props, bassin_cible)):
                if finding:
                    finding.downstream = self.backend.downstream(urn)
                    findings.append(finding)
        findings.sort(key=lambda f: (f.severite != "rupture", f.asset_urn))
        return findings

    # -- action -------------------------------------------------------------------

    def act(self, finding: Finding) -> ImpactReport:
        """Ecrit dans le graphe. C'est ce qui distingue un moniteur d'un agent."""
        self.backend.write_tag(finding.asset_urn, finding.tag)
        note = (f"[Sentinelle {finding.detecte_le}] {finding.detail} "
                f"{len(finding.downstream)} asset(s) en aval marques a risque.")
        self.backend.write_description(finding.asset_urn, note)

        for urn in finding.downstream:
            self.backend.write_tag(urn, RISK_TAG)
            self.backend.write_description(
                urn,
                f"[Sentinelle {finding.detecte_le}] Amont degrade : {finding.asset_urn}. "
                f"Les livrables issus de cet asset sont a revalider.",
            )

        return ImpactReport(
            declencheur={
                "type": finding.type,
                "asset_urn": finding.asset_urn,
                "detecte_le": finding.detecte_le,
                "detail": finding.detail,
                "severite": finding.severite,
            },
            impact={
                "assets_aval": finding.downstream,
                "profondeur_lineage": len(finding.downstream),
            },
            actions_ecrites_dans_datahub={
                "tags_ajoutes": [finding.tag, RISK_TAG],
                "descriptions_mises_a_jour": [finding.asset_urn, *finding.downstream],
            },
        )


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Agent Sentinelle — DataHub.")
    parser.add_argument("--server", default=os.environ.get("DATAHUB_GMS", "http://localhost:8080"))
    parser.add_argument("--token", default=os.environ.get("DATAHUB_TOKEN"))
    parser.add_argument("--offline", metavar="FIXTURE",
                        help="Rejoue un graphe fige au lieu d'interroger un serveur")
    parser.add_argument("--platform", default=None, help="Filtre de plateforme, ex. duckdb")
    parser.add_argument("--bassin", default=None, help="Bassin de la parcelle etudiee")
    parser.add_argument("--simulate-stale", default=None,
                        help="Force une source a paraitre perimee, pour la demo")
    parser.add_argument("--apply", action="store_true",
                        help="Ecrit reellement dans DataHub (sinon simulation)")
    parser.add_argument("--today", default=None, help="Date de reference, ISO")
    args = parser.parse_args(argv)

    backend: Backend
    if args.offline:
        backend = OfflineBackend(args.offline, apply_writes=args.apply)
    else:
        backend = LiveBackend(args.server, args.token, apply_writes=args.apply)

    today = date.fromisoformat(args.today) if args.today else date.today()
    sentinelle = Sentinelle(backend, today=today)
    findings = sentinelle.scan(platform=args.platform, bassin_cible=args.bassin,
                               simulate_stale=args.simulate_stale)

    if not findings:
        print("Aucune degradation detectee.")
        return 0

    os.makedirs(REPORT_DIR, exist_ok=True)
    for index, finding in enumerate(findings, start=1):
        report = sentinelle.act(finding)
        path = os.path.join(REPORT_DIR, f"impact_{today.isoformat()}_{index}.json")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(report.to_json())
        print(f"[{finding.severite}] {finding.type} — {finding.asset_urn}")
        print(f"  {finding.detail}")
        print(f"  {len(finding.downstream)} asset(s) en aval invalides")
        print(f"  rapport : {path}")

    mode = "ecrites dans DataHub" if args.apply else "simulees (ajouter --apply)"
    print(f"\n{len(getattr(backend, 'writes', []))} ecriture(s) {mode}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
