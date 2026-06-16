"""
Itinerary Agent MCP tools.
- get_pois: Fetches POIs from the mock API
- get_weather: Stub returning mock weather (replaced with OpenWeatherMap in Phase 4)
- get_travel_times: Stub returning estimated travel times
- build_itinerary: Assembles a day-by-day plan, weather-aware
"""

from __future__ import annotations

import os
import random
from datetime import date, timedelta
from typing import Optional

import httpx

MOCK_API_URL = os.getenv("MOCK_API_URL", "http://localhost:8001")
MOCK_SCENARIO = os.getenv("MOCK_SCENARIO", "")

# Weather conditions mapped to rough probabilities per "season"
_WEATHER_POOL = [
    ("sunny", 22, 14, 0),
    ("partly_cloudy", 19, 12, 0),
    ("cloudy", 17, 10, 0),
    ("rainy", 15, 9, 8),
    ("rainy", 14, 8, 12),
]

random.seed(0)  # deterministic for demos


def get_pois(
    city: str,
    categories: Optional[list[str]] = None,
    limit: int = 10,
    indoor_only: bool = False,
) -> list[dict]:
    """
    Retrieve points of interest for a city.

    Args:
        city: City name (e.g. 'Paris')
        categories: List of POI categories to filter by (optional).
                    Options: museum | park | restaurant | landmark | beach |
                             shopping | entertainment | religious | sport
        limit: Maximum number of results (default 10, max 50)
        indoor_only: If True, only return indoor POIs (useful on rainy days)

    Returns:
        List of POI objects sorted by rating descending.
    """
    params: dict = {"city": city, "limit": limit}
    if categories:
        params["categories"] = ",".join(categories)
    if indoor_only:
        params["indoor_only"] = "true"

    with httpx.Client(timeout=10) as client:
        resp = client.get(f"{MOCK_API_URL}/pois/search", params=params)
        resp.raise_for_status()
        return resp.json().get("pois", [])


def get_weather(city: str, dates: list[str]) -> list[dict]:
    """
    Get weather forecast for a city across a list of dates.

    Args:
        city: City name
        dates: List of dates in YYYY-MM-DD format

    Returns:
        List of daily forecasts with condition, temp_high_c, temp_low_c,
        precipitation_mm, and is_outdoor_friendly flag.
    """
    forecasts = []
    for d in dates:
        condition, high, low, precip = random.choice(_WEATHER_POOL)
        forecasts.append({
            "date": d,
            "city": city,
            "condition": condition,
            "temp_high_c": high + random.randint(-2, 2),
            "temp_low_c": low + random.randint(-2, 2),
            "precipitation_mm": precip,
            "is_outdoor_friendly": condition not in ("rainy", "stormy"),
        })
    return forecasts


def get_travel_times(
    origin_name: str,
    destination_name: str,
    mode: str = "walking",
) -> dict:
    """
    Estimate travel time between two named locations.

    Args:
        origin_name: Starting point (e.g. 'Eiffel Tower')
        destination_name: Ending point (e.g. 'Louvre Museum')
        mode: Travel mode — 'walking' | 'driving' | 'transit'

    Returns:
        dict with duration_minutes and distance_km (estimated).
    """
    # Stub: real implementation uses Google Distance Matrix in Phase 4
    base_minutes = {"walking": 25, "transit": 15, "driving": 10}
    duration = base_minutes.get(mode, 20) + random.randint(-5, 15)
    return {
        "origin": origin_name,
        "destination": destination_name,
        "mode": mode,
        "duration_minutes": max(5, duration),
        "distance_km": round(duration * 0.07, 1),
        "note": "Estimated — connect Google Distance Matrix in Phase 4 for real data",
    }


def build_itinerary(
    city: str,
    dates: list[str],
    pois: list[dict],
    travel_mode: str = "walking",
) -> dict:
    """
    Build a day-by-day itinerary for a city.
    Automatically swaps outdoor POIs for indoor ones on rainy days.

    Args:
        city: Destination city
        dates: List of dates in YYYY-MM-DD format (one per day)
        pois: List of POI objects (from get_pois)
        travel_mode: Preferred travel mode between POIs

    Returns:
        Full itinerary with one DayPlan per date, weather-aware POI assignment,
        and estimated travel times.
    """
    weather = get_weather(city, dates)
    weather_by_date = {w["date"]: w for w in weather}

    # Split POIs into indoor and outdoor pools
    indoor_pois = [p for p in pois if p.get("is_indoor")]
    outdoor_pois = [p for p in pois if not p.get("is_indoor")]

    # Aim for ~3 POIs per day
    pois_per_day = 3
    day_plans = []
    poi_index = {"indoor": 0, "outdoor": 0}

    for day_date in dates:
        w = weather_by_date.get(day_date, {})
        is_rainy = not w.get("is_outdoor_friendly", True)

        # Pick POIs: prefer indoor on rainy days
        day_pois = []
        if is_rainy:
            # Use indoor POIs, fall back to any remaining
            pool = indoor_pois[poi_index["indoor"]:]
            poi_index["indoor"] += min(pois_per_day, len(pool))
            day_pois = pool[:pois_per_day]
            if len(day_pois) < pois_per_day:
                extra = outdoor_pois[poi_index["outdoor"]:]
                day_pois += extra[: pois_per_day - len(day_pois)]
        else:
            pool = outdoor_pois[poi_index["outdoor"]:]
            poi_index["outdoor"] += min(pois_per_day, len(pool))
            day_pois = pool[:pois_per_day]
            if len(day_pois) < pois_per_day:
                extra = indoor_pois[poi_index["indoor"]:]
                day_pois += extra[: pois_per_day - len(day_pois)]

        # Compute travel legs
        legs = []
        for i in range(len(day_pois) - 1):
            leg = get_travel_times(
                day_pois[i]["name"],
                day_pois[i + 1]["name"],
                travel_mode,
            )
            legs.append(leg)

        total_cost = sum(p.get("entry_fee_usd", 0) for p in day_pois)

        day_plans.append({
            "date": day_date,
            "weather": w,
            "pois": day_pois,
            "travel_legs": legs,
            "daily_activities_cost_usd": round(total_cost, 2),
            "weather_note": (
                "🌧️ Rainy day — itinerary adjusted to indoor activities"
                if is_rainy
                else "☀️ Great day for outdoor exploration"
            ),
        })

    total_cost = sum(d["daily_activities_cost_usd"] for d in day_plans)

    return {
        "city": city,
        "days": day_plans,
        "total_activities_cost_usd": round(total_cost, 2),
        "travel_mode": travel_mode,
    }
