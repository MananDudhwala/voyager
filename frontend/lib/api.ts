import type { TripRequestForm, TripPlan } from "./validations";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function createPlan(data: TripRequestForm): Promise<{ plan_id: string }> {
  const res = await fetch(`${BASE}/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getPlan(planId: string): Promise<TripPlan> {
  const res = await fetch(`${BASE}/plan/${planId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listScenarios(): Promise<string[]> {
  const res = await fetch(`${BASE}/scenarios`);
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return data.scenarios ?? [];
}

export async function activateScenario(name: string): Promise<void> {
  await fetch(`${BASE}/scenarios/activate/${name}`, { method: "POST" });
}

export async function deactivateScenario(): Promise<void> {
  await fetch(`${BASE}/scenarios/deactivate`, { method: "POST" });
}
