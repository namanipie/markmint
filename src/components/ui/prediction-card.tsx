// @ts-nocheck
"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Prediction } from "@/lib/types";
import { ConfidenceBadge } from "./confidence-badge";

export interface PredictionCardProps {
  prediction: Prediction;
  className?: string;
  onOpenIntelligence?: (topicName: string) => void;
}

export function PredictionCard({ prediction, className, onOpenIntelligence }: PredictionCardProps) {
  let progressColor = "bg-destructive";
  if (prediction.probability >= 75) progressColor = "bg-success";
  else if (prediction.probability >= 50) progressColor = "bg-warning";

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className={cn("glass rounded-2xl p-6 flex flex-col gap-4 border border-border/60 hover:border-accent/30 transition-all", className)}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-foreground">{prediction.topic}</h3>
          {prediction.reason_codes && prediction.reason_codes.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {prediction.reason_codes.slice(0, 2).map((rc) => (
                <span key={rc} className="text-[10px] bg-secondary px-1.5 py-0.5 rounded font-mono text-muted-foreground">
                  {rc.replace(/_/g, " ")}
                </span>
              ))}
            </div>
          )}
        </div>
        <ConfidenceBadge
          confidence={
            typeof prediction.confidence === "string"
              ? prediction.confidence
              : (prediction.confidence as number) >= 75
              ? "HIGH"
              : (prediction.confidence as number) >= 50
              ? "MEDIUM"
              : "LOW"
          }
        />
      </div>

      <div className="space-y-1">
        <div className="flex justify-between text-sm text-muted-foreground">
          <span>Historical Recurrence Likelihood</span>
          <span className="font-semibold text-foreground">{Math.round(prediction.probability)}%</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${prediction.probability}%` }}
            className={cn("h-full rounded-full", progressColor)}
          />
        </div>
        <p className="text-[11px] text-muted-foreground mt-1.5 italic">
          * Probabilistic estimate based on multi-year historical evidence, not certainty.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 rounded-xl bg-secondary/50 p-3">
        <div className="flex flex-col">
          <span className="text-xs text-muted-foreground">Paper Appearance</span>
          <span className="text-sm font-medium text-foreground">
            {prediction.evidence.papers_present} of {prediction.evidence.total_papers} papers
          </span>
        </div>
        <div className="flex flex-col">
          <span className="text-xs text-muted-foreground">Long Answers</span>
          <span className="text-sm font-medium text-foreground">
            {prediction.evidence.long_answer_count}
          </span>
        </div>
      </div>

      {/* Visual Historical Timeline */}
      {prediction.timeline && prediction.timeline.length > 0 ? (
        <div className="space-y-2 bg-secondary/20 p-3 rounded-xl border border-border/40">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span className="font-medium">Historical Timeline Sequence</span>
            <span className="text-[10px] font-mono">● = Present  ○ = Exam Held, Absent  ┄ = Gap Year</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {prediction.timeline.map((entry) => (
              <span
                key={entry.year}
                title={
                  entry.present
                    ? `Exam Present: Tested in ${entry.year}`
                    : entry.exam_exists === false
                    ? `No exam archived for ${entry.year} (unobserved gap year)`
                    : `Exam held in ${entry.year}, but this item was not examined`
                }
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs font-mono font-medium transition-colors",
                  entry.present
                    ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                    : entry.exam_exists === false
                    ? "bg-secondary/20 text-muted-foreground/40 border border-dashed border-border/30"
                    : "bg-secondary/40 text-muted-foreground/60 border border-border/30"
                )}
              >
                <span
                  className={cn(
                    "h-1.5 w-1.5 rounded-full",
                    entry.present
                      ? "bg-emerald-500"
                      : entry.exam_exists === false
                      ? "bg-transparent border border-muted-foreground/40"
                      : "bg-muted-foreground/30"
                  )}
                />
                {entry.year}
              </span>
            ))}
          </div>
        </div>
      ) : prediction.evidence.historicalYears && prediction.evidence.historicalYears.length > 0 ? (
        <div className="space-y-2">
          <span className="text-xs text-muted-foreground">Historical Appearances</span>
          <div className="flex flex-wrap gap-2">
            {prediction.evidence.historicalYears.map((year) => (
              <span key={year} className="inline-flex items-center gap-1 rounded-md bg-secondary px-2 py-1 text-xs text-muted-foreground">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                {year}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      {onOpenIntelligence && (
        <button
          onClick={() => onOpenIntelligence(prediction.topic)}
          className="w-full mt-1 py-2 px-3 rounded-xl bg-accent/10 hover:bg-accent/20 text-accent text-xs font-medium border border-accent/20 flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
        >
          <span>View Topic Intelligence Drilldown</span>
        </button>
      )}
    </motion.div>
  );
}

