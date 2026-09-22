"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  Target,
  Sparkles,
  BookOpen,
  Calendar,
  Layers,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Clock,
  Award,
  Hash,
  Activity,
  ArrowRight
} from "lucide-react";
import { getTopicIntelligence } from "@/lib/api";
import { TopicIntelligenceResponse } from "@/lib/types";
import { MathText } from "@/components/ui/math-text";
import { ConfidenceBadge } from "@/components/ui/confidence-badge";
import { Drawer } from "@/components/ui/drawer";

interface TopicIntelligenceModalProps {
  isOpen: boolean;
  onClose: () => void;
  courseId: number | string;
  topicId?: number | string | null;
  initialTopicName?: string;
}

export function TopicIntelligenceModal({
  isOpen,
  onClose,
  courseId,
  topicId,
  initialTopicName
}: TopicIntelligenceModalProps) {
  const [data, setData] = useState<TopicIntelligenceResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const targetIdentifier = topicId || initialTopicName;
    if (!isOpen || !targetIdentifier) {
      setData(null);
      return;
    }

    let active = true;
    setIsLoading(true);
    setError(null);

    getTopicIntelligence(courseId, targetIdentifier)
      .then((res) => {
        if (!active) return;
        setData(res);
      })
      .catch((err) => {
        if (!active) return;
        console.error("Failed to fetch topic intelligence", err);
        setError("Unable to load topic intelligence evidence. Please try again.");
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [isOpen, courseId, topicId, initialTopicName]);

  // Handle ESC key to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  
  return (
    <Drawer
      isOpen={isOpen}
      onClose={onClose}
      title={data?.topic_name || initialTopicName || "Topic Intelligence"}
      subtitle={
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-accent">
            Topic Intelligence Drilldown
          </span>
          {data?.unit && (
            <span className="inline-flex items-center rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium text-foreground">
              Unit {data.unit.number}: {data.unit.name}
            </span>
          )}
        </div>
      }
    >
      <div className="flex flex-col gap-6">

          {isLoading && (
            <div className="flex flex-col items-center justify-center py-16 space-y-4">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-accent border-t-transparent" />
              <p className="text-sm text-muted-foreground">Synthesizing topic evidence and MintAI forecast...</p>
            </div>
          )}

          {error && !isLoading && (
            <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-6 text-center">
              <AlertCircle className="mx-auto h-8 w-8 text-destructive mb-2" />
              <p className="text-sm font-medium text-destructive">{error}</p>
            </div>
          )}

          {data && !isLoading && (
            <>
              {/* "Why is MarkMint showing me this?" Concise Student Evidence Card */}
              <div className="rounded-2xl border border-accent/20 bg-accent/5 p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <HelpCircle className="h-5 w-5 text-accent" />
                    <h3 className="text-sm font-bold text-foreground">Why is MarkMint showing me this?</h3>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-accent/10 text-accent font-semibold border border-accent/20">
                    Empirical Evidence
                  </span>
                </div>

                {/* Top 4 Concise Evidence Badges */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                  <div className="rounded-xl bg-card border border-border/60 p-3">
                    <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground mb-0.5">
                      <Layers className="h-3.5 w-3.5 text-accent" />
                      <span>Paper Recurrence</span>
                    </div>
                    <div className="text-base font-bold text-foreground">
                      {data.repetition_metrics.paper_count} of {data.repetition_metrics.total_papers}
                    </div>
                    <div className="text-[10px] text-muted-foreground">
                      {Math.round(data.repetition_metrics.paper_coverage * 100)}% of past papers
                    </div>
                  </div>

                  <div className="rounded-xl bg-card border border-border/60 p-3">
                    <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground mb-0.5">
                      <Clock className="h-3.5 w-3.5 text-accent" />
                      <span>Last Seen</span>
                    </div>
                    <div className="text-base font-bold text-foreground">
                      {data.repetition_metrics.last_seen_year || "Historical"}
                    </div>
                    <div className="text-[10px] text-muted-foreground">
                      {data.repetition_metrics.first_seen_year ? `Active since ${data.repetition_metrics.first_seen_year}` : "Archived exams"}
                    </div>
                  </div>

                  <div className="rounded-xl bg-card border border-border/60 p-3">
                    <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground mb-0.5">
                      <Award className="h-3.5 w-3.5 text-accent" />
                      <span>Marks Profile</span>
                    </div>
                    <div className="text-base font-bold text-foreground">
                      ~{data.repetition_metrics.average_marks} Marks
                    </div>
                    <div className="text-[10px] text-muted-foreground">
                      Up to {data.repetition_metrics.max_marks}M per question
                    </div>
                  </div>

                  <div className="rounded-xl bg-card border border-border/60 p-3">
                    <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground mb-0.5">
                      <Activity className="h-3.5 w-3.5 text-accent" />
                      <span>Total Questions</span>
                    </div>
                    <div className="text-base font-bold text-foreground">
                      {data.repetition_metrics.question_count} Questions
                    </div>
                    <div className="text-[10px] text-muted-foreground">
                      {data.repetition_metrics.total_marks} total marks seen
                    </div>
                  </div>
                </div>

                {/* Plain-English Evidence Rationale */}
                <div className="rounded-xl bg-card/80 border border-border/60 p-3.5 space-y-2 text-xs">
                  <div className="font-semibold text-foreground flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-accent" />
                    <span>Evidence-Backed Explanation</span>
                  </div>
                  <ul className="space-y-1.5 text-muted-foreground list-disc list-inside">
                    <li>
                      <strong className="text-foreground">Tested in {data.repetition_metrics.paper_count} of {data.repetition_metrics.total_papers} papers:</strong> Appears in {Math.round(data.repetition_metrics.paper_coverage * 100)}% of archived examination papers for this course.
                    </li>
                    {data.repetition_metrics.last_seen_year && (
                      <li>
                        <strong className="text-foreground">Recency:</strong> Last examined in the <span className="font-mono text-foreground font-semibold">{data.repetition_metrics.last_seen_year}</span> exam session.
                      </li>
                    )}
                    {Object.keys(data.repetition_metrics.assessment_distribution || {}).length > 0 && (
                      <li>
                        <strong className="text-foreground">Assessment Cycles:</strong> Examined in {Object.entries(data.repetition_metrics.assessment_distribution).map(([k, v]) => `${k} (${v}x)`).join(", ")}.
                      </li>
                    )}
                    {data.question_families && data.question_families.length > 0 && (
                      <li>
                        <strong className="text-foreground">Question Families:</strong> Contains {data.question_families.length} recurring question {data.question_families.length === 1 ? "family" : "families"} with repeating archetypes.
                      </li>
                    )}
                    {data.repetition_metrics.total_papers <= 2 && (
                      <li className="text-amber-500">
                        <strong className="text-amber-500">Evidence Note:</strong> Only {data.repetition_metrics.total_papers} examination papers are currently archived for this specific cycle/course, so predictions have a smaller empirical sample size.
                      </li>
                    )}
                  </ul>
                </div>
              </div>

              {/* MintAI Forecast & Personalization Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Forecast Card */}
                <div className="rounded-2xl border border-accent/20 bg-accent/5 p-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-accent" />
                      <span className="text-sm font-semibold text-foreground">MintAI Objective Forecast</span>
                    </div>
                    <ConfidenceBadge confidence={data.forecast.confidence} />
                  </div>

                  <div>
                    <div className="flex justify-between text-xs text-muted-foreground mb-1.5">
                      <span>Paper Coverage Rate</span>
                      <span className="font-semibold text-foreground">
                        {data.repetition_metrics.paper_count} of {data.repetition_metrics.total_papers} papers
                      </span>
                    </div>
                    <div className="h-2.5 w-full overflow-hidden rounded-full bg-secondary">
                      <div
                        className="h-full rounded-full bg-accent transition-all duration-500"
                        style={{ width: `${data.forecast.probability}%` }}
                      />
                    </div>
                    <p className="text-[10px] text-muted-foreground mt-1 italic">
                      This bar shows what fraction of past papers contained this topic — not a prediction of future exam occurrence.
                    </p>
                  </div>

                  {data.timeline && data.timeline.length > 0 ? (
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>Chronological Exam Recurrence:</span>
                        <span className="text-[10px] font-mono">● = Topic Present  ○ = Exam Held, Absent</span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {data.timeline.map((entry) => (
                          <span
                            key={entry.year}
                            title={
                              entry.present
                                ? `Topic tested in ${entry.year}`
                                : entry.exam_exists === false
                                ? `No exam recorded in ${entry.year} (gap year)`
                                : `Exam held in ${entry.year}, but topic was not examined`
                            }
                            className={`px-2 py-0.5 rounded text-xs font-mono font-medium inline-flex items-center gap-1 ${
                              entry.present
                                ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                                : entry.exam_exists === false
                                ? "bg-muted/20 text-muted-foreground/40 border border-dashed border-border/30"
                                : "bg-secondary text-muted-foreground/60 border border-border/40"
                            }`}
                          >
                            <span
                              className={`h-1.5 w-1.5 rounded-full ${
                                entry.present
                                  ? "bg-emerald-500"
                                  : entry.exam_exists === false
                                  ? "bg-transparent border border-muted-foreground/40"
                                  : "bg-muted-foreground/30"
                              }`}
                            />
                            {entry.year}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : (
                    data.forecast.historical_years && data.forecast.historical_years.length > 0 && (
                      <div className="space-y-1">
                        <span className="text-xs text-muted-foreground">Observed Examination Years:</span>
                        <div className="flex flex-wrap gap-1.5">
                          {data.forecast.historical_years.map((yr) => (
                            <span key={yr} className="px-2 py-0.5 rounded bg-secondary text-xs font-mono font-semibold text-foreground">
                              {yr}
                            </span>
                          ))}
                        </div>
                      </div>
                    )
                  )}

                  <p className="text-xs text-muted-foreground italic bg-secondary/30 p-2.5 rounded-lg border border-border/40">
                    &ldquo;{data.forecast.rationale}&rdquo;
                  </p>
                </div>

                {/* Personalization Card */}
                <div className="rounded-2xl border border-border bg-secondary/30 p-5 space-y-4 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Target className="h-4 w-4 text-primary" />
                        <span className="text-sm font-semibold text-foreground">Student Action & Priority</span>
                      </div>
                      <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                        data.personalization.status === "MASTERED"
                          ? "bg-emerald-500/20 text-emerald-400"
                          : data.personalization.status === "IN_PROGRESS"
                          ? "bg-amber-500/20 text-amber-400"
                          : "bg-secondary text-muted-foreground"
                      }`}>
                        {data.personalization.status.replace("_", " ")}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
                      <span>Personalized Need Score:</span>
                      <span className="font-semibold text-foreground">{data.personalization.priority_score}%</span>
                    </div>

                    <div className="rounded-xl bg-card border border-border/60 p-3 flex items-start gap-2.5">
                      <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                      <div>
                        <span className="text-xs font-semibold text-foreground">Recommended Action:</span>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {data.personalization.recommended_action}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="text-[11px] text-muted-foreground border-t border-border/40 pt-2 flex items-center justify-between">
                    <span>Practice: {data.personalization.practice_correct}/{data.personalization.practice_attempted} correct</span>
                    <span className="italic">Progress changes priority, never historical probability</span>
                  </div>
                </div>
              </div>

              {/* Past Questions from Examination Papers */}
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
                    <BookOpen className="h-4 w-4 text-accent" />
                    Actual Examination Questions ({data.past_questions.length})
                  </h3>
                  <span className="text-xs text-muted-foreground">Rendered with KaTeX Math</span>
                </div>

                <div className="space-y-3">
                  {data.past_questions.map((q) => (
                    <div
                      key={q.id}
                      className="rounded-xl border border-border bg-card p-4 hover:border-accent/40 transition-colors space-y-2.5 shadow-sm"
                    >
                      <div className="flex items-center justify-between gap-2 flex-wrap text-xs">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-accent">Q{q.question_number || q.id}</span>
                          <span className="rounded bg-secondary px-2 py-0.5 text-foreground font-medium">
                            {q.year || "Unknown Year"}
                          </span>
                          <span className="rounded bg-secondary/80 px-2 py-0.5 text-muted-foreground">
                            {q.assessment_type}
                          </span>
                          {q.marks !== null && (
                            <span className="rounded bg-accent/10 text-accent font-semibold px-2 py-0.5">
                              {q.marks} Marks
                            </span>
                          )}
                        </div>

                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                          q.repeat_type === "EXACT_REPEAT"
                            ? "bg-emerald-500/20 text-emerald-400"
                            : q.repeat_type === "FAMILY_REPEAT"
                            ? "bg-blue-500/20 text-blue-400"
                            : "bg-secondary text-muted-foreground"
                        }`}>
                          {q.repeat_type.replace("_", " ")}
                        </span>
                      </div>

                      <div className="text-sm text-foreground overflow-x-auto py-1">
                        <MathText content={q.original_text} />
                      </div>

                      {q.family_name && (
                        <div className="text-[11px] text-muted-foreground flex items-center gap-1.5 border-t border-border/40 pt-1.5">
                          <span className="font-medium text-foreground">Family:</span>
                          <span className="truncate">{q.family_name}</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end p-4 border-t border-border bg-secondary/20">
          <button
            onClick={onClose}
            className="rounded-xl bg-secondary px-5 py-2 text-sm font-medium text-foreground hover:bg-secondary/80 transition-colors"
          >
            Close
          </button>
        </div>
    </Drawer>
  );
}