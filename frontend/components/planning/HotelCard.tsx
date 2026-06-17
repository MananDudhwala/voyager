"use client";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { HotelOption } from "@/lib/validations";
import { Building2, Star, Wifi, Dumbbell, Coffee } from "lucide-react";

const TIER_COLORS: Record<string, string> = {
  budget: "text-chart-3",
  midscale: "text-chart-2",
  upscale: "text-chart-1",
  luxury: "text-chart-4",
};

const fmt = (n: number) => `₹${Math.round(n).toLocaleString("en-IN")}`;

const AMENITY_ICONS: Record<string, React.ReactNode> = {
  WiFi: <Wifi className="w-3 h-3" />,
  Gym: <Dumbbell className="w-3 h-3" />,
  Breakfast: <Coffee className="w-3 h-3" />,
};

export function HotelCard({ hotel }: { hotel: HotelOption }) {
  const tierColor = TIER_COLORS[hotel.tier] ?? "text-foreground";

  return (
    <Card className="glass-card border-0 rounded-2xl p-5 space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-2">
          <Building2 className="w-4 h-4 text-chart-3 shrink-0" />
          <div>
            <p className="font-semibold leading-tight">{hotel.name}</p>
            <p className="text-xs text-muted-foreground">{hotel.city}</p>
          </div>
        </div>
        <div className="text-right shrink-0">
          <p className="text-xl font-bold text-chart-3">{fmt(hotel.total_price)}</p>
          <p className="text-xs text-muted-foreground">{fmt(hotel.price_per_night)}/night · {hotel.nights}n</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Badge variant="outline" className={`text-xs capitalize ${tierColor}`}>
          {hotel.tier}
        </Badge>
        <div className="flex items-center gap-0.5">
          {Array.from({ length: 5 }).map((_, i) => (
            <Star
              key={i}
              className={`w-3 h-3 ${i < Math.round(hotel.star_rating) ? "fill-chart-3 text-chart-3" : "text-border"}`}
            />
          ))}
          <span className="text-xs text-muted-foreground ml-1">{hotel.star_rating}</span>
        </div>
      </div>

      {hotel.amenities.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {hotel.amenities.slice(0, 5).map((a) => (
            <div key={a} className="flex items-center gap-1 text-xs text-muted-foreground px-2 py-1 rounded-full glass">
              {AMENITY_ICONS[a] ?? null}
              {a}
            </div>
          ))}
        </div>
      )}

      <p className="text-xs text-muted-foreground border-t border-border pt-3">
        📋 {hotel.cancellation_policy}
      </p>
    </Card>
  );
}
