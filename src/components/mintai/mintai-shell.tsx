"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { CourseSelectorModal } from "@/components/mintai/course-selector-modal";
import { MintAIOverviewTab } from "@/components/mintai/tabs/mintai-overview-tab";
import { MintAIExamDNATab } from "@/components/mintai/tabs/mintai-exam-dna-tab";
import { MintAIPracticeTab } from "@/components/mintai/tabs/mintai-practice-tab";
import { MintAIStudyTab } from "@/components/mintai/tabs/mintai-study-tab";
import { coursesCatalog, CourseCatalogItem } from "@/lib/courses";
import { getStudyContext, updateStudyContext } from "@/lib/study-context";
import {
  getCurriculumBranches,
  getCurriculumSemesters,
  getCurriculumSubjects,
  findCurriculumSubjectByCourseId,
  getPredictions,
  getExamDNA,
  getExamAnnouncementsForCourse,
  ExamAnnouncementItem,
} from "@/lib/api";
import { CurriculumSubject, ExamDNA } from "@/lib/types";
import {
  Sparkles,
  Dna,
  FileCheck2,
  BookOpen,
  ChevronRight,
  ChevronDown,
  Layers,
  Users,
  Check,
  RotateCcw,
  ShieldCheck,
} from "lucide-react";

export type MintAITab = "overview" | "dna" | "practice" | "study";

export function MintAIShell() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Eligible courses with archived past papers
  const eligibleCourses = useMemo(() => {
    return coursesCatalog.filter((c) => c.paperCount > 0);
  }, []);

  // Academic Cascade States
  const [branches, setBranches] = useState<string[]>([]);
  const [selectedBranch, setSelectedBranch] = useState<string>("Computer Science and Engineering");
  const [semesters, setSemesters] = useState<number[]>([1, 2, 3, 4, 5, 6, 7, 8]);
  const [selectedSemester, setSelectedSemester] = useState<number>(1);
  const [semesterSubjects, setSemesterSubjects] = useState<CurriculumSubject[]>([]);

  // Core Active States
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);
  const [selectedCycle, setSelectedCycle] = useState<string>("ENDSEM");
  const [selectedUnits, setSelectedUnits] = useState<number[]>([1, 2, 3, 4, 5]);
  const [activeTab, setActiveTab] = useState<MintAITab>("overview");
  const [isCourseModalOpen, setIsCourseModalOpen] = useState<boolean>(false);

  // Predictions & Intelligence States
  const [predictionsData, setPredictionsData] = useState<any>(null);
  const [dnaData, setDnaData] = useState<ExamDNA | null>(null);
  const [isLoadingIntelligence, setIsLoadingIntelligence] = useState<boolean>(false);
  const [forecastFilter, setForecastFilter] = useState<"ALL" | "TOPIC" | "FAMILY">("ALL");
  const [showAllSignals, setShowAllSignals] = useState<boolean>(false);
  const [classAnnouncements, setClassAnnouncements] = useState<ExamAnnouncementItem[]>([]);

  // 1. Resolve Active Course Object
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
        units: [],
      } as unknown as CourseCatalogItem;
    }
    return null;
  }, [eligibleCourses, semesterSubjects, selectedCourseId, selectedSemester]);

  // 2. Sync URL parameters helper
  const updateUrlParams = useCallback(
    (newCourseId: number | null, newCycle: string, newTab: MintAITab, newUnits: number[]) => {
      const params = new URLSearchParams(window.location.search);

      if (newCourseId) {
        params.set("course", String(newCourseId));
        params.delete("course_id");
      }
      if (newCycle && newCycle !== "ALL") {
        params.set("cycle", newCycle);
      } else {
        params.delete("cycle");
      }
      if (newTab && newTab !== "overview") {
        params.set("tab", newTab);
      } else {
        params.delete("tab");
      }

      // Check if custom units differ from standard cycle default
      const defaultUnits =
        newCycle === "CT1" ? [1, 2] : newCycle === "CT2" ? [3, 4] : [1, 2, 3, 4, 5];
      const isCustomUnits =
        newUnits.length !== defaultUnits.length ||
        !newUnits.every((u) => defaultUnits.includes(u));

      if (isCustomUnits && newUnits.length > 0 && newUnits.length < 5) {
        params.set("units", newUnits.join(","));
      } else {
        params.delete("units");
      }

      const queryString = params.toString();
      const newUrl = queryString ? `/mintai?${queryString}` : "/mintai";
      if (typeof window !== "undefined") {
        window.history.pushState(null, "", newUrl);
      }
      router.replace(newUrl, { scroll: false });
    },
    [router]
  );

  // 3. Initial Load from URL and StudyContext
  useEffect(() => {
    let isMounted = true;

    async function initAcademicContext() {
      try {
        const branchList = await getCurriculumBranches();
        if (!isMounted) return;
        setBranches(branchList);

        const ctx = getStudyContext();
        const urlParams = new URLSearchParams(window.location.search);

        const targetCourseParam =
          urlParams.get("course") ||
          urlParams.get("course_id") ||
          (ctx?.course_id ? String(ctx.course_id) : null);

        const targetCycleParam =
          urlParams.get("cycle") ||
          urlParams.get("assessment_cycle") ||
          ctx?.assessment_cycle ||
          "ENDSEM";

        const targetTabParam = urlParams.get("tab") as MintAITab | null;
        if (targetTabParam && ["overview", "dna", "practice", "study"].includes(targetTabParam)) {
          setActiveTab(targetTabParam);
        } else {
          setActiveTab("overview");
        }

        let resolvedCycle = "ENDSEM";
        if (targetCycleParam && ["ALL", "ENDSEM", "CT1", "CT2"].includes(targetCycleParam.toUpperCase())) {
          resolvedCycle = targetCycleParam.toUpperCase();
        }
        setSelectedCycle(resolvedCycle);

        const unitsParam = urlParams.get("units");
        if (unitsParam) {
          const parsed = unitsParam.split(",").map(Number).filter((n) => !isNaN(n) && n > 0);
          if (parsed.length > 0) setSelectedUnits(parsed);
        } else if (resolvedCycle === "CT1") {
          setSelectedUnits([1, 2]);
        } else if (resolvedCycle === "CT2") {
          setSelectedUnits([3, 4]);
        } else {
          setSelectedUnits([1, 2, 3, 4, 5]);
        }

        let initialBranch = ctx?.branch || "Computer Science and Engineering";
        let initialSemester = ctx?.semester || 1;

        if (targetCourseParam) {
          const numId = Number(targetCourseParam);
          const found = !isNaN(numId) ? findCurriculumSubjectByCourseId(numId) : null;
          if (found) {
            initialBranch = found.branch;
            initialSemester = found.semester;
            setSelectedCourseId(found.subject.course_id || numId);
          } else {
            const matchedCatalog = eligibleCourses.find(
              (c) =>
                String(c.id) === targetCourseParam ||
                c.code.toLowerCase() === targetCourseParam.toLowerCase() ||
                c.canonicalCode.toLowerCase() === targetCourseParam.toLowerCase() ||
                c.slug.toLowerCase() === targetCourseParam.toLowerCase()
            );
            if (matchedCatalog) {
              setSelectedCourseId(matchedCatalog.id);
            }
          }
        } else {
          // Default to first eligible course (Calculus) for instant preview
          setSelectedCourseId(eligibleCourses[0]?.id || 1);
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
        console.error("Failed to initialize MintAI context:", err);
      }
    }

    initAcademicContext();

    return () => {
      isMounted = false;
    };
  }, [eligibleCourses]);

  // Listen for browser Back/Forward navigation to sync tabs and filters
  useEffect(() => {
    const handlePopState = () => {
      const urlParams = new URLSearchParams(window.location.search);
      const targetTab = urlParams.get("tab") as MintAITab | null;
      if (targetTab && ["overview", "dna", "practice", "study"].includes(targetTab)) {
        setActiveTab(targetTab);
      } else {
        setActiveTab("overview");
      }

      const targetCycle = urlParams.get("cycle");
      if (targetCycle && ["ALL", "ENDSEM", "CT1", "CT2"].includes(targetCycle.toUpperCase())) {
        setSelectedCycle(targetCycle.toUpperCase());
      }

      const targetCourse = urlParams.get("course") || urlParams.get("course_id");
      if (targetCourse) {
        const numId = Number(targetCourse);
        if (!isNaN(numId)) {
          setSelectedCourseId(numId);
        }
      }

      const unitsParam = urlParams.get("units");
      if (unitsParam) {
        const parsed = unitsParam.split(",").map(Number).filter((n) => !isNaN(n) && n > 0);
        if (parsed.length > 0) setSelectedUnits(parsed);
      }
    };

    window.addEventListener("popstate", handlePopState);
    return () => {
      window.removeEventListener("popstate", handlePopState);
    };
  }, []);

  // 4. Fetch Intelligence & Announcements on Course or Cycle change
  const fetchIntelligence = useCallback(async (courseId: number, cycle: string) => {
    setIsLoadingIntelligence(true);
    try {
      const [preds, dna, ann] = await Promise.all([
        getPredictions(courseId, cycle),
        getExamDNA(courseId, cycle),
        getExamAnnouncementsForCourse(courseId).catch(() => []),
      ]);
      setPredictionsData(preds);
      setDnaData(dna);
      setClassAnnouncements(ann || []);
    } catch (err) {
      console.error("Failed to fetch MintAI intelligence:", err);
    } finally {
      setIsLoadingIntelligence(false);
    }
  }, []);

  useEffect(() => {
    if (selectedCourseId) {
      fetchIntelligence(selectedCourseId, selectedCycle);
    }
  }, [selectedCourseId, selectedCycle, fetchIntelligence]);

  // 5. Interactive Handlers
  const handleSelectCourse = (courseId: number) => {
    setSelectedCourseId(courseId);
    setShowAllSignals(false);
    const targetCourse = eligibleCourses.find((c) => c.id === courseId);
    if (targetCourse) {
      updateStudyContext({
        branch: selectedBranch,
        semester: selectedSemester,
        course_id: targetCourse.id,
        course_name: targetCourse.name,
        course_code: targetCourse.canonicalCode || targetCourse.code,
        assessment_cycle: selectedCycle,
      });
    }
    updateUrlParams(courseId, selectedCycle, activeTab, selectedUnits);
  };

  const handleSelectCycle = (cycle: string) => {
    setSelectedCycle(cycle);
    setShowAllSignals(false);
    let nextUnits = [1, 2, 3, 4, 5];
    if (cycle === "CT1") nextUnits = [1, 2];
    else if (cycle === "CT2") nextUnits = [3, 4];
    setSelectedUnits(nextUnits);

    if (currentCourse) {
      updateStudyContext({
        course_id: currentCourse.id,
        course_name: currentCourse.name,
        course_code: currentCourse.canonicalCode || currentCourse.code,
        assessment_cycle: cycle,
      });
    }
    updateUrlParams(selectedCourseId, cycle, activeTab, nextUnits);
  };

  const handleTabChange = (tab: MintAITab) => {
    setActiveTab(tab);
    updateUrlParams(selectedCourseId, selectedCycle, tab, selectedUnits);
  };

  const toggleUnit = (unitNum: number) => {
    let nextUnits: number[];
    if (selectedUnits.includes(unitNum)) {
      if (selectedUnits.length === 1) return; // Keep at least 1 unit
      nextUnits = selectedUnits.filter((u) => u !== unitNum).sort();
    } else {
      nextUnits = [...selectedUnits, unitNum].sort();
    }
    setSelectedUnits(nextUnits);
    updateUrlParams(selectedCourseId, selectedCycle, activeTab, nextUnits);
  };

  // 6. Topic Unit Helper
  const getTopicUnit = useCallback(
    (topicName: string): number => {
      if (!topicName || !currentCourse) return 1;
      const lower = topicName.toLowerCase().trim();
      if (currentCourse.units && currentCourse.units.length > 0) {
        for (const u of currentCourse.units) {
          if (
            u.topics &&
            u.topics.some((t) => {
              const tLower = t.toLowerCase().trim();
              return tLower === lower || lower.includes(tLower) || tLower.includes(lower);
            })
          ) {
            return u.number;
          }
        }
      }
      if (currentCourse.highYieldTopics && currentCourse.highYieldTopics.length > 0) {
        const match = currentCourse.highYieldTopics.find((h) => {
          const hLower = h.topic.toLowerCase().trim();
          return hLower === lower || lower.includes(hLower) || hLower.includes(lower);
        });
        if (match && match.unitNumber) return match.unitNumber;
      }
      let hash = 0;
      for (let i = 0; i < lower.length; i++) {
        hash = (hash << 5) - hash + lower.charCodeAt(i);
        hash |= 0;
      }
      const totalUnits = currentCourse.units?.length || 5;
      return (Math.abs(hash) % totalUnits) + 1;
    },
    [currentCourse]
  );

  // 7. Structured Forecast Items
  const allForecastItems = useMemo(() => {
    if (!currentCourse) return [];
    if (
      predictionsData?.predictions &&
      Array.isArray(predictionsData.predictions) &&
      predictionsData.predictions.length > 0
    ) {
      return predictionsData.predictions.map((p: any, idx: number) => {
        const isFamily = p.family_id != null || (p.repetition_type && p.repetition_type !== "NONE");
        const papersWithItem =
          p.papers_with_family ||
          p.papers_with_topic ||
          p.papers_with_item ||
          p.distinct_paper_count ||
          p.historyCount ||
          1;
        const totalPapers =
          p.papers_analyzed || dnaData?.sample_size?.papers || currentCourse.paperCount || 1;
        const coverageRatio =
          p.paper_coverage != null
            ? p.paper_coverage
            : totalPapers > 0
            ? papersWithItem / totalPapers
            : 0.5;
        const calibratedProb =
          p.probability != null
            ? Math.round(p.probability * 100)
            : p.score != null
            ? Math.round(p.score * 100)
            : null;

        const unitNumber = getTopicUnit(p.name);
        const unitObj = currentCourse?.units?.find((u) => u.number === unitNumber);
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
          totalMarksObserved:
            p.total_marks_observed != null ? Math.round(p.total_marks_observed) : null,
          explanation:
            p.explanation ||
            (isFamily
              ? `Exact verbatim repeat family observed across historical examination papers.`
              : `Consistently tested syllabus area with documented examination frequency.`),
        };
      });
    }

    // Fallback from catalog
    return (currentCourse.highYieldTopics || []).map((hyt, idx) => {
      const unitNumber = hyt.unitNumber || getTopicUnit(hyt.topic);
      const unitObj = currentCourse?.units?.find((u) => u.number === unitNumber);
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
        explanation: `Documented across ${hyt.paperCount} historical examination papers.`,
      };
    });
  }, [predictionsData, dnaData, currentCourse, getTopicUnit]);

  // Filtered Forecast items by units and signal filter
  const filteredForecastItems = useMemo(() => {
    let items = allForecastItems;
    if (selectedUnits.length > 0 && selectedUnits.length < (currentCourse?.units?.length || 5)) {
      items = items.filter((item: any) => selectedUnits.includes(item.unitNumber));
    }
    if (forecastFilter === "TOPIC") {
      return items.filter((item: any) => !item.isFamily);
    }
    if (forecastFilter === "FAMILY") {
      return items.filter((item: any) => item.isFamily);
    }
    return items;
  }, [allForecastItems, selectedUnits, currentCourse, forecastFilter]);

  const displayedForecastItems = useMemo(() => {
    if (showAllSignals) return filteredForecastItems;
    return filteredForecastItems.slice(0, 4);
  }, [filteredForecastItems, showAllSignals]);

  // Active classmate announcement
  const activeAnnouncement = classAnnouncements.find(
    (a) =>
      a.exam_type.toUpperCase() === selectedCycle.toUpperCase() ||
      (selectedCycle === "ALL" && a.exam_type)
  );

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground font-sans">
      <Navbar />

      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 md:px-10 py-6 space-y-6">
        {/* Breadcrumb Navigation */}
        <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-xs text-muted-foreground">
          <Link href="/" className="hover:text-foreground transition-colors">
            Home
          </Link>
          <ChevronRight className="w-3.5 h-3.5" />
          <span className="text-foreground font-medium">MintAI Intelligence</span>
          {currentCourse && (
            <>
              <ChevronRight className="w-3.5 h-3.5" />
              <span className="text-muted-foreground truncate max-w-[200px]">{currentCourse.name}</span>
            </>
          )}
        </nav>

        {/* ========================================================================= */}
        {/* PERSISTENT MINTAI CONTROL HEADER                                          */}
        {/* ========================================================================= */}
        <section className="p-4 sm:p-5 rounded-2xl bg-card border border-border/80 shadow-xs space-y-4">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            {/* Left: Active Course Trigger Button */}
            <div className="space-y-1">
              <span className="text-[10px] font-bold tracking-widest text-muted-foreground uppercase">
                Active Course
              </span>
              <button
                type="button"
                onClick={() => setIsCourseModalOpen(true)}
                className="flex items-center gap-2.5 text-left group cursor-pointer"
              >
                <div className="w-9 h-9 rounded-xl bg-accent/15 border border-accent/25 text-accent flex items-center justify-center font-bold text-sm shrink-0 group-hover:scale-105 transition-transform">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h1 className="text-base sm:text-lg font-bold text-foreground group-hover:text-accent transition-colors leading-tight">
                      {currentCourse ? currentCourse.name : "Select Engineering Course"}
                    </h1>
                    <ChevronDown className="w-4 h-4 text-muted-foreground group-hover:text-foreground transition-colors" />
                  </div>
                  <div className="text-[11px] text-muted-foreground flex items-center gap-2 pt-0.5 font-mono">
                    {currentCourse?.canonicalCode && (
                      <span className="font-semibold text-accent">{currentCourse.canonicalCode}</span>
                    )}
                    {currentCourse && <span>•</span>}
                    <span>{currentCourse ? `${currentCourse.paperCount} verified papers` : "Click to choose course"}</span>
                  </div>
                </div>
              </button>
            </div>

            {/* Right: Assessment Cycle Switcher */}
            <div className="space-y-1 lg:text-right">
              <span className="text-[10px] font-bold tracking-widest text-muted-foreground uppercase">
                Assessment Cycle
              </span>
              <div className="flex items-center gap-1.5 p-1 rounded-xl bg-muted/20 border border-border/60 text-xs font-semibold overflow-x-auto no-scrollbar">
                {[
                  { id: "CT1", label: "CT1 (Units 1-2)" },
                  { id: "CT2", label: "CT2 (Units 3-4)" },
                  { id: "ENDSEM", label: "End Semester (1-5)" },
                  { id: "ALL", label: "All Cycles" },
                ].map((cycle) => (
                  <button
                    key={cycle.id}
                    type="button"
                    onClick={() => handleSelectCycle(cycle.id)}
                    className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer whitespace-nowrap ${
                      selectedCycle === cycle.id
                        ? "bg-accent text-accent-foreground font-bold shadow-2xs"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {cycle.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Unit Scoping Chips & Classmate Alert Line */}
          <div className="pt-3 border-t border-border/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-[11px] font-semibold text-muted-foreground mr-1">Portion Units:</span>
              {[1, 2, 3, 4, 5].map((u) => {
                const isSelected = selectedUnits.includes(u);
                return (
                  <button
                    key={u}
                    type="button"
                    onClick={() => toggleUnit(u)}
                    className={`px-2.5 py-1 rounded-lg text-[11px] font-mono font-bold transition-all cursor-pointer flex items-center gap-1 ${
                      isSelected
                        ? "bg-accent/15 border border-accent/30 text-accent shadow-2xs"
                        : "bg-muted/15 border border-border/40 text-muted-foreground hover:text-foreground opacity-60 hover:opacity-100"
                    }`}
                  >
                    <span>Unit {u}</span>
                    {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                  </button>
                );
              })}
            </div>

            {activeAnnouncement && (
              <div className="flex items-center gap-1.5 text-accent font-medium text-[11px] bg-accent/5 px-2.5 py-1 rounded-lg border border-accent/20">
                <Users className="w-3.5 h-3.5 shrink-0" />
                <span>
                  Classmate Alert: {activeAnnouncement.exam_title || activeAnnouncement.exam_type} reported on Units{" "}
                  {activeAnnouncement.units.join(", ")}
                </span>
              </div>
            )}
          </div>
        </section>

        {/* ========================================================================= */}
        {/* UNIFIED 4-SECTION TAB NAVIGATION BAR                                      */}
        {/* ========================================================================= */}
        <div className="sticky top-16 z-40 bg-background/95 backdrop-blur-md pt-2 pb-1 border-b border-border/60">
          <div className="flex items-center gap-2 overflow-x-auto no-scrollbar py-1">
            {[
              {
                id: "overview" as MintAITab,
                label: "Overview",
                icon: Sparkles,
                badge: `${filteredForecastItems.length} Predictions`,
              },
              {
                id: "dna" as MintAITab,
                label: "Exam DNA",
                icon: Dna,
                badge: "Analytics",
              },
              {
                id: "practice" as MintAITab,
                label: "Practice",
                icon: FileCheck2,
                badge: "CTs & MCQs",
              },
              {
                id: "study" as MintAITab,
                label: "Study",
                icon: BookOpen,
                badge: "Dr. E Suresh",
              },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  data-tab={tab.id}
                  data-testid={`mintai-tab-${tab.id}`}
                  onClick={() => handleTabChange(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap shrink-0 min-h-[44px] ${
                    isActive
                      ? "bg-foreground text-background shadow-xs font-extrabold"
                      : "bg-card hover:bg-muted/40 text-muted-foreground hover:text-foreground border border-border/70"
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? "text-accent" : "text-muted-foreground"}`} />
                  <span>{tab.label}</span>
                  <span
                    className={`px-1.5 py-0.2 rounded-md text-[10px] font-mono ${
                      isActive
                        ? "bg-background/20 text-background font-bold"
                        : "bg-muted/40 text-muted-foreground"
                    }`}
                  >
                    {tab.badge}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* ========================================================================= */}
        {/* ACTIVE SECTION CONTENT BODY                                               */}
        {/* ========================================================================= */}
        <section className="pt-2">
          {activeTab === "overview" && (
            <MintAIOverviewTab
              currentCourse={currentCourse}
              selectedCycle={selectedCycle}
              selectedUnits={selectedUnits}
              displayedForecastItems={displayedForecastItems}
              filteredForecastItems={filteredForecastItems}
              forecastFilter={forecastFilter}
              setForecastFilter={setForecastFilter}
              showAllSignals={showAllSignals}
              setShowAllSignals={setShowAllSignals}
              isLoadingIntelligence={isLoadingIntelligence}
              onSwitchTab={handleTabChange}
              onOpenCourseModal={() => setIsCourseModalOpen(true)}
            />
          )}

          {activeTab === "dna" && (
            <MintAIExamDNATab
              currentCourse={currentCourse}
              selectedCycle={selectedCycle}
            />
          )}

          {activeTab === "practice" && (
            <MintAIPracticeTab
              currentCourse={currentCourse}
              selectedCycle={selectedCycle}
              selectedUnits={selectedUnits}
            />
          )}

          {activeTab === "study" && (
            <MintAIStudyTab
              currentCourse={currentCourse}
              selectedCycle={selectedCycle}
              selectedUnits={selectedUnits}
            />
          )}
        </section>
      </main>

      <Footer />

      {/* Unified Course Selection Modal */}
      <CourseSelectorModal
        isOpen={isCourseModalOpen}
        onClose={() => setIsCourseModalOpen(false)}
        selectedCourseId={selectedCourseId}
        onSelectCourse={handleSelectCourse}
        branches={branches}
        selectedBranch={selectedBranch}
        onBranchChange={async (branch) => {
          setSelectedBranch(branch);
          const sems = await getCurriculumSemesters(branch);
          setSemesters(sems);
          const nextSem = sems.includes(selectedSemester) ? selectedSemester : sems[0] || 1;
          setSelectedSemester(nextSem);
          const subs = await getCurriculumSubjects(branch, nextSem);
          setSemesterSubjects(subs);
        }}
        semesters={semesters}
        selectedSemester={selectedSemester}
        onSemesterChange={async (sem) => {
          setSelectedSemester(sem);
          const subs = await getCurriculumSubjects(selectedBranch, sem);
          setSemesterSubjects(subs);
        }}
        semesterSubjects={semesterSubjects}
        eligibleCourses={eligibleCourses}
      />
    </div>
  );
}
