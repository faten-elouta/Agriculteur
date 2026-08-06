import json
from unittest.mock import patch

from services.real_data_service import fetch_hydro_stations, fetch_rpg_parcels, fetch_rpg_with_fallback, interpolate_soil, parcel_centroid, search_communes


class Response:
    def __init__(self, payload): self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *_): return None
    def read(self): return json.dumps(self.payload).encode()


def commune():
    return {"nom": "Vierzon", "code": "18279", "centre": {"coordinates": [2.0776, 47.2351]}, "bbox": {"coordinates": [[[2, 47.18], [2.15, 47.18], [2.15, 47.28], [2, 47.28], [2, 47.18]]]}}


@patch("services.real_data_service.urlopen")
def test_search_communes(mock):
    mock.return_value = Response([commune()])
    assert search_communes("Vierzon")[0]["code"] == "18279"


@patch("services.real_data_service.urlopen")
def test_real_rpg_parcel_mapping(mock):
    mock.return_value = Response({"features": [{"properties": {"id_parcel": "2596532", "surf_parc": 4.29, "code_cultu": "PPH"}, "geometry": {"type": "MultiPolygon", "coordinates": []}}]})
    parcel = fetch_rpg_parcels(commune())[0]
    assert parcel["id"] == "RPG-2023-2596532"
    assert parcel["surface_ha"] == 4.29
    assert "anonymisé" in parcel["source"]


@patch("services.real_data_service.urlopen")
def test_hydro_keeps_active_stations(mock):
    mock.return_value = Response({"data": [{"code_station": "K549090001", "en_service": True}, {"code_station": "X", "en_service": False}]})
    assert [s["code_station"] for s in fetch_hydro_stations(commune())] == ["K549090001"]


def test_centroid_and_interpolation_are_deterministic():
    parcel = {"geometry": {"type": "Polygon", "coordinates": [[[2.0, 47.2], [2.1, 47.2], [2.1, 47.3], [2.0, 47.3], [2.0, 47.2]]]}}
    assert parcel_centroid(parcel) == (2.04, 47.24)
    first = interpolate_soil(*parcel_centroid(parcel))
    assert first == interpolate_soil(*parcel_centroid(parcel))
    assert first.method == "interpolation_idw"
    assert 60 <= first.reserve_utile_mm <= 200


@patch("services.real_data_service.fetch_rpg_parcels")
def test_rpg_falls_back_to_previous_year(mock):
    from services.real_data_service import PublicDataError
    mock.side_effect = [PublicDataError("absent"), [{"id": "fallback"}]]
    parcels, year, log = fetch_rpg_with_fallback(commune(), preferred_year=2023)
    assert year == 2022
    assert parcels[0]["id"] == "fallback"
    assert len(log) == 2
