"""
Pydantic models shared across all Voyager agents and the orchestrator.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TravelClass(str, Enum):
    ECONOMY = "economy"
    PREMIUM_ECONOMY = "premium_economy"
    BUSINESS = "business"


class HotelTier(str, Enum):
    BUDGET = "budget"
    MIDSCALE = "midscale"
    UPSCALE = "upscale"
    LUXURY = "luxury"


class WeatherCondition(str, Enum):
    SUNNY = "sunny"
    PARTLY_CLOUDY = "partly_cloudy"
    CLOUDY = "cloudy"
    RAINY = "rainy"
    STORMY = "stormy"
    SNOWY = "snowy"


class POICategory(str, Enum):
    MUSEUM = "museum"
    PARK = "park"
    RESTAURANT = "restaurant"
    LANDMARK = "landmark"
    BEACH = "beach"
    SHOPPING = "shopping"
    ENTERTAINMENT = "entertainment"
    RELIGIOUS = "religious"
    SPORT = "sport"


class PlanStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_INPUT = "needs_input"


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class TripRequest(BaseModel):
    """Top-level user request handed to the orchestrator."""

    origin: str = Field(..., description="IATA airport code or city name, e.g. 'JFK' or 'New York'")
    destination: str = Field(..., description="IATA airport code or city name, e.g. 'CDG' or 'Paris'")
    depart_date: date = Field(..., description="Outbound flight date")
    return_date: date = Field(..., description="Return flight date")
    travelers: int = Field(default=1, ge=1, le=9)
    budget_inr: float = Field(..., gt=0, description="Total budget in INR (₹) for the entire trip")
    preferences: Optional[dict] = Field(default=None, description="Optional traveler preferences")


# ---------------------------------------------------------------------------
# Budget models
# ---------------------------------------------------------------------------


class BudgetAllocation(BaseModel):
    """How the orchestrator splits the total budget across domains."""

    total: float
    flights: float
    hotels: float
    activities: float

    @property
    def flights_pct(self) -> float:
        return round(self.flights / self.total * 100, 1)

    @property
    def hotels_pct(self) -> float:
        return round(self.hotels / self.total * 100, 1)

    @property
    def activities_pct(self) -> float:
        return round(self.activities / self.total * 100, 1)


# ---------------------------------------------------------------------------
# Flight models
# ---------------------------------------------------------------------------


class FlightOption(BaseModel):
    flight_id: str
    airline: str
    flight_number: str
    origin: str
    destination: str
    depart_time: str  # ISO 8601 datetime string
    arrive_time: str
    duration_minutes: int
    stops: int
    travel_class: TravelClass = TravelClass.ECONOMY
    price_per_person: float
    total_price: float
    baggage_included: bool = True
    available_seats: int

    @property
    def is_direct(self) -> bool:
        return self.stops == 0


# ---------------------------------------------------------------------------
# Hotel models
# ---------------------------------------------------------------------------


class HotelOption(BaseModel):
    hotel_id: str
    name: str
    city: str
    tier: HotelTier
    star_rating: float = Field(ge=1.0, le=5.0)
    price_per_night: float
    total_price: float  # price_per_night * nights
    nights: int
    amenities: list[str] = Field(default_factory=list)
    cancellation_policy: str = "Free cancellation up to 48h before check-in"
    available: bool = True
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# ---------------------------------------------------------------------------
# POI + Itinerary models
# ---------------------------------------------------------------------------


class POI(BaseModel):
    poi_id: str
    name: str
    city: str
    category: POICategory
    description: str
    latitude: float
    longitude: float
    estimated_duration_minutes: int = 60
    entry_fee_inr: float = 0.0
    is_indoor: bool = False
    rating: Optional[float] = Field(default=None, ge=1.0, le=5.0)


class WeatherForecast(BaseModel):
    date: date
    condition: WeatherCondition
    temp_high_c: float
    temp_low_c: float
    precipitation_mm: float = 0.0

    @property
    def is_outdoor_friendly(self) -> bool:
        return self.condition not in (WeatherCondition.RAINY, WeatherCondition.STORMY)


class DayPlan(BaseModel):
    date: date
    weather: Optional[WeatherForecast] = None
    pois: list[POI] = Field(default_factory=list)
    notes: Optional[str] = None


class Itinerary(BaseModel):
    destination: str
    days: list[DayPlan]
    total_activities_cost: float = 0.0


# ---------------------------------------------------------------------------
# Final plan
# ---------------------------------------------------------------------------


class TripPlan(BaseModel):
    plan_id: str
    request: TripRequest
    budget: BudgetAllocation
    currency: str = "INR"
    flight_outbound: Optional[FlightOption] = None
    flight_return: Optional[FlightOption] = None
    hotel: Optional[HotelOption] = None
    itinerary: Optional[Any] = None
    status: PlanStatus = PlanStatus.PENDING
    total_cost: float = 0.0
    savings: float = 0.0  # budget - total_cost
    summary: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Orchestrator event streaming
# ---------------------------------------------------------------------------


class OrchestratorEvent(BaseModel):
    """SSE event emitted during orchestrator execution for the frontend."""

    event_type: str  # "thinking" | "tool_call" | "tool_result" | "replan" | "done" | "error"
    agent: str  # "orchestrator" | "flight_agent" | "hotel_agent" | "itinerary_agent"
    message: str
    data: Optional[dict] = None
