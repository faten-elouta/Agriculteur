# Devpost submission draft — Terroir Context Agents

> Brouillon prêt à coller dans le formulaire Devpost du hackathon
> « Build with DataHub: The Agent Hackathon ». Remplacer les `[ ]` avant
> soumission (liens PR, vidéo).

---

## Project name

Terroir Context Agents

## Elevator pitch (≤140 characters)

"Which crop will still have water at its critical stage? Terroir Context Agents
answers before sowing — every number traced in DataHub." (136 chars — paste as
is into the Elevator pitch field.)

## Tagline

Un agriculteur ne peut semer qu'une fois par an. On lui montre, avant de semer,
si sa culture aura soif au moment où il n'y aura plus d'eau — et pourquoi, avec
des preuves tracées dans DataHub, pas des intuitions.

## Links

- **Try it live:** https://terroir-context-agents.vercel.app
- **Code repository:** https://github.com/faten-elouta/Agriculteur (Apache 2.0)
- **DataHub contributions (open source, opened during this hackathon):**
  - Connector: `hubeau` ingestion source — [ PR link once opened: https://github.com/faten-elouta/datahub/pull/new/feat/hubeau-source ]
  - Skill: `environmental-data-provenance` freshness/SLA monitoring — https://github.com/datahub-project/datahub/pull/18967
  - Docs: testing tip for `adding-source.md` — [ PR link once opened: https://github.com/faten-elouta/datahub/pull/new/docs/adding-source-testing-tip ]
- **Demo video (1 min):** `docs/video/terroir-context-agents.mp4` — to upload
  as unlisted on YouTube/Vimeo and paste the share link here before submitting.
- **Video thumbnail (3:2):** `docs/video/thumbnail.png`

---

## Inspiration

A farmer decides what to sow once a year. Once the seed is in the ground, the
calendar is fixed — if a crop's critical growth stage lands during peak water
stress and withdrawal restrictions kick in, the loss is already locked in.
Nobody making that call today has an easy way to see, before sowing, whether
this year's forecast puts a specific crop's most vulnerable week on a
collision course with the water shortage.

We also noticed the hackathon's own datasets (`nyc-taxi`, `showcase-ecommerce`)
ship with planted freshness and quality problems — a deliberate playground for
exactly the kind of agent we wanted to build: one that treats a data pipeline's
health as something to actively monitor and act on, not just read.

## What it does

Terroir Context Agents compares three crops on a real parcel **before sowing**,
using live public data — no synthetic fixtures required for the primary path:

1. **The parcel** — a farmer enters a commune; the app fetches real RPG parcel
   boundaries (IGN), soil texture (ISRIC SoilGrids, with a documented fallback
   chain), and nearby water-monitoring stations (Hub'Eau), all through public,
   keyless APIs.
2. **The result, in three tiers** — decision first, then why, then proof:
   - **Decision:** the three crops ranked by water-stress risk and margin
     (€/ha), a plain-language verdict, and a "what if I switch crop A for crop
     B" comparator.
   - **Why:** the exact dates where a crop's critical growth stage overlaps
     the forecast water-tension window, and concrete corrective levers
     (shift sowing date, earlier-maturing variety, secure irrigation rights)
     each with a quantified marginal gain in €/ha.
   - **Proof, collapsed by default:** the full data-quality certificate,
     confidence dashboard, and DataHub lineage graph — never hidden, just not
     forced on a farmer who wants an answer in ten seconds.
3. **A trust gate that refuses to lie.** Every number traces to a DataHub URN.
   When a critical source is stale or missing, the app doesn't quietly degrade
   — it says so, in plain language, or refuses to produce a number at all.
4. **A Sentinel agent that watches its own foundations.** Simulate a station
   outage and watch the invalidation propagate through the real DataHub
   lineage graph — `hubeau_hydrometrie → features_bilan_hydrique →
   scenarios_cultures → recommandations_parcelle` — tagging every downstream
   recommendation as unsafe and filing an incident, automatically.
5. **A second, domain-agnostic mode for judges.** The same Sentinelle agent
   also runs against the hackathon's own `nyc-taxi` datapack (`make
   demo-generic`), detecting the planted freshness anomaly and tagging it —
   proving the architecture isn't agriculture-specific, just instantiated
   there.

## How we built it

- **Python + Streamlit** for the UI; **FastAPI/FastMCP** for a GMS-compatible
  MCP server exposing 12 tools (search, lineage, freshness, run/incident
  read+write, DataHub Skills + Agent Context Kit).
- **DataHub is the runtime, not a dashboard bolted on afterward.** The
  recommendation engine reads dataset freshness and calibration metadata from
  the graph *before* computing a number, and every run and every simulated
  incident is written back as a `DataProcessInstance` / incident in DataHub —
  read and write, not just read.
- **Real public data**, no API key: French administrative geography
  (`geo.api.gouv.fr`), RPG parcels (IGN API Carto), soil texture (ISRIC
  SoilGrids), river and groundwater monitoring stations (Hub'Eau).
- **Deterministic agronomic model**: degree-day phenology per crop, a simple
  water-balance model, and an explicit three-tier confidence gate — the LLM
  never produces a number; every figure comes from a documented formula
  traceable to its inputs.
- **Metadata-aware code generation**: given the context graph, the same
  service that powers the app also generates ingestion recipes, dbt-style SQL,
  and Airflow DAGs from real dataset schemas and lineage — sample artifacts
  are in `examples/generated/`.

## DataHub, specifically

- **Entities**: `Dataset`s for every upstream source, `MLModel` +
  `MLModelGroup` for the hydrological model with its calibration basin as
  metadata, `MLFeatureTable`/`MLFeature`, a `DataProcessInstance` per
  recommendation run (what makes every recommendation replayable), a domain,
  a French-language glossary, and risk/provenance tags.
- **Lineage** is navigable end-to-end from a farmer-facing number back to the
  raw station reading that fed it.
- **MCP Server**: 12 tools, exercised in both the agriculture graph and the
  hackathon's own `nyc-taxi`/`showcase-ecommerce` datapacks.
- **DataHub Skills / Agent Context Kit**: consumed the freshness/lineage/
  curation skills from the official registry, and contributed one back
  (`environmental-data-provenance` — PR #18967, open).
- **Contributed upstream, not just consumed**: a new `hubeau` ingestion
  connector (French open water data had no connector in DataHub before this),
  plus a small docs fix for a real friction point hit while building it.

## Challenges we ran into

- **Refusing to fabricate precision.** A tester asked for a 2035/2050 climate
  comparison. We didn't have real multi-year climate projection data wired
  in, and faking a "+2.1°C in 2050" number would have directly contradicted
  the app's own "no invented figures" principle. We scoped that out as a
  separate, honestly-sourced follow-up (Open-Meteo's Climate API — verified
  live, free, keyless, real CMIP6 ensembles) instead of shipping a plausible
  lie.
- **Building a real DataHub source connector from scratch.** No connector
  existed for French water data. We ended up modeling the schema by sampling
  live API responses rather than hardcoding field names, so it stays correct
  as the upstream API evolves — and hit (and documented) a real friction
  point running a single new source's tests without the entire monorepo's
  test extras installed.
- **Redesigning the decision screen mid-hackathon** based on direct farmer
  feedback: an early version made a farmer read through data-provenance
  jargon before getting an answer. We collapsed the four-screen result tunnel
  into a single decision → why → proof pyramid, without touching the
  calculation engine.

## Accomplishments that we're proud of

- Every number a farmer sees traces to a DataHub URN; the app can produce
  *no* number rather than a false one when a critical source is degraded.
- The same code path runs, unmodified, on the hackathon's own datapacks and
  on a real French water-stress decision.
- A DataHub connector and a documentation fix, both opened upstream, not just
  planned.

## What we learned

- The interesting failure mode for "AI + data" isn't the model being wrong —
  it's the model being confidently wrong because nobody checked whether its
  inputs were still fresh. A context graph makes that checkable structurally
  instead of by convention.
- Writing back to the graph (runs, incidents, tags) is what turns a read-only
  dashboard into something the next agent — or the next hackathon
  participant — actually inherits.

## What's next

- Wire the verified Open-Meteo Climate API in as a properly-scoped second
  project phase for honest multi-year (2035/2050) crop resilience scoring.
- Extend the `hubeau` connector to Hub'Eau's time-series and water-withdrawal
  APIs.
- Expand beyond the Cher basin and the three demo crops.

## Built with

python, streamlit, fastapi, fastmcp, datahub, mcp, pandas, pydantic, requests,
docker, vercel, ign-api-carto, hubeau, soilgrids, geo-api-gouv-fr

## Challenges covered

Agents That Do Real Work · Metadata-Aware Code Generation & Development ·
Production ML Agents (via `MLModel` lineage protection on the calibrated
hydrological model)
