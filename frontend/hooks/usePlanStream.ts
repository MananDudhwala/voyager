"use client";
import { useEffect, useRef } from "react";
import { useVoyagerStore } from "@/lib/store";
import { streamPlan } from "@/lib/sse";
import { getPlan } from "@/lib/api";

export function usePlanStream(planId: string | null) {
  const { startPlanning, addEvent, setPlan, setError } = useVoyagerStore();
  const cleanupRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    if (!planId) return;
    startPlanning(planId);

    const cleanup = streamPlan(planId, {
      onEvent: addEvent,
      onPlanComplete: setPlan,
      onError: (err) => {
        setError(err);
        // Try to fetch final plan anyway
        getPlan(planId)
          .then(setPlan)
          .catch(() => {});
      },
    });

    cleanupRef.current = cleanup;
    return cleanup;
  }, [planId]); // eslint-disable-line react-hooks/exhaustive-deps
}
