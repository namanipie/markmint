"use client";

import React, { useState, useMemo } from "react";
import {
  BrainCircuit,
  Calendar,
  AlertCircle,
  HelpCircle,
  Info,
  Scale
} from "lucide-react";
import {
  CognitiveDemandDistributionDNA,
  TemporalCognitiveDemandBreakdown,
  SectionCognitiveProfileDNA
} from "@/lib/types";

interface Props {
  cognitiveDemandDistribution?: CognitiveDemandDistributionDNA;
  temporalCognitiveDemand?: TemporalCognitiveDemandBreakdown[];
  sectionCognitiveProfiles?: SectionCognitiveProfileDNA[];
  demandQuestionTypeCrossTabulation?: Record<string, Record<string, number>>;
  assessmentCycle?: string;
}

interface ArchetypeConfig {
  key: string;
  label: string;
  shortLabel: string;
  description: string;
  examples: string;
  bgLight: string;
  textClass: string;
  borderClass: string;
  barColor: string;
}

const ARCHETYPE_CONFIGS: Record<string, ArchetypeConfig> = {
  RECALL_AND_CONCEPT: {
    key: "RECALL_AND_CONCEPT",
    label: "Recall & Concept",
    shortLabel: "Recall",
    description: "Knowledge retrieval, definitions, conceptual explanations, principles, factual identification, listing components.",
    examples: "Define, state, explain the concept, what is, list advantages",
    bgLight: "bg-blue-500/10",
    textClass: "text-blue-600 dark:text-blue-400",
    borderClass: "border-blue-500/20",
    barColor: "bg-blue-500"
  },
  PROCEDURAL_COMPUTATION: {
    key: "PROCEDURAL_COMPUTATION",
    label: "Procedural & Computational",
    shortLabel: "Procedural",
    description: "Mathematical calculations, algorithmic execution, numerical solving, code tracing, procedural transformations.",
    examples: "Calculate, solve, evaluate, compute, trace execution",
    bgLight: "bg-emerald-500/10",
    textClass: "text-emerald-600 dark:text-emerald-400",
    borderClass: "border-emerald-500/20",
    barColor: "bg-emerald-500"
  },
  ANALYTICAL_PROOF_AND_DESIGN: {
    key: "ANALYTICAL_PROOF_AND_DESIGN",
    label: "Analytical, Proof & Design",
    shortLabel: "Analytical",
    description: "Formal proofs, derivations, system/schema/algorithm design, open-ended synthesis, analytical comparison, debugging.",
    examples: "Prove that, derive expression, design schema, compare, optimize",
    bgLight: "bg-purple-500/10",
    textClass: "text-purple-600 dark:text-purple-400",
    borderClass: "border-purple-500/20",
    barColor: "bg-purple-500"
  },
  UNCLASSIFIED: {
    key: "UNCLASSIFIED",
    label: "Unclassified",
    shortLabel: "Unclassified",
    description: "Insufficient, indeterminate, or contradictory evidence.",
    examples: "Multi-part conflicting demands or non-discriminatory text",
    bgLight: "bg-zinc-500/10",
    textClass: "text-zinc-600 dark:text-zinc-400",
    borderClass: "border-zinc-500/20",
    barColor: "bg-zinc-400 dark:bg-zinc-600"
  }
};

const ORDERED_KEYS = [
  "RECALL_AND_CONCEPT",
  "PROCEDURAL_COMPUTATION",
  "ANALYTICAL_PROOF_AND_DESIGN",
  "UNCLASSIFIED"
];

export function HistoricalCognitiveDemand({
  cognitiveDemandDistribution,
  temporalCognitiveDemand = [],
  sectionCognitiveProfiles = [],
  demandQuestionTypeCrossTabulation = {},
  assessmentCycle = "ALL"
}: Props) {
  const [viewMode, setViewMode] = useState<"overview" | "cycles" | "sections" | "chronology" | "qtypes">("overview");
  const [metricMode, setMetricMode] = useState<"questions" | "marks">("questions");

  const totalQuestions = cognitiveDemandDistribution?.total_questions || 0;
  const isMarksReliable = Boolean(cognitiveDemandDistribution?.is_marks_reliable);
  const unclassifiedPct = cognitiveDemandDistribution?.unclassified_percentage
    ? Math.round(cognitiveDemandDistribution.unclassified_percentage * 1000) / 10
    : 0;
  const unclassifiedCount = cognitiveDemandDistribution?.unclassified_count || 0;

  // Active items map
  const itemsMap = useMemo(() => {
    const map: Record<string, { count: number; pct: number; scoredMarks: number; marksPct: number | null }> = {};
    for (const k of ORDERED_KEYS) {
      map[k] = { count: 0, pct: 0, scoredMarks: 0, marksPct: null };
    }
    if (cognitiveDemandDistribution?.items) {
      for (const item of cognitiveDemandDistribution.items) {
        if (map[item.demand]) {
          map[item.demand] = {
            count: item.question_count,
            pct: Math.round(item.percentage * 1000) / 10,
            scoredMarks: item.scored_marks,
            marksPct: item.marks_percentage !== null && item.marks_percentage !== undefined
              ? Math.round(item.marks_percentage * 1000) / 10
              : null
          };
        }
      }
    }
    return map;
  }, [cognitiveDemandDistribution]);

  // Cycles present
  const cyclesData = useMemo(() => {
    if (!cognitiveDemandDistribution?.by_assessment_cycle) return [];
    const entries = Object.entries(cognitiveDemandDistribution.by_assessment_cycle);
    return entries.map(([cycleName, demandMap]) => {
      const cycleTotal = Object.values(demandMap).reduce((a, b) => a + b, 0);
      return {
        cycle: cycleName,
        total: cycleTotal,
        demands: demandMap
      };
    }).sort((a, b) => {
      // Prioritize standard cycles
      const order = ["CT1", "CT2", "ENDSEM", "ALL"];
      const aIdx = order.indexOf(a.cycle);
      const bIdx = order.indexOf(b.cycle);
      if (aIdx !== -1 && bIdx !== -1) return aIdx - bIdx;
      if (aIdx !== -1) return -1;
      if (bIdx !== -1) return 1;
      return a.cycle.localeCompare(b.cycle);
    });
  }, [cognitiveDemandDistribution]);

  // Question Type Cross-Tabulation Matrix
  const qtypeMatrix = useMemo(() => {
    const qtypesSet = new Set<string>();
    for (const demandKey of Object.keys(demandQuestionTypeCrossTabulation)) {
      for (const qt of Object.keys(demandQuestionTypeCrossTabulation[demandKey])) {
        qtypesSet.add(qt);
      }
    }

    const rows = Array.from(qtypesSet).map((qt) => {
      const counts: Record<string, number> = {};
      let rowTotal = 0;
      for (const k of ORDERED_KEYS) {
        const c = demandQuestionTypeCrossTabulation[k]?.[qt] || 0;
        counts[k] = c;
        rowTotal += c;
      }
      return {
        qtype: qt,
        total: rowTotal,
        counts
      };
    });

    return rows.sort((a, b) => b.total - a.total);
  }, [demandQuestionTypeCrossTabulation]);

  if (!cognitiveDemandDistribution || totalQuestions === 0) {
    return (
      <section className="bg-card border border-border rounded-2xl p-6 md:p-8 shadow-sm space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20">
            <BrainCircuit className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold tracking-tight text-foreground">
              Historical Cognitive Demand
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              Observable historical question-demand patterns derived from question format and structure, not measurements of student difficulty.
            </p>
          </div>
        </div>
        <div className="p-8 text-center border border-dashed border-border rounded-xl">
          <p className="text-xs text-muted-foreground">
            No historical questions available to derive cognitive demand signals for this scope.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="bg-card border border-border rounded-2xl p-6 md:p-8 shadow-sm space-y-6">
      {/* 1. Header and Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-border/50 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20">
              <BrainCircuit className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold tracking-tight text-foreground flex items-center gap-2">
                  Historical Cognitive Demand
                </h3>
                {assessmentCycle && assessmentCycle !== "ALL" && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-accent/10 text-accent border border-accent/20">
                    Cycle: {assessmentCycle}
                  </span>
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                Observable historical question-demand patterns derived from question format and structure, not measurements of student difficulty.
              </p>
            </div>
          </div>
        </div>

        {/* Action Controls: View mode and Metric mode */}
        <div className="flex flex-wrap items-center gap-2 self-start lg:self-center">
          {/* View switcher */}
          <div className="flex items-center bg-muted/60 p-1 rounded-xl border border-border text-xs font-medium">
            <button
              onClick={() => setViewMode("overview")}
              className={`px-3 py-1 rounded-lg transition-colors ${
                viewMode === "overview"
                  ? "bg-card text-foreground shadow-sm font-semibold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setViewMode("cycles")}
              className={`px-3 py-1 rounded-lg transition-colors ${
                viewMode === "cycles"
                  ? "bg-card text-foreground shadow-sm font-semibold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Cycles ({cyclesData.length})
            </button>
            <button
              onClick={() => setViewMode("sections")}
              className={`px-3 py-1 rounded-lg transition-colors ${
                viewMode === "sections"
                  ? "bg-card text-foreground shadow-sm font-semibold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Sections ({sectionCognitiveProfiles.length})
            </button>
            <button
              onClick={() => setViewMode("chronology")}
              className={`px-3 py-1 rounded-lg transition-colors ${
                viewMode === "chronology"
                  ? "bg-card text-foreground shadow-sm font-semibold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Chronology ({temporalCognitiveDemand.length})
            </button>
            <button
              onClick={() => setViewMode("qtypes")}
              className={`px-3 py-1 rounded-lg transition-colors ${
                viewMode === "qtypes"
                  ? "bg-card text-foreground shadow-sm font-semibold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Question Types
            </button>
          </div>

          {/* Metric toggle: questions vs marks */}
          <div className="flex items-center bg-muted/60 p-1 rounded-xl border border-border text-xs">
            <button
              onClick={() => setMetricMode("questions")}
              className={`px-2.5 py-1 rounded-lg transition-colors ${
                metricMode === "questions"
                  ? "bg-card text-foreground font-semibold shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Questions
            </button>
            <button
              disabled={!isMarksReliable}
              onClick={() => isMarksReliable && setMetricMode("marks")}
              title={
                isMarksReliable
                  ? "Toggle marks-weighted demand breakdown"
                  : "Marks data incomplete for this historical scope."
              }
              className={`px-2.5 py-1 rounded-lg transition-colors flex items-center gap-1 ${
                metricMode === "marks"
                  ? "bg-card text-foreground font-semibold shadow-sm"
                  : isMarksReliable
                  ? "text-muted-foreground hover:text-foreground"
                  : "opacity-40 cursor-not-allowed text-muted-foreground"
              }`}
            >
              <Scale className="w-3.5 h-3.5" />
              Marks
            </button>
          </div>
        </div>
      </div>

      {/* Non-predictive notice banner */}
      <div className="p-3.5 rounded-xl bg-muted/40 border border-border/70 flex items-start gap-3 text-xs text-muted-foreground">
        <Info className="w-4 h-4 text-muted-foreground shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong className="text-foreground font-medium">Historical Context Notice:</strong> Historical cognitive demand describes the types of tasks observed in archived examinations. It does not measure student difficulty or predict future examination content.
        </p>
      </div>

      {/* Unreliable Marks Notice when relevant */}
      {!isMarksReliable && metricMode === "questions" && (
        <div className="px-3.5 py-2 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-between text-xs text-amber-700 dark:text-amber-300">
          <span className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            Marks data incomplete for this historical scope ({cognitiveDemandDistribution.marks_completeness_pct}% scored). Metrics are displayed as observed question counts.
          </span>
        </div>
      )}

      {/* 2. Proportional Stacked Demand Bar (Global summary) */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs text-muted-foreground font-medium">
          <span>Overall Historical Task Demand Distribution ({totalQuestions} questions)</span>
          <span>{metricMode === "marks" ? "Marks-Weighted Proportions" : "Question-Count Proportions"}</span>
        </div>
        <div className="h-4 w-full bg-muted/70 rounded-full overflow-hidden flex shadow-inner">
          {ORDERED_KEYS.map((k) => {
            const cfg = ARCHETYPE_CONFIGS[k];
            const data = itemsMap[k];
            const val = metricMode === "marks" && data.marksPct !== null ? data.marksPct : data.pct;
            if (val <= 0) return null;
            return (
              <div
                key={k}
                style={{ width: `${val}%` }}
                className={`${cfg.barColor} transition-all duration-300 hover:opacity-90 relative group`}
                title={`${cfg.label}: ${val}% (${data.count} questions)`}
              />
            );
          })}
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-4 pt-1 text-xs">
          {ORDERED_KEYS.map((k) => {
            const cfg = ARCHETYPE_CONFIGS[k];
            const data = itemsMap[k];
            const val = metricMode === "marks" && data.marksPct !== null ? data.marksPct : data.pct;
            return (
              <div key={k} className="flex items-center gap-1.5">
                <span className={`w-2.5 h-2.5 rounded-full ${cfg.barColor}`} />
                <span className="text-foreground font-medium">{cfg.shortLabel}:</span>
                <span className="text-muted-foreground font-mono">{val}%</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. Main Views */}
      {viewMode === "overview" && (
        <div className="space-y-6">
          {/* 4 Archetype Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {ORDERED_KEYS.map((k) => {
              const cfg = ARCHETYPE_CONFIGS[k];
              const data = itemsMap[k];
              const displayVal = metricMode === "marks" && data.marksPct !== null ? data.marksPct : data.pct;

              return (
                <div
                  key={k}
                  className={`rounded-xl border p-4.5 space-y-3 bg-card transition-all shadow-sm ${cfg.borderClass}`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`px-2.5 py-1 rounded-lg text-xs font-semibold ${cfg.bgLight} ${cfg.textClass}`}>
                      {cfg.label}
                    </span>
                    <span className="text-xs font-mono text-muted-foreground">
                      {data.count} Qs
                    </span>
                  </div>

                  <div>
                    <div className="text-2xl font-bold font-mono tracking-tight text-foreground">
                      {displayVal}%
                    </div>
                    <div className="text-[11px] text-muted-foreground mt-0.5 flex items-center justify-between">
                      <span>{data.count} of {totalQuestions} items</span>
                      {data.marksPct !== null && (
                        <span className="font-mono text-foreground/80 font-medium">
                          {data.marksPct}% marks
                        </span>
                      )}
                    </div>
                  </div>

                  <p className="text-xs text-muted-foreground/90 leading-relaxed border-t border-border/50 pt-2">
                    {cfg.description}
                  </p>

                  <div className="text-[11px] text-muted-foreground/75 italic">
                    Examples: {cfg.examples}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Unclassified Evidence Card */}
          <div className="p-4 rounded-xl border border-border bg-muted/20 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <HelpCircle className="w-4 h-4 text-zinc-500" />
                Unclassified Evidence Accounting
              </span>
              <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-zinc-500/10 text-zinc-600 dark:text-zinc-400">
                {unclassifiedPct}% ({unclassifiedCount} Qs)
              </span>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              <strong className="text-foreground">{unclassifiedPct}%</strong> of archived questions have insufficient or conflicting evidence for deterministic demand classification. Uncertainty is explicitly preserved to protect historical fidelity; ambiguous prompts and multi-part questions with conflicting demands are never artificially assigned to clean archetypes.
            </p>
          </div>
        </div>
      )}

      {viewMode === "cycles" && (
        <div className="space-y-4">
          <div className="text-xs text-muted-foreground">
            Side-by-side comparison of historical assessment formats across distinct examination cycles.
          </div>

          {cyclesData.length === 0 ? (
            <div className="p-8 text-center text-xs text-muted-foreground border border-dashed rounded-xl">
              No distinct assessment cycle groupings found for this scope.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {cyclesData.map((c) => {
                return (
                  <div key={c.cycle} className="rounded-xl border border-border p-4.5 bg-card space-y-4 shadow-sm">
                    <div className="flex items-center justify-between border-b border-border/50 pb-2.5">
                      <div>
                        <span className="text-sm font-bold text-foreground">
                          {c.cycle}
                        </span>
                        <span className="block text-[11px] text-muted-foreground">
                          {c.cycle === "CT1" ? "Continuous Assessment Test 1" : c.cycle === "CT2" ? "Continuous Assessment Test 2" : c.cycle === "ENDSEM" ? "End Semester Examination" : "All Cycles"}
                        </span>
                      </div>
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-muted text-foreground font-semibold">
                        {c.total} Qs
                      </span>
                    </div>

                    {/* Cycle stacked mini-bar */}
                    <div className="h-2.5 w-full bg-muted/80 rounded-full overflow-hidden flex">
                      {ORDERED_KEYS.map((k) => {
                        const cnt = c.demands[k] || 0;
                        const pct = c.total > 0 ? (cnt / c.total) * 100 : 0;
                        if (pct <= 0) return null;
                        return (
                          <div
                            key={k}
                            style={{ width: `${pct}%` }}
                            className={ARCHETYPE_CONFIGS[k].barColor}
                            title={`${ARCHETYPE_CONFIGS[k].label}: ${Math.round(pct * 10) / 10}%`}
                          />
                        );
                      })}
                    </div>

                    {/* Breakdown rows */}
                    <div className="space-y-2 text-xs">
                      {ORDERED_KEYS.map((k) => {
                        const cfg = ARCHETYPE_CONFIGS[k];
                        const cnt = c.demands[k] || 0;
                        const pct = c.total > 0 ? Math.round((cnt / c.total) * 1000) / 10 : 0;

                        return (
                          <div key={k} className="flex items-center justify-between py-0.5">
                            <span className="flex items-center gap-1.5 text-muted-foreground">
                              <span className={`w-2 h-2 rounded-full ${cfg.barColor}`} />
                              <span>{cfg.shortLabel}</span>
                            </span>
                            <span className="font-mono text-foreground font-medium">
                              {cnt} <span className="text-[11px] text-muted-foreground">({pct}%)</span>
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {viewMode === "sections" && (
        <div className="space-y-4">
          <div className="text-xs text-muted-foreground">
            Observed demand distribution across normalized examination paper sections.
          </div>

          {sectionCognitiveProfiles.length === 0 ? (
            <div className="p-8 text-center text-xs text-muted-foreground border border-dashed rounded-xl">
              No section-level data available for this course.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {sectionCognitiveProfiles.map((sec) => {
                return (
                  <div key={sec.section_name} className="rounded-xl border border-border p-4.5 bg-card space-y-3.5 shadow-sm">
                    <div className="flex items-center justify-between border-b border-border/50 pb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-foreground">
                          {sec.section_name}
                        </span>
                      </div>
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-muted text-foreground font-semibold">
                        {sec.total_questions} Questions
                      </span>
                    </div>

                    {/* Stacked mini-bar */}
                    <div className="h-2.5 w-full bg-muted/80 rounded-full overflow-hidden flex">
                      {ORDERED_KEYS.map((k) => {
                        const cnt = sec.demand_counts[k] || 0;
                        const pct = sec.total_questions > 0 ? (cnt / sec.total_questions) * 100 : 0;
                        if (pct <= 0) return null;
                        return (
                          <div
                            key={k}
                            style={{ width: `${pct}%` }}
                            className={ARCHETYPE_CONFIGS[k].barColor}
                            title={`${ARCHETYPE_CONFIGS[k].label}: ${Math.round(pct * 10) / 10}%`}
                          />
                        );
                      })}
                    </div>

                    {/* Breakdown pills */}
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {ORDERED_KEYS.map((k) => {
                        const cfg = ARCHETYPE_CONFIGS[k];
                        const cnt = sec.demand_counts[k] || 0;
                        const pct = sec.demand_percentages[k]
                          ? Math.round(sec.demand_percentages[k] * 1000) / 10
                          : 0;

                        return (
                          <div key={k} className="p-2 rounded-lg bg-muted/40 border border-border/40 flex items-center justify-between">
                            <span className="text-[11px] text-muted-foreground flex items-center gap-1">
                              <span className={`w-1.5 h-1.5 rounded-full ${cfg.barColor}`} />
                              {cfg.shortLabel}
                            </span>
                            <span className="font-mono text-xs text-foreground font-semibold">
                              {cnt} <span className="text-[10px] text-muted-foreground">({pct}%)</span>
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {viewMode === "chronology" && (
        <div className="space-y-4">
          <div className="text-xs text-muted-foreground">
            Year-by-year historical demand evolution across verified examination years. Non-contiguous years remain discrete gaps.
          </div>

          {temporalCognitiveDemand.length === 0 ? (
            <div className="p-8 text-center text-xs text-muted-foreground border border-dashed rounded-xl">
              No chronologically dated exams with demand classification available.
            </div>
          ) : (
            <div className="space-y-3">
              {temporalCognitiveDemand.map((yr) => {
                return (
                  <div
                    key={yr.year}
                    className="p-4 rounded-xl border border-border bg-card space-y-3 transition-colors hover:border-foreground/20"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center gap-3">
                        <span className="text-base font-bold font-mono text-foreground flex items-center gap-1.5">
                          <Calendar className="w-4 h-4 text-accent" />
                          {yr.year}
                        </span>
                        <span className="text-xs text-muted-foreground font-mono">
                          {yr.exam_count} paper{yr.exam_count === 1 ? "" : "s"} ({yr.total_questions} Qs)
                        </span>
                        {yr.is_sparse && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/20">
                            Sparse historical data
                          </span>
                        )}
                      </div>

                      {yr.marks_percentages && (
                        <span className="text-[11px] font-mono text-muted-foreground">
                          {yr.scored_marks} scored marks evaluated
                        </span>
                      )}
                    </div>

                    {/* Stacked bar */}
                    <div className="h-3 w-full bg-muted/80 rounded-full overflow-hidden flex">
                      {ORDERED_KEYS.map((k) => {
                        const cnt = yr.demand_counts[k] || 0;
                        const pct = yr.total_questions > 0 ? (cnt / yr.total_questions) * 100 : 0;
                        if (pct <= 0) return null;
                        return (
                          <div
                            key={k}
                            style={{ width: `${pct}%` }}
                            className={ARCHETYPE_CONFIGS[k].barColor}
                            title={`${ARCHETYPE_CONFIGS[k].label}: ${Math.round(pct * 10) / 10}%`}
                          />
                        );
                      })}
                    </div>

                    {/* Proportions list */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-xs">
                      {ORDERED_KEYS.map((k) => {
                        const cfg = ARCHETYPE_CONFIGS[k];
                        const cnt = yr.demand_counts[k] || 0;
                        const pct = yr.demand_percentages[k]
                          ? Math.round(yr.demand_percentages[k] * 1000) / 10
                          : 0;

                        return (
                          <div key={k} className="flex items-center justify-between px-2 py-1 rounded bg-muted/30 border border-border/30">
                            <span className="text-[11px] text-muted-foreground flex items-center gap-1">
                              <span className={`w-1.5 h-1.5 rounded-full ${cfg.barColor}`} />
                              {cfg.shortLabel}
                            </span>
                            <span className="font-mono text-xs font-semibold text-foreground">
                              {cnt} <span className="text-[10px] text-muted-foreground">({pct}%)</span>
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {viewMode === "qtypes" && (
        <div className="space-y-4">
          <div className="text-xs text-muted-foreground">
            Empirical mapping between verifiable historical question types and cognitive demand archetypes.
          </div>

          {qtypeMatrix.length === 0 ? (
            <div className="p-8 text-center text-xs text-muted-foreground border border-dashed rounded-xl">
              No question-type cross-tabulation data available.
            </div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-border">
              <table className="w-full text-xs text-left">
                <thead className="bg-muted/50 border-b border-border text-muted-foreground font-semibold uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="py-2.5 px-3">Question Type</th>
                    <th className="py-2.5 px-3 text-right">Total</th>
                    <th className="py-2.5 px-3 text-blue-600 dark:text-blue-400">Recall & Concept</th>
                    <th className="py-2.5 px-3 text-emerald-600 dark:text-emerald-400">Procedural</th>
                    <th className="py-2.5 px-3 text-purple-600 dark:text-purple-400">Analytical</th>
                    <th className="py-2.5 px-3 text-zinc-500">Unclassified</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {qtypeMatrix.map((row) => (
                    <tr key={row.qtype} className="hover:bg-muted/30 transition-colors">
                      <td className="py-2.5 px-3 font-medium text-foreground">
                        {row.qtype}
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono font-semibold text-foreground">
                        {row.total}
                      </td>
                      <td className="py-2.5 px-3 font-mono">
                        {row.counts["RECALL_AND_CONCEPT"] > 0 ? (
                          <span className="text-blue-600 dark:text-blue-400 font-semibold">
                            {row.counts["RECALL_AND_CONCEPT"]}{" "}
                            <span className="text-[10px] text-muted-foreground font-normal">
                              ({Math.round((row.counts["RECALL_AND_CONCEPT"] / row.total) * 100)}%)
                            </span>
                          </span>
                        ) : (
                          <span className="text-muted-foreground/40">—</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 font-mono">
                        {row.counts["PROCEDURAL_COMPUTATION"] > 0 ? (
                          <span className="text-emerald-600 dark:text-emerald-400 font-semibold">
                            {row.counts["PROCEDURAL_COMPUTATION"]}{" "}
                            <span className="text-[10px] text-muted-foreground font-normal">
                              ({Math.round((row.counts["PROCEDURAL_COMPUTATION"] / row.total) * 100)}%)
                            </span>
                          </span>
                        ) : (
                          <span className="text-muted-foreground/40">—</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 font-mono">
                        {row.counts["ANALYTICAL_PROOF_AND_DESIGN"] > 0 ? (
                          <span className="text-purple-600 dark:text-purple-400 font-semibold">
                            {row.counts["ANALYTICAL_PROOF_AND_DESIGN"]}{" "}
                            <span className="text-[10px] text-muted-foreground font-normal">
                              ({Math.round((row.counts["ANALYTICAL_PROOF_AND_DESIGN"] / row.total) * 100)}%)
                            </span>
                          </span>
                        ) : (
                          <span className="text-muted-foreground/40">—</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 font-mono">
                        {row.counts["UNCLASSIFIED"] > 0 ? (
                          <span className="text-zinc-500 font-semibold">
                            {row.counts["UNCLASSIFIED"]}{" "}
                            <span className="text-[10px] text-muted-foreground font-normal">
                              ({Math.round((row.counts["UNCLASSIFIED"] / row.total) * 100)}%)
                            </span>
                          </span>
                        ) : (
                          <span className="text-muted-foreground/40">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
