"""Metadata-aware code generation from real DataHub schemas.

Generates production-ready ingestion recipes, transformation SQL, and pipeline DAGs
by reading actual schemas, lineage, and metadata from DataHub.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from services.datahub_client import DataHubClient


@dataclass
class DatasetSchema:
    """Schema information for a dataset."""
    urn: str
    name: str
    platform: str
    description: str
    fields: list[dict[str, Any]]
    upstream_urns: list[str]
    downstream_urns: list[str]
    custom_properties: dict[str, str]
    tags: list[str]
    glossary_terms: list[str]


@dataclass
class MLModelInfo:
    """ML Model information from DataHub."""
    urn: str
    name: str
    description: str
    version: str
    training_data_urns: list[str]
    feature_table_urn: str | None
    features: list[str]
    custom_properties: dict[str, str]


class CodeGenerationService:
    """Generates code artifacts from DataHub metadata."""

    def __init__(self, client: DataHubClient):
        self.client = client

    def discover_datasets(self, platform: str | None = None) -> list[DatasetSchema]:
        """Discover all datasets and their schemas from DataHub."""
        if not self.client.enabled:
            return []

        # Search for datasets
        search_results = self.client.search_entities(
            query="*",
            entity_type="DATASET",
            platform=platform,
            count=500
        )

        datasets = []
        for entity in search_results:
            urn = entity.get("urn")
            if not urn:
                continue

            # Get full properties including schema
            props = self.client.get_entity(urn, aspects=[
                "datasetProperties", "schemaMetadata", "globalTags",
                "glossaryTerms", "upstreamLineage", "ownership"
            ])

            if not props:
                continue

            dataset_props = props.get("datasetProperties", {})
            schema = props.get("schemaMetadata", {})
            tags = props.get("globalTags", {})
            glossary = props.get("glossaryTerms", {})
            lineage = props.get("upstreamLineage", {})

            fields = []
            for f in schema.get("fields", []):
                fields.append({
                    "name": f.get("fieldPath"),
                    "type": f.get("type", {}).get("type", {}),
                    "native_type": f.get("nativeDataType"),
                    "description": f.get("description", ""),
                })

            upstream = [u.get("dataset") for u in lineage.get("upstreams", [])]
            downstream = self._get_downstream(urn)

            datasets.append(DatasetSchema(
                urn=urn,
                name=dataset_props.get("name", ""),
                platform=self._extract_platform(urn),
                description=dataset_props.get("description", ""),
                fields=fields,
                upstream_urns=upstream,
                downstream_urns=downstream,
                custom_properties=dataset_props.get("customProperties", {}),
                tags=[t.get("tag", "").split(":")[-1] for t in tags.get("tags", [])],
                glossary_terms=[t.get("urn", "").split(":")[-1] for t in glossary.get("terms", [])],
            ))

        return datasets

    def discover_ml_models(self) -> list[MLModelInfo]:
        """Discover ML models and their lineage from DataHub."""
        if not self.client.enabled:
            return []

        search_results = self.client.search_entities(
            query="*",
            entity_type="MLMODEL",
            count=100
        )

        models = []
        for entity in search_results:
            urn = entity.get("urn")
            if not urn:
                continue

            props = self.client.get_entity(urn, aspects=[
                "mlModelProperties", "mlModelGroups", "upstreamLineage"
            ])

            if not props:
                continue

            model_props = props.get("mlModelProperties", {})
            groups = props.get("mlModelGroups", {})
            lineage = props.get("upstreamLineage", {})

            training_data = [u.get("dataset") for u in lineage.get("upstreams", [])]
            feature_table_urn = None
            features = []

            # Find feature table from groups or lineage
            for u in lineage.get("upstreams", []):
                if "feature" in u.get("dataset", "").lower():
                    feature_table_urn = u.get("dataset")
                    # Get features from feature table
                    ft_props = self.client.get_entity(feature_table_urn, aspects=["mlFeatureTableProperties"])
                    if ft_props:
                        ft_info = ft_props.get("mlFeatureTableProperties", {})
                        features = ft_info.get("mlFeatures", [])

            models.append(MLModelInfo(
                urn=urn,
                name=model_props.get("name", ""),
                description=model_props.get("description", ""),
                version=model_props.get("version", {}).get("versionTag", "1.0.0"),
                training_data_urns=training_data,
                feature_table_urn=feature_table_urn,
                features=features,
                custom_properties=model_props.get("customProperties", {}),
            ))

        return models

    def _get_downstream(self, urn: str) -> list[str]:
        """Get downstream datasets for a given URN."""
        lineage = self.client.dataset_lineage(urn)
        if not lineage:
            return []
        return [edge["urn"] for edge in lineage if edge["direction"] == "DOWNSTREAM"]

    def _extract_platform(self, urn: str) -> str:
        """Extract platform from URN."""
        parts = urn.split(",")
        if len(parts) > 1:
            platform_part = parts[0].split(":")[-1]
            return platform_part
        return "unknown"

    def generate_ingestion_recipe(self, dataset: DatasetSchema, output_dir: Path) -> Path:
        """Generate DataHub ingestion recipe YAML for a dataset."""
        recipe = {
            "source": {
                "type": dataset.platform.lower(),
                "config": {
                    "platform_instance": dataset.custom_properties.get("platform_instance", "prod"),
                    "database": dataset.custom_properties.get("database", ""),
                    "schema": dataset.custom_properties.get("schema", "public"),
                    "table": dataset.name,
                }
            },
            "sink": {
                "type": "datahub-rest",
                "config": {
                    "server": "${DATAHUB_GMS_URL}",
                    "token": "${DATAHUB_TOKEN}",
                }
            },
            "transformers": [
                {
                    "type": "simple_add_dataset_ownership",
                    "config": {
                        "ownership": [
                            {
                                "owner": dataset.custom_properties.get("owner", "data-team"),
                                "type": "TECHNICAL_OWNER"
                            }
                        ]
                    }
                },
                {
                    "type": "add_dataset_tags",
                    "config": {
                        "tags": dataset.tags
                    }
                },
                {
                    "type": "add_dataset_glossary_terms",
                    "config": {
                        "terms": dataset.glossary_terms
                    }
                }
            ]
        }

        # Add custom properties as transformer
        if dataset.custom_properties:
            recipe["transformers"].append({
                "type": "add_dataset_properties",
                "config": {
                    "properties": dataset.custom_properties
                }
            })

        output_file = output_dir / f"ingestion_{dataset.name}.yaml"
        output_dir.mkdir(parents=True, exist_ok=True)

        import yaml
        with open(output_file, "w") as f:
            yaml.dump(recipe, f, default_flow_style=False, sort_keys=False)

        return output_file

    def generate_transformation_sql(self, dataset: DatasetSchema, output_dir: Path) -> Path:
        """Generate dbt-style SQL transformation from lineage."""
        if not dataset.upstream_urns:
            return None

        # Build SELECT statement from upstream fields
        upstream_fields = []
        for up_urn in dataset.upstream_urns:
            up_props = self.client.get_entity(up_urn, aspects=["schemaMetadata"])
            if up_props:
                schema = up_props.get("schemaMetadata", {})
                for f in schema.get("fields", []):
                    upstream_fields.append(f"{f.get('fieldPath')} as {f.get('fieldPath')}")

        select_clause = ",\n    ".join(upstream_fields) if upstream_fields else "*"

        sql = (
            f"-- Generated transformation for {dataset.name}\n"
            f"-- Source: {len(dataset.upstream_urns)} upstream dataset(s)\n"
            f"-- Generated at: {datetime.now().isoformat()}\n\n"
            "with source_data as (\n"
            "    select\n"
            f"        {select_clause}\n"
            "    from {{ ref('upstream_table') }}\n"
            "    where 1=1\n"
            "    -- Add incremental logic here\n"
            "    {% if is_incremental() %}\n"
            "        and updated_at > (select max(updated_at) from {{ this }})\n"
            "    {% endif %}\n"
            ")\n\n"
            "select * from source_data\n"
        )

        output_file = output_dir / f"transform_{dataset.name}.sql"
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            f.write(sql)

        return output_file

    def generate_airflow_dag(self, datasets: list[DatasetSchema], output_dir: Path) -> Path:
        """Generate Airflow DAG for the full pipeline."""
        # Build task dependencies from lineage
        dag_id = "datahub_generated_pipeline"
        tasks = []

        for ds in datasets:
            task_id = f"ingest_{ds.name}"
            upstream_tasks = []

            for up_urn in ds.upstream_urns:
                up_name = up_urn.split(",")[1] if "," in up_urn else up_urn
                upstream_tasks.append(f"ingest_{up_name}")

            tasks.append({
                "task_id": task_id,
                "upstream": upstream_tasks,
                "dataset": ds,
            })

        dag_content = f'''"""
Auto-generated Airflow DAG from DataHub metadata.
Generated at: {datetime.now().isoformat()}
Datasets: {len(datasets)}
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

default_args = {{
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}}

dag = DAG(
    '{dag_id}',
    default_args=default_args,
    description='Auto-generated pipeline from DataHub lineage',
    schedule_interval='@daily',
    catchup=False,
    tags=['datahub', 'auto-generated'],
)

'''

        # Generate task definitions
        for task in tasks:
            ds = task["dataset"]
            dag_content += f'''
def ingest_{ds.name}():
    """Ingest {ds.name} from {ds.platform}."""
    # TODO: Implement actual ingestion logic
    # Example: spark.read.format("{ds.platform}").load(...).writeToDataHub()
    print("Ingesting {ds.name}")
    return "{ds.name}"

ingest_{ds.name}_task = PythonOperator(
    task_id='ingest_{ds.name}',
    python_callable=ingest_{ds.name},
    dag=dag,
)
'''

        # Set dependencies
        dag_content += "\n# Dependencies\n"
        for task in tasks:
            if task["upstream"]:
                upstream_str = " >> ".join([f"ingest_{u.split('_', 1)[1]}_task" for u in task["upstream"]])
                dag_content += f"{upstream_str} >> ingest_{task['dataset'].name}_task\n"

        output_file = output_dir / f"dag_{dag_id}.py"
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            f.write(dag_content)

        return output_file

    def generate_all_artifacts(self, output_dir: Path, platform: str | None = None) -> dict[str, list[Path]]:
        """Generate all code artifacts from DataHub metadata."""
        results = {
            "ingestion_recipes": [],
            "transformations": [],
            "dags": [],
        }

        datasets = self.discover_datasets(platform)

        for ds in datasets:
            # Ingestion recipe
            recipe_path = self.generate_ingestion_recipe(ds, output_dir / "ingestion")
            results["ingestion_recipes"].append(recipe_path)

            # Transformation SQL
            sql_path = self.generate_transformation_sql(ds, output_dir / "transformations")
            if sql_path:
                results["transformations"].append(sql_path)

        # Generate DAG from all datasets
        if datasets:
            dag_path = self.generate_airflow_dag(datasets, output_dir / "dags")
            results["dags"].append(dag_path)

        # Generate ML model artifacts
        models = self.discover_ml_models()
        for model in models:
            ml_artifacts = self._generate_ml_artifacts(model, output_dir / "ml")
            results.setdefault("ml", []).extend(ml_artifacts)

        return results

    def _generate_ml_artifacts(self, model: MLModelInfo, output_dir: Path) -> list[Path]:
        """Generate ML-related artifacts (training pipeline, feature store, etc.)."""
        output_dir.mkdir(parents=True, exist_ok=True)
        artifacts = []

        # Training pipeline config
        training_config = {
            "model_name": model.name,
            "version": model.version,
            "training_data": model.training_data_urns,
            "features": model.features,
            "hyperparameters": model.custom_properties,
            "output_path": f"s3://models/{model.name}/{model.version}/",
        }

        config_path = output_dir / f"training_{model.name}.json"
        with open(config_path, "w") as f:
            json.dump(training_config, f, indent=2)
        artifacts.append(config_path)

        # Feature store definition
        if model.feature_table_urn:
            feature_config = {
                "feature_table": model.feature_table_urn,
                "features": model.features,
                "online_store": "redis",
                "offline_store": "s3",
                "entity_columns": ["id"],
            }

            feat_path = output_dir / f"features_{model.name}.yaml"
            import yaml
            with open(feat_path, "w") as f:
                yaml.dump(feature_config, f, default_flow_style=False)
            artifacts.append(feat_path)

        return artifacts


def main():
    """CLI for generating code artifacts."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate code from DataHub metadata")
    parser.add_argument("--server", default=None, help="DataHub GMS URL")
    parser.add_argument("--token", default=None, help="DataHub token")
    parser.add_argument("--output", default="examples/generated", help="Output directory")
    parser.add_argument("--platform", default=None, help="Filter by platform")
    args = parser.parse_args()

    client = DataHubClient(gms_url=args.server, token=args.token)
    service = CodeGenerationService(client)

    output_dir = Path(args.output)
    results = service.generate_all_artifacts(output_dir, args.platform)

    print(f"Generated artifacts in {output_dir}:")
    for category, files in results.items():
        print(f"  {category}: {len(files)} files")
        for f in files:
            print(f"    - {f}")


if __name__ == "__main__":
    main()