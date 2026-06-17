"""
Hotel Agent MCP tools.
All functions query the mock API (or optionally Duffel sandbox).
"""

from __future__ import annotations

import os
from typing import Optional

import httpx

MOCK_API_URL = os.getenv("MOCK_API_URL", "http://localhost:8001")


def _headers() -> dict:
    """Build request headers, reading MOCK_SCENARIO live so activate_scenario takes effect."""
    h = {}
    scenario = os.getenv("MOCK_SCENARIO", "")
    if scenario:
        h["X-Mock-Scenario"] = scenario
    return h


def search_hotels(
    city: str,
    check_in: str,
    check_out: str,
    guests: int = 1,
    max_price_per_night: Optional[float] = None,
    tier: Optional[str] = None,
) -> list[dict]:
    """
    Search for available hotels in a city.

    Args:
        city: Destination city name (e.g. 'Paris')
        check_in: Check-in date in YYYY-MM-DD format
        check_out: Check-out date in YYYY-MM-DD format
        guests: Number of guests (default 1)
        max_price_per_night: Maximum price per night in INR (optional)
        tier: Filter by tier — 'budget' | 'midscale' | 'upscale' | 'luxury' (optional)

    Returns:
        List of available hotel options sorted by price ascending.
    """
    params: dict = {
        "city": city,
        "check_in": check_in,
        "check_out": check_out,
        "guests": guests,
    }
    if max_price_per_night is not None:
        params["max_price_per_night"] = max_price_per_night
    if tier:
        params["tier"] = tier

    with httpx.Client(timeout=10) as client:
        resp = client.get(
            f"{MOCK_API_URL}/hotels/search",
            params=params,
            headers=_headers(),
        )
        resp.raise_for_status()
        return resp.json().get("hotels", [])


def get_hotel_details(hotel_id: str) -> dict:
    """
    Get full details for a specific hotel.

    Args:
        hotel_id: The unique hotel identifier

    Returns:
        Full hotel details including amenities and cancellation policy.
    """
    with httpx.Client(timeout=10) as client:
        resp = client.get(
            f"{MOCK_API_URL}/hotels/{hotel_id}",
            headers=_headers(),
        )
        resp.raise_for_status()
        return resp.json()
