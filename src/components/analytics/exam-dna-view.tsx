"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Dna,
  BarChart3,
  Calendar,
  AlertCircle,
  HelpCircle,
  Hash,
  Sparkles,
  GitBranch,
  ShieldCheck,
  FileText
} from "lucide-react";
import { getExamDNA } from "@/lib/api";
import {
  ExamDNA,
  UnitDistribution,
  QuestionTypeBreakdown,
  MarksDistribution
} from "@/lib/types";
import { ChartCard } from "@/components/ui/chart-card";
import { UnitDistributionChart } from "@/components/charts/unit-distribution-chart";
import { QuestionTypeChart } from "@/components/charts/question-type-chart";
import { MarksDistributionChart } from "@/components/charts/marks-distribution-chart";

interface ExamDNAViewProps {
  courseId: number | string;
  courseName: string;
  canonicalCode?: string | null;
  language?: string;
  assessmentCycle?: string;
  cutoffYear?: number;
}

export function ExamDNAView({
  courseId,
  courseName,
  canonicalCode,
  language,
  assessmentCycle,
  cutoffYear
}: ExamDNAViewProps) {
  const [dna, setDna] = useState<ExamDNA | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Sync loading state upon prop changes without direct setState in effect body
  const [queryKey, setQueryKey] = useState(() => `${courseId}-${language || ""}-${assessmentCycle || ""}-${cutoffYear || ""}`);
  const targetKey = `${courseId}-${language || ""}-${assessmentCycle || ""}-${cutoffYear || ""}`;

  if (queryKey !== targetKey) {
    setQueryKey(targetKey);
    setIsLoading(true);
    setError(null);
  }

  useEffect(() => {
    let active = true;

    getExamDNA(courseId, {
      assessmentCycle: assessmentCycle || "ALL",
      language,
      cutoffYear
    })
      .then((res) => {
        if (!active) return;
        setDna(res);
        setIsLoading(false);
      })
      .catch((err) => {
        if (!active) return;
        console.error("Failed to load Exam DNA", err);
        setError("Unable to compute Exam DNA for this course. Please verify historical corpus availability.");
        setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [courseId, language, assessmentCycle, cutoffYear]);

  // Chart data transformations
  const unitChartData: UnitDistribution[] = useMemo(() => {
    if (!dna || !dna.units) return [];
    return dna.units.map((u) => ({
      unit: u.unit,
      name: u.unit,
      weight: Math.round(u.historical_weighting * 100),
      questionCount: u.question_count
    }));
  }, [dna]);

  const questionTypeChartData: QuestionTypeBreakdown[] = useMemo(() => {
    if (!dna || !dna.question_types) return [];
    return dna.question_types.map((qt) => ({
      type:
        qt.question_type.toLowerCase() === "unclassified"
          ? "Unclassified / General"
          : qt.question_type.charAt(0).toUpperCase() + qt.question_type.slice(1),
      count: qt.count,
      percentage: Math.round(qt.percentage * 100)
    }));
  }, [dna]);

  const marksChartData: MarksDistribution[] = useMemo(() => {
    if (!dna || !dna.marks_distribution?.buckets) return [];
    return dna.marks_distribution.buckets.map((b) => ({
      marks: b.marks,
      name: `${b.marks} ${b.marks === 1 ? "Mark" : "Marks"}`,
      count: b.question_count,
      label: `${b.marks}m`,
      percentage: Math.round(b.percentage_of_questions * 100)
    }));
  }, [dna]);

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
  const historicalExamCount = sample_size.papers;
  const historicalQuestionCount = sample_size.questions;

  return (
    <div className="space-y-8">
      {/* 1. Dataset Header & Metadata Section */}
      <section className="bg-card border border-border rounded-2xl p-6 md:p-8 shadow-sm space-y-6">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 border-b border-border/50 pb-5">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-accent/10 text-accent">
                <Dna className="w-5 h-5" />
              </span>
              <h2 className="text-xl font-bold tracking-tight text-foreground">
                Exam DNA: Historical Examination Fingerprint
              </h2>
            </div>
            <p className="text-sm text-muted-foreground">
              Empirical historical observations answering: <em>&ldquo;How does {canonicalCode ? `${courseName} (${canonicalCode})` : courseName} historically ask questions?&rdquo;</em>
            </p>
            <div className="text-xs font-medium text-accent pt-1">
              Based on {historicalExamCount} historical {historicalExamCount === 1 ? "exam" : "exams"} ({historicalQuestionCount} questions analyzed)
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`px-3 py-1 rounded-full text-xs font-semibold capitalize border ${
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

        {/* Dataset Summary Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-muted/20 border border-border/60 rounded-xl p-4 space-y-1">
            <span className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-accent" /> Exams Analysed
            </span>
            <div className="text-2xl font-bold text-foreground">{sample_size.papers}</div>
            <p className="text-[11px] text-muted-foreground">Verified past exam papers</p>
          </div>

          <div className="bg-muted/20 border border-border/60 rounded-xl p-4 space-y-1">
            <span className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
              <Hash className="w-3.5 h-3.5 text-accent" /> Questions Analysed
            </span>
            <div className="text-2xl font-bold text-foreground">{sample_size.questions}</div>
            <p className="text-[11px] text-muted-foreground">Total question corpus</p>
          </div>

          <div className="bg-muted/20 border border-border/60 rounded-xl p-4 space-y-1">
            <span className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-accent" /> Historical Range
            </span>
            <div className="text-2xl font-bold text-foreground">
              {sample_size.time_range_years[0] > 0
                ? `${sample_size.time_range_years[0]} - ${sample_size.time_range_years[1]}`
                : "Undated"}
            </div>
            <p className="text-[11px] text-muted-foreground">
              {sample_size.years && sample_size.years.length > 0
                ? `${sample_size.years.length} distinct years (${sample_size.years.join(", ")})`
                : "Historical evidence span"}
            </p>
          </div>

          <div className="bg-muted/20 border border-border/60 rounded-xl p-4 space-y-1">
            <span className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
              <BarChart3 className="w-3.5 h-3.5 text-accent" /> Total Evaluated Marks
            </span>
            <div className="text-2xl font-bold text-foreground">
              {sample_size.total_marks ? sample_size.total_marks : "0"}
            </div>
            <p className="text-[11px] text-muted-foreground">Cumulative exam score weight</p>
          </div>
        </div>

        {/* Temporal / Sufficiency Notice */}
        {isInsufficient ? (
          <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400 text-xs flex items-center gap-2.5">
            <HelpCircle className="w-4 h-4 shrink-0" />
            <span>
              <strong>Limited Historical Sample:</strong> This course has fewer than 4 verified exam papers in the active archive. Percentages represent available historical observations rather than permanent curriculum invariants.
            </span>
          </div>
        ) : (
          <div className="p-3 rounded-xl bg-secondary/30 border border-border/40 text-xs text-muted-foreground flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-accent shrink-0" />
            <span>
              <strong>Non-Predictive Historical Layer:</strong> These metrics describe documented historical examination behaviors across verified papers. MarkMint never speculates or fabricates missing information.
            </span>
          </div>
        )}
      </section>

      {/* 2. Unit Distribution & 3. Question-Type Distribution (2-Column Grid) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* 2. Unit Distribution */}
        <ChartCard
          title="Unit Distribution"
          description={`Historical distribution across syllabus units based on ${historicalExamCount} exams (${
            unit_distribution?.is_marks_weighted ? "Marks-Weighted" : "Question-Count Fallback"
          })`}
          className="bg-card border border-border shadow-sm flex flex-col justify-between"
        >
          <div className="space-y-4">
            {units.length === 0 ? (
              <div className="h-[280px] flex items-center justify-center text-xs text-muted-foreground">
                No syllabus unit mappings recorded for this course.
              </div>
            ) : (
              <div>
                <UnitDistributionChart data={unitChartData} />

                {/* Unit breakdown table / list */}
                <div className="mt-4 divide-y divide-border/40 border-t border-border/40 text-xs">
                  {units.map((u) => {
                    const pct = Math.round(u.historical_weighting * 100);
                    return (
                      <div key={u.unit} className="py-2.5 flex items-center justify-between gap-2">
                        <div className="space-y-0.5">
                          <span className="font-semibold text-foreground">{u.unit}</span>
                          <div className="text-[11px] text-muted-foreground">
                            Appeared in {Math.round(u.paper_coverage * 100)}% of papers
                            {u.recent_weighting > 0 && ` • Recent: ${Math.round(u.recent_weighting * 100)}%`}
                          </div>
                        </div>
                        <div className="text-right">
                          <span className="font-bold text-foreground">{pct}%</span>
                          <div className="text-[11px] text-muted-foreground">
                            {u.marks} marks ({u.question_count} Qs)
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Unmapped Metadata Disclosure */}
            {unit_distribution && unit_distribution.unmapped_question_count > 0 && (
              <div className="mt-3 p-2.5 rounded-lg bg-muted/40 border border-border/60 text-[11px] text-muted-foreground flex items-center justify-between">
                <span>Questions unmapped to syllabus units:</span>
                <span className="font-semibold text-foreground">
                  {unit_distribution.unmapped_question_count} Qs ({unit_distribution.unmapped_marks} marks)
                </span>
              </div>
            )}
          </div>
        </ChartCard>

        {/* 3. Question-Type Distribution */}
        <ChartCard
          title="Question-Type Distribution"
          description={`Historical breakdown of question classifications based on ${historicalQuestionCount} questions across ${historicalExamCount} exams`}
          className="bg-card border border-border shadow-sm flex flex-col justify-between"
        >
          <div className="space-y-4">
            {question_types.length === 0 ? (
              <div className="h-[280px] flex items-center justify-center text-xs text-muted-foreground">
                No question type classifications recorded.
              </div>
            ) : (
              <div>
                <QuestionTypeChart data={questionTypeChartData} />

                {/* Question Types breakdown table / list */}
                <div className="mt-4 divide-y divide-border/40 border-t border-border/40 text-xs">
                  {question_types.map((qt) => {
                    const pct = Math.round(qt.percentage * 100);
                    const isUnclassified = qt.question_type.toLowerCase() === "unclassified";
                    return (
                      <div key={qt.question_type} className="py-2.5 flex items-center justify-between gap-2">
                        <span className="font-medium capitalize text-foreground flex items-center gap-1.5">
                          {isUnclassified ? (
                            <span className="text-muted-foreground italic">Unclassified / General</span>
                          ) : (
                            qt.question_type
                          )}
                        </span>
                        <div className="text-right">
                          <span className="font-bold text-foreground">{pct}%</span>
                          <span className="text-[11px] text-muted-foreground ml-2">({qt.count} Qs)</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="mt-3 p-2.5 rounded-lg bg-muted/30 border border-border/40 text-[11px] text-muted-foreground">
              Based on historical question classifications recorded in the archive. Unclassified questions are reported honestly without artificial synthesis.
            </div>
          </div>
        </ChartCard>
      </div>

      {/* 4. Marks Distribution */}
      <section className="bg-card border border-border rounded-2xl p-6 md:p-8 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border/50 pb-4">
          <div>
            <h3 className="text-lg font-bold tracking-tight text-foreground flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-accent" />
              Marks Distribution (Empirical Question Weights)
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              How frequently different mark values occur based on {historicalExamCount} historical exams
            </p>
          </div>
          {marks_distribution && marks_distribution.avg_marks && (
            <div className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-accent/10 text-accent border border-accent/20">
              Avg Weight: {marks_distribution.avg_marks} marks/question
            </div>
          )}
        </div>

        {!marks_distribution || marks_distribution.buckets.length === 0 ? (
          <div className="py-12 text-center text-xs text-muted-foreground">
            No discrete mark distribution data available for this course.
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            {/* Pie Chart of Mark Tiers */}
            <div className="lg:col-span-5 flex flex-col items-center">
              <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                Mark Tier Breakdown
              </div>
              <MarksDistributionChart data={marksChartData} />
            </div>

            {/* Table of Discrete Mark Tiers */}
            <div className="lg:col-span-7 space-y-3">
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
                        <td className="py-2.5 font-semibold text-accent">
                          {Math.round(b.percentage_of_marks * 100)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {marks_distribution.unscored_question_count > 0 && (
                <div className="p-2.5 rounded-lg bg-muted/40 border border-border/60 text-[11px] text-muted-foreground flex items-center justify-between">
                  <span>Questions without assigned mark values:</span>
                  <span className="font-semibold text-foreground">
                    {marks_distribution.unscored_question_count} Qs ({Math.round(marks_distribution.unscored_percentage * 100)}%)
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </section>

      {/* 5. Question Patterns */}
      <section className="bg-card border border-border rounded-2xl p-6 md:p-8 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border/50 pb-4">
          <div>
            <h3 className="text-lg font-bold tracking-tight text-foreground flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-accent" />
              Question Patterns & Formulation Lineage
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              Deterministic patterns extracted from Question Families and Question Stems based on {historicalExamCount} historical exams
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Repetition Breakdown Card */}
          <div className="bg-muted/20 border border-border/60 rounded-xl p-5 space-y-4">
            <div>
              <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Repetition Architecture
              </h4>
              <p className="text-[11px] text-muted-foreground mt-0.5">
                Exact vs conceptual recurrence observed across papers
              </p>
            </div>

            {pattern_summary?.repetition_breakdown ? (
              <div className="space-y-3.5 pt-1">
                <div>
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-muted-foreground">Exact Repeats</span>
                    <span className="font-bold text-foreground">
                      {pattern_summary.repetition_breakdown.exact_repeat_count} ({Math.round(pattern_summary.repetition_breakdown.exact_repeat_percentage * 100)}%)
                    </span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                      style={{ width: `${Math.round(pattern_summary.repetition_breakdown.exact_repeat_percentage * 100)}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-muted-foreground">Family Recurrence</span>
                    <span className="font-bold text-foreground">
                      {pattern_summary.repetition_breakdown.family_repeat_count} ({Math.round(pattern_summary.repetition_breakdown.family_repeat_percentage * 100)}%)
                    </span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full transition-all duration-500"
                      style={{ width: `${Math.round(pattern_summary.repetition_breakdown.family_repeat_percentage * 100)}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-muted-foreground">Singletons / Unique</span>
                    <span className="font-bold text-foreground">
                      {pattern_summary.repetition_breakdown.singleton_count} ({Math.round(pattern_summary.repetition_breakdown.singleton_percentage * 100)}%)
                    </span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full bg-muted-foreground/40 rounded-full transition-all duration-500"
                      style={{ width: `${Math.round(pattern_summary.repetition_breakdown.singleton_percentage * 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-xs text-muted-foreground py-6 text-center">No repetition breakdown available.</p>
            )}
          </div>

          {/* Formulation Stems */}
          <div className="bg-muted/20 border border-border/60 rounded-xl p-5 md:col-span-2 space-y-4">
            <div>
              <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Common Question Formulation Stems
              </h4>
              <p className="text-[11px] text-muted-foreground mt-0.5">
                Deterministic syntactic verb stem distribution extracted from actual questions
              </p>
            </div>

            {pattern_summary?.stem_patterns && pattern_summary.stem_patterns.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                {pattern_summary.stem_patterns.map((sp) => (
                  <div key={sp.pattern} className="bg-card border border-border/60 p-3 rounded-lg text-xs space-y-1.5">
                    <div className="flex justify-between items-center font-semibold">
                      <span className="text-foreground">{sp.pattern}</span>
                      <span className="px-2 py-0.5 rounded bg-accent/10 text-accent font-bold text-[11px]">
                        {Math.round(sp.percentage * 100)}%
                      </span>
                    </div>
                    <div className="text-[11px] text-muted-foreground flex items-center justify-between">
                      <span>{sp.question_count} questions</span>
                      {sp.example_verbs && sp.example_verbs.length > 0 && (
                        <span className="truncate max-w-[140px] text-right font-mono text-[10px]">
                          {sp.example_verbs.slice(0, 3).join(", ")}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground py-6 text-center">No formulation stem patterns extracted.</p>
            )}
          </div>
        </div>

        {/* Top Recurring Families */}
        {pattern_summary?.top_recurring_families && pattern_summary.top_recurring_families.length > 0 && (
          <div className="space-y-3.5 pt-2">
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
              <GitBranch className="w-4 h-4 text-accent" />
              Most Frequent Recurring Question Families (Based on {historicalExamCount} Historical Exams)
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3.5">
              {pattern_summary.top_recurring_families.slice(0, 6).map((fam) => (
                <div key={fam.family_name} className="p-3.5 bg-muted/20 border border-border/60 rounded-xl text-xs space-y-2">
                  <div className="font-semibold text-foreground flex items-start justify-between gap-2">
                    <span className="line-clamp-2 leading-snug">{fam.family_name.replace(/_/g, " ")}</span>
                    <span className="px-2 py-0.5 rounded bg-accent/10 text-accent text-[10px] font-bold shrink-0">
                      {fam.occurrences}x
                    </span>
                  </div>
                  <div className="pt-1.5 border-t border-border/40 flex justify-between items-center text-[11px] text-muted-foreground">
                    <span>In {fam.distinct_paper_count} papers ({fam.years.join(", ")})</span>
                    {fam.average_marks && <span className="font-medium text-foreground">~{fam.average_marks}m</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
