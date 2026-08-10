"""Carte SVG interactive de la commune : parcelles RPG et stations d'eau.

Reprojection équirectangulaire simple des géométries WGS84 (RPG) vers un
viewBox SVG ; la parcelle sélectionnée est mise en évidence, les autres
restent visibles et chacune amène à sa fiche (<details>) ; les stations
hydrométriques/piézométriques sont posées avec une infobulle native
(code et libellé). Aucune bibliothèque de carte : purement le SVG rendu
dans le navigateur, animé par les révéls génériques.
"""

from __future__ import annotations

import html
from typing import Any

from ui.i18n import MS, t

SELECTED_FILL = "#2B6C8F"
SELECTED_STROKE = "#14394B"
OTHER_FILL = "#D8E2D6"
OTHER_STROKE = "#9FB3A8"
STATION_COLOR = "#C08A2E"
BORDER = "#E1E4DD"

PADDING = 0.0012


def _station_coords(station: dict[str, Any]) -> tuple[float, float] | None:
    lon = station.get("longitude") or station.get("lon")
    lat = station.get("latitude") or station.get("lat")
    if lon is not None and lat is not None:
        return float(lon), float(lat)
    geometry = station.get("geometrie") or station.get("geometry")
    if isinstance(geometry, dict) and geometry.get("coordinates"):
        coords = geometry["coordinates"]
        if len(coords) >= 2:
            return float(coords[0]), float(coords[1])
    return None


def _polygons(geometry: dict[str, Any] | None) -> list[list[list[tuple[float, float]]]]:
    """Rings (polygones fermés) d'une géométrie Polygon ou MultiPolygon."""
    if not geometry:
        return []
    rings: list[list[list[tuple[float, float]]]] = []
    kind = geometry.get("type")
    coords = geometry.get("coordinates") or []
    polys = coords if kind == "MultiPolygon" else [coords]
    for poly in polys:
        if not poly:
            continue
        ring = []
        for lon, lat in poly[0]:
            ring.append((float(lon), float(lat)))
        if ring:
            rings.append([ring])
    return rings


def render_parcel_map(
    parcels: list[dict[str, Any]],
    stations: list[dict[str, Any]],
    selected_id: str | None,
    lang: str = MS,
) -> str:
    """SVG de la carte : parcelles (polygones) + stations (pastilles)."""
    selected_id = selected_id or (parcels[0].get("id") if parcels else None)
    all_points = [
        (lon, lat)
        for parcel in parcels
        for polys in _polygons(parcel.get("geometry"))
        for ring in polys
        for lon, lat in ring
    ]
    station_points = [
        coord for station in stations if (coord := _station_coords(station)) is not None
    ]
    if not parcels and not stations:
        return ""

    lons = [p[0] for p in all_points + station_points]
    lats = [p[1] for p in all_points + station_points]
    if all_points or station_points:
        if max(lons) - min(lons) < 1e-9 or max(lats) - min(lats) < 1e-9:
            max_lon = max(lons) + PADDING
            max_lat = max(lats) + PADDING
        min_lon = min(lons) - PADDING
        min_lat = min(lats) - PADDING
        max_lon = max(lons) + PADDING
        max_lat = max(lats) + PADDING

    span_lon = (max_lon - min_lon) if all_points or station_points else 1
    span_lat = (max_lat - min_lat) if all_points or station_points else 1
    width, height = 900, int(900 * span_lat / span_lon * 1.0)
    height = max(320, height)

    def project(lon: float, lat: float) -> tuple[float, float]:
        x = (lon - min_lon) / span_lon * width
        y = (max_lat - lat) / span_lat * height
        return x, y

    out: list[str] = []
    if all_points or station_points:
        out.append(
            f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(t(lang, "map.aria"))}" '
            f'xmlns="http://www.w3.org/2000/svg" '
            f'style="width:100%;height:auto;display:block;background:#F5F7F4;">'
            f'<rect width="{width}" height="{height}" fill="#F5F7F4"/>'
        )
    detail_html: list[str] = []
    for parcel in parcels:
        parcel_id = parcel.get("id") or parcel.get("label", "")
        is_selected = parcel_id == selected_id
        slug = f"pm-{parcel_id.replace('_', '-')[:40]}"
        for polys in _polygons(parcel.get("geometry")):
            for ring in polys:
                points = " ".join(f"{x:.1f},{y:.1f}" for x, y in (project(lon, lat) for lon, lat in ring))
                attrs = (
                    f'fill="{SELECTED_FILL}" stroke="{SELECTED_STROKE}"'
                    if is_selected
                    else f'fill="{OTHER_FILL}" stroke="{OTHER_STROKE}"'
                )
                out.append(
                    f'<a href="#{slug}" aria-label="{html.escape(str(parcel.get("label", "")))}">'
                    f'<polygon points="{points}" {attrs} stroke-width="{3 if is_selected else 1.5}" '
                    f'stroke-linejoin="round" opacity="{1 if is_selected else 0.92}">'
                    f'<title>{html.escape(str(parcel.get("label", "")))} · '
                    f'{parcel.get("surface_ha", "?")} ha · {parcel.get("sol", "")}</title>'
                    f"</polygon></a>"
                )
        label = parcel.get("label", parcel_id)
        detail_html.append(
            f'<details id="{slug}" class="parcel-card"'
            f'{" open" if is_selected else ""}>'
            f"<summary>{html.escape(str(label))}"
            f'<span class="parcel-card-area">{parcel.get("surface_ha", "?")} ha</span></summary>'
            f"<dl>"
            f"<dt>{html.escape(t(lang, 'map.soil'))}</dt><dd>{html.escape(str(parcel.get('sol', '—')))}</dd>"
            f"<dt>{html.escape(t(lang, 'map.ru'))}</dt><dd>{parcel.get('reserve_utile_mm', '—')} mm</dd>"
            f"<dt>{html.escape(t(lang, 'map.commune'))}</dt><dd>{html.escape(str(parcel.get('commune', '—')))}</dd>"
            f"</dl></details>"
        )

    for index, station in enumerate(stations):
        if not all_points and not station_points:
            break
        coord = _station_coords(station)
        if coord is None:
            continue
        x, y = project(*coord)
        name = station.get("libelle_station") or station.get("code_station") or "Station"
        code = station.get("code_station", "")
        out.append(
            f'<g class="station-marker" style="--st-i:{index};">'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="11" fill="{STATION_COLOR}" opacity="0.18"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{STATION_COLOR}" '
            f'stroke="#F5F7F4" stroke-width="2">'
            f'<title>{html.escape(str(name))} · {html.escape(str(code))}</title>'
            f"</circle></g>"
        )

    if all_points or station_points:
        out.append(
            f'<g class="map-legend">'
            f'<rect x="{width - 210:.0f}" y="{height - 62:.0f}" width="196" height="48" rx="6" fill="#FFFFFF" '
            f'stroke="{BORDER}"/>'
            f'<circle cx="{width - 192:.0f}" cy="{height - 42:.0f}" r="5" fill="{SELECTED_FILL}"/>'
            f'<text x="{width - 180:.0f}" y="{height - 39:.0f}" font-family="system-ui" font-size="11" '
            f'fill="#1C2620">{html.escape(t(lang, "map.selected"))}</text>'
            f'<circle cx="{width - 192:.0f}" cy="{height - 24:.0f}" r="5" fill="{STATION_COLOR}"/>'
            f'<text x="{width - 180:.0f}" y="{height - 21:.0f}" font-family="system-ui" font-size="11" '
            f'fill="#1C2620">{html.escape(t(lang, "map.station"))}</text>'
            f"</g>"
        )
        out.append("</svg>")
    out.append(f'<div class="parcel-cards">{"".join(detail_html)}</div>')
    return "".join(out)
