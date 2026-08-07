# PR title (paste this)

```
feat(skills): add freshness & SLA monitoring skill
```

# PR description (paste this body)

## Summary

Adds a new DataHub skill, `.agent-skills/freshness-sla-monitoring/SKILL.md`,
following the existing convention of `.agent-skills/test-review/` (plain
Markdown, references relative paths, no frontmatter required).

The skill covers the most common day-to-day job of a data reliability
analyst on a DataHub deployment:

- daily freshness checks against declared SLA (dataQualityAssertions),
- lineage-aware downstream impact assessment,
- OPERATIONAL incident lifecycle (open on the downstream consumer, track,
  resolve),
- explicit rules: never invent dataset names, never assume freshness, reuse
  active incidents.

It is written to work with any MCP/agent setup that can call the DataHub
GraphQL API (search, assertions, lineage, incidents) and was validated
against the acryl-datahub SDK (AgentSkill registration, see
`datahub/api/entities/agent/agent_skill.py`).

## Why

The repo already hosts internal skills (e.g. `test-review`); adding a
generic operational skill makes the pattern reusable by any agent operating
against DataHub and demonstrates the Agent Context Kit workflow
(`datahub agent-skill register`) for a common operational use case.

## Checklist

- [x] SKILL.md follows the `.agent-skills/` layout (Markdown, scoped
      instructions, explicit rules)
- [x] Only DataHub public APIs are referenced (GraphQL search, assertions,
      lineage, incidents)
- [x] No repo-specific paths or secrets
