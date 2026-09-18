"use client";

import { PredictionItem } from "@/lib/types";
import { MathText } from "@/components/ui/math-text";
import { ArrowRight, Info, CheckCircle2 } from "lucide-react";

interface PredictionCardProps {
  prediction: PredictionItem;
  isFamilyMode: boolean;
  totalPapersAnalyzed: number;
  onWhyClick: () => void;
  onPracticeClick: () => void;
  onMarkDone?: () => void;
  studentStatus?: string;
}

export function PredictionCard({
  prediction: p,
  isFamilyMode,
  totalPapersAnalyzed,
  onWhyClick,
  onPracticeClick,
  onMarkDone,
  studentStatus
}: PredictionCardProps) {
  const distinctPapers = p.distinct_paper_count ?? p.papers_with_topic ?? 0;
  
  // Natural language explanations based on recurrence
  let explanation = "";
  if (distinctPapers >= 4) {
    explanation = "A highly recurring pattern across multiple past exams.";
  } else if (distinctPapers > 1) {
    explanation = "This has appeared in several past exam papers.";
  } else if (distinctPapers === 1) {
    explanation = "This appeared exactly once in the papers we analyzed.";
  } else {
    explanation = "Predicted as highly probable based on syllabus weighting.";
  }

  const marksStr = p.average_marks 
    ? `~${p.average_marks} marks` 
    : p.total_marks_observed 
      ? `~${Math.round(p.total_marks_observed)} marks` 
      : p.marks_seen 
        ? `~${Math.round(p.marks_seen)} marks` 
        : "";

  return (
    <div className="bg-card rounded-2xl p-6 border border-border shadow-sm hover:shadow-md hover:border-primary/30 transition-all duration-300 relative group overflow-hidden">
      {/* Subtle indicator bar on the left */}
      <div className={`absolute left-0 top-0 bottom-0 w-1 ${
        p.confidence === "HIGH" ? "bg-verified" : p.confidence === "MEDIUM" ? "bg-warning" : "bg-border"
      }`} />

      <div className="flex flex-col md:flex-row gap-6">
        <div className="flex-1 space-y-4">
          <div className="space-y-1.5">
            <h4 className="text-xl font-bold text-foreground leading-tight pr-4">
              <MathText content={p.name} />
            </h4>
            <div className="flex items-center gap-3 text-sm font-medium text-muted-foreground">
              {distinctPapers > 0 && (
                <span className={distinctPapers >= 3 ? "text-primary" : ""}>
                  Seen in {distinctPapers} {distinctPapers === 1 ? "paper" : "papers"}
                </span>
              )}
              {distinctPapers > 0 && marksStr && <span className="w-1 h-1 rounded-full bg-border" />}
              {marksStr && <span>{marksStr}</span>}
              {p.repetition_type === "EXACT_REPEAT" && (
                <>
                  <span className="w-1 h-1 rounded-full bg-border" />
                  <span className="text-highlight uppercase tracking-wider text-[10px] font-bold">Exact Repeat</span>
                </>
              )}
            </div>
          </div>
          
          <p className="text-sm text-muted-foreground/90 max-w-xl">
            {explanation}
          </p>
        </div>

        <div className="flex items-end md:items-center gap-3 shrink-0 mt-2 md:mt-0">
          {onMarkDone && (
            <button 
              onClick={onMarkDone}
              className={`p-2.5 rounded-full transition-colors ${
                studentStatus === "COMPLETED" 
                  ? "bg-verified/10 text-verified hover:bg-verified/20" 
                  : "bg-secondary text-muted-foreground hover:bg-secondary/80 hover:text-foreground"
              }`}
              title={studentStatus === "COMPLETED" ? "Mastered" : "Mark as done"}
            >
              <CheckCircle2 className="w-5 h-5" />
            </button>
          )}
          
          <button
            onClick={onWhyClick}
            className="px-4 py-2.5 rounded-xl font-bold bg-secondary text-foreground hover:bg-secondary/80 transition-colors flex items-center gap-2 text-sm"
          >
            <Info className="w-4 h-4" />
            <span>Why?</span>
          </button>
          
          <button
            onClick={onPracticeClick}
            className="px-4 py-2.5 rounded-xl font-bold bg-primary text-primary-foreground hover:bg-primary/90 transition-colors flex items-center gap-2 text-sm shadow-sm"
          >
            <span>Practice</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {/* Hidden Technical Drawer triggers via the Why button now */}
    </div>
  );
}
