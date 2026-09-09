"""
Geocoding service: turns a place name typed by the user (e.g. "Dallas, TX")
into (latitude, longitude) using OpenStreetMap's free Nominatim API.
No API key required, but Nominatim asks for a descriptive User-Agent and
respectful rate limiting (max ~1 request/second).
"""
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "eld-trip-planner-assessment/1.0"}


class GeocodeError(Exception):
    pass


def geocode(place_name: str):
    """Returns (lat, lon, display_name) for the given place, or raises GeocodeError."""
    if not place_name or not place_name.strip():
        raise GeocodeError("Location cannot be empty.")

    params = {"q": place_name, "format": "json", "limit": 1}
    response = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=10)
    response.raise_for_status()
    results = response.json()

    if not results:
        raise GeocodeError(f"Could not find a location matching '{place_name}'.")

    top = results[0]
    return float(top["lat"]), float(top["lon"]), top.get("display_name", place_name)
