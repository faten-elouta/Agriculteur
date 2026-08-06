# brief.md — TERROIR CONTEXT AGENTS

> Soumission « Build with DataHub: The Agent Hackathon » — deadline 10 août 2026, 23h00 GMT+2
> Version 2.0 — 30 juillet 2026 — stratégie de soumission, double mode de données

---

<strategie_de_soumission>

<constat_declencheur>
Le hackathon fournit ses propres jeux de données, chargeables en une commande : `datahub datapack load showcase-ecommerce`, `nyc-taxi`, `healthcare`, `fiction-retail`. Deux d'entre eux contiennent **des problèmes de fraîcheur et de qualité volontairement plantés**. Le showcase couvre 1 049 entités avec du lineage cross-plateforme sur Snowflake, Looker, PowerBI, Tableau, dbt, Spark, PostgreSQL et S3.

Autrement dit : **les organisateurs ont préparé exactement le terrain de jeu de l'agent Sentinelle.** Ne pas s'en servir serait une erreur stratégique.

La page précise aussi que ces jeux sont sûrs pour une publication Apache 2.0, et que toute donnée apportée par le participant doit avoir une licence compatible. C'est un avertissement direct sur le plan initial (DRIAS, RPG).
</constat_declencheur>

<decision_structurante>
Le projet ship en **deux modes**, un seul code, deux jeux de données.

| | Mode générique | Mode agriculture |
|---|---|---|
| Données | `nyc-taxi` + `showcase-ecommerce`, chargés par datapack | Snapshot agricole embarqué dans le repo |
| Rôle | **Prouver que l'architecture marche sur les données du jury, en 2 minutes** | La démonstration métier, le fond de la vidéo |
| Ce qu'on y montre | Détection des anomalies plantées, remontée du lineage cross-plateforme, écriture des tags et du rapport d'impact | Le calendrier de recouvrement, les leviers, la décision avant semis |
| Commande | `datahub datapack load nyc-taxi && make demo-generic` | `make demo` |
</decision_structurante>

<pourquoi_cela_maximise_la_note>
- **Use of DataHub** — le mode générique tourne sur le graphe officiel, avec du lineage cross-plateforme réel sur 8 systèmes. Beaucoup plus profond que ce qu'un snapshot maison peut produire en 11 jours.
- **Technical Execution** — un juge teste en 2 minutes sur des données qu'il connaît déjà, sans clé API, sans télécharger quoi que ce soit. C'est le chemin d'évaluation le plus court possible.
- **Originality** — les anomalies plantées sont là pour être trouvées ; peu de participants les exploiteront comme déclencheur d'une invalidation métier en aval.
- **Real-World Usefulness** — le double mode **prouve** la thèse « le domaine agricole est l'instanciation, pas le produit » au lieu de l'affirmer. Un juge voit le même code décider sur des courses de taxi et sur un assolement.
- **Submission Quality** — la première ligne du README devient une commande copiable qui marche.
</pourquoi_cela_maximise_la_note>

<risque_licence_neutralise>
Le snapshot agricole embarqué est **synthétique mais réaliste** : construit par un script à partir de statistiques publiques (normales climatiques, rendements départementaux, coefficients FAO-56), clairement libellé comme tel dans `data/SOURCES.md`, avec un fichier de licence propre. Aucune redistribution de donnée sous licence contrainte dans le repo.

En parallèle, un script `fetch_real.py` récupère les vraies données HubEau (licence ouverte, redistribuable) pour qui veut faire tourner en réel. Les sources à licence plus incertaine — DRIAS, RPG — sont **fetchées, jamais commitées**.

Cette séparation n'est pas un contournement, c'est la bonne pratique, et elle mérite un paragraphe dans le README : elle montre au jury qu'on a lu les règles.
</risque_licence_neutralise>

<visibilite_communaute>
Les juges incluent l'équipe DataHub, et le canal `#agent-hackathon` du Slack DataHub est là où ils sont. Des office hours sont prévues à mi-parcours.

- Rejoindre le Slack **le J1**, pas le J10.
- Poster deux fois : une fois le concept en trois lignes (J2), une fois un GIF de la Sentinelle qui détecte une anomalie plantée de `nyc-taxi` (J7). Rien de plus — la visibilité utile est brève et démontrable.
- Participer aux office hours avec **une question précise** sur le modèle de métadonnées, pas une question générale. Une bonne question fait plus pour la mémorisation qu'un long message.
- Ouvrir les PR open source **avant** la soumission, pour qu'elles soient visibles et discutées, pas découvertes le jour du jugement.
</visibilite_communaute>

<ce_qui_ne_change_pas>
Le fond métier, l'architecture à trois agents, la porte de confiance, l'interface et les leviers restent identiques. Le mode générique n'est pas un second projet : c'est **le même code branché sur un autre graphe**, ce qui est précisément la preuve que le graphe est bien le runtime.
</ce_qui_ne_change_pas>

</strategie_de_soumission>

---

<positionnement>

**Mission**
Aider l'agriculteur à choisir sa culture **avant de semer**, à partir des prévisions de température, de précipitations et d'eau disponible sur la saison à venir.

**La question à laquelle l'agent répond**
> « Ce que je m'apprête à semer trouvera-t-il l'eau dont il aura besoin, au moment où il en aura besoin ? »

C'est une décision qui se prend une fois par an, qui engage toute la campagne, et qui ne se rattrape pas. Une fois la graine en terre, le calendrier est fixé : si le pic de besoin tombe pendant la canicule et que les prélèvements sont restreints, la perte est acquise. **Tout le produit sert ce moment-là — avant le semis, jamais après.**

**Les trois prévisions qui fondent la décision**

| Prévision | Ce qu'elle détermine |
|---|---|
| **Température** | La vitesse de développement de la culture, donc **la date à laquelle elle atteindra son stade critique**. Un printemps chaud avance la floraison de deux semaines et la pousse dans l'été. |
| **Précipitations** | La pluie efficace disponible gratuitement, donc le déficit qu'il faudra combler par irrigation. |
| **Eau disponible** | Débits d'étiage, niveaux de nappe, probabilité d'arrêté de restriction — **est-ce qu'irriguer sera seulement possible**, physiquement et légalement. |

La température n'est donc pas seulement un facteur de stress : c'est elle qui **déplace le calendrier**. C'est le lien qui rend le produit non trivial, et personne ne le fait bien aujourd'hui.

**Ce que l'agent produit**
Trois cultures classées, chacune avec son calendrier complet du semis à la récolte estimée, le nombre de jours pendant lesquels son stade critique tombe dans la fenêtre de tension, la marge brute attendue — et, pour toute culture à risque, **les leviers concrets pour la sauver** : décaler le semis, variété plus précoce, volume à sécuriser.

**Ce qui le rend crédible, et gagnant pour ce hackathon**
Une prévision est fragile par nature. Un conseil fondé sur une prévision non traçable est un risque, pas une aide. DataHub est ce qui transforme le second en le premier : chaque chiffre remonte à sa source, à sa date et à son modèle, et **une recommandation s'invalide toute seule quand la donnée qui la fondait se dégrade**.

**Anti-thèse à éviter**
Un chatbot agronomique auquel on aurait branché un catalogue. Si le projet fonctionne encore après avoir débranché DataHub, il est disqualifié de facto sur le critère n°1.

</positionnement>

---

<objectifs>

<objectif_primaire>
Donner à l'agriculteur, **avant le semis**, une comparaison de cultures fondée sur les prévisions de température, de précipitations et d'eau disponible — et lui montrer comment éviter la collision entre le besoin en eau de sa culture et la période où l'eau manquera.
</objectif_primaire>

<objectifs_secondaires>
1. Produire des recommandations de choix de culture chiffrées en €/ha sur 3 scénarios climatiques.
2. Détecter et propager automatiquement l'invalidation d'une recommandation quand une source amont se dégrade.
3. Enrichir le graphe à chaque exécution : le catalogue devient plus riche parce que les agents l'utilisent.
4. Générer le code d'ingestion DataHub d'un nouveau territoire à partir des métadonnées existantes.
</objectifs_secondaires>

<non_objectifs>
- Concurrencer un outil d'aide à la décision agronomique professionnel.
- Calibrer finement un modèle hydrologique (hors périmètre hackathon).
- Reconstruire des fonctionnalités déjà livrées par DataHub (search UI, lineage viewer, glossaire).
- Traiter des données personnelles d'exploitants.
</non_objectifs>

</objectifs>

---

<utilisateurs>

<persona id="P1" nom="Agriculteur / conseiller de chambre d'agriculture" statut="utilisateur final">
  <besoin>Choisir entre 3 cultures pour la prochaine campagne sur une parcelle donnée, avec le coût d'irrigation associé.</besoin>
  <question_type>« Sur ma parcelle à Vierzon, maïs ou sorgho l'an prochain ? Et si l'été est sec ? »</question_type>
  <attente_de_sortie>3 scénarios chiffrés + niveau de confiance explicite + date de dernière donnée.</attente_de_sortie>
  <competence_technique>nulle</competence_technique>
</persona>

<persona id="P2" nom="Data / ML platform engineer" statut="cible du jury">
  <besoin>Savoir quels livrables aval sont cassés quand une source amont tombe, sans audit manuel.</besoin>
  <question_type>« La station K4470010 est muette depuis 12 jours — qu'est-ce qui est impacté ? »</question_type>
  <attente_de_sortie>Liste des assets et des recommandations invalidées, tagués dans DataHub, avec rapport d'impact déposé.</attente_de_sortie>
  <competence_technique>élevée</competence_technique>
</persona>

<persona id="P3" nom="Data steward territorial" statut="bénéficiaire indirect">
  <besoin>Que le catalogue s'enrichisse au fil de l'usage plutôt que de se périmer.</besoin>
  <attente_de_sortie>Glossaire, descriptions, ownership et documents complétés par les agents.</attente_de_sortie>
  <competence_technique>moyenne</competence_technique>
</persona>

</utilisateurs>

---

<perimetre>

<inclus>
- Territoire : **Nouvel Espace Cher** — sous-bassins du Cher (Centre-Val de Loire, France).
- Cultures évaluées : maïs grain, sorgho grain, tournesol, orge de printemps, blé tendre, luzerne. Le système en propose 3 et **n'est pas limité aux cultures déjà déclarées sur la parcelle** — proposer une culture à laquelle l'agriculteur n'avait pas pensé fait partie de la valeur.
- **Horizons de prévision : 3, 6 et 12 mois.** L'horizon est le curseur central de l'application. Plus il est lointain, moins la prévision est fiable, et l'interface l'affiche au lieu de le masquer.
- **Date de semis**, saisie par l'agriculteur. C'est elle qui positionne la fenêtre critique de la culture sur le calendrier — deux cultures identiques semées à trois semaines d'écart n'ont pas le même risque.
- **Type de sol et réserve utile** de la parcelle : ils déterminent combien de jours la culture tient sans irrigation pendant un épisode sec.
- Horizon de décision : une campagne culturale (assolement N+1).
</inclus>

<exclu>
- Autres régions, autres cultures, viticulture, élevage.
- Décision infra-saisonnière (pilotage d'irrigation au jour le jour).
- Prise en compte du sol à la parcelle au-delà de la réserve utile moyenne.
</exclu>

</perimetre>

---

<donnees_entree>

<source id="S1" nom="HubEau — Hydrométrie" criticite="haute">
  <fournisseur>Eau France / OFB (service public, libre)</fournisseur>
  <acces>API REST — `https://hubeau.eaufrance.fr/api/v2/hydrometrie/observations_tr`</acces>
  <granularite>station × pas de temps horaire/journalier</granularite>
  <champs_utilises>
    code_station : string (identifiant national)
    date_obs : timestamp ISO-8601
    grandeur_hydro : enum {Q=débit, H=hauteur}
    resultat_obs : float (débit en L/s)
    code_statut : int (qualification de la mesure)
  </champs_utilises>
  <volume_attendu>~15 stations × 10 ans de pas journalier</volume_attendu>
  <role>Contrainte de disponibilité de la ressource et contexte d'étiage.</role>
</source>

<source id="S2" nom="HubEau — Piézométrie (niveaux nappes)" criticite="moyenne">
  <acces>API REST — `https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/chroniques`</acces>
  <champs_utilises>
    code_bss : string
    date_mesure : date
    niveau_nappe_eau : float (m NGF)
    profondeur_nappe : float (m)
  </champs_utilises>
  <role>État de la ressource souterraine, principale source d'irrigation sur le bassin.</role>
</source>

<source id="S3" nom="HubEau — ONDE (observatoire des étiages)" criticite="moyenne">
  <acces>API REST — `https://hubeau.eaufrance.fr/api/v1/ecoulement/observations`</acces>
  <champs_utilises>
    code_station : string
    date_observation : date
    libelle_ecoulement : enum {écoulement visible, écoulement non visible, assec, observation impossible}
  </champs_utilises>
  <role>Signal terrain d'assèchement — utilisé comme facteur de risque réglementaire (restrictions d'usage).</role>
</source>

<source id="S4" nom="DRIAS — projections climatiques" criticite="haute">
  <fournisseur>Météo-France / DRIAS Les Futurs (libre, téléchargement fichier — pas d'API REST)</fournisseur>
  <acces>Export CSV/NetCDF depuis drias-climat.fr, figé en snapshot dans le repo</acces>
  <granularite>maille SAFRAN 8 km × pas journalier</granularite>
  <champs_utilises>
    id_maille : int
    date : date
    tas : float (température moyenne, °C)
    tasmax / tasmin : float (°C)
    prtot : float (précipitations, mm/j)
    evspsblpot : float (ETP Penman, mm/j)
    scenario : enum {historique, rcp45, rcp85}
  </champs_utilises>
  <role>Cœur du volet « estimation température et eau ». Alimente le bilan hydrique.</role>
</source>

<source id="S5" nom="RPG — Registre Parcellaire Graphique" criticite="moyenne">
  <fournisseur>IGN / data.gouv.fr (anonymisé, libre)</fournisseur>
  <acces>Téléchargement GeoPackage / Shapefile</acces>
  <champs_utilises>
    id_parcel : string
    code_cultu : string (code culture déclarée)
    surf_parc : float (hectares)
    geometry : polygon (EPSG:2154 Lambert-93)
  </champs_utilises>
  <role>Ancrage spatial, rattachement parcelle → maille climatique → sous-bassin.</role>
</source>

<source id="S6" nom="Référentiel agro-économique" criticite="haute">
  <fournisseur>Construit manuellement — sources : FAO-56 (coefficients culturaux), Agreste (rendements départementaux), barèmes chambres d'agriculture, redevances Agence de l'eau Loire-Bretagne</fournisseur>
  <acces>CSV versionné dans `data/reference/`</acces>
  <schema>
    culture : string
    kc_initial / kc_mid / kc_end : float (coefficients culturaux FAO-56)
    duree_stade_j : int[]
    rendement_ref_qx_ha : float
    prix_moyen_eur_qx : float
    charges_operationnelles_eur_ha : float
    prix_eau_eur_m3 : float
    seuil_stress_hydrique_mm : float
  </schema>
  <role>Traduction du bilan hydrique en euros. C'est la source la plus fragile — elle sera taguée comme telle dans le graphe.</role>
</source>

<source id="S7" nom="Sol — réserve utile de la parcelle" criticite="haute">
  <fournisseur>GIS Sol / INRAE — Référentiel Régional Pédologique (RRP), complété par la BDAT</fournisseur>
  <acces>Téléchargement de couches SIG, jointure spatiale avec le RPG</acces>
  <champs_utilises>
    id_ucs : string (unité cartographique de sol)
    type_sol : string (ex. limono-argileux)
    reserve_utile_mm : float
    profondeur_enracinement_cm : float
  </champs_utilises>
  <role>Détermine l'autonomie hydrique de la parcelle : combien de jours de tension la culture absorbe avant de décrocher. **C'est cette source qui permet au système de proposer des cultures auxquelles l'agriculteur n'avait pas pensé** — un sol à forte réserve utile ouvre des options qu'un sol filtrant ferme.</role>
</source>

<source id="S8" nom="Prévision saisonnière" criticite="haute">
  <fournisseur>Copernicus Climate Change Service (C3S) — prévisions saisonnières multi-modèles, libres après inscription. Repli : climatologie DRIAS.</fournisseur>
  <acces>API CDS / export figé en snapshot</acces>
  <champs_utilises>
    mois_cible : date
    anomalie_temperature : float (°C vs normale)
    tercile_precipitation : enum {sec, normal, humide}
    probabilite : float (0–1)
  </champs_utilises>
  <horizons>
    3 mois : prévision saisonnière probabiliste — fiabilité utile
    6 mois : prévision dégradée + climatologie — fiabilité faible
    12 mois : climatologie + tendance DRIAS uniquement — aucune valeur prédictive individuelle
  </horizons>
  <role>Alimente la **fenêtre de tension sur la ressource** affichée sur le calendrier. Le niveau de preuve chute avec l'horizon, et cette chute est **matérialisée dans l'interface et dans le graphe** — c'est la démonstration la plus honnête que le projet puisse faire de sa propre incertitude.</role>
</source>

<qualification_des_sources>
Chaque source est enregistrée dans DataHub avec des **custom properties de confiance** :
`last_updated`, `freshness_sla_days`, `spatial_coverage`, `licence`, `niveau_de_preuve` ∈ {mesure, modélisation, dire d'expert}.
Le niveau de preuve est utilisé par l'agent Conseiller pour moduler son langage.
</qualification_des_sources>

</donnees_entree>

---

<donnees_sortie>

<sortie id="O1" nom="Recommandation de culture" destinataire="P1" format="JSON + rendu UI">
```json
{
  "parcelle_id": "string",
  "commune": "string",
  "surface_ha": 0.0,
  "sol": {
    "type": "string",
    "reserve_utile_mm": 0.0,
    "autonomie_jours_sans_irrigation": 0
  },
  "date_semis": "ISO-8601",
  "horizon_mois": 3,
  "genere_le": "ISO-8601",
  "fenetre_de_tension": [
    {"mois": "2027-07", "intensite": "forte", "probabilite": 0.0, "origine": "prevision_saisonniere"}
  ],
  "cultures": [
    {
      "culture": "tournesol",
      "rang": 1,
      "deja_cultivee_sur_parcelle": false,
      "calendrier": {
        "semis": "2027-04-20",
        "levee": "2027-05-04",
        "stade_critique": {"nom": "floraison", "debut": "2027-06-25", "fin": "2027-07-20"},
        "maturite": "2027-08-28",
        "recolte_estimee": "2027-09-05",
        "duree_cycle_j": 138,
        "incertitude_recolte_j": 12
      },
      "recouvrement_avec_tension_j": 0,
      "verdict": "cycle_termine_avant|pic_decale|pic_en_pleine_tension",
      "besoin_irrigation_mm": 0.0,
      "cout_eau_eur_ha": 0.0,
      "marge_brute_eur_ha": 0.0,
      "perte_si_restriction_eur_ha": 0.0,
      "adaptation_au_sol": "bonne|moyenne|inadaptee",
      "leviers": [
        {
          "type": "decaler_semis|variete_plus_precoce|securiser_irrigation|reduire_densite|changer_culture",
          "action": "Avancer le semis au 25 mars",
          "recouvrement_apres_j": 0,
          "recolte_apres": "2027-08-18",
          "gain_marge_eur_ha": 0.0,
          "faisabilite": "immediate|a_verifier|sous_autorisation",
          "reserve": "string"
        }
      ]
    }
  ],
  "confiance": {
    "niveau": "haute|degradee|insuffisante",
    "motifs": ["string"],
    "fiabilite_prevision": "utile|faible|climatologique"
  },
  "provenance": {
    "datasets_amont": [
      {"urn": "urn:li:dataset:...", "last_updated": "ISO-8601", "niveau_de_preuve": "mesure"}
    ],
    "modele": {"urn": "urn:li:mlModel:...", "version": "string", "bassin_calibration": "string"},
    "run_urn": "urn:li:dataProcessInstance:...",
    "chaine_lineage_verifiee": true
  }
}
```
  <champ_central>`recouvrement_avec_tension_j` — le nombre de jours pendant lesquels le pic de besoin en eau de la culture tombe dans la fenêtre de tension prévue. **C'est la variable de décision du produit.** Zéro jour de recouvrement bat une marge brute théorique plus élevée.</champ_central>
  <regle_dure>Si `confiance.niveau == "insuffisante"`, le bloc `cultures` est **vide**. Aucun chiffre n'est produit sans provenance vérifiée.</regle_dure>
  <regle_horizon>À 12 mois, `fiabilite_prevision` vaut obligatoirement `climatologique` et l'interface ne présente aucune probabilité individuelle — seulement des tendances.</regle_horizon>
</sortie>

<sortie id="O2" nom="Rapport d'impact" destinataire="P2" format="JSON + document DataHub">
```json
{
  "declencheur": {
    "type": "freshness_breach|schema_drift|calibration_mismatch|assec_declare",
    "asset_urn": "urn:li:dataset:...",
    "detecte_le": "ISO-8601",
    "detail": "string"
  },
  "impact": {
    "assets_aval": ["urn:li:dataset:...", "urn:li:mlModel:..."],
    "profondeur_lineage": 0,
    "recommandations_invalidees": [
      {"parcelle_id": "string", "run_urn": "...", "emise_le": "ISO-8601", "delta_marge_eur_ha": 0.0}
    ],
    "exposition_financiere_eur": 0.0
  },
  "actions_ecrites_dans_datahub": {
    "tags_ajoutes": ["recommandation-a-risque"],
    "descriptions_mises_a_jour": ["urn:..."],
    "document_urn": "urn:li:document:..."
  }
}
```
</sortie>

<sortie id="O3" nom="Artefacts de code générés" destinataire="P2" format="fichiers dans examples/">
  - Recette d'ingestion DataHub YAML pour un nouveau territoire
  - Script de transformation SQL (DuckDB/dbt-style) du bilan hydrique
  - DAG Airflow d'orchestration de la chaîne
  <justification>Couvre le challenge « Metadata-Aware Code Generation ». Le code est généré **après lecture des schémas réels dans DataHub**, jamais deviné.</justification>
</sortie>

<sortie id="O4" nom="Enrichissement du graphe" destinataire="P3" format="écritures DataHub">
  À chaque exécution : `save_document` du run, `update_description` des datasets sous-documentés,
  `add_glossary_terms` sur les colonnes rattachables au glossaire métier, `add_tags` de confiance.
</sortie>

</donnees_sortie>

---

<modeles>

<modele id="M1" nom="Bilan hydrique FAO-56 + datation des stades par degrés-jours" type="déterministe" role="cœur métier">
  <formulation>
    Stades : cumul_DJ(j) = Σ max(0, T_moy(j) − T_base). Un stade est atteint quand le cumul franchit son seuil.
    → **la prévision de température date la floraison, elle ne fait pas que la stresser**
    ETM(j) = Kc(stade) × ETP(j)
    Pluie_efficace(j) = f(prtot(j), RU_sol)
    Deficit(j) = max(0, ETM(j) − Pluie_efficace(j) − Reserve(j))
    Besoin_irrigation = Σ Deficit(j) sur le cycle cultural
    Recouvrement = |fenêtre du stade critique ∩ fenêtre de tension prévue| en jours
  </formulation>
  <entrees>S4 et S8 (température, précipitations, ETP), S6 (T_base, seuils de cumul par stade, Kc), S7 (réserve utile)</entrees>
  <sortie>Dates de stades → fenêtre critique → jours de recouvrement → mm d'irrigation → m³/ha → €/ha</sortie>
  <justification>Standard international, auditable, implémentable en ~150 lignes. Les degrés-jours sont ce qui relie la prévision de température au calendrier, donc au risque. Sans eux, le produit se réduit à une moyenne saisonnière et perd son intérêt.</justification>
</modele>

<modele id="M2" nom="GR4J — contexte hydrologique du bassin" type="hydrologique conceptuel" role="contrainte de ressource">
  <usage>Simulation des débits d'étiage du sous-bassin pour estimer le risque de restriction d'usage.</usage>
  <parametres>X1..X4, jeux pré-calibrés issus de la littérature publique (INRAE) — **aucun code ni paramètre propriétaire réutilisé**.</parametres>
  <enregistrement>Déclaré dans DataHub comme `MLModel` avec `bassin_calibration`, `periode_calibration`, `NSE`, `version`.</enregistrement>
  <point_critique>C'est ce champ `bassin_calibration` que l'agent Conseiller contrôle avant toute recommandation. Un modèle calibré sur un autre bassin ⇒ confiance dégradée. **C'est la démonstration la plus parlante du projet.**</point_critique>
</modele>

<modele id="M3" nom="LLM d'orchestration" type="génératif">
  <choix>Claude (Sonnet) via API, ou tout modèle compatible — configurable par variable d'environnement.</choix>
  <role>Compréhension de la question, planification des appels MCP, rédaction de la réponse et du rapport d'impact.</role>
  <interdiction_stricte>Le LLM **ne calcule aucun chiffre**. Tous les nombres proviennent de M1/M2 exécutés en Python. Le LLM ne fait que router, contrôler et rédiger. Cette séparation est explicitée dans le README — c'est un argument de crédibilité fort.</interdiction_stricte>
</modele>

</modeles>

---

<architecture_agents>

<principe_directeur>
**Aucun agent ne contient de chemin de données en dur.** Chaque agent découvre ce qu'il doit utiliser en interrogeant DataHub. On peut ajouter une source ou changer de modèle en modifiant uniquement le graphe.
</principe_directeur>

<agent id="A1" nom="Cartographe" challenge="Metadata-Aware Code Generation">
  <mission>Construire et maintenir le graphe de contexte ; générer le code d'ingestion d'un nouveau territoire.</mission>
  <entrees>Snapshots de données, schémas observés</entrees>
  <outils_datahub>SDK Python (émission d'entités et de lineage), `search`, `list_schema_fields`, `update_description`, `add_glossary_terms`, `set_domains`, `add_owners`</outils_datahub>
  <sorties>Graphe peuplé + O3 (recettes YAML, SQL, DAG)</sorties>
  <mode>batch, exécuté au setup puis à la demande</mode>
</agent>

<agent id="A2" nom="Conseiller" challenge="Agents That Do Real Work">
  <mission>Répondre à P1 avec des scénarios chiffrés et une provenance vérifiée.</mission>
  <boucle_imposee>
    1. Interpréter la question (parcelle, horizon, cultures candidates)
    2. `search` → identifier les datasets et le modèle pertinents **dans le graphe**
    3. `get_entities` + `list_schema_fields` → lire schémas, descriptions, custom properties
    4. `get_lineage` (amont) → reconstituer la chaîne complète
    5. **PORTE DE CONFIANCE** (cf. garde_fous) → haute / dégradée / insuffisante
    6. Si ≥ dégradée : dérouler le **calendrier cultural complet** de chaque candidate (semis → levée → stade critique → maturité → récolte), exécuter M1 et M2, calculer le recouvrement
    7. **Chercher les leviers correctifs** pour chaque culture à risque : décalage de semis, variété plus précoce, volume d'irrigation à sécuriser, densité. Ne retenir que ceux qui réduisent réellement le recouvrement, avec leur effet chiffré
    8. Produire O1, puis écrire le run dans le graphe (`DataProcessInstance` + `save_document`)
  </boucle_imposee>
  <interdiction>Ne jamais court-circuiter les étapes 2 à 5, même si la réponse semble évidente.</interdiction>
</agent>

<agent id="A3" nom="Sentinelle" challenge="Production ML Agents">
  <mission>Protéger la chaîne en production : détecter les dégradations amont et invalider l'aval.</mission>
  <declencheurs>
    - fraîcheur : `now − last_updated > freshness_sla_days`
    - dérive de schéma : colonne renommée/supprimée vs schéma catalogué
    - incohérence de calibration : `bassin_calibration ≠ bassin de la parcelle`
    - signal métier : assec ONDE déclaré sur le sous-bassin
  </declencheurs>
  <sequence>
    1. Détecter sur l'asset amont
    2. `get_lineage` **descendant** → périmètre d'impact complet
    3. Croiser avec les runs passés → recommandations invalidées + exposition financière
    4. **Écrire dans le graphe** : `add_tags("recommandation-a-risque")`, `update_description`, `save_document` du rapport O2
    5. Rejouer les recommandations impactées et notifier
  </sequence>
  <valeur_differenciante>Ceci est structurellement impossible sans graphe de lineage. C'est l'argument central de la soumission.</valeur_differenciante>
</agent>

<travail_en_equipe>
A1 alimente le graphe → A2 le consomme → A2 et A3 y réécrivent → A1 exploite ces écritures pour améliorer la documentation. Boucle fermée : **le contexte s'enrichit parce que les agents l'utilisent**.
</travail_en_equipe>

</architecture_agents>

---

<graphe_datahub>

<platform>`urn:li:dataPlatform:duckdb` pour les datasets, plateforme custom `terroir` pour les entités dérivées.</platform>

<entites>
| Type DataHub | Instances |
|---|---|
| `Dataset` | `hubeau_hydrometrie`, `hubeau_piezometrie`, `hubeau_onde`, `drias_climat`, `rpg_parcelles`, `ref_agro_economique`, `features_bilan_hydrique`, `scenarios_cultures`, `recommandations_parcelle` |
| `DataFlow` / `DataJob` | `build_features`, `run_scenarios`, `score_recommandations` |
| `MLModel` | `gr4j_cher_v1` (+ `MLModelGroup` `gr4j_bassins`) |
| `MLFeatureTable` / `MLFeature` | `bilan_hydrique_features` : `etm_cumul`, `deficit_cumul`, `jours_stress`, `debit_etiage_qmna5` |
| `DataProcessInstance` | un par exécution de scénario — **c'est ce qui rend chaque recommandation rejouable et traçable** |
| `GlossaryTerm` | ETP, ETM, coefficient cultural, réserve utile, pluie efficace, marge brute, redevance prélèvement, QMNA5, assec |
| `Domain` | `Agriculture & Ressource en eau` |
| `Tag` | `source-mesuree`, `source-modelisee`, `dire-d-expert`, `recommandation-a-risque`, `calibration-hors-bassin`, `donnee-perimee` |
| `Document` | rapports d'impact, notes de méthode, fiches de run |
</entites>

<lineage_cible>
```
hubeau_hydrometrie ─┐
hubeau_piezometrie ─┤
hubeau_onde        ─┼→ [build_features] → features_bilan_hydrique ─┐
drias_climat       ─┤                                              │
rpg_parcelles      ─┘                                              ├→ [run_scenarios] → scenarios_cultures
                                        gr4j_cher_v1 (MLModel) ────┘                            │
                                        ref_agro_economique ────────────────────────────────────┤
                                                                                                ▼
                                                                                 recommandations_parcelle
                                                                                                │
                                                                                    DataProcessInstance (× n runs)
```
</lineage_cible>

<outils_mcp_utilises>
Lecture : `search`, `get_entities`, `get_lineage`, `list_schema_fields`, `get_dataset_queries`, `search_documents`, `grep_documents`
Écriture : `add_tags`, `remove_tags`, `update_description`, `add_glossary_terms`, `set_domains`, `add_owners`, `save_document`
Hors MCP (SDK Python) : création des entités, du lineage et des `DataProcessInstance`.
</outils_mcp_utilises>

<datahub_skills>
Skills consommées : `datahub-setup`, plus les skills de recherche/lineage/curation du registre officiel.
Skill contribuée (cf. contribution_open_source) : `environmental-data-provenance`.
</datahub_skills>

</graphe_datahub>

---

<garde_fous>

<porte_de_confiance>
Évaluée avant **toute** production de chiffre :

| Niveau | Conditions | Comportement |
|---|---|---|
| **haute** | toutes sources dans leur SLA de fraîcheur, schémas conformes, modèle calibré sur le bassin de la parcelle, aucun tag de risque en amont | scénarios complets, langage assertif |
| **dégradée** | 1 source hors SLA **ou** modèle calibré sur bassin voisin **ou** source `dire-d-expert` critique | scénarios produits, **bandeau d'avertissement obligatoire**, motifs listés |
| **insuffisante** | source critique absente/hors SLA > 2× le seuil **ou** dérive de schéma non résolue **ou** lineage rompu | **aucun chiffre produit**, explication de ce qui manque et de qui contacter (owner récupéré via DataHub) |
</porte_de_confiance>

<regles>
- R1 — Aucun nombre affiché sans URN de provenance associée.
- R2 — Le LLM ne produit jamais de valeur numérique (cf. M3).
- R3 — Toute recommandation crée un `DataProcessInstance` avant d'être rendue à l'utilisateur.
- R4 — Toute écriture dans le graphe est journalisée localement et rejouable.
- R5 — En mode mock, l'UI affiche un bandeau permanent « données figées — démonstration ».
</regles>

</garde_fous>

---

<restrictions>

<techniques>
- DataHub **OSS**, pas Cloud : les assertions natives, les usage stats et le Context Intelligence ne sont pas disponibles. Elles sont **remplacées par des custom properties et des tags** gérés par les agents — c'est assumé et expliqué dans le README, pas caché.
- **Mode générique** : aucun prérequis au-delà de la Quickstart. `datahub datapack load nyc-taxi` puis `make demo-generic`. Les anomalies de fraîcheur plantées servent de déclencheur à la Sentinelle ; `showcase-ecommerce` sert à démontrer la profondeur du lineage cross-plateforme.
- **Mode agriculture** : snapshot synthétique embarqué, `docker compose up` + `make demo`, **sans aucune clé API**. Contrainte non négociable pour l'évaluation par le jury.
- DRIAS ne fournit pas d'API REST ; les prévisions saisonnières C3S demandent une inscription. Ces sources sont donc **fetchées à la demande, jamais embarquées**.
</techniques>

<juridiques_et_ethiques>
- **Aucune donnée sous licence contrainte n'est commitée dans le repo.** Les jeux officiels du hackathon et le snapshot synthétique sont les seuls contenus versionnés ; `fetch_real.py` récupère le reste chez la source, avec ses conditions.
- `data/SOURCES.md` documente, pour chaque source : origine, licence, redistribuable ou non, et la mention explicite « synthétique » là où c'est le cas.
- Le RPG est anonymisé et n'est pas embarqué : **aucune donnée personnelle d'exploitant** n'est traitée. Les parcelles de démonstration sont fictives.
- Licence de sortie : **Apache 2.0**, fichier `LICENSE` à la racine, visible dans la section About du dépôt GitHub. *Exigence explicite du règlement — vérifier dès J1, pas la veille.*
- **Aucun code, donnée ou paramètre non publiable issu d'un contexte professionnel antérieur.** Tout est reconstruit à partir de sources publiques citées.
</juridiques_et_ethiques>

<perimetre_de_responsabilite>
Avertissement affiché dans l'UI et le README : outil de démonstration technique, **ne constitue pas un conseil agronomique ou d'investissement**. Les paramètres économiques sont indicatifs et datés.
</perimetre_de_responsabilite>

</restrictions>

---

<interface_utilisateur>

<techno>Streamlit, page unique, CSS injecté. Polices auto-hébergées dans le repo — la démo doit s'afficher correctement **hors ligne**, sans CDN.</techno>

<intention_de_design>
Un instrument de mesure, pas un tableau de bord. L'écran doit se lire comme une fiche de station hydrométrique : peu d'éléments, beaucoup de blanc, une hiérarchie évidente, aucun ornement. La sobriété n'est pas une contrainte esthétique ici — c'est la traduction visuelle de la thèse du projet : **ce qui est affiché est mesuré, daté et traçable.**
</intention_de_design>

<regle_fondatrice>
**La couleur ne décore jamais. Elle ne signale que la confiance.**
Toute l'interface est en encre sur papier. Les seuls éléments colorés sont l'épine de provenance (bleu) et les états de confiance (vert / ambre / rouge). Conséquence : quand une pastille ambre apparaît, l'œil la trouve instantanément parce que rien d'autre ne réclame l'attention. C'est ce qui rend la démonstration de la Sentinelle lisible en vidéo.
</regle_fondatrice>

<palette>
| Rôle | Nom | Hex | Usage |
|---|---|---|---|
| Fond | `--papier` | `#F7F6F3` | fond général, blanc calcaire légèrement froid |
| Texte | `--encre` | `#1B2430` | tout le texte, bleu-noir |
| Filets | `--craie` | `#E2E0DA` | séparateurs, bordures, grilles — 1 px, jamais plus |
| Accent unique | `--eau` | `#2E6F8E` | épine de provenance, liens vers DataHub |
| État confiance haute | `--sur` | `#3F7A5A` | pastille + libellé |
| État confiance dégradée | `--vigilance` | `#C08A2E` | pastille + libellé + bandeau |
| État confiance insuffisante | `--rupture` | `#A63D2F` | pastille + libellé + rupture d'épine |

Aucune autre couleur. Pas de dégradés. Pas d'ombres portées. Rayon de bordure : 2 px maximum.
</palette>

<typographie>
Une seule superfamille open source, auto-hébergée : **IBM Plex**.

| Rôle | Fonte | Usage |
|---|---|---|
| Titre | IBM Plex Serif, 600 | le titre de l'écran et le nom de la culture recommandée — c'est tout |
| Corps | IBM Plex Sans, 400/500 | libellés, phrases, explications |
| Chiffres | IBM Plex Mono, 400/500 | **tous les nombres, dates, unités et URN, sans exception** |

<regle>Tout ce qui est mesuré est en chasse fixe ; tout ce qui est écrit est en chasse proportionnelle. Cette règle est visible au premier coup d'œil et rappelle en permanence ce qui vient d'une donnée et ce qui vient d'une phrase.</regle>

Échelle : 13 / 15 / 18 / 24 / 40 px. Interlignage corps 1,55. Les libellés de section sont en Plex Sans 12 px, majuscules, interlettrage +0,08em.
</typographie>

<element_signature>
**L'épine de provenance** — une bande verticale fine, à droite de l'écran, toujours visible.

Elle représente la chaîne de données comme une carotte de sondage : un segment par maillon, du bas (les stations de mesure) vers le haut (la recommandation). Chaque segment porte son nom, sa date de dernière donnée en chasse fixe, et une pastille d'état.

```
  ┌─┐
  │▓│  RECOMMANDATION        30/07/2026
  │▓│
  │▓│  scenarios_cultures    30/07/2026
  │▓│
  │▓│  gr4j_cher_v1     ●    bassin : Cher amont
  │▓│
  │▓│  features_bilan   ●    29/07/2026
  │▓│
  │▓│  drias_climat     ●    RCP 8.5 — 2024
  │▓│
  │▓│  hubeau_hydro     ●    29/07/2026
  └─┘
```

Quand la Sentinelle se déclenche, le segment fautif vire au rouge et **la rupture remonte l'épine segment par segment** jusqu'à la recommandation, qui bascule en état barré. Un seul mouvement, 600 ms, échelonné.

C'est le seul élément mémorable de l'interface, et c'est aussi le plan 4 de la vidéo. Tout le reste doit rester silencieux autour.
</element_signature>

<mise_en_page>
Une seule question, une seule image, une seule épreuve. Pas d'onglets, pas de menu, pas de barre latérale.

```
┌────────────────────────────────────────────────────────┬──────┐
│  Terroir Context Agents                    mode démo   │      │
├────────────────────────────────────────────────────────┤ PRO  │
│  Parcelle [Vierzon-142 ▾]   Semis [15 avril ▾]         │ VEN  │
│  sol limono-argileux — réserve utile 140 mm            │ ANC  │
│  Horizon  [3 mois] (6 mois) [12 mois]                  │ E    │
├────────────────────────────────────────────────────────┤      │
│           mars avr  mai  juin juil août sept oct       │      │
│  Eau       ░░   ░░   ░░   ▒▒   ██   ██   ▒▒   ░░       │      │
│                                                        │      │
│  Tournesol      ├───────●●●●●───────┤          +340 ✓  │      │
│                 20/04   floraison  05/09               │      │
│  Orge      ├────●●●●●───┤                      +295 ✓  │      │
│            15/03        22/06                          │      │
│  Maïs           ├──────────●●●●●●●────────┤     −64 ✗  │      │
│                 15/04     floraison      10/10         │      │
│                                                        │      │
│  Le maïs fleurit en pleine tension — 34 j de           │      │
│  recouvrement. Vous voulez le garder ?                 │      │
│                                                        │      │
│  ┌──────────────────────────────────────────────────┐  │      │
│  │ Avancer le semis au 25 mars      34 j → 6 j      │  │      │
│  │ récolte le 18/09                     +180 €/ha   │  │      │
│  ├──────────────────────────────────────────────────┤  │      │
│  │ Variété précoce, indice 280      34 j → 11 j     │  │      │
│  │ récolte le 12/09                     +120 €/ha   │  │      │
│  ├──────────────────────────────────────────────────┤  │      │
│  │ Sécuriser 1 400 m³               34 j → 0 j      │  │      │
│  │ sous autorisation de prélèvement      +90 €/ha   │  │      │
│  └──────────────────────────────────────────────────┘  │      │
├────────────────────────────────────────────────────────┤      │
│  [ Simuler une panne de station ]                      │      │
└────────────────────────────────────────────────────────┴──────┘
```

<justification>
La décision de l'agriculteur n'est pas « quelle culture rapporte le plus » — c'est **« est-ce que ma culture va avoir soif au moment où il n'y aura plus d'eau »**. Cette question est un problème de recouvrement entre deux fenêtres temporelles. Superposer les deux fenêtres sur un même axe de mois la résout visuellement : là où le stade critique d'une culture tombe sous une case sombre, il y a perte. L'alignement fait tout le travail ; aucun calcul mental n'est demandé.

Chaque culture est représentée par **la barre de son cycle complet**, du semis à la récolte estimée, avec les deux dates écrites en clair et le stade critique marqué à l'intérieur. La longueur de la barre est une information à part entière : l'orge quitte la scène avant que la tension ne s'installe, et cela se voit sans qu'un mot soit nécessaire.
</justification>
</mise_en_page>

<graphiques>

<principe>
**Un seul graphique dans toute l'application.** Le calendrier de recouvrement. Tout le reste est du texte et deux nombres. Un deuxième graphique obligerait à choisir lequel regarder en premier.
</principe>

<graphique id="G1" nom="Calendrier de recouvrement" type="alignement temporel" statut="unique">
  <axe_x>Les mois du cycle cultural, à partir de la date de semis saisie. **Changer la date de semis décale les courbes de culture sous la bande d'eau** — c'est la manipulation la plus instructive de l'application, et elle est gratuite.</axe_x>

  <bande_eau>
    Première ligne, détachée des autres. Une case par mois, dont l'intensité encode la tension prévue sur la ressource : étiage attendu, anomalie de température, probabilité de restriction d'usage.
    Cases neutres tant que la tension est faible, `--vigilance` puis `--rupture` quand elle s'installe. C'est le seul endroit où la couleur apparaît par défaut, parce que c'est bien un état.
  </bande_eau>

  <lignes_culture>
    Une ligne par culture proposée, alignée colonne par colonne sur la bande d'eau. La hauteur de barre encode le besoin en eau du stade en cours. Les barres sont en encre ; **une barre ne prend la couleur `--rupture` que lorsqu'elle est haute ET située sous une case de tension forte.** La règle de couleur du projet tient : elle ne signale qu'un état de risque.
    Les mois hors cycle (culture récoltée, ou pas encore semée) sont vides — pas une barre à zéro, rien du tout. Le vide dit « cette culture a déjà quitté la scène », et c'est exactement l'argument commercial de l'orge de printemps.
  </lignes_culture>

  <verdict>
    En bout de ligne, la marge brute en €/ha et une pastille d'état. Deux caractères, pas une phrase.
    Sous le graphique, **une seule phrase** explique le classement, toujours construite sur le recouvrement : « Le maïs atteint son pic de besoin en pleine tension. 34 jours de recouvrement. »
  </verdict>

  <horizon>
    Le sélecteur 3 / 6 / 12 mois ne change pas la forme du graphique : il change **la netteté de la bande d'eau**. À 3 mois, les cases sont franches. À 6 mois, elles s'atténuent. À 12 mois, elles deviennent hachurées et la mention « tendance climatologique, pas une prévision » remplace les probabilités.
    L'incertitude n'est pas écrite dans une note de bas de page : elle est visible dans le graphique.
  </horizon>
</graphique>

<role_du_sol>
Le type de sol et la réserve utile s'affichent en une ligne sous le sélecteur de parcelle, jamais dans un graphique. Leur effet est visible ailleurs : c'est ce qui explique qu'une culture absente de la parcelle apparaisse dans les propositions. Une culture recommandée pour cette raison porte la mention **« proposée pour votre sol »** — c'est le moment où le système apporte quelque chose que l'agriculteur ne savait pas.
</role_du_sol>

<interdits>
- Pas de camembert, pas de jauge, pas de carte de chaleur multicolore.
- Pas de deuxième graphique, même « en repliable ».
- Pas d'axe Y gradué : les hauteurs se comparent entre elles, pas dans l'absolu.
- Pas de couleur catégorielle. Les cultures ne sont pas des couleurs, ce sont des lignes libellées.
- Pas d'animation d'apparition. Le seul mouvement de l'application reste la propagation de la rupture sur l'épine.
</interdits>

<accessibilite>
« Voir les chiffres » déplie un tableau équivalent : par culture, fenêtre critique, jours de recouvrement, besoin en mm, coût, marge. Replié par défaut, atteignable au clavier, lu par les lecteurs d'écran. Chaque pastille d'état est doublée d'un mot écrit.
</accessibilite>

<implementation>
SVG généré côté Python à partir du contrat `O1`, sans bibliothèque graphique ni CDN. Une grille de mois, une bande, trois séries de barres : le tracé manuel est plus court qu'une configuration de bibliothèque, et il reste net en vidéo comme à l'impression.
</implementation>

</graphiques>

<leviers_correctifs>

<principe>
Un agriculteur ne change pas de culture sur simple conseil : la rotation, le matériel, les contrats de vente et l'assolement voisin contraignent son choix. Un système qui se contente de dire « ne semez pas de maïs » sera ignoré. **La valeur est de dire comment garder la culture voulue sans la perdre.**
</principe>

<leviers_testes>
| Levier | Ce qu'il déplace | Faisabilité |
|---|---|---|
| Décaler la date de semis | Toute la barre du cycle, donc le stade critique | immédiate |
| Variété plus précoce | La durée du cycle, donc la date de récolte | immédiate — à commander |
| Sécuriser un volume d'irrigation | Ne déplace rien, comble le déficit | sous autorisation de prélèvement |
| Réduire la densité de semis | Le besoin en eau au pic | immédiate |
| Changer de culture | Tout | dernier recours, contraint par la rotation |
</leviers_testes>

<presentation>
Le bloc n'apparaît **que si une culture est à risque**, et seulement pour celle-là. Trois leviers maximum, classés par gain. Chaque levier tient en deux lignes :
- ligne 1 : l'action en langage d'agriculteur + l'effet sur le recouvrement (`34 j → 6 j`)
- ligne 2 : la nouvelle date de récolte ou la réserve applicable + le gain en €/ha

Aucun levier n'est affiché s'il n'améliore pas réellement le résultat. Un levier sous condition administrative porte sa réserve écrite, jamais masquée.
</presentation>

<phrase_de_bascule>
Le bloc est introduit par une question, pas par un avertissement : « Le maïs fleurit en pleine tension — 34 j de recouvrement. Vous voulez le garder ? » Le système propose, l'agriculteur décide. C'est aussi ce qui évite le ton prescriptif qui ferait fuir l'utilisateur réel.
</phrase_de_bascule>

<interaction>
Cliquer un levier **rejoue le calendrier avec ce levier appliqué** : les barres se repositionnent, le recouvrement se recalcule, un nouveau `DataProcessInstance` est écrit dans le graphe. Le levier n'est donc pas un texte de conseil, c'est une simulation traçable au même titre que la recommandation initiale.
</interaction>

<incertitude_de_recolte>
La date de récolte est une estimation, jamais un engagement. Elle porte son incertitude (`incertitude_recolte_j` du contrat O1) et s'affiche sous la forme « vers le 18/09 ». À l'horizon 12 mois, seule la fourchette est donnée, sans date centrale.
</incertitude_de_recolte>

</leviers_correctifs>

<regles_de_simplicite>
- **Une décision par bande.** Où ? Quand ? Puis la réponse. Puis l'épreuve.
- **Trois clics maximum** entre l'arrivée sur la page et une recommandation chiffrée.
- **Divulgation progressive** : le détail du calcul (bilan hydrique jour par jour, paramètres du modèle) est replié derrière « Voir le détail ». La page d'accueil ne montre jamais plus de 12 nombres.
- **Séparation des vocabulaires** : la zone centrale parle à l'agriculteur (aucun jargon, aucun URN) ; l'épine parle à l'ingénieur données. Elles ne se mélangent jamais. Il n'y a pas de « mode expert » — les deux publics lisent le même écran, chacun sa colonne.
- **Chiffres** : trois chiffres significatifs maximum, unité toujours accolée, séparateur de milliers en espace fine.
- **Aucune icône décorative.** Les seules icônes autorisées sont les pastilles d'état et la flèche de lien.
- **Responsive** : sous 900 px, l'épine passe sous les cartes sans changer d'ordre de lecture.
</regles_de_simplicite>

<redaction_interface>
Voix active, phrases courtes, casse de phrase. Le bouton dit ce qui va se passer.

| Situation | Texte |
|---|---|
| Bouton principal | `Comparer les cultures` |
| Écran vide | `Choisissez une parcelle pour commencer.` |
| Confiance dégradée (bandeau ambre) | `Chiffres indicatifs. Le modèle est calibré sur le bassin du Cher amont, votre parcelle est sur le Fouzon.` |
| Confiance insuffisante (aucun chiffre) | `Impossible de chiffrer. La station K4470010 n'a pas transmis depuis 12 jours, au-delà du seuil de 5 jours. Contacter l'owner du jeu de données : hydro-team.` |
| Après la panne simulée | `3 recommandations invalidées. Rapport d'impact enregistré dans DataHub.` |
| Lien vers le catalogue | `Ouvrir dans DataHub →` |

<principe>Un message d'erreur ne s'excuse pas et ne reste jamais vague : il dit ce qui s'est passé, depuis quand, et qui contacter. Le nom de l'owner vient de DataHub — c'est une démonstration de plus, glissée dans la copie.</principe>
</redaction_interface>

<mouvement>
Un seul moment orchestré dans toute l'application : la propagation de la rupture le long de l'épine. Rien d'autre ne bouge — pas de compteurs animés, pas d'apparitions au défilement, pas de transitions de survol au-delà d'un changement de fond de 1 %.
`prefers-reduced-motion: reduce` remplace la propagation par un basculement d'état instantané.
</mouvement>

<qualite_minimale>
- Contraste AA sur tous les textes.
- **Aucun état signalé par la couleur seule** : chaque pastille est doublée d'un libellé écrit.
- Focus clavier visible sur tous les contrôles.
- Toute la démonstration est atteignable au clavier seul.
</qualite_minimale>

<note_video>
Le bouton de la bande 3 est le moment fort de la vidéo. Il doit s'exécuter de façon fiable en moins de 15 secondes, et l'épine doit rester entièrement visible à l'écran pendant la propagation — cadrer le plan 4 sur l'épine, pas sur les cartes.
</note_video>

</interface_utilisateur>

---

<plan_execution>

| Jour | Étape | Critère de sortie |
|---|---|---|
| **J1** (30-31/07) | Socle : `datahub docker quickstart`, PAT, MCP branché, `pip install datahub-agent-context`, repo créé **avec LICENSE Apache 2.0 visible**, `brief.md` commité, **Slack `#agent-hackathon` rejoint**, `datapack load nyc-taxi` + `showcase-ecommerce` | Une requête MCP répond, et le graphe officiel est chargé |
| **J2** (01/08) | **Sentinelle v0 sur les données du jury** : détecter les anomalies de fraîcheur plantées de `nyc-taxi`, remonter le lineage descendant, poser un tag. **Ouvrir la PR du connecteur HubEau.** Poster le concept en 3 lignes sur Slack | Un tag écrit dans DataHub à partir d'une anomalie plantée |
| **J3–J4** (02-03/08) | **A1 Cartographe** : `catalog/build_graph.py`, snapshot agricole synthétique, entités, lineage complet, glossaire FR, custom properties | Depuis `recommandations_parcelle`, on remonte jusqu'aux sources dans l'UI |
| **J5–J6** (04-05/08) | **A2 Conseiller** : boucle imposée, porte de confiance, degrés-jours + bilan hydrique, calendrier, recouvrement, contrat O1 | Réponse chiffrée + provenance ; refus propre quand une source est coupée |
| **J7** (06/08) | **A3 Sentinelle complète** sur les deux modes + leviers correctifs. Poster un GIF de la détection sur Slack | Panne simulée → tags + rapport d'impact dans DataHub, dans les deux modes |
| **J8** (07/08) | Artefacts générés O3 + `make demo-generic` propre | 3 fichiers réalistes dans `examples/`, mode générique en 2 min |
| **J9** (08/08) | UI Streamlit + `docker compose` + `data/SOURCES.md` | Un tiers clone et lance en < 5 min |
| **J10** (09/08) | README, description Devpost, vidéo, PR skill + docs | Vidéo < 3 min publiée en public, PR ouvertes et liées |
| **J11** (10/08) | Tampon + soumission **avant 23h00 GMT+2** | Soumis |

<repli>
Ordre de coupe si retard : projections 2050 → carte interactive → 3ᵉ culture → GR4J (remplacé par un seuil d'étiage simple).
**Jamais coupés** : le lineage bout en bout, la porte de confiance, la Sentinelle. C'est là qu'est la note.
</repli>

</plan_execution>

---

<contribution_open_source>

<pr id="C1" cible="repo datahub-skills" effort="faible" impact="fort">
  Skill **`environmental-data-provenance`** : workflow réutilisable « avant de produire une recommandation à partir de données environnementales, vérifie fraîcheur, périmètre spatial, niveau de preuve et cohérence de calibration ». Généralisable au-delà de l'agriculture.
</pr>

<pr id="C2" cible="repo datahub" effort="moyen" impact="très fort">
  **Connecteur d'ingestion HubEau** — première source de données environnementales publiques françaises dans DataHub. Le règlement cite explicitement les nouveaux connecteurs comme contribution valorisée, et aucun connecteur de ce type n'existe.
</pr>

<pr id="C3" cible="docs" effort="très faible" impact="moyen">
  Amélioration de la documentation Agent Context Kit à partir des frictions réellement rencontrées pendant le hackathon (à noter au fil de l'eau dans `NOTES.md`).
</pr>

<note>C2 est le meilleur rapport effort/points de toute la soumission. Le lancer dès J2 en parallèle du reste.</note>

</contribution_open_source>

---

<alignement_jury>

| Critère | Comment le projet y répond | Preuve dans la soumission |
|---|---|---|
| **Use of DataHub** | Le graphe est le runtime : découverte, contrôle, impact, capitalisation. Lecture **et** écriture. `MLModel`, `MLFeatureTable`, `DataProcessInstance`, glossaire, lineage bout en bout — **sur le graphe officiel du hackathon comme sur le nôtre**. | Plan 1 et 2 de la vidéo + section README « Débranchez DataHub, tout s'arrête » |
| **Technical Execution** | Deux commandes, deux modes, aucune clé API. Contrats JSON stricts, LLM séparé du calcul. | `make demo-generic` en 2 min sur `nyc-taxi` |
| **Originality** | Ne réimplémente rien de DataHub : **compose** lineage + ML metadata + glossaire pour un usage nouveau — l'invalidation rétroactive de décisions métier déjà prises. | Section README « Ce que nous n'avons pas reconstruit » |
| **Real-World Usefulness** | Le même code décide sur des courses de taxi et sur un assolement : la thèse « le domaine est l'instanciation » est **prouvée, pas affirmée**. | Le double mode, démontré en vidéo |
| **Submission Quality** | Première ligne du README = une commande copiable qui marche. Vidéo scénarisée, `examples/` d'artefacts générés, `SOURCES.md` transparent sur les licences. | — |
| **Bonus OSS** | 3 PR : connecteur HubEau sur `datahub-project/datahub`, skill sur `datahub-project/datahub-skills`, docs. Ouvertes dès le J2. | Liens des PR dans la description Devpost |
| **Couverture des challenges** | 3 challenges sur 4 couverts par A1, A2, A3. | Section README « Challenges couverts » |

</alignement_jury>

---

<script_video>

Durée cible : 2 min 45. **Le plan 1 se déroule sur les données du jury, pas sur les nôtres** — un juge reconnaît son propre jeu de test dans les vingt premières secondes.

| Plan | Durée | Contenu |
|---|---|---|
| 1 | 0:00–0:25 | `datahub datapack load nyc-taxi` puis `make demo-generic`. La Sentinelle trouve l'anomalie de fraîcheur plantée, remonte le lineage, pose son tag. Aucune configuration. |
| 2 | 0:25–0:50 | Même code, autre graphe : le lineage agricole, du semis à la station de mesure. Glossaire FR, MLModel avec son bassin de calibration. |
| 3 | 0:50–1:40 | Le Conseiller répond : calendrier de recouvrement, cultures classées, leviers correctifs cliquables. Puis le refus propre quand une source critique est coupée. |
| 4 | 1:40–2:20 | Bouton « panne » : la rupture remonte l'épine de provenance, la Sentinelle chiffre l'exposition et rejoue les recommandations invalidées. |
| 5 | 2:20–2:45 | Pourquoi c'est impossible sans DataHub, la transposition à d'autres domaines, et les PR contribuées. |

</script_video>

---

<criteres_acceptation>

- [ ] `datahub datapack load nyc-taxi && make demo-generic` fonctionne sur une machine vierge, en moins de 2 minutes
- [ ] `git clone && docker compose up && make demo` fonctionne sans aucune clé API
- [ ] `LICENSE` Apache 2.0 visible dans le About GitHub
- [ ] `data/SOURCES.md` documente origine, licence et caractère synthétique de chaque donnée embarquée
- [ ] Aucune donnée sous licence contrainte n'est commitée
- [ ] Le lineage est navigable de bout en bout dans les deux modes
- [ ] Le Conseiller **refuse** proprement quand une source critique est coupée
- [ ] La Sentinelle **écrit** effectivement tags, descriptions et document dans DataHub, dans les deux modes
- [ ] `examples/` contient au moins 5 artefacts (recommandation, rapport d'impact, recette YAML, SQL, DAG)
- [ ] Vidéo < 3 min, publique, sous-titrée, ouvrant sur le jeu de données officiel
- [ ] Les 3 PR open source sont ouvertes, discutées et liées dans la description
- [ ] Soumission enregistrée avant le 10/08/2026 23h00 GMT+2

</criteres_acceptation>
