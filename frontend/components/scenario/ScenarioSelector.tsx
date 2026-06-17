"use client";
import { useEffect, useState } from "react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { listScenarios, activateScenario, deactivateScenario } from "@/lib/api";
import { useVoyagerStore } from "@/lib/store";
import { FlaskConical } from "lucide-react";

const SCENARIO_LABELS: Record<string, string> = {
  no_flights: "No flights",
  hotel_sold_out: "Hotel sold out",
  budget_overrun: "Budget overrun",
};

export function ScenarioSelector() {
  const [scenarios, setScenarios] = useState<string[]>([]);
  const { activeScenario, setScenario } = useVoyagerStore();

  useEffect(() => {
    listScenarios().then(setScenarios).catch(() => {});
  }, []);

  async function handleChange(value: string | null) {
    if (!value || value === "happy_path") {
      await deactivateScenario();
      setScenario(null);
    } else {
      await activateScenario(value);
      setScenario(value);
    }
  }

  return (
    <div className="flex items-center gap-2">
      {activeScenario && (
        <Badge variant="destructive" className="text-xs">
          Demo: {SCENARIO_LABELS[activeScenario] ?? activeScenario}
        </Badge>
      )}
      <Select onValueChange={handleChange} defaultValue="happy_path">
        <SelectTrigger id="scenario-select" className="w-44 h-8 text-xs glass border-border">
          <FlaskConical className="w-3 h-3 mr-1 text-muted-foreground" />
          <SelectValue placeholder="Test scenario" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="happy_path">✅ Happy path</SelectItem>
          {scenarios.map((s) => (
            <SelectItem key={s} value={s}>
              ⚠️ {SCENARIO_LABELS[s] ?? s}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
