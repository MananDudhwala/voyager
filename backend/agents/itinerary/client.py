"""
OpenTripMap + OpenWeatherMap client stubs.
Swap these in during Phase 4 / Phase 6 when real API keys are available.
"""

from __future__ import annotations

import os

import httpx

OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "")
OPENTRIPMAP_API_KEY = os.getenv("OPENTRIPMAP_API_KEY", "")


class OpenWeatherMapClient:
    """
    Fetches 5-day / 3-hour forecasts from OpenWeatherMap free tier.
    Activate by setting OPENWEATHERMAP_API_KEY in .env.
    """

    BASE = "https://api.openweathermap.org/data/2.5"

    def __init__(self, api_key: str = OPENWEATHERMAP_API_KEY) -> None:
        if not api_key:
            raise ValueError("OPENWEATHERMAP_API_KEY is not set")
        self._key = api_key

    def get_forecast(self, city: str, days: int = 5) -> list[dict]:
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                f"{self.BASE}/forecast",
                params={"q": city, "appid": self._key, "units": "metric", "cnt": days * 8},
            )
            resp.raise_for_status()
            data = resp.json()

        # Aggregate to daily
        daily: dict[str, dict] = {}
        for item in data.get("list", []):
            day = item["dt_txt"][:10]
            if day not in daily:
                daily[day] = {
                    "date": day,
                    "city": city,
                    "temp_highs": [],
                    "temp_lows": [],
                    "conditions": [],
                    "precipitation_mm": 0.0,
                }
            daily[day]["temp_highs"].append(item["main"]["temp_max"])
            daily[day]["temp_lows"].append(item["main"]["temp_min"])
            daily[day]["conditions"].append(item["weather"][0]["main"].lower())
            daily[day]["precipitation_mm"] += item.get("rain", {}).get("3h", 0)

        result = []
        for d in daily.values():
            condition = "rainy" if "rain" in d["conditions"] else "sunny"
            result.append({
                "date": d["date"],
                "city": city,
                "condition": condition,
                "temp_high_c": round(max(d["temp_highs"]), 1),
                "temp_low_c": round(min(d["temp_lows"]), 1),
                "precipitation_mm": round(d["precipitation_mm"], 1),
                "is_outdoor_friendly": condition not in ("rainy", "stormy"),
            })
        return result


class OpenTripMapClient:
    """
    Fetches real POI data from OpenTripMap free tier.
    Activate by setting OPENTRIPMAP_API_KEY in .env.
    """

    BASE = "https://api.opentripmap.com/0.1/en"

    def __init__(self, api_key: str = OPENTRIPMAP_API_KEY) -> None:
        if not api_key:
            raise ValueError("OPENTRIPMAP_API_KEY is not set")
        self._key = api_key

    def get_pois(self, city: str, radius_m: int = 5000, limit: int = 20) -> list[dict]:
        # Step 1: geocode city
        with httpx.Client(timeout=10) as client:
            geo = client.get(
                f"{self.BASE}/places/geoname",
                params={"name": city, "apikey": self._key},
            )
            geo.raise_for_status()
            coords = geo.json()
            lat, lon = coords["lat"], coords["lon"]

            # Step 2: fetch POIs around coords
            pois_resp = client.get(
                f"{self.BASE}/places/radius",
                params={
                    "radius": radius_m,
                    "lon": lon,
                    "lat": lat,
                    "limit": limit,
                    "apikey": self._key,
                    "format": "json",
                },
            )
            pois_resp.raise_for_status()
            return pois_resp.json()
