import type { OrchestratorEvent, TripPlan } from "./validations";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type StreamCallbacks = {
  onEvent: (event: OrchestratorEvent) => void;
  onPlanComplete: (plan: TripPlan) => void;
  onError: (err: string) => void;
};

export function streamPlan(planId: string, callbacks: StreamCallbacks): () => void {
  const url = `${BASE}/stream/${planId}`;
  const es = new EventSource(url);

  // Generic orchestrator events
  const AGENT_EVENTS = ["thinking", "tool_call", "tool_result", "replan", "done", "error"];

  AGENT_EVENTS.forEach((eventType) => {
    es.addEventListener(eventType, (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        callbacks.onEvent({ event_type: eventType as OrchestratorEvent["event_type"], ...data });
      } catch {
        // ignore parse errors
      }
    });
  });

  es.addEventListener("plan_complete", (e: MessageEvent) => {
    try {
      const plan: TripPlan = JSON.parse(e.data);
      callbacks.onPlanComplete(plan);
    } catch {
      callbacks.onError("Failed to parse final plan");
    }
    es.close();
  });

  // EventSource fires onerror on every transient disconnect/reconnect, not just
  // fatal failures. We tolerate a few consecutive errors before giving up so that
  // brief network hiccups don't permanently kill the stream.
  let consecutiveErrors = 0;
  const MAX_ERRORS = 3;

  es.onerror = () => {
    consecutiveErrors++;
    if (consecutiveErrors >= MAX_ERRORS) {
      callbacks.onError("Stream connection lost");
      es.close();
    }
    // else: let EventSource auto-reconnect
  };

  // Reset the error counter whenever we receive any successful message
  const resetErrors = () => { consecutiveErrors = 0; };
  AGENT_EVENTS.forEach((eventType) => es.addEventListener(eventType, resetErrors));
  es.addEventListener("plan_complete", resetErrors);

  // Return cleanup function
  return () => es.close();
}
