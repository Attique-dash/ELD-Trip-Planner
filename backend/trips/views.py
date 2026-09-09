from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .serializers import TripRequestSerializer
from .services.geocode import geocode, GeocodeError
from .services.routing import get_route, RoutingError
from .services.hos_calculator import (
    HOSCalculator,
    split_segments_into_days,
    compute_totals_by_status,
)


@api_view(["POST"])
def plan_trip(request):
    """
    POST /api/plan-trip/
    body: {
      "current_location": "Chicago, IL",
      "pickup_location": "St. Louis, MO",
      "dropoff_location": "Dallas, TX",
      "current_cycle_used": 12
    }

    Returns route info for the map + one entry per daily log sheet.
    """
    serializer = TripRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    try:
        cur_lat, cur_lon, cur_name = geocode(data["current_location"])
        pick_lat, pick_lon, pick_name = geocode(data["pickup_location"])
        drop_lat, drop_lon, drop_name = geocode(data["dropoff_location"])
    except GeocodeError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    try:
        leg1 = get_route(cur_lat, cur_lon, pick_lat, pick_lon)
        leg2 = get_route(pick_lat, pick_lon, drop_lat, drop_lon)
    except RoutingError as e:
        return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

    calculator = HOSCalculator(current_cycle_used_hours=data["current_cycle_used"])
    plan = calculator.plan(
        leg1_miles=leg1["distance_miles"], leg1_hours=leg1["duration_hours"],
        leg2_miles=leg2["distance_miles"], leg2_hours=leg2["duration_hours"],
    )

    day_lists = split_segments_into_days(plan.segments)
    log_sheets = []
    for i, day_segments in enumerate(day_lists):
        totals = compute_totals_by_status(day_segments)
        log_sheets.append({
            "day": i + 1,
            "segments": [
                {
                    "status": seg.status,
                    "start_hour": seg.start_hour,
                    "end_hour": seg.end_hour,
                    "label": seg.label,
                }
                for seg in day_segments
            ],
            "totals": totals,
        })

    response_data = {
        "locations": {
            "current": {"lat": cur_lat, "lon": cur_lon, "name": cur_name},
            "pickup": {"lat": pick_lat, "lon": pick_lon, "name": pick_name},
            "dropoff": {"lat": drop_lat, "lon": drop_lon, "name": drop_name},
        },
        "route": {
            "leg1_geometry": leg1["geometry"],
            "leg2_geometry": leg2["geometry"],
            "total_distance_miles": plan.total_distance_miles,
        },
        "trip_summary": {
            "total_driving_hours": plan.total_driving_hours,
            "total_trip_hours": plan.total_trip_hours,
            "fuel_stops": plan.fuel_stops,
            "days_required": plan.days,
            "warnings": plan.warnings,
        },
        "log_sheets": log_sheets,
    }
    return Response(response_data, status=status.HTTP_200_OK)
