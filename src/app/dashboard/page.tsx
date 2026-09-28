"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { coursesCatalog, CourseCatalogItem } from "@/lib/courses";
import { getStudyContext, updateStudyContext, StudyContext } from "@/lib/study-context";
import { useStreak } from "@/hooks/use-streak";
import {
  Sparkles,
  Dna,
  Target,
  ArrowRight,
  BookOpen,
  Calendar,
  CheckCircle2,
  Clock,
  Layers,
  ShieldCheck,
  Flame,
  ChevronRight,
  FileText,
  HelpCircle,
  TrendingUp,
  BrainCircuit,
  RotateCcw
} from "lucide-react";

export default function DashboardPage() {
  const streak = useStreak();
  const [studyContext, setStudyContext] = useState<StudyContext | null>(null);
  const [isClient, setIsClient] = useState(false);

  // Eligible courses with PYQ papers in archive
  const eligibleCourses = useMemo(() => {
    return coursesCatalog.filter((c) => c.paperCount > 0);
  }, []);

  // Initialize active course from study context or fallback to primary course
  const [selectedCourseId, setSelectedCourseId] = useState<number>(() => {
    return eligibleCourses[0]?.id || 1;
  });

  const [selectedCycle, setSelectedCycle] = useState<string>("ENDSEM");

  useEffect(() => {
    setIsClient(true);
    const ctx = getStudyContext();
    if (ctx) {
      setStudyContext(ctx);
      if (ctx.course_id && eligibleCourses.some((c) => c.id === ctx.course_id)) {
        setSelectedCourseId(ctx.course_id);
      }
      if (ctx.assessment_cycle) {
        setSelectedCycle(ctx.assessment_cycle);
      }
    }

    const handleUpdate = () => {
      const updated = getStudyContext();
      setStudyContext(updated);
      if (updated?.course_id && eligibleCourses.some((c) => c.id === updated.course_id)) {
        setSelectedCourseId(updated.course_id);
      }
      if (updated?.assessment_cycle) {
        setSelectedCycle(updated.assessment_cycle);
      }
    };

    window.addEventListener("markmint:study_context_updated", handleUpdate);
    window.addEventListener("markmint:study_context_cleared", handleUpdate);
    return () => {
      window.removeEventListener("markmint:study_context_updated", handleUpdate);
      window.removeEventListener("markmint:study_context_cleared", handleUpdate);
    };
  }, [eligibleCourses]);

  const currentCourse: CourseCatalogItem = useMemo(() => {
    return eligibleCourses.find((c) => c.id === selectedCourseId) || eligibleCourses[0];
  }, [eligibleCourses, selectedCourseId]);

  const handleCourseChange = (courseId: number) => {
    setSelectedCourseId(courseId);
    const target = eligibleCourses.find((c) => c.id === courseId);
    if (target) {
      updateStudyContext({
        course_id: target.id,
        course_name: target.name,
        course_code: target.code,
        assessment_cycle: selectedCycle,
      });
    }
  };

  const handleCycleChange = (cycle: string) => {
    setSelectedCycle(cycle);
    if (currentCourse) {
      updateStudyContext({
        course_id: currentCourse.id,
        course_name: currentCourse.name,
        course_code: currentCourse.code,
        assessment_cycle: cycle,
      });
    }
  };

  // Study progress metrics from context
  const completedTaskCount = useMemo(() => {
    if (!studyContext?.task_statuses) return 0;
    return Object.values(studyContext.task_statuses).filter((s) => s === "COMPLETED").length;
  }, [studyContext]);

  const cycleDisplayLabel = useMemo(() => {
    switch (selectedCycle) {
      case "ENDSEM":
        return "End Semester";
      case "CT1":
        return "Class Test 1";
      case "CT2":
        return "Class Test 2";
      default:
        return "All Assessment Cycles";
    }
  }, [selectedCycle]);

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground font-sans">
      <Navbar />

      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 md:px-10 py-8 space-y-8">
        {/* Breadcrumb Navigation */}
        <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-xs text-muted-foreground">
          <Link href="/" className="hover:text-foreground transition-colors">
            Home
          </Link>
          <ChevronRight className="w-3.5 h-3.5" />
          <span className="text-foreground font-medium">Dashboard</span>
        </nav>

        {/* 1. MintAI Command Header & Context Switcher */}
        <div className="bg-card border border-border rounded-2xl p-6 md:p-8 shadow-sm space-y-6">
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 pb-6 border-b border-border/50">
            <div className="space-y-2 max-w-2xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent/10 border border-accent/20 text-xs font-semibold text-accent uppercase tracking-wider">
                <BrainCircuit className="w-3.5 h-3.5" />
                MintAI Workspace Command Center
              </div>
              <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-foreground">
                Study Dashboard
              </h1>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Your personal hub for university exam intelligence. Monitor active course evidence, inspect predictive forecasts, review historical exam footprints, and execute targeted study plans.
              </p>
            </div>

            {/* Streak & Active Status */}
            <div className="flex items-center gap-3 self-start md:self-auto">
              <div className="px-4 py-2.5 rounded-xl bg-muted/30 border border-border text-right shadow-xs space-y-0.5">
                <div className="text-[11px] text-muted-foreground flex items-center justify-end gap-1.5 font-medium">
                  <Flame className="w-3.5 h-3.5 text-orange-500" />
                  Study Streak
                </div>
                <div className="text-lg font-bold text-foreground">
                  {streak} {streak === 1 ? "Day" : "Days"} Active
                </div>
              </div>
            </div>
          </div>

          {/* Active Study Scope Selector Bar */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pt-1">
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-accent shrink-0" />
                <label htmlFor="dashboard-course-select" className="text-xs font-semibold text-foreground whitespace-nowrap">
                  Current Course:
                </label>
                <select
                  id="dashboard-course-select"
                  value={selectedCourseId}
                  onChange={(e) => handleCourseChange(Number(e.target.value))}
                  className="bg-background border border-border rounded-lg px-3 py-1.5 text-xs font-semibold text-foreground focus:ring-2 focus:ring-accent focus:outline-none min-w-[260px] shadow-xs"
                >
                  {eligibleCourses.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.canonicalCode ? `[${c.canonicalCode}] ` : ""}{c.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Assessment Cycle Target Pill Selector */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground whitespace-nowrap font-medium">Target:</span>
                <div className="inline-flex rounded-lg border border-border p-0.5 bg-muted/20 text-xs">
                  {(["ENDSEM", "CT1", "CT2", "ALL"] as const).map((cycle) => (
                    <button
                      key={cycle}
                      onClick={() => handleCycleChange(cycle)}
                      className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all cursor-pointer ${
                        selectedCycle === cycle
                          ? "bg-accent text-accent-foreground font-semibold shadow-xs"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {cycle === "ENDSEM" ? "End Sem" : cycle}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Current Course Quick Summary */}
            <div className="text-xs text-muted-foreground flex items-center gap-3">
              <span>{currentCourse.paperCount} Archived Exams</span>
              <span>&bull;</span>
              <span>{currentCourse.questionCount} Questions</span>
              <span>&bull;</span>
              <span>{currentCourse.units.length} Syllabus Units</span>
            </div>
          </div>
        </div>

        {/* 2. Core Capabilities: The 3 Clear Jobs Inside MintAI */}
        <div className="space-y-4">
          <div className="space-y-1">
            <h2 className="text-lg font-bold tracking-tight text-foreground flex items-center gap-2">
              <Layers className="w-4 h-4 text-accent" />
              Core MintAI Capabilities
            </h2>
            <p className="text-xs text-muted-foreground">
              Select an action based on what you need to accomplish right now
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Capability 1: Predictive Forecast */}
            <div className="bg-card border border-border rounded-2xl p-6 shadow-sm flex flex-col justify-between space-y-6 hover:border-accent/40 transition-all group">
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-xl bg-accent/10 border border-accent/20 flex items-center justify-center text-accent">
                  <Sparkles className="w-5 h-5 group-hover:rotate-12 transition-transform" />
                </div>
                <div className="space-y-1">
                  <div className="text-[11px] font-semibold text-accent uppercase tracking-wider">
                    Core Intelligence
                  </div>
                  <h3 className="text-lg font-bold text-foreground">
                    Predictive Exam Forecast
                  </h3>
                  <p className="text-xs text-muted-foreground leading-relaxed pt-1">
                    <em>&ldquo;What does historical evidence suggest I should focus on for my exam?&rdquo;</em>
                  </p>
                </div>

                <div className="pt-2 border-t border-border/50 space-y-2 text-xs text-muted-foreground">
                  <div className="flex items-center justify-between">
                    <span>Ranked High-Yield Topics:</span>
                    <span className="font-semibold text-foreground">{currentCourse.highYieldTopics.length} Identified</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Target Exam Cycle:</span>
                    <span className="font-semibold text-accent">{cycleDisplayLabel}</span>
                  </div>
                  {currentCourse.highYieldTopics[0] && (
                    <div className="p-2.5 rounded-lg bg-muted/30 border border-border/50 text-[11px] space-y-0.5">
                      <span className="text-muted-foreground block text-[10px] uppercase font-bold tracking-wider">Top Historical Yield</span>
                      <span className="font-semibold text-foreground line-clamp-1">{currentCourse.highYieldTopics[0].topic}</span>
                    </div>
                  )}
                </div>
              </div>

              <Link
                href={`/mintai?course_id=${currentCourse.id}&cycle=${selectedCycle}`}
                className="w-full py-2.5 px-4 bg-foreground text-background text-xs font-semibold rounded-xl hover:bg-foreground/90 transition-all flex items-center justify-center gap-2 shadow-xs group-hover:shadow-sm"
              >
                <span>Open Intelligence Forecast</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </div>

            {/* Capability 2: Historical Analysis & Exam DNA */}
            <div className="bg-card border border-border rounded-2xl p-6 shadow-sm flex flex-col justify-between space-y-6 hover:border-accent/40 transition-all group">
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-xl bg-accent/10 border border-accent/20 flex items-center justify-center text-accent">
                  <Dna className="w-5 h-5 group-hover:scale-110 transition-transform" />
                </div>
                <div className="space-y-1">
                  <div className="text-[11px] font-semibold text-accent uppercase tracking-wider">
                    Historical Analytics
                  </div>
                  <h3 className="text-lg font-bold text-foreground">
                    Exam DNA Analysis
                  </h3>
                  <p className="text-xs text-muted-foreground leading-relaxed pt-1">
                    <em>&ldquo;What has actually happened across past exams?&rdquo;</em>
                  </p>
                </div>

                <div className="pt-2 border-t border-border/50 space-y-2 text-xs text-muted-foreground">
                  <div className="flex items-center justify-between">
                    <span>Verified Exam Papers:</span>
                    <span className="font-semibold text-foreground">{currentCourse.paperCount} Papers</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Analyzed Questions:</span>
                    <span className="font-semibold text-foreground">{currentCourse.questionCount} Questions</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-muted/30 border border-border/50 text-[11px] space-y-1">
                    <span className="text-muted-foreground block text-[10px] uppercase font-bold tracking-wider">Historical Signals</span>
                    <span className="text-foreground block font-medium">Assessment Blueprints &bull; Cognitive Demand &bull; Unit Weights &bull; Mark Tiers</span>
                  </div>
                </div>
              </div>

              <Link
                href={`/mintai/exam-dna?course=${currentCourse.id}&cycle=${selectedCycle}`}
                className="w-full py-2.5 px-4 bg-secondary text-secondary-foreground hover:bg-secondary/80 border border-border/60 text-xs font-semibold rounded-xl transition-all flex items-center justify-center gap-2 shadow-xs"
              >
                <span>Inspect Exam DNA</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </div>

            {/* Capability 3: Study Plan Execution */}
            <div className="bg-card border border-border rounded-2xl p-6 shadow-sm flex flex-col justify-between space-y-6 hover:border-accent/40 transition-all group">
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-xl bg-accent/10 border border-accent/20 flex items-center justify-center text-accent">
                  <Target className="w-5 h-5 group-hover:rotate-45 transition-transform" />
                </div>
                <div className="space-y-1">
                  <div className="text-[11px] font-semibold text-accent uppercase tracking-wider">
                    Study Execution
                  </div>
                  <h3 className="text-lg font-bold text-foreground">
                    Interactive Study Plan
                  </h3>
                  <p className="text-xs text-muted-foreground leading-relaxed pt-1">
                    <em>&ldquo;What am I going to study and what have I completed?&rdquo;</em>
                  </p>
                </div>

                <div className="pt-2 border-t border-border/50 space-y-2 text-xs text-muted-foreground">
                  <div className="flex items-center justify-between">
                    <span>Completed Topics:</span>
                    <span className="font-semibold text-emerald-500 flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      {completedTaskCount} Completed
                    </span>
                  </div>
                  {studyContext?.last_topic_name ? (
                    <div className="p-2.5 rounded-lg bg-muted/30 border border-border/50 text-[11px] space-y-0.5">
                      <span className="text-muted-foreground block text-[10px] uppercase font-bold tracking-wider">Last Targeted Topic</span>
                      <span className="font-semibold text-foreground line-clamp-1">{studyContext.last_topic_name}</span>
                    </div>
                  ) : (
                    <div className="p-2.5 rounded-lg bg-muted/30 border border-border/50 text-[11px] space-y-0.5">
                      <span className="text-muted-foreground block text-[10px] uppercase font-bold tracking-wider">Active Workflow</span>
                      <span className="text-foreground block font-medium">Daily schedules &bull; Topic checkoffs &bull; Study notes</span>
                    </div>
                  )}
                </div>
              </div>

              <Link
                href={`/study-plan?course_id=${currentCourse.id}`}
                className="w-full py-2.5 px-4 bg-secondary text-secondary-foreground hover:bg-secondary/80 border border-border/60 text-xs font-semibold rounded-xl transition-all flex items-center justify-center gap-2 shadow-xs"
              >
                <span>Continue Study Plan</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </div>
          </div>
        </div>

        {/* 3. Quick-Launch Common Engineering Courses */}
        <section className="bg-card border border-border rounded-2xl p-6 md:p-8 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border/50 pb-4">
            <div>
              <h2 className="text-lg font-bold tracking-tight text-foreground flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-accent" />
                Quick-Switch Engineering Courses
              </h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                Switch study context to another archived SRMIST engineering course
              </p>
            </div>
            <Link
              href="/courses"
              className="text-xs font-medium text-accent hover:underline flex items-center gap-1"
            >
              <span>View All 31 Cataloged Courses</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 pt-1">
            {eligibleCourses.slice(0, 8).map((course) => {
              const isSelected = course.id === selectedCourseId;
              return (
                <button
                  key={course.id}
                  onClick={() => handleCourseChange(course.id)}
                  className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between gap-2 ${
                    isSelected
                      ? "bg-accent/10 border-accent/40 shadow-xs"
                      : "bg-muted/20 border-border/60 hover:border-accent/30 hover:bg-muted/40"
                  }`}
                >
                  <div className="space-y-1">
                    <span className="text-[10px] font-mono font-bold text-muted-foreground">
                      {course.code}
                    </span>
                    <h3 className="text-xs font-bold text-foreground line-clamp-2 leading-snug">
                      {course.name}
                    </h3>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-1 border-t border-border/40">
                    <span>{course.paperCount} exams</span>
                    {isSelected ? (
                      <span className="text-[10px] font-bold text-accent px-1.5 py-0.5 rounded bg-accent/15">Active</span>
                    ) : (
                      <span className="text-[10px] text-muted-foreground hover:text-foreground">Switch &rarr;</span>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        {/* 4. Non-Predictive Institutional Scope Notice */}
        <div className="p-4 rounded-xl bg-muted/20 border border-border/40 text-xs text-muted-foreground flex items-start gap-2.5">
          <ShieldCheck className="w-4 h-4 text-accent shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-semibold text-foreground">
              MintAI Evidence-Based Analytics Notice
            </p>
            <p className="text-[11px] leading-relaxed">
              MintAI derives intelligence signals strictly from verified past examination papers and official SRMIST syllabus documents. MintAI does not claim or guarantee future examination outcomes, and examination formats remain subject to institutional discretion.
            </p>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
