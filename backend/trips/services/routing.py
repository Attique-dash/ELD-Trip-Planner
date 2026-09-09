"""
Routing service: gets a driving route (distance, duration, and the road
geometry to draw on the map) between two points using the free public
OSRM demo server. No API key required.

Note: the public OSRM demo server (router.project-osrm.org) is meant for
light/demo use. For a production app you'd self-host OSRM or use a paid
provider, but it's perfectly fine for this assessment.
"""
import requests

OSRM_URL = "https://router.project-osrm.org/route/v1/driving/{coords}"


class RoutingError(Exception):
    pass


def get_route(start_lat, start_lon, end_lat, end_lon):
    """
    Returns a dict:
      {
        "distance_miles": float,
        "duration_hours": float,
        "geometry": [[lat, lon], [lat, lon], ...]  # polyline points for the map
      }
    """
    coords = f"{start_lon},{start_lat};{end_lon},{end_lat}"
    url = OSRM_URL.format(coords=coords)
    params = {"overview": "full", "geometries": "geojson"}

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        raise RoutingError("Could not calculate a driving route between these locations.")

    route = data["routes"][0]
    distance_miles = route["distance"] / 1609.34   # meters -> miles
    duration_hours = route["duration"] / 3600.0     # seconds -> hours

    # geojson coordinates come as [lon, lat] - flip to [lat, lon] for Leaflet
    geometry = [[point[1], point[0]] for point in route["geometry"]["coordinates"]]

    return {
        "distance_miles": round(distance_miles, 1),
        "duration_hours": round(duration_hours, 2),
        "geometry": geometry,
    }
