#!/usr/bin/env python3
"""
catalog/build_graph.py — Construit le graphe de contexte Terroir dans DataHub.

Ce script est le socle du projet : il declare les sources, le lineage bout en bout,
le glossaire metier, les modeles ML et les proprietes de confiance que les agents
Conseiller et Sentinelle liront ensuite. Aucun agent ne contient de chemin de donnees
en dur ; tout se decouvre ici.

Usage:
    python catalog/build_graph.py --dry-run out.json
    python catalog/build_graph.py --server http://localhost:8080 --token $DATAHUB_TOKEN

Licence: Apache-2.0
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from typing import Iterable, List, Optional

import datahub.metadata.schema_classes as models
from datahub.emitter.mce_builder import (
    make_data_flow_urn,
    make_data_job_urn,
    make_dataset_urn,
    make_domain_urn,
    make_ml_feature_table_urn,
    make_ml_feature_urn,
    make_ml_model_group_urn,
    make_ml_model_urn,
    make_tag_urn,
    make_term_urn,
    make_user_urn,
)
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.emitter.rest_emitter import DatahubRestEmitter

PLATFORM = "duckdb"
ENV = "PROD"
FLOW_ID = "terroir_pipeline"
ORCHESTRATOR = "airflow"
DOMAIN_NAME = "Agriculture & Ressource en eau"
DOMAIN_URN = make_domain_urn("agriculture-ressource-en-eau")

NOW_MS = int(time.time() * 1000)
AUDIT = models.AuditStampClass(time=NOW_MS, actor=make_user_urn("terroir-cartographe"))


# --------------------------------------------------------------------------------------
# Vocabulaire du projet
# --------------------------------------------------------------------------------------

GLOSSARY = {
    "etp": ("ETP", "Evapotranspiration potentielle : lame d'eau qu'un couvert de reference "
                   "consommerait si l'eau n'etait pas limitante. Exprimee en mm/jour."),
    "etm": ("ETM", "Evapotranspiration maximale de la culture : ETP ponderee par le "
                   "coefficient cultural du stade en cours."),
    "coefficient-cultural": ("Coefficient cultural (Kc)",
                             "Facteur FAO-56 qui traduit l'ETP de reference en besoin reel "
                             "de la culture, variable selon le stade."),
    "reserve-utile": ("Reserve utile (RU)",
                      "Quantite d'eau du sol reellement mobilisable par la plante, en mm. "
                      "Determine l'autonomie de la parcelle sans irrigation."),
    "pluie-efficace": ("Pluie efficace",
                       "Fraction des precipitations effectivement stockee dans la reserve "
                       "du sol, apres ruissellement et drainage."),
    "degres-jours": ("Degres-jours",
                     "Cumul thermique au-dessus d'une temperature de base. Date l'atteinte "
                     "des stades phenologiques : c'est ce qui relie la prevision de "
                     "temperature au calendrier de la culture."),
    "stade-critique": ("Stade critique",
                       "Periode du cycle ou un deficit hydrique degrade irreversiblement le "
                       "rendement. Floraison pour le mais, remplissage pour les cereales."),
    "recouvrement": ("Recouvrement",
                     "Nombre de jours pendant lesquels le stade critique d'une culture "
                     "tombe dans la fenetre de tension prevue sur la ressource en eau. "
                     "Variable de decision du produit."),
    "marge-brute": ("Marge brute",
                    "Produit brut moins charges operationnelles et cout de l'eau, en EUR/ha."),
    "redevance-prelevement": ("Redevance prelevement",
                              "Contribution due a l'agence de l'eau par volume preleve, "
                              "composante du cout d'irrigation."),
    "qmna5": ("QMNA5", "Debit mensuel minimal de frequence quinquennale : reference "
                       "reglementaire d'etiage utilisee pour anticiper les restrictions."),
}

TAGS = {
    "source-mesuree": "Donnee issue d'une mesure instrumentale.",
    "source-modelisee": "Donnee issue d'un modele ou d'une reanalyse.",
    "source-synthetique": "Donnee generee pour la demonstration, non redistribuee depuis un tiers.",
    "dire-d-expert": "Valeur de reference issue de la litterature ou d'un bareme, non mesuree.",
    "recommandation-a-risque": "Livrable aval dont une source amont s'est degradee.",
    "calibration-hors-bassin": "Modele applique en dehors de son perimetre de calibration.",
    "donnee-perimee": "Fraicheur au-dela du SLA declare.",
}


@dataclass
class Source:
    """Une source du graphe, avec ses proprietes de confiance."""

    name: str
    description: str
    fields: List[tuple]  # (nom, type, doc)
    niveau_de_preuve: str  # mesure | modelisation | dire_d_expert
    freshness_sla_days: int
    last_updated: str
    licence: str
    redistribuable: str
    spatial_coverage: str = "Nouvel Espace Cher"
    tags: List[str] = field(default_factory=list)
    terms: List[str] = field(default_factory=list)
    owner: str = "terroir-data-team"

    @property
    def urn(self) -> str:
        return make_dataset_urn(platform=PLATFORM, name=self.name, env=ENV)


SOURCES: List[Source] = [
    Source(
        name="hubeau_hydrometrie",
        description="Debits et hauteurs d'eau des stations hydrometriques du bassin. "
                    "Contrainte de disponibilite de la ressource et contexte d'etiage.",
        fields=[
            ("code_station", "string", "Identifiant national de la station"),
            ("date_obs", "date", "Date de l'observation"),
            ("grandeur_hydro", "string", "Q = debit, H = hauteur"),
            ("resultat_obs", "number", "Valeur observee, en L/s pour Q"),
            ("code_statut", "number", "Qualification de la mesure"),
        ],
        niveau_de_preuve="mesure",
        freshness_sla_days=5,
        last_updated="2026-07-29",
        licence="Licence Ouverte / Etalab 2.0",
        redistribuable="oui",
        tags=["source-mesuree"],
        terms=["qmna5"],
    ),
    Source(
        name="hubeau_piezometrie",
        description="Niveaux des nappes souterraines, principale ressource d'irrigation "
                    "sur le bassin.",
        fields=[
            ("code_bss", "string", "Identifiant du point de mesure"),
            ("date_mesure", "date", "Date de la mesure"),
            ("niveau_nappe_eau", "number", "Niveau piezometrique, en m NGF"),
            ("profondeur_nappe", "number", "Profondeur sous le sol, en m"),
        ],
        niveau_de_preuve="mesure",
        freshness_sla_days=15,
        last_updated="2026-07-28",
        licence="Licence Ouverte / Etalab 2.0",
        redistribuable="oui",
        tags=["source-mesuree"],
    ),
    Source(
        name="hubeau_onde",
        description="Observations terrain d'ecoulement et d'assec. Signal precoce de "
                    "restriction d'usage.",
        fields=[
            ("code_station", "string", "Station ONDE"),
            ("date_observation", "date", "Date de la campagne"),
            ("libelle_ecoulement", "string", "Ecoulement visible, non visible, assec"),
        ],
        niveau_de_preuve="mesure",
        freshness_sla_days=30,
        last_updated="2026-07-15",
        licence="Licence Ouverte / Etalab 2.0",
        redistribuable="oui",
        tags=["source-mesuree"],
    ),
    Source(
        name="prevision_saisonniere",
        description="Prevision saisonniere probabiliste : anomalie de temperature et "
                    "tercile de precipitation par mois cible. Fiabilite utile a 3 mois, "
                    "faible a 6, purement climatologique a 12.",
        fields=[
            ("mois_cible", "date", "Mois de la prevision"),
            ("anomalie_temperature", "number", "Ecart a la normale, en degres C"),
            ("tercile_precipitation", "string", "sec | normal | humide"),
            ("probabilite", "number", "Probabilite associee au tercile, 0 a 1"),
            ("horizon_mois", "number", "Distance a la date d'emission"),
        ],
        niveau_de_preuve="modelisation",
        freshness_sla_days=35,
        last_updated="2026-07-01",
        licence="Snapshot synthetique derive de statistiques publiques",
        redistribuable="oui (synthetique)",
        tags=["source-modelisee", "source-synthetique"],
        terms=["degres-jours"],
    ),
    Source(
        name="climat_journalier",
        description="Serie climatique journaliere de reference : temperature, "
                    "precipitations, ETP. Base du bilan hydrique et du cumul de "
                    "degres-jours.",
        fields=[
            ("id_maille", "string", "Maille climatique de 8 km"),
            ("date", "date", "Jour"),
            ("tas", "number", "Temperature moyenne, en degres C"),
            ("prtot", "number", "Precipitations, en mm/j"),
            ("evspsblpot", "number", "ETP Penman, en mm/j"),
        ],
        niveau_de_preuve="modelisation",
        freshness_sla_days=10,
        last_updated="2026-07-27",
        licence="Snapshot synthetique derive de normales publiques",
        redistribuable="oui (synthetique)",
        tags=["source-modelisee", "source-synthetique"],
        terms=["etp", "degres-jours"],
    ),
    Source(
        name="sol_rrp",
        description="Type de sol et reserve utile par unite cartographique. Determine "
                    "l'autonomie hydrique de la parcelle et ouvre ou ferme des cultures.",
        fields=[
            ("id_ucs", "string", "Unite cartographique de sol"),
            ("type_sol", "string", "Texture dominante"),
            ("reserve_utile_mm", "number", "Reserve utile, en mm"),
            ("profondeur_enracinement_cm", "number", "Profondeur exploitable, en cm"),
        ],
        niveau_de_preuve="modelisation",
        freshness_sla_days=3650,
        last_updated="2026-01-01",
        licence="Snapshot synthetique derive du referentiel pedologique public",
        redistribuable="oui (synthetique)",
        tags=["source-modelisee", "source-synthetique"],
        terms=["reserve-utile"],
    ),
    Source(
        name="parcelles",
        description="Parcelles de demonstration : geometrie, surface, culture declaree. "
                    "Aucune donnee personnelle d'exploitant.",
        fields=[
            ("id_parcel", "string", "Identifiant de parcelle"),
            ("code_cultu", "string", "Culture declaree"),
            ("surf_parc", "number", "Surface, en hectares"),
            ("id_ucs", "string", "Rattachement au sol"),
            ("id_maille", "string", "Rattachement climatique"),
        ],
        niveau_de_preuve="modelisation",
        freshness_sla_days=365,
        last_updated="2026-03-01",
        licence="Parcelles fictives",
        redistribuable="oui (synthetique)",
        tags=["source-synthetique"],
    ),
    Source(
        name="ref_agro_economique",
        description="Referentiel par culture : temperature de base, seuils de cumul de "
                    "degres-jours par stade, coefficients culturaux, rendements de "
                    "reference, prix et charges. Source la plus fragile du graphe.",
        fields=[
            ("culture", "string", "Culture"),
            ("t_base", "number", "Temperature de base, en degres C"),
            ("seuils_dj_stades", "string", "Cumuls de degres-jours par stade"),
            ("kc_initial", "number", "Coefficient cultural initial"),
            ("kc_mid", "number", "Coefficient cultural a mi-cycle"),
            ("kc_end", "number", "Coefficient cultural de fin de cycle"),
            ("indice_precocite", "number", "Indice varietal de precocite"),
            ("rendement_ref_qx_ha", "number", "Rendement de reference, en qx/ha"),
            ("prix_moyen_eur_qx", "number", "Prix moyen, en EUR/qx"),
            ("charges_operationnelles_eur_ha", "number", "Charges, en EUR/ha"),
            ("prix_eau_eur_m3", "number", "Cout de l'eau, en EUR/m3"),
        ],
        niveau_de_preuve="dire_d_expert",
        freshness_sla_days=400,
        last_updated="2025-11-15",
        licence="Compilation de baremes publics",
        redistribuable="oui",
        spatial_coverage="France metropolitaine",
        tags=["dire-d-expert"],
        terms=["coefficient-cultural", "degres-jours", "marge-brute", "redevance-prelevement"],
    ),
]

DERIVED: List[Source] = [
    Source(
        name="features_bilan_hydrique",
        description="Features du bilan hydrique par parcelle et par culture candidate : "
                    "dates de stades issues du cumul de degres-jours, ETM, deficit, "
                    "jours de stress.",
        fields=[
            ("id_parcel", "string", "Parcelle"),
            ("culture", "string", "Culture candidate"),
            ("date_semis", "date", "Date de semis retenue"),
            ("date_stade_critique_debut", "date", "Debut du stade critique"),
            ("date_stade_critique_fin", "date", "Fin du stade critique"),
            ("date_recolte_estimee", "date", "Recolte estimee"),
            ("etm_cumul_mm", "number", "ETM cumulee sur le cycle"),
            ("deficit_cumul_mm", "number", "Deficit hydrique cumule"),
            ("jours_stress", "number", "Jours au-dela du seuil de stress"),
        ],
        niveau_de_preuve="modelisation",
        freshness_sla_days=2,
        last_updated="2026-07-29",
        licence="Produit du pipeline",
        redistribuable="oui",
        tags=["source-modelisee"],
        terms=["etm", "pluie-efficace", "stade-critique"],
    ),
    Source(
        name="scenarios_cultures",
        description="Scenarios chiffres par parcelle, culture et horizon de prevision, "
                    "avec le recouvrement entre stade critique et fenetre de tension.",
        fields=[
            ("id_parcel", "string", "Parcelle"),
            ("culture", "string", "Culture"),
            ("horizon_mois", "number", "Horizon de prevision"),
            ("recouvrement_j", "number", "Jours de collision"),
            ("besoin_irrigation_mm", "number", "Besoin d'irrigation"),
            ("cout_eau_eur_ha", "number", "Cout de l'eau"),
            ("marge_brute_eur_ha", "number", "Marge brute"),
        ],
        niveau_de_preuve="modelisation",
        freshness_sla_days=2,
        last_updated="2026-07-29",
        licence="Produit du pipeline",
        redistribuable="oui",
        tags=["source-modelisee"],
        terms=["recouvrement", "marge-brute"],
    ),
    Source(
        name="recommandations_parcelle",
        description="Livrable final remis a l'agriculteur : cultures classees, calendrier "
                    "complet, leviers correctifs et niveau de confiance. Chaque ligne est "
                    "rattachee au run qui l'a produite.",
        fields=[
            ("id_parcel", "string", "Parcelle"),
            ("rang", "number", "Classement"),
            ("culture", "string", "Culture recommandee"),
            ("verdict", "string", "cycle_termine_avant | pic_decale | pic_en_pleine_tension"),
            ("marge_brute_eur_ha", "number", "Marge brute attendue"),
            ("niveau_confiance", "string", "haute | degradee | insuffisante"),
            ("run_urn", "string", "DataProcessInstance ayant produit la ligne"),
        ],
        niveau_de_preuve="modelisation",
        freshness_sla_days=2,
        last_updated="2026-07-30",
        licence="Produit du pipeline",
        redistribuable="oui",
        tags=["source-modelisee"],
        terms=["recouvrement", "marge-brute"],
    ),
]

ALL_DATASETS = SOURCES + DERIVED
BY_NAME = {s.name: s for s in ALL_DATASETS}

# Lineage : cible -> (amonts, datajob)
LINEAGE = {
    "features_bilan_hydrique": (
        ["climat_journalier", "prevision_saisonniere", "sol_rrp", "parcelles",
         "hubeau_hydrometrie", "hubeau_piezometrie", "hubeau_onde"],
        "build_features",
    ),
    "scenarios_cultures": (
        ["features_bilan_hydrique", "ref_agro_economique"],
        "run_scenarios",
    ),
    "recommandations_parcelle": (
        ["scenarios_cultures"],
        "score_recommandations",
    ),
}

JOBS = {
    "build_features": "Datation des stades par degres-jours et bilan hydrique FAO-56.",
    "run_scenarios": "Croisement du stade critique avec la fenetre de tension, chiffrage.",
    "score_recommandations": "Classement, recherche des leviers correctifs, niveau de confiance.",
}

MODEL_URN = make_ml_model_urn(platform=PLATFORM, model_name="gr4j_cher_v1", env=ENV)
MODEL_GROUP_URN = make_ml_model_group_urn(platform=PLATFORM, group_name="gr4j_bassins", env=ENV)
FEATURE_TABLE_URN = make_ml_feature_table_urn(feature_table_name="bilan_hydrique_features",
                                              platform=PLATFORM)
FEATURES = {
    "etm_cumul": "ETM cumulee sur le cycle cultural, en mm.",
    "deficit_cumul": "Deficit hydrique cumule, en mm.",
    "jours_stress": "Nombre de jours au-dela du seuil de stress.",
    "recouvrement_j": "Jours de collision entre stade critique et fenetre de tension.",
}

TYPE_MAP = {
    "string": models.StringTypeClass,
    "number": models.NumberTypeClass,
    "date": models.DateTypeClass,
}


# --------------------------------------------------------------------------------------
# Construction des MetadataChangeProposals
# --------------------------------------------------------------------------------------

def mcp(urn: str, aspect) -> MetadataChangeProposalWrapper:
    return MetadataChangeProposalWrapper(entityUrn=urn, aspect=aspect)


def schema_aspect(src: Source) -> models.SchemaMetadataClass:
    fields = [
        models.SchemaFieldClass(
            fieldPath=name,
            type=models.SchemaFieldDataTypeClass(type=TYPE_MAP[ftype]()),
            nativeDataType=ftype,
            description=doc,
        )
        for name, ftype, doc in src.fields
    ]
    return models.SchemaMetadataClass(
        schemaName=src.name,
        platform=f"urn:li:dataPlatform:{PLATFORM}",
        version=0,
        hash="",
        platformSchema=models.OtherSchemaClass(rawSchema=""),
        fields=fields,
    )


def confidence_properties(src: Source) -> models.DatasetPropertiesClass:
    """Les proprietes de confiance remplacent les assertions natives, absentes en OSS.

    C'est ce que la Sentinelle lit pour decider si une source est degradee, et ce que
    le Conseiller lit pour calibrer son langage.
    """
    return models.DatasetPropertiesClass(
        name=src.name,
        description=src.description,
        customProperties={
            "niveau_de_preuve": src.niveau_de_preuve,
            "freshness_sla_days": str(src.freshness_sla_days),
            "last_updated": src.last_updated,
            "spatial_coverage": src.spatial_coverage,
            "licence": src.licence,
            "redistribuable": src.redistribuable,
        },
    )


def build_vocabulary() -> Iterable[MetadataChangeProposalWrapper]:
    yield mcp(DOMAIN_URN, models.DomainPropertiesClass(
        name=DOMAIN_NAME,
        description="Decision culturale avant semis a partir des previsions de temperature, "
                    "de precipitations et d'eau disponible.",
    ))
    for slug, (label, definition) in GLOSSARY.items():
        yield mcp(make_term_urn(slug), models.GlossaryTermInfoClass(
            name=label, definition=definition, termSource="INTERNAL",
        ))
    for slug, description in TAGS.items():
        yield mcp(make_tag_urn(slug), models.TagPropertiesClass(
            name=slug, description=description,
        ))


def build_datasets() -> Iterable[MetadataChangeProposalWrapper]:
    for src in ALL_DATASETS:
        yield mcp(src.urn, confidence_properties(src))
        yield mcp(src.urn, schema_aspect(src))
        yield mcp(src.urn, models.DomainsClass(domains=[DOMAIN_URN]))
        yield mcp(src.urn, models.OwnershipClass(owners=[
            models.OwnerClass(owner=make_user_urn(src.owner),
                              type=models.OwnershipTypeClass.TECHNICAL_OWNER)
        ]))
        if src.tags:
            yield mcp(src.urn, models.GlobalTagsClass(tags=[
                models.TagAssociationClass(tag=make_tag_urn(t)) for t in src.tags
            ]))
        if src.terms:
            yield mcp(src.urn, models.GlossaryTermsClass(
                terms=[models.GlossaryTermAssociationClass(urn=make_term_urn(t))
                       for t in src.terms],
                auditStamp=AUDIT,
            ))


def build_pipeline() -> Iterable[MetadataChangeProposalWrapper]:
    flow_urn = make_data_flow_urn(orchestrator=ORCHESTRATOR, flow_id=FLOW_ID, cluster=ENV)
    yield mcp(flow_urn, models.DataFlowInfoClass(
        name=FLOW_ID,
        description="Chaine de decision culturale, des previsions a la recommandation.",
    ))
    for job_id, description in JOBS.items():
        job_urn = make_data_job_urn(orchestrator=ORCHESTRATOR, flow_id=FLOW_ID,
                                    job_id=job_id, cluster=ENV)
        yield mcp(job_urn, models.DataJobInfoClass(
            name=job_id, type="COMMAND", description=description,
        ))

    for target_name, (upstream_names, job_id) in LINEAGE.items():
        target = BY_NAME[target_name].urn
        upstreams = [BY_NAME[n].urn for n in upstream_names]
        job_urn = make_data_job_urn(orchestrator=ORCHESTRATOR, flow_id=FLOW_ID,
                                    job_id=job_id, cluster=ENV)
        yield mcp(job_urn, models.DataJobInputOutputClass(
            inputDatasets=upstreams, outputDatasets=[target],
        ))
        yield mcp(target, models.UpstreamLineageClass(upstreams=[
            models.UpstreamClass(dataset=u, type=models.DatasetLineageTypeClass.TRANSFORMED)
            for u in upstreams
        ]))


def build_ml() -> Iterable[MetadataChangeProposalWrapper]:
    yield mcp(MODEL_GROUP_URN, models.MLModelGroupPropertiesClass(
        description="Modeles hydrologiques GR4J calibres par bassin.",
    ))
    yield mcp(MODEL_URN, models.MLModelPropertiesClass(
        name="gr4j_cher_v1",
        description="GR4J calibre sur le Cher amont. Simule les debits d'etiage utilises "
                    "pour estimer la probabilite de restriction d'usage.",
        groups=[MODEL_GROUP_URN],
        version=models.VersionTagClass(versionTag="1.0.0"),
        # Ce champ est le point de controle le plus important du projet : le Conseiller
        # refuse de conclure si la parcelle n'est pas dans le bassin de calibration.
        customProperties={
            "bassin_calibration": "Cher amont",
            "periode_calibration": "2005-2020",
            "nse": "0.78",
            "source_parametres": "litterature publique",
        },
        trainingMetrics=[models.MLMetricClass(name="NSE", value="0.78")],
        mlFeatures=[make_ml_feature_urn("bilan_hydrique_features", f) for f in FEATURES],
    ))
    yield mcp(FEATURE_TABLE_URN, models.MLFeatureTablePropertiesClass(
        description="Features du bilan hydrique consommees par le moteur de scenarios.",
        mlFeatures=[make_ml_feature_urn("bilan_hydrique_features", f) for f in FEATURES],
    ))
    for name, description in FEATURES.items():
        yield mcp(make_ml_feature_urn("bilan_hydrique_features", name),
                  models.MLFeaturePropertiesClass(description=description))
    # Le modele consomme les features et alimente les scenarios : c'est ce chemin que la
    # Sentinelle remonte pour invalider les recommandations.
    yield mcp(MODEL_URN, models.UpstreamLineageClass(upstreams=[
        models.UpstreamClass(dataset=BY_NAME["features_bilan_hydrique"].urn,
                             type=models.DatasetLineageTypeClass.TRANSFORMED)
    ]))


def all_mcps() -> List[MetadataChangeProposalWrapper]:
    return [
        *build_vocabulary(),
        *build_datasets(),
        *build_pipeline(),
        *build_ml(),
    ]


# --------------------------------------------------------------------------------------
# Emission
# --------------------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Construit le graphe Terroir dans DataHub.")
    parser.add_argument("--server", default="http://localhost:8080",
                        help="URL du GMS DataHub")
    parser.add_argument("--token", default=None, help="Personal access token")
    parser.add_argument("--dry-run", metavar="FICHIER", default=None,
                        help="N'emet rien : ecrit les MCP dans un fichier JSON")
    args = parser.parse_args(argv)

    proposals = all_mcps()

    if args.dry_run:
        with open(args.dry_run, "w", encoding="utf-8") as handle:
            json.dump([p.to_obj() for p in proposals], handle, indent=2, ensure_ascii=False)
        print(f"{len(proposals)} MCP ecrits dans {args.dry_run}")
        return 0

    emitter = DatahubRestEmitter(gms_server=args.server, token=args.token)
    for proposal in proposals:
        emitter.emit(proposal)
    print(f"{len(proposals)} MCP emis vers {args.server}")
    print(f"Domaine   : {DOMAIN_NAME}")
    print(f"Datasets  : {len(ALL_DATASETS)}")
    print(f"Termes    : {len(GLOSSARY)}")
    print(f"Modele    : {MODEL_URN}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
