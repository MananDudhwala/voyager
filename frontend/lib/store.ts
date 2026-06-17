import { create } from "zustand";
import type { OrchestratorEvent, TripPlan } from "./validations";

type PlanningStatus = "idle" | "planning" | "completed" | "error";

type VoyagerStore = {
  // Plan state
  planId: string | null;
  status: PlanningStatus;
  events: OrchestratorEvent[];
  plan: TripPlan | null;
  error: string | null;

  // Scenario
  activeScenario: string | null;

  // Actions
  startPlanning: (planId: string) => void;
  addEvent: (event: OrchestratorEvent) => void;
  setPlan: (plan: TripPlan) => void;
  setError: (err: string) => void;
  setScenario: (name: string | null) => void;
  reset: () => void;
};

export const useVoyagerStore = create<VoyagerStore>((set) => ({
  planId: null,
  status: "idle",
  events: [],
  plan: null,
  error: null,
  activeScenario: null,

  startPlanning: (planId) =>
    set({ planId, status: "planning", events: [], plan: null, error: null }),

  addEvent: (event) =>
    set((state) => ({ events: [...state.events, event] })),

  setPlan: (plan) =>
    set({ plan, status: "completed" }),

  setError: (error) =>
    set({ error, status: "error" }),

  setScenario: (activeScenario) =>
    set({ activeScenario }),

  reset: () =>
    set({ planId: null, status: "idle", events: [], plan: null, error: null }),
}));
