"use client";

import React, { useState, useMemo } from "react";
import {
  Compass,
  Layers,
  AlertCircle,
  Info,
  Clock,
  FileQuestion
} from "lucide-react";
import {
  TemporalUnitFocusBreakdown,
  TopicHistoricalFootprint,
  TemporalTopicFocusBreakdown,
  UnitDNA
} from "@/lib/types";
import { HistoricalFocusChart, FocusChartRow } from "@/components/charts/historical-focus-chart";

interface Props {
  temporalUnitFocus?: TemporalUnitFocusBreakdown[];
  topicHistoricalFootprints?: TopicHistoricalFootprint[];
  temporalTopicFocus?: TemporalTopicFocusBreakdown[];
  syllabusUnits?: UnitDNA[];
}

export function HistoricalFocusEvolution({
  temporalUnitFocus = [],
  topicHistoricalFootprints = [],
  temporalTopicFocus = [],
  syllabusUnits = []
}: Props) {
  const [selectedUnit, setSelectedUnit] = useState<string>("ALL");
  const [metricMode, setMetricMode] = useState<"questions" | "marks">("questions");

  // 1. Resolve Available Syllabus Units
  const { availableUnits, unmappedUnitPresent } = useMemo(() => {
    const unitSet = new Set<string>();
    let unmappedFound = false;

    for (const r of temporalUnitFocus) {
      if (!r.unit) continue;
      if (r.unit.toLowerCase().includes("unmapped")) {
        unmappedFound = true;
      } else {
        unitSet.add(r.unit);
      }
    }
    for (const r of temporalTopicFocus) {
      if (!r.unit) continue;
      if (r.unit.toLowerCase().includes("unmapped")) {
        unmappedFound = true;
      } else {
        unitSet.add(r.unit);
      }
    }

    // Sort syllabus units by official syllabus order if available
    const officialNames = (syllabusUnits || []).map((u) => u.unit);
    const sorted: string[] = [];

    for (const name of officialNames) {
      if (unitSet.has(name)) {
        sorted.push(name);
        unitSet.delete(name);
      }
    }
    for (const rem of Array.from(unitSet).sort()) {
      sorted.push(rem);
    }

    if (unmappedFound) {
      sorted.push("Unmapped / Unknown");
    }

    return {
      availableUnits: sorted,
      unmappedUnitPresent: unmappedFound
    };
  }, [temporalUnitFocus, temporalTopicFocus, syllabusUnits]);

  // Total distinct historical exam years in dataset
  const allRecordedYears = useMemo(() => {
    const years = new Set<number>();
    for (const r of temporalUnitFocus) {
      if (r.year) years.add(r.year);
    }
    for (const r of temporalTopicFocus) {
      if (r.year) years.add(r.year);
    }
    return Array.from(years).sort((a, b) => a - b);
  }, [temporalUnitFocus, temporalTopicFocus]);

  // 2. Data for "ALL" units view (Syllabus Units Overview)
  const { allUnitsChartData, allUnitsHasSparse, allUnitsHasUnscored } = useMemo(() => {
    if (!temporalUnitFocus.length) {
      return { allUnitsChartData: [], allUnitsHasSparse: false, allUnitsHasUnscored: false };
    }

    const yearMap = new Map<number, FocusChartRow>();
    let sparseFound = false;
    let unscoredFound = false;

    for (const r of temporalUnitFocus) {
      const y = r.year;
      if (!yearMap.has(y)) {
        if (r.is_sparse) sparseFound = true;
        yearMap.set(y, {
          yearLabel: `${y}`,
          year: y,
          isSparse: r.is_sparse,
          examCount: r.exam_count,
          totalQuestions: 0,
          totalMarks: 0
        });
      }
      const entry = yearMap.get(y)!;
      entry.totalQuestions += r.question_count;
      entry.totalMarks = Math.round((entry.totalMarks + r.scored_marks) * 10) / 10;

      const unitKey = r.unit;
      entry[unitKey] = metricMode === "questions" ? r.question_percentage : r.marks_weight_percentage;
      entry[`${unitKey}_count`] = r.question_count;
      entry[`${unitKey}_marks`] = r.scored_marks;
    }

    for (const entry of yearMap.values()) {
      if (entry.totalMarks === 0 && entry.totalQuestions > 0) {
        unscoredFound = true;
      }
    }

    const chartData = Array.from(yearMap.values()).sort((a, b) => a.year - b.year);
    return {
      allUnitsChartData: chartData,
      allUnitsHasSparse: sparseFound,
      allUnitsHasUnscored: unscoredFound
    };
  }, [temporalUnitFocus, metricMode]);

  // 3. Data for single Unit view (Topics within Unit)
  const unitTopicData = useMemo(() => {
    if (selectedUnit === "ALL") return null;

    const isTargetUnmapped = selectedUnit.toLowerCase().includes("unmapped");
    const filteredTopicRows = temporalTopicFocus.filter((r) => {
      if (isTargetUnmapped) {
        return r.unit.toLowerCase().includes("unmapped") || r.topic.toLowerCase().includes("unmapped");
      }
      return r.unit === selectedUnit;
    });

    const relevantFootprints = topicHistoricalFootprints.filter((f) => {
      if (isTargetUnmapped) {
        return f.unit_name.toLowerCase().includes("unmapped") || f.topic_name.toLowerCase().includes("unmapped");
      }
      return f.unit_name === selectedUnit;
    });

    // Collect distinct topics in this unit
    const topicNames = Array.from(new Set(filteredTopicRows.map((r) => r.topic))).sort();

    const yearMap = new Map<number, FocusChartRow>();
    let sparseFound = false;
    let unscoredFound = false;

    for (const r of filteredTopicRows) {
      const y = r.year;
      if (!yearMap.has(y)) {
        if (r.is_sparse) sparseFound = true;
        yearMap.set(y, {
          yearLabel: `${y}`,
          year: y,
          isSparse: r.is_sparse,
          examCount: r.exam_count,
          totalQuestions: 0,
          totalMarks: 0
        });
      }
      const entry = yearMap.get(y)!;
      entry.totalQuestions += r.question_count;
      entry.totalMarks = Math.round((entry.totalMarks + r.scored_marks) * 10) / 10;

      const tKey = r.topic;
      entry[tKey] = metricMode === "questions" ? r.question_percentage : r.marks_weight_percentage;
      entry[`${tKey}_count`] = r.question_count;
      entry[`${tKey}_marks`] = r.scored_marks;
    }

    for (const entry of yearMap.values()) {
      if (entry.totalMarks === 0 && entry.totalQuestions > 0) {
        unscoredFound = true;
      }
    }

    const chartData = Array.from(yearMap.values()).sort((a, b) => a.year - b.year);

    return {
      topicRows: filteredTopicRows,
      footprints: relevantFootprints,
      topicNames,
      chartData,
      hasSparse: sparseFound,
      hasUnscored: unscoredFound
    };
  }, [selectedUnit, temporalTopicFocus, topicHistoricalFootprints, metricMode]);

  // Overall check if component has any temporal focus data
  const hasData = temporalUnitFocus.length > 0 || temporalTopicFocus.length > 0;
  if (!hasData) {
    return (
      <section className="bg-card border border-border rounded-2xl p-6 md:p-8 shadow-sm space-y-4">
        <div className="flex items-center gap-2">
          <Compass className="w-5 h-5 text-accent" />
          <h3 className="text-lg font-bold tracking-tight text-foreground">
            Historical Exam Focus Evolution: Syllabus & Topics
          </h3>
        </div>
        <p className="text-xs text-muted-foreground">
          No multi-year syllabus focus or topic evolution data is recorded for this course in the archive.
        </p>
      </section>
    );
  }

  // Active view parameters
  const isAllUnits = selectedUnit === "ALL";
  const activeChartData = isAllUnits ? allUnitsChartData : unitTopicData?.chartData || [];
  const activeSeriesKeys = isAllUnits ? availableUnits : unitTopicData?.topicNames || [];
  const activeHasSparse = isAllUnits ? allUnitsHasSparse : unitTopicData?.hasSparse || false;
  const activeHasUnscored = isAllUnits ? allUnitsHasUnscored : unitTopicData?.hasUnscored || false;
  const isViewingUnmapped = selectedUnit.toLowerCase().includes("unmapped");

  return (
    <section className="bg-card border border-border rounded-2xl p-6 md:p-8 shadow-sm space-y-6">
      {/* 1. Header & Metric Mode Toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border/50 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Compass className="w-5 h-5 text-accent" />
            <h3 className="text-lg font-bold tracking-tight text-foreground">
              Historical Exam Focus Evolution: Syllabus & Topics
            </h3>
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-accent/10 text-accent border border-accent/20">
              Descriptive Archive
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            Empirical historical distribution of syllabus units and topics across verified exam sessions. Descriptive archive — not a trend prediction.
          </p>
        </div>

        {/* View / Metric Mode Selector */}
        <div className="inline-flex p-1 bg-muted/40 border border-border/60 rounded-xl self-start sm:self-auto shrink-0">
          <button
            type="button"
            onClick={() => setMetricMode("questions")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              metricMode === "questions"
                ? "bg-background text-foreground shadow-xs border border-border/80 font-semibold"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Historical Question Share (%)
          </button>
          <button
            type="button"
            onClick={() => setMetricMode("marks")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              metricMode === "marks"
                ? "bg-background text-foreground shadow-xs border border-border/80 font-semibold"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Historical Marks Weight (%)
          </button>
        </div>
      </div>

      {/* 2. Unit Selector */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-muted-foreground" />
          <span className="text-xs font-semibold text-foreground uppercase tracking-wider">
            Filter Syllabus Scope:
          </span>
        </div>
        <div className="flex items-center gap-2 overflow-x-auto pb-1 max-w-full">
          <button
            type="button"
            onClick={() => setSelectedUnit("ALL")}
            className={`px-3 py-1.5 text-xs rounded-lg transition-all shrink-0 font-medium ${
              selectedUnit === "ALL"
                ? "bg-accent text-accent-foreground font-semibold shadow-xs"
                : "bg-muted/30 border border-border/60 text-muted-foreground hover:text-foreground hover:bg-muted/50"
            }`}
          >
            All Units (Curriculum Overview)
          </button>

          {availableUnits.map((u) => {
            const isSelected = u === selectedUnit;
            const isUnmapped = u.toLowerCase().includes("unmapped");
            return (
              <button
                key={u}
                type="button"
                onClick={() => setSelectedUnit(u)}
                className={`px-3 py-1.5 text-xs rounded-lg transition-all shrink-0 font-medium ${
                  isSelected
                    ? "bg-accent text-accent-foreground font-semibold shadow-xs"
                    : isUnmapped
                    ? "bg-zinc-800/40 border border-zinc-700/60 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60"
                    : "bg-muted/30 border border-border/60 text-muted-foreground hover:text-foreground hover:bg-muted/50"
                }`}
              >
                {u}
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. Status & Data Quality Notices */}
      {activeHasSparse && (
        <div className="flex items-start gap-2.5 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-200/90">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-amber-300">Sparse Historical Observations:</span>{" "}
            One or more recorded exam years in this view contain fewer than 3 verified papers or fewer than 5 recorded questions.
            Observed proportions strictly reflect the specific archived examinations in those sessions without interpolation.
          </div>
        </div>
      )}

      {unmappedUnitPresent && (isAllUnits || isViewingUnmapped) && (
        <div className="flex items-start gap-2.5 p-3 rounded-xl bg-muted/40 border border-border/60 text-xs text-muted-foreground">
          <FileQuestion className="w-4 h-4 text-muted-foreground shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-foreground">Unmapped Past Questions Retained:</span>{" "}
            A subset of historical questions in the corpus is not currently mapped to an explicit syllabus unit or topic.
            They are preserved as &quot;Unmapped / Unknown&quot; so that reported percentages mathematically represent 100% of the historical corpus without artificial inflation.
          </div>
        </div>
      )}

      {metricMode === "marks" && activeHasUnscored && (
        <div className="flex items-start gap-2.5 p-3 rounded-xl bg-muted/40 border border-border/60 text-xs text-muted-foreground">
          <Info className="w-4 h-4 text-muted-foreground shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-foreground">Unassigned Mark Allocations:</span>{" "}
            Certain archived papers lack explicit per-question mark weights. Scored marks weights are calculated strictly from questions with verified numeric mark allocations.
          </div>
        </div>
      )}

      {/* 4. Chart Visualization Area */}
      {activeChartData.length > 0 ? (
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-muted/10 border border-border/50">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-xs text-muted-foreground mb-3">
              <span>
                {isAllUnits
                  ? `Historical Unit representation (${metricMode === "questions" ? "question share %" : "marks weight %"}) by exam year`
                  : `Historical Topic representation in "${selectedUnit}" (${metricMode === "questions" ? "question share %" : "marks weight %"}) by exam year`}
              </span>
              <span className="text-[11px] font-mono shrink-0">
                {activeChartData.length} {activeChartData.length === 1 ? "exam year" : "exam years"} observed (missing years shown as discrete gaps)
              </span>
            </div>

            <HistoricalFocusChart
              data={activeChartData}
              seriesKeys={activeSeriesKeys}
              metricMode={metricMode}
              categoryName={isAllUnits ? "Unit" : "Topic"}
            />
          </div>

          {/* 5. Topic Persistence Footprint Summary (Only shown when a specific Unit is selected) */}
          {!isAllUnits && unitTopicData && unitTopicData.footprints.length > 0 && (
            <div className="space-y-3 pt-2">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-accent" />
                <h4 className="text-xs font-semibold text-foreground uppercase tracking-wider">
                  Historical Topic Persistence Summary ({selectedUnit})
                </h4>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {unitTopicData.footprints.map((footprint) => {
                  const yearsCount = footprint.years_observed.length;
                  const totalYears = allRecordedYears.length;
                  const isPersistent = totalYears > 1 && yearsCount === totalYears;
                  const isSingle = yearsCount === 1;

                  return (
                    <div
                      key={footprint.topic_id || footprint.topic_name}
                      className="p-3.5 rounded-xl bg-muted/20 border border-border/50 space-y-2 hover:border-border transition-colors"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <span className="font-semibold text-xs text-foreground leading-tight" title={footprint.topic_name}>
                          {footprint.topic_name}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold shrink-0 border ${
                            isPersistent
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                              : isSingle
                              ? "bg-amber-500/10 text-amber-300 border-amber-500/20"
                              : "bg-sky-500/10 text-sky-300 border-sky-500/20"
                          }`}
                        >
                          {isPersistent
                            ? "Persistent across archive"
                            : isSingle
                            ? "Single-session observation"
                            : "Intermittent observation"}
                        </span>
                      </div>

                      <div className="text-[11px] text-muted-foreground space-y-1">
                        <div className="flex items-center justify-between">
                          <span>Observed in archive:</span>
                          <span className="font-mono text-zinc-200">
                            {yearsCount} of {totalYears} {totalYears === 1 ? "year" : "years"}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span>Paper coverage:</span>
                          <span className="font-mono text-zinc-200">
                            {Math.round(footprint.paper_coverage_percentage)}% of verified exams
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span>Total recorded volume:</span>
                          <span className="font-mono text-zinc-200">
                            {footprint.total_questions} Qs • {Math.round(footprint.total_marks)}m
                          </span>
                        </div>
                      </div>

                      <div className="pt-1 flex flex-wrap gap-1">
                        {footprint.years_observed.map((y) => (
                          <span
                            key={y}
                            className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-muted/50 text-muted-foreground border border-border/40"
                          >
                            {y}
                          </span>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 6. Detailed Tabular Historical Breakdown */}
          <div className="space-y-3 pt-2">
            <h4 className="text-xs font-semibold text-foreground uppercase tracking-wider">
              {isAllUnits
                ? "Annual Syllabus Unit Focus Observations"
                : `Annual Topic Focus Observations for ${selectedUnit}`}
            </h4>

            {isAllUnits ? (
              // All Units Table
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="border-b border-border text-muted-foreground">
                      <th className="pb-2 font-semibold">Exam Year</th>
                      <th className="pb-2 font-semibold">Historical Scope</th>
                      <th className="pb-2 font-semibold">
                        Syllabus Unit Composition ({metricMode === "questions" ? "Question Share %" : "Marks Share %"})
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/40">
                    {allUnitsChartData.map((row) => (
                      <tr key={row.year} className="hover:bg-muted/30 transition-colors">
                        <td className="py-2.5 font-bold text-foreground align-top">
                          <div className="flex items-center gap-1.5">
                            <span>Exam Year {row.year}</span>
                            {row.isSparse && (
                              <span className="px-1.5 py-0.5 rounded text-[10px] bg-amber-500/15 text-amber-300 border border-amber-500/25">
                                Sparse
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="py-2.5 text-muted-foreground align-top">
                          <div>{row.totalQuestions} Questions</div>
                          {row.totalMarks > 0 && <div className="text-[11px]">{row.totalMarks} Marks</div>}
                          {row.examCount !== undefined && row.examCount > 0 && (
                            <div className="text-[10px] text-muted-foreground/75">
                              {row.examCount} {row.examCount === 1 ? "paper" : "papers"}
                            </div>
                          )}
                        </td>
                        <td className="py-2.5 align-top">
                          <div className="flex flex-wrap gap-1.5">
                            {availableUnits.map((u) => {
                              const pct = row[u];
                              const count = row[`${u}_count`];
                              const marks = row[`${u}_marks`];
                              if (pct === undefined || pct === null || pct === 0) return null;
                              const isUnmapped = u.toLowerCase().includes("unmapped");

                              return (
                                <span
                                  key={u}
                                  className={`inline-flex items-center gap-1 px-2 py-1 rounded border text-[11px] ${
                                    isUnmapped
                                      ? "bg-zinc-800/40 border-zinc-700/60 text-zinc-300"
                                      : "bg-muted/40 border-border/60 text-foreground"
                                  }`}
                                >
                                  <span className="font-medium truncate max-w-[130px]" title={u}>
                                    {u}:
                                  </span>
                                  <span className="font-bold text-accent">{pct}%</span>
                                  <span className="text-[10px] text-muted-foreground font-mono">
                                    ({metricMode === "questions" ? `${count} Qs` : `${marks}m`})
                                  </span>
                                </span>
                              );
                            })}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              // Unit Specific Topics Table
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="border-b border-border text-muted-foreground">
                      <th className="pb-2 font-semibold">Exam Year</th>
                      <th className="pb-2 font-semibold">Topic</th>
                      <th className="pb-2 font-semibold text-right">Question Count</th>
                      <th className="pb-2 font-semibold text-right">Question Share</th>
                      <th className="pb-2 font-semibold text-right">Scored Marks</th>
                      <th className="pb-2 font-semibold text-right">Marks Weight</th>
                      <th className="pb-2 font-semibold">Observed Question Types</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/40">
                    {(unitTopicData?.topicRows || []).map((row, idx) => (
                      <tr key={`${row.year}-${row.topic}-${idx}`} className="hover:bg-muted/30 transition-colors">
                        <td className="py-2 font-bold text-foreground align-top">
                          <div className="flex items-center gap-1.5">
                            <span>{row.year}</span>
                            {row.is_sparse && (
                              <span className="px-1.5 py-0.5 rounded text-[9px] bg-amber-500/15 text-amber-300 border border-amber-500/25">
                                Sparse
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="py-2 text-foreground font-medium align-top">
                          <div className="max-w-[200px] truncate" title={row.topic}>
                            {row.topic}
                          </div>
                        </td>
                        <td className="py-2 text-right font-mono text-zinc-300 align-top">
                          {row.question_count}
                        </td>
                        <td className="py-2 text-right font-mono font-semibold text-accent align-top">
                          {row.question_percentage}%
                        </td>
                        <td className="py-2 text-right font-mono text-zinc-300 align-top">
                          {row.scored_marks}m
                        </td>
                        <td className="py-2 text-right font-mono font-semibold text-accent align-top">
                          {row.marks_weight_percentage}%
                        </td>
                        <td className="py-2 align-top">
                          <div className="flex flex-wrap gap-1">
                            {Object.entries(row.question_types || {}).map(([qt, count]) => (
                              <span
                                key={qt}
                                className="px-1.5 py-0.5 rounded text-[10px] bg-muted/40 text-muted-foreground border border-border/50 font-mono"
                              >
                                {qt}: {count}
                              </span>
                            ))}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="py-12 text-center text-xs text-muted-foreground">
          No historical focus records found for the selected scope.
        </div>
      )}

      {/* 7. Non-Predictive Archive Notice */}
      <div className="p-3 rounded-xl bg-muted/20 border border-border/40 text-[11px] text-muted-foreground space-y-1">
        <div>
          <strong>Non-Predictive Archive Notice:</strong> This breakdown reflects observed syllabus unit and topic frequencies from archived past examination papers.
          Historical representation does not forecast or predict question appearances for future examinations, indicate &quot;safe bets&quot;, or imply curriculum addition or removal.
        </div>
        <div>
          Historical years are evaluated discretely without interpolating across missing calendar years.
        </div>
      </div>
    </section>
  );
}
