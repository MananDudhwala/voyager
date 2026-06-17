"use client";
import { useEffect, useRef } from "react";
import { useVoyagerStore } from "@/lib/store";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import type { OrchestratorEvent } from "@/lib/validations";

const AGENT_COLORS: Record<string, string> = {
  orchestrator: "text-primary",
  flight_agent: "text-chart-2",
  hotel_agent: "text-chart-3",
  itinerary_agent: "text-chart-5",
};

const EVENT_ICONS: Record<string, string> = {
  thinking: "💭",
  tool_call: "🔧",
  tool_result: "✅",
  replan: "🔄",
  done: "🎉",
  error: "❌",
};

const EVENT_BADGE: Record<string, string> = {
  thinking: "secondary",
  tool_call: "outline",
  tool_result: "default",
  replan: "destructive",
  done: "default",
  error: "destructive",
};

export function OrchestratorLog() {
  const events = useVoyagerStore((s) => s.events);
  const status = useVoyagerStore((s) => s.status);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events.length]);

  return (
    <div className="glass-card rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-border">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold">Agent Reasoning</span>
          {status === "planning" && (
            <span className="live-dot w-2 h-2 rounded-full bg-primary inline-block" />
          )}
        </div>
        <span className="text-xs text-muted-foreground">{events.length} events</span>
      </div>

      <ScrollArea className="h-80">
        <div className="p-4 space-y-2.5">
          {events.length === 0 ? (
            <div className="flex items-center justify-center h-24 text-muted-foreground text-sm">
              <div className="shimmer w-full h-full rounded-lg" />
            </div>
          ) : (
            events.map((ev, i) => <EventRow key={i} event={ev} index={i} />)
          )}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>
    </div>
  );
}

function EventRow({ event, index }: { event: OrchestratorEvent; index: number }) {
  const agentColor = AGENT_COLORS[event.agent] ?? "text-foreground";
  const icon = EVENT_ICONS[event.event_type] ?? "•";

  return (
    <div
      className="animate-slide-in flex gap-3 text-sm"
      style={{ animationDelay: `${Math.min(index * 20, 200)}ms` }}
    >
      <span className="shrink-0 w-5 text-center">{icon}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className={`text-xs font-medium ${agentColor}`}>{event.agent}</span>
          <Badge variant={EVENT_BADGE[event.event_type] as "secondary" | "outline" | "default" | "destructive"} className="h-4 text-[10px] px-1.5">
            {event.event_type}
          </Badge>
        </div>
        <p className="text-muted-foreground leading-relaxed break-words">{event.message}</p>
      </div>
    </div>
  );
}
