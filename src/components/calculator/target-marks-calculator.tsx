"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import { 
  Target, 
  Sparkles, 
  BookOpen, 
  CheckCircle2, 
  AlertCircle, 
  HelpCircle, 
  TrendingUp, 
  Award,
  ArrowRight,
  Info
} from "lucide-react";
import { coursesCatalog, CourseCatalogItem } from "@/lib/courses";

// SRMIST Regulation Grade Scales (2021 & 2026 regulations)
export interface GradeThreshold {
  grade: string;
  label: string;
  minTotal: number;
  gradePoints: number;
  color: string;
  badgeBg: string;
}

export const SRM_GRADE_THRESHOLDS: GradeThreshold[] = [
  { grade: "O", label: "Outstanding", minTotal: 91, gradePoints: 10, color: "text-amber-500", badgeBg: "bg-amber-500/10 border-amber-500/25 text-amber-500" },
  { grade: "A+", label: "Excellent", minTotal: 81, gradePoints: 9, color: "text-emerald-500", badgeBg: "bg-emerald-500/10 border-emerald-500/25 text-emerald-500" },
  { grade: "A", label: "Very Good", minTotal: 71, gradePoints: 8, color: "text-sky-500", badgeBg: "bg-sky-500/10 border-sky-500/25 text-sky-500" },
  { grade: "B+", label: "Good", minTotal: 61, gradePoints: 7, color: "text-blue-500", badgeBg: "bg-blue-500/10 border-blue-500/25 text-blue-500" },
  { grade: "B", label: "Above Average", minTotal: 56, gradePoints: 6, color: "text-violet-500", badgeBg: "bg-violet-500/10 border-violet-500/25 text-violet-500" },
  { grade: "C", label: "Pass (Minimum)", minTotal: 50, gradePoints: 5, color: "text-muted-foreground", badgeBg: "bg-muted/30 border-border text-foreground" },
];

export function TargetMarksCalculator() {
  const [regulation, setRegulation] = useState<"2021" | "2026">("2021");
  const [selectedCourseSlug, setSelectedCourseSlug] = useState<string>("calculus-and-linear-algebra");
  const [inputMode, setInputMode] = useState<"aggregate" | "itemized">("itemized");

  // Itemized internal marks (SRM 50-mark internal structure)
  const [cla1, setCla1] = useState<number>(12); // out of 15
  const [cla2, setCla2] = useState<number>(13); // out of 15
  const [cla3, setCla3] = useState<number>(8);  // out of 10
  const [continuous, setContinuous] = useState<number>(9); // out of 10 (assignments, quiz, attendance)

  // Aggregate internal marks (out of 50)
  const [aggregateInternal, setAggregateInternal] = useState<number>(42);

  // Selected target grade
  const [selectedGrade, setSelectedGrade] = useState<string>("O");

  const activeCourse = useMemo(() => {
    return coursesCatalog.find((c) => c.slug === selectedCourseSlug || c.code === selectedCourseSlug) || coursesCatalog[0];
  }, [selectedCourseSlug]);

  // Compute total internal marks out of 50
  const totalInternal = useMemo(() => {
    if (inputMode === "aggregate") {
      return Math.min(50, Math.max(0, aggregateInternal || 0));
    }
    const c1 = Math.min(15, Math.max(0, cla1 || 0));
    const c2 = Math.min(15, Math.max(0, cla2 || 0));
    const c3 = Math.min(10, Math.max(0, cla3 || 0));
    const cont = Math.min(10, Math.max(0, continuous || 0));
    return Math.min(50, c1 + c2 + c3 + cont);
  }, [inputMode, aggregateInternal, cla1, cla2, cla3, continuous]);

  // Formula: Total = Internals (50) + (EndSem (100) / 2)
  // EndSem required = (TargetTotal - Internals) * 2
  const gradePredictions = useMemo(() => {
    return SRM_GRADE_THRESHOLDS.map((tier) => {
      const neededTotal = tier.minTotal;
      const rawNeededEndSem = (neededTotal - totalInternal) * 2;
      const minRequired = Math.ceil(Math.max(0, rawNeededEndSem));
      
      // SRM Minimum EndSem Passing Criterion: minimum 45/100 or 50/100 in End Sem paper
      const passingEndSemMinimum = regulation === "2026" ? 50 : 45;
      const effectiveRequired = Math.max(minRequired, passingEndSemMinimum);

      let status: "achievable" | "guaranteed" | "impossible";
      let message = "";

      if (rawNeededEndSem <= 0) {
        status = "guaranteed";
        message = `Internal marks alone (${totalInternal}/50) cover the threshold. Just score minimum passing marks (${passingEndSemMinimum}/100) in End Sem.`;
      } else if (rawNeededEndSem > 100) {
        status = "impossible";
        const maxScorePossible = totalInternal + 50; // if 100 in EndSem
        message = `Mathematically unachievable from current internals. Maximum attainable total is ${maxScorePossible.toFixed(1)}/100.`;
      } else {
        status = "achievable";
        message = `Need ${effectiveRequired}/100 in End-Semester Examination to secure ${tier.grade} Grade.`;
      }

      return {
        ...tier,
        rawNeededEndSem,
        effectiveRequired: Math.min(100, effectiveRequired),
        status,
        message,
      };
    });
  }, [totalInternal, regulation]);

  const activeTargetTier = useMemo(() => {
    return gradePredictions.find((g) => g.grade === selectedGrade) || gradePredictions[0];
  }, [gradePredictions, selectedGrade]);

  return (
    <div className="w-full max-w-4xl mx-auto space-y-8">
      {/* Top Header Card */}
      <div className="p-6 md:p-8 rounded-3xl bg-card border border-border shadow-xs space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-border/60">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="p-2 rounded-xl bg-accent/15 text-accent">
                <Target className="w-5 h-5" />
              </span>
              <h2 className="text-xl md:text-2xl font-bold tracking-tight text-foreground">
                SRM End-Semester Target Marks Predictor
              </h2>
            </div>
            <p className="text-xs text-muted-foreground">
              Calculates the exact marks needed in your 100-mark End-Semester Examination based on official SRMIST evaluation formulas.
            </p>
          </div>

          {/* Regulation Switcher */}
          <div className="flex items-center gap-2 p-1 bg-muted/20 border border-border/80 rounded-xl text-xs font-semibold self-start md:self-auto shrink-0">
            <span className="text-[11px] text-muted-foreground px-2">Regulation:</span>
            <button
              type="button"
              onClick={() => setRegulation("2021")}
              className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                regulation === "2021"
                  ? "bg-accent text-accent-foreground font-bold shadow-2xs"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              2021 Reg (45% Min)
            </button>
            <button
              type="button"
              onClick={() => setRegulation("2026")}
              className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                regulation === "2026"
                  ? "bg-accent text-accent-foreground font-bold shadow-2xs"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              2026 Reg (50% Min)
            </button>
          </div>
        </div>

        {/* Course Selector & Mode Toggle */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground">Select Subject / Course</label>
            <select
              value={selectedCourseSlug}
              onChange={(e) => setSelectedCourseSlug(e.target.value)}
              className="w-full bg-background border border-border rounded-xl px-3.5 py-2.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-accent transition-all cursor-pointer"
            >
              {coursesCatalog.map((course) => (
                <option key={course.id} value={course.slug}>
                  {course.code} • {course.name} ({course.credits} Credits)
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground">Internal Assessment Breakdown</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setInputMode("itemized")}
                className={`py-2 px-3 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
                  inputMode === "itemized"
                    ? "bg-foreground text-background border-foreground font-bold"
                    : "bg-background border-border text-muted-foreground hover:text-foreground"
                }`}
              >
                Itemized (CLA1 + CLA2 + CLA3)
              </button>
              <button
                type="button"
                onClick={() => setInputMode("aggregate")}
                className={`py-2 px-3 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
                  inputMode === "aggregate"
                    ? "bg-foreground text-background border-foreground font-bold"
                    : "bg-background border-border text-muted-foreground hover:text-foreground"
                }`}
              >
                Total Internals (/50)
              </button>
            </div>
          </div>
        </div>

        {/* Internal Marks Inputs */}
        {inputMode === "itemized" ? (
          <div className="p-4 sm:p-5 rounded-2xl bg-muted/15 border border-border/80 space-y-3">
            <div className="flex items-center justify-between text-xs font-semibold text-muted-foreground">
              <span>Continuous Assessment Components</span>
              <span className="font-mono text-foreground">
                Sum: <strong className="text-accent text-sm">{totalInternal.toFixed(1)}</strong> / 50 Marks
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="space-y-1">
                <label className="text-[11px] font-medium text-muted-foreground">CLA 1 (Cycle Test 1)</label>
                <div className="relative">
                  <input
                    type="number"
                    min="0"
                    max="15"
                    step="0.5"
                    value={cla1}
                    onChange={(e) => setCla1(parseFloat(e.target.value) || 0)}
                    className="w-full bg-background border border-border rounded-xl px-3 py-2 text-sm font-mono font-bold focus:outline-none focus:ring-2 focus:ring-accent"
                  />
                  <span className="absolute right-3 top-2 text-xs text-muted-foreground">/15</span>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-medium text-muted-foreground">CLA 2 (Cycle Test 2)</label>
                <div className="relative">
                  <input
                    type="number"
                    min="0"
                    max="15"
                    step="0.5"
                    value={cla2}
                    onChange={(e) => setCla2(parseFloat(e.target.value) || 0)}
                    className="w-full bg-background border border-border rounded-xl px-3 py-2 text-sm font-mono font-bold focus:outline-none focus:ring-2 focus:ring-accent"
                  />
                  <span className="absolute right-3 top-2 text-xs text-muted-foreground">/15</span>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-medium text-muted-foreground">CLA 3 (Quiz/Project)</label>
                <div className="relative">
                  <input
                    type="number"
                    min="0"
                    max="10"
                    step="0.5"
                    value={cla3}
                    onChange={(e) => setCla3(parseFloat(e.target.value) || 0)}
                    className="w-full bg-background border border-border rounded-xl px-3 py-2 text-sm font-mono font-bold focus:outline-none focus:ring-2 focus:ring-accent"
                  />
                  <span className="absolute right-3 top-2 text-xs text-muted-foreground">/10</span>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-medium text-muted-foreground">Assignments / Cont.</label>
                <div className="relative">
                  <input
                    type="number"
                    min="0"
                    max="10"
                    step="0.5"
                    value={continuous}
                    onChange={(e) => setContinuous(parseFloat(e.target.value) || 0)}
                    className="w-full bg-background border border-border rounded-xl px-3 py-2 text-sm font-mono font-bold focus:outline-none focus:ring-2 focus:ring-accent"
                  />
                  <span className="absolute right-3 top-2 text-xs text-muted-foreground">/10</span>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-4 sm:p-5 rounded-2xl bg-muted/15 border border-border/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-foreground">Aggregate Internal Marks Earned</label>
              <p className="text-xs text-muted-foreground">Total continuous assessment marks out of 50</p>
            </div>
            <div className="relative w-full sm:w-48">
              <input
                type="number"
                min="0"
                max="50"
                step="0.5"
                value={aggregateInternal}
                onChange={(e) => setAggregateInternal(parseFloat(e.target.value) || 0)}
                className="w-full bg-background border border-border rounded-xl px-4 py-2.5 text-base font-mono font-bold focus:outline-none focus:ring-2 focus:ring-accent"
              />
              <span className="absolute right-4 top-2.5 text-sm font-medium text-muted-foreground">/ 50</span>
            </div>
          </div>
        )}
      </div>

      {/* Target Grade Selector Chips */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold uppercase tracking-wider text-muted-foreground">
            Select Your Target Grade
          </h3>
          <span className="text-xs text-muted-foreground font-mono">
            Evaluation: Total = Internals + (EndSem / 2)
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2.5">
          {gradePredictions.map((tier) => {
            const isSelected = selectedGrade === tier.grade;
            return (
              <button
                key={tier.grade}
                type="button"
                onClick={() => setSelectedGrade(tier.grade)}
                className={`p-3.5 rounded-2xl border text-center transition-all cursor-pointer flex flex-col items-center justify-between gap-2 ${
                  isSelected
                    ? "bg-accent/15 border-accent shadow-xs ring-2 ring-accent/30"
                    : "bg-card border-border hover:border-border/80 hover:bg-muted/10"
                }`}
              >
                <div className="flex items-center gap-1.5">
                  <span className={`text-xl font-extrabold font-mono ${tier.color}`}>
                    {tier.grade}
                  </span>
                  <span className="text-[10px] text-muted-foreground font-mono">({tier.gradePoints} GP)</span>
                </div>
                <span className="text-[11px] font-semibold text-foreground truncate w-full">
                  {tier.label}
                </span>
                <span className="text-[10px] font-mono text-muted-foreground">
                  &ge; {tier.minTotal} marks
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Target Result Hero Banner */}
      <div className="p-6 md:p-8 rounded-3xl bg-card border border-border/80 shadow-sm relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-lg">
            <div className="flex items-center gap-2">
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${activeTargetTier.badgeBg}`}>
                Target: {activeTargetTier.grade} Grade ({activeTargetTier.label})
              </span>
              {activeTargetTier.status === "achievable" && (
                <span className="text-xs font-semibold text-emerald-500 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Achievable
                </span>
              )}
              {activeTargetTier.status === "impossible" && (
                <span className="text-xs font-semibold text-red-500 flex items-center gap-1">
                  <AlertCircle className="w-3.5 h-3.5" /> Out of Range
                </span>
              )}
            </div>

            <h3 className="text-2xl sm:text-3xl font-extrabold text-foreground tracking-tight">
              {activeTargetTier.status === "achievable" ? (
                <>
                  Score at least{" "}
                  <span className="text-accent font-mono underline decoration-accent/30 decoration-4">
                    {activeTargetTier.effectiveRequired} / 100
                  </span>{" "}
                  in End Sem
                </>
              ) : activeTargetTier.status === "guaranteed" ? (
                <>
                  <span className="text-emerald-500 font-mono">Guaranteed</span> with Passing Score
                </>
              ) : (
                <>Requires &gt; 100 marks in End Sem</>
              )}
            </h3>

            <p className="text-xs text-muted-foreground leading-relaxed">
              {activeTargetTier.message}
            </p>
          </div>

          {/* Quick Action to MintAI Predictions for This Subject */}
          <div className="flex flex-col sm:flex-row md:flex-col gap-2 shrink-0">
            <Link
              href={`/srm/${activeCourse.slug}?tab=overview`}
              className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-2xl bg-foreground text-background font-semibold text-xs hover:bg-foreground/90 transition-all shadow-xs cursor-pointer"
            >
              <Sparkles className="w-4 h-4 text-accent" />
              <span>Study Top Predictions for {activeCourse.code}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>

            <Link
              href={`/srm/${activeCourse.slug}?tab=practice`}
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-2xl bg-muted/30 text-foreground border border-border/80 font-semibold text-xs hover:bg-muted/50 transition-all cursor-pointer"
            >
              <BookOpen className="w-3.5 h-3.5 text-muted-foreground" />
              <span>Solve Past PYQs &amp; CT Papers</span>
            </Link>
          </div>
        </div>

        {/* Grade Breakdown Table */}
        <div className="mt-8 pt-6 border-t border-border/60">
          <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3">
            Full Grade Conversion Matrix for {activeCourse.name}
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
            {gradePredictions.map((tier) => (
              <div
                key={tier.grade}
                className="p-3 rounded-xl bg-muted/15 border border-border/60 flex items-center justify-between text-xs"
              >
                <div className="flex items-center gap-2">
                  <span className={`font-mono font-bold text-sm ${tier.color}`}>{tier.grade}</span>
                  <span className="text-muted-foreground text-[11px] font-medium">{tier.label}</span>
                </div>
                <div className="text-right font-mono">
                  {tier.status === "impossible" ? (
                    <span className="text-[11px] text-red-500 font-semibold">Unattainable</span>
                  ) : tier.status === "guaranteed" ? (
                    <span className="text-[11px] text-emerald-500 font-semibold">&ge; {regulation === "2026" ? 50 : 45} (Pass)</span>
                  ) : (
                    <span className="font-bold text-foreground">{tier.effectiveRequired} / 100</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
