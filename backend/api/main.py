"""
Voyager Backend API — main FastAPI application.

Provides:
  POST /plan            → start a planning run, return plan_id
  GET  /stream/{plan_id} → SSE stream of OrchestratorEvents
  GET  /scenarios        → list available demo scenarios
  POST /scenarios/{name} → activate a scenario

Run:
    uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from shared.models import TripRequest, TripPlan, OrchestratorEvent


# ---------------------------------------------------------------------------
# In-memory store for running/completed plans
# ---------------------------------------------------------------------------

_plans: dict[str, TripPlan | None] = {}
_event_queues: dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Voyager API",
    description="Backend API for the Voyager multi-agent trip planner",
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
    return {"status": "ok", "service": "voyager-api"}


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------

class PlanRequestBody(BaseModel):
    origin: str
    destination: str
    depart_date: str
    return_date: str
    travelers: int = 1
    budget_inr: float


@app.post("/plan")
async def create_plan(body: PlanRequestBody):
    """
    Start a planning run.
    Returns plan_id immediately; stream progress via GET /stream/{plan_id}.
    """
    from datetime import date

    plan_id = str(uuid.uuid4())
    _plans[plan_id] = None  # sentinel: planning in progress

    request = TripRequest(
        origin=body.origin,
        destination=body.destination,
        depart_date=date.fromisoformat(body.depart_date),
        return_date=date.fromisoformat(body.return_date),
        travelers=body.travelers,
        budget_inr=body.budget_inr,
    )

    async def run_planning():
        try:
            from orchestrator.agent import VoyagerOrchestrator
            orchestrator = VoyagerOrchestrator()

            async def push_event(event: OrchestratorEvent):
                await _event_queues[plan_id].put(event)

            plan = await orchestrator.plan(request, event_callback=push_event)
            _plans[plan_id] = plan
        except Exception as e:
            err_event = OrchestratorEvent(
                event_type="error",
                agent="orchestrator",
                message=str(e),
            )
            await _event_queues[plan_id].put(err_event)
        finally:
            # Signal stream end
            await _event_queues[plan_id].put(None)

    asyncio.create_task(run_planning())

    return {"plan_id": plan_id, "status": "planning"}


@app.get("/plan/{plan_id}")
async def get_plan(plan_id: str):
    """Retrieve the completed TripPlan."""
    if plan_id not in _plans:
        raise HTTPException(status_code=404, detail="Plan not found")
    plan = _plans[plan_id]
    if plan is None:
        return {"plan_id": plan_id, "status": "planning"}
    return plan.model_dump()


# ---------------------------------------------------------------------------
# SSE stream
# ---------------------------------------------------------------------------

@app.get("/stream/{plan_id}")
async def stream_plan(plan_id: str):
    """
    Server-Sent Events stream of OrchestratorEvents for a planning run.
    Emits JSON-encoded events; closes when planning completes.
    """
    if plan_id not in _plans:
        raise HTTPException(status_code=404, detail="Plan not found")

    queue = _event_queues[plan_id]

    async def event_generator():
        while True:
            event = await queue.get()
            if event is None:
                break
            yield {
                "event": event.event_type,
                "data": json.dumps({
                    "agent": event.agent,
                    "message": event.message,
                    "data": event.data,
                }),
            }
        # Send final plan snapshot
        plan = _plans.get(plan_id)
        if plan:
            yield {
                "event": "plan_complete",
                "data": plan.model_dump_json(),
            }

    return EventSourceResponse(event_generator())


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

from pathlib import Path

SCENARIOS_DIR = Path(__file__).parent.parent / "mock" / "scenarios"


@app.get("/scenarios")
def list_scenarios():
    names = [p.stem for p in SCENARIOS_DIR.glob("*.json")]
    return {"scenarios": names}


@app.get("/scenarios/{name}")
def get_scenario(name: str):
    path = SCENARIOS_DIR / f"{name}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Scenario not found")
    return json.loads(path.read_text())


@app.post("/scenarios/activate/{name}")
def activate_scenario(name: str):
    """Set the active scenario (affects new planning runs)."""
    path = SCENARIOS_DIR / f"{name}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Scenario not found")
    os.environ["MOCK_SCENARIO"] = name
    return {"active_scenario": name}


@app.post("/scenarios/deactivate")
def deactivate_scenario():
    """Clear the active scenario (happy path)."""
    os.environ.pop("MOCK_SCENARIO", None)
    return {"active_scenario": None}
