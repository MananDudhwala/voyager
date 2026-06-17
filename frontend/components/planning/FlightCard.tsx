"use client";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { FlightOption } from "@/lib/validations";
import { Plane, Clock, Luggage, ArrowRight } from "lucide-react";

type Props = { flight: FlightOption; label?: string };

const fmt = (n: number) => `₹${Math.round(n).toLocaleString("en-IN")}`;

export function FlightCard({ flight, label = "Flight" }: Props) {
  const hours = Math.floor(flight.duration_minutes / 60);
  const mins = flight.duration_minutes % 60;

  return (
    <Card className="glass-card border-0 rounded-2xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Plane className="w-4 h-4 text-primary" />
          <span className="text-xs font-medium text-muted-foreground">{label}</span>
        </div>
        <div className="text-right">
          <p className="text-xl font-bold text-primary">{fmt(flight.total_price)}</p>
          <p className="text-xs text-muted-foreground">{fmt(flight.price_per_person)}/person</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="text-center">
          <p className="text-2xl font-bold">{flight.origin}</p>
          <p className="text-xs text-muted-foreground">{flight.depart_time}</p>
        </div>
        <div className="flex-1 flex flex-col items-center gap-1">
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="w-3 h-3" />
            {hours}h {mins}m
          </div>
          <div className="w-full flex items-center gap-1">
            <div className="flex-1 h-px bg-border" />
            <ArrowRight className="w-3 h-3 text-muted-foreground shrink-0" />
            <div className="flex-1 h-px bg-border" />
          </div>
          <Badge variant="outline" className="text-[10px] h-4 px-1.5">
            {flight.stops === 0 ? "Direct" : `${flight.stops} stop${flight.stops > 1 ? "s" : ""}`}
          </Badge>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold">{flight.destination}</p>
          <p className="text-xs text-muted-foreground">{flight.arrive_time}</p>
        </div>
      </div>

      <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t border-border">
        <span className="font-medium text-foreground">{flight.airline} · {flight.flight_number}</span>
        <div className="flex items-center gap-1">
          <Luggage className="w-3 h-3" />
          {flight.baggage_included ? "Baggage included" : "No baggage"}
        </div>
      </div>
    </Card>
  );
}
