#!/usr/bin/env python3
"""
catalog/make_fixture.py — Fige le graphe en fixture pour le mode hors ligne.

Permet a la Sentinelle de tourner et d'etre testee sans serveur DataHub, ce qui rend
la demo reproductible pour un juge qui n'a rien installe.

    python catalog/build_graph.py --dry-run /tmp/mcps.json
    python catalog/make_fixture.py /tmp/mcps.json fixtures/graph.json

Licence: Apache-2.0
"""

import collections
import json
import sys


def payload(mcp: dict) -> dict:
    aspect = mcp["aspect"]
    return json.loads(aspect["value"]) if "value" in aspect else aspect


def main(src: str, dst: str) -> int:
    mcps = json.load(open(src, encoding="utf-8"))
    datasets: dict = {}
    lineage = collections.defaultdict(list)

    for mcp in mcps:
        if mcp["aspectName"] == "datasetProperties":
            datasets[mcp["entityUrn"]] = payload(mcp).get("customProperties", {})
        elif mcp["aspectName"] == "upstreamLineage":
            for upstream in payload(mcp)["upstreams"]:
                lineage[upstream["dataset"]].append(mcp["entityUrn"])

    json.dump({"datasets": datasets, "lineage": dict(lineage)},
              open(dst, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"{len(datasets)} datasets, {len(lineage)} noeuds amont -> {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
