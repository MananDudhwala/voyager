"""
Demo: No flights — budget too tight, orchestrator reallocates from hotels and retries.

Run:
    python -m demo.run_no_flights
"""

from __future__ import annotations

import asyncio
import os
from datetime import date

os.environ["MOCK_SCENARIO"] = "no_flights"  # Force no flights

from orchestrator.agent import VoyagerOrchestrator
from shared.models import TripRequest


async def main():
    print("=" * 60)
    print("✈️  VOYAGER — No Flights Demo")
    print("    Scenario: all flights return empty → orchestrator reallocates")
    print("=" * 60 + "\n")

    request = TripRequest(
        origin="JFK",
        destination="Paris",
        depart_date=date(2026, 8, 10),
        return_date=date(2026, 8, 15),
        travelers=2,
        budget_usd=3000.0,
    )

    orchestrator = VoyagerOrchestrator()
    plan = await orchestrator.plan(request)

    print("\n" + "=" * 60)
    print("📋  RESULT")
    print("=" * 60)
    print(f"Status  : {plan.status.value}")
    print(f"Summary : {plan.summary}")
    if plan.warnings:
        print("\n⚠️  Warnings / Replan steps:")
        for w in plan.warnings:
            print(f"  - {w}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
