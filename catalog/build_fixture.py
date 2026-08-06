"""Construit/valide la fixture agricole sans serveur DataHub ni SDK."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="fixtures/graph.json")
    args = parser.parse_args()
    output = Path(args.output)
    if not output.exists():
        raise SystemExit("Fixture source absente; restaurez fixtures/graph.json depuis le dépôt.")
    graph = json.loads(output.read_text(encoding="utf-8"))
    if not isinstance(graph.get("datasets"), dict) or not isinstance(graph.get("lineage"), dict):
        raise SystemExit("Fixture invalide: datasets/lineage manquants.")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(graph['datasets'])} datasets, {len(graph['lineage'])} noeuds amont -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
