"use client";



import React, { useState, useEffect, useMemo, useCallback } from "react";

import Link from "next/link";

import { Navbar } from "@/components/layout/navbar";

import { Footer } from "@/components/layout/footer";

import { MathText } from "@/components/ui/math-text";

import { Drawer } from "@/components/ui/drawer";

import { TopicQuestionsViewer } from "@/components/ui/topic-questions-viewer";

import { MintAIQuestionGenerator } from "@/components/ui/mint-ai-question-generator";

import { coursesCatalog, CourseCatalogItem } from "@/lib/courses";
import { ExamUnitSelector } from "@/components/analytics/exam-unit-selector";

import { getStudyContext, updateStudyContext, StudyContext } from "@/lib/study-context";

import {

  getCurriculumBranches,

  getCurriculumSemesters,

  getCurriculumSubjects,

  findCurriculumSubjectByCourseId,

  getPredictions,
  getModelPerformance,

  getExamDNA

} from "@/lib/api";

import { CurriculumSubject, ExamDNA } from "@/lib/types";

import { motion, AnimatePresence } from "framer-motion";

import {

  Dna,

  Sparkles,

  ArrowRight,

  ShieldCheck,

  ChevronRight,

  ChevronDown,

  ChevronUp,

  Search,

  Loader2,

  FileText,

  Info,

  X,

  BookOpen,

  Check,

  RotateCcw,

  FileCheck2,

  Layers,

  Megaphone

} from "lucide-react";



function cleanExplanation(text?: string | null): string {

  if (!text) return "";

  return text

    .replace(/\(\s*\d+\s*marks\s+across\s+(\d+)\s*question\(s\)\s*\)/gi, "across $1 historical questions")

    .replace(/\(\s*across\s+(\d+)\s*question\(s\)\s*\)/gi, "across $1 historical questions")

    .replace(/\s*representing\s+\d+\s*marks\.?/gi, ".")

    .replace(/\(\s*\d+\s*marks\s+total\s*\)/gi, "")

    .replace(/\s*and\s+\d+\s*marks/gi, "")

    .replace(/\(\s*\d+\s*marks\s*\)/gi, "")

    .replace(/\s{2,}/g, " ")

    .replace(/\s+\./g, ".")

    .trim();

}



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



  // Active Course: Null until explicitly chosen by user or via URL param (NO AUTOFILL)

  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);

  const [selectedCycle, setSelectedCycle] = useState<string>("ENDSEM");
  const [selectedUnits, setSelectedUnits] = useState<number[]>([1, 2, 3, 4, 5]);
  const [examScopeLabel, setExamScopeLabel] = useState<string>("End Semester");



  // Primary Course Selection Modal State

  const [isCourseModalOpen, setIsCourseModalOpen] = useState<boolean>(false);

  const [courseSearchQuery, setCourseSearchQuery] = useState<string>("");



  // Forecast view filter: "ALL" | "TOPIC" | "FAMILY"

  const [forecastFilter, setForecastFilter] = useState<"ALL" | "TOPIC" | "FAMILY">("ALL");

  const [showAllSignals, setShowAllSignals] = useState<boolean>(false);



  // Slide-over Practice Drawer State

  const [activePracticeTopic, setActivePracticeTopic] = useState<{

    name: string;

    rank?: number;

    probability?: number | null;

    isFamily?: boolean;

    repetition_type?: string | null;

    historicalOccurrences?: number;

    totalMarksObserved?: number | null;

    paperCoverage?: number;

    papersWithItem?: number;

    totalPapers?: number;

    explanation?: string;

  } | null>(null);

  const [drawerActiveTab, setDrawerActiveTab] = useState<"pyq" | "ai">("pyq");



  // Real backend intelligence states

  const [predictionsData, setPredictionsData] = useState<any>(null);

  const [dnaData, setDnaData] = useState<ExamDNA | null>(null);

  const [isLoadingIntelligence, setIsLoadingIntelligence] = useState<boolean>(false);

  const [intelligenceError, setIntelligenceError] = useState<string | null>(null);
  const [modelPerformance, setModelPerformance] = useState<any>(null);
  const [isLoadingPerformance, setIsLoadingPerformance] = useState<boolean>(false);



  // Lock body scroll and ESC listener when course selection modal is open

  useEffect(() => {

    const handleKeyDown = (e: KeyboardEvent) => {

      if (e.key === "Escape") setIsCourseModalOpen(false);

    };

    if (isCourseModalOpen) {

      window.addEventListener("keydown", handleKeyDown);

      document.body.style.overflow = "hidden";

    }

    return () => {

      window.removeEventListener("keydown", handleKeyDown);

      document.body.style.overflow = "";

    };

  }, [isCourseModalOpen]);



  // 1. Initial Load: Load branches & check for explicit deep link in URL

  useEffect(() => {

    let isMounted = true;



    async function initAcademicContext() {

      try {

        const branchList = await getCurriculumBranches();

        if (!isMounted) return;

        setBranches(branchList);



        const ctx = getStudyContext();

        setStudyContext(ctx);



        // Check URL search params for deep linking (e.g. ?course_id=2 or ?course=chemistry)

        const urlParams = typeof window !== "undefined" ? new URLSearchParams(window.location.search) : null;

        const targetCourseId = urlParams?.get("course_id") || urlParams?.get("course");

        const targetCycle = urlParams?.get("cycle") || urlParams?.get("assessment_cycle");



        let initialBranch = "Computer Science and Engineering";

        let initialSemester = 1;

        let initialCycle = "ENDSEM";



        if (targetCycle && ["ALL", "ENDSEM", "CT1", "CT2"].includes(targetCycle.toUpperCase())) {

          initialCycle = targetCycle.toUpperCase();

        }

        setSelectedCycle(initialCycle);

        const unitsParam = urlParams?.get("units");
        if (unitsParam) {
          const parsed = unitsParam.split(",").map(Number).filter(n => !isNaN(n) && n > 0);
          if (parsed.length > 0) {
            setSelectedUnits(parsed);
          }
        } else if (initialCycle === "CT1") {
          setSelectedUnits([1, 2]);
        } else if (initialCycle === "CT2") {
          setSelectedUnits([3, 4]);
        } else {
          setSelectedUnits([1, 2, 3, 4, 5]);
        }



        if (targetCourseId) {

          // Explicit deep link in URL: resolve and load requested course

          const numId = Number(targetCourseId);

          const found = !isNaN(numId) ? findCurriculumSubjectByCourseId(numId) : null;

          if (found) {

            initialBranch = found.branch;

            initialSemester = found.semester;

            setSelectedCourseId(found.subject.course_id || numId);

          } else {

            const matchedCatalog = eligibleCourses.find(

              (c) =>

                String(c.id) === targetCourseId ||

                c.code.toLowerCase() === targetCourseId.toLowerCase() ||

                c.canonicalCode.toLowerCase() === targetCourseId.toLowerCase() ||

                c.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').includes(targetCourseId.toLowerCase()) ||

                targetCourseId.toLowerCase().includes(c.name.toLowerCase().replace(/[^a-z0-9]+/g, '-')) ||

                c.name.toLowerCase().includes(targetCourseId.toLowerCase().replace(/-/g, ' '))

            );

            if (matchedCatalog) {

              setSelectedCourseId(matchedCatalog.id);

            }

          }

        } else {

          // NO COURSE IN URL: DO NOT AUTOFILL. PROMPT USER WITH PRIMARY MODAL

          setSelectedCourseId(null);

          setIsCourseModalOpen(true);

        }



        setSelectedBranch(initialBranch);

        const semList = await getCurriculumSemesters(initialBranch);

        if (!isMounted) return;

        setSemesters(semList);

        setSelectedSemester(initialSemester);



        const subList = await getCurriculumSubjects(initialBranch, initialSemester);

        if (!isMounted) return;

        setSemesterSubjects(subList);

      } catch (err) {

        console.error("Failed to initialize academic context:", err);

      }

    }



    initAcademicContext();



    const handleContextUpdate = () => {

      const updated = getStudyContext();

      setStudyContext(updated);

    };



    window.addEventListener("markmint:study_context_updated", handleContextUpdate);

    window.addEventListener("markmint:study_context_cleared", handleContextUpdate);

    return () => {

      isMounted = false;

      window.removeEventListener("markmint:study_context_updated", handleContextUpdate);

      window.removeEventListener("markmint:study_context_cleared", handleContextUpdate);

    };

  }, [eligibleCourses]);



  // Handle Branch change inside setup modal

  const handleBranchChange = async (newBranch: string) => {

    setSelectedBranch(newBranch);

    try {

      const semList = await getCurriculumSemesters(newBranch);

      setSemesters(semList);

      const nextSem = semList.includes(selectedSemester) ? selectedSemester : semList[0] || 1;

      setSelectedSemester(nextSem);



      const subList = await getCurriculumSubjects(newBranch, nextSem);

      setSemesterSubjects(subList);

    } catch (err) {

      console.error("Failed to update branch:", err);

    }

  };



  // Handle Semester change inside setup modal

  const handleSemesterChange = async (newSem: number) => {

    setSelectedSemester(newSem);

    try {

      const subList = await getCurriculumSubjects(selectedBranch, newSem);

      setSemesterSubjects(subList);

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



  // Active course object from catalog or API (null if no course selected yet)

  const currentCourse: CourseCatalogItem | null = useMemo(() => {

    if (!selectedCourseId) return null;



    const verified = eligibleCourses.find((c) => c.id === selectedCourseId);

    if (verified) return verified;



    const apiSubject = semesterSubjects.find((s) => s.course_id === selectedCourseId);

    if (apiSubject) {

      return {

        id: apiSubject.course_id!,

        name: apiSubject.subject_name,

        code: `API-${apiSubject.course_id}`,

        canonicalCode: apiSubject.canonical_code,

        semester: (apiSubject as any).semester || selectedSemester,

        paperCount: 0,

        questionCount: 0,

        units: []

      } as unknown as CourseCatalogItem;

    }



    return null;

  }, [eligibleCourses, semesterSubjects, selectedCourseId, selectedSemester]);



  // Instant Search Across All 43 Courses

  const searchedCourses = useMemo(() => {

    if (!courseSearchQuery.trim()) return [];

    const q = courseSearchQuery.toLowerCase().trim();

    return eligibleCourses.filter((c) =>

      c.name.toLowerCase().includes(q) ||

      c.code.toLowerCase().includes(q) ||

      (c.canonicalCode && c.canonicalCode.toLowerCase().includes(q))

    );

  }, [eligibleCourses, courseSearchQuery]);



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



  // Only fetch when course is explicitly selected by user

  useEffect(() => {

    if (selectedCourseId) {

      fetchIntelligence(selectedCourseId, selectedCycle);

    } else {

      setPredictionsData(null);

      setDnaData(null);

      setIsLoadingIntelligence(false);

    }

  }, [selectedCourseId, selectedCycle, fetchIntelligence]);



  // Explicit user course selection handler

  const handleCourseSwitch = (courseId: number) => {

    setShowAllSignals(false);

    setSelectedCourseId(courseId);

    setCourseSearchQuery("");

    setIsCourseModalOpen(false);



    const found = findCurriculumSubjectByCourseId(courseId);

    if (found) {

      setSelectedBranch(found.branch);

      setSelectedSemester(found.semester);

      syncContext(found.branch, found.semester, courseId, found.subject.subject_name, found.subject.canonical_code);

    } else {

      const target = eligibleCourses.find((c) => c.id === courseId);

      if (target) {

        syncContext(selectedBranch, selectedSemester, target.id, target.name, target.canonicalCode || target.code);

      } else {

        const subject = semesterSubjects.find((s) => s.course_id === courseId);

        if (subject && subject.course_id) {

          syncContext(selectedBranch, selectedSemester, subject.course_id, subject.subject_name, subject.canonical_code);

        }

      }

    }

  };



  const handleCycleChange = (cycle: string) => {

    setShowAllSignals(false);

    setSelectedCycle(cycle);

    if (cycle === "CT1") {
      setSelectedUnits([1, 2]);
    } else if (cycle === "CT2") {
      setSelectedUnits([3, 4]);
    } else {
      const allUnits = currentCourse?.units?.map(u => u.number) || [1, 2, 3, 4, 5];
      setSelectedUnits(allUnits);
    }

    if (currentCourse) {

      updateStudyContext({

        course_id: currentCourse.id,

        course_name: currentCourse.name,

        course_code: currentCourse.canonicalCode || currentCourse.code,

        assessment_cycle: cycle,

      });

    }

  };



  // Normalized assessment cycle display naming


  const handleUnitsChange = (units: number[], examLabel?: string) => {
    setSelectedUnits(units);
    if (examLabel) {
      setExamScopeLabel(examLabel);
    }
  };

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




  // Map any topic name or family to its corresponding unit number
  const getTopicUnit = useCallback((topicName: string): number => {
    if (!topicName || !currentCourse) return 1;
    const lower = topicName.toLowerCase().trim();

    // 1. Check currentCourse.units
    if (currentCourse.units && currentCourse.units.length > 0) {
      for (const u of currentCourse.units) {
        if (u.topics && u.topics.some(t => {
          const tLower = t.toLowerCase().trim();
          return tLower === lower || lower.includes(tLower) || tLower.includes(lower);
        })) {
          return u.number;
        }
      }
    }

    // 2. Check currentCourse.highYieldTopics
    if (currentCourse.highYieldTopics && currentCourse.highYieldTopics.length > 0) {
      const match = currentCourse.highYieldTopics.find(h => {
        const hLower = h.topic.toLowerCase().trim();
        return hLower === lower || lower.includes(hLower) || hLower.includes(lower);
      });
      if (match && match.unitNumber) return match.unitNumber;
    }

    let hash = 0;
    for (let i = 0; i < lower.length; i++) {
      hash = ((hash << 5) - hash) + lower.charCodeAt(i);
      hash |= 0;
    }
    const totalUnits = currentCourse.units?.length || 5;
    return (Math.abs(hash) % totalUnits) + 1;
  }, [currentCourse]);

  // Structured Forecast Output: topics and question families

  const allForecastItems = useMemo(() => {

    if (!currentCourse) return [];



    if (predictionsData?.predictions && Array.isArray(predictionsData.predictions) && predictionsData.predictions.length > 0) {

      return predictionsData.predictions.map((p: any, idx: number) => {

        const isFamily = p.family_id != null || (p.repetition_type && p.repetition_type !== "NONE");

        const papersWithItem = p.papers_with_family || p.papers_with_topic || p.papers_with_item || p.distinct_paper_count || p.historyCount || 1;

        const totalPapers = p.papers_analyzed || dnaData?.sample_size?.papers || currentCourse.paperCount || 1;

        const coverageRatio = p.paper_coverage != null ? p.paper_coverage : totalPapers > 0 ? papersWithItem / totalPapers : 0.5;

        const calibratedProb = p.probability != null ? Math.round(p.probability * 100) : (p.score != null ? Math.round(p.score * 100) : null);



        const unitNumber = getTopicUnit(p.name);
        const unitObj = currentCourse?.units?.find(u => u.number === unitNumber);
        const unitName = unitObj?.name || `Unit ${unitNumber}`;

        return {

          rank: p.rank || idx + 1,

          name: p.name,

          unitNumber,

          unitName,

          isFamily,

          repetition_type: p.repetition_type || (isFamily ? "EXACT" : null),

          confidence: p.confidence || (coverageRatio >= 0.7 ? "HIGH" : "MEDIUM"),

          probability: calibratedProb,

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

    return (currentCourse.highYieldTopics || []).map((hyt, idx) => {
      const unitNumber = hyt.unitNumber || getTopicUnit(hyt.topic);
      const unitObj = currentCourse?.units?.find(u => u.number === unitNumber);
      const unitName = unitObj?.name || `Unit ${unitNumber}`;

      return {

        rank: idx + 1,

        name: hyt.topic,

        unitNumber,

        unitName,

      isFamily: false,

      repetition_type: null,

      confidence: "MEDIUM",

      probability: null,

      papersWithItem: hyt.paperCount,

      totalPapers: currentCourse.paperCount,

      paperCoverage: currentCourse.paperCount > 0 ? hyt.paperCount / currentCourse.paperCount : 0.6,

      historicalOccurrences: hyt.questionCount,

      totalMarksObserved: null,

      explanation: `Documented across ${hyt.paperCount} historical examination papers.`

    }; });

  }, [predictionsData, dnaData, currentCourse]);



  // Filtered forecast items based on tab selector

  const filteredForecastItems = useMemo(() => {

    let items = allForecastItems;

    // 1. Filter by Selected Exam Units
    if (selectedUnits.length > 0 && selectedUnits.length < (currentCourse?.units?.length || 5)) {
      items = items.filter((item: any) => selectedUnits.includes(item.unitNumber));
    }

    // 2. Filter by Signal Type
    if (forecastFilter === "TOPIC") {
      return items.filter((item: any) => !item.isFamily);
    }
    if (forecastFilter === "FAMILY") {
      return items.filter((item: any) => item.isFamily);
    }

    return items;

  }, [allForecastItems, selectedUnits, currentCourse, forecastFilter]);



  const displayedForecastItems = useMemo(() => {

    if (showAllSignals) {

      return filteredForecastItems;

    }

    return filteredForecastItems.slice(0, 4);

  }, [filteredForecastItems, showAllSignals]);



  // Compact historical evidence counters

  const scopePapersCount = dnaData?.sample_size?.papers || currentCourse?.paperCount || 0;

  const scopeQuestionsCount = dnaData?.sample_size?.questions || currentCourse?.questionCount || 0;



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



        {/* 1. ACADEMIC CONTEXT SELECTOR & EVIDENCE TRUST BAR */}

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



            {/* Compact 1-Line Evidence Trust Bar */}

            {currentCourse ? (

              <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/20 border border-border/60 rounded-xl px-3.5 py-2 self-start md:self-auto flex-wrap">

                <ShieldCheck className="w-4 h-4 text-accent shrink-0" />

                <span>

                  Evidence: <strong className="text-foreground font-semibold">{scopePapersCount}</strong> verified papers •{" "}

                  <strong className="text-foreground font-semibold">{scopeQuestionsCount}</strong> questions •{" "}

                  <strong className="text-foreground font-semibold">{currentCourse.units?.length || 5}</strong> units

                </span>

                <span className="text-border mx-0.5">•</span>

                <Link

                  href={`/mintai/exam-dna?course=${currentCourse.id}${selectedCycle !== "ALL" ? `&cycle=${selectedCycle}` : ""}`}

                  className="font-semibold text-accent hover:underline flex items-center gap-1 shrink-0"

                >

                  <span>Exam DNA</span>

                  <ArrowRight className="w-3 h-3" />

                </Link>

              </div>

            ) : (

              <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/20 border border-border/60 rounded-xl px-3.5 py-2 self-start md:self-auto">

                <ShieldCheck className="w-4 h-4 text-accent shrink-0" />

                <span>

                  <strong>43</strong> engineering courses • <strong>313</strong> verified papers indexed

                </span>

              </div>

            )}

          </div>



          {/* Active Course Card: Primary Card to Choose / Switch Course */}

          <div className="pt-3 border-t border-border/50 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">

            {currentCourse ? (

              <button

                type="button"

                onClick={() => {

                  setCourseSearchQuery("");

                  setIsCourseModalOpen(true);

                }}

                className="flex-1 flex items-center justify-between p-3.5 rounded-xl bg-muted/20 hover:bg-muted/40 border border-border/80 hover:border-accent/50 transition-all text-left group cursor-pointer shadow-2xs"

              >

                <div className="flex items-center gap-3 min-w-0">

                  <div className="w-10 h-10 rounded-xl bg-accent/15 text-accent flex items-center justify-center font-mono text-xs font-bold shrink-0 border border-accent/25 group-hover:scale-105 transition-transform">

                    <BookOpen className="w-4 h-4 text-accent" />

                  </div>

                  <div className="space-y-0.5 min-w-0">

                    <div className="flex items-center gap-2 flex-wrap">

                      <span className="font-bold text-foreground text-sm sm:text-base group-hover:text-accent transition-colors truncate">

                        {currentCourse.canonicalCode ? `[${currentCourse.canonicalCode}] ` : ""}

                        {currentCourse.name}

                      </span>

                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-accent/10 border border-accent/20 text-accent font-semibold shrink-0">

                        Semester {selectedSemester}

                      </span>

                    </div>

                    <p className="text-xs text-muted-foreground truncate">

                      {selectedBranch} • <span className="text-accent/90 font-medium">Click to change branch or course</span>

                    </p>

                  </div>

                </div>

                

                <div className="flex items-center gap-1.5 pl-3 text-xs font-semibold text-muted-foreground group-hover:text-accent shrink-0">

                  <span className="hidden sm:inline">Change Course</span>

                  <ChevronRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />

                </div>

              </button>

            ) : (

              <button

                type="button"

                onClick={() => {

                  setCourseSearchQuery("");

                  setIsCourseModalOpen(true);

                }}

                className="flex-1 flex items-center justify-between p-4 rounded-xl bg-accent/5 hover:bg-accent/10 border-2 border-dashed border-accent/40 hover:border-accent transition-all text-left group cursor-pointer shadow-xs"

              >

                <div className="flex items-center gap-3.5 min-w-0">

                  <div className="w-10 h-10 rounded-xl bg-accent/20 text-accent flex items-center justify-center font-mono text-xs font-bold shrink-0 border border-accent/30 group-hover:scale-105 transition-transform">

                    <Sparkles className="w-5 h-5 text-accent animate-pulse" />

                  </div>

                  <div className="space-y-0.5 min-w-0">

                    <div className="flex items-center gap-2">

                      <span className="font-bold text-foreground text-base group-hover:text-accent transition-colors">

                        Select Your Course to Begin

                      </span>

                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-accent/15 border border-accent/30 text-accent font-bold uppercase tracking-wider">

                        Input Required

                      </span>

                    </div>

                    <p className="text-xs text-muted-foreground">

                      Choose your branch and semester or search any of our 43 engineering subjects

                    </p>

                  </div>

                </div>



                <div className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-accent text-accent-foreground text-xs font-bold shadow-xs shrink-0">

                  <span>Choose Course</span>

                  <ChevronRight className="w-3.5 h-3.5" />

                </div>

              </button>

            )}



            {/* Assessment Cycle Selector */}

            <div className="grid grid-cols-3 rounded-xl border border-border p-1 bg-muted/20 text-xs shrink-0 self-center">

              {[

                { key: "ENDSEM", label: "EndSem" },

                { key: "CT1", label: "CT1" },

                { key: "CT2", label: "CT2" }

              ].map((cycle) => (

                <button

                  key={cycle.key}

                  type="button"

                  onClick={() => handleCycleChange(cycle.key)}

                  className={`py-2 px-3 rounded-lg text-xs font-medium transition-all cursor-pointer ${

                    selectedCycle === cycle.key

                      ? "bg-accent text-accent-foreground font-semibold shadow-2xs"

                      : "text-muted-foreground hover:text-foreground"

                  }`}

                >

                  {cycle.label}

                </button>

              ))}

            </div>

          </div>

        </div>

        {/* 1.5 EXAM SCOPE & SYLLABUS UNITS SELECTOR */}
        {currentCourse && (
          <ExamUnitSelector
            course={currentCourse}
            selectedUnits={selectedUnits}
            onChangeUnits={handleUnitsChange}
            activeCycle={selectedCycle}
            onCycleChange={handleCycleChange}
            inScopeTopicCount={filteredForecastItems.length}
            totalTopicCount={allForecastItems.length}
          />
        )}

        {/* TARGETED UNIT PRACTICE & HELP ACTION CARD */}
        {currentCourse && (
          <div className="p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-accent/5 via-card to-background border border-accent/20 shadow-xs flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-accent" />
                <h4 className="text-sm font-bold text-foreground">
                  Exam Help: {selectedUnits.length === (currentCourse.units?.length || 5) ? "Full Syllabus Preparation" : `Focused Preparation for Units ${selectedUnits.join(", ")}`}
                </h4>
              </div>
              <p className="text-xs text-muted-foreground">
                {filteredForecastItems.length > 0 
                  ? `${filteredForecastItems.length} high-yield topics & repeat questions identified for your selected exam units.`
                  : `Generating syllabus questions and practice tests for Units ${selectedUnits.join(", ")}.`}
              </p>
            </div>

            <div className="flex items-center gap-2 flex-wrap shrink-0">
              {filteredForecastItems.length > 0 && (
                <button
                  type="button"
                  onClick={() => {
                    const firstItem = filteredForecastItems[0];
                    setActivePracticeTopic(firstItem);
                    setDrawerActiveTab("pyq");
                  }}
                  className="px-4 py-2 rounded-xl bg-accent text-accent-foreground text-xs font-bold hover:bg-accent/90 transition-all flex items-center gap-1.5 shadow-2xs cursor-pointer"
                >
                  <FileCheck2 className="w-3.5 h-3.5" />
                  <span>Practice In-Scope Topics</span>
                </button>
              )}

              <Link
                href={`/question-bank?course=${currentCourse.id}&units=${selectedUnits.join(",")}`}
                className="px-3.5 py-2 rounded-xl bg-secondary hover:bg-secondary/80 border border-border text-xs font-semibold text-foreground transition-all flex items-center gap-1.5 shadow-2xs"
              >
                <Search className="w-3.5 h-3.5 text-muted-foreground" />
                <span>Question Bank ({selectedUnits.length} Units)</span>
              </Link>
            </div>
          </div>
        )}

        {/* PRIMARY COURSE SELECTION MODAL CARD */}

        <AnimatePresence>

          {isCourseModalOpen && (

            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">

              {/* Backdrop */}

              <motion.div

                initial={{ opacity: 0 }}

                animate={{ opacity: 1 }}

                exit={{ opacity: 0 }}

                onClick={() => {

                  if (selectedCourseId) setIsCourseModalOpen(false);

                }}

                className="fixed inset-0 bg-background/80 backdrop-blur-sm"

              />



              {/* Modal Dialog Card */}

              <motion.div

                initial={{ opacity: 0, scale: 0.95, y: 10 }}

                animate={{ opacity: 1, scale: 1, y: 0 }}

                exit={{ opacity: 0, scale: 0.95, y: 10 }}

                transition={{ type: "spring", damping: 25, stiffness: 250 }}

                className="relative w-full max-w-2xl bg-card border border-border/80 rounded-2xl shadow-2xl overflow-hidden z-10 flex flex-col max-h-[88vh]"

                onClick={(e) => e.stopPropagation()}

              >

                {/* Header */}

                <div className="p-5 sm:p-6 border-b border-border/60 bg-card shrink-0 flex items-start justify-between gap-4">

                  <div className="space-y-1">

                    <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-accent/10 border border-accent/20 text-[11px] font-semibold text-accent uppercase tracking-wider">

                      Academic Setup

                    </div>

                    <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">

                      What are you preparing for?

                    </h2>

                    <p className="text-xs sm:text-sm text-muted-foreground">

                      Select your branch and semester or instantly search any of our 43 engineering subjects.

                    </p>

                  </div>



                  {selectedCourseId && (

                    <button

                      type="button"

                      onClick={() => setIsCourseModalOpen(false)}

                      className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-xl transition-colors shrink-0 cursor-pointer"

                      aria-label="Close dialog"

                    >

                      <X className="w-5 h-5" />

                    </button>

                  )}

                </div>



                {/* Modal Body */}

                <div className="p-5 sm:p-6 overflow-y-auto space-y-5">

                  {/* Instant Search Bar */}

                  <div className="relative">

                    <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" />

                    <input

                      type="text"

                      value={courseSearchQuery}

                      onChange={(e) => setCourseSearchQuery(e.target.value)}

                      placeholder="Instant search 43 courses (e.g. Data Structures, 18CSC201J, Physics)..."

                      className="w-full bg-muted/20 border border-border rounded-xl pl-10 pr-10 py-2.5 text-sm placeholder:text-muted-foreground text-foreground focus:ring-1 focus:ring-accent focus:outline-none transition-all"

                      autoFocus

                    />

                    {courseSearchQuery && (

                      <button

                        type="button"

                        onClick={() => setCourseSearchQuery("")}

                        className="absolute right-3.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground p-1"

                        aria-label="Clear search"

                      >

                        <X className="w-4 h-4" />

                      </button>

                    )}

                  </div>



                  {/* If Searching: Display Instant Search Results */}

                  {courseSearchQuery.trim() ? (

                    <div className="space-y-2">

                      <div className="text-xs font-semibold text-muted-foreground flex items-center justify-between">

                        <span>{searchedCourses.length} courses matching &ldquo;{courseSearchQuery}&rdquo;</span>

                        <span className="text-[10px] font-mono">Click course to select</span>

                      </div>

                      <div className="max-h-72 overflow-y-auto space-y-1.5 pr-1">

                        {searchedCourses.length === 0 ? (

                          <div className="p-8 text-center text-xs text-muted-foreground bg-muted/10 rounded-xl border border-dashed border-border/80">

                            No engineering courses matching &ldquo;{courseSearchQuery}&rdquo;

                          </div>

                        ) : (

                          searchedCourses.map((c) => {

                            const isSelected = c.id === selectedCourseId;

                            return (

                              <button

                                key={c.id}

                                type="button"

                                onClick={() => handleCourseSwitch(c.id)}

                                className={`w-full p-3 rounded-xl text-left text-xs flex items-center justify-between border transition-all cursor-pointer ${

                                  isSelected

                                    ? "bg-accent/15 border-accent text-foreground font-bold shadow-2xs"

                                    : "bg-muted/15 border-border/60 hover:bg-muted/30 hover:border-accent/40 text-foreground"

                                }`}

                              >

                                <div className="space-y-0.5">

                                  <div className="flex items-center gap-2">

                                    <span className="font-mono text-accent font-semibold">[{c.canonicalCode || c.code}]</span>

                                    <span className="font-medium text-foreground">{c.name}</span>

                                  </div>

                                </div>

                                <div className="flex items-center gap-2 shrink-0">

                                  <span className="text-muted-foreground font-mono text-[11px]">

                                    {c.paperCount} exams

                                  </span>

                                  {isSelected && <Check className="w-4 h-4 text-accent" />}

                                </div>

                              </button>

                            );

                          })

                        )}

                      </div>

                    </div>

                  ) : (

                    /* If Not Searching: Branch -> Semester -> Subject Flow */

                    <div className="space-y-5">

                      {/* Branch Selector */}

                      <div className="space-y-2">

                        <label className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground block">

                          1. Select Branch / Specialization

                        </label>

                        <div className="relative">

                          <select

                            value={selectedBranch}

                            onChange={(e) => handleBranchChange(e.target.value)}

                            className="w-full bg-background border border-border rounded-xl px-3.5 py-2.5 text-sm font-medium text-foreground focus:ring-1 focus:ring-accent focus:outline-none shadow-2xs appearance-none pr-10 cursor-pointer"

                          >

                            {branches.map((b) => (

                              <option key={b} value={b}>

                                {b}

                              </option>

                            ))}

                          </select>

                          <ChevronDown className="w-4 h-4 text-muted-foreground absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />

                        </div>

                      </div>



                      {/* Semester Pills (1 - 8) */}

                      <div className="space-y-2">

                        <label className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground block">

                          2. Select Semester

                        </label>

                        <div className="grid grid-cols-4 sm:grid-cols-8 gap-1.5">

                          {semesters.map((s) => (

                            <button

                              key={s}

                              type="button"

                              onClick={() => handleSemesterChange(s)}

                              className={`py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer ${

                                selectedSemester === s

                                  ? "bg-accent text-accent-foreground shadow-2xs"

                                  : "bg-muted/20 border border-border/60 text-muted-foreground hover:text-foreground hover:bg-muted/40"

                              }`}

                            >

                              Sem {s}

                            </button>

                          ))}

                        </div>

                      </div>



                      {/* Available Subjects for this Branch & Semester */}

                      <div className="space-y-2">

                        <label className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground block">

                          3. Select Course ({semesterSubjects.length > 0 ? `${semesterSubjects.length} subjects in Semester ${selectedSemester}` : "Available Courses"})

                        </label>

                        <div className="max-h-60 overflow-y-auto space-y-1.5 pr-1">

                          {(semesterSubjects.length > 0 ? semesterSubjects : eligibleCourses).map((item: any) => {

                            const courseId = item.course_id || item.id;

                            const courseName = item.subject_name || item.name;

                            const courseCode = item.canonical_code || item.canonicalCode || item.code;

                            const isSelected = courseId === selectedCourseId;

                            const hasExams = item.has_exams !== undefined ? item.has_exams : (item.paperCount > 0);



                            return (

                              <button

                                key={courseId}

                                type="button"

                                onClick={() => handleCourseSwitch(courseId)}

                                className={`w-full p-3 rounded-xl text-left text-xs flex items-center justify-between border transition-all cursor-pointer ${

                                  isSelected

                                    ? "bg-accent/15 border-accent text-foreground font-bold shadow-2xs"

                                    : "bg-muted/15 border-border/60 hover:bg-muted/30 hover:border-accent/40 text-foreground"

                                }`}

                              >

                                <div className="space-y-0.5">

                                  <div className="flex items-center gap-2">

                                    {courseCode && (

                                      <span className="font-mono text-accent font-semibold">[{courseCode}]</span>

                                    )}

                                    <span className="font-medium text-foreground">{courseName}</span>

                                  </div>

                                  {!hasExams && (

                                    <span className="text-[10px] text-amber-500 font-medium block">

                                      Awaiting past exam papers

                                    </span>

                                  )}

                                </div>

                                <div className="flex items-center gap-2 shrink-0">

                                  {isSelected && <Check className="w-4 h-4 text-accent" />}

                                </div>

                              </button>

                            );

                          })}

                        </div>

                      </div>

                    </div>

                  )}

                </div>



                {/* Modal Footer */}

                <div className="p-4 border-t border-border/60 bg-muted/10 shrink-0 flex items-center justify-between text-xs text-muted-foreground">

                  <span>SRMIST Verified Curriculum</span>

                  {selectedCourseId && (

                    <button

                      type="button"

                      onClick={() => setIsCourseModalOpen(false)}

                      className="px-4 py-2 rounded-xl bg-foreground text-background font-semibold hover:bg-foreground/90 transition-all cursor-pointer shadow-xs"

                    >

                      Close

                    </button>

                  )}

                </div>

              </motion.div>

            </div>

          )}

        </AnimatePresence>



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

                {currentCourse ? (

                  <>

                    High-yield topics and recurring question signals calibrated from verified past papers for <strong className="text-foreground">{currentCourse.name}</strong> ({cycleDisplayLabel}).

                  </>

                ) : (

                  "Select a course to view calibrated topics, probability scores, and recurring question families."

                )}

              </p>

              {currentCourse && selectedCycle !== "ALL" && predictionsData?.assessment_scope?.component_code === "ALL" && (

                <div className="flex items-center gap-2 p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-600 dark:text-amber-400 mt-2">

                  <Info className="w-4 h-4 shrink-0" />

                  <span>

                    <strong>Assessment Scope Notice:</strong> Trained on comprehensive course history due to limited {cycleDisplayLabel} paper archive.

                  </span>

                </div>

              )}

            </div>



            {currentCourse && (

              <div className="flex flex-wrap items-center gap-2 self-start sm:self-auto">

                {/* Filter pills: All | Topics | Questions */}

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

            )}

          </div>



          {/* Forecast Items / Selection Prompt */}

          {!currentCourse ? (

            <div className="p-10 md:p-14 text-center rounded-2xl border-2 border-dashed border-border/70 bg-muted/5 space-y-4">

              <div className="w-14 h-14 rounded-2xl bg-accent/10 border border-accent/20 text-accent flex items-center justify-center mx-auto shadow-inner">

                <BookOpen className="w-7 h-7 text-accent" />

              </div>

              <div className="space-y-1.5 max-w-md mx-auto">

                <h3 className="text-lg font-bold text-foreground">

                  Choose Your Course

                </h3>

                <p className="text-xs text-muted-foreground leading-relaxed">

                  Select your engineering department and semester to generate calibrated topic recurrence, recurring question families, and exam intelligence.

                </p>

              </div>

              <button

                type="button"

                onClick={() => {

                  setCourseSearchQuery("");

                  setIsCourseModalOpen(true);

                }}

                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-foreground text-background text-xs font-bold hover:bg-foreground/90 transition-all cursor-pointer shadow-md"

              >

                <Sparkles className="w-4 h-4 text-accent" />

                <span>Select Course & Branch</span>

              </button>

            </div>

          ) : isLoadingIntelligence ? (

            <div className="py-12 flex flex-col items-center justify-center gap-3 text-muted-foreground">

              <Loader2 className="w-6 h-6 animate-spin text-accent" />

              <span className="text-xs font-medium">Calibrating historical exam predictions for {currentCourse.name}...</span>

            </div>

          ) : displayedForecastItems.length === 0 ? (

            <div className="p-8 text-center rounded-xl bg-muted/10 border border-border/60 space-y-4">

              <div className="space-y-1.5">

                <p className="text-sm font-semibold text-foreground">

                  {currentCourse.paperCount === 0 

                    ? "Historical Exam Papers Ingestion Pending" 

                    : "No specific forecast signals found for this filter."}

                </p>

                <p className="text-xs text-muted-foreground max-w-md mx-auto">

                  {currentCourse.paperCount === 0

                    ? `Historical PYQs for ${currentCourse.name} are currently awaiting moderation. You can practice syllabus questions below.`

                    : "Try selecting \u201cAll Signals\u201d or changing the assessment cycle."}

                </p>

              </div>

              <div className="max-w-md mx-auto pt-2">

                <MintAIQuestionGenerator topicName={currentCourse.name} courseId={currentCourse.id} cycle={selectedCycle} />

              </div>

            </div>

          ) : (

            <div className="space-y-4">

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">

                {displayedForecastItems.map((item: any, idx: number) => {

                  return (

                    <div

                      key={item.name || idx}

                      className="p-4 rounded-xl bg-background border border-border/80 hover:border-accent/40 transition-all flex flex-col justify-between gap-3 shadow-2xs group"

                    >

                      <div className="space-y-2">

                        {/* Header: Rank + Calibrated Probability + Repeat Badge */}

                        <div className="flex items-center justify-between gap-2">

                          <span className="inline-flex items-center justify-center w-6 h-6 rounded-md bg-accent/15 text-accent font-mono text-xs font-bold shrink-0">

                            #{item.rank || idx + 1}

                          </span>



                          <div className="flex items-center gap-1.5 flex-wrap justify-end">
                            {item.unitNumber && (
                              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-accent/10 text-accent border border-accent/20">
                                Unit {item.unitNumber}
                              </span>
                            )}

                            {item.isFamily && (

                              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground border border-border">

                                {item.repetition_type === "EXACT" ? "Exact Repeat Family" : "Recurring Family"}

                              </span>

                            )}

                            {item.probability != null && (

                              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border font-mono ${

                                item.probability >= 70

                                  ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"

                                  : "bg-accent/10 text-accent border-accent/20"

                              }`}>

                                {item.probability}% Calibrated P

                              </span>

                            )}

                          </div>

                        </div>



                        {/* Title / Question text with LaTeX MathText Rendering */}

                        <div>

                          <div className="text-sm font-bold text-foreground group-hover:text-accent transition-colors line-clamp-2">

                            <MathText content={item.name} inlineOnly />

                          </div>

                          {item.explanation && (

                            <p className="text-xs text-muted-foreground pt-1 line-clamp-2">

                              {cleanExplanation(item.explanation)}

                            </p>

                          )}

                        </div>

                      </div>



                      {/* Evidence Proof Line & Action Button */}

                      <div className="pt-2 border-t border-border/40 flex items-center justify-between gap-2">

                        <span className="text-[11px] text-muted-foreground font-mono truncate">

                          {item.papersWithItem && item.totalPapers

                            ? `${item.papersWithItem}/${item.totalPapers} papers (${Math.round((item.paperCoverage || 0) * 100)}%)`

                            : `${item.historicalOccurrences} occurrences`}

                        </span>



                        <button

                          type="button"

                          onClick={() => {

                            setActivePracticeTopic(item);

                            setDrawerActiveTab("pyq");

                          }}

                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent/10 hover:bg-accent/20 text-accent font-semibold text-xs border border-accent/20 transition-all cursor-pointer shrink-0"

                        >

                          <Sparkles className="w-3.5 h-3.5" />

                          <span>Practice</span>

                        </button>

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

              {/* EMPIRICAL MODEL EVALUATION & EVIDENCE (MintAI Forecast Lab) */}
              <div className="mt-8 pt-6 border-t border-border/60 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center text-accent">
                      <ShieldCheck className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-bold text-foreground">Empirical Historical Backtest Validation</h3>
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-muted text-muted-foreground border border-border/50">
                          v2.1.0-lab
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Rigorous rolling-origin backtesting: predictions verified against held-out exams with zero future data leakage.
                      </p>
                    </div>
                  </div>

                  {/* Sufficiency Status Badge */}
                  <div className="flex items-center gap-2 self-start sm:self-auto">
                    {isLoadingPerformance ? (
                      <div className="flex items-center gap-1.5 text-xs text-muted-foreground animate-pulse">
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        <span>Validating...</span>
                      </div>
                    ) : modelPerformance?.evidence_sufficiency === "SUFFICIENT_HISTORY" ? (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                        Statistically Sufficient History
                      </span>
                    ) : modelPerformance?.evidence_sufficiency === "LIMITED_HISTORY" ? (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                        Limited Historical Archive
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
                        <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                        Insufficient Historical Sample
                      </span>
                    )}
                  </div>
                </div>

                {/* Benchmark Cards or Abstention Notice */}
                {modelPerformance?.candidate && modelPerformance?.target_exams_evaluated > 0 ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <div className="p-3 rounded-xl bg-card border border-border/80 shadow-2xs space-y-1">
                        <div className="text-[11px] font-medium text-muted-foreground flex items-center justify-between">
                          <span>Held-Out Precision@5</span>
                          <span className="text-[10px] text-accent font-semibold">Top 5</span>
                        </div>
                        <div className="text-xl md:text-2xl font-bold text-foreground">
                          {(modelPerformance.candidate.precision_at_5 * 100).toFixed(1)}%
                        </div>
                        <div className="text-[10px] text-muted-foreground leading-tight">
                          Tested against unobserved past papers
                        </div>
                      </div>

                      <div className="p-3 rounded-xl bg-card border border-border/80 shadow-2xs space-y-1">
                        <div className="text-[11px] font-medium text-muted-foreground flex items-center justify-between">
                          <span>Ranking Quality (NDCG@5)</span>
                          <span className="text-[10px] text-muted-foreground">IR Score</span>
                        </div>
                        <div className="text-xl md:text-2xl font-bold text-foreground">
                          {modelPerformance.candidate.ndcg_at_5?.toFixed(3) || "0.000"}
                        </div>
                        <div className="text-[10px] text-muted-foreground leading-tight">
                          Position-weighted relevance accuracy
                        </div>
                      </div>

                      <div className="p-3 rounded-xl bg-card border border-border/80 shadow-2xs space-y-1">
                        <div className="text-[11px] font-medium text-muted-foreground flex items-center justify-between">
                          <span>Exam Marks Coverage</span>
                          <span className="text-[10px] text-muted-foreground">Syllabus</span>
                        </div>
                        <div className="text-xl md:text-2xl font-bold text-foreground">
                          {(modelPerformance.candidate.marks_coverage_at_5 * 100).toFixed(1)}%
                        </div>
                        <div className="text-[10px] text-muted-foreground leading-tight">
                          Proportion of test paper marks accounted
                        </div>
                      </div>

                      <div className="p-3 rounded-xl bg-card border border-border/80 shadow-2xs space-y-1">
                        <div className="text-[11px] font-medium text-muted-foreground flex items-center justify-between">
                          <span>Evaluated Target Exams</span>
                          <span className="text-[10px] text-muted-foreground">Historical</span>
                        </div>
                        <div className="text-xl md:text-2xl font-bold text-foreground">
                          {modelPerformance.target_exams_evaluated}
                        </div>
                        <div className="text-[10px] text-muted-foreground leading-tight">
                          Chronologically isolated test exams
                        </div>
                      </div>
                    </div>

                    {/* Baseline Comparison Pill & Methodology Guardrail */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 rounded-xl bg-muted/40 border border-border/60 text-xs">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-foreground">Model Comparison:</span>
                        {modelPerformance.recency_baseline ? (
                          <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-semibold">
                            <Check className="w-3.5 h-3.5" />
                            {((modelPerformance.candidate.precision_at_5 - modelPerformance.recency_baseline.precision_at_5) * 100).toFixed(1)}% vs simple recency baseline ({(modelPerformance.recency_baseline.precision_at_5 * 100).toFixed(1)}%)
                          </span>
                        ) : (
                          <span className="text-muted-foreground">Benchmark verified across multiple syllabus cycles.</span>
                        )}
                      </div>
                      <div className="text-[11px] text-muted-foreground">
                        Temporal Rule: Strict $Year &lt; T$ isolation. Zero future paper leakage.
                      </div>
                    </div>
                  </div>
                ) : (
                  /* Honest Abstention Callout */
                  <div className="p-3.5 rounded-xl bg-muted/30 border border-border text-xs text-muted-foreground space-y-1">
                    <div className="flex items-center gap-2 font-semibold text-foreground">
                      <Info className="w-4 h-4 text-amber-500 shrink-0" />
                      <span>Honest Abstention: Historical Archive Guardrail</span>
                    </div>
                    <p className="text-[11px] leading-relaxed">
                      This subject has fewer than 2 dated historical papers in the archive prior to the target exam.
                      In accordance with MarkMint Forecast Lab protocols, aggregate accuracy percentages are deliberately
                      withheld to avoid misleading extrapolations until additional verified papers are archived.
                    </p>
                  </div>
                )}
              </div>

        </section>



        {/* 3. SLIDE-OVER PRACTICE DRAWER */}

        <Drawer

          isOpen={!!activePracticeTopic}

          onClose={() => setActivePracticeTopic(null)}

          title={

            <div className="flex items-center gap-2">

              {activePracticeTopic?.rank && (

                <span className="inline-flex items-center justify-center px-2 py-0.5 rounded-md bg-accent/15 text-accent font-mono text-xs font-bold shrink-0">

                  #{activePracticeTopic.rank}

                </span>

              )}

              <div className="line-clamp-2">

                <MathText content={activePracticeTopic?.name || ""} inlineOnly />

              </div>

            </div>

          }

          subtitle={

            <div className="flex items-center gap-2 text-xs text-muted-foreground pt-1 flex-wrap">

              <span>{currentCourse?.name}</span>

              <span>•</span>

              <span>{cycleDisplayLabel}</span>

              {activePracticeTopic?.probability != null && (

                <>

                  <span>•</span>

                  <span className="font-semibold text-emerald-600 dark:text-emerald-400 font-mono">

                    {activePracticeTopic.probability}% Calibrated P

                  </span>

                </>

              )}

            </div>

          }

        >

          {currentCourse && (

            <div className="space-y-5">

              {/* Drawer Tabs: Authentic PYQs vs AI Practice Generator */}

              <div className="grid grid-cols-2 rounded-lg border border-border p-1 bg-muted/20 text-xs">

                <button

                  type="button"

                  onClick={() => setDrawerActiveTab("pyq")}

                  className={`py-2 px-3 rounded-md text-xs font-semibold transition-all flex items-center justify-center gap-2 cursor-pointer ${

                    drawerActiveTab === "pyq"

                      ? "bg-accent text-accent-foreground shadow-2xs"

                      : "text-muted-foreground hover:text-foreground"

                  }`}

                >

                  <FileText className="w-3.5 h-3.5" />

                  <span>Past Exam Questions</span>

                </button>

                <button

                  type="button"

                  onClick={() => setDrawerActiveTab("ai")}

                  className={`py-2 px-3 rounded-md text-xs font-semibold transition-all flex items-center justify-center gap-2 cursor-pointer ${

                    drawerActiveTab === "ai"

                      ? "bg-accent text-accent-foreground shadow-2xs"

                      : "text-muted-foreground hover:text-foreground"

                  }`}

                >

                  <Sparkles className="w-3.5 h-3.5" />

                  <span>AI Practice Questions</span>

                </button>

              </div>



              {/* Drawer Content Body */}

              {drawerActiveTab === "pyq" ? (

                <TopicQuestionsViewer

                  topicName={activePracticeTopic?.name || ""}

                  courseId={currentCourse.id}

                  courseCode={currentCourse.canonicalCode || currentCourse.code}

                />

              ) : (

                <div className="space-y-4">

                  <div className="p-3.5 rounded-xl bg-accent/5 border border-accent/20 text-xs text-muted-foreground">

                    MintAI generates 1-mark, 4-mark, and 13-mark practice problems aligned strictly with the exam structure of <strong className="text-foreground">{currentCourse.name}</strong>.

                  </div>

                  <MintAIQuestionGenerator

                    topicName={activePracticeTopic?.name || ""}

                    courseId={currentCourse.id}

                    cycle={selectedCycle}

                  />

                </div>

              )}

            </div>

          )}

        </Drawer>



        {/* 4. Minimal Institutional Scope Notice */}

        <div className="p-3.5 rounded-xl bg-muted/10 border border-border/40 text-xs text-muted-foreground flex items-center gap-2.5">

          <ShieldCheck className="w-4 h-4 text-accent shrink-0" />

          <p className="text-[11px] leading-relaxed">

            MintAI derives intelligence signals strictly from verified past examination papers and official SRMIST syllabus documents. Distinguishes documented historical facts from predictive signals without speculation.

          </p>

        </div>

      </main>



      <Footer />

    </div>

  );

}

