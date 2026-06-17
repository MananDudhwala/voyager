import { z } from "zod";

export const tripRequestSchema = z.object({
  origin: z.string().min(2, "Origin is required"),
  destination: z.string().min(2, "Destination is required"),
  depart_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Use YYYY-MM-DD format"),
  return_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Use YYYY-MM-DD format"),
  travelers: z.number().int().min(1).max(9),
  budget_inr: z.number().min(5000, "Minimum budget is ₹5,000"),
});

export type TripRequestForm = z.infer<typeof tripRequestSchema>;

export type OrchestratorEvent = {
  event_type: "thinking" | "tool_call" | "tool_result" | "replan" | "done" | "error";
  agent: "orchestrator" | "flight_agent" | "hotel_agent" | "itinerary_agent";
  message: string;
  data?: Record<string, unknown>;
};

export type FlightOption = {
  flight_id: string;
  airline: string;
  flight_number: string;
  origin: string;
  destination: string;
  depart_time: string;
  arrive_time: string;
  duration_minutes: number;
  stops: number;
  travel_class: string;
  price_per_person: number;
  total_price: number;
  baggage_included: boolean;
  available_seats: number;
};

export type HotelOption = {
  hotel_id: string;
  name: string;
  city: string;
  tier: "budget" | "midscale" | "upscale" | "luxury";
  star_rating: number;
  price_per_night: number;
  total_price: number;
  nights: number;
  amenities: string[];
  cancellation_policy: string;
  available: boolean;
};

export type POI = {
  poi_id: string;
  name: string;
  city: string;
  category: string;
  description: string;
  latitude: number;
  longitude: number;
  estimated_duration_minutes: number;
  entry_fee_inr: number;
  is_indoor: boolean;
  rating: number;
};

export type DayPlan = {
  date: string;
  weather: {
    condition: string;
    temp_high_c: number;
    temp_low_c: number;
    precipitation_mm: number;
    is_outdoor_friendly: boolean;
  };
  pois: POI[];
  travel_legs: Array<{ origin: string; destination: string; duration_minutes: number }>;
  daily_activities_cost_inr: number;
  weather_note: string;
};

export type TripPlan = {
  plan_id: string;
  status: "pending" | "planning" | "completed" | "failed" | "needs_input";
  currency: string;
  flight_outbound: FlightOption | null;
  flight_return: FlightOption | null;
  hotel: HotelOption | null;
  itinerary: { city: string; days: DayPlan[]; total_activities_cost_usd: number } | null;
  budget: { total: number; flights: number; hotels: number; activities: number };
  total_cost: number;
  savings: number;
  summary: string;
  warnings: string[];
};
