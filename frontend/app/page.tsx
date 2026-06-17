"use client";
import { useRouter } from "next/navigation";
import { TripForm } from "@/components/trip-form/TripForm";
import { ScenarioSelector } from "@/components/scenario/ScenarioSelector";
import { createPlan } from "@/lib/api";
import type { TripRequestForm } from "@/lib/validations";
import { Globe, Zap, Shield } from "lucide-react";

export default function Home() {
  const router = useRouter();

  async function handleSubmit(data: TripRequestForm) {
    const { plan_id } = await createPlan(data);
    // Mark this plan as intentionally navigated-to (not a pop/direct-URL).
    // The plan page checks for this and redirects home if missing.
    sessionStorage.setItem("voyager_active_plan", plan_id);
    router.push(`/plan/${plan_id}`);
  }

  return (
    <main className="min-h-screen bg-background bg-mesh relative overflow-hidden">
      {/* Ambient glow orbs */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden" aria-hidden>
        <div className="absolute -top-40 -left-40 w-96 h-96 rounded-full bg-primary/10 blur-3xl" />
        <div className="absolute top-1/3 -right-32 w-80 h-80 rounded-full bg-accent/8 blur-3xl" />
        <div className="absolute bottom-0 left-1/3 w-72 h-72 rounded-full bg-chart-2/8 blur-3xl" />
      </div>

      <div className="relative z-10 max-w-5xl mx-auto px-4 pt-16 pb-24">
        {/* Header */}
        <div className="flex justify-between items-center mb-16">
          <div className="flex items-center gap-2">
            <Globe className="w-6 h-6 text-primary" />
            <span className="text-lg font-bold tracking-tight">Voyager</span>
          </div>
          <ScenarioSelector />
        </div>

        {/* Hero */}
        <div className="text-center mb-14">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass text-xs font-medium text-primary mb-6">
            <span className="live-dot w-1.5 h-1.5 rounded-full bg-primary inline-block" />
            Powered by Claude + Multi-Agent MCP
          </div>
          <h1 className="text-5xl md:text-6xl font-bold tracking-tight mb-4 leading-tight">
            Plan your India trip with{" "}
            <span className="text-gradient">AI agents</span>
          </h1>
          <p className="text-muted-foreground text-lg max-w-xl mx-auto">
            Tell us your city and budget in ₹. Our agents book IndiGo / Air India flights,
            pick the best Indian hotels, and build a weather-aware day-by-day itinerary.
          </p>
        </div>

        {/* Feature pills */}
        <div className="flex flex-wrap justify-center gap-3 mb-12">
          {[
            { icon: Zap, label: "IndiGo / Air India / SpiceJet" },
            { icon: Shield, label: "Monsoon-aware itinerary" },
            { icon: Globe, label: "Budget in ₹ — live reasoning" },
          ].map(({ icon: Icon, label }) => (
            <div key={label} className="flex items-center gap-2 px-4 py-2 rounded-full glass text-sm text-muted-foreground">
              <Icon className="w-4 h-4 text-primary" />
              {label}
            </div>
          ))}
        </div>

        {/* Form */}
        <TripForm onSubmit={handleSubmit} />
      </div>
    </main>
  );
}
