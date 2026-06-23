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
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from shared.cache import cache_get, cache_set, close_redis, get_redis, redis_ping
from shared.models import OrchestratorEvent, TripPlan, TripRequest

# ---------------------------------------------------------------------------
# Plan store
# ---------------------------------------------------------------------------
# In-memory sentinel: None means "planning in progress"; absent key = not found.
# Completed TripPlan objects are persisted in Redis (2-hour TTL) so they survive
# restarts, with the in-memory dict as an automatic fallback when Redis is down.

_plans_in_progress: set[str] = set()      # plan_ids currently being planned
_event_queues: dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)

_PLAN_TTL = 7200  # 2 hours
_PLAN_KEY_PREFIX = "voyager:plan"


async def _save_plan(plan_id: str, plan: TripPlan) -> None:
    """Persist a completed TripPlan to Redis (with in-memory fallback)."""
    key = f"{_PLAN_KEY_PREFIX}:{plan_id}"
    await cache_set(key, plan.model_dump(mode="json"), ttl=_PLAN_TTL)


async def _load_plan(plan_id: str) -> TripPlan | None | str:
    """
    Load a plan by ID.
    Returns:
      - ``"in_progress"`` if planning is still running
      - a ``TripPlan`` instance if complete
      - ``None`` if not found
    """
    if plan_id in _plans_in_progress:
        return "in_progress"
    key = f"{_PLAN_KEY_PREFIX}:{plan_id}"
    data = await cache_get(key)
    if data is None:
        return None
    return TripPlan.model_validate(data)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_redis()  # warm the Redis pool; fast now that Redis is running
    yield
    await close_redis()


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
async def health():
    redis_status = "ok" if await redis_ping() else "unavailable"
    return {"status": "ok", "service": "voyager-api", "redis": redis_status}


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
    _plans_in_progress.add(plan_id)  # mark as in-progress

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
            await _save_plan(plan_id, plan)
        except BaseException as e:
            import sys
            import traceback
            # Print full traceback to server stderr for debugging
            traceback.print_exc(file=sys.stderr)
            # Unwrap ExceptionGroup so the frontend gets the real error message
            try:
                from orchestrator.agent import _unwrap_exception
                msg = _unwrap_exception(e)
            except Exception:
                msg = str(e) or repr(e)
            err_event = OrchestratorEvent(
                event_type="error",
                agent="orchestrator",
                message=msg,
            )
            await _event_queues[plan_id].put(err_event)
        finally:
            _plans_in_progress.discard(plan_id)  # planning done (success or error)
            # Signal stream end
            await _event_queues[plan_id].put(None)

    asyncio.create_task(run_planning())

    return {"plan_id": plan_id, "status": "planning"}


@app.get("/plan/{plan_id}")
async def get_plan(plan_id: str):
    """Retrieve the completed TripPlan."""
    result = await _load_plan(plan_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    if result == "in_progress":
        return {"plan_id": plan_id, "status": "planning"}
    return result.model_dump()


# ---------------------------------------------------------------------------
# SSE stream
# ---------------------------------------------------------------------------

@app.get("/stream/{plan_id}")
async def stream_plan(plan_id: str):
    """
    Server-Sent Events stream of OrchestratorEvents for a planning run.
    Emits JSON-encoded events; closes when planning completes.
    """
    # Accept both in-progress (sentinel) and completed (Redis) plan IDs
    if plan_id not in _event_queues and plan_id not in _plans_in_progress:
        # check Redis in case this is a reconnect for a completed plan
        result = await _load_plan(plan_id)
        if result is None:
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
        result = await _load_plan(plan_id)
        if isinstance(result, TripPlan):
            yield {
                "event": "plan_complete",
                "data": result.model_dump_json(),
            }

    return EventSourceResponse(event_generator())



# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------


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
