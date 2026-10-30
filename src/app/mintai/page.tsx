import { Suspense } from "react";
import { MintAIShell } from "@/components/mintai/mintai-shell";
import { Loader2 } from "lucide-react";

export const metadata = {
  title: "MintAI Intelligence Engine | SRMIST Examination Forecasting & Exam DNA",
  description: "Bayesian examination forecasts, recurring question archetypes, timed exam simulations, and verified Dr. E. Suresh & Gate Smashers study masterclasses for SRMIST Regulation 2021 students.",
};

export default function MintAIPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
          <div className="flex items-center gap-3 text-accent">
            <Loader2 className="w-6 h-6 animate-spin" />
            <span className="text-sm font-medium text-muted-foreground">
              Loading MintAI Intelligence Engine...
            </span>
          </div>
        </div>
      }
    >
      <MintAIShell />
    </Suspense>
  );
}
