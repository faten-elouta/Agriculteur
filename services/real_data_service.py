"""Accès aux données publiques réelles françaises, sans clé API."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class PublicDataError(RuntimeError):
    """Erreur compréhensible d'une API publique."""


@dataclass(frozen=True)
class RealTerritory:
    commune: dict[str, Any]
    parcels: list[dict[str, Any]]
    hydro_stations: list[dict[str, Any]]
    fetched_at: str
    rpg_year: int
    resolution_log: list[dict[str, str]]


@dataclass(frozen=True)
class ResolvedSoil:
    soil_type: str
    reserve_utile_mm: int
    method: str
    source: str
    confidence: str
    detail: str


def _get(url: str, params: dict[str, Any], timeout: float = 12) -> dict[str, Any] | list[Any]:
    request = Request(f"{url}?{urlencode(params)}", headers={"User-Agent": "TerroirContextAgents/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise PublicDataError(f"Source publique indisponible ({url}).") from exc


def search_communes(query: str) -> list[dict[str, Any]]:
    """Recherche une commune dans le référentiel officiel de l'État."""
    if len(query.strip()) < 2:
        raise PublicDataError("Saisissez au moins deux caractères pour la commune.")
    data = _get(
        "https://geo.api.gouv.fr/communes",
        {"nom": query.strip(), "fields": "nom,code,centre,bbox", "format": "json", "geometry": "centre", "limit": 5},
    )
    if not isinstance(data, list) or not data:
        raise PublicDataError(f"Aucune commune trouvée pour « {query} ».")
    return data


def _search_polygon(lon: float, lat: float, radius: float = 0.018) -> dict[str, Any]:
    return {"type": "Polygon", "coordinates": [[[lon-radius, lat-radius], [lon+radius, lat-radius], [lon+radius, lat+radius], [lon-radius, lat+radius], [lon-radius, lat-radius]]]}


def _coordinates(geometry: dict[str, Any]) -> list[tuple[float, float]]:
    """Aplatit les coordonnées Polygon/MultiPolygon."""
    out: list[tuple[float, float]] = []
    def visit(value: Any) -> None:
        if isinstance(value, list) and len(value) >= 2 and all(isinstance(v, (int, float)) for v in value[:2]):
            out.append((float(value[0]), float(value[1])))
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(geometry.get("coordinates", []))
    return out


def parcel_centroid(parcel: dict[str, Any]) -> tuple[float, float]:
    points = _coordinates(parcel.get("geometry") or {})
    if not points:
        raise PublicDataError("Géométrie de parcelle absente : sol impossible à localiser.")
    return round(sum(p[0] for p in points) / len(points), 8), round(sum(p[1] for p in points) / len(points), 8)


# Points de référence pédologiques régionaux de démonstration. Ils servent uniquement
# au dernier recours et ne sont jamais présentés comme une mesure parcellaire.
SOIL_REFERENCE_POINTS = [
    (2.02, 47.18, 132, "limono-argileux"),
    (2.16, 47.20, 146, "limoneux"),
    (2.00, 47.30, 151, "argileux"),
    (2.18, 47.29, 137, "limono-argileux"),
]


def interpolate_soil(lon: float, lat: float) -> ResolvedSoil:
    """Interpolation IDW déterministe, réservée au dernier recours."""
    weighted: list[tuple[float, str, float]] = []
    weights: list[float] = []
    for x, y, reserve, soil_type in SOIL_REFERENCE_POINTS:
        distance2 = (lon - x) ** 2 + (lat - y) ** 2
        weight = 1.0 / max(distance2, 1e-9)
        weighted.append((reserve * weight, soil_type, weight))
        weights.append(weight)
    reserve = round(sum(value for value, _, _ in weighted) / sum(weights))
    type_weights: dict[str, float] = {}
    for _, soil_type, weight in weighted:
        type_weights[soil_type] = type_weights.get(soil_type, 0.0) + weight
    soil_type = max(type_weights, key=type_weights.get)
    return ResolvedSoil(soil_type, reserve, "interpolation_idw", "points de référence pédologiques régionaux", "faible", "Valeur interpolée spatialement, non mesurée; analyse de sol nécessaire.")


def resolve_soil(parcel: dict[str, Any]) -> ResolvedSoil:
    """Essaie SoilGrids, puis applique une interpolation documentée si nécessaire."""
    lon, lat = parcel_centroid(parcel)
    try:
        data = _get("https://rest.isric.org/soilgrids/v2.0/properties/query", {"lon": lon, "lat": lat, "property": "clay,sand", "depth": "0-30cm", "value": "mean"}, timeout=4)
        layers = data.get("properties", {}).get("layers", []) if isinstance(data, dict) else []
        values: dict[str, float] = {}
        for layer in layers:
            depths = layer.get("depths", [])
            if depths:
                raw = depths[0].get("values", {}).get("mean")
                if raw is not None:
                    values[layer.get("name", "")] = float(raw) / 10.0
        if "clay" not in values or "sand" not in values:
            raise PublicDataError("SoilGrids ne renvoie pas la texture attendue.")
        clay, sand = values["clay"], values["sand"]
        soil_type = "argileux" if clay >= 35 else "sableux" if sand >= 60 else "limono-argileux" if clay >= 22 else "limoneux"
        # Fonction de pédotransfert démonstrative bornée pour 1 m de sol.
        reserve = round(max(60, min(200, 95 + 1.8 * clay - 0.45 * sand)))
        return ResolvedSoil(soil_type, reserve, "source_secondaire", "ISRIC SoilGrids 250 m", "moyenne", "Texture modélisée à 250 m; réserve utile estimée par fonction de pédotransfert.")
    except PublicDataError:
        return interpolate_soil(lon, lat)


def fetch_rpg_parcels(commune: dict[str, Any], year: int = 2023, limit: int = 20) -> list[dict[str, Any]]:
    """Récupère des parcelles RPG réelles, publiques et anonymisées."""
    lon, lat = commune["centre"]["coordinates"]
    data = _get(
        "https://apicarto.ign.fr/api/rpg/v2",
        {"annee": year, "_limit": limit, "geom": json.dumps(_search_polygon(float(lon), float(lat)), separators=(",", ":"))},
    )
    features = data.get("features", []) if isinstance(data, dict) else []
    parcels: list[dict[str, Any]] = []
    for feature in features:
        props = feature.get("properties", {})
        if not props.get("id_parcel") or props.get("surf_parc") is None:
            continue
        parcels.append({
            "id": f"RPG-{year}-{props['id_parcel']}",
            "label": f"RPG {props['id_parcel']} — {float(props['surf_parc']):.2f} ha",
            "commune": commune["nom"],
            "code_insee": commune["code"],
            "surface_ha": round(float(props["surf_parc"]), 2),
            "sol": "non renseigné par le RPG",
            "reserve_utile_mm": 140,
            "culture_actuelle": props.get("code_cultu", "non renseignée"),
            "source": "IGN API Carto — RPG anonymisé",
            "millesime": year,
            "geometry": feature.get("geometry"),
        })
    if not parcels:
        raise PublicDataError(f"Aucune parcelle RPG {year} trouvée près du centre de {commune['nom']}.")
    return sorted(parcels, key=lambda item: item["surface_ha"], reverse=True)


def fetch_rpg_with_fallback(commune: dict[str, Any], preferred_year: int = 2023) -> tuple[list[dict[str, Any]], int, list[dict[str, str]]]:
    """Essaie plusieurs millésimes RPG du plus récent au plus ancien."""
    log: list[dict[str, str]] = []
    for year in range(preferred_year, max(2014, preferred_year - 4), -1):
        try:
            parcels = fetch_rpg_parcels(commune, year=year)
            log.append({"field": "parcelles", "source": f"IGN RPG {year}", "status": "utilisée"})
            return parcels, year, log
        except PublicDataError as exc:
            log.append({"field": "parcelles", "source": f"IGN RPG {year}", "status": f"échec: {exc}"})
    raise PublicDataError("Aucune parcelle trouvée dans les quatre derniers millésimes RPG testés.")


def fetch_hydro_stations(commune: dict[str, Any], limit: int = 10) -> list[dict[str, Any]]:
    """Récupère les stations hydrométriques réelles autour de la commune."""
    bbox = commune.get("bbox")
    if bbox and bbox.get("coordinates"):
        ring = bbox["coordinates"][0]
        xs, ys = [p[0] for p in ring], [p[1] for p in ring]
        bounds = f"{min(xs)},{min(ys)},{max(xs)},{max(ys)}"
    else:
        lon, lat = commune["centre"]["coordinates"]
        bounds = f"{lon-.08},{lat-.06},{lon+.08},{lat+.06}"
    data = _get(
        "https://hubeau.eaufrance.fr/api/v2/hydrometrie/referentiel/stations",
        {"bbox": bounds, "size": limit, "format": "json"},
    )
    stations = data.get("data", []) if isinstance(data, dict) else []
    return [station for station in stations if station.get("en_service")]


def fetch_piezo_stations(commune: dict[str, Any], limit: int = 10) -> list[dict[str, Any]]:
    """Source secondaire: stations de nappes Hub'Eau du département."""
    code_department = str(commune["code"])[:2]
    data = _get("https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/stations", {"code_departement": code_department, "size": limit, "format": "json"})
    rows = data.get("data", []) if isinstance(data, dict) else []
    return [{**row, "code_station": row.get("code_bss") or row.get("bss_id"), "libelle_station": row.get("nom_commune", "Station piézométrique"), "source_type": "piezometrie"} for row in rows]


def fetch_water_stations_with_fallback(commune: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Hydrométrie d'abord, piézométrie ensuite si elle manque."""
    log: list[dict[str, str]] = []
    try:
        stations = fetch_hydro_stations(commune)
        if stations:
            log.append({"field": "eau", "source": "Hub'Eau Hydrométrie", "status": "utilisée"})
            return stations, log
        log.append({"field": "eau", "source": "Hub'Eau Hydrométrie", "status": "aucune station"})
    except PublicDataError as exc:
        log.append({"field": "eau", "source": "Hub'Eau Hydrométrie", "status": f"échec: {exc}"})
    try:
        stations = fetch_piezo_stations(commune)
        if stations:
            log.append({"field": "eau", "source": "Hub'Eau Piézométrie", "status": "source secondaire utilisée"})
            return stations, log
        log.append({"field": "eau", "source": "Hub'Eau Piézométrie", "status": "aucune station"})
    except PublicDataError as exc:
        log.append({"field": "eau", "source": "Hub'Eau Piézométrie", "status": f"échec: {exc}"})
    return [], log


def fetch_real_territory(commune_name: str, rpg_year: int = 2023) -> RealTerritory:
    """Assemble commune, RPG et référentiel Hub'Eau en un appel métier."""
    commune = search_communes(commune_name)[0]
    parcels, actual_year, parcel_log = fetch_rpg_with_fallback(commune, preferred_year=rpg_year)
    stations, water_log = fetch_water_stations_with_fallback(commune)
    return RealTerritory(
        commune=commune,
        parcels=parcels,
        hydro_stations=stations,
        fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        rpg_year=actual_year,
        resolution_log=[{"field": "commune", "source": "API Découpage administratif", "status": "utilisée"}, *parcel_log, *water_log],
    )
