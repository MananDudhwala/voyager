"""
Flight Agent MCP tools.
All functions query the mock API (or optionally Duffel sandbox).
"""

from __future__ import annotations

import os
from typing import Optional

import httpx

MOCK_API_URL = os.getenv("MOCK_API_URL", "http://localhost:8001")
MOCK_SCENARIO = os.getenv("MOCK_SCENARIO", "")


def _headers() -> dict:
    h = {}
    if MOCK_SCENARIO:
        h["X-Mock-Scenario"] = MOCK_SCENARIO
    return h


def search_flights(
    origin: str,
    destination: str,
    date: str,
    passengers: int = 1,
    max_price: Optional[float] = None,
) -> list[dict]:
    """
    Search for available flights.

    Args:
        origin: Origin airport/city (e.g. 'JFK')
        destination: Destination airport/city (e.g. 'CDG')
        date: Departure date in YYYY-MM-DD format
        passengers: Number of passengers (default 1)
        max_price: Maximum total price in USD (optional)

    Returns:
        List of flight options sorted by price ascending.
    """
    params: dict = {
        "origin": origin,
        "destination": destination,
        "date": date,
        "passengers": passengers,
    }
    if max_price is not None:
        params["max_price"] = max_price

    with httpx.Client(timeout=10) as client:
        resp = client.get(
            f"{MOCK_API_URL}/flights/search",
            params=params,
            headers=_headers(),
        )
        resp.raise_for_status()
        return resp.json().get("flights", [])


def get_flight_details(flight_id: str) -> dict:
    """
    Get full details for a specific flight.

    Args:
        flight_id: The unique flight identifier

    Returns:
        Full flight details including baggage, stops, and seat count.
    """
    with httpx.Client(timeout=10) as client:
        resp = client.get(
            f"{MOCK_API_URL}/flights/{flight_id}",
            headers=_headers(),
        )
        resp.raise_for_status()
        return resp.json()
