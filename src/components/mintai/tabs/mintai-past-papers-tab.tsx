"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import {
  FileText,
  Filter,
  Search,
  CheckCircle2,
  Eye,
  EyeOff,
  Sparkles,
  BookOpen,
  Calendar,
  Layers,
  Award,
  Activity,
  Check,
  ChevronDown
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

interface MintAIPastPapersTabProps {
  currentCourse: CourseCatalogItem | null;
  selectedCycle: string;
  selectedUnits?: number[];
}

interface UnifiedHistoricalItem {
  id: string;
  sourceType: "PYQ" | "CT";
  questionNumber?: number | string;
  text: string;
  unit: number;
  marks: number;
  year?: string | number;
  assessmentType: string;
  repetitionType?: string | null;
  familyName?: string | null;
  sourceTitle: string;
  answerKey?: string | null;
}

export function MintAIPastPapersTab({
  currentCourse,
  selectedCycle,
  selectedUnits
}: MintAIPastPapersTabProps) {
  // Filter States
  const [filterAssessment, setFilterAssessment] = useState<string>(selectedCycle || "ALL");
  const [filterUnit, setFilterUnit] = useState<string>("ALL");
  const [filterMarks, setFilterMarks] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Sync assessment filter with shell header cycle
  useEffect(() => {
    if (selectedCycle) {
      setFilterAssessment(selectedCycle);
    }
  }, [selectedCycle]);

  // Data States
  const [pyqs, setPyqs] = useState<HistoricalQuestion[]>([]);
  const [ctQuestions, setCtQuestions] = useState<CycleTestQuestion[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Practiced and Answer Key Reveal States
  const [practicedIds, setPracticedIds] = useState<Record<string, boolean>>({});
  const [revealedAnswers, setRevealedAnswers] = useState<Record<string, boolean>>({});

  // 1. Fetch PYQs and CT archives on course/cycle change
  useEffect(() => {
    let isMounted = true;
    if (!currentCourse) return;

    async function loadCorpus() {
      setIsLoading(true);
      try {
        const [pyqRes, ctRes] = await Promise.all([
          getHistoricalQuestions(
            currentCourse!.id,
            undefined,
            filterAssessment === "ALL" ? undefined : filterAssessment,
            100
          ).catch(() => ({ questions: [] as HistoricalQuestion[] })),
          getCycleTestQuestions(
            currentCourse!.name,
            filterAssessment === "ALL" ? undefined : filterAssessment,
            100,
            "descriptive"
          ).catch(() => ({ questions: [] as CycleTestQuestion[] }))
        ]);

        if (!isMounted) return;
        setPyqs(pyqRes?.questions || []);
        setCtQuestions(ctRes?.questions || []);
      } catch (err) {
        console.error("Failed to load historical papers corpus:", err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    loadCorpus();

    return () => {
      isMounted = false;
    };
  }, [currentCourse, filterAssessment]);

  // Helper: Unit Resolver
  const resolveUnit = useCallback(
    (topics: string[] | string | undefined, text: string): number => {
      const topicList = Array.isArray(topics)
        ? topics
        : typeof topics === "string"
        ? [topics]
        : [];

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

      // Hash fallback
      let hash = 0;
      for (let i = 0; i < text.length; i++) {
        hash = (hash << 5) - hash + text.charCodeAt(i);
        hash |= 0;
      }
      return (Math.abs(hash) % 5) + 1;
    },
    [currentCourse]
  );

  // 2. Unify into a single chronological library
  const unifiedCorpus: UnifiedHistoricalItem[] = useMemo(() => {
    const list: UnifiedHistoricalItem[] = [];

    // Map PYQs
    pyqs.forEach((q, idx) => {
      const qText = cleanQuestionText(q.original_text || "");
      list.push({
        id: `pyq-${q.id || idx}`,
        sourceType: "PYQ",
        questionNumber: q.question_number || idx + 1,
        text: qText,
        unit: resolveUnit(q.topics, qText),
        marks: q.marks || 10,
        year: q.year || "Past Exam",
        assessmentType: q.assessment_type || "EndSem",
        repetitionType: q.repetition_type,
        familyName: q.family_name,
        sourceTitle: q.source_document_title || "SRM End Semester Exam Paper",
        answerKey: (q as any).answer_key || null
      });
    });

    // Map CT Questions (Descriptive)
    ctQuestions.forEach((ct, idx) => {
      // Exclude MCQs from Past Papers tab (they are in Practice tab)
      if (ct.is_mcq || ct.q_type === "MCQ") return;
      if (ct.options && ct.options.length >= 2) return;

      const qText = cleanQuestionText(ct.question_text || "");
      list.push({
        id: `ct-${ct.q_num || idx}`,
        sourceType: "CT",
        questionNumber: ct.q_num || idx + 1,
        text: qText,
        unit: ct.unit || resolveUnit(ct.topic ? [ct.topic] : undefined, qText),
        marks: ct.marks || 8,
        year: ct.cycle || "Cycle Test",
        assessmentType: ct.cycle || "CT",
        repetitionType: null,
        familyName: null,
        sourceTitle: ct.source_file || `${ct.cycle} Assessment Archive`,
        answerKey: ct.answer_key
      });
    });

    return list;
  }, [pyqs, ctQuestions, resolveUnit]);

  // 3. Filtered items
  const filteredItems = useMemo(() => {
    return unifiedCorpus.filter((item) => {
      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const textMatch = item.text.toLowerCase().includes(q);
        const sourceMatch = item.sourceTitle.toLowerCase().includes(q);
        const familyMatch = (item.familyName || "").toLowerCase().includes(q);
        if (!textMatch && !sourceMatch && !familyMatch) return false;
      }

      // Unit filter
      if (filterUnit !== "ALL") {
        if (item.unit !== parseInt(filterUnit, 10)) return false;
      }

      // Marks filter
      if (filterMarks !== "ALL") {
        const m = parseInt(filterMarks, 10);
        if (m === 2 && item.marks > 2) return false;
        if (m === 5 && (item.marks < 3 || item.marks > 5)) return false;
        if (m === 8 && (item.marks < 6 || item.marks > 8)) return false;
        if (m === 10 && item.marks < 10) return false;
      }

      return true;
    });
  }, [unifiedCorpus, searchQuery, filterUnit, filterMarks]);

  if (!currentCourse) return null;

  return (
    <div className="space-y-6">
      {/* ========================================================================= */}
      {/* FILTER CONTROL BAR                                                        */}
      {/* ========================================================================= */}
      <div className="p-4 sm:p-5 rounded-2xl bg-card border border-border/80 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border/50 pb-3">
          <div className="space-y-0.5">
            <h2 className="text-lg sm:text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <FileText className="w-5 h-5 text-primary" />
              <span>Historical Question Library</span>
            </h2>
            <p className="text-xs text-muted-foreground">
              Unified previous year papers &amp; cycle test archives for <strong className="text-foreground">{currentCourse.name}</strong>.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="px-2.5 py-1 rounded-lg bg-primary/10 text-primary font-bold">
              {filteredItems.length} Questions Cataloged
            </span>
          </div>
        </div>

        {/* Filter Rows */}
        <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
          {/* Search Field (6 cols) */}
          <div className="sm:col-span-6 relative">
            <Search className="w-3.5 h-3.5 absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by keywords, formulas, theorem names..."
              className="w-full bg-background border border-border rounded-xl pl-9 pr-3 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-hidden focus:ring-1 focus:ring-primary"
            />
          </div>

          {/* Assessment Cycle Selector (2 cols) */}
          <div className="sm:col-span-2">
            <select
              value={filterAssessment}
              onChange={(e) => setFilterAssessment(e.target.value)}
              className="w-full bg-background border border-border rounded-xl px-2.5 py-2 text-xs text-foreground focus:outline-hidden focus:ring-1 focus:ring-primary"
            >
              <option value="ALL">All Exams</option>
              <option value="ENDSEM">End Semester</option>
              <option value="CT1">CT1</option>
              <option value="CT2">CT2</option>
            </select>
          </div>

          {/* Unit Filter (2 cols) */}
          <div className="sm:col-span-2">
            <select
              value={filterUnit}
              onChange={(e) => setFilterUnit(e.target.value)}
              className="w-full bg-background border border-border rounded-xl px-2.5 py-2 text-xs text-foreground focus:outline-hidden focus:ring-1 focus:ring-primary"
            >
              <option value="ALL">All Units</option>
              <option value="1">Unit 1</option>
              <option value="2">Unit 2</option>
              <option value="3">Unit 3</option>
              <option value="4">Unit 4</option>
              <option value="5">Unit 5</option>
            </select>
          </div>

          {/* Marks Filter (2 cols) */}
          <div className="sm:col-span-2">
            <select
              value={filterMarks}
              onChange={(e) => setFilterMarks(e.target.value)}
              className="w-full bg-background border border-border rounded-xl px-2.5 py-2 text-xs text-foreground focus:outline-hidden focus:ring-1 focus:ring-primary"
            >
              <option value="ALL">All Marks</option>
              <option value="2">2-Mark (Short)</option>
              <option value="5">5-Mark</option>
              <option value="8">8-Mark</option>
              <option value="10">10-Mark (Long)</option>
            </select>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* QUESTIONS LIST                                                            */}
      {/* ========================================================================= */}
      {isLoading ? (
        <div className="py-16 text-center text-xs text-muted-foreground flex items-center justify-center gap-2">
          <Activity className="w-4 h-4 animate-spin text-primary" />
          <span>Fetching verified examination corpus...</span>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="p-12 text-center rounded-2xl border border-dashed border-border/80 bg-card/40 space-y-2">
          <FileText className="w-8 h-8 text-muted-foreground mx-auto" />
          <p className="text-sm font-semibold text-foreground">No questions match your current filters</p>
          <p className="text-xs text-muted-foreground">Try clearing search terms or setting unit to &ldquo;All Units&rdquo;.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredItems.map((q, idx) => {
            const isPracticed = Boolean(practicedIds[q.id]);
            const isAnswerRevealed = Boolean(revealedAnswers[q.id]);

            return (
              <div
                key={q.id || idx}
                className={`p-4 sm:p-5 rounded-2xl border transition-all ${
                  isPracticed
                    ? "bg-card/40 border-emerald-500/30"
                    : "bg-card border-border/80 hover:border-primary/40 shadow-xs"
                }`}
              >
                {/* Header Metadata */}
                <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-border/40 text-xs">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="px-2 py-0.5 rounded font-mono font-bold bg-secondary text-foreground text-[10px]">
                      Q#{q.questionNumber}
                    </span>
                    <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-primary/10 text-primary font-bold">
                      Unit {q.unit}
                    </span>
                    <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-secondary text-secondary-foreground font-semibold">
                      {q.year} {q.assessmentType}
                    </span>
                    {q.familyName && (
                      <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-purple-500/10 text-purple-600 dark:text-purple-400 font-semibold border border-purple-500/20">
                        {q.familyName}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full bg-primary/15 text-primary font-bold font-mono text-xs">
                      {q.marks} Marks
                    </span>
                    <button
                      type="button"
                      onClick={() => setPracticedIds((prev) => ({ ...prev, [q.id]: !prev[q.id] }))}
                      className={`p-1.5 rounded-lg border transition-colors cursor-pointer ${
                        isPracticed
                          ? "bg-emerald-500 text-white border-emerald-500"
                          : "bg-background border-border text-muted-foreground hover:text-foreground"
                      }`}
                      title={isPracticed ? "Marked as Practiced" : "Mark as Practiced"}
                    >
                      <Check className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Question Stem */}
                <div className="py-3.5 text-xs sm:text-sm text-foreground leading-relaxed font-normal">
                  <MathText content={q.text} />
                </div>

                {/* Paper Source & Solution Key Button */}
                <div className="pt-2.5 border-t border-border/40 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[11px] text-muted-foreground">
                  <span className="font-mono truncate max-w-sm">
                    {q.sourceTitle}
                  </span>

                  {q.answerKey ? (
                    <button
                      type="button"
                      onClick={() => setRevealedAnswers((prev) => ({ ...prev, [q.id]: !prev[q.id] }))}
                      className="inline-flex items-center gap-1 font-semibold text-primary hover:underline cursor-pointer"
                    >
                      {isAnswerRevealed ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                      <span>{isAnswerRevealed ? "Hide Official Answer Key" : "View Faculty Solution Key"}</span>
                    </button>
                  ) : (
                    <span className="text-[10px] text-muted-foreground italic">
                      Solution available in Practice mode
                    </span>
                  )}
                </div>

                {/* Expandable Faculty Solution Key */}
                {isAnswerRevealed && q.answerKey && (
                  <div className="mt-3 p-3.5 rounded-xl bg-secondary/60 border border-border/80 text-xs space-y-1.5 animate-in fade-in-50 duration-150">
                    <div className="font-semibold text-foreground flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-primary" />
                      <span>Official Faculty Solution &amp; Marking Breakdown</span>
                    </div>
                    <div className="text-muted-foreground leading-relaxed">
                      <MathText content={q.answerKey} />
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
