---
name: Modèle recommandations_parcelle
description: >
  Fiche modèle du modèle de recommandation de culture `recommandations_parcelle`.
  À utiliser quand un agent doit expliquer les recommandations, leur provenance
  ou les données qui alimentent le modèle.
---

# Modèle recommandations_parcelle

## Qu'est-ce que c'est

Modèle de recommandation de culture avant semis, produit par Terroir Context
Agents à partir des sources de contexte publiques (eau, sol, climat, économie,
parcelle). Il compare trois cultures et positionne leur stade critique face à
la tension saisonnière sur l'eau.

## Provenance (lineage amont)

Le modèle est relié à ses datasets d'entrée dans le graphe DataHub :
`hubeau_hydrometrie`, `hubeau_piezometrie`, `hubeau_onde`, `sol_rrp`,
`climat_journalier`, `prevision_saisonniere`, `ref_agro_economique`,
`parcelles`.

Pour expliquer une recommandation :

1. Lire le lineage du modèle ou des datasets via `get_lineage`.
2. Vérifier la fraîcheur des sources amont via `freshness_summary` — une
   recommandation fondée sur une source périmée doit être signalée.
3. Citer la provenance (source, millésime, niveau de preuve) plutôt que
   d'affirmer un chiffre.

## Règles

- Les valeurs climatiques futures et économiques sont modélisées (snapshots
  synthétiques) : toujours le signaler.
- Les parcelles sont des parcelles RPG réelles anonymisées ; le sol est une
  estimation (SoilGrids ou interpolation IDW) de confiance moyenne/faible.
- Ne jamais présenter un chiffre sans sa provenance.
