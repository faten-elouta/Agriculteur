---
name: Surveillance de la fraîcheur des sources
description: >
  Règles de surveillance de la fraîcheur des sources de contexte Terroir.
  À utiliser quand on doit vérifier l'état des sources (SLA vs dernière
  mise à jour), signaler une source périmée ou évaluer l'impact en aval.
---

# Surveillance de la fraîcheur des sources

## Quand l'utiliser

- Vérifier si les sources du graphe respectent leur SLA de fraîcheur annoncé.
- Ouvrir un incident DataHub sur les assets impactés par une source périmée.
- Tracer son propre run une fois le contrôle effectué.

## Procédure

1. Appeler `freshness_summary` : chaque source répond `ok` (à jour), `stale`
   (dépassement de SLA) ou `unknown` (date inconnue).
2. Pour chaque source `stale`, appeler `get_lineage` pour identifier les
   datasets aval impactés (le signal descend la chaîne).
3. Créer un incident `OPERATIONAL` via `create_incident` sur le premier asset
   aval impacté, titre explicite : « Source X en dépassement de SLA ».
4. Tracer le run de surveillance via `emit_run` sur `recommandations_parcelle`
   avec un résumé des incidents ouverts.
5. Quand la source est rétablie, résoudre l'incident via `resolve_incident`.

## Règles

- Ne jamais supposer une date de mise à jour : toujours lire `last_updated`
  dans le graphe.
- Un dépassement de SLA strict est `stale` ; ne le classer `ok` sous aucun
  prétexte.
- L'incident est créé sur l'asset AVAL (l'impact), pas sur la source.
