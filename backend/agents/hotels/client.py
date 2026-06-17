"""
Optional Duffel sandbox client for real hotel data.
"""

from __future__ import annotations

import os

import httpx

DUFFEL_API_KEY = os.getenv("DUFFEL_API_KEY", "")
DUFFEL_BASE = "https://api.duffel.com"


class DuffelHotelClient:
    def __init__(self, api_key: str = DUFFEL_API_KEY) -> None:
        if not api_key:
            raise ValueError("DUFFEL_API_KEY is not set")
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Duffel-Version": "v2",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def search_accommodations(
        self,
        city_iata: str,
        check_in: str,
        check_out: str,
        guests: int = 1,
    ) -> list[dict]:
        payload = {
            "data": {
                "location": {"radius": 10, "geographic_coordinates": {"longitude": 0, "latitude": 0}},
                "check_in_date": check_in,
                "check_out_date": check_out,
                "rooms": 1,
                "guests": [{"type": "adult"} for _ in range(guests)],
            }
        }
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{DUFFEL_BASE}/stays/search",
                json=payload,
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json().get("data", {}).get("results", [])
