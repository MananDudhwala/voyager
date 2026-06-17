"use client";
import type { DayPlan } from "@/lib/validations";
import { Badge } from "@/components/ui/badge";

const CONDITION_ICON: Record<string, string> = {
  sunny: "☀️",
  partly_cloudy: "⛅",
  cloudy: "☁️",
  rainy: "🌧️",
  stormy: "⛈️",
  snowy: "❄️",
};

const CATEGORY_ICON: Record<string, string> = {
  museum: "🏛️",
  park: "🌿",
  restaurant: "🍽️",
  landmark: "🗺️",
  beach: "🏖️",
  shopping: "🛍️",
  entertainment: "🎭",
  religious: "⛪",
  sport: "⚽",
};

type Props = { days: DayPlan[] };

export function ItineraryTimeline({ days }: Props) {
  return (
    <div className="glass-card rounded-2xl overflow-hidden">
      <div className="px-5 py-4 border-b border-border">
        <h3 className="text-sm font-semibold">📅 Day-by-Day Itinerary</h3>
      </div>
      <div className="divide-y divide-border">
        {days.map((day, i) => {
          const weather = day.weather ?? {};
          const icon = CONDITION_ICON[weather.condition ?? ""] ?? "🌤️";
          const isRainy = !weather.is_outdoor_friendly;

          return (
            <div key={day.date} className="p-5 space-y-3 animate-slide-in" style={{ animationDelay: `${i * 60}ms` }}>
              {/* Day header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-muted-foreground uppercase tracking-widest">
                    Day {i + 1}
                  </span>
                  <span className="text-sm font-semibold">
                    {new Date(day.date).toLocaleDateString("en-US", { weekday: "long", month: "short", day: "numeric" })}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-lg">{icon}</span>
                  {weather.temp_high_c !== undefined && (
                    <span className="text-xs text-muted-foreground">{weather.temp_high_c}°C</span>
                  )}
                  {isRainy && (
                    <Badge variant="secondary" className="text-[10px] h-4 px-1.5 text-chart-4">
                      Indoor day
                    </Badge>
                  )}
                </div>
              </div>

              {/* Weather note */}
              {day.weather_note && (
                <p className="text-xs text-muted-foreground italic">{day.weather_note}</p>
              )}

              {/* POI list */}
              <div className="space-y-2">
                {day.pois.map((poi, pi) => (
                  <div key={poi.poi_id ?? pi} className="flex items-start gap-3 pl-3 border-l-2 border-primary/30">
                    <span className="text-base shrink-0">{CATEGORY_ICON[poi.category] ?? "📍"}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-medium leading-tight">{poi.name}</p>
                        {poi.entry_fee_inr > 0 && (
                          <span className="text-xs text-muted-foreground shrink-0">
                            ₹{poi.entry_fee_inr.toLocaleString("en-IN")}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground line-clamp-1">{poi.description}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="outline" className="text-[10px] h-4 px-1.5 capitalize">{poi.category}</Badge>
                        <span className="text-[10px] text-muted-foreground">~{poi.estimated_duration_minutes}min</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Daily cost */}
              {day.daily_activities_cost_inr > 0 && (
                <p className="text-xs text-muted-foreground text-right">
                  Day total: <span className="font-semibold text-foreground">
                    ₹{day.daily_activities_cost_inr.toLocaleString("en-IN")}
                  </span>
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
