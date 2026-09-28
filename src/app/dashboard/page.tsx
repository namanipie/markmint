"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { coursesCatalog, CourseCatalogItem } from "@/lib/courses";
import { getStudyContext, updateStudyContext, StudyContext } from "@/lib/study-context";
import { getPredictions, getExamDNA } from "@/lib/api";
import { ExamDNA } from "@/lib/types";
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
  ChevronRight,
  HelpCircle,
  TrendingUp,
  BrainCircuit,
  Loader2,
  FileText,
  BarChart3,
  Repeat
} from "lucide-react";

export default function DashboardPage() {
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

  // Real backend intelligence states
  const [predictionsData, setPredictionsData] = useState<any>(null);
  const [dnaData, setDnaData] = useState<ExamDNA | null>(null);
  const [isLoadingIntelligence, setIsLoadingIntelligence] = useState<boolean>(true);
  const [intelligenceError, setIntelligenceError] = useState<string | null>(null);

  // Load study context on client mount
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

  // Fetch real predictions and DNA for the selected course + cycle
  const fetchIntelligence = useCallback(async (courseId: number, cycle: string) => {
    setIsLoadingIntelligence(true);
    setIntelligenceError(null);
    try {
      const [predsResult, dnaResult] = await Promise.allSettled([
        getPredictions(courseId, cycle),
        getExamDNA(courseId, cycle)
      ]);

      if (predsResult.status === "fulfilled") {
        setPredictionsData(predsResult.value);
      } else {
        setPredictionsData(null);
      }

      if (dnaResult.status === "fulfilled") {
        setDnaData(dnaResult.value);
      } else {
        setDnaData(null);
      }
    } catch (err: any) {
      setIntelligenceError(err?.message || "Failed to load exam intelligence.");
    } finally {
      setIsLoadingIntelligence(false);
    }
  }, []);

  useEffect(() => {
    if (selectedCourseId) {
      fetchIntelligence(selectedCourseId, selectedCycle);
    }
  }, [selectedCourseId, selectedCycle, fetchIntelligence]);

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

  // Normalized assessment cycle display naming: All, CT1, CT2, End Semester
  const cycleDisplayLabel = useMemo(() => {
    switch (selectedCycle) {
      case "ENDSEM":
        return "End Semester";
      case "CT1":
        return "CT1";
      case "CT2":
        return "CT2";
      default:
        return "All";
    }
  }, [selectedCycle]);

  // Top high-yield topics from real predictions or catalog fallback
  const topForecastTopics = useMemo(() => {
    if (predictionsData?.predictions && Array.isArray(predictionsData.predictions) && predictionsData.predictions.length > 0) {
      return predictionsData.predictions.slice(0, 4);
    }
    return (currentCourse?.highYieldTopics || []).slice(0, 4).map((hyt, idx) => ({
      rank: idx + 1,
      name: hyt.topic,
      confidence: "MEDIUM",
      papers_with_topic: hyt.paperCount,
      papers_analyzed: currentCourse.paperCount,
      paper_coverage: currentCourse.paperCount > 0 ? (hyt.paperCount / currentCourse.paperCount) : 0.6,
      historical_occurrences: hyt.questionCount,
      total_marks_observed: null,
      explanation: `Documented across ${hyt.paperCount} historical examination papers.`
    }));
  }, [predictionsData, currentCourse]);

  // Compact historical evidence counters
  const totalArchivedPapers = dnaData?.sample_size?.papers || currentCourse.paperCount;
  const totalAnalyzedQuestions = dnaData?.sample_size?.questions || currentCourse.questionCount;
  const verifiedYears = dnaData?.sample_size?.years || [];
  const yearsSummary = verifiedYears.length > 0
    ? `${verifiedYears.length} Verified Years (${verifiedYears[0]}–${verifiedYears[verifiedYears.length - 1]})`
    : `${currentCourse.paperCount} Papers Archived`;

  // Cognitive demand distribution summary
  const cognitiveDemandSummary = useMemo(() => {
    if (!dnaData?.cognitive_demand_distribution?.items) return null;
    const items = dnaData.cognitive_demand_distribution.items;
    const recall = items.find((i: any) => i.demand === "RECALL_AND_CONCEPT");
    const procedural = items.find((i: any) => i.demand === "PROCEDURAL_COMPUTATION");
    const analytical = items.find((i: any) => i.demand === "ANALYTICAL_PROOF_AND_DESIGN");
    return {
      recallPct: recall ? Math.round(recall.percentage * 100) : 0,
      proceduralPct: procedural ? Math.round(procedural.percentage * 100) : 0,
      analyticalPct: analytical ? Math.round(analytical.percentage * 100) : 0,
    };
  }, [dnaData]);

  // Recurrence summary
  const exactRepetitionCount = dnaData?.repetition?.exact_count || 0;

  // Next topic to continue
  const continueTopicName = studyContext?.last_topic_name || topForecastTopics[0]?.name || "First High-Yield Topic";

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground font-sans selection:bg-accent/20">
      <Navbar />

      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 md:px-10 py-6 md:py-8 space-y-6 md:space-y-8">
        {/* Authentic Breadcrumb Navigation */}
        <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-xs text-muted-foreground">
          <Link href="/" className="hover:text-foreground transition-colors">
            Home
          </Link>
          <ChevronRight className="w-3.5 h-3.5" />
          <span className="text-foreground font-medium">Dashboard</span>
        </nav>

        {/* 1. MintAI Header & Active Study Context Selector */}
        <div className="bg-card border border-border/80 rounded-2xl p-5 md:p-6 shadow-xs space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-accent/10 border border-accent/20 text-[11px] font-semibold text-accent uppercase tracking-wider">
                <BrainCircuit className="w-3.5 h-3.5" />
                MintAI Workspace
              </div>
              <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground">
                Your Exam Intelligence
              </h1>
              <p className="text-xs sm:text-sm text-muted-foreground">
                Evidence-based historical analysis and predictive exam forecasting for SRMIST courses.
              </p>
            </div>

            {/* Evidence Volume Badge */}
            <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/20 border border-border/60 rounded-xl px-3.5 py-2 self-start md:self-auto">
              <ShieldCheck className="w-4 h-4 text-accent shrink-0" />
              <span>
                <strong className="text-foreground font-semibold">{totalArchivedPapers}</strong> historical exams &bull;{" "}
                <strong className="text-foreground font-semibold">{totalAnalyzedQuestions}</strong> questions &bull;{" "}
                <strong className="text-foreground font-semibold">{currentCourse.units.length}</strong> syllabus units
              </span>
            </div>
          </div>

          {/* Context Selector Bar: Course + Assessment Target */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-border/50">
            <div className="flex flex-wrap items-center gap-3">
              {/* Course Selector */}
              <div className="flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-accent shrink-0" />
                <label htmlFor="dashboard-course-select" className="text-xs font-semibold text-foreground whitespace-nowrap">
                  Course:
                </label>
                <select
                  id="dashboard-course-select"
                  value={selectedCourseId}
                  onChange={(e) => handleCourseChange(Number(e.target.value))}
                  className="bg-background border border-border rounded-lg px-3 py-1.5 text-xs font-semibold text-foreground focus:ring-2 focus:ring-accent focus:outline-none min-w-[240px] sm:min-w-[280px] shadow-xs"
                >
                  {eligibleCourses.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.canonicalCode ? `[${c.canonicalCode}] ` : ""}{c.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Assessment Cycle Selector: Normalized Naming (All, CT1, CT2, End Semester) */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground whitespace-nowrap font-medium">Target:</span>
                <div className="inline-flex rounded-lg border border-border p-0.5 bg-muted/20 text-xs">
                  {[
                    { key: "ENDSEM", label: "End Semester" },
                    { key: "CT1", label: "CT1" },
                    { key: "CT2", label: "CT2" },
                    { key: "ALL", label: "All" }
                  ].map((cycle) => (
                    <button
                      key={cycle.key}
                      onClick={() => handleCycleChange(cycle.key)}
                      className={`px-3 py-1 rounded-md text-xs font-medium transition-all cursor-pointer ${
                        selectedCycle === cycle.key
                          ? "bg-accent text-accent-foreground font-semibold shadow-xs"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {cycle.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Quick Link to Forecast */}
            <Link
              href={`/mintai?course_id=${currentCourse.id}${selectedCycle !== "ALL" ? `&cycle=${selectedCycle}` : ""}`}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-accent hover:underline shrink-0"
            >
              <span>Full Forecast View</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* 2. PRIMARY OUTPUT: YOUR MINTAI FORECAST */}
        <section className="bg-card border-2 border-accent/20 rounded-2xl p-6 md:p-8 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-4 border-b border-border/50">
            <div className="space-y-1">
              <div className="inline-flex items-center gap-2 text-xs font-bold text-accent uppercase tracking-wider">
                <Sparkles className="w-4 h-4" />
                <span>Primary Intelligence Forecast</span>
              </div>
              <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground">
                Your MintAI Forecast
              </h2>
              <p className="text-xs sm:text-sm text-muted-foreground">
                High-yield topics calibrated from verified historical exam papers for <strong className="text-foreground">{currentCourse.name}</strong> ({cycleDisplayLabel}).
              </p>
            </div>

            <div className="flex items-center gap-2 self-start sm:self-auto">
              <span className="px-2.5 py-1 rounded-lg text-xs font-mono font-bold bg-accent/15 text-accent border border-accent/20">
                Target: {cycleDisplayLabel}
              </span>
              <span className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-secondary text-secondary-foreground border border-border">
                {topForecastTopics.length} High-Yield Topics
              </span>
            </div>
          </div>

          {/* Forecast Items Grid */}
          {isLoadingIntelligence ? (
            <div className="py-12 flex flex-col items-center justify-center gap-3 text-muted-foreground">
              <Loader2 className="w-6 h-6 animate-spin text-accent" />
              <span className="text-xs font-medium">Calibrating historical exam predictions...</span>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                {topForecastTopics.map((topic: any, idx: number) => {
                  const isHighSignal = topic.confidence === "HIGH" || (topic.paper_coverage && topic.paper_coverage >= 0.7);
                  return (
                    <div
                      key={topic.name || idx}
                      className="p-4 rounded-xl bg-background border border-border/80 hover:border-accent/40 transition-all flex flex-col justify-between gap-3 shadow-2xs group"
                    >
                      <div className="space-y-2">
                        <div className="flex items-center justify-between gap-2">
                          <span className="inline-flex items-center justify-center w-6 h-6 rounded-md bg-accent/15 text-accent font-mono text-xs font-bold">
                            #{topic.rank || idx + 1}
                          </span>
                          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                            isHighSignal
                              ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
                              : "bg-accent/10 text-accent border-accent/20"
                          }`}>
                            {isHighSignal ? "High Historical Signal" : "Moderate Historical Signal"}
                          </span>
                        </div>

                        <div>
                          <h3 className="text-sm font-bold text-foreground group-hover:text-accent transition-colors line-clamp-1">
                            {topic.name}
                          </h3>
                          <p className="text-xs text-muted-foreground pt-0.5 line-clamp-1">
                            {topic.explanation || `Appeared across ${topic.papers_with_topic || topic.historyCount || 0} archived exams.`}
                          </p>
                        </div>
                      </div>

                      {/* Evidence Proof Line */}
                      <div className="pt-2 border-t border-border/40 flex items-center justify-between text-[11px] text-muted-foreground font-mono">
                        <span>
                          {topic.papers_with_topic && topic.papers_analyzed
                            ? `Appeared in ${topic.papers_with_topic} of ${topic.papers_analyzed} papers (${Math.round((topic.paper_coverage || 0) * 100)}%)`
                            : `${topic.historical_occurrences || topic.historyCount || 1} historical questions`}
                        </span>
                        {topic.total_marks_observed && (
                          <span className="font-semibold text-foreground">
                            {Math.round(topic.total_marks_observed)} Marks
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Primary Call to Action */}
              <div className="pt-3 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="text-xs text-muted-foreground flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-accent shrink-0" />
                  <span>
                    Forecast derived strictly from verified paper frequency and syllabus weightings without speculation.
                  </span>
                </div>

                <Link
                  href={`/mintai?course_id=${currentCourse.id}${selectedCycle !== "ALL" ? `&cycle=${selectedCycle}` : ""}`}
                  className="w-full sm:w-auto px-6 py-3 rounded-xl bg-foreground text-background text-xs font-semibold hover:bg-foreground/90 transition-all flex items-center justify-center gap-2 shadow-xs"
                >
                  <span>Open Full Intelligence Forecast</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          )}
        </section>

        {/* 3. SUPPORTING EVIDENCE: WHY MINTAI IS SHOWING THIS */}
        <section className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              <HelpCircle className="w-4 h-4 text-accent" />
              <span>Evidence Foundations</span>
            </div>
            <h2 className="text-xl font-bold tracking-tight text-foreground">
              Why MintAI Shows This Forecast
            </h2>
            <p className="text-xs text-muted-foreground">
              Documented institutional signals backing the high-yield topic ranking.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 pt-1">
            {/* Tile 1: Historical Recurrence */}
            <div className="p-4 rounded-xl bg-muted/20 border border-border/50 space-y-1.5">
              <div className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <Repeat className="w-3.5 h-3.5 text-accent" />
                <span>Historical Recurrence</span>
              </div>
              <div className="text-lg font-bold text-foreground">
                {exactRepetitionCount > 0 ? `${exactRepetitionCount} Repeat Questions` : "Factual Repetition"}
              </div>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                Recurring question families identified across verified examination sessions.
              </p>
            </div>

            {/* Tile 2: Blueprint Architecture */}
            <div className="p-4 rounded-xl bg-muted/20 border border-border/50 space-y-1.5">
              <div className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-accent" />
                <span>Assessment Blueprint</span>
              </div>
              <div className="text-lg font-bold text-foreground">
                {dnaData?.assessment_blueprints?.[0]?.representative_blueprint?.sections?.length
                  ? `${dnaData.assessment_blueprints[0].representative_blueprint.sections.length}-Part Structure`
                  : "Verified Blueprint"}
              </div>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                Conforms to documented institutional sectioning, marks distribution, and choice rules.
              </p>
            </div>

            {/* Tile 3: Cognitive Demand Profile */}
            <div className="p-4 rounded-xl bg-muted/20 border border-border/50 space-y-1.5">
              <div className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <BarChart3 className="w-3.5 h-3.5 text-accent" />
                <span>Cognitive Modality</span>
              </div>
              <div className="text-lg font-bold text-foreground">
                {cognitiveDemandSummary
                  ? `${cognitiveDemandSummary.recallPct}% Recall &bull; ${cognitiveDemandSummary.proceduralPct}% Calc`
                  : "Empirical Demand"}
              </div>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                Observable question demands derived from wording, calculation, and proof modalities.
              </p>
            </div>

            {/* Tile 4: Syllabus Scope */}
            <div className="p-4 rounded-xl bg-muted/20 border border-border/50 space-y-1.5">
              <div className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                <span>Syllabus Calibration</span>
              </div>
              <div className="text-lg font-bold text-foreground">
                {currentCourse.units.length} Units Covered
              </div>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                Calibrated to the official SRMIST syllabus curriculum without unmapped topics.
              </p>
            </div>
          </div>
        </section>

        {/* 4. HISTORICAL EXAM EVIDENCE (EXAM DNA PREVIEW) */}
        <section className="bg-card border border-border rounded-2xl p-6 md:p-8 shadow-sm space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
            <div className="space-y-1">
              <div className="inline-flex items-center gap-2 text-xs font-semibold text-accent uppercase tracking-wider">
                <Dna className="w-4 h-4" />
                <span>Historical Exam DNA</span>
              </div>
              <h2 className="text-xl md:text-2xl font-bold tracking-tight text-foreground">
                Historical Exam Evidence
              </h2>
              <p className="text-xs sm:text-sm text-muted-foreground">
                The factual past-paper record backing MintAI&apos;s forecasts for <strong className="text-foreground">{currentCourse.name}</strong>.
              </p>
            </div>

            <Link
              href={`/mintai/exam-dna?course=${currentCourse.id}${selectedCycle !== "ALL" ? `&cycle=${selectedCycle}` : ""}`}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-secondary text-secondary-foreground hover:bg-secondary/80 border border-border/60 text-xs font-semibold transition-all shadow-2xs self-start sm:self-auto"
            >
              <span>Explore Historical Evidence</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-1">
            <div className="p-4 rounded-xl bg-muted/20 border border-border/50 space-y-1">
              <span className="text-[10px] font-mono uppercase font-bold text-muted-foreground">Exam Corpus Volume</span>
              <div className="text-xl font-bold text-foreground">
                {totalArchivedPapers} Papers &bull; {totalAnalyzedQuestions} Questions
              </div>
              <p className="text-[11px] text-muted-foreground">
                Zero synthetic questions. All evidence verified from institutional papers.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-muted/20 border border-border/50 space-y-1">
              <span className="text-[10px] font-mono uppercase font-bold text-muted-foreground">Chronology Verification</span>
              <div className="text-xl font-bold text-foreground">
                {yearsSummary}
              </div>
              <p className="text-[11px] text-muted-foreground">
                Temporal trends tracked across verified examination years with strict cutoff semantics.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-muted/20 border border-border/50 space-y-1">
              <span className="text-[10px] font-mono uppercase font-bold text-muted-foreground">Question Format Archetypes</span>
              <div className="text-xl font-bold text-foreground">
                {dnaData?.question_types?.length ? `${dnaData.question_types.length} Question Types` : "MCQ & Descriptive"}
              </div>
              <p className="text-[11px] text-muted-foreground">
                Categorized by short answer, numerical, algorithmic, and analytical proof questions.
              </p>
            </div>
          </div>
        </section>

        {/* 5. EXECUTION LAYER: YOUR STUDY PROGRESS */}
        <section className="bg-card border border-border rounded-2xl p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-xl">
            <div className="inline-flex items-center gap-2 text-xs font-semibold text-accent uppercase tracking-wider">
              <Target className="w-4 h-4" />
              <span>Study Execution</span>
            </div>
            <h2 className="text-xl font-bold tracking-tight text-foreground">
              Your Study Progress
            </h2>
            <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
              Move from exam analysis into an actual plan. Track topic checkoffs, practice historical question families, and review verified notes.
            </p>

            <div className="flex items-center gap-4 text-xs text-muted-foreground pt-1 flex-wrap">
              <span className="flex items-center gap-1.5 text-foreground font-medium">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                {completedTaskCount} topics completed
              </span>
              <span>&bull;</span>
              <span className="flex items-center gap-1.5 text-muted-foreground">
                <Clock className="w-4 h-4 text-accent" />
                Next: <strong className="text-foreground">{continueTopicName}</strong>
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <Link
              href={`/study-plan?course_id=${currentCourse.id}${selectedCycle !== "ALL" ? `&cycle=${selectedCycle}` : ""}`}
              className="px-6 py-3 rounded-xl bg-foreground text-background text-xs font-semibold hover:bg-foreground/90 transition-all flex items-center gap-2 shadow-xs"
            >
              <span>Continue Study Plan</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </section>

        {/* 6. Quick Course Switcher: Canonical Engineering Courses */}
        <section className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border/50 pb-3">
            <div>
              <h2 className="text-sm font-bold text-foreground flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-accent" />
                Quick Course Switcher
              </h2>
              <p className="text-[11px] text-muted-foreground">
                Switch active course intelligence across common engineering subjects
              </p>
            </div>
            <Link
              href="/courses"
              className="text-xs font-semibold text-accent hover:underline flex items-center gap-1"
            >
              <span>Browse All Courses</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {eligibleCourses.slice(0, 6).map((course) => {
              const isSelected = course.id === selectedCourseId;
              return (
                <button
                  key={course.id}
                  onClick={() => handleCourseChange(course.id)}
                  className={`p-3 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between gap-2 ${
                    isSelected
                      ? "bg-accent/10 border-accent/40 shadow-xs"
                      : "bg-muted/20 border-border/60 hover:border-accent/30 hover:bg-muted/40"
                  }`}
                >
                  <div className="space-y-0.5">
                    <span className="text-[9px] font-mono font-bold text-muted-foreground">
                      {course.code}
                    </span>
                    <h3 className="text-xs font-bold text-foreground line-clamp-2 leading-snug">
                      {course.name}
                    </h3>
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1 border-t border-border/40">
                    <span>{course.paperCount} exams</span>
                    {isSelected ? (
                      <span className="font-bold text-accent">Active</span>
                    ) : (
                      <span>Switch &rarr;</span>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        {/* 7. Institutional Scope Notice */}
        <div className="p-4 rounded-xl bg-muted/20 border border-border/40 text-xs text-muted-foreground flex items-start gap-2.5">
          <ShieldCheck className="w-4 h-4 text-accent shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <p className="font-semibold text-foreground text-[11px]">
              MintAI Evidence-Based Analytics Notice
            </p>
            <p className="text-[11px] leading-relaxed">
              MintAI derives intelligence signals strictly from verified past examination papers and official SRMIST syllabus documents. MintAI distinguishes documented historical facts from predictive signals and does not claim future certainty.
            </p>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
