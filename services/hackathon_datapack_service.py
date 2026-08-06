"""Hackathon datapack support for nyc-taxi and showcase-ecommerce.

Provides utilities to work with DataHub's official hackathon datapacks,
including anomaly detection, lineage exploration, and demo scenarios.
"""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from services.datahub_client import DataHubClient


@dataclass
class DatapackInfo:
    """Information about a loaded datapack."""
    name: str
    datasets: list[dict[str, Any]]
    lineage_edges: list[dict[str, str]]
    anomalies: list[dict[str, Any]]


class HackathonDatapackService:
    """Service for working with hackathon datapacks."""

    DATAPACKS = {
        "nyc-taxi": {
            "description": "NYC Taxi trips with planted freshness/schema anomalies",
            "expected_datasets": 100,
            "platform": "postgres",
            "anomaly_types": ["freshness_breach", "schema_drift", "null_percentage"],
        },
        "showcase-ecommerce": {
            "description": "E-commerce showcase with cross-platform lineage (Snowflake, Looker, PowerBI, Tableau, dbt, Spark, PostgreSQL, S3)",
            "expected_datasets": 1049,
            "platform": "multi",
            "anomaly_types": ["freshness_breach", "broken_lineage", "missing_ownership"],
        },
        "healthcare": {
            "description": "Healthcare claims data",
            "expected_datasets": 50,
            "platform": "snowflake",
            "anomaly_types": [],
        },
        "fiction-retail": {
            "description": "Fictional retail dataset",
            "expected_datasets": 30,
            "platform": "bigquery",
            "anomaly_types": [],
        },
    }

    def __init__(self, client: DataHubClient):
        self.client = client

    def load_datapack(self, name: str, wait: bool = True) -> bool:
        """Load a datapack via DataHub CLI."""
        if name not in self.DATAPACKS:
            raise ValueError(f"Unknown datapack: {name}. Available: {list(self.DATAPACKS.keys())}")

        try:
            result = subprocess.run(
                ["datahub", "datapack", "load", name],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode != 0:
                print(f"Failed to load {name}: {result.stderr}")
                return False

            if wait:
                self._wait_for_ingestion(name)

            return True
        except subprocess.TimeoutExpired:
            print(f"Timeout loading {name}")
            return False
        except FileNotFoundError:
            print("DataHub CLI not found. Install with: pip install acryl-datahub")
            return False

    def _wait_for_ingestion(self, datapack: str, max_wait: int = 120) -> None:
        """Wait for datapack ingestion to complete."""
        expected = self.DATAPACKS[datapack]["expected_datasets"]
        start = time.time()

        while time.time() - start < max_wait:
            datasets = self.discover_datapack_datasets(datapack)
            if len(datasets) >= expected * 0.8:  # 80% threshold
                print(f"Loaded {len(datasets)}/{expected} datasets for {datapack}")
                return
            time.sleep(5)

        print(f"Warning: Only {len(datasets)}/{expected} datasets loaded after {max_wait}s")

    def discover_datapack_datasets(self, datapack: str) -> list[dict[str, Any]]:
        """Discover datasets from a specific datapack."""
        platform = self.DATAPACKS[datapack]["platform"]

        if platform == "multi":
            # Search across all platforms for showcase-ecommerce
            results = self.client.search_entities(
                query=f"datapack:{datapack}",
                entity_type="DATASET",
                count=2000
            )
        else:
            results = self.client.search_entities(
                query="*",
                entity_type="DATASET",
                platform=platform,
                count=500
            )

        return results

    def detect_anomalies(self, datapack: str) -> list[dict[str, Any]]:
        """Detect planted anomalies in hackathon datapacks."""
        anomalies = []
        datasets = self.discover_datapack_datasets(datapack)
        anomaly_types = self.DATAPACKS[datapack]["anomaly_types"]

        for ds in datasets:
            urn = ds.get("urn")
            if not urn:
                continue

            props = self.client.get_entity(urn, aspects=[
                "datasetProperties", "schemaMetadata", "status"
            ])

            if not props:
                continue

            dataset_props = props.get("datasetProperties", {})
            custom = dataset_props.get("customProperties", {})
            schema = props.get("schemaMetadata", {})
            status = props.get("status", {})

            # Freshness breach detection
            if "freshness_breach" in anomaly_types:
                last_updated = custom.get("last_updated")
                sla_days = custom.get("freshness_sla_days")
                if last_updated and sla_days:
                    from datetime import date
                    try:
                        delta = (date.today() - date.fromisoformat(last_updated[:10])).days
                        if delta > int(sla_days):
                            anomalies.append({
                                "type": "freshness_breach",
                                "dataset_urn": urn,
                                "dataset_name": dataset_props.get("name"),
                                "severity": "critical" if delta > 2 * int(sla_days) else "warning",
                                "details": f"Last updated {delta} days ago, SLA is {sla_days} days",
                                "delta_days": delta,
                                "sla_days": int(sla_days),
                            })
                    except ValueError:
                        pass

            # Schema drift detection
            if "schema_drift" in anomaly_types:
                expected_fields = custom.get("expected_field_count")
                actual_fields = len(schema.get("fields", []))
                if expected_fields and actual_fields != int(expected_fields):
                    anomalies.append({
                        "type": "schema_drift",
                        "dataset_urn": urn,
                        "dataset_name": dataset_props.get("name"),
                        "severity": "warning",
                        "details": f"Expected {expected_fields} fields, found {actual_fields}",
                        "expected": int(expected_fields),
                        "actual": actual_fields,
                    })

            # Null percentage anomaly
            if "null_percentage" in anomaly_types:
                null_pct = custom.get("null_percentage_threshold")
                if null_pct:
                    # Would need column-level stats - simplified here
                    pass

            # Broken lineage
            if "broken_lineage" in anomaly_types:
                lineage = props.get("upstreamLineage", {})
                if not lineage.get("upstreams") and "raw" not in dataset_props.get("name", "").lower():
                    anomalies.append({
                        "type": "broken_lineage",
                        "dataset_urn": urn,
                        "dataset_name": dataset_props.get("name"),
                        "severity": "warning",
                        "details": "No upstream lineage found for derived dataset",
                    })

            # Missing ownership
            if "missing_ownership" in anomaly_types:
                ownership = props.get("ownership", {})
                if not ownership.get("owners"):
                    anomalies.append({
                        "type": "missing_ownership",
                        "dataset_urn": urn,
                        "dataset_name": dataset_props.get("name"),
                        "severity": "info",
                        "details": "No owners assigned",
                    })

        return anomalies

    def get_cross_platform_lineage(self, datapack: str) -> dict[str, list[str]]:
        """Get cross-platform lineage for showcase-ecommerce."""
        if datapack != "showcase-ecommerce":
            return {}

        datasets = self.discover_datapack_datasets(datapack)
        platform_lineage = {}

        for ds in datasets:
            urn = ds.get("urn")
            if not urn:
                continue

            platform = self._extract_platform(urn)
            if platform not in platform_lineage:
                platform_lineage[platform] = []

            # Get upstream platforms
            props = self.client.get_entity(urn, aspects=["upstreamLineage"])
            if props:
                lineage = props.get("upstreamLineage", {})
                for up in lineage.get("upstreams", []):
                    up_platform = self._extract_platform(up.get("dataset", ""))
                    if up_platform and up_platform != platform:
                        platform_lineage[platform].append(up_platform)

        # Deduplicate
        for platform, upstreams in platform_lineage.items():
            platform_lineage[platform] = list(set(upstreams))

        return platform_lineage

    def _extract_platform(self, urn: str) -> str:
        """Extract platform from URN."""
        if not urn:
            return "unknown"
        parts = urn.split(",")
        if len(parts) > 1:
            return parts[0].split(":")[-1]
        return "unknown"

    def run_sentinelle_on_datapack(self, datapack: str, apply: bool = False) -> dict[str, Any]:
        """Run the Sentinelle agent on a hackathon datapack."""
        from agents.sentinelle import Sentinelle, LiveBackend, Finding

        backend = LiveBackend(
            server=self.client.gms_url,
            token=self.client.token,
            apply_writes=apply
        )

        sentinelle = Sentinelle(backend)
        platform = self.DATAPACKS[datapack]["platform"]

        if platform == "multi":
            # Run on all platforms
            all_findings = []
            for p in ["postgres", "snowflake", "bigquery", "redshift"]:
                findings = sentinelle.scan(platform=p)
                all_findings.extend(findings)
        else:
            all_findings = sentinelle.scan(platform=platform)

        # Also detect hackathon-specific anomalies
        hackathon_anomalies = self.detect_anomalies(datapack)

        # Convert hackathon anomalies to findings
        for anomaly in hackathon_anomalies:
            finding = Finding(
                type=anomaly["type"],
                asset_urn=anomaly["dataset_urn"],
                detecte_le=time.strftime("%Y-%m-%d"),
                detail=anomaly["details"],
                severite="rupture" if anomaly["severity"] == "critical" else "vigilance",
            )
            finding.downstream = backend.downstream(anomaly["dataset_urn"])
            all_findings.append(finding)

        # Act on findings
        reports = []
        for finding in all_findings:
            report = sentinelle.act(finding)
            reports.append(report.to_json())

        return {
            "datapack": datapack,
            "findings_count": len(all_findings),
            "anomalies_detected": len(hackathon_anomalies),
            "reports": reports,
            "writes": len(getattr(backend, 'writes', [])),
        }

    def generate_datapack_report(self, datapack: str, output_dir: Path) -> Path:
        """Generate a comprehensive report for a datapack."""
        datasets = self.discover_datapack_datasets(datapack)
        anomalies = self.detect_anomalies(datapack)
        cross_platform = self.get_cross_platform_lineage(datapack)

        report = {
            "datapack": datapack,
            "description": self.DATAPACKS[datapack]["description"],
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_datasets": len(datasets),
                "anomalies_found": len(anomalies),
                "anomalies_by_type": {},
                "platforms": {},
            },
            "datasets": [],
            "anomalies": anomalies,
            "cross_platform_lineage": cross_platform,
        }

        # Count by platform
        for ds in datasets:
            urn = ds.get("urn")
            if urn:
                platform = self._extract_platform(urn)
                report["summary"]["platforms"][platform] = report["summary"]["platforms"].get(platform, 0) + 1

        # Count anomalies by type
        for a in anomalies:
            atype = a["type"]
            report["summary"]["anomalies_by_type"][atype] = report["summary"]["anomalies_by_type"].get(atype, 0) + 1

        # Add dataset details
        for ds in datasets[:50]:  # Limit to first 50
            urn = ds.get("urn")
            if urn:
                props = self.client.get_entity(urn, aspects=["datasetProperties"])
                if props:
                    dp = props.get("datasetProperties", {})
                    report["datasets"].append({
                        "urn": urn,
                        "name": dp.get("name"),
                        "platform": self._extract_platform(urn),
                        "description": dp.get("description", "")[:200],
                    })

        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"datapack_report_{datapack}.json"

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return output_file


def main():
    """CLI for hackathon datapack operations."""
    import argparse

    parser = argparse.ArgumentParser(description="Hackathon datapack utilities")
    parser.add_argument("--server", default=None, help="DataHub GMS URL")
    parser.add_argument("--token", default=None, help="DataHub token")
    parser.add_argument("action", choices=["load", "discover", "anomalies", "sentinelle", "report", "lineage"])
    parser.add_argument("datapack", choices=list(HackathonDatapackService.DATAPACKS.keys()))
    parser.add_argument("--apply", action="store_true", help="Apply writes to DataHub")
    parser.add_argument("--output", default="reports/datapacks", help="Output directory")

    args = parser.parse_args()

    client = DataHubClient(gms_url=args.server, token=args.token)
    service = HackathonDatapackService(client)

    if args.action == "load":
        success = service.load_datapack(args.datapack)
        print(f"Load {'successful' if success else 'failed'}")

    elif args.action == "discover":
        datasets = service.discover_datapack_datasets(args.datapack)
        print(f"Found {len(datasets)} datasets")
        for ds in datasets[:10]:
            print(f"  - {ds.get('urn')}")

    elif args.action == "anomalies":
        anomalies = service.detect_anomalies(args.datapack)
        print(f"Found {len(anomalies)} anomalies:")
        for a in anomalies:
            print(f"  [{a['severity']}] {a['type']}: {a['dataset_name']} - {a['details']}")

    elif args.action == "sentinelle":
        result = service.run_sentinelle_on_datapack(args.datapack, apply=args.apply)
        print(f"Sentinelle results for {args.datapack}:")
        print(f"  Findings: {result['findings_count']}")
        print(f"  Hackathon anomalies: {result['anomalies_detected']}")
        print(f"  Writes: {result['writes']}")

    elif args.action == "report":
        output_file = service.generate_datapack_report(args.datapack, Path(args.output))
        print(f"Report generated: {output_file}")

    elif args.action == "lineage":
        lineage = service.get_cross_platform_lineage(args.datapack)
        print(f"Cross-platform lineage for {args.datapack}:")
        for platform, upstreams in lineage.items():
            print(f"  {platform} <- {', '.join(upstreams) if upstreams else 'none'}")


if __name__ == "__main__":
    main()