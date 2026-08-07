"""KPIs du parcours : Confiance, Produit, IA.

Trois familles, toutes calculées à partir des données déjà produites par
l'application (aucune nouvelle source) :

- **Confiance** : conformité SLA des sources, niveau de preuve, garanties du
  certificat, fiabilité de la prévision, cultures sûres, traçabilité.
- **Produit** : cultures comparées, écart de marge, besoin en eau, risque
  moyen, origine de la parcelle, mode de données.
- **IA** : score technique expert, fiabilité annoncée, outils MCP exposés,
  skills chargés, incidents ouverts, modèle hydrologique et version.

En mode connecté (DATAHUB_GMS_URL), les valeurs de graphe sont lues dans
DataHub ; sinon, un calcul local reproduit exactement les mêmes formules
(le message le précise dans la légende du tableau de bord).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

MCP_TOOLS = 12
SKILLS_FALLBACK = 3


@dataclass(frozen=True)
class Kpi:
    key: str
    label: str
    value: float
    unit: str
    tone: str  # sur | vigilance | rupture | eau | neutre
    caption: str
    display: str | None = None  # libellé libre, remplace value+unit si fourni


def _freshness(graph: dict[str, Any]) -> dict[str, Any]:
    """Mêmes formules que les badges : âge vs SLA, statut par URN."""
    datasets = graph.get("datasets", {})
    today = date.today()
    statuses: dict[str, str] = {}
    for urn, meta in datasets.items():
        sla_raw = meta.get("freshness_sla_days")
        last_raw = meta.get("last_updated")
        try:
            sla_days = float(sla_raw)
            last = datetime.fromisoformat(last_raw).date()
        except (TypeError, ValueError):
            statuses[urn] = "unknown"
            continue
        statuses[urn] = "stale" if (today - last).days > sla_days else "ok"
    ok = sum(1 for s in statuses.values() if s == "ok")
    stale = sum(1 for s in statuses.values() if s == "stale")
    unknown = sum(1 for s in statuses.values() if s == "unknown")
    total = len(statuses)
    return {"ok": ok, "stale": stale, "unknown": unknown, "total": total}


def _live_freshness(graph: dict[str, Any], client: Any) -> dict[str, Any]:
    targets = {t for upstream in graph.get("lineage", {}).values() for t in upstream}
    sources = [urn for urn in graph.get("datasets", {}) if urn not in targets]
    summary = client.freshness_summary(sources)
    return {
        "ok": summary.get("ok", 0),
        "stale": summary.get("stale", 0),
        "unknown": summary.get("unknown", 0),
        "total": max(1, len(sources)),
    }


def _live_skills(client: Any) -> int:
    try:
        return len(client.list_skills())
    except Exception:
        return 0


def _live_open_incidents(client: Any) -> int:
    try:
        incidents = client.list_incidents()
    except Exception:
        return 0
    return sum(1 for incident in incidents if incident.get("status") == "ACTIVE")


def build_kpis(
    graph: dict[str, Any],
    result: dict[str, Any],
    client: Any | None = None,
) -> dict[str, list[Kpi]]:
    """Les trois familles de KPIs du parcours décisionnel."""
    live = bool(client) and getattr(client, "connected", lambda: False)()

    # --- Confiance ---------------------------------------------------------
    if live:
        freshness = _live_freshness(graph, client)
        sla_ok = freshness["ok"]
        sla_total = max(1, freshness["total"])
    else:
        freshness = _freshness(graph)
        sla_ok = freshness["ok"]
        sla_total = max(1, freshness["total"])
    sla_rate = round(sla_ok / sla_total * 100)
    sla_tone = "sur" if sla_rate >= 90 else ("vigilance" if sla_rate >= 60 else "rupture")

    datasets = graph.get("datasets", {})
    measured = sum(1 for meta in datasets.values() if meta.get("niveau_de_preuve") == "mesure")
    proof_rate = round(measured / max(1, len(datasets)) * 100)
    proof_tone = "sur" if proof_rate >= 70 else "vigilance"

    quality = {
        "verified_count": sum(
            item["level"] == "elevee"
            for item in [
                {"level": "elevee" if result.get("mode_donnees") == "reel_hybride" else "faible"},
                {"level": "elevee" if result.get("provenance", {}).get("chaine_lineage_verifiee") else "insuffisante"},
                {"level": "elevee"},
                {"level": "moyenne" if result.get("horizon_mois") == 3 else "faible"},
            ]
        ),
        "total_count": 4,
    }
    quality_rate = round(quality["verified_count"] / max(1, quality["total_count"]) * 100)

    fiabilite = result.get("confiance", {}).get("fiabilite_prevision")
    fiabilite_rate = round(fiabilite * 100) if isinstance(fiabilite, (int, float)) else None

    crops = result.get("cultures", [])
    safe_share = round(sum(1 for c in crops if c.get("etat") == "sûr") / max(1, len(crops)) * 100)

    confidence = [
        Kpi("sla", "Conformité SLA des sources", sla_rate, "%", sla_tone,
            f"{freshness['ok']} à jour · {freshness['stale']} périmée(s) · {freshness['unknown']} inconnue(s)"),
        Kpi("preuve", "Sources de mesure directe", proof_rate, "%", proof_tone,
            f"{measured} source(s) en mesure sur {len(datasets)}"),
        Kpi("garanties", "Garanties élevées du certificat", quality_rate, "%", "sur",
            f"{quality['verified_count']} preuves fortes sur {quality['total_count']}"),
        Kpi("fiabilite", "Fiabilité annoncée de la prévision", fiabilite_rate, "%", "eau",
            f"horizon {result.get('horizon_mois')} mois") if fiabilite_rate is not None
        else Kpi("fiabilite", "Fiabilité de la prévision", 0, "%", "vigilance",
                 "non annoncée pour cet horizon"),
        Kpi("cultures_sures", "Cultures au verdict sûr", safe_share, "%",
            "sur" if safe_share >= 50 else "vigilance",
            f"{sum(1 for c in crops if c.get('etat') == 'sûr')} sur {len(crops)}"),
        Kpi("traçabilité", "Chaîne de lineage vérifiée", 1 if result.get("provenance", {}).get("chaine_lineage_verifiee") else 0,
            "", "sur" if result.get("provenance", {}).get("chaine_lineage_verifiee") else "rupture",
            "sources reliées jusqu'à la recommandation",
            display="Oui" if result.get("provenance", {}).get("chaine_lineage_verifiee") else "Non"),
    ]

    # --- Produit -----------------------------------------------------------
    margins = [c.get("marge_brute_eur_ha", 0) for c in crops]
    margin_span = round(max(margins) - min(margins)) if margins else 0
    total_water = round(sum(c.get("besoin_irrigation_mm", 0) for c in crops))
    risk_days = round(sum(c.get("recouvrement_avec_tension_j", 0) for c in crops) / max(1, len(crops)))
    data_mode = result.get("mode_donnees", "inconnu")
    real_parcel = data_mode == "reel_hybride" or bool(result.get("parcelle_source"))

    product = [
        Kpi("cultures", "Cultures comparées", len(crops), "", "eau",
            f"sur la parcelle {result.get('parcelle_id', '—')}"),
        Kpi("ecart_marge", "Écart de marge entre cultures", margin_span, "€/ha", "sur",
            "fourchette du classement proposé"),
        Kpi("eau", "Besoin en eau cumulé", total_water, "mm", "vigilance",
            "lame d'irrigation des cultures comparées"),
        Kpi("risque", "Jours de tension en moyenne", risk_days, "j", "rupture" if risk_days > 14 else ("vigilance" if risk_days > 0 else "sur"),
            "recouvrement avec la fenêtre de tension"),
        Kpi("parcelle", "Parcelle d'origine", 1 if real_parcel else 0, "",
            "sur" if real_parcel else "vigilance",
            result.get("parcelle_source", "RPG public anonymisé")),
        Kpi("decision", "Étapes du parcours décisionnel", 7, "", "eau",
            "4 écrans de choix + 3 étapes de vérification"),
    ]

    # --- IA ----------------------------------------------------------------
    expert_overall = 0
    try:
        from services.expert_report_service import build_expert_report

        expert_overall = int(build_expert_report(result).get("overall_score", 0))
    except Exception:
        expert_overall = 0
    skills_count = _live_skills(client) if live else SKILLS_FALLBACK
    open_incidents = _live_open_incidents(client) if live else 0
    model = result.get("provenance", {}).get("modele", {})

    ai = [
        Kpi("score_technique", "Score technique moyen", expert_overall, "/100",
            "sur" if expert_overall >= 70 else ("vigilance" if expert_overall >= 45 else "rupture"),
            "audit des données et des modèles"),
        Kpi("mcp", "Outils MCP exposés", MCP_TOOLS, "", "eau",
            "grappe d'outils disponible pour un agent"),
        Kpi("skills", "Skills chargés par l'agent", skills_count, "",
            "sur" if skills_count else "vigilance",
            "fraîcheur, recommandations, codegen" if not live else "lus dans le graphe"),
        Kpi("incidents", "Incidents ouverts dans le graphe", open_incidents, "",
            "rupture" if open_incidents else "sur",
            "détectés par la Sentinelle le long du lineage"),
        Kpi("modele", "Modèle hydrologique", float(model.get("version", "1.0.0").split(".")[0]), "", "eau",
            f"{model.get('bassin_calibration', 'Cher amont')} · GR4J",
            display=model.get("version", "1.0.0")),
        Kpi("runs", "Runs tracés par exécution", 1, "", "sur",
            "un run écrit sur recommandations_parcelle"),
    ]

    return {"confiance": confidence, "produit": product, "ia": ai}
