"use client";

import React, { useState, useEffect } from "react";
import { Check, X, MessageSquare, ThumbsUp, ThumbsDown } from "lucide-react";
import { submitBetaFeedback, hasGivenBetaFeedback, markBetaFeedbackGiven } from "@/lib/telemetry";

interface BetaFeedbackWidgetProps {
  courseCode?: string;
  hasMeaningfulUsage: boolean;
}

export function BetaFeedbackWidget({ courseCode, hasMeaningfulUsage }: BetaFeedbackWidgetProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [step, setStep] = useState<"ask" | "reason" | "thanks" | "closed">("ask");
  const [confusionReason, setConfusionReason] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    // Only display after student has engaged in meaningful usage (e.g. viewed intelligence or prediction)
    if (hasMeaningfulUsage && !hasGivenBetaFeedback() && step === "ask") {
      const timer = setTimeout(() => {
        setIsVisible(true);
      }, 1500); // 1.5s gentle delay so it never pops up jarringly
      return () => clearTimeout(timer);
    }
  }, [hasMeaningfulUsage, step]);

  if (!isVisible || step === "closed") return null;

  const handleThumbsUp = async () => {
    setIsSubmitting(true);
    await submitBetaFeedback(true, undefined, { course_code: courseCode });
    setIsSubmitting(false);
    setStep("thanks");
    setTimeout(() => {
      setIsVisible(false);
      setStep("closed");
    }, 2500);
  };

  const handleThumbsDown = () => {
    setStep("reason");
  };

  const handleReasonSubmit = async () => {
    setIsSubmitting(true);
    await submitBetaFeedback(false, confusionReason, { course_code: courseCode });
    setIsSubmitting(false);
    setStep("thanks");
    setTimeout(() => {
      setIsVisible(false);
      setStep("closed");
    }, 2500);
  };

  const handleDismiss = () => {
    markBetaFeedbackGiven();
    setIsVisible(false);
    setStep("closed");
  };

  return (
    <aside aria-label="Feedback" className="fixed bottom-5 right-5 z-40 max-w-xs sm:max-w-sm w-[calc(100vw-2.5rem)] rounded-xl border border-border/80 bg-card/95 backdrop-blur-md p-3.5 shadow-lg shadow-black/10 text-xs transition-all duration-300 animate-in fade-in slide-in-from-bottom-2">
      {step === "ask" && (
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-foreground font-medium">
            <span className="w-2 h-2 rounded-full bg-accent inline-block shrink-0" />
            <span>Was this forecast useful?</span>
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            <button
              onClick={handleThumbsUp}
              disabled={isSubmitting}
              className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-accent/10 hover:bg-accent/20 text-accent font-semibold transition-colors cursor-pointer"
            >
              <ThumbsUp className="w-3.5 h-3.5" />
              <span>Yes</span>
            </button>
            <button
              onClick={handleThumbsDown}
              disabled={isSubmitting}
              className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-secondary hover:bg-secondary/80 text-muted-foreground hover:text-foreground font-semibold transition-colors cursor-pointer"
            >
              <ThumbsDown className="w-3.5 h-3.5" />
              <span>No</span>
            </button>
            <button
              onClick={handleDismiss}
              className="p-1 text-muted-foreground hover:text-foreground rounded transition-colors ml-1"
              aria-label="Dismiss feedback"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {step === "reason" && (
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-foreground">What confused you?</span>
            <span className="text-[10px] text-muted-foreground">Optional</span>
          </div>
          <input
            type="text"
            value={confusionReason}
            onChange={(e) => setConfusionReason(e.target.value)}
            placeholder="e.g. Scope was unclear, missing specific unit..."
            className="w-full px-2.5 py-1.5 rounded-md bg-secondary/50 border border-border text-foreground text-xs focus:outline-none focus:border-accent/60 placeholder:text-muted-foreground/60"
            maxLength={200}
            autoFocus
            onKeyDown={(e) => {
              if (e.key === "Enter") handleReasonSubmit();
            }}
          />
          <div className="flex items-center justify-end gap-2 mt-1">
            <button
              onClick={() => handleReasonSubmit()}
              className="px-2 py-1 text-muted-foreground hover:text-foreground text-[11px]"
            >
              Skip
            </button>
            <button
              onClick={handleReasonSubmit}
              disabled={isSubmitting}
              className="px-3 py-1 rounded bg-foreground text-background font-medium hover:bg-foreground/90 transition-colors"
            >
              {isSubmitting ? "Sending..." : "Submit"}
            </button>
          </div>
        </div>
      )}

      {step === "thanks" && (
        <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-medium py-0.5">
          <Check className="w-4 h-4" />
          <span>Thank you! Your feedback helps calibrate MarkMint.</span>
        </div>
      )}
    </aside>
  );
}
