# Exemples

## `gms_demo.py` — démo autonome contre le graphe DataHub public

Interroge le serveur GMS-compatible hébergé sur Render
(`https://terroir-context-gms.onrender.com`, configurable via `DATAHUB_GMS_URL`)
avec la bibliothèque standard uniquement :

1. connecte au GMS et liste les 11 datasets du graphe de contexte (fraîcheur),
2. lit le lineage de `features_bilan_hydrique` (amont : climat, sol, parcelles,
   Hub'Eau… ; aval : scénarios cultures, modèle hydrologique),
3. écrit dans le graphe : trace un run `SUCCESS` sur `recommandations_parcelle`,
   crée puis résout un incident sur `sol_rrp`,
4. résume la fraîcheur des 8 sources vs leur SLA annoncé.

```bash
python examples/gms_demo.py
```
