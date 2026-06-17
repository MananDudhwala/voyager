"""
Optional Duffel sandbox client for real flight data.
Swap this in by setting USE_DUFFEL=true in your .env.
"""

from __future__ import annotations

import os

import httpx

DUFFEL_API_KEY = os.getenv("DUFFEL_API_KEY", "")
DUFFEL_BASE = "https://api.duffel.com"


class DuffelClient:
    def __init__(self, api_key: str = DUFFEL_API_KEY) -> None:
        if not api_key:
            raise ValueError("DUFFEL_API_KEY is not set")
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Duffel-Version": "v2",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def search_offers(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        passengers: int = 1,
        cabin_class: str = "economy",
    ) -> list[dict]:
        payload = {
            "data": {
                "slices": [
                    {
                        "origin": origin,
                        "destination": destination,
                        "departure_date": departure_date,
                    }
                ],
                "passengers": [{"type": "adult"} for _ in range(passengers)],
                "cabin_class": cabin_class,
            }
        }
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{DUFFEL_BASE}/air/offer_requests?return_offers=true",
                json=payload,
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json().get("data", {}).get("offers", [])
