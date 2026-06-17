"""
Hotel Agent MCP tools.
Real data via SerpAPI Google Hotels, mock fallback for local dev / scenarios.
"""
from __future__ import annotations

import hashlib
import os
from datetime import date as _date

import httpx

MOCK_API_URL = os.getenv("MOCK_API_URL", "http://localhost:8001")
USE_REAL_API = os.getenv("USE_REAL_API", "false").lower() == "true"
SERPAPI_KEY  = os.getenv("SERPAPI_KEY", "")

_AMENITY_MAP = {
    "Free Wi-Fi": "WiFi", "WiFi": "WiFi", "Wi-Fi": "WiFi",
    "Pool": "Pool", "Swimming pool": "Pool",
    "Spa": "Spa",
    "Fitness centre": "Gym", "Gym": "Gym", "Fitness center": "Gym",
    "Restaurant": "Restaurant",
    "Room service": "Room Service",
    "Bar": "Bar",
    "Breakfast included": "Breakfast", "Free breakfast": "Breakfast",
    "Parking": "Parking", "Free parking": "Parking",
}


def _stars_to_tier(rating: float) -> str:
    if rating >= 4.5:
        return "luxury"
    if rating >= 4.0:
        return "upscale"
    if rating >= 3.0:
        return "midscale"
    return "budget"


def _extract_amenities(prop: dict) -> list[str]:
    seen, result = set(), []
    for a in prop.get("amenities", []):
        label = _AMENITY_MAP.get(a)
        if label and label not in seen:
            seen.add(label)
            result.append(label)
        if len(result) >= 6:
            break
    return result


def _extract_policy(prop: dict) -> str:
    """Best-effort cancellation policy from Google Hotels property data."""
    for opt in prop.get("rates", []):
        policy = opt.get("rate_details", {}).get("cancellation_policy", "")
        if policy:
            return policy
    return "Check hotel for cancellation policy"


def _serpapi_search_hotels(
    city: str,
    check_in: str,
    check_out: str,
    guests: int = 1,
    max_price_per_night: float | None = None,
    tier: str | None = None,
) -> list[dict]:
    from serpapi import GoogleSearch

    nights = (_date.fromisoformat(check_out) - _date.fromisoformat(check_in)).days or 1

    search = GoogleSearch({
        "engine":         "google_hotels",
        "q":              f"Hotels in {city}, India",
        "check_in_date":  check_in,
        "check_out_date": check_out,
        "adults":         guests,
        "currency":       "INR",
        "hl":             "en",
        "gl":             "in",
        "api_key":        SERPAPI_KEY,
    })

    data       = search.get_dict()
    properties = data.get("properties", [])
    output     = []

    for prop in properties:
        # SerpAPI returns rate_per_night as {"lowest": "₹4,500", "extracted_lowest": 4500}
        rate_info = prop.get("rate_per_night", {})
        ppn = rate_info.get("extracted_lowest", None)
        if ppn is None:
            ppn = prop.get("extracted_rate_per_night", {}).get("lowest", None)
        if ppn is None:
            continue

        ppn = float(ppn)
        if max_price_per_night and ppn > max_price_per_night:
            continue

        stars      = float(prop.get("overall_rating", 3.0))
        hotel_tier = _stars_to_tier(stars)
        if tier and hotel_tier != tier:
            continue

        hotel_id = hashlib.md5(prop.get("name", "").encode()).hexdigest()[:8]
        gps      = prop.get("gps_coordinates", {})

        output.append({
            "hotel_id":            hotel_id,
            "name":                prop.get("name", "Unknown Hotel"),
            "city":                city,
            "tier":                hotel_tier,
            "star_rating":         round(min(max(stars, 1.0), 5.0), 1),
            "price_per_night":     round(ppn),
            "total_price":         round(ppn * nights),
            "nights":              nights,
            "amenities":           _extract_amenities(prop),
            "cancellation_policy": _extract_policy(prop),
            "available":           True,
            "latitude":            gps.get("latitude"),
            "longitude":           gps.get("longitude"),
        })

    return sorted(output, key=lambda x: x["price_per_night"])


# ── Mock fallback ──────────────────────────────────────────────────────────

def _headers() -> dict:
    h = {}
    s = os.getenv("MOCK_SCENARIO", "")
    if s:
        h["X-Mock-Scenario"] = s
    return h


def _mock_search_hotels(
    city: str,
    check_in: str,
    check_out: str,
    guests: int = 1,
    max_price_per_night: float | None = None,
    tier: str | None = None,
) -> list[dict]:
    params: dict = {
        "city": city, "check_in": check_in,
        "check_out": check_out, "guests": guests,
    }
    if max_price_per_night:
        params["max_price_per_night"] = max_price_per_night
    if tier:
        params["tier"] = tier
    with httpx.Client(timeout=10) as client:
        resp = client.get(f"{MOCK_API_URL}/hotels/search",
                          params=params, headers=_headers())
        resp.raise_for_status()
        return resp.json().get("hotels", [])


# ── Public API ─────────────────────────────────────────────────────────────

def search_hotels(
    city: str,
    check_in: str,
    check_out: str,
    guests: int = 1,
    max_price_per_night: float | None = None,
    tier: str | None = None,
) -> list[dict]:
    """
    Search for available hotels in a city.

    Args:
        city: Destination city name (e.g. 'Goa')
        check_in: Check-in date in YYYY-MM-DD format
        check_out: Check-out date in YYYY-MM-DD format
        guests: Number of guests (default 1)
        max_price_per_night: Maximum price per night in INR (optional)
        tier: Filter by tier — 'budget' | 'midscale' | 'upscale' | 'luxury' (optional)

    Returns:
        List of available hotel options sorted by price ascending.
    """
    if USE_REAL_API:
        return _serpapi_search_hotels(city, check_in, check_out,
                                       guests, max_price_per_night, tier)
    return _mock_search_hotels(city, check_in, check_out,
                                guests, max_price_per_night, tier)


def get_hotel_details(hotel_id: str) -> dict:
    """Get full details for a specific hotel."""
    with httpx.Client(timeout=10) as client:
        resp = client.get(f"{MOCK_API_URL}/hotels/{hotel_id}", headers=_headers())
        resp.raise_for_status()
        return resp.json()
