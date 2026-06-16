"""
Budget math utilities for the Voyager orchestrator.
Handles allocation, reallocation, and constraint checking.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.models import BudgetAllocation


# Default budget split percentages
DEFAULT_FLIGHTS_PCT = 0.40
DEFAULT_HOTELS_PCT = 0.40
DEFAULT_ACTIVITIES_PCT = 0.20

# Minimum guardrails — never go below these fractions
MIN_FLIGHTS_PCT = 0.20
MIN_HOTELS_PCT = 0.20
MIN_ACTIVITIES_PCT = 0.05

# Reallocation step — how much to shift between buckets on each retry
REALLOC_STEP = 0.10


def default_allocation(total: float) -> BudgetAllocation:
    """Return the default 40/40/20 budget split."""
    return BudgetAllocation(
        total=total,
        flights=round(total * DEFAULT_FLIGHTS_PCT, 2),
        hotels=round(total * DEFAULT_HOTELS_PCT, 2),
        activities=round(total * DEFAULT_ACTIVITIES_PCT, 2),
    )


def shift_to_flights(allocation: BudgetAllocation, step: float = REALLOC_STEP) -> BudgetAllocation | None:
    """
    Move `step` fraction of the total from hotels to flights.
    Returns None if the shift would violate the hotel minimum guardrail.
    """
    shift_amount = round(allocation.total * step, 2)
    new_hotels = allocation.hotels - shift_amount
    new_flights = allocation.flights + shift_amount

    if new_hotels / allocation.total < MIN_HOTELS_PCT:
        return None  # Can't shift any more — at the floor

    return BudgetAllocation(
        total=allocation.total,
        flights=round(new_flights, 2),
        hotels=round(new_hotels, 2),
        activities=allocation.activities,
    )


def shift_to_hotels(allocation: BudgetAllocation, step: float = REALLOC_STEP) -> BudgetAllocation | None:
    """Move `step` fraction from flights to hotels."""
    shift_amount = round(allocation.total * step, 2)
    new_flights = allocation.flights - shift_amount
    new_hotels = allocation.hotels + shift_amount

    if new_flights / allocation.total < MIN_FLIGHTS_PCT:
        return None

    return BudgetAllocation(
        total=allocation.total,
        flights=round(new_flights, 2),
        hotels=round(new_hotels, 2),
        activities=allocation.activities,
    )


def is_within_budget(cost: float, budget: float, tolerance: float = 0.01) -> bool:
    """Return True if cost is within budget (with a small tolerance for rounding)."""
    return cost <= budget * (1 + tolerance)


def remaining_budget(total: float, flight_cost: float, hotel_cost: float) -> float:
    """How much is left for activities after flights and hotels."""
    return round(total - flight_cost - hotel_cost, 2)


def format_usd(amount: float) -> str:
    """Human-readable USD string."""
    return f"${amount:,.2f}"


@dataclass
class BudgetSummary:
    allocation: BudgetAllocation
    flight_cost: float = 0.0
    hotel_cost: float = 0.0
    activities_cost: float = 0.0

    @property
    def total_spent(self) -> float:
        return round(self.flight_cost + self.hotel_cost + self.activities_cost, 2)

    @property
    def remaining(self) -> float:
        return round(self.allocation.total - self.total_spent, 2)

    @property
    def is_over_budget(self) -> bool:
        return self.total_spent > self.allocation.total

    def describe(self) -> str:
        return (
            f"Budget: {format_usd(self.allocation.total)} | "
            f"Flights: {format_usd(self.flight_cost)} | "
            f"Hotel: {format_usd(self.hotel_cost)} | "
            f"Activities: {format_usd(self.activities_cost)} | "
            f"Remaining: {format_usd(self.remaining)}"
        )
