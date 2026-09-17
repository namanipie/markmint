"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  Layers,
  Sparkles,
  BookOpen,
  Calendar,
  Clock,
  AlertCircle,
  Activity,
  FileText
} from "lucide-react";
import { getSingleFamilyEvidence } from "@/lib/api";
import { SingleFamilyResponse } from "@/lib/types";
import { MathText } from "@/components/ui/math-text";

interface FamilyEvidenceModalProps {
  isOpen: boolean;
  onClose: () => void;
  courseId: number | string;
  familyId?: number | string | null;
  initialFamilyName?: string;
  onViewQuestions?: (familyId: number, familyName: string) => void;
}

export function FamilyEvidenceModal({
  isOpen,
  onClose,
  courseId,
  familyId,
  initialFamilyName,
  onViewQuestions
}: FamilyEvidenceModalProps) {
  const [data, setData] = useState<SingleFamilyResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !familyId) {
      setData(null);
      return;
    }

    let active = true;
    setIsLoading(true);
    setError(null);

    getSingleFamilyEvidence(courseId, familyId)
      .then((res) => {
        if (!active) return;
        setData(res);
      })
      .catch((err) => {
        if (!active) return;
        console.error("Failed to fetch family evidence", err);
        setError("Unable to load question family evidence. Please try again.");
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [isOpen, courseId, familyId]);

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

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4 overflow-y-auto"
      role="dialog"
      aria-modal="true"
      aria-labelledby="family-modal-title"
    >
      <div className="relative w-full max-w-4xl max-h-[90vh] flex flex-col rounded-2xl bg-card border border-border shadow-2xl overflow-hidden animate-in fade-in-0 zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-border bg-secondary/20">
          <div className="space-y-1.5 flex-1 pr-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-accent flex items-center gap-1">
                <Layers className="w-3.5 h-3.5" />
                Question Family Evidence
              </span>
              {familyId && (
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-secondary text-secondary-foreground border border-border">
                  Family #{familyId}
                </span>
              )}
              {data?.repetition_type && (
                <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                  data.repetition_type === "EXACT_REPEAT"
                    ? "bg-purple-500/15 text-purple-400 border border-purple-500/30"
                    : "bg-accent/15 text-accent border border-accent/30"
                }`}>
                  {data.repetition_type.replace(/_/g, " ")}
                </span>
              )}
            </div>

            <h2 id="family-modal-title" className="text-base font-bold text-foreground leading-snug">
              <MathText content={data?.canonical_name || initialFamilyName || "Loading family evidence..."} />
            </h2>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {isLoading ? (
            <div className="py-20 flex flex-col items-center justify-center gap-3 text-muted-foreground">
              <Activity className="w-8 h-8 animate-spin text-accent" />
              <p className="text-sm font-medium">Extracting empirical examination appearances...</p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive flex items-center gap-3">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <p className="text-sm">{error}</p>
            </div>
          ) : data ? (
            <>
              {/* Evidence Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3.5 rounded-xl bg-background/60 border border-border">
                  <div className="text-[10px] font-mono uppercase text-muted-foreground">Distinct Papers</div>
                  <div className="text-lg font-bold font-mono text-accent mt-0.5">
                    {data.distinct_paper_count} / {data.total_papers_analyzed}
                  </div>
                  <div className="text-[10px] text-muted-foreground">
                    {Math.round(data.paper_coverage * 100)}% paper coverage
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-background/60 border border-border">
                  <div className="text-[10px] font-mono uppercase text-muted-foreground">Total Appearances</div>
                  <div className="text-lg font-bold font-mono text-foreground mt-0.5">
                    {data.occurrence_count} Questions
                  </div>
                  <div className="text-[10px] text-muted-foreground">Across historical cycles</div>
                </div>

                <div className="p-3.5 rounded-xl bg-background/60 border border-border">
                  <div className="text-[10px] font-mono uppercase text-muted-foreground">Observed Marks</div>
                  <div className="text-lg font-bold font-mono text-foreground mt-0.5">
                    {data.average_marks !== null && data.average_marks > 0 ? `~${data.average_marks} Marks` : "Marks Unspecified"}
                  </div>
                  <div className="text-[10px] text-muted-foreground">
                    {data.total_marks_observed !== null && data.total_marks_observed > 0 ? `${data.total_marks_observed} total non-alt marks` : "No verified marks recorded"}
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-background/60 border border-border">
                  <div className="text-[10px] font-mono uppercase text-muted-foreground">Timeline Span</div>
                  <div className="text-lg font-bold font-mono text-foreground mt-0.5">
                    {data.first_seen_year || "—"} → {data.last_seen_year || "—"}
                  </div>
                  <div className="text-[10px] text-muted-foreground">
                    {data.observed_years.length} active year(s)
                  </div>
                </div>
              </div>

              {/* Longitudinal Examination Timeline */}
              {data.timeline && data.timeline.length > 0 && (
                <div className="p-4 rounded-xl bg-background/60 border border-border space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-foreground flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-accent" />
                      Empirical Year-by-Year Exam Presence
                    </span>
                    <span className="font-mono text-[10px] text-muted-foreground">
                      ● Tested &nbsp; ○ Held, Absent &nbsp; ┄ No Exam Record
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {data.timeline.map((entry) => (
                      <span
                        key={entry.year}
                        title={
                          entry.present
                            ? `Exam Present: Tested in ${entry.year}`
                            : entry.exam_exists === false
                            ? `No exam archived for ${entry.year} (unobserved gap year)`
                            : `Exam held in ${entry.year}, but this question family was not examined`
                        }
                        className={`inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-mono font-medium ${
                          entry.present
                            ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                            : entry.exam_exists === false
                            ? "bg-muted/20 text-muted-foreground/40 border border-dashed border-border/30"
                            : "bg-muted/40 text-muted-foreground/60 border border-border/30"
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
              )}

              {/* Assessment Type Distribution */}
              {data.assessment_history && data.assessment_history.length > 0 && (
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-muted-foreground font-medium">Observed In Assessment Types:</span>
                  <div className="flex flex-wrap gap-1">
                    {data.assessment_history.map((at) => (
                      <span
                        key={at}
                        className="px-2 py-0.5 rounded bg-background border border-border font-mono text-[11px] text-foreground"
                      >
                        {at}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Chronological Appearances */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5" />
                    Chronological Appearances in Examination Papers ({data.appearances.length})
                  </h3>
                  {onViewQuestions && (
                    <button
                      onClick={() => {
                        onViewQuestions(data.family_id, data.canonical_name);
                        onClose();
                      }}
                      className="text-xs text-accent hover:underline flex items-center gap-1 font-medium cursor-pointer"
                    >
                      <BookOpen className="w-3.5 h-3.5" />
                      <span>Open in Questions Browser</span>
                    </button>
                  )}
                </div>

                <div className="space-y-2.5">
                  {data.appearances.map((app, idx) => (
                    <div
                      key={app.question_id || idx}
                      className="p-4 rounded-xl bg-background/80 border border-border/80 text-xs space-y-2"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] border-b border-border/40 pb-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-mono font-bold text-accent">Q#{app.question_number}</span>
                          {app.year && (
                            <span className="font-mono text-muted-foreground">[{app.year}]</span>
                          )}
                          {app.assessment_type && (
                            <span className="px-1.5 py-0.5 bg-muted rounded font-mono text-[10px]">
                              {app.assessment_type}
                            </span>
                          )}
                          {app.term && (
                            <span className="px-1.5 py-0.5 bg-muted/60 rounded font-mono text-[10px]">
                              {app.term}
                            </span>
                          )}
                          {app.is_alternative && (
                            <span className="text-amber-500 font-semibold text-[10px]">
                              [Alternative / OR Choice]
                            </span>
                          )}
                        </div>

                        <div className="font-mono font-bold text-foreground">
                          {app.marks !== null && app.marks > 0 ? `${app.marks} Marks` : "Marks Unspecified"}
                        </div>
                      </div>

                      <div className="text-foreground leading-relaxed text-xs">
                        <MathText content={app.original_text} />
                      </div>

                      {app.source_document_title && (
                        <div className="text-[10px] text-muted-foreground pt-1 flex items-center gap-1">
                          <FileText className="w-3 h-3" />
                          <span className="truncate">Paper: {app.source_document_title}</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : null}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-border bg-secondary/10 flex justify-between items-center">
          <div className="text-[11px] text-muted-foreground">
            Strict empirical examination record • Zero fabricated probability
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-background border border-border rounded-lg text-xs font-semibold hover:border-accent transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
