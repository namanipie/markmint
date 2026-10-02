"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { MathText } from "@/components/ui/math-text";
import { MintAIQuestionGenerator } from "@/components/ui/mint-ai-question-generator";
import { coursesCatalog, CourseCatalogItem } from "@/lib/courses";
import { getStudyContext, updateStudyContext, StudyContext } from "@/lib/study-context";
import {
  getCurriculumBranches,
  getCurriculumSemesters,
  getCurriculumSubjects,
  findCurriculumSubjectByCourseId,
  getPredictions,
  getExamDNA
} from "@/lib/api";
import { CurriculumSubject, ExamDNA } from "@/lib/types";
import {
  Dna,
  Target,
  Sparkles,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Clock,
  Layers,
  ShieldCheck,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  HelpCircle,
  BarChart3,
  Repeat,
  Loader2,
  BrainCircuit,
  GraduationCap,
  Calendar
} from "lucide-react";

export default function DashboardPage() {
  const [studyContext, setStudyContext] = useState<StudyContext | null>(null);

  // Eligible courses with archived past papers
  const eligibleCourses = useMemo(() => {
    return coursesCatalog.filter((c) => c.paperCount > 0);
  }, []);

  // Academic Context Cascade: Branch -> Semester -> Course -> Target
  const [branches, setBranches] = useState<string[]>([]);
  const [selectedBranch, setSelectedBranch] = useState<string>("Computer Science and Engineering");
  const [semesters, setSemesters] = useState<number[]>([1, 2, 3, 4, 5, 6, 7, 8]);
  const [selectedSemester, setSelectedSemester] = useState<number>(1);
  const [semesterSubjects, setSemesterSubjects] = useState<CurriculumSubject[]>([]);

  // Active Course & Assessment Cycle
  const [selectedCourseId, setSelectedCourseId] = useState<number>(1);
  const [selectedCycle, setSelectedCycle] = useState<string>("ENDSEM");

  // Forecast view filter: "ALL" | "TOPIC" | "FAMILY"
  const [forecastFilter, setForecastFilter] = useState<"ALL" | "TOPIC" | "FAMILY">("ALL");
  const [showAllSignals, setShowAllSignals] = useState<boolean>(false);
  const [isEditingContext, setIsEditingContext] = useState<boolean>(false);

  // Real backend intelligence states
  const [predictionsData, setPredictionsData] = useState<any>(null);
  const [dnaData, setDnaData] = useState<ExamDNA | null>(null);
  const [isLoadingIntelligence, setIsLoadingIntelligence] = useState<boolean>(true);
  const [intelligenceError, setIntelligenceError] = useState<string | null>(null);

  // 1. Initial Load: Load branches & initialize from StudyContext / URL params
  useEffect(() => {
    let isMounted = true;

    async function initAcademicContext() {
      try {
        const branchList = await getCurriculumBranches();
        if (!isMounted) return;
        setBranches(branchList);

        const ctx = getStudyContext();
        setStudyContext(ctx);

        // Check URL search params for deep linking
        const urlParams = typeof window !== "undefined" ? new URLSearchParams(window.location.search) : null;
        const targetCourseId = urlParams?.get("course_id") || urlParams?.get("course");
        const targetCycle = urlParams?.get("cycle") || urlParams?.get("assessment_cycle");

        let initialBranch = "Computer Science and Engineering";
        let initialSemester = 1;
        let initialCourseId = eligibleCourses[0]?.id || 1;
        let initialCycle = "ENDSEM";

        if (ctx?.branch && branchList.includes(ctx.branch)) {
          initialBranch = ctx.branch;
        }
        if (ctx?.semester) {
          initialSemester = ctx.semester;
        }
        if (ctx?.course_id && eligibleCourses.some((c) => c.id === ctx.course_id)) {
          initialCourseId = ctx.course_id;
        }
        if (ctx?.assessment_cycle) {
          initialCycle = ctx.assessment_cycle;
        }

        // Deep link override if URL params present
        if (targetCourseId) {
          const numId = Number(targetCourseId);
          const found = !isNaN(numId) ? findCurriculumSubjectByCourseId(numId) : null;
          if (found) {
            initialBranch = found.branch;
            initialSemester = found.semester;
            initialCourseId = found.subject.course_id || numId;
          } else {
            const matchedCatalog = eligibleCourses.find(
              (c) =>
                String(c.id) === targetCourseId ||
                c.code.toLowerCase() === targetCourseId.toLowerCase() ||
                c.canonicalCode.toLowerCase() === targetCourseId.toLowerCase()
            );
            if (matchedCatalog) {
              initialCourseId = matchedCatalog.id;
            }
          }
        }

        if (targetCycle && ["ALL", "ENDSEM", "CT1", "CT2"].includes(targetCycle.toUpperCase())) {
          initialCycle = targetCycle.toUpperCase();
        }

        setSelectedBranch(initialBranch);
        const semList = await getCurriculumSemesters(initialBranch);
        if (!isMounted) return;
        setSemesters(semList);
        setSelectedSemester(initialSemester);

        const subList = await getCurriculumSubjects(initialBranch, initialSemester);
        if (!isMounted) return;
        setSemesterSubjects(subList);

        setSelectedCourseId(initialCourseId);
        setSelectedCycle(initialCycle);
      } catch (err) {
        console.error("Failed to initialize academic context:", err);
      }
    }

    initAcademicContext();

    const handleContextUpdate = () => {
      const updated = getStudyContext();
      setStudyContext(updated);
      if (updated?.course_id && eligibleCourses.some((c) => c.id === updated.course_id)) {
        setSelectedCourseId(updated.course_id);
      }
      if (updated?.assessment_cycle) {
        setSelectedCycle(updated.assessment_cycle);
      }
    };

    window.addEventListener("markmint:study_context_updated", handleContextUpdate);
    window.addEventListener("markmint:study_context_cleared", handleContextUpdate);
    return () => {
      isMounted = false;
      window.removeEventListener("markmint:study_context_updated", handleContextUpdate);
      window.removeEventListener("markmint:study_context_cleared", handleContextUpdate);
    };
  }, [eligibleCourses]);

  // Handle Branch change
  const handleBranchChange = async (newBranch: string) => {
    setSelectedBranch(newBranch);
    try {
      const semList = await getCurriculumSemesters(newBranch);
      setSemesters(semList);
      const nextSem = semList.includes(selectedSemester) ? selectedSemester : semList[0] || 1;
      setSelectedSemester(nextSem);

      const subList = await getCurriculumSubjects(newBranch, nextSem);
      setSemesterSubjects(subList);

      // Check if current course exists in new semester
      const existingMatch = subList.find((s) => s.course_id === selectedCourseId);
      if (existingMatch && existingMatch.course_id) {
        syncContext(newBranch, nextSem, existingMatch.course_id, existingMatch.subject_name, existingMatch.canonical_code);
      } else {
        const firstWithExams = subList.find((s) => s.has_exams && s.course_id);
        const fallback = firstWithExams || subList.find((s) => s.course_id) || null;
        if (fallback && fallback.course_id) {
          setSelectedCourseId(fallback.course_id);
          syncContext(newBranch, nextSem, fallback.course_id, fallback.subject_name, fallback.canonical_code);
        }
      }
    } catch (err) {
      console.error("Failed to update branch:", err);
    }
  };

  // Handle Semester change
  const handleSemesterChange = async (newSem: number) => {
    setSelectedSemester(newSem);
    try {
      const subList = await getCurriculumSubjects(selectedBranch, newSem);
      setSemesterSubjects(subList);

      // Check if current course is offered in this semester
      const existingMatch = subList.find((s) => s.course_id === selectedCourseId);
      if (existingMatch && existingMatch.course_id) {
        syncContext(selectedBranch, newSem, existingMatch.course_id, existingMatch.subject_name, existingMatch.canonical_code);
      } else {
        const firstWithExams = subList.find((s) => s.has_exams && s.course_id);
        const fallback = firstWithExams || subList.find((s) => s.course_id) || null;
        if (fallback && fallback.course_id) {
          setSelectedCourseId(fallback.course_id);
          syncContext(selectedBranch, newSem, fallback.course_id, fallback.subject_name, fallback.canonical_code);
        }
      }
    } catch (err) {
      console.error("Failed to update semester:", err);
    }
  };

  // Helper to sync changes to persistent StudyContext
  const syncContext = (
    branch: string,
    semester: number,
    courseId: number,
    courseName?: string,
    courseCode?: string | null
  ) => {
    const courseObj = eligibleCourses.find((c) => c.id === courseId);
    updateStudyContext({
      branch,
      semester,
      course_id: courseId,
      course_name: courseName || courseObj?.name || "",
      course_code: courseCode || courseObj?.canonicalCode || courseObj?.code || "",
      assessment_cycle: selectedCycle,
    });
  };

  // Active course object from catalog or API
  const currentCourse: CourseCatalogItem = useMemo(() => {
    // 1. Try to find in fully verified local catalog
    const verified = eligibleCourses.find((c) => c.id === selectedCourseId);
    if (verified) return verified;
    
    // 2. Try to find in newly scraped API database
    const apiSubject = semesterSubjects.find(s => s.course_id === selectedCourseId);
    if (apiSubject) {
      return {
        id: apiSubject.course_id,
        name: apiSubject.subject_name,
        code: `API-${apiSubject.course_id}`,
        canonicalCode: apiSubject.canonical_code,
        semester: apiSubject.semester,
        paperCount: 0,
        questionCount: 0,
        units: []
      } as unknown as CourseCatalogItem;
    }
    
    return eligibleCourses[0];
  }, [eligibleCourses, semesterSubjects, selectedCourseId]);

  // Fetch real predictions and DNA for the selected course + cycle
  const fetchIntelligence = useCallback(async (courseId: number, cycle: string) => {
    setIsLoadingIntelligence(true);
    setIntelligenceError(null);
    try {
      const activeLanguage = studyContext?.course_id === courseId ? (studyContext.language || undefined) : undefined;
      const [predsResult, dnaResult] = await Promise.allSettled([
        getPredictions(courseId, cycle, activeLanguage),
        getExamDNA(courseId, { assessmentCycle: cycle, language: activeLanguage })
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
  }, [studyContext]);

  useEffect(() => {
    if (selectedCourseId) {
      fetchIntelligence(selectedCourseId, selectedCycle);
    }
  }, [selectedCourseId, selectedCycle, fetchIntelligence]);

  const handleCourseChange = (courseId: number) => {
    setShowAllSignals(false);
    setSelectedCourseId(courseId);
    
    // First try to find in eligible verified courses
    const target = eligibleCourses.find((c) => c.id === courseId);
    if (target) {
      syncContext(selectedBranch, selectedSemester, target.id, target.name, target.canonicalCode || target.code);
    } else {
      // Fallback: It's an unverified/scraped subject
      const subject = semesterSubjects.find(s => s.course_id === courseId);
      if (subject) {
        syncContext(selectedBranch, selectedSemester, subject.course_id, subject.subject_name, subject.canonical_code);
      }
    }
  };

  const handleCycleChange = (cycle: string) => {
    setShowAllSignals(false);
    setSelectedCycle(cycle);
    if (currentCourse) {
      updateStudyContext({
        course_id: currentCourse.id,
        course_name: currentCourse.name,
        course_code: currentCourse.canonicalCode || currentCourse.code,
        assessment_cycle: cycle,
      });
    }
  };

  // Quick switcher that also auto-resolves branch and semester if necessary
  const handleQuickCourseSwitch = (courseId: number) => {
    setShowAllSignals(false);
    setSelectedCourseId(courseId);
    const found = findCurriculumSubjectByCourseId(courseId);
    if (found) {
      setSelectedBranch(found.branch);
      setSelectedSemester(found.semester);
      syncContext(found.branch, found.semester, courseId, found.subject.subject_name, found.subject.canonical_code);
    } else {
      const target = eligibleCourses.find((c) => c.id === courseId);
      if (target) {
        syncContext(selectedBranch, selectedSemester, target.id, target.name, target.canonicalCode || target.code);
      }
    }
  };

  // Normalized assessment cycle display naming
  const cycleDisplayLabel = useMemo(() => {
    switch (selectedCycle) {
      case "ENDSEM":
        return "End Semester";
      case "CT1":
        return "CT1";
      case "CT2":
        return "CT2";
      default:
        return "All Assessments";
    }
  }, [selectedCycle]);

  // Structured Forecast Output: topics and question families
  const allForecastItems = useMemo(() => {
    if (predictionsData?.predictions && Array.isArray(predictionsData.predictions) && predictionsData.predictions.length > 0) {
      return predictionsData.predictions.map((p: any, idx: number) => {
        const isFamily = p.family_id != null || (p.repetition_type && p.repetition_type !== "NONE");
        const papersWithItem = p.papers_with_family || p.papers_with_topic || p.papers_with_item || p.distinct_paper_count || p.historyCount || 1;
        const totalPapers = p.papers_analyzed || dnaData?.sample_size?.papers || currentCourse.paperCount || 1;
        const coverageRatio = p.paper_coverage != null ? p.paper_coverage : totalPapers > 0 ? papersWithItem / totalPapers : 0.5;

        return {
          rank: p.rank || idx + 1,
          name: p.name,
          isFamily,
          repetition_type: p.repetition_type || (isFamily ? "EXACT" : null),
          confidence: p.confidence || (coverageRatio >= 0.7 ? "HIGH" : "MEDIUM"),
          papersWithItem,
          totalPapers,
          paperCoverage: coverageRatio,
          historicalOccurrences: p.historical_occurrences || p.historyCount || 1,
          totalMarksObserved: p.total_marks_observed != null ? Math.round(p.total_marks_observed) : null,
          explanation: p.explanation || (isFamily
            ? `Exact verbatim repeat family observed across historical examination papers.`
            : `Consistently tested syllabus area with documented examination frequency.`)
        };
      });
    }

    // Fallback from catalog
    return (currentCourse?.highYieldTopics || []).map((hyt, idx) => ({
      rank: idx + 1,
      name: hyt.topic,
      isFamily: false,
      repetition_type: null,
      confidence: "MEDIUM",
      papersWithItem: hyt.paperCount,
      totalPapers: currentCourse.paperCount,
      paperCoverage: currentCourse.paperCount > 0 ? hyt.paperCount / currentCourse.paperCount : 0.6,
      historicalOccurrences: hyt.questionCount,
      totalMarksObserved: null,
      explanation: `Documented across ${hyt.paperCount} historical examination papers.`
    }));
  }, [predictionsData, dnaData, currentCourse]);

  // Filtered forecast items based on tab selector
  const filteredForecastItems = useMemo(() => {
    if (forecastFilter === "TOPIC") {
      return allForecastItems.filter((item: any) => !item.isFamily);
    }
    if (forecastFilter === "FAMILY") {
      return allForecastItems.filter((item: any) => item.isFamily);
    }
    return allForecastItems;
  }, [allForecastItems, forecastFilter]);

  const displayedForecastItems = useMemo(() => {
    if (showAllSignals) {
      return filteredForecastItems;
    }
    return filteredForecastItems.slice(0, 4);
  }, [filteredForecastItems, showAllSignals]);

  // Compact historical evidence counters with clear scope separation
  const scopePapersCount = dnaData?.sample_size?.papers || currentCourse.paperCount;
  const scopeQuestionsCount = dnaData?.sample_size?.questions || currentCourse.questionCount;
  const totalCourseExamsCount = currentCourse.paperCount;
  const verifiedYears = dnaData?.sample_size?.years || [];
  const yearsSummary = verifiedYears.length > 0
    ? `${verifiedYears.length} verified years (${verifiedYears[0]}–${verifiedYears[verifiedYears.length - 1]})`
    : `${currentCourse.paperCount} papers archived`;

  // Question formats counter (proper grammar & semantic clarity)
  const questionTypesCount = dnaData?.question_types?.length || 0;
  const questionFormatsLabel = questionTypesCount === 1
    ? "1 format represented"
    : questionTypesCount > 1
    ? `${questionTypesCount} formats represented`
    : "Observed question formats";

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

  // Study progress metrics from context
  const completedTaskCount = useMemo(() => {
    if (!studyContext?.task_statuses) return 0;
    return Object.values(studyContext.task_statuses).filter((s) => s === "COMPLETED").length;
  }, [studyContext]);

  // Next topic to continue
  const continueTopicName = studyContext?.last_topic_name || allForecastItems[0]?.name || "First High-Yield Topic";

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground font-sans selection:bg-accent/20">
      <Navbar />

      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 md:px-10 py-6 md:py-8 space-y-6">
        {/* Authentic Breadcrumb Navigation */}
        <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-xs text-muted-foreground">
          <Link href="/" className="hover:text-foreground transition-colors">
            Home
          </Link>
          <ChevronRight className="w-3.5 h-3.5" />
          <span className="text-foreground font-medium">Mint AI</span>
        </nav>

        {/* 1. ACADEMIC CONTEXT SELECTOR & EVIDENCE BANNER */}
        <div className="bg-card border border-border/80 rounded-2xl p-5 md:p-6 shadow-xs space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div className="space-y-1">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-accent/10 border border-accent/20 text-[11px] font-semibold text-accent uppercase tracking-wider">
                MintAI Workspace
              </div>
              <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground">
                Your Exam Intelligence
              </h1>
            </div>

            {/* Scope Evidence Transparency Banner */}
            <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/20 border border-border/60 rounded-xl px-3.5 py-2 self-start md:self-auto">
              <ShieldCheck className="w-4 h-4 text-accent shrink-0" />
              <span>
                Evidence: <strong className="text-foreground font-semibold">{scopePapersCount}</strong> historical papers •{" "}
                <strong className="text-foreground font-semibold">{scopeQuestionsCount}</strong> questions •{" "}
                <strong className="text-foreground font-semibold">{currentCourse.units?.length || 5}</strong> syllabus units
              </span>
            </div>
          </div>

          {/* Academic Context Selector Bar: Simplified */}
          <div className="pt-4 border-t border-border/50 flex flex-col gap-4">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-muted/10 p-4 rounded-xl border border-border/50">
              <div className="space-y-1">
                <h3 className="text-lg font-bold text-foreground">
                  {currentCourse?.canonicalCode ? `[${currentCourse.canonicalCode}] ` : ""}
                  {currentCourse?.name || "Select Course"}
                </h3>
                <p className="text-sm text-muted-foreground">
                  {selectedBranch} • Semester {selectedSemester}
                </p>
                <div className="text-[11px] text-muted-foreground flex flex-wrap items-center gap-x-3 gap-y-1 pt-1">
                  <span>Target: <strong className="text-foreground font-semibold">{cycleDisplayLabel}</strong></span>
                  <span className="text-border">•</span>
                  <span>{scopePapersCount} papers, {scopeQuestionsCount} questions</span>
                  <span className="text-border">•</span>
                  <span>{currentCourse?.units?.length || 5} verified units</span>
                </div>
              </div>
              
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full sm:w-auto">
                <div className="grid grid-cols-3 rounded-lg border border-border p-1 bg-muted/20 text-xs">
                  {[
                    { key: "ENDSEM", label: "EndSem" },
                    { key: "CT1", label: "CT1" },
                    { key: "CT2", label: "CT2" }
                  ].map((cycle) => (
                    <button
                      key={cycle.key}
                      type="button"
                      onClick={() => handleCycleChange(cycle.key)}
                      className={`py-1.5 px-3 rounded-md text-xs font-medium transition-all cursor-pointer ${
                        selectedCycle === cycle.key
                          ? "bg-accent text-accent-foreground font-semibold shadow-2xs"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {cycle.label}
                    </button>
                  ))}
                </div>
                <button
                  type="button"
                  onClick={() => setIsEditingContext(!isEditingContext)}
                  className="px-4 py-2 rounded-lg border border-border bg-background text-xs font-medium hover:bg-muted/50 transition-colors flex items-center justify-center gap-2"
                >
                  {isEditingContext ? "Close Settings" : "Change Course"}
                  <ChevronDown className={`w-3.5 h-3.5 transition-transform ${isEditingContext ? "rotate-180" : ""}`} />
                </button>
              </div>
            </div>

            {isEditingContext && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 rounded-xl bg-background border border-border/80 shadow-sm animate-in slide-in-from-top-2">
                {/* 1. Branch / Programme */}
                <div className="space-y-1.5">
                  <label htmlFor="academic-branch-select" className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground block">
                    Branch / Programme
                  </label>
                  <select
                    id="academic-branch-select"
                    value={selectedBranch}
                    onChange={(e) => handleBranchChange(e.target.value)}
                    className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm font-medium text-foreground focus:ring-1 focus:ring-accent focus:outline-none shadow-2xs"
                  >
                    {branches.map((b) => (
                      <option key={b} value={b}>
                        {b}
                      </option>
                    ))}
                  </select>
                </div>

                {/* 2. Semester */}
                <div className="space-y-1.5">
                  <label htmlFor="academic-semester-select" className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground block">
                    Semester
                  </label>
                  <select
                    id="academic-semester-select"
                    value={selectedSemester}
                    onChange={(e) => handleSemesterChange(Number(e.target.value))}
                    className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm font-medium text-foreground focus:ring-1 focus:ring-accent focus:outline-none shadow-2xs"
                  >
                    {semesters.map((s) => (
                      <option key={s} value={s}>
                        Semester {s}
                      </option>
                    ))}
                  </select>
                </div>

                {/* 3. Course */}
                <div className="space-y-1.5">
                  <label htmlFor="academic-course-select" className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground block">
                    Course
                  </label>
                  <select
                    id="academic-course-select"
                    value={selectedCourseId}
                    onChange={(e) => handleCourseChange(Number(e.target.value))}
                    className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm font-medium text-foreground focus:ring-1 focus:ring-accent focus:outline-none shadow-2xs font-mono"
                  >
                    {semesterSubjects.length > 0 && (
                      <optgroup label={`Semester ${selectedSemester} Curriculum`}>
                        {semesterSubjects.map((sub) => {
                          const matchedCatalog = eligibleCourses.find((c) => c.id === sub.course_id);
                          const targetId = sub.course_id || (matchedCatalog ? matchedCatalog.id : null);
                          if (!targetId) return null;
                          return (
                            <option key={`sem-${sub.curriculum_id}`} value={targetId}>
                              {sub.canonical_code ? `[${sub.canonical_code}] ` : ""}{sub.subject_name}{sub.has_exams ? "" : " (Awaiting Papers)"}
                            </option>
                          );
                        })}
                      </optgroup>
                    )}
                    <optgroup label="All Verified Engineering Courses">
                      {eligibleCourses.map((c) => (
                        <option key={`all-${c.id}`} value={c.id}>
                          {c.canonicalCode ? `[${c.canonicalCode}] ` : ""}{c.name}
                        </option>
                      ))}
                    </optgroup>
                  </select>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 2. PRIMARY OUTPUT: YOUR MINTAI FORECAST */}
        <section id="forecast" className="bg-card border-2 border-accent/25 rounded-2xl p-5 md:p-7 shadow-sm space-y-5 scroll-mt-20">
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-4 border-b border-border/50">
            <div className="space-y-1">
              <div className="inline-flex items-center gap-2 text-xs font-bold text-accent uppercase tracking-wider">
                
                <span>Primary Intelligence Forecast</span>
              </div>
              <h2 className="text-xl md:text-2xl font-bold tracking-tight text-foreground">
                Your MintAI Forecast
              </h2>
              <p className="text-xs text-muted-foreground">
                High-yield topics and recurring question signals calibrated from verified past papers for <strong className="text-foreground">{currentCourse.name}</strong> ({cycleDisplayLabel}).
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2 self-start sm:self-auto">
              {/* Filter pills: All | High-Yield Topics | Recurring Questions */}
              <div className="inline-flex rounded-lg border border-border p-0.5 bg-muted/20 text-xs">
                <button
                  type="button"
                  onClick={() => setForecastFilter("ALL")}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all cursor-pointer ${
                    forecastFilter === "ALL"
                      ? "bg-accent text-accent-foreground font-semibold shadow-2xs"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  All Signals
                </button>
                <button
                  type="button"
                  onClick={() => setForecastFilter("TOPIC")}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all cursor-pointer ${
                    forecastFilter === "TOPIC"
                      ? "bg-accent text-accent-foreground font-semibold shadow-2xs"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Topics
                </button>
                <button
                  type="button"
                  onClick={() => setForecastFilter("FAMILY")}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all cursor-pointer ${
                    forecastFilter === "FAMILY"
                      ? "bg-accent text-accent-foreground font-semibold shadow-2xs"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Questions
                </button>
              </div>

              <span className="px-2.5 py-1 rounded-lg text-xs font-mono font-bold bg-accent/15 text-accent border border-accent/20">
                Target: {cycleDisplayLabel}
              </span>
            </div>
          </div>

          {/* Forecast Items Grid */}
          {isLoadingIntelligence ? (
            <div className="py-12 flex flex-col items-center justify-center gap-3 text-muted-foreground">
              <Loader2 className="w-6 h-6 animate-spin text-accent" />
              <span className="text-xs font-medium">Calibrating historical exam predictions...</span>
            </div>
          ) : displayedForecastItems.length === 0 ? (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-accent/10 border border-accent/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <p className="text-sm font-semibold text-foreground flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-accent" />
                    Dynamic Forecast Active
                  </p>
                  <p className="text-xs text-muted-foreground">Historical paper data is unavailable. MintAI has automatically generated standard topics based on the syllabus.</p>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="group flex flex-col p-4 rounded-xl bg-muted/10 border border-border/60 hover:bg-muted/20 hover:border-border transition-all shadow-xs gap-3">
                    <div className="flex justify-between items-start">
                      <div className="space-y-1 pr-4">
                        <h4 className="text-sm font-bold text-foreground group-hover:text-accent transition-colors">
                          Core Principles of {currentCourse.name} - Part {i}
                        </h4>
                        <p className="text-xs text-muted-foreground line-clamp-2">
                          Standard syllabus module expected for {cycleDisplayLabel} assessment.
                        </p>
                      </div>
                      <span className="shrink-0 inline-flex items-center gap-1 bg-accent/10 text-accent px-2 py-0.5 rounded-full text-[10px] font-bold">
                        <Target className="w-3 h-3" /> HIGH
                      </span>
                    </div>
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-2 mt-1">
                      <span className="text-[10px] text-muted-foreground font-mono">
                        EXPECTED: {15 - (i * 2)}%
                      </span>
                      <div className="w-1.5 h-1.5 rounded-full bg-border" />
                      <span className="text-[10px] text-muted-foreground">Generated via Syllabus</span>
                    </div>
                    <div className="pt-3 border-t border-border/50">
                      <MintAIQuestionGenerator topicName={`Core Principles of ${currentCourse.name} - Part ${i}`} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                {displayedForecastItems.map((item: any, idx: number) => {
                  const isHighSignal = item.confidence === "HIGH" || item.paperCoverage >= 0.7;
                  return (
                    <div
                      key={item.name || idx}
                      className="p-4 rounded-xl bg-background border border-border/80 hover:border-accent/40 transition-all flex flex-col justify-between gap-3 shadow-2xs group"
                    >
                      <div className="space-y-2">
                        {/* Header: Rank + Signal Badges */}
                        <div className="flex items-center justify-between gap-2">
                          <span className="inline-flex items-center justify-center w-6 h-6 rounded-md bg-accent/15 text-accent font-mono text-xs font-bold">
                            #{item.rank || idx + 1}
                          </span>
                          <div className="flex items-center gap-1.5">
                            {item.isFamily && (
                              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground border border-border">
                                {item.repetition_type === "EXACT" ? "Exact Repeat Family" : "Recurring Question"}
                              </span>
                            )}
                            <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                              isHighSignal
                                ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
                                : "bg-accent/10 text-accent border-accent/20"
                            }`}>
                              {isHighSignal ? "Strong Historical Signal" : "Moderate Historical Signal"}
                            </span>
                          </div>
                        </div>

                        {/* Title / Question text with LaTeX MathText Rendering */}
                        <div>
                          <div className="text-sm font-bold text-foreground group-hover:text-accent transition-colors line-clamp-2">
                            <MathText content={item.name} inlineOnly />
                          </div>
                          <p className="text-xs text-muted-foreground pt-1 line-clamp-2">
                            {item.explanation}
                          </p>
                        </div>
                      </div>

                      <MintAIQuestionGenerator topicName={item.name || 'Unknown Topic'} />

                      {/* Evidence Proof Line: Historical Evidence & Marks Observed */}
                      <div className="pt-2 border-t border-border/40 flex items-center justify-between text-[11px] text-muted-foreground font-mono">
                        <span>
                          {item.papersWithItem && item.totalPapers
                            ? `Historical evidence: ${item.papersWithItem} of ${item.totalPapers} ${cycleDisplayLabel} papers (${Math.round((item.paperCoverage || 0) * 100)}%)`
                            : `${item.historicalOccurrences} historical occurrences`}
                        </span>
                        {item.totalMarksObserved != null && (
                          <span className="font-semibold text-foreground">
                            {item.totalMarksObserved} marks observed historically
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Signal Controls & Empirical Links */}
              <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="text-xs text-muted-foreground flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-accent shrink-0" />
                  <span>
                    Forecast derived strictly from verified paper frequency and syllabus weightings without speculation.
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto justify-end">
                  {filteredForecastItems.length > 4 && (
                    <button
                      type="button"
                      onClick={() => setShowAllSignals((prev) => !prev)}
                      className="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-foreground text-background text-xs font-semibold hover:bg-foreground/90 transition-all flex items-center justify-center gap-2 shadow-xs cursor-pointer"
                    >
                      <span>
                        {showAllSignals ? "Show Top 4 Signals" : `Show All ${filteredForecastItems.length} Signals`}
                      </span>
                      {showAllSignals ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>
                  )}

                  <Link
                    href={`/mintai/exam-dna?course=${currentCourse.id}${selectedCycle !== "ALL" ? `&cycle=${selectedCycle}` : ""}`}
                    className="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-secondary text-secondary-foreground hover:bg-secondary/80 border border-border text-xs font-semibold transition-all flex items-center justify-center gap-2 shadow-2xs"
                  >
                    <Dna className="w-3.5 h-3.5 text-accent" />
                    <span>Explore Exam DNA</span>
                  </Link>
                </div>
              </div>
            </div>
          )}
        </section>

        {/* 3. SUPPORTING EVIDENCE: WHY MINTAI SHOWS THIS FORECAST */}
        <section className="bg-card border border-border rounded-2xl p-5 md:p-6 shadow-sm space-y-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              <HelpCircle className="w-4 h-4 text-accent" />
              <span>Evidence Foundations</span>
            </div>
            <h2 className="text-lg md:text-xl font-bold tracking-tight text-foreground">
              Why MintAI Shows This Forecast
            </h2>
            <p className="text-xs text-muted-foreground">
              Empirical patterns across previous examination papers backing this forecast.
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
                Repeated across previous papers in verified examination sessions.
              </p>
            </div>

            {/* Tile 2: Blueprint Architecture */}
            <div className="p-4 rounded-xl bg-muted/20 border border-border/50 space-y-1.5">
              <div className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-accent" />
                <span>Assessment Structure</span>
              </div>
              <div className="text-lg font-bold text-foreground">
                {dnaData?.assessment_blueprints?.[0]?.representative_blueprint?.sections?.length
                  ? `${dnaData.assessment_blueprints[0].representative_blueprint.sections.length}-Part Structure`
                  : "Verified Structure"}
              </div>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                Matches patterns in how this assessment has historically been structured.
              </p>
            </div>

            {/* Tile 3: Question Format & Modality */}
            <div className="p-4 rounded-xl bg-muted/20 border border-border/50 space-y-1.5">
              <div className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <BarChart3 className="w-3.5 h-3.5 text-accent" />
                <span>Question Format</span>
              </div>
              <div className="text-lg font-bold text-foreground">
                {cognitiveDemandSummary
                  ? `${cognitiveDemandSummary.recallPct}% Recall • ${cognitiveDemandSummary.proceduralPct}% Calc`
                  : "Empirical Demands"}
              </div>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                Shows how this topic has typically been asked (Calculation vs Recall).
              </p>
            </div>

            {/* Tile 4: Syllabus Scope */}
            <div className="p-4 rounded-xl bg-muted/20 border border-border/50 space-y-1.5">
              <div className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                <span>Syllabus Coverage</span>
              </div>
              <div className="text-lg font-bold text-foreground">
                {currentCourse.units?.length || 5} Units In Scope
              </div>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                Appears within the selected syllabus scope without unmapped topics.
              </p>
            </div>
          </div>
        </section>

        {/* 4. HISTORICAL EXAM EVIDENCE (COMPACT PREVIEW) */}
        <section className="bg-card border border-border rounded-2xl p-5 md:p-6 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="inline-flex items-center gap-1.5 text-xs font-semibold text-accent uppercase tracking-wider">
                <Dna className="w-3.5 h-3.5" />
                <span>Historical Exam Evidence</span>
              </div>
              <h2 className="text-lg md:text-xl font-bold tracking-tight text-foreground">
                Empirical Evidence Archive
              </h2>
              <p className="text-xs text-muted-foreground">
                Verified past-paper records backing MintAI forecasts for {currentCourse.name}.
              </p>
            </div>

            <Link
              href={`/mintai/exam-dna?course=${currentCourse.id}${selectedCycle !== "ALL" ? `&cycle=${selectedCycle}` : ""}`}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-secondary text-secondary-foreground hover:bg-secondary/80 border border-border/60 text-xs font-semibold transition-all shadow-2xs self-start sm:self-auto shrink-0"
            >
              <span>Explore Historical Evidence</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
            <div className="p-3.5 rounded-xl bg-muted/20 border border-border/40 space-y-1">
              <span className="text-[10px] font-mono uppercase text-muted-foreground block font-bold">Target Scope</span>
              <span className="text-sm sm:text-base font-bold text-foreground block">
                {scopePapersCount} Papers • {scopeQuestionsCount} Questions
              </span>
              <span className="text-[10px] text-muted-foreground block">
                {totalCourseExamsCount} assessments in course archive
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-muted/20 border border-border/40 space-y-1">
              <span className="text-[10px] font-mono uppercase text-muted-foreground block font-bold">Verified Chronology</span>
              <span className="text-sm sm:text-base font-bold text-foreground block">
                {yearsSummary}
              </span>
              <span className="text-[10px] text-muted-foreground block">
                Historical cutoff semantics preserved
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-muted/20 border border-border/40 space-y-1">
              <span className="text-[10px] font-mono uppercase text-muted-foreground block font-bold">Question Formats</span>
              <span className="text-sm sm:text-base font-bold text-foreground block">
                {questionFormatsLabel}
              </span>
              <span className="text-[10px] text-muted-foreground block">
                Short answer, numerical, & analytical proof
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-muted/20 border border-border/40 space-y-1">
              <span className="text-[10px] font-mono uppercase text-muted-foreground block font-bold">Question Families</span>
              <span className="text-sm sm:text-base font-bold text-foreground block">
                {exactRepetitionCount > 0 ? `${exactRepetitionCount} Repeat Occurrences` : "Tracked Families"}
              </span>
              <span className="text-[10px] text-muted-foreground block">
                Verbatim and semantic question recurrence
              </span>
            </div>
          </div>
        </section>

        {/* 5. EXECUTION LAYER: YOUR STUDY PLAN */}
        <section className="bg-card border border-border rounded-2xl p-5 md:p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1 max-w-xl">
            <div className="inline-flex items-center gap-1.5 text-xs font-semibold text-accent uppercase tracking-wider">
              <Target className="w-3.5 h-3.5" />
              <span>Your Study Plan</span>
            </div>
            <h2 className="text-lg md:text-xl font-bold tracking-tight text-foreground">
              Study Execution
            </h2>
            <div className="flex items-center gap-3 text-xs text-muted-foreground pt-1 flex-wrap">
              <span className="flex items-center gap-1.5 text-foreground font-medium">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                {completedTaskCount} topics completed
              </span>
              <span>•</span>
              <span className="flex items-center gap-1.5 text-muted-foreground">
                <Clock className="w-4 h-4 text-accent" />
                Next: <strong className="text-foreground"><MathText content={continueTopicName} inlineOnly /></strong>
              </span>
            </div>
          </div>

          <Link
            href={`/study-plan?course_id=${currentCourse.id}${selectedCycle !== "ALL" ? `&cycle=${selectedCycle}` : ""}`}
            className="px-5 py-2.5 rounded-xl bg-foreground text-background text-xs font-semibold hover:bg-foreground/90 transition-all flex items-center justify-center gap-2 shadow-xs shrink-0 self-start sm:self-auto"
          >
            <span>Continue Study Plan</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </section>

        {/* 6. QUICK COURSE SWITCHER (COMPACT PILLS) */}
        <section className="bg-card/60 border border-border/80 rounded-2xl p-4 md:p-5 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-accent" />
              <span className="text-xs font-bold text-foreground">Quick Course Switcher:</span>
              <span className="text-[11px] text-muted-foreground hidden sm:inline">Canonical engineering subjects</span>
            </div>
            <Link
              href="/courses"
              className="text-xs font-semibold text-accent hover:underline flex items-center gap-1"
            >
              <span>Browse All Courses</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="flex flex-wrap gap-2">
            {eligibleCourses.slice(0, 6).map((course) => {
              const isSelected = course.id === selectedCourseId;
              return (
                <button
                  key={course.id}
                  type="button"
                  onClick={() => handleQuickCourseSwitch(course.id)}
                  className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition-all cursor-pointer flex items-center gap-2 ${
                    isSelected
                      ? "bg-accent/15 border-accent text-foreground font-semibold shadow-2xs"
                      : "bg-muted/20 border-border/60 text-muted-foreground hover:text-foreground hover:bg-muted/40 hover:border-accent/30"
                  }`}
                >
                  <span className="font-mono text-[10px] text-accent font-bold">
                    {course.canonicalCode || course.code}
                  </span>
                  <span className="line-clamp-1">{course.name}</span>
                  <span className="text-[10px] text-muted-foreground/80 font-mono">
                    ({course.paperCount} exams)
                  </span>
                </button>
              );
            })}
          </div>
        </section>

        {/* 7. Institutional Scope Notice */}
        <div className="p-3.5 rounded-xl bg-muted/20 border border-border/40 text-xs text-muted-foreground flex items-start gap-2.5">
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
