"""
Demo: Budget overrun — prices inflated 1.8x, orchestrator surfaces the overrun and asks user.

Run:
    python -m demo.run_budget_overrun
"""

from __future__ import annotations

import asyncio
import os
from datetime import date

os.environ["MOCK_SCENARIO"] = "budget_overrun"

from shared.models import TripRequest
from orchestrator.agent import VoyagerOrchestrator


async def main():
    print("=" * 60)
    print("💸  VOYAGER — Budget Overrun Demo")
    print("    Scenario: prices inflated 1.8x → orchestrator asks user to adjust")
    print("=" * 60 + "\n")

    request = TripRequest(
        origin="JFK",
        destination="Paris",
        depart_date=date(2026, 8, 10),
        return_date=date(2026, 8, 15),
        travelers=2,
        budget_usd=2000.0,  # Deliberately tight budget
    )

    orchestrator = VoyagerOrchestrator()
    plan = await orchestrator.plan(request)

    print("\n" + "=" * 60)
    print("📋  RESULT")
    print("=" * 60)
    print(f"Status     : {plan.status.value}")
    print(f"Total cost : ${plan.total_cost:,.2f}")
    print(f"Budget     : ${request.budget_usd:,.2f}")
    print(f"Over by    : ${max(0, plan.total_cost - request.budget_usd):,.2f}")
    print(f"Summary    : {plan.summary}")
    if plan.warnings:
        print("\n⚠️  Warnings:")
        for w in plan.warnings:
            print(f"  - {w}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
