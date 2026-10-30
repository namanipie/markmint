"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import {
  FileText,
  Layers,
  CheckSquare,
  Clock,
  Sparkles,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  Eye,
  EyeOff,
  Award,
  BookOpen,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  HelpCircle,
  Printer,
  Calendar,
  ExternalLink,
  Zap,
  Activity
} from "lucide-react";
import { MathText } from "@/components/ui/math-text";
import { cleanQuestionText } from "@/lib/utils";
import {
  getHistoricalQuestions,
  getCycleTestQuestions,
  CycleTestQuestion
} from "@/lib/api";
import { HistoricalQuestion } from "@/lib/types";
import { CourseCatalogItem } from "@/lib/courses";
import { McqTestingSuite } from "@/components/practice/mcq-testing-suite";
import { MintAIQuestionGenerator } from "@/components/ui/mint-ai-question-generator";

export type PracticeDestination = "pyqs" | "ct_archives" | "mcqs" | "quiz" | "generator";

interface MintAIPracticeTabProps {
  currentCourse: CourseCatalogItem | null;
  selectedCycle: string;
  selectedUnits?: number[];
}

export function MintAIPracticeTab({
  currentCourse,
  selectedCycle,
  selectedUnits
}: MintAIPracticeTabProps) {
  // 1. Destination Navigation State (defaulting to PYQs or URL query)
  const [activeDestination, setActiveDestination] = useState<PracticeDestination>("pyqs");

  // Sync destination with URL query parameter `dest` or `mode` on mount
  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const destParam = (params.get("dest") || params.get("mode")) as PracticeDestination | null;
    if (destParam && ["pyqs", "ct_archives", "mcqs", "quiz", "generator"].includes(destParam)) {
      setActiveDestination(destParam);
    }
  }, []);

  const handleSelectDestination = (dest: PracticeDestination) => {
    setActiveDestination(dest);
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      params.set("tab", "practice");
      params.set("dest", dest);
      params.delete("mode");
      const newUrl = `/mintai?${params.toString()}`;
      window.history.replaceState(null, "", newUrl);
    }
  };

  // 2. Filter States (Unit, Cycle, Marks, Search)
  const [filterUnit, setFilterUnit] = useState<string>("ALL");
  const [filterCycle, setFilterCycle] = useState<string>(selectedCycle || "ALL");
  const [filterMarks, setFilterMarks] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Keep cycle filter in sync with MintAI shell header
  useEffect(() => {
    if (selectedCycle) {
      setFilterCycle(selectedCycle);
    }
  }, [selectedCycle]);

  // If parent shell selects specific units (e.g. CT1 -> units 1, 2), sync initial unit filter
  useEffect(() => {
    if (selectedUnits && selectedUnits.length === 2 && selectedUnits[0] === 1) {
      // e.g. CT1 defaults
    }
  }, [selectedUnits]);

  // 3. Previous Year Questions (PYQs) Data State
  const [pyqs, setPyqs] = useState<HistoricalQuestion[]>([]);
  const [isLoadingPyqs, setIsLoadingPyqs] = useState<boolean>(false);
  const [revealedPyqSolutions, setRevealedPyqSolutions] = useState<Record<number, boolean>>({});
  const [practicedPyqIds, setPracticedPyqIds] = useState<Record<number, boolean>>({});

  // 4. Cycle Test Archive Data State
  const [ctQuestions, setCtQuestions] = useState<CycleTestQuestion[]>([]);
  const [isLoadingCt, setIsLoadingCt] = useState<boolean>(false);
  const [ctPartFilter, setCtPartFilter] = useState<string>("ALL");
  const [revealedCtAnswers, setRevealedCtAnswers] = useState<Record<number, boolean>>({});

  // 5. AI Question Generator State
  const [selectedTopicForAi, setSelectedTopicForAi] = useState<string>("");

  // Fetch PYQs for Course
  useEffect(() => {
    if (!currentCourse) return;
    let active = true;
    setIsLoadingPyqs(true);

    // Fetch up to 30 past questions for fast response
    getHistoricalQuestions(
      currentCourse.id,
      undefined,
      filterCycle !== "ALL" ? filterCycle : undefined,
      30
    )
      .then((res) => {
        if (!active) return;
        setPyqs(res.questions || []);
      })
      .catch((err) => {
        console.warn("Failed to load historical questions:", err);
      })
      .finally(() => {
        if (active) setIsLoadingPyqs(false);
      });

    return () => {
      active = false;
    };
  }, [currentCourse, filterCycle]);

  // Fetch Cycle Test Questions for Course
  useEffect(() => {
    if (!currentCourse) return;
    let active = true;
    setIsLoadingCt(true);

    // Cycle tests are CT1 and CT2; for ENDSEM or ALL, fetch all available CTs
    const ctCycleParam = (filterCycle === "CT1" || filterCycle === "CT2") ? filterCycle : undefined;

    getCycleTestQuestions(
      currentCourse.name,
      ctCycleParam,
      100,
      "all"
    )
      .then((res) => {
        if (!active) return;
        setCtQuestions(res.questions || []);
      })
      .catch((err) => {
        console.warn("Failed to load CT questions:", err);
      })
      .finally(() => {
        if (active) setIsLoadingCt(false);
      });

    return () => {
      active = false;
    };
  }, [currentCourse, filterCycle]);

  // Separate CT questions into Descriptive and MCQs
  const ctDescriptiveQuestions = useMemo(() => {
    return ctQuestions.filter((q) => {
      if (q.is_mcq || q.q_type === "MCQ") return false;
      if (q.options && q.options.length >= 2) return false;
      return true;
    });
  }, [ctQuestions]);

  const ctMcqQuestions = useMemo(() => {
    return ctQuestions.filter((q) => {
      if (q.is_mcq || q.q_type === "MCQ") return true;
      if (q.options && q.options.length >= 2) return true;
      const txt = q.question_text || "";
      return /(?:^|[\n\s])(?:\([A-Da-d]\)|\[[A-Da-d]\]|[A-Da-d][\.\)])\s*[\s\S]+?(?:\([B-Db-d]\)|\[[B-Db-d]\]|[B-Db-d][\.\)])/.test(txt);
    });
  }, [ctQuestions]);

  // Unit Resolver Helper for PYQs
  const getQuestionUnit = useCallback(
    (q: HistoricalQuestion): number => {
      const topicList = Array.isArray(q.topics)
        ? q.topics
        : (typeof q.topics === "string" ? [q.topics] : []);
      if (topicList.length > 0 && currentCourse?.units) {
        for (const t of topicList) {
          const tLower = t.toLowerCase().trim();
          for (const u of currentCourse.units) {
            if (u.topics?.some((topic) => topic.toLowerCase().includes(tLower) || tLower.includes(topic.toLowerCase()))) {
              return u.number;
            }
          }
        }
      }
      // Deterministic hash fallback
      let hash = 0;
      const str = q.original_text || "";
      for (let i = 0; i < str.length; i++) {
        hash = (hash << 5) - hash + str.charCodeAt(i);
        hash |= 0;
      }
      return (Math.abs(hash) % 5) + 1;
    },
    [currentCourse]
  );

  // Filtered PYQs based on active search, unit, and marks
  const filteredPyqs = useMemo(() => {
    return pyqs.filter((q) => {
      // 1. Search Query
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase().trim();
        const textMatch = (q.original_text || "").toLowerCase().includes(query);
        const docMatch = (q.source_document_title || "").toLowerCase().includes(query);
        const familyMatch = (q.family_name || "").toLowerCase().includes(query);
        if (!textMatch && !docMatch && !familyMatch) return false;
      }
      // 2. Unit Filter
      if (filterUnit !== "ALL") {
        const uNum = Number(filterUnit);
        if (!isNaN(uNum) && getQuestionUnit(q) !== uNum) return false;
      }
      // 3. Marks Filter
      if (filterMarks !== "ALL") {
        const mNum = Number(filterMarks);
        if (!isNaN(mNum)) {
          const qm = q.marks || 0;
          if (mNum === 2 && qm > 2) return false;
          if (mNum === 5 && (qm < 4 || qm > 8)) return false;
          if (mNum === 10 && (qm < 9 || qm > 12)) return false;
          if (mNum === 15 && qm < 13) return false;
        }
      }
      return true;
    });
  }, [pyqs, searchQuery, filterUnit, filterMarks, getQuestionUnit]);

  // Filtered CT Descriptive Questions
  const filteredCtDescriptive = useMemo(() => {
    return ctDescriptiveQuestions.filter((q) => {
      // 1. Search Query
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase().trim();
        const textMatch = (q.question_text || "").toLowerCase().includes(query);
        const topicMatch = (q.topic || "").toLowerCase().includes(query);
        if (!textMatch && !topicMatch) return false;
      }
      // 2. Part Filter (Part A: 2m, Part B: 5/10m, Part C)
      if (ctPartFilter !== "ALL") {
        if (ctPartFilter === "PART_A" && (q.marks > 3 || (q.section && q.section.toUpperCase().includes("PART B")))) return false;
        if (ctPartFilter === "PART_B" && (q.marks <= 3 || (q.section && q.section.toUpperCase().includes("PART A")))) return false;
      }
      // 3. Unit Filter
      if (filterUnit !== "ALL") {
        const uNum = Number(filterUnit);
        if (!isNaN(uNum) && q.unit !== uNum) return false;
      }
      return true;
    });
  }, [ctDescriptiveQuestions, searchQuery, ctPartFilter, filterUnit]);

  // Available topics for AI generator dropdown
  const availableTopics = useMemo(() => {
    if (!currentCourse) return [];
    const set = new Set<string>();
    if (currentCourse.units) {
      currentCourse.units.forEach((u) => {
        u.topics?.forEach((t) => set.add(t));
      });
    }
    if (currentCourse.highYieldTopics) {
      currentCourse.highYieldTopics.forEach((h) => set.add(h.topic));
    }
    return Array.from(set);
  }, [currentCourse]);

  if (!currentCourse) {
    return (
      <div className="p-8 text-center rounded-2xl border border-dashed border-border/80 bg-card/40 space-y-2">
        <Sparkles className="w-8 h-8 text-muted-foreground mx-auto" />
        <p className="text-sm font-semibold text-foreground">Select an engineering course to begin practice</p>
        <p className="text-xs text-muted-foreground">Access verified past exam papers, cycle test archives, instant MCQs, and timed simulations.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ========================================================================= */}
      {/* PRACTICE HUB CONTROL HEADER                                               */}
      {/* ========================================================================= */}
      <div className="p-5 rounded-2xl bg-card border border-border/80 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border/50 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-accent/10 text-accent">
                <CheckSquare className="w-5 h-5" />
              </span>
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                Practice &amp; Question Solving Hub
              </h2>
            </div>
            <p className="text-xs text-muted-foreground">
              Consolidated testing center for <strong className="text-foreground">{currentCourse.name}</strong>. Practice authentic SRM questions, cycle tests, interactive MCQs, timed test runs, and AI problems.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto font-mono text-xs">
            <span className="px-2.5 py-1 rounded-lg bg-accent/10 text-accent border border-accent/20 font-bold">
              {pyqs.length} PYQs
            </span>
            <span className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
              {ctMcqQuestions.length} MCQs
            </span>
          </div>
        </div>

        {/* 5-Destination Navigation Tabs */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-1">
          {[
            {
              id: "pyqs" as PracticeDestination,
              label: "PYQs (Past Papers)",
              icon: FileText,
              badge: `${pyqs.length} Qs`,
            },
            {
              id: "ct_archives" as PracticeDestination,
              label: "CT Archives",
              icon: Layers,
              badge: `${ctDescriptiveQuestions.length} Normal`,
            },
            {
              id: "mcqs" as PracticeDestination,
              label: "Interactive MCQs",
              icon: CheckSquare,
              badge: `${ctMcqQuestions.length} Active`,
            },
            {
              id: "quiz" as PracticeDestination,
              label: "Timed Tests",
              icon: Clock,
              badge: "Simulation",
            },
            {
              id: "generator" as PracticeDestination,
              label: "AI Generator",
              icon: Sparkles,
              badge: "Unseen",
            },
          ].map((dest) => {
            const Icon = dest.icon;
            const isActive = activeDestination === dest.id;
            return (
              <button
                key={dest.id}
                type="button"
                data-dest={dest.id}
                onClick={() => handleSelectDestination(dest.id)}
                className={`flex flex-col sm:flex-row items-center justify-between gap-1.5 p-3 rounded-xl border text-left transition-all cursor-pointer ${
                  isActive
                    ? "bg-foreground text-background shadow-xs font-bold border-foreground"
                    : "bg-muted/20 hover:bg-muted/40 text-muted-foreground hover:text-foreground border-border/70"
                }`}
              >
                <div className="flex items-center gap-2">
                  <Icon className={`w-4 h-4 ${isActive ? "text-accent" : "text-muted-foreground"}`} />
                  <span className="text-xs font-semibold">{dest.label}</span>
                </div>
                <span
                  className={`text-[10px] font-mono px-1.5 py-0.2 rounded ${
                    isActive ? "bg-background/20 text-background font-bold" : "bg-muted text-muted-foreground"
                  }`}
                >
                  {dest.badge}
                </span>
              </button>
            );
          })}
        </div>

        {/* Universal Filter & Search Bar */}
        <div className="pt-3 border-t border-border/50 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-semibold text-muted-foreground mr-1">Portion Unit:</span>
            {["ALL", "1", "2", "3", "4", "5"].map((u) => {
              const isSelected = filterUnit === u;
              return (
                <button
                  key={u}
                  type="button"
                  onClick={() => setFilterUnit(u)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                    isSelected
                      ? "bg-accent text-accent-foreground font-bold shadow-2xs"
                      : "bg-muted/30 border border-border/60 text-muted-foreground hover:text-foreground hover:bg-muted/50"
                  }`}
                >
                  {u === "ALL" ? "All Units" : `Unit ${u}`}
                </button>
              );
            })}
          </div>

          <div className="flex items-center gap-2 flex-1 max-w-sm">
            <div className="relative w-full">
              <Search className="w-3.5 h-3.5 text-muted-foreground absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search questions or topics..."
                className="w-full bg-background border border-border/70 rounded-lg pl-8 pr-3 py-1.5 text-xs focus:ring-1 focus:ring-accent focus:outline-none"
              />
            </div>
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                className="text-muted-foreground hover:text-foreground text-[11px] underline shrink-0 cursor-pointer"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* DESTINATION 1: PREVIOUS YEAR QUESTIONS (PYQS)                             */}
      {/* ========================================================================= */}
      {activeDestination === "pyqs" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs px-1">
            <span className="text-muted-foreground">
              Showing <strong>{filteredPyqs.length}</strong> verified past examination questions for {currentCourse.name}
            </span>
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-muted-foreground">Filter Marks:</span>
              <select
                value={filterMarks}
                onChange={(e) => setFilterMarks(e.target.value)}
                className="bg-background border border-border rounded px-2 py-1 text-xs focus:ring-1 focus:ring-accent"
              >
                <option value="ALL">All Marks</option>
                <option value="2">2-Mark (Short)</option>
                <option value="5">5-Mark</option>
                <option value="10">10-Mark</option>
                <option value="15">15-Mark (Long)</option>
              </select>
            </div>
          </div>

          {isLoadingPyqs ? (
            <div className="py-16 text-center text-xs text-muted-foreground flex items-center justify-center gap-2">
              <Activity className="w-4 h-4 animate-spin text-accent" />
              <span>Fetching verified examination questions...</span>
            </div>
          ) : filteredPyqs.length === 0 ? (
            <div className="p-8 text-center rounded-2xl border border-dashed border-border/80 bg-card/40 space-y-2">
              <FileText className="w-8 h-8 text-muted-foreground mx-auto" />
              <p className="text-sm font-semibold text-foreground">No questions match your current filter</p>
              <p className="text-xs text-muted-foreground">Try clearing search terms or selecting &ldquo;All Units&rdquo;.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredPyqs.map((q, idx) => {
                const uNum = getQuestionUnit(q);
                const isPracticed = Boolean(practicedPyqIds[q.id]);
                const isSolutionRevealed = Boolean(revealedPyqSolutions[q.id]);

                return (
                  <div
                    key={q.id || idx}
                    className={`p-4 sm:p-5 rounded-2xl border transition-all ${
                      isPracticed
                        ? "bg-card/40 border-emerald-500/30"
                        : "bg-card border-border/80 hover:border-accent/40 shadow-xs"
                    }`}
                  >
                    {/* Header Badges */}
                    <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-border/40 text-xs">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="px-2 py-0.5 rounded-md font-mono font-bold bg-muted text-foreground text-[10px]">
                          Q#{q.question_number || idx + 1}
                        </span>
                        <span className="px-2 py-0.5 rounded-md font-mono text-[10px] bg-accent/10 text-accent font-semibold">
                          Unit {uNum}
                        </span>
                        <span className="px-2 py-0.5 rounded-md font-mono text-[10px] bg-secondary text-secondary-foreground font-semibold">
                          {q.year || "Past Exam"} {q.assessment_type || "Semester"}
                        </span>
                        {q.repetition_type && (
                          <span className="px-2 py-0.5 rounded-md font-mono text-[10px] bg-purple-500/10 text-purple-400 font-semibold border border-purple-500/20">
                            {q.repetition_type.replace(/_/g, " ")}
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-2">
                        <span className="px-2.5 py-0.5 rounded-full bg-accent/15 text-accent font-bold font-mono text-xs">
                          {q.marks || 10} Marks
                        </span>
                        <button
                          type="button"
                          onClick={() => setPracticedPyqIds((prev) => ({ ...prev, [q.id]: !prev[q.id] }))}
                          className={`p-1.5 rounded-lg border transition-colors cursor-pointer ${
                            isPracticed
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                              : "bg-muted/30 text-muted-foreground border-border/60 hover:text-foreground"
                          }`}
                          title={isPracticed ? "Practiced" : "Mark as Practiced"}
                        >
                          <CheckCircle2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    {/* Question Formulation */}
                    <div className="py-3 text-xs sm:text-sm text-foreground leading-relaxed">
                      <MathText content={cleanQuestionText(q.original_text)} />
                    </div>

                    {/* Footer: Citation & Guidance Toggle */}
                    <div className="pt-2.5 border-t border-border/40 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[11px] text-muted-foreground">
                      <div className="flex items-center gap-1.5 font-mono">
                        <FileText className="w-3.5 h-3.5 text-accent shrink-0" />
                        <span className="truncate max-w-[280px] sm:max-w-md">
                          {q.source_document_title || `${currentCourse.name} Verified Examination Paper`}
                        </span>
                      </div>

                      <button
                        type="button"
                        onClick={() => setRevealedPyqSolutions((prev) => ({ ...prev, [q.id]: !prev[q.id] }))}
                        className="inline-flex items-center gap-1 font-semibold text-accent hover:underline cursor-pointer self-start sm:self-auto"
                      >
                        {isSolutionRevealed ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                        <span>{isSolutionRevealed ? "Hide Solution Guidance" : "View Solution Rubric"}</span>
                      </button>
                    </div>

                    {/* Expandable Solution / Rubric */}
                    {isSolutionRevealed && (
                      <div className="mt-3 p-3.5 rounded-xl bg-muted/20 border border-border/60 text-xs space-y-1.5 animate-in fade-in-50 duration-150">
                        <div className="font-semibold text-foreground flex items-center gap-1.5">
                          <Award className="w-3.5 h-3.5 text-accent" />
                          <span>Official Mark Rubric &amp; Solution Strategy</span>
                        </div>
                        <p className="text-muted-foreground leading-relaxed">
                          For full credit ({q.marks || 10} marks): State the core theorem/definition (20%), execute complete intermediate algebraic or differential derivations (50%), and calculate exact final numerical/symbolic form with appropriate units (30%).
                        </p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* DESTINATION 2: CYCLE TEST DESCRIPTIVE ARCHIVE                             */}
      {/* ========================================================================= */}
      {activeDestination === "ct_archives" && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-xl bg-muted/20 border border-border/60 text-xs">
            <div>
              <span className="font-semibold text-foreground">Cycle Test Descriptive Archive</span>
              <p className="text-[11px] text-muted-foreground">
                Authentic normal questions from {currentCourse.name} CT1 &amp; CT2 papers with faculty marking keys.
              </p>
            </div>

            <div className="flex items-center gap-1.5">
              <span className="text-[11px] text-muted-foreground">Section Part:</span>
              <select
                value={ctPartFilter}
                onChange={(e) => setCtPartFilter(e.target.value)}
                className="bg-background border border-border rounded px-2 py-1 text-xs focus:ring-1 focus:ring-accent"
              >
                <option value="ALL">All Parts</option>
                <option value="PART_A">Part A (Short Answer)</option>
                <option value="PART_B">Part B (Long Analytical)</option>
              </select>
            </div>
          </div>

          {isLoadingCt ? (
            <div className="py-16 text-center text-xs text-muted-foreground flex items-center justify-center gap-2">
              <Activity className="w-4 h-4 animate-spin text-accent" />
              <span>Fetching cycle test archives...</span>
            </div>
          ) : filteredCtDescriptive.length === 0 ? (
            <div className="p-8 text-center rounded-2xl border border-dashed border-border/80 bg-card/40 space-y-2">
              <Layers className="w-8 h-8 text-muted-foreground mx-auto" />
              <p className="text-sm font-semibold text-foreground">No descriptive cycle test questions found</p>
              <p className="text-xs text-muted-foreground">Check the &ldquo;Interactive MCQs&rdquo; tab or select another assessment cycle.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredCtDescriptive.map((q, idx) => {
                const isAnswerRevealed = Boolean(revealedCtAnswers[idx]);
                return (
                  <div
                    key={idx}
                    className="p-4 sm:p-5 rounded-2xl bg-card border border-border/80 hover:border-accent/40 shadow-xs space-y-3 transition-all"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-border/40 text-xs">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded font-mono font-bold bg-accent/15 text-accent text-[10px]">
                          {q.cycle || "CT"} Q#{q.q_num || idx + 1}
                        </span>
                        {q.section && (
                          <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-muted text-muted-foreground">
                            {q.section}
                          </span>
                        )}
                        {q.unit && (
                          <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-secondary text-secondary-foreground">
                            Unit {q.unit}
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-2">
                        <span className="px-2.5 py-0.5 rounded-full bg-accent/15 text-accent font-bold font-mono text-xs">
                          {q.marks || 4} Marks
                        </span>
                      </div>
                    </div>

                    <div className="py-2 text-xs sm:text-sm text-foreground leading-relaxed">
                      <MathText content={cleanQuestionText(q.question_text)} />
                    </div>

                    <div className="pt-2 border-t border-border/40 flex items-center justify-between text-[11px] text-muted-foreground">
                      <span className="font-mono truncate max-w-[260px]">
                        {q.source_file || `${q.cycle} Examination Paper`}
                      </span>

                      {q.answer_key && (
                        <button
                          type="button"
                          onClick={() => setRevealedCtAnswers((prev) => ({ ...prev, [idx]: !prev[idx] }))}
                          className="inline-flex items-center gap-1 font-semibold text-accent hover:underline cursor-pointer"
                        >
                          {isAnswerRevealed ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                          <span>{isAnswerRevealed ? "Hide Answer Key" : "Show Faculty Answer Key"}</span>
                        </button>
                      )}
                    </div>

                    {isAnswerRevealed && q.answer_key && (
                      <div className="p-3.5 rounded-xl bg-muted/20 border border-border/60 text-xs space-y-1.5 animate-in fade-in-50 duration-150">
                        <div className="font-semibold text-foreground flex items-center gap-1.5">
                          <CheckCircle2 className="w-3.5 h-3.5 text-accent" />
                          <span>Official Faculty Solution &amp; Answer Key</span>
                        </div>
                        <div className="text-muted-foreground leading-relaxed">
                          <MathText content={q.answer_key} />
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* DESTINATION 3: INTERACTIVE MCQ PRACTICE                                   */}
      {/* ========================================================================= */}
      {activeDestination === "mcqs" && (
        <div className="space-y-4">
          {ctMcqQuestions.length === 0 ? (
            <div className="p-8 text-center rounded-2xl border border-dashed border-border/80 bg-card/40 space-y-2">
              <CheckSquare className="w-8 h-8 text-muted-foreground mx-auto" />
              <p className="text-sm font-semibold text-foreground">No MCQs available for this cycle</p>
              <p className="text-xs text-muted-foreground">Select another assessment cycle (e.g. &ldquo;All Cycles&rdquo;) to practice MCQs.</p>
            </div>
          ) : (
            <McqTestingSuite
              questions={ctMcqQuestions}
              subjectName={currentCourse.name}
              cycle={filterCycle}
              initialMode="PRACTICE"
            />
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* DESTINATION 4: TIMED EXAMINATION TESTS                                    */}
      {/* ========================================================================= */}
      {activeDestination === "quiz" && (
        <div className="space-y-4">
          {ctMcqQuestions.length === 0 ? (
            <div className="p-8 text-center rounded-2xl border border-dashed border-border/80 bg-card/40 space-y-2">
              <Clock className="w-8 h-8 text-muted-foreground mx-auto" />
              <p className="text-sm font-semibold text-foreground">Timed test requires active questions</p>
              <p className="text-xs text-muted-foreground">Switch to &ldquo;All Cycles&rdquo; or select another cycle to start a timed exam run.</p>
            </div>
          ) : (
            <McqTestingSuite
              questions={ctMcqQuestions}
              subjectName={currentCourse.name}
              cycle={filterCycle}
              initialMode="QUIZ"
            />
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* DESTINATION 5: MINTAI QUESTION GENERATOR                                  */}
      {/* ========================================================================= */}
      {activeDestination === "generator" && (
        <div className="space-y-5">
          <div className="p-5 rounded-2xl bg-card border border-border/80 shadow-xs space-y-4">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-accent/10 text-accent">
                <Sparkles className="w-5 h-5" />
              </span>
              <div>
                <h3 className="text-base font-bold text-foreground">
                  MintAI Question Generator &amp; Synthesizer
                </h3>
                <p className="text-xs text-muted-foreground">
                  Synthesize brand new, unseen examination problems modeled on SRMIST {filterCycle === "ALL" ? "semester" : filterCycle} blueprints with marking rubrics and step-by-step solutions.
                </p>
              </div>
            </div>

            {/* Topic Selector for Generator */}
            {availableTopics.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-border/40">
                <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                  <BookOpen className="w-3.5 h-3.5 text-accent" />
                  <span>Target Specific Syllabus Topic (Optional):</span>
                </label>
                <select
                  value={selectedTopicForAi}
                  onChange={(e) => setSelectedTopicForAi(e.target.value)}
                  className="w-full bg-background border border-border rounded-xl px-3 py-2 text-xs focus:ring-1 focus:ring-accent"
                >
                  <option value="">{currentCourse.name} (Course General / Balanced)</option>
                  {availableTopics.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="pt-2">
              <MintAIQuestionGenerator
                topicName={selectedTopicForAi || currentCourse.name}
                courseId={currentCourse.id}
                cycle={filterCycle}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
