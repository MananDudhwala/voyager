"""
Orchestrator planner — budget allocation and constraint checking.
This is pure logic with no LLM calls; the agent uses it as a helper.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from shared.budget import (
    default_allocation,
    shift_to_flights,
    shift_to_hotels,
    is_within_budget,
    remaining_budget,
    format_usd,
    BudgetSummary,
)
from shared.models import BudgetAllocation, TripRequest


class PlanningState:
    """
    Mutable state container for a single planning run.
    Tracks allocations, costs, retries, and replanning decisions.
    """

    MAX_FLIGHT_RETRIES = 2
    MAX_HOTEL_RETRIES = 2

    def __init__(self, request: TripRequest) -> None:
        self.request = request
        self.allocation: BudgetAllocation = default_allocation(request.budget_usd)
        self.budget_summary = BudgetSummary(allocation=self.allocation)

        self.flight_cost: float = 0.0
        self.hotel_cost: float = 0.0
        self.activities_cost: float = 0.0

        self.flight_retries: int = 0
        self.hotel_retries: int = 0

        self.warnings: list[str] = []
        self.events: list[dict] = []

    # ------------------------------------------------------------------
    # Budget helpers
    # ------------------------------------------------------------------

    @property
    def nights(self) -> int:
        delta = self.request.return_date - self.request.depart_date
        return max(delta.days, 1)

    @property
    def trip_dates(self) -> list[str]:
        """List of date strings for each day of the trip."""
        return [
            (self.request.depart_date + timedelta(days=i)).isoformat()
            for i in range(self.nights)
        ]

    @property
    def max_hotel_per_night(self) -> float:
        return round(self.allocation.hotels / self.nights, 2)

    @property
    def activities_budget(self) -> float:
        return remaining_budget(
            self.request.budget_usd, self.flight_cost, self.hotel_cost
        )

    def record_flight_cost(self, cost: float) -> None:
        self.flight_cost = cost
        self.budget_summary.flight_cost = cost

    def record_hotel_cost(self, cost: float) -> None:
        self.hotel_cost = cost
        self.budget_summary.hotel_cost = cost

    def record_activities_cost(self, cost: float) -> None:
        self.activities_cost = cost
        self.budget_summary.activities_cost = cost

    # ------------------------------------------------------------------
    # Replanning decisions
    # ------------------------------------------------------------------

    def try_shift_budget_to_flights(self) -> bool:
        """
        Attempt to shift 10% from hotels to flights.
        Returns True if the shift was possible, False if we've hit guardrails.
        """
        if self.flight_retries >= self.MAX_FLIGHT_RETRIES:
            return False
        new_alloc = shift_to_flights(self.allocation)
        if new_alloc is None:
            return False
        self.allocation = new_alloc
        self.budget_summary = BudgetSummary(allocation=self.allocation)
        self.flight_retries += 1
        self.warn(
            f"No flights found — shifted 10% from hotels to flights. "
            f"New flight budget: {format_usd(self.allocation.flights)}"
        )
        return True

    def try_shift_budget_to_hotels(self) -> bool:
        """Attempt to shift 10% from flights to hotels."""
        if self.hotel_retries >= self.MAX_HOTEL_RETRIES:
            return False
        new_alloc = shift_to_hotels(self.allocation)
        if new_alloc is None:
            return False
        self.allocation = new_alloc
        self.budget_summary = BudgetSummary(allocation=self.allocation)
        self.hotel_retries += 1
        self.warn(
            f"No hotels found — shifted 10% from flights to hotels. "
            f"New hotel budget: {format_usd(self.allocation.hotels)}"
        )
        return True

    def adjacent_dates(self, offset_days: int = 1) -> tuple[str, str]:
        """Return check-in/check-out shifted by ±offset_days."""
        new_in = self.request.depart_date + timedelta(days=offset_days)
        new_out = self.request.return_date + timedelta(days=offset_days)
        return new_in.isoformat(), new_out.isoformat()

    def is_over_budget(self) -> bool:
        return self.budget_summary.is_over_budget

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def emit(self, event_type: str, agent: str, message: str, data: Optional[dict] = None) -> dict:
        event = {
            "event_type": event_type,
            "agent": agent,
            "message": message,
            "data": data or {},
        }
        self.events.append(event)
        return event

    def budget_status(self) -> str:
        return self.budget_summary.describe()
