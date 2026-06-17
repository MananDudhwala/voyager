"""
Flight Agent MCP tools.
Real data via SerpAPI Google Flights, mock fallback for local dev / scenarios.
"""
from __future__ import annotations

import hashlib
import os
from typing import Optional

import httpx

MOCK_API_URL = os.getenv("MOCK_API_URL", "http://localhost:8001")
USE_REAL_API = os.getenv("USE_REAL_API", "false").lower() == "true"
SERPAPI_KEY  = os.getenv("SERPAPI_KEY", "")

# City name → IATA airport code for Indian destinations
CITY_TO_IATA: dict[str, str] = {
    "goa":       "GOI",
    "jaipur":    "JAI",
    "udaipur":   "UDR",
    "manali":    "KUU",
    "kochi":     "COK",
    "varanasi":  "VNS",
    "leh":       "IXL",
    "coorg":     "IXE",
    "rishikesh": "DED",
    "andaman":   "IXZ",
    "delhi":     "DEL",
    "mumbai":    "BOM",
    "bangalore": "BLR",
    "hyderabad": "HYD",
    "chennai":   "MAA",
    "kolkata":   "CCU",
    "pune":      "PNQ",
    "ahmedabad": "AMD",
}


def _resolve_iata(code_or_city: str) -> str:
    s = code_or_city.strip()
    if len(s) == 3 and s.isupper():
        return s
    return CITY_TO_IATA.get(s.lower(), s.upper()[:3])


def _map_cabin(google_class: str) -> str:
    return {
        "Economy": "economy",
        "Premium economy": "economy",
        "Business": "business",
        "First": "first",
    }.get(google_class, "economy")


def _has_baggage(offer: dict) -> bool:
    for leg in offer.get("flights", []):
        if any("baggage" in e.lower() for e in leg.get("extensions", [])):
            return True
    return False


def _serpapi_search_flights(
    origin: str,
    destination: str,
    date: str,
    passengers: int = 1,
    max_price: Optional[float] = None,
) -> list[dict]:
    from serpapi import GoogleSearch

    origin_iata = _resolve_iata(origin)
    dest_iata   = _resolve_iata(destination)

    search = GoogleSearch({
        "engine":        "google_flights",
        "departure_id":  origin_iata,
        "arrival_id":    dest_iata,
        "outbound_date": date,
        "adults":        passengers,
        "currency":      "INR",
        "hl":            "en",
        "type":          "2",   # one-way
        "api_key":       SERPAPI_KEY,
    })

    data = search.get_dict()
    all_offers = data.get("best_flights", []) + data.get("other_flights", [])

    output = []
    for offer in all_offers:
        legs = offer.get("flights", [])
        if not legs:
            continue

        total_inr = offer.get("price", 0)
        if max_price and total_inr > max_price:
            continue

        first_leg = legs[0]
        last_leg  = legs[-1]
        raw_id    = f"{origin_iata}-{dest_iata}-{first_leg.get('departure_airport', {}).get('time', '')}"

        output.append({
            "flight_id":        hashlib.md5(raw_id.encode()).hexdigest()[:8],
            "airline":          first_leg.get("airline", "Unknown"),
            "flight_number":    first_leg.get("flight_number", ""),
            "origin":           origin_iata,
            "destination":      dest_iata,
            "depart_time":      first_leg.get("departure_airport", {}).get("time", ""),
            "arrive_time":      last_leg.get("arrival_airport", {}).get("time", ""),
            "duration_minutes": offer.get("total_duration", 0),
            "stops":            len(legs) - 1,
            "travel_class":     _map_cabin(first_leg.get("travel_class", "Economy")),
            "price_per_person": round(total_inr / passengers),
            "total_price":      total_inr,
            "baggage_included": _has_baggage(offer),
            "available_seats":  9,
        })

    return sorted(output, key=lambda x: x["total_price"])


# ── Mock fallback ──────────────────────────────────────────────────────────

def _headers() -> dict:
    h = {}
    scenario = os.getenv("MOCK_SCENARIO", "")
    if scenario:
        h["X-Mock-Scenario"] = scenario
    return h


def _mock_search_flights(
    origin: str,
    destination: str,
    date: str,
    passengers: int = 1,
    max_price: Optional[float] = None,
) -> list[dict]:
    params: dict = {
        "origin": origin, "destination": destination,
        "date": date, "passengers": passengers,
    }
    if max_price is not None:
        params["max_price"] = max_price
    with httpx.Client(timeout=10) as client:
        resp = client.get(f"{MOCK_API_URL}/flights/search",
                          params=params, headers=_headers())
        resp.raise_for_status()
        return resp.json().get("flights", [])


# ── Public API ─────────────────────────────────────────────────────────────

def search_flights(
    origin: str,
    destination: str,
    date: str,
    passengers: int = 1,
    max_price: Optional[float] = None,
) -> list[dict]:
    """Search for available flights. Returns list of FlightOption dicts sorted by price."""
    if USE_REAL_API:
        return _serpapi_search_flights(origin, destination, date, passengers, max_price)
    return _mock_search_flights(origin, destination, date, passengers, max_price)


def get_flight_details(flight_id: str) -> dict:
    """Fetch full details for a specific flight (always uses mock — no by-ID lookup in Google Flights)."""
    with httpx.Client(timeout=10) as client:
        resp = client.get(f"{MOCK_API_URL}/flights/{flight_id}", headers=_headers())
        resp.raise_for_status()
        return resp.json()
