"""
Voyager Orchestrator Agent.

Uses Claude via the Anthropic SDK with MCP tool_use to delegate to:
  - Flight Agent  (search_flights, get_flight_details)
  - Hotel Agent   (search_hotels, get_hotel_details)
  - Itinerary Agent (get_pois, get_weather, get_travel_times, build_itinerary)

The orchestrator runs the full planning loop, handles replanning, and
streams OrchestratorEvent objects for the frontend SSE feed.

Usage:
    import asyncio
    from shared.models import TripRequest
    from orchestrator.agent import VoyagerOrchestrator
    from datetime import date

    async def main():
        request = TripRequest(
            origin="JFK",
            destination="CDG",
            depart_date=date(2026, 8, 1),
            return_date=date(2026, 8, 6),
            travelers=2,
            budget_usd=3000,
        )
        orchestrator = VoyagerOrchestrator()
        plan = await orchestrator.plan(request)
        print(plan.model_dump_json(indent=2))

    asyncio.run(main())
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the backend directory (two levels up from this file)
load_dotenv(Path(__file__).parent.parent / ".env")
import uuid
from collections.abc import AsyncGenerator
from typing import Any, Optional

import anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from orchestrator.planner import PlanningState
from orchestrator.prompts import ORCHESTRATOR_SYSTEM_PROMPT, build_planning_prompt, build_replan_prompt
from shared.models import (
    TripPlan,
    TripRequest,
    PlanStatus,
    FlightOption,
    HotelOption,
    Itinerary,
    OrchestratorEvent,
    TravelClass,
    HotelTier,
)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL = "claude-opus-4-5"

# City name → IATA code mapping for flight searches
CITY_TO_IATA: dict[str, str] = {
    # Indian domestic destinations
    "goa": "GOI",
    "jaipur": "JAI",
    "udaipur": "UDR",
    "manali": "KUU",   # Kullu-Manali airport
    "kochi": "COK",
    "kerala": "COK",
    "varanasi": "VNS",
    "delhi": "DEL",
    "new delhi": "DEL",
    "mumbai": "BOM",
    "bombay": "BOM",
    "bangalore": "BLR",
    "bengaluru": "BLR",
    "hyderabad": "HYD",
    "chennai": "MAA",
    "madras": "MAA",
    "kolkata": "CCU",
    "calcutta": "CCU",
    "pune": "PNQ",
    "ahmedabad": "AMD",
    "amritsar": "ATQ",
    "leh": "IXL",
    "ladakh": "IXL",
    "coimbatore": "CJB",
    "pondicherry": "PNY",
    "mysore": "MYQ",
    # International gateways (for future use)
    "dubai": "DXB",
    "singapore": "SIN",
    "london": "LHR",
    "paris": "CDG",
    "new york": "JFK",
    "bangkok": "BKK",
    "kuala lumpur": "KUL",
}


def _to_iata(name: str) -> str:
    """Convert city name to IATA code, or return as-is if already a code."""
    return CITY_TO_IATA.get(name.lower(), name.upper())

# Paths to each MCP server
import sys

BACKEND_DIR = Path(__file__).parent.parent
PYTHON = str(Path(sys.executable))


def _server_params(module: str) -> StdioServerParameters:
    return StdioServerParameters(
        command=PYTHON,
        args=["-m", module],
        env={**os.environ, "PYTHONPATH": str(BACKEND_DIR)},
    )


FLIGHT_SERVER = _server_params("agents.flights.server")
HOTEL_SERVER = _server_params("agents.hotels.server")
ITINERARY_SERVER = _server_params("agents.itinerary.server")


class VoyagerOrchestrator:
    """
    High-level orchestrator that coordinates the three MCP sub-agents.
    """

    def __init__(self) -> None:
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is not set in environment")
        self._client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def plan(
        self,
        request: TripRequest,
        event_callback: Optional[AsyncGenerator] = None,
    ) -> TripPlan:
        """
        Run the full planning loop for a TripRequest.
        Optionally stream OrchestratorEvents via event_callback.
        """
        state = PlanningState(request)
        plan_id = str(uuid.uuid4())

        async def emit(event_type: str, agent: str, message: str, data: dict = None) -> None:
            event = state.emit(event_type, agent, message, data)
            if event_callback:
                await event_callback(OrchestratorEvent(**event))
            print(f"[{agent}] {event_type}: {message}")

        await emit("thinking", "orchestrator", f"Starting trip plan for {request.destination}")
        await emit(
            "thinking",
            "orchestrator",
            f"Budget: {request.budget_usd} USD — allocating 40/40/20 split\n"
            f"  Flights: ${state.allocation.flights} | Hotels: ${state.allocation.hotels} | "
            f"Activities: ${state.allocation.activities}",
        )

        flight_out, flight_ret = await self._plan_flights(state, emit)
        hotel = await self._plan_hotel(state, emit)
        itinerary = await self._plan_itinerary(state, emit)

        total_cost = round(
            state.flight_cost + state.hotel_cost + state.activities_cost, 2
        )
        savings = round(request.budget_usd - total_cost, 2)

        status = PlanStatus.COMPLETED
        if flight_out is None or hotel is None:
            status = PlanStatus.NEEDS_INPUT
        if state.is_over_budget():
            status = PlanStatus.NEEDS_INPUT
            state.warn(
                f"Total cost {total_cost} exceeds budget {request.budget_usd}. "
                "Consider increasing budget or adjusting dates."
            )

        summary = self._build_summary(request, flight_out, hotel, total_cost, savings, state)

        await emit("done", "orchestrator", f"Plan complete — status: {status.value}", {
            "total_cost": total_cost,
            "savings": savings,
        })

        return TripPlan(
            plan_id=plan_id,
            request=request,
            budget=state.allocation,
            flight_outbound=flight_out,
            flight_return=flight_ret,
            hotel=hotel,
            itinerary=itinerary,
            status=status,
            total_cost=total_cost,
            savings=savings,
            summary=summary,
            warnings=state.warnings,
        )

    # ------------------------------------------------------------------
    # Flight planning
    # ------------------------------------------------------------------

    async def _plan_flights(self, state: PlanningState, emit) -> tuple[Optional[FlightOption], Optional[FlightOption]]:
        """Search for outbound + return flights, with budget reallocation on failure."""
        request = state.request

        for attempt in range(PlanningState.MAX_FLIGHT_RETRIES + 1):
            await emit(
                "tool_call", "flight_agent",
                f"Searching flights {request.origin}→{request.destination} "
                f"on {request.depart_date} | budget: ${state.allocation.flights}",
            )

            flights_out = await self._call_flight_tool(
                "search_flights",
                origin=_to_iata(request.origin),
                destination=_to_iata(request.destination),
                date=request.depart_date.isoformat(),
                passengers=request.travelers,
                max_price=state.allocation.flights * 0.6,
            )

            if not flights_out:
                await emit("replan", "orchestrator", "No outbound flights found within budget")
                if not state.try_shift_budget_to_flights():
                    await emit("error", "orchestrator", "Cannot find flights — budget exhausted")
                    return None, None
                continue

            # Pick cheapest direct, otherwise cheapest overall
            direct = [f for f in flights_out if f.get("stops", 1) == 0]
            chosen_out_data = direct[0] if direct else flights_out[0]

            await emit(
                "tool_result", "flight_agent",
                f"Found {len(flights_out)} outbound options — selected {chosen_out_data['airline']} "
                f"{chosen_out_data['flight_number']} at ${chosen_out_data['price_per_person']}/person",
                {"flight": chosen_out_data},
            )

            # Search return flight
            return_budget = state.allocation.flights - chosen_out_data["total_price"]
            flights_ret = await self._call_flight_tool(
                "search_flights",
                origin=_to_iata(request.destination),
                destination=_to_iata(request.origin),
                date=request.return_date.isoformat(),
                passengers=request.travelers,
                max_price=return_budget,
            )

            chosen_ret_data = flights_ret[0] if flights_ret else None

            total_flight_cost = chosen_out_data["total_price"] + (
                chosen_ret_data["total_price"] if chosen_ret_data else 0
            )
            state.record_flight_cost(total_flight_cost)

            await emit(
                "thinking", "orchestrator",
                f"Flights booked: ${total_flight_cost} (budget: ${state.allocation.flights}). "
                f"{state.budget_status()}",
            )

            out = self._dict_to_flight(chosen_out_data, request.travelers)
            ret = self._dict_to_flight(chosen_ret_data, request.travelers) if chosen_ret_data else None
            return out, ret

        return None, None

    # ------------------------------------------------------------------
    # Hotel planning
    # ------------------------------------------------------------------

    async def _plan_hotel(self, state: PlanningState, emit) -> Optional[HotelOption]:
        request = state.request

        for attempt in range(PlanningState.MAX_HOTEL_RETRIES + 1):
            await emit(
                "tool_call", "hotel_agent",
                f"Searching hotels in {request.destination} "
                f"{request.depart_date}→{request.return_date} | "
                f"max/night: ${state.max_hotel_per_night}",
            )

            hotels = await self._call_hotel_tool(
                "search_hotels",
                city=request.destination,
                check_in=request.depart_date.isoformat(),
                check_out=request.return_date.isoformat(),
                guests=request.travelers,
                max_price_per_night=state.max_hotel_per_night,
            )

            available = [h for h in hotels if h.get("available", True)]

            if not available:
                await emit("replan", "orchestrator", "No available hotels found within budget")
                if not state.try_shift_budget_to_hotels():
                    # Try adjacent dates
                    new_in, new_out = state.adjacent_dates(1)
                    await emit(
                        "replan", "orchestrator",
                        f"Trying adjacent dates: {new_in}→{new_out}",
                    )
                    hotels = await self._call_hotel_tool(
                        "search_hotels",
                        city=request.destination,
                        check_in=new_in,
                        check_out=new_out,
                        guests=request.travelers,
                        max_price_per_night=state.max_hotel_per_night * 1.15,
                    )
                    available = [h for h in hotels if h.get("available", True)]
                    if not available:
                        await emit("error", "orchestrator", "No hotels found even with adjacent dates")
                        return None
                else:
                    continue

            chosen = available[0]
            state.record_hotel_cost(chosen.get("total_price", 0))

            await emit(
                "tool_result", "hotel_agent",
                f"Selected {chosen['name']} ({chosen['tier']}) — "
                f"${chosen['price_per_night']}/night × {state.nights} nights = ${chosen.get('total_price', 0)}",
                {"hotel": chosen},
            )

            return self._dict_to_hotel(chosen, state.nights)

        return None

    # ------------------------------------------------------------------
    # Itinerary planning
    # ------------------------------------------------------------------

    async def _plan_itinerary(self, state: PlanningState, emit) -> Optional[Itinerary]:
        request = state.request

        await emit(
            "tool_call", "itinerary_agent",
            f"Fetching POIs for {request.destination} | dates: {state.trip_dates}",
        )

        pois = await self._call_itinerary_tool(
            "get_pois",
            city=request.destination,
            limit=20,
        )

        weather = await self._call_itinerary_tool(
            "get_weather",
            city=request.destination,
            dates=state.trip_dates,
        )

        rainy_days = [w["date"] for w in weather if not w.get("is_outdoor_friendly", True)]
        if rainy_days:
            await emit(
                "thinking", "itinerary_agent",
                f"Rain forecast on {rainy_days} — will substitute indoor POIs",
            )

        itinerary_data = await self._call_itinerary_tool(
            "build_itinerary",
            city=request.destination,
            dates=state.trip_dates,
            pois=pois,
            travel_mode="walking",
        )

        state.record_activities_cost(itinerary_data.get("total_activities_cost_usd", 0))

        await emit(
            "tool_result", "itinerary_agent",
            f"Built {len(itinerary_data.get('days', []))} day itinerary | "
            f"activities cost: ${state.activities_cost}",
            {"itinerary": itinerary_data},
        )

        # Return raw dict — stored as-is in TripPlan.itinerary (Optional[Any])
        return itinerary_data  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # MCP tool call helpers
    # ------------------------------------------------------------------

    async def _call_flight_tool(self, tool: str, **kwargs) -> Any:
        async with stdio_client(FLIGHT_SERVER) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool, arguments=kwargs)
                text = result.content[0].text if result.content else "[]"
                return json.loads(text)

    async def _call_hotel_tool(self, tool: str, **kwargs) -> Any:
        async with stdio_client(HOTEL_SERVER) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool, arguments=kwargs)
                text = result.content[0].text if result.content else "[]"
                return json.loads(text)

    async def _call_itinerary_tool(self, tool: str, **kwargs) -> Any:
        async with stdio_client(ITINERARY_SERVER) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool, arguments=kwargs)
                text = result.content[0].text if result.content else "{}"
                return json.loads(text)

    # ------------------------------------------------------------------
    # Data conversion helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _dict_to_flight(d: dict, travelers: int) -> FlightOption:
        return FlightOption(
            flight_id=d.get("flight_id", ""),
            airline=d.get("airline", ""),
            flight_number=d.get("flight_number", ""),
            origin=d.get("origin", ""),
            destination=d.get("destination", ""),
            depart_time=d.get("depart_time", ""),
            arrive_time=d.get("arrive_time", ""),
            duration_minutes=d.get("duration_minutes", 0),
            stops=d.get("stops", 0),
            travel_class=TravelClass(d.get("travel_class", "economy")),
            price_per_person=d.get("price_per_person", 0),
            total_price=d.get("total_price", 0),
            baggage_included=bool(d.get("baggage_included", True)),
            available_seats=d.get("available_seats", 0),
        )

    @staticmethod
    def _dict_to_hotel(d: dict, nights: int) -> HotelOption:
        return HotelOption(
            hotel_id=d.get("hotel_id", ""),
            name=d.get("name", ""),
            city=d.get("city", ""),
            tier=HotelTier(d.get("tier", "midscale")),
            star_rating=d.get("star_rating", 3.0),
            price_per_night=d.get("price_per_night", 0),
            total_price=d.get("total_price", 0),
            nights=nights,
            amenities=d.get("amenities", []) if isinstance(d.get("amenities"), list)
                      else d.get("amenities", "").split("|"),
            cancellation_policy=d.get("cancellation_policy", ""),
            available=bool(d.get("available", True)),
            latitude=d.get("latitude"),
            longitude=d.get("longitude"),
        )

    @staticmethod
    def _build_summary(
        request: TripRequest,
        flight: Optional[FlightOption],
        hotel: Optional[HotelOption],
        total_cost: float,
        savings: float,
        state: PlanningState,
    ) -> str:
        dest = request.destination
        travelers = request.travelers
        budget = request.budget_usd

        if flight and hotel:
            return (
                f"Your {state.nights}-night trip to {dest} for {travelers} traveler(s) is ready. "
                f"Flying {flight.airline} ({flight.flight_number}), staying at {hotel.name}. "
                f"Total cost: ${total_cost:,.2f} of your ${budget:,.2f} budget "
                f"({'saving ' + f'${savings:,.2f}' if savings >= 0 else f'over budget by ${abs(savings):,.2f}'})."
            )
        return (
            f"Partial plan for {dest} — some components could not be booked within your ${budget:,.2f} budget. "
            "See warnings for details."
        )
