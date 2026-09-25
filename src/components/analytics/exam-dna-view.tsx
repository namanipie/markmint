"use client";

import React, { useState, useEffect } from "react";
import {
  Dna,
  Layers,
  BarChart3,
  Calendar,
  AlertCircle,
  HelpCircle,
  BookOpen,
  Hash,
  Sparkles,
  GitBranch,
  CheckCircle2,
  Filter
} from "lucide-react";
import { getExamDNA } from "@/lib/api";
import { ExamDNA, UnitDNA, MarkBucketDNA, QuestionTypeDNA } from "@/lib/types";

interface ExamDNAViewProps {
  courseId: number | string;
  courseName: string;
  canonicalCode?: string | null;
  language?: string;
  assessmentCycle?: string;
}

export function ExamDNAView({
  courseId,
  courseName,
  canonicalCode,
  language,
  assessmentCycle
}: ExamDNAViewProps) {
  const [dna, setDna] = useState<ExamDNA | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setIsLoading(true);
    setError(null);

    getExamDNA(courseId, {
      assessmentCycle: assessmentCycle || "ALL",
      language
    })
      .then((res) => {
        if (!active) return;
        setDna(res);
      })
      .catch((err) => {
        if (!active) return;
        console.error("Failed to load Exam DNA", err);
        setError("Unable to compute Exam DNA for this course. Please verify historical corpus availability.");
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [courseId, language, assessmentCycle]);

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-xl p-10 text-center space-y-4">
        <div className="inline-flex p-3 rounded-full bg-accent/10 text-accent animate-pulse">
          <Dna className="w-8 h-8 animate-spin" />
        </div>
        <div>
          <h3 className="text-base font-semibold text-foreground">Sequencing Course Exam DNA...</h3>
          <p className="text-xs text-muted-foreground mt-1 max-w-md mx-auto">
            Aggregating historical paper structure, unit marks distribution, question types, and recurring formulation patterns.
          </p>
        </div>
      </div>
    );
  }

  if (error || !dna) {
    return (
      <div className="p-6 bg-destructive/10 border border-destructive/20 text-destructive rounded-xl flex items-center gap-3">
        <AlertCircle className="w-6 h-6 shrink-0" />
        <div>
          <h4 className="font-semibold text-sm">Exam DNA Unavailable</h4>
          <p className="text-xs opacity-90 mt-0.5">{error || "No historical examination records found for this course."}</p>
        </div>
      </div>
    );
  }

  const { sample_size, units, question_types, marks_distribution, unit_distribution, pattern_summary } = dna;
  const isInsufficient = sample_size.sufficiency === "insufficient";

  return (
    <div className="space-y-6">
      {/* 1. Historical Scope & Sample Size Header */}
      <div className="bg-card border border-border rounded-xl p-5 md:p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/50 pb-5">
          <div>
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-md bg-accent/10 text-accent">
                <Dna className="w-4 h-4" />
              </span>
              <h2 className="text-lg font-bold tracking-tight">Exam DNA: Historical Examination Fingerprint</h2>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Empirical analysis answering: <em>"How does {courseName} historically construct examination papers?"</em>
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span
              className={`px-2.5 py-1 rounded-full text-xs font-semibold capitalize border ${
                sample_size.sufficiency === "strong"
                  ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
                  : sample_size.sufficiency === "moderate"
                  ? "bg-blue-500/10 text-blue-500 border-blue-500/20"
                  : sample_size.sufficiency === "limited"
                  ? "bg-amber-500/10 text-amber-500 border-amber-500/20"
                  : "bg-destructive/10 text-destructive border-destructive/20"
              }`}
            >
              {sample_size.sufficiency} Evidence Sufficiency
            </span>
          </div>
        </div>

        {/* Dataset Metadata Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-5">
          <div className="bg-muted/30 border border-border/50 rounded-lg p-3">
            <span className="text-[11px] font-medium text-muted-foreground flex items-center gap-1">
              <BookOpen className="w-3 h-3" /> Papers Analyzed
            </span>
            <div className="text-xl font-bold mt-1 text-foreground">{sample_size.papers}</div>
            <span className="text-[10px] text-muted-foreground">archived exams</span>
          </div>

          <div className="bg-muted/30 border border-border/50 rounded-lg p-3">
            <span className="text-[11px] font-medium text-muted-foreground flex items-center gap-1">
              <Hash className="w-3 h-3" /> Questions Analyzed
            </span>
            <div className="text-xl font-bold mt-1 text-foreground">{sample_size.questions}</div>
            <span className="text-[10px] text-muted-foreground">total question pool</span>
          </div>

          <div className="bg-muted/30 border border-border/50 rounded-lg p-3">
            <span className="text-[11px] font-medium text-muted-foreground flex items-center gap-1">
              <Calendar className="w-3 h-3" /> Historical Range
            </span>
            <div className="text-xl font-bold mt-1 text-foreground">
              {sample_size.time_range_years[0] > 0
                ? `${sample_size.time_range_years[0]} - ${sample_size.time_range_years[1]}`
                : "Undated"}
            </div>
            <span className="text-[10px] text-muted-foreground">
              {sample_size.years && sample_size.years.length > 0 ? `${sample_size.years.length} distinct years` : "evidence span"}
            </span>
          </div>

          <div className="bg-muted/30 border border-border/50 rounded-lg p-3">
            <span className="text-[11px] font-medium text-muted-foreground flex items-center gap-1">
              <BarChart3 className="w-3 h-3" /> Total Marks
            </span>
            <div className="text-xl font-bold mt-1 text-foreground">
              {sample_size.total_marks ? `${sample_size.total_marks}` : "0"}
            </div>
            <span className="text-[10px] text-muted-foreground">non-alt evaluated marks</span>
          </div>
        </div>

        {isInsufficient && (
          <div className="mt-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400 text-xs flex items-center gap-2">
            <HelpCircle className="w-4 h-4 shrink-0" />
            <span>
              <strong>Limited Historical Sample:</strong> This course has fewer than 4 verified exam papers in the corpus. Aggregated percentages reflect available evidence and should be interpreted conservatively.
            </span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 2. Unit Distribution */}
        <div className="bg-card border border-border rounded-xl p-5 md:p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-border/50 pb-3">
            <div>
              <h3 className="text-sm font-bold flex items-center gap-2">
                <Layers className="w-4 h-4 text-accent" />
                Unit Distribution
              </h3>
              <p className="text-[11px] text-muted-foreground mt-0.5">
                Historical weighting across syllabus units ({unit_distribution?.is_marks_weighted ? "Marks-Weighted" : "Question-Count Fallback"})
              </p>
            </div>
          </div>

          {units.length === 0 ? (
            <div className="py-8 text-center text-xs text-muted-foreground">
              No syllabus unit mappings cataloged yet for this course.
            </div>
          ) : (
            <div className="space-y-3.5">
              {units.map((u) => {
                const pct = Math.round(u.historical_weighting * 100);
                return (
                  <div key={u.unit} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-foreground">{u.unit}</span>
                      <div className="flex items-center gap-3 text-muted-foreground">
                        <span>{u.question_count} questions</span>
                        <span className="font-medium text-foreground">{u.marks} marks ({pct}%)</span>
                      </div>
                    </div>
                    <div className="w-full h-2 rounded-full bg-muted overflow-hidden flex">
                      <div
                        className="h-full bg-accent rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(100, Math.max(2, pct))}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-[10px] text-muted-foreground">
                      <span>Paper Coverage: {Math.round(u.paper_coverage * 100)}% of exams</span>
                      {u.recent_weighting > 0 && (
                        <span>Recent Weight: {Math.round(u.recent_weighting * 100)}%</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Missing Metadata Notice */}
          {unit_distribution && unit_distribution.unmapped_question_count > 0 && (
            <div className="p-2.5 rounded-lg bg-muted/40 border border-border/60 text-[11px] text-muted-foreground flex items-center justify-between">
              <span>Unmapped questions without unit association:</span>
              <span className="font-medium text-foreground">
                {unit_distribution.unmapped_question_count} Qs ({unit_distribution.unmapped_marks} marks)
              </span>
            </div>
          )}
        </div>

        {/* 3. Question-Type Distribution */}
        <div className="bg-card border border-border rounded-xl p-5 md:p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-border/50 pb-3">
            <div>
              <h3 className="text-sm font-bold flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-accent" />
                Question-Type Distribution
              </h3>
              <p className="text-[11px] text-muted-foreground mt-0.5">
                Classification breakdown from verified historical examinations
              </p>
            </div>
          </div>

          {question_types.length === 0 ? (
            <div className="py-8 text-center text-xs text-muted-foreground">
              No question type classifications recorded.
            </div>
          ) : (
            <div className="space-y-3">
              {question_types.map((qt) => {
                const pct = Math.round(qt.percentage * 100);
                const isUnclassified = qt.question_type.toLowerCase() === "unclassified";
                return (
                  <div key={qt.question_type} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold capitalize text-foreground flex items-center gap-1.5">
                        {isUnclassified ? (
                          <span className="text-muted-foreground italic">Unclassified / General</span>
                        ) : (
                          qt.question_type
                        )}
                      </span>
                      <span className="font-medium text-foreground">
                        {qt.count} Qs ({pct}%)
                      </span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-muted overflow-hidden flex">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          isUnclassified ? "bg-muted-foreground/40" : "bg-primary"
                        }`}
                        style={{ width: `${Math.min(100, Math.max(2, pct))}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* 4. Marks Distribution */}
      <div className="bg-card border border-border rounded-xl p-5 md:p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-border/50 pb-3">
          <div>
            <h3 className="text-sm font-bold flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-accent" />
              Marks Distribution (Empirical Paper Architecture)
            </h3>
            <p className="text-[11px] text-muted-foreground mt-0.5">
              Historical allocation by mark value derived from actual examination question weights
            </p>
          </div>
          {marks_distribution && marks_distribution.avg_marks && (
            <div className="text-xs font-medium text-muted-foreground">
              Average Question Weight: <span className="text-foreground font-bold">{marks_distribution.avg_marks} marks</span>
            </div>
          )}
        </div>

        {!marks_distribution || marks_distribution.buckets.length === 0 ? (
          <div className="py-8 text-center text-xs text-muted-foreground">
            No discrete mark distribution data available for this course.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-border text-muted-foreground">
                  <th className="pb-2 font-semibold">Mark Tier</th>
                  <th className="pb-2 font-semibold">Question Count</th>
                  <th className="pb-2 font-semibold">% of Questions</th>
                  <th className="pb-2 font-semibold">Cumulative Marks</th>
                  <th className="pb-2 font-semibold">% of Total Marks</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40">
                {marks_distribution.buckets.map((b) => (
                  <tr key={b.marks} className="hover:bg-muted/30 transition-colors">
                    <td className="py-2.5 font-bold text-foreground">
                      {b.marks} {b.marks === 1 ? "Mark" : "Marks"}
                    </td>
                    <td className="py-2.5 text-muted-foreground">{b.question_count}</td>
                    <td className="py-2.5 font-medium text-foreground">
                      {Math.round(b.percentage_of_questions * 100)}%
                    </td>
                    <td className="py-2.5 text-muted-foreground">{b.cumulative_marks}</td>
                    <td className="py-2.5 font-medium text-accent">
                      {Math.round(b.percentage_of_marks * 100)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {marks_distribution && marks_distribution.unscored_question_count > 0 && (
          <div className="p-2.5 rounded-lg bg-muted/40 border border-border/60 text-[11px] text-muted-foreground flex items-center justify-between">
            <span>Questions without assigned mark metadata:</span>
            <span className="font-medium text-foreground">
              {marks_distribution.unscored_question_count} Qs ({Math.round(marks_distribution.unscored_percentage * 100)}%)
            </span>
          </div>
        )}
      </div>

      {/* 5. Question-Pattern Summary */}
      <div className="bg-card border border-border rounded-xl p-5 md:p-6 shadow-sm space-y-5">
        <div className="flex items-center justify-between border-b border-border/50 pb-3">
          <div>
            <h3 className="text-sm font-bold flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-accent" />
              Question-Pattern Summary
            </h3>
            <p className="text-[11px] text-muted-foreground mt-0.5">
              Deterministic aggregation of formulation stems and recurring canonical question families
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Repetition Breakdown Card */}
          <div className="bg-muted/20 border border-border/60 rounded-xl p-4 space-y-3">
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Repetition Architecture
            </h4>
            {pattern_summary?.repetition_breakdown ? (
              <div className="space-y-2.5">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-muted-foreground">Exact Repeats</span>
                    <span className="font-bold text-foreground">
                      {pattern_summary.repetition_breakdown.exact_repeat_count} ({Math.round(pattern_summary.repetition_breakdown.exact_repeat_percentage * 100)}%)
                    </span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full bg-emerald-500 rounded-full"
                      style={{ width: `${Math.round(pattern_summary.repetition_breakdown.exact_repeat_percentage * 100)}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-muted-foreground">Family Recurrence</span>
                    <span className="font-bold text-foreground">
                      {pattern_summary.repetition_breakdown.family_repeat_count} ({Math.round(pattern_summary.repetition_breakdown.family_repeat_percentage * 100)}%)
                    </span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{ width: `${Math.round(pattern_summary.repetition_breakdown.family_repeat_percentage * 100)}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-muted-foreground">Singletons / Unique</span>
                    <span className="font-bold text-foreground">
                      {pattern_summary.repetition_breakdown.singleton_count} ({Math.round(pattern_summary.repetition_breakdown.singleton_percentage * 100)}%)
                    </span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full bg-muted-foreground/40 rounded-full"
                      style={{ width: `${Math.round(pattern_summary.repetition_breakdown.singleton_percentage * 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">No repetition breakdown available.</p>
            )}
          </div>

          {/* Formulation Stems */}
          <div className="bg-muted/20 border border-border/60 rounded-xl p-4 md:col-span-2 space-y-3">
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Common Question Formulation Stems
            </h4>
            {pattern_summary?.stem_patterns && pattern_summary.stem_patterns.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {pattern_summary.stem_patterns.map((sp) => (
                  <div key={sp.pattern} className="bg-card/70 border border-border/40 p-2.5 rounded-lg text-xs space-y-1">
                    <div className="flex justify-between font-semibold">
                      <span className="text-foreground">{sp.pattern}</span>
                      <span className="text-accent">{Math.round(sp.percentage * 100)}%</span>
                    </div>
                    <div className="text-[11px] text-muted-foreground">
                      {sp.question_count} questions
                      {sp.example_verbs && sp.example_verbs.length > 0 && ` • e.g. ${sp.example_verbs.slice(0, 3).join(", ")}`}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">No formulation stem patterns extracted.</p>
            )}
          </div>
        </div>

        {/* Top Recurring Families */}
        {pattern_summary?.top_recurring_families && pattern_summary.top_recurring_families.length > 0 && (
          <div className="space-y-3 pt-2">
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
              <GitBranch className="w-3.5 h-3.5 text-accent" /> High-Yield Recurring Question Families
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {pattern_summary.top_recurring_families.slice(0, 6).map((fam) => (
                <div key={fam.family_name} className="p-3 bg-muted/20 border border-border/50 rounded-lg text-xs space-y-1">
                  <div className="font-semibold text-foreground flex items-center justify-between">
                    <span className="truncate pr-2">{fam.family_name.replace(/_/g, " ")}</span>
                    <span className="px-1.5 py-0.5 rounded bg-accent/10 text-accent text-[10px] shrink-0">
                      {fam.occurrences} appearances
                    </span>
                  </div>
                  <div className="flex justify-between text-[11px] text-muted-foreground">
                    <span>In {fam.distinct_paper_count} papers ({fam.years.join(", ")})</span>
                    {fam.average_marks && <span>~{fam.average_marks} marks</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
