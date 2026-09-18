// @ts-nocheck
"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Prediction } from "@/lib/types";

export interface PredictionCardProps {
  prediction: Prediction;
  className?: string;
  onOpenIntelligence?: (topicName: string) => void;
}

export function PredictionCard({ prediction, className, onOpenIntelligence }: PredictionCardProps) {
  let progressColor = "bg-accent";
  if (prediction.probability >= 75) progressColor = "bg-emerald-600 dark:bg-emerald-500";
  else if (prediction.probability >= 50) progressColor = "bg-amber-500";

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className={cn("bg-card rounded-xl p-5 flex flex-col gap-5 border border-border hover:border-accent/30 transition-all shadow-sm", className)}
    >
      {/* Primary: Topic / Title & Expected Marks/Yield */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-foreground leading-tight">{prediction.topic}</h3>
        </div>
        <div className="flex flex-col items-end shrink-0">
          <span className="text-xl font-black text-foreground">{Math.round(prediction.probability)}%</span>
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-widest">Recurrence</span>
        </div>
      </div>

      {/* Secondary: Confidence & Core Stats */}
      <div className="flex items-center gap-4 text-sm border-b border-border/50 pb-4">
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: prediction.confidence === "HIGH" || prediction.confidence >= 75 ? "#10b981" : prediction.confidence === "MEDIUM" || prediction.confidence >= 50 ? "#f59e0b" : "#ef4444" }} />
          <span className="font-medium text-foreground">
            {typeof prediction.confidence === "string" ? prediction.confidence : prediction.confidence >= 75 ? "High" : prediction.confidence >= 50 ? "Medium" : "Low"} Confidence
          </span>
        </div>
        <div className="h-4 w-[1px] bg-border" />
        <div className="text-muted-foreground">
          {prediction.evidence.papers_present} / {prediction.evidence.total_papers} Papers
        </div>
        <div className="h-4 w-[1px] bg-border" />
        <div className="text-muted-foreground">
          {prediction.evidence.long_answer_count} Long Answers
        </div>
      </div>

      {/* Tertiary: Technical Metadata & Evidence */}
      <div className="flex flex-col gap-3">
        {prediction.timeline && prediction.timeline.length > 0 ? (
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] uppercase tracking-wider text-muted-foreground mr-2 font-semibold">History:</span>
            {prediction.timeline.map((entry) => (
              <span
                key={entry.year}
                title={
                  entry.present
                    ? `Exam Present: Tested in ${entry.year}`
                    : entry.exam_exists === false
                    ? `No exam archived for ${entry.year}`
                    : `Exam held in ${entry.year}, but not examined`
                }
                className={cn(
                  "inline-flex items-center justify-center rounded px-1.5 py-0.5 text-[10px] font-mono",
                  entry.present
                    ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 font-medium"
                    : "text-muted-foreground opacity-50"
                )}
              >
                {entry.year}
              </span>
            ))}
          </div>
        ) : prediction.evidence.historicalYears && prediction.evidence.historicalYears.length > 0 ? (
          <div className="flex flex-wrap items-center gap-1.5">
             <span className="text-[11px] uppercase tracking-wider text-muted-foreground mr-2 font-semibold">History:</span>
            {prediction.evidence.historicalYears.map((year) => (
              <span key={year} className="inline-flex items-center justify-center rounded px-1.5 py-0.5 text-[10px] font-mono bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 font-medium">
                {year}
              </span>
            ))}
          </div>
        ) : null}

        {prediction.reason_codes && prediction.reason_codes.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {prediction.reason_codes.map((rc) => (
              <span key={rc} className="text-[10px] text-muted-foreground opacity-70 font-mono">
                #{rc.toLowerCase()}
              </span>
            ))}
          </div>
        )}
      </div>

      {onOpenIntelligence && (
        <button
          onClick={() => onOpenIntelligence(prediction.topic)}
          className="w-full mt-2 py-2.5 px-3 rounded-lg bg-foreground text-background text-xs font-semibold hover:bg-foreground/90 transition-colors cursor-pointer"
        >
          View Evidence Drawer
        </button>
      )}
    </motion.div>
  );
}
