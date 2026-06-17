"use client";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { tripRequestSchema, type TripRequestForm } from "@/lib/validations";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plane, MapPin, Calendar, Users, IndianRupee, ArrowRight, Loader2 } from "lucide-react";
import { useState } from "react";

const DESTINATIONS = [
  "Goa",
  "Jaipur",
  "Udaipur",
  "Manali",
  "Kochi",
  "Varanasi",
  "Leh",
  "Coorg",
  "Rishikesh",
  "Andaman",
];

const ORIGINS = [
  "DEL",  // Delhi
  "BOM",  // Mumbai
  "BLR",  // Bangalore
  "HYD",  // Hyderabad
  "MAA",  // Chennai
  "CCU",  // Kolkata
  "PNQ",  // Pune
  "AMD",  // Ahmedabad
  "COK",  // Kochi
  "GOI",  // Goa
];

const ORIGIN_LABELS: Record<string, string> = {
  DEL: "DEL — Delhi",
  BOM: "BOM — Mumbai",
  BLR: "BLR — Bangalore",
  HYD: "HYD — Hyderabad",
  MAA: "MAA — Chennai",
  CCU: "CCU — Kolkata",
  PNQ: "PNQ — Pune",
  AMD: "AMD — Ahmedabad",
  COK: "COK — Kochi",
  GOI: "GOI — Goa",
};

type Props = { onSubmit: (data: TripRequestForm) => Promise<void> };

export function TripForm({ onSubmit }: Props) {
  const [loading, setLoading] = useState(false);

  const { register, handleSubmit, control, watch, formState: { errors } } = useForm<TripRequestForm>({
    resolver: zodResolver(tripRequestSchema),
    defaultValues: {
      origin: "DEL",
      destination: "Goa",
      depart_date: "2026-08-10",
      return_date: "2026-08-15",
      travelers: 2,
      budget_inr: 50000,
    },
  });

  const budget = watch("budget_inr") || 50000;
  const flights = Math.round(budget * 0.4);
  const hotels = Math.round(budget * 0.4);
  const activities = Math.round(budget * 0.2);

  const fmt = (n: number) => `₹${n.toLocaleString("en-IN")}`;

  async function submit(data: TripRequestForm) {
    setLoading(true);
    try {
      await onSubmit(data);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit(submit)} className="glass-card rounded-2xl p-8 glow-sm space-y-8">
      {/* Row 1 — Origin / Destination */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <label className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
            <Plane className="w-3.5 h-3.5" /> From
          </label>
          <Controller
            name="origin"
            control={control}
            render={({ field }) => (
              <Select onValueChange={field.onChange} value={field.value}>
                <SelectTrigger id="origin" className="bg-secondary/50 border-border h-11">
                  <SelectValue placeholder="Origin airport" />
                </SelectTrigger>
                <SelectContent>
                  {ORIGINS.map((o) => (
                    <SelectItem key={o} value={o}>{ORIGIN_LABELS[o] ?? o}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
          {errors.origin && <p className="text-xs text-destructive">{errors.origin.message}</p>}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
            <MapPin className="w-3.5 h-3.5" /> Destination
          </label>
          <Controller
            name="destination"
            control={control}
            render={({ field }) => (
              <Select onValueChange={field.onChange} value={field.value}>
                <SelectTrigger id="destination" className="bg-secondary/50 border-border h-11">
                  <SelectValue placeholder="Where to?" />
                </SelectTrigger>
                <SelectContent>
                  {DESTINATIONS.map((d) => (
                    <SelectItem key={d} value={d}>{d}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
          {errors.destination && <p className="text-xs text-destructive">{errors.destination.message}</p>}
        </div>
      </div>

      {/* Row 2 — Dates */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <label htmlFor="depart_date" className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5" /> Departure
          </label>
          <input
            id="depart_date"
            type="date"
            {...register("depart_date")}
            className="w-full h-11 rounded-md bg-secondary/50 border border-border px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
          {errors.depart_date && <p className="text-xs text-destructive">{errors.depart_date.message}</p>}
        </div>

        <div className="space-y-2">
          <label htmlFor="return_date" className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5" /> Return
          </label>
          <input
            id="return_date"
            type="date"
            {...register("return_date")}
            className="w-full h-11 rounded-md bg-secondary/50 border border-border px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
          {errors.return_date && <p className="text-xs text-destructive">{errors.return_date.message}</p>}
        </div>
      </div>

      {/* Row 3 — Travelers */}
      <div className="space-y-2">
        <label htmlFor="travelers" className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
          <Users className="w-3.5 h-3.5" /> Travelers
        </label>
        <Controller
          name="travelers"
          control={control}
          render={({ field }) => (
            <Select onValueChange={(v) => field.onChange(Number(v))} value={String(field.value)}>
              <SelectTrigger id="travelers" className="bg-secondary/50 border-border h-11 w-44">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {[1,2,3,4,5,6].map((n) => (
                  <SelectItem key={n} value={String(n)}>{n} {n === 1 ? "traveler" : "travelers"}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
      </div>

      {/* Budget slider — INR */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
            <IndianRupee className="w-3.5 h-3.5" /> Total Budget
          </label>
          <span className="text-2xl font-bold text-primary">{fmt(budget)}</span>
        </div>

        <Controller
          name="budget_inr"
          control={control}
          render={({ field }) => (
            <Slider
              id="budget_slider"
              min={5000}
              max={500000}
              step={5000}
              value={[field.value]}
              onValueChange={(v) => field.onChange(Array.isArray(v) ? v[0] : v)}
              className="cursor-pointer"
            />
          )}
        />

        {/* Live split preview */}
        <div className="grid grid-cols-3 gap-3 pt-1">
          {[
            { label: "✈️ Flights", amount: flights, color: "text-chart-1" },
            { label: "🏨 Hotels", amount: hotels, color: "text-chart-2" },
            { label: "🗺️ Activities", amount: activities, color: "text-chart-3" },
          ].map(({ label, amount, color }) => (
            <div key={label} className="glass rounded-xl p-3 text-center">
              <p className="text-xs text-muted-foreground mb-1">{label}</p>
              <p className={`text-base font-bold ${color}`}>{fmt(amount)}</p>
              <p className="text-xs text-muted-foreground">
                {label.includes("Activities") ? "20%" : "40%"}
              </p>
            </div>
          ))}
        </div>
      </div>

      <Button
        id="plan-trip-btn"
        type="submit"
        disabled={loading}
        className="w-full h-12 text-base font-semibold gap-2 bg-primary hover:bg-primary/90 transition-all duration-200 glow-sm"
      >
        {loading ? (
          <><Loader2 className="w-4 h-4 animate-spin" /> Planning your trip…</>
        ) : (
          <>Plan my trip <ArrowRight className="w-4 h-4" /></>
        )}
      </Button>
    </form>
  );
}
