"use client";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import type { TripPlan } from "@/lib/validations";

type Props = { plan: TripPlan };

const COLORS = ["hsl(295,60%,65%)", "hsl(185,55%,55%)", "hsl(85,60%,55%)", "hsl(15,60%,60%)"];

const fmt = (n: number) => `₹${Math.round(n).toLocaleString("en-IN")}`;

export function BudgetBreakdown({ plan }: Props) {
  const flightCost = (plan.flight_outbound?.total_price ?? 0) + (plan.flight_return?.total_price ?? 0);
  const hotelCost = plan.hotel?.total_price ?? 0;
  const activitiesCost = plan.itinerary?.total_activities_cost_usd ?? 0;

  // Budget may be missing while plan is still streaming
  if (!plan.budget) return null;

  const remaining = Math.max(0, plan.budget.total - plan.total_cost);

  const data = [
      { name: "Flights", value: Math.round(flightCost) },
    { name: "Hotel", value: Math.round(hotelCost) },
    { name: "Activities", value: Math.round(activitiesCost) },
    { name: "Savings", value: Math.round(remaining) },
  ].filter((d) => d.value > 0);

  return (
    <div className="glass-card rounded-2xl p-6">
      <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
        💰 Budget Breakdown
        <span className="text-muted-foreground font-normal">
          {fmt(plan.total_cost)} of {fmt(plan.budget.total)}
        </span>
      </h3>

      <div className="flex flex-col md:flex-row items-center gap-6">
        <ResponsiveContainer width={180} height={180}>
          <PieChart>
            <Pie data={data} cx="50%" cy="50%" innerRadius={55} outerRadius={80} paddingAngle={3} dataKey="value">
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} strokeWidth={0} />
              ))}
            </Pie>
            <Tooltip
              formatter={(v) => [fmt(Number(v)), ""]}
              contentStyle={{ background: "oklch(0.16 0.025 265)", border: "1px solid oklch(1 0 0/10%)", borderRadius: 8, fontSize: 12 }}
            />
          </PieChart>
        </ResponsiveContainer>

        <div className="flex-1 space-y-3 w-full">
          {data.map((d, i) => (
            <div key={d.name} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: COLORS[i % COLORS.length] }} />
                <span className="text-sm text-muted-foreground">{d.name}</span>
              </div>
              <span className="text-sm font-semibold">{fmt(d.value)}</span>
            </div>
          ))}

          {plan.savings > 0 && (
            <div className="mt-3 pt-3 border-t border-border">
              <p className="text-xs text-chart-2 font-medium">
                🎉 Saving {fmt(plan.savings)} under budget!
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
