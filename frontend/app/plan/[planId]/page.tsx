"use client";
import { use, useEffect } from "react";
import { useRouter } from "next/navigation";
import { usePlanStream } from "@/hooks/usePlanStream";
import { useVoyagerStore } from "@/lib/store";
import { OrchestratorLog } from "@/components/planning/OrchestratorLog";
import { FlightCard } from "@/components/planning/FlightCard";
import { HotelCard } from "@/components/planning/HotelCard";
import { ItineraryTimeline } from "@/components/planning/ItineraryTimeline";
import { BudgetBreakdown } from "@/components/planning/BudgetBreakdown";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Globe, ArrowLeft, AlertCircle } from "lucide-react";
import Link from "next/link";
import { Progress } from "@/components/ui/progress";

type Props = { params: Promise<{ planId: string }> };

export default function PlanPage({ params }: Props) {
  const { planId } = use(params);
  const router = useRouter();

  // Redirect to home if we landed here without going through the form
  // (direct URL, browser back/forward "pop", or page refresh).
  // NOTE: we don't delete the key here because React StrictMode runs effects
  // twice in dev — deleting on the first run causes the second run to redirect.
  // The key is overwritten naturally on each new plan creation.
  useEffect(() => {
    const activePlan = sessionStorage.getItem("voyager_active_plan");
    if (activePlan !== planId) {
      router.replace("/");
    }
  }, [planId, router]);

  // Connect to the SSE stream for this plan.
  usePlanStream(planId);

  const { status, plan, events, error } = useVoyagerStore();


  const progress = Math.min(
    100,
    status === "planning"
      ? Math.min(90, events.length * 8)
      : status === "completed"
        ? 100
        : 0
  );

  return (
    <main className="min-h-screen bg-background bg-mesh relative overflow-hidden">
      {/* Ambient orbs */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden" aria-hidden>
        <div className="absolute -top-32 -left-32 w-96 h-96 rounded-full bg-primary/8 blur-3xl" />
        <div className="absolute bottom-0 right-0 w-80 h-80 rounded-full bg-chart-2/8 blur-3xl" />
      </div>

      <div className="relative z-10 max-w-5xl mx-auto px-4 pt-10 pb-24">
        {/* Nav */}
        <div className="flex items-center justify-between mb-8">
          <Link href="/" className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
            <ArrowLeft className="w-4 h-4" />
            New trip
          </Link>
          <div className="flex items-center gap-2">
            <Globe className="w-5 h-5 text-primary" />
            <span className="font-bold">Voyager</span>
          </div>
          <StatusBadge status={status} />
        </div>

        {/* Progress bar while planning */}
        {status === "planning" && (
          <div className="mb-8 space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-2 text-muted-foreground">
                <span className="live-dot w-2 h-2 rounded-full bg-primary inline-block" />
                Agents planning your trip…
              </span>
              <span className="text-muted-foreground">{events.length} steps</span>
            </div>
            <Progress value={progress} className="h-1.5" />
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mb-6 flex items-center gap-3 px-4 py-3 rounded-xl border border-destructive/30 bg-destructive/10 text-sm text-destructive">
            <AlertCircle className="w-4 h-4 shrink-0" />
            {error}
          </div>
        )}

        {/* Warnings */}
        {plan?.warnings?.length ? (
          <div className="mb-6 space-y-2">
            {plan.warnings.map((w, i) => (
              <div key={i} className="flex items-start gap-2 px-4 py-2.5 rounded-xl glass text-sm text-chart-3">
                ⚠️ {w}
              </div>
            ))}
          </div>
        ) : null}

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Left — live log */}
          <div className="lg:col-span-2 space-y-6">
            <OrchestratorLog />
            {plan && <BudgetBreakdown plan={plan} />}
          </div>

          {/* Right — results */}
          <div className="lg:col-span-3 space-y-6">
            {plan ? (
              <>
                {/* Summary */}
                <div className="glass-card rounded-2xl p-6 glow-sm">
                  <p className="text-sm font-medium text-muted-foreground mb-1">Trip Summary</p>
                  <p className="text-foreground leading-relaxed">{plan.summary}</p>
                </div>

                {/* Tabs */}
                <Tabs defaultValue="flights">
                  <TabsList className="glass border-0 w-full">
                    <TabsTrigger value="flights" className="flex-1">✈️ Flights</TabsTrigger>
                    <TabsTrigger value="hotel" className="flex-1">🏨 Hotel</TabsTrigger>
                    <TabsTrigger value="itinerary" className="flex-1">📅 Itinerary</TabsTrigger>
                  </TabsList>

                  <TabsContent value="flights" className="space-y-4 mt-4">
                    {plan.flight_outbound ? (
                      <FlightCard flight={plan.flight_outbound} label="Outbound" />
                    ) : (
                      <EmptyState message="No outbound flight found" />
                    )}
                    {plan.flight_return ? (
                      <FlightCard flight={plan.flight_return} label="Return" />
                    ) : (
                      <EmptyState message="No return flight found" />
                    )}
                  </TabsContent>

                  <TabsContent value="hotel" className="mt-4">
                    {plan.hotel ? (
                      <HotelCard hotel={plan.hotel} />
                    ) : (
                      <EmptyState message="No hotel found" />
                    )}
                  </TabsContent>

                  <TabsContent value="itinerary" className="mt-4">
                    {plan.itinerary?.days?.length ? (
                      <ItineraryTimeline days={plan.itinerary.days} />
                    ) : (
                      <EmptyState message="No itinerary generated" />
                    )}
                  </TabsContent>
                </Tabs>
              </>
            ) : (
              /* Skeleton while planning */
              <div className="space-y-4">
                {[120, 100, 140].map((h, i) => (
                  <div key={i} className="glass-card rounded-2xl shimmer" style={{ height: h }} />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

function StatusBadge({ status }: { status: string }) {
  const MAP: Record<string, { label: string; class: string }> = {
    idle: { label: "Waiting", class: "" },
    planning: { label: "Planning…", class: "animate-pulse" },
    completed: { label: "Completed", class: "" },
    error: { label: "Error", class: "" },
    needs_input: { label: "Needs input", class: "" },
  };
  const s = MAP[status] ?? MAP.idle;
  return (
    <Badge
      variant={status === "completed" ? "default" : status === "error" ? "destructive" : "secondary"}
      className={`text-xs ${s.class}`}
    >
      {s.label}
    </Badge>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="glass-card rounded-2xl p-8 text-center text-sm text-muted-foreground">
      {message}
    </div>
  );
}
