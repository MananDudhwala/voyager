"""
Demo: Happy path — Delhi → Goa, 5 days, ₹50,000, 2 travelers (Indian context).

Run:
    python -m demo.run_happy_path
"""

from __future__ import annotations

import asyncio
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
os.environ.pop("MOCK_SCENARIO", None)

from orchestrator.agent import VoyagerOrchestrator  # noqa: E402
from shared.models import TripRequest  # noqa: E402


async def main():
    print("=" * 60)
    print("🌍  VOYAGER — Happy Path Demo (India)")
    print("    Delhi → Goa, 5 nights, ₹50,000, 2 travelers")
    print("=" * 60 + "\n")

    request = TripRequest(
        origin="DEL",
        destination="Goa",
        depart_date=date(2026, 8, 10),
        return_date=date(2026, 8, 15),
        travelers=2,
        budget_usd=50000.0,  # INR stored in budget_usd field
    )

    orchestrator = VoyagerOrchestrator()
    plan = await orchestrator.plan(request)

    print("\n" + "=" * 60)
    print("📋  FINAL PLAN")
    print("=" * 60)
    print(f"Status   : {plan.status.value}")
    print(f"Currency : {plan.currency}")
    print(f"Summary  : {plan.summary}")
    print(f"Total    : ₹{plan.total_cost:,.0f} / ₹{request.budget_usd:,.0f} budget")
    print(f"Savings  : ₹{plan.savings:,.0f}")

    if plan.warnings:
        print("\n⚠️  Warnings:")
        for w in plan.warnings:
            print(f"  - {w}")

    print("\n✈️  Outbound Flight:")
    if plan.flight_outbound:
        f = plan.flight_outbound
        print(f"  {f.airline} {f.flight_number} | {f.origin}→{f.destination} | ₹{f.total_price:,.0f}")

    print("\n🏨  Hotel:")
    if plan.hotel:
        h = plan.hotel
        print(f"  {h.name} ({h.tier.value}, ⭐{h.star_rating}) | ₹{h.price_per_night:,.0f}/night × {h.nights} nights")

    print("\n📅  Itinerary:")
    if plan.itinerary and isinstance(plan.itinerary, dict):
        for day in plan.itinerary.get("days", []):
            weather = day.get("weather", {})
            print(f"\n  {day['date']} — {weather.get('condition', '?')} {day.get('weather_note', '')}")
            for poi in day.get("pois", []):
                fee = poi.get("entry_fee_usd", 0)
                fee_str = f"₹{fee:.0f}" if fee > 0 else "Free"
                print(f"    • {poi['name']} ({poi['category']}) — {fee_str}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
