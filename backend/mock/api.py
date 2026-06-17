"""
FastAPI mock API — serves flights, hotels, and POI data from SQLite.
Supports scenario injection via MOCK_SCENARIO env var or X-Mock-Scenario header.

Run:
    uvicorn mock.api:app --reload --port 8001
"""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DB_DIR = Path(__file__).parent / "db"
SCENARIOS_DIR = Path(__file__).parent / "scenarios"

FLIGHTS_DB = DB_DIR / "flights.db"
HOTELS_DB = DB_DIR / "hotels.db"
POIS_DB = DB_DIR / "pois.db"


# ---------------------------------------------------------------------------
# Scenario loader
# ---------------------------------------------------------------------------

_SCENARIO_CACHE: dict[str, dict] = {}


def _load_scenario(name: str) -> dict:
    if name in _SCENARIO_CACHE:
        return _SCENARIO_CACHE[name]
    path = SCENARIOS_DIR / f"{name}.json"
    if not path.exists():
        raise HTTPException(status_code=400, detail=f"Unknown scenario: {name}")
    data = json.loads(path.read_text())
    _SCENARIO_CACHE[name] = data
    return data


def _active_scenario(x_mock_scenario: str | None) -> dict | None:
    """Resolve scenario from header → env var → None (happy path)."""
    name = x_mock_scenario or os.getenv("MOCK_SCENARIO", "").strip()
    if not name:
        return None
    return _load_scenario(name)


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _conn(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _rows(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict]:
    cur = conn.execute(sql, params)
    return [dict(r) for r in cur.fetchall()]


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure DBs exist; seed if missing
    for db in (FLIGHTS_DB, HOTELS_DB, POIS_DB):
        if not db.exists():
            import subprocess
            import sys
            subprocess.run(
                [sys.executable, "-m", "mock.db.seed"],
                cwd=Path(__file__).parent.parent,
                check=True,
            )
            break
    yield


app = FastAPI(
    title="Voyager Mock API",
    description="Mock data API for the Voyager multi-agent trip planner",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "service": "voyager-mock-api"}


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

@app.get("/scenarios")
def list_scenarios():
    """List all available scenario names."""
    names = [p.stem for p in SCENARIOS_DIR.glob("*.json")]
    return {"scenarios": names}


@app.get("/scenarios/{name}")
def get_scenario(name: str):
    return _load_scenario(name)


# ---------------------------------------------------------------------------
# Flights
# ---------------------------------------------------------------------------

@app.get("/flights/search")
def search_flights(
    origin: str = Query(...),
    destination: str = Query(...),
    date: str = Query(..., description="YYYY-MM-DD"),
    passengers: int = Query(default=1, ge=1),
    max_price: float | None = Query(default=None),
    x_mock_scenario: str | None = Header(default=None),
):
    scenario = _active_scenario(x_mock_scenario)

    # Scenario: force empty results
    if scenario and scenario.get("overrides", {}).get("flights", {}).get("empty_results"):
        return {"flights": [], "scenario": scenario["name"]}

    with _conn(FLIGHTS_DB) as conn:
        sql = """
            SELECT * FROM flights
            WHERE origin = ? AND destination = ?
              AND available_seats >= ?
        """
        params: list = [origin.upper(), destination.upper(), passengers]

        if max_price is not None:
            # Apply scenario price multiplier before filtering
            multiplier = 1.0
            if scenario:
                multiplier = scenario.get("overrides", {}).get("flights", {}).get(
                    "min_price_multiplier", 1.0
                )
            effective_max = max_price / multiplier
            sql += " AND price_per_person <= ?"
            params.append(effective_max)

        sql += " ORDER BY price_per_person ASC LIMIT 10"
        flights = _rows(conn, sql, tuple(params))

    # Apply price multiplier to results
    if scenario:
        multiplier = scenario.get("overrides", {}).get("flights", {}).get(
            "min_price_multiplier", 1.0
        )
        for f in flights:
            f["price_per_person"] = round(f["price_per_person"] * multiplier, 2)
            f["total_price"] = round(f["price_per_person"] * passengers, 2)
    else:
        for f in flights:
            f["total_price"] = round(f["price_per_person"] * passengers, 2)

    return {"flights": flights, "count": len(flights)}


@app.get("/flights/{flight_id}")
def get_flight(flight_id: str, x_mock_scenario: str | None = Header(default=None)):
    with _conn(FLIGHTS_DB) as conn:
        rows = _rows(conn, "SELECT * FROM flights WHERE flight_id = ?", (flight_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Flight not found")
    return rows[0]


# ---------------------------------------------------------------------------
# Hotels
# ---------------------------------------------------------------------------

@app.get("/hotels/search")
def search_hotels(
    city: str = Query(...),
    check_in: str = Query(..., description="YYYY-MM-DD"),
    check_out: str = Query(..., description="YYYY-MM-DD"),
    guests: int = Query(default=1, ge=1),
    max_price_per_night: float | None = Query(default=None),
    tier: str | None = Query(default=None),
    x_mock_scenario: str | None = Header(default=None),
):
    from datetime import date as dt

    scenario = _active_scenario(x_mock_scenario)

    check_in_dt = dt.fromisoformat(check_in)
    check_out_dt = dt.fromisoformat(check_out)
    nights = max((check_out_dt - check_in_dt).days, 1)

    with _conn(HOTELS_DB) as conn:
        sql = "SELECT * FROM hotels WHERE city = ? AND available = 1"
        params: list = [city]

        if tier:
            sql += " AND tier = ?"
            params.append(tier)

        if max_price_per_night is not None:
            multiplier = 1.0
            if scenario:
                multiplier = scenario.get("overrides", {}).get("hotels", {}).get(
                    "min_price_multiplier", 1.0
                )
            effective_max = max_price_per_night / multiplier
            sql += " AND price_per_night <= ?"
            params.append(effective_max)

        sql += " ORDER BY price_per_night ASC LIMIT 10"
        hotels = _rows(conn, sql, tuple(params))

    # Scenario: force top N unavailable
    if scenario:
        force_unavail = scenario.get("overrides", {}).get("hotels", {}).get(
            "force_unavailable_top_n", 0
        )
        for i, h in enumerate(hotels):
            if i < force_unavail:
                h["available"] = 0

        multiplier = scenario.get("overrides", {}).get("hotels", {}).get(
            "min_price_multiplier", 1.0
        )
        for h in hotels:
            h["price_per_night"] = round(h["price_per_night"] * multiplier, 2)
            h["total_price"] = round(h["price_per_night"] * nights, 2)
            h["amenities"] = h.get("amenities", "").split("|")
    else:
        for h in hotels:
            h["total_price"] = round(h["price_per_night"] * nights, 2)
            h["nights"] = nights
            h["amenities"] = h.get("amenities", "").split("|")

    # Filter out unavailable after scenario injection
    available_hotels = [h for h in hotels if h.get("available", 1)]

    return {"hotels": available_hotels, "count": len(available_hotels), "nights": nights}


@app.get("/hotels/{hotel_id}")
def get_hotel(hotel_id: str, x_mock_scenario: str | None = Header(default=None)):
    with _conn(HOTELS_DB) as conn:
        rows = _rows(conn, "SELECT * FROM hotels WHERE hotel_id = ?", (hotel_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Hotel not found")
    h = rows[0]
    h["amenities"] = h.get("amenities", "").split("|")
    return h


# ---------------------------------------------------------------------------
# POIs
# ---------------------------------------------------------------------------

@app.get("/pois/search")
def search_pois(
    city: str = Query(...),
    categories: str | None = Query(default=None, description="Comma-separated list"),
    limit: int = Query(default=10, ge=1, le=50),
    indoor_only: bool = Query(default=False),
):
    with _conn(POIS_DB) as conn:
        sql = "SELECT * FROM pois WHERE city = ?"
        params: list = [city]

        if indoor_only:
            sql += " AND is_indoor = 1"

        if categories:
            cats = [c.strip() for c in categories.split(",")]
            placeholders = ",".join("?" * len(cats))
            sql += f" AND category IN ({placeholders})"
            params.extend(cats)

        sql += " ORDER BY rating DESC LIMIT ?"
        params.append(limit)

        pois = _rows(conn, sql, tuple(params))

    return {"pois": pois, "count": len(pois)}


@app.get("/pois/{poi_id}")
def get_poi(poi_id: str):
    with _conn(POIS_DB) as conn:
        rows = _rows(conn, "SELECT * FROM pois WHERE poi_id = ?", (poi_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="POI not found")
    return rows[0]


# ---------------------------------------------------------------------------
# Cities (for frontend autocomplete)
# ---------------------------------------------------------------------------

@app.get("/cities")
def list_cities():
    with _conn(HOTELS_DB) as conn:
        rows = _rows(conn, "SELECT DISTINCT city FROM hotels ORDER BY city")
    return {"cities": [r["city"] for r in rows]}
