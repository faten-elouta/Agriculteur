---
name: Génération de code metadata-aware
description: >
  Workflow de génération de code de pipeline (recettes d'ingestion, SQL de
  transformation, DAG Airflow) à partir des schémas, du lineage et des règles
  réels lus dans DataHub. À utiliser pour produire des artefacts prêts à
  merger, jamais du code qui devine la structure des données.
---

# Génération de code metadata-aware

## Quand l'utiliser

- Générer une recette d'ingestion DataHub pour un dataset existant.
- Générer une transformation SQL (modèle dbt) avec les colonnes réelles.
- Générer un DAG Airflow dont les dépendances suivent le lineage réel.

## Procédure

1. Découvrir les datasets via la recherche : ne générer que pour des entités
   qui existent dans le graphe, jamais de structure inventée.
2. Lire les schémas réels (`schemaMetadata`) : noms de champs, types natifs,
   descriptions. Les colonnes utilisées dans le SQL doivent venir de là.
3. Lire le lineage (`upstreamLineage`) pour déduire les dépendances du DAG et
   les sources de la transformation.
4. Lire les propriétés réelles (owner, tags, glossary terms, SLA) et les
   reporter dans la recette d'ingestion (transformers).
5. Écrire les artefacts dans un dossier de sortie, chacun dans son fichier,
   avec les métadonnées lues (pas de TODO vide).

## Règles

- Pas de champ inventé : si le schéma est vide, produire un artefact honnête
  (champs vides) plutôt qu'un faux schéma.
- Le DAG généré doit s'exécuter : pas de variable non définie, pas
  d'interpolation cassée — vérifier le contenu généré.
- Les secrets passent par variables d'environnement (`DATAHUB_GMS_URL`,
  `DATAHUB_TOKEN`), jamais en clair dans un artefact.
