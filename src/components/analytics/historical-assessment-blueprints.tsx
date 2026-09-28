"use client";

import React, { useState, useMemo } from "react";
import {
  Layers,
  FileText,
  Calendar,
  AlertCircle,
  CheckCircle2,
  GitCompare,
  Split,
  ChevronDown,
  ChevronUp,
  Info
} from "lucide-react";
import { BlueprintCluster, SectionBlueprint } from "@/lib/types";

interface Props {
  assessmentBlueprints?: BlueprintCluster[];
  selectedCycle?: string;
  onCycleChange?: (cycle: string) => void;
}

export function HistoricalAssessmentBlueprints({
  assessmentBlueprints = [],
  selectedCycle = "ALL",
  onCycleChange
}: Props) {
  const [internalCycle, setInternalCycle] = useState<string>("ALL");
  const [viewMode, setViewMode] = useState<"cards" | "comparison" | "timeline">("cards");
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});

  // Sync with prop if provided
  const activeCycle = selectedCycle !== "ALL" ? selectedCycle : internalCycle;

  const handleCycleSelect = (cycle: string) => {
    setInternalCycle(cycle);
    if (onCycleChange) {
      onCycleChange(cycle);
    }
  };

  const toggleSectionExpand = (clusterSig: string, secIdx: number) => {
    const key = `${clusterSig}_${secIdx}`;
    setExpandedSections((prev) => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  // Distinct cycles present across the extracted blueprint clusters
  const availableCycles = useMemo(() => {
    const cycleSet = new Set<string>();
    for (const b of assessmentBlueprints) {
      const c = b.representative_blueprint.assessment_cycle;
      if (c && c !== "ALL") {
        cycleSet.add(c);
      }
      if (b.assessment_cycles_observed) {
        for (const ac of b.assessment_cycles_observed) {
          if (ac && ac !== "ALL") cycleSet.add(ac);
        }
      }
    }
    return ["ALL", ...Array.from(cycleSet).sort()];
  }, [assessmentBlueprints]);

  // Filter clusters by the active cycle
  const filteredClusters = useMemo(() => {
    if (activeCycle === "ALL") {
      return assessmentBlueprints;
    }
    return assessmentBlueprints.filter((b) => {
      const repCycle = b.representative_blueprint.assessment_cycle;
      if (repCycle === activeCycle) return true;
      if (b.assessment_cycles_observed?.includes(activeCycle)) return true;
      return false;
    });
  }, [assessmentBlueprints, activeCycle]);

  // Overall metadata metrics
  const totalAnalyzedPapers = useMemo(() => {
    return filteredClusters.reduce((sum, c) => sum + c.matching_paper_count, 0);
  }, [filteredClusters]);

  const distinctYears = useMemo(() => {
    const years = new Set<number>();
    for (const c of filteredClusters) {
      for (const y of c.years_observed) {
        if (y) years.add(y);
      }
    }
    return Array.from(years).sort((a, b) => a - b);
  }, [filteredClusters]);

  // Helper: Status label & badge style
  const getStatusBadge = (status: string, isDominant: boolean) => {
    if (isDominant) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
          <CheckCircle2 className="w-3 h-3" />
          Dominant Structure
        </span>
      );
    }
    if (status === "RECURRING_STRUCTURE") {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
          <Layers className="w-3 h-3" />
          Recurring Structure
        </span>
      );
    }
    if (status === "STRUCTURAL_VARIANT") {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
          <Split className="w-3 h-3" />
          Structural Variant
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-muted text-muted-foreground border border-border">
        <FileText className="w-3 h-3" />
        Single Observed Paper
      </span>
    );
  };

  // Helper: Choice text
  const formatChoiceDirective = (sec: SectionBlueprint) => {
    if (sec.choice_detail) {
      return sec.choice_detail;
    }
    if (sec.choice_type === "COMPULSORY") {
      return "Compulsory (Answer All Questions)";
    }
    if (sec.choice_type === "UNITARY_CHOICE") {
      return "Unitary Choice (Answer Any One)";
    }
    if (sec.choice_type === "SELECTIVE_CHOICE") {
      return "Selective Choice";
    }
    if (sec.has_internal_choice && sec.internal_choice_pairs > 0) {
      return `${sec.internal_choice_pairs} Internal Choice Pair${sec.internal_choice_pairs > 1 ? "s" : ""}`;
    }
    return "Choice rule unspecified in archive";
  };

  if (!assessmentBlueprints || assessmentBlueprints.length === 0) {
    return (
      <section className="bg-card border border-border rounded-2xl p-6 md:p-8 shadow-sm space-y-4">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-accent" />
          <h3 className="text-lg font-bold tracking-tight text-foreground">
            Historical Assessment Structure & Blueprints
          </h3>
        </div>
        <div className="p-8 text-center bg-muted/20 border border-border/50 rounded-xl space-y-2">
          <p className="text-xs font-medium text-foreground">
            No segmented examination blueprints recorded in the archive for this selection.
          </p>
          <p className="text-[11px] text-muted-foreground max-w-md mx-auto">
            Historical examinations for this course either lack distinct section boundaries or are archived without structured section instructions.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="bg-card border border-border rounded-2xl p-6 md:p-8 shadow-sm space-y-6">
      {/* 1. Header & Quick Metrics */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/50 pb-4">
        <div>
          <h3 className="text-lg font-bold tracking-tight text-foreground flex items-center gap-2">
            <Layers className="w-5 h-5 text-accent" />
            Historical Assessment Structure & Blueprints
          </h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Observed examination architectures, section patterns, and marks allocation across archived exam papers
          </p>
        </div>

        {/* Aggregate Paper & Structure Count */}
        <div className="flex items-center gap-2">
          <div className="px-3 py-1.5 rounded-lg bg-accent/10 text-accent border border-accent/20 text-xs font-semibold">
            {filteredClusters.length} Observed Structure{filteredClusters.length > 1 ? "s" : ""} ({totalAnalyzedPapers} Paper{totalAnalyzedPapers !== 1 ? "s" : ""})
          </div>
        </div>
      </div>

      {/* 2. Non-Predictive Notice Callout */}
      <div className="p-3.5 rounded-xl bg-muted/20 border border-border/40 text-xs text-muted-foreground flex items-start gap-2.5">
        <Info className="w-4 h-4 text-accent shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-semibold text-foreground">
            Historical Descriptive Archive Notice
          </p>
          <p className="text-[11px] leading-relaxed">
            Historical structures describe archived examinations and do not predict the structure of future examinations. Question counts, internal choices, and marks distributions reflect observed past papers only. Examination formats may change at institutional discretion.
          </p>
        </div>
      </div>

      {/* 3. Controls: Assessment Cycle Filter & View Mode */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-muted/20 p-3 rounded-xl border border-border/60">
        {/* Cycle Filter */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold text-foreground whitespace-nowrap">
            Assessment Cycle:
          </span>
          <div className="inline-flex rounded-lg border border-border p-0.5 bg-background text-xs">
            {availableCycles.map((c) => {
              const label =
                c === "ALL"
                  ? "All Cycles"
                  : c === "ENDSEM"
                  ? "End-Semester"
                  : c === "CT1"
                  ? "Class Test 1"
                  : c === "CT2"
                  ? "Class Test 2"
                  : c;
              const count =
                c === "ALL"
                  ? assessmentBlueprints.reduce((sum, b) => sum + b.matching_paper_count, 0)
                  : assessmentBlueprints
                      .filter(
                        (b) =>
                          b.representative_blueprint.assessment_cycle === c ||
                          b.assessment_cycles_observed?.includes(c)
                      )
                      .reduce((sum, b) => sum + b.matching_paper_count, 0);

              return (
                <button
                  key={c}
                  onClick={() => handleCycleSelect(c)}
                  className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                    activeCycle === c
                      ? "bg-accent text-accent-foreground font-semibold shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {label} <span className="opacity-75 text-[10px]">({count})</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* View Mode Toggle */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-foreground whitespace-nowrap">
            View:
          </span>
          <div className="inline-flex rounded-lg border border-border p-0.5 bg-background text-xs">
            <button
              onClick={() => setViewMode("cards")}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                viewMode === "cards"
                  ? "bg-accent text-accent-foreground font-semibold shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              Observed Blueprints
            </button>

            {filteredClusters.length > 1 && (
              <button
                onClick={() => setViewMode("comparison")}
                className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                  viewMode === "comparison"
                    ? "bg-accent text-accent-foreground font-semibold shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <GitCompare className="w-3.5 h-3.5" />
                Structural Comparison
              </button>
            )}

            {distinctYears.length > 0 && (
              <button
                onClick={() => setViewMode("timeline")}
                className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                  viewMode === "timeline"
                    ? "bg-accent text-accent-foreground font-semibold shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Calendar className="w-3.5 h-3.5" />
                Timeline Coverage
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 4. Main Content Based on View Mode */}

      {/* VIEW A: Blueprint Cards */}
      {viewMode === "cards" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {filteredClusters.map((cluster, cIdx) => {
              const rep = cluster.representative_blueprint;
              const letterIndex = String.fromCharCode(65 + cIdx); // A, B, C...

              return (
                <div
                  key={cluster.signature}
                  className={`flex flex-col justify-between rounded-xl border bg-card/60 p-5 space-y-4 shadow-sm transition-all hover:border-accent/40 ${
                    cluster.is_dominant
                      ? "border-emerald-500/40 ring-1 ring-emerald-500/10"
                      : "border-border/80"
                  }`}
                >
                  {/* Card Top: Title, Status Badge, Cycle */}
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                          Structure {letterIndex} • {rep.assessment_cycle}
                        </div>
                        <h4 className="text-base font-bold text-foreground">
                          {rep.section_count}-Section Paper Structure
                        </h4>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        {getStatusBadge(cluster.status, cluster.is_dominant)}
                        {cluster.is_sparse && (
                          <span className="text-[10px] text-amber-600 dark:text-amber-400">
                            Sparse observation (1 paper)
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Observation Summary Line */}
                    <div className="text-xs text-muted-foreground flex flex-wrap items-center gap-x-3 gap-y-1 pt-1">
                      <span className="font-semibold text-foreground">
                        Observed in {cluster.matching_paper_count} exam{cluster.matching_paper_count > 1 ? "s" : ""}{" "}
                        <span className="text-muted-foreground font-normal">
                          ({cluster.percentage_of_cycle}% of {rep.assessment_cycle} cycle)
                        </span>
                      </span>
                      <span>•</span>
                      <span>
                        Observed Years:{" "}
                        <strong className="text-foreground">
                          {cluster.years_observed.length > 0
                            ? cluster.years_observed.join(", ")
                            : "No verified year"}
                        </strong>
                      </span>
                    </div>
                  </div>

                  {/* Quantitative Metrics Bar */}
                  <div className="grid grid-cols-3 gap-2 p-3 rounded-lg bg-muted/40 border border-border/50 text-center">
                    <div>
                      <div className="text-[10px] text-muted-foreground uppercase font-medium">
                        Total Questions
                      </div>
                      <div className="text-sm font-bold text-foreground">
                        {rep.total_questions} Qs
                      </div>
                      <div className="text-[10px] text-muted-foreground">
                        {rep.primary_questions} primary{rep.alternative_questions > 0 ? ` + ${rep.alternative_questions} alts` : ""}
                      </div>
                    </div>

                    <div>
                      <div className="text-[10px] text-muted-foreground uppercase font-medium">
                        Scored Marks
                      </div>
                      <div className="text-sm font-bold text-foreground">
                        {rep.total_scored_marks} Marks
                      </div>
                      <div className="text-[10px] text-muted-foreground">
                        Sum of scored Qs
                      </div>
                    </div>

                    <div>
                      <div className="text-[10px] text-muted-foreground uppercase font-medium">
                        Offered Marks
                      </div>
                      <div className="text-sm font-bold text-accent">
                        {rep.total_offered_marks} Marks
                      </div>
                      <div className="text-[10px] text-muted-foreground">
                        With choice pool
                      </div>
                    </div>
                  </div>

                  {/* Missing marks flag if paper has unscored questions */}
                  {rep.has_unscored_questions && (
                    <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-700 dark:text-amber-400 flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 shrink-0" />
                      <span>
                        <strong>Incomplete Marks Data:</strong> One or more questions in this blueprint do not specify numeric marks in the archive.
                      </span>
                    </div>
                  )}

                  {/* Section-by-Section Details */}
                  <div className="space-y-2 pt-2 border-t border-border/40">
                    <div className="text-xs font-semibold text-foreground uppercase tracking-wider flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5 text-accent" />
                      Section-by-Section Composition
                    </div>

                    <div className="space-y-2">
                      {rep.sections.map((sec, secIdx) => {
                        const secKey = `${cluster.signature}_${secIdx}`;
                        const isExpanded = !!expandedSections[secKey];
                        const marksStr =
                          sec.marks_per_question.length > 0
                            ? `${sec.marks_per_question.join("/")} mark${sec.marks_per_question.length > 1 || sec.marks_per_question[0] !== 1 ? "s" : ""} each`
                            : "unscored";

                        return (
                          <div
                            key={secIdx}
                            className="p-3 rounded-lg border border-border/60 bg-background/80 space-y-2"
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="space-y-0.5">
                                <div className="text-xs font-bold text-foreground flex items-center gap-2">
                                  <span>{sec.name.replace("_", " ")}</span>
                                  {sec.question_number_range && (
                                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground font-normal">
                                      Q. {sec.question_number_range}
                                    </span>
                                  )}
                                </div>
                                <div className="text-xs text-muted-foreground">
                                  {sec.total_questions} question{sec.total_questions !== 1 ? "s" : ""} •{" "}
                                  <strong className="text-foreground">{marksStr}</strong> •{" "}
                                  <strong className="text-accent">{sec.scored_marks_sum} marks</strong>
                                </div>
                              </div>

                              <div className="text-right">
                                <span className="text-[11px] font-medium text-muted-foreground block">
                                  {sec.has_internal_choice ? (
                                    <span className="text-foreground font-semibold">
                                      Internal Choice
                                    </span>
                                  ) : (
                                    <span>Compulsory</span>
                                  )}
                                </span>
                              </div>
                            </div>

                            {/* Choice Directive / Instructions */}
                            <div className="text-[11px] text-muted-foreground/90 bg-muted/30 px-2 py-1 rounded border border-border/40">
                              <span className="font-semibold text-foreground">Rule:</span>{" "}
                              {formatChoiceDirective(sec)}
                            </div>

                            {/* Unscored section warning */}
                            {sec.has_unscored_questions && (
                              <div className="text-[11px] text-amber-600 dark:text-amber-400">
                                ⚠ {sec.unscored_questions_count} question(s) unscored in archive
                              </div>
                            )}

                            {/* Expandable Section Composition (Unit & Question Types) */}
                            <div className="pt-1">
                              <button
                                type="button"
                                onClick={() => toggleSectionExpand(cluster.signature, secIdx)}
                                className="inline-flex items-center gap-1 text-[11px] text-accent hover:underline font-medium"
                              >
                                {isExpanded ? (
                                  <>
                                    <ChevronUp className="w-3 h-3" />
                                    Hide Question Types & Unit Distribution
                                  </>
                                ) : (
                                  <>
                                    <ChevronDown className="w-3 h-3" />
                                    View Question Types & Unit Distribution
                                  </>
                                )}
                              </button>

                              {isExpanded && (
                                <div className="mt-2.5 p-2.5 rounded-lg bg-muted/30 border border-border/40 space-y-3 text-xs">
                                  {/* Question Types */}
                                  <div>
                                    <div className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
                                      Observed Question Types
                                    </div>
                                    <div className="flex flex-wrap gap-1.5">
                                      {Object.entries(sec.question_types).map(([qt, count]) => (
                                        <span
                                          key={qt}
                                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-background border border-border text-[11px] font-medium text-foreground"
                                        >
                                          {qt}: <strong>{count}Q</strong>
                                        </span>
                                      ))}
                                    </div>
                                  </div>

                                  {/* Unit Distribution */}
                                  <div>
                                    <div className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
                                      Syllabus Unit Distribution
                                    </div>
                                    <div className="flex flex-wrap gap-1.5">
                                      {Object.entries(sec.unit_distribution).map(([uName, count]) => (
                                        <span
                                          key={uName}
                                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[11px] font-medium ${
                                            uName.toLowerCase().includes("unmapped")
                                              ? "bg-amber-500/10 border-amber-500/20 text-amber-700 dark:text-amber-400"
                                              : "bg-background border-border text-foreground"
                                          }`}
                                        >
                                          {uName}: <strong>{count}Q</strong>
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* VIEW B: Structural Comparison Matrix */}
      {viewMode === "comparison" && filteredClusters.length > 1 && (
        <div className="space-y-4">
          <div className="p-3 rounded-lg bg-muted/20 border border-border/40 text-xs text-muted-foreground">
            <strong>Side-by-side Structural Comparison:</strong> Identifies architectural differences across distinct observed blueprints. MintAI describes verified archive patterns and does not rank or prescribe any blueprint as standard.
          </div>

          <div className="overflow-x-auto rounded-xl border border-border">
            <table className="w-full text-xs text-left divide-y divide-border">
              <thead className="bg-muted/40">
                <tr>
                  <th className="p-3 font-semibold text-muted-foreground min-w-[160px]">
                    Structural Dimension
                  </th>
                  {filteredClusters.map((cluster, idx) => (
                    <th key={cluster.signature} className="p-3 font-bold text-foreground min-w-[200px]">
                      <div className="flex items-center justify-between gap-1">
                        <span>Structure {String.fromCharCode(65 + idx)}</span>
                        {getStatusBadge(cluster.status, cluster.is_dominant)}
                      </div>
                      <div className="text-[11px] font-normal text-muted-foreground mt-0.5">
                        {cluster.matching_paper_count} paper{cluster.matching_paper_count !== 1 ? "s" : ""} ({cluster.percentage_of_cycle}%)
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border bg-card">
                {/* Cycle */}
                <tr>
                  <td className="p-3 font-semibold text-muted-foreground">Assessment Cycle</td>
                  {filteredClusters.map((c) => (
                    <td key={c.signature} className="p-3 font-medium text-foreground">
                      {c.representative_blueprint.assessment_cycle}
                    </td>
                  ))}
                </tr>

                {/* Observed Years */}
                <tr>
                  <td className="p-3 font-semibold text-muted-foreground">Observed Years</td>
                  {filteredClusters.map((c) => (
                    <td key={c.signature} className="p-3 text-foreground">
                      {c.years_observed.length > 0 ? c.years_observed.join(", ") : "Unspecified"}
                    </td>
                  ))}
                </tr>

                {/* Section Count */}
                <tr>
                  <td className="p-3 font-semibold text-muted-foreground">Section Count</td>
                  {filteredClusters.map((c) => (
                    <td key={c.signature} className="p-3 font-bold text-foreground">
                      {c.representative_blueprint.section_count} Sections
                    </td>
                  ))}
                </tr>

                {/* Total Questions */}
                <tr>
                  <td className="p-3 font-semibold text-muted-foreground">Total Questions</td>
                  {filteredClusters.map((c) => (
                    <td key={c.signature} className="p-3 text-foreground">
                      <strong className="text-foreground">{c.representative_blueprint.total_questions} Questions</strong>
                      <span className="block text-[11px] text-muted-foreground">
                        {c.representative_blueprint.primary_questions} primary, {c.representative_blueprint.alternative_questions} alternative
                      </span>
                    </td>
                  ))}
                </tr>

                {/* Paper Marks */}
                <tr>
                  <td className="p-3 font-semibold text-muted-foreground">Marks Allocation</td>
                  {filteredClusters.map((c) => (
                    <td key={c.signature} className="p-3 text-foreground">
                      <strong className="text-accent">{c.representative_blueprint.total_scored_marks} scored</strong>
                      <span className="block text-[11px] text-muted-foreground">
                        {c.representative_blueprint.total_offered_marks} total offered marks
                      </span>
                    </td>
                  ))}
                </tr>

                {/* Section Breakdown Summary */}
                <tr>
                  <td className="p-3 font-semibold text-muted-foreground align-top">Section Composition</td>
                  {filteredClusters.map((c) => (
                    <td key={c.signature} className="p-3 space-y-1 align-top">
                      {c.representative_blueprint.sections.map((sec, i) => (
                        <div key={i} className="text-[11px] text-foreground">
                          <strong>{sec.name.replace("_", " ")}:</strong> {sec.total_questions}Q ×{" "}
                          {sec.marks_per_question.join("/") || "unscored"}m ({sec.scored_marks_sum}m)
                        </div>
                      ))}
                    </td>
                  ))}
                </tr>

                {/* Choice Rules */}
                <tr>
                  <td className="p-3 font-semibold text-muted-foreground align-top">Choice Directives</td>
                  {filteredClusters.map((c) => (
                    <td key={c.signature} className="p-3 space-y-1 align-top">
                      {c.representative_blueprint.sections.map((sec, i) => (
                        <div key={i} className="text-[11px] text-muted-foreground">
                          <strong className="text-foreground">{sec.name.replace("_", " ")}:</strong>{" "}
                          {formatChoiceDirective(sec)}
                        </div>
                      ))}
                    </td>
                  ))}
                </tr>

                {/* Incomplete Data Status */}
                <tr>
                  <td className="p-3 font-semibold text-muted-foreground">Data Completeness</td>
                  {filteredClusters.map((c) => (
                    <td key={c.signature} className="p-3 text-[11px]">
                      {c.representative_blueprint.has_unscored_questions ? (
                        <span className="text-amber-600 dark:text-amber-400 font-medium">
                          Contains unscored questions
                        </span>
                      ) : (
                        <span className="text-emerald-600 dark:text-emerald-400 font-medium">
                          Complete marks recorded
                        </span>
                      )}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* VIEW C: Historical Timeline Coverage */}
      {viewMode === "timeline" && distinctYears.length > 0 && (
        <div className="space-y-4">
          <div className="p-3 rounded-lg bg-muted/20 border border-border/40 text-xs text-muted-foreground">
            <strong>Historical Year-by-Year Observation Grid:</strong> Displays which years used each observed structural blueprint. Missing years reflect gaps in the archive and are strictly unrepresented rather than interpolated.
          </div>

          <div className="overflow-x-auto rounded-xl border border-border p-4 bg-muted/10">
            <div className="min-w-[600px] space-y-3">
              {/* Year Headers */}
              <div className="grid grid-cols-12 gap-2 text-center text-xs font-bold text-muted-foreground border-b border-border/60 pb-2">
                <div className="col-span-4 text-left">Observed Structure</div>
                <div className="col-span-8 grid" style={{ gridTemplateColumns: `repeat(${distinctYears.length}, minmax(0, 1fr))` }}>
                  {distinctYears.map((yr) => (
                    <span key={yr} className="text-foreground">
                      {yr}
                    </span>
                  ))}
                </div>
              </div>

              {/* Rows */}
              {filteredClusters.map((c, idx) => {
                const letter = String.fromCharCode(65 + idx);
                const observedYearsSet = new Set(c.years_observed);

                return (
                  <div
                    key={c.signature}
                    className="grid grid-cols-12 gap-2 items-center text-xs py-2 border-b border-border/30 last:border-0 hover:bg-muted/30 rounded px-1"
                  >
                    <div className="col-span-4 flex items-center gap-2">
                      <span className="font-bold text-foreground">
                        Structure {letter}
                      </span>
                      <span className="text-[11px] text-muted-foreground truncate">
                        ({c.representative_blueprint.section_count} Sec, {c.representative_blueprint.total_questions}Q)
                      </span>
                    </div>

                    <div className="col-span-8 grid text-center" style={{ gridTemplateColumns: `repeat(${distinctYears.length}, minmax(0, 1fr))` }}>
                      {distinctYears.map((yr) => {
                        const isObserved = observedYearsSet.has(yr);
                        return (
                          <div key={yr} className="flex justify-center items-center py-1">
                            {isObserved ? (
                              <span
                                title={`Structure ${letter} observed in ${yr}`}
                                className={`w-6 h-6 rounded-full inline-flex items-center justify-center text-[10px] font-bold ${
                                  c.is_dominant
                                    ? "bg-emerald-500 text-white shadow-sm"
                                    : "bg-accent text-accent-foreground shadow-sm"
                                }`}
                              >
                                ✓
                              </span>
                            ) : (
                              <span
                                title={`No observation in ${yr}`}
                                className="w-1.5 h-1.5 rounded-full bg-border block"
                              />
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
