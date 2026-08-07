# Contribution OSS au projet DataHub (bonus Devpost)

Ce dossier contient une contribution **prête à soumettre** au repo
[datahub-project/datahub](https://github.com/datahub-project/datahub) — une
DataHub Skill au format du dossier `.agent-skills/` du repo, comme le demande
l'Appel à projet « Build with DataHub: The Agent Hackathon » (bonus :
« contribute back to the graph », *ex. contributing skills*).

## Ce que nous apportons

| Artefact | Chemin | Statut |
| --- | --- | --- |
| Skill « Freshness & SLA monitoring » | `contrib/datahub/.agent-skills/freshness-sla-monitoring/SKILL.md` | prêt à soumettre |
| Description de la PR (corps + titre) | `contrib/datahub/PR-description.md` | prêt à coller |
| Les 3 skills Terroir (agentskills.io) | `catalog/skills/*/SKILL.md` | enregistrés dans notre graphe |

## Pourquoi ce skill

Le repo DataHub héberge ses propres skills dans `.agent-skills/` (ex.
`test-review`). Il manque un skill générique pour le cas d'usage le plus
courant d'une plateforme de données : **surveiller la fraîcheur des datasets
et gérer les incidents en cascade** (assertions, lineage amont/aval, création
d'incident, suivi). C'est exactement la procédure que nous exécutons dans ce
repo (voir `catalog/skills/freshness_sla/SKILL.md`), généralisée pour
n'importe quelle instance DataHub.

La procédure du skill s'appuie uniquement sur des APIs DataHub publiques
(GraphQL `dataQualityAssertions`, `scrollAcrossEntities`, entités Incident),
donc applicable partout.

## Comment soumettre

1. Créer une PR sur https://github.com/datahub-project/datahub :
   - branche : `add-freshness-sla-monitoring-skill`
   - nouveaux fichiers : copier `.agent-skills/freshness-sla-monitoring/`
     à la racine du repo (les `.agent-skills/*/SKILL.md` existants sont à la
     racine, ex. `.agent-skills/test-review/SKILL.md`).
2. Coller le titre + le corps de `PR-description.md`.
3. Signer le CLA DataHub (le bot le demande sur la PR).

## Preuve que les skills marchent (dans ce repo)

- `catalog/skills/*/SKILL.md` sont enregistrés dans le graphe comme entités
  AgentSkill via `catalog/ingest_skills.py` (contrat REST OpenAPI v3, ou via
  le SDK `datahub.api.entities.agent.agent_skill.AgentSkill` — vérifié avec
  acryl-datahub 1.7).
- Le serveur MCP les expose aux agents (`list_skills`, `get_skill`,
  `agent_context`) — le serveur de démo public embarque les 3 skills.
- Tests : `tests/test_mcp_real_backend.py`, `tests/test_demo_gms.py`
  (91 tests verts).
