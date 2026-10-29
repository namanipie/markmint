"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  FileText,
  Sparkles,
  Search,
  X,
  Eye,
  EyeOff,
  CheckCircle2,
  Layers,
  CheckSquare,
  Printer,
  ChevronDown,
  ChevronUp,
  Download,
  BookOpen
} from "lucide-react";
import { MathText } from "@/components/ui/math-text";
import { CycleTestQuestion, getCycleTestQuestions } from "@/lib/api";
import { McqTestingSuite } from "@/components/practice/mcq-testing-suite";

interface CycleTestArchiveViewerProps {
  initialSubject?: string;
  initialCycle?: string;
  onSelectCourse?: (subjectName: string) => void;
}

function isMcqQuestion(q: CycleTestQuestion): boolean {
  if (q.is_mcq || q.q_type === "MCQ") return true;
  if (q.options && q.options.length >= 2) return true;
  const txt = q.question_text || "";
  if (/(?:^|[\n\s])(?:\([A-Da-d]\)|\[[A-Da-d]\]|[A-Da-d][\.\)])\s*[\s\S]+?(?:\([B-Db-d]\)|\[[B-Db-d]\]|[B-Db-d][\.\)])/.test(txt)) {
    return true;
  }
  return false;
}

export function CycleTestArchiveViewer({
  initialSubject = "ALL",
  initialCycle = "ALL",
  onSelectCourse,
}: CycleTestArchiveViewerProps) {
  const [selectedSubject, setSelectedSubject] = useState<string>(initialSubject);
  const [selectedCycle, setSelectedCycle] = useState<string>(initialCycle);
  const [activeCategory, setActiveCategory] = useState<"all" | "descriptive" | "mcq">("all");
  const [selectedType, setSelectedType] = useState<string>("ALL");
  const [selectedMarks, setSelectedMarks] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [revealedKeys, setRevealedKeys] = useState<Record<string, boolean>>({});

  // Printable Worksheet state
  const [showPrintModal, setShowPrintModal] = useState<boolean>(false);
  const [includeSolutionsInPrint, setIncludeSolutionsInPrint] = useState<boolean>(false);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [questions, setQuestions] = useState<CycleTestQuestion[]>([]);
  const [availableSubjects, setAvailableSubjects] = useState<{ subject: string; count: number }[]>([]);
  const [totalAvailable, setTotalAvailable] = useState<number>(0);
  const [totalDescriptive, setTotalDescriptive] = useState<number>(0);
  const [totalMcqs, setTotalMcqs] = useState<number>(0);

  // Sync initial props
  useEffect(() => {
    if (initialSubject) setSelectedSubject(initialSubject);
  }, [initialSubject]);

  useEffect(() => {
    if (initialCycle) setSelectedCycle(initialCycle);
  }, [initialCycle]);

  // Load questions from backend endpoint
  useEffect(() => {
    let active = true;
    setIsLoading(true);

    getCycleTestQuestions(selectedSubject, selectedCycle, 300, activeCategory)
      .then((res) => {
        if (!active) return;
        setQuestions(res.questions || []);
        setTotalAvailable(res.total_available || 0);
        setTotalDescriptive(res.total_descriptive || 0);
        setTotalMcqs(res.total_mcqs || 0);
        if (res.available_subjects && res.available_subjects.length > 0) {
          setAvailableSubjects(res.available_subjects);
        }
        setIsLoading(false);
      })
      .catch(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [selectedSubject, selectedCycle, activeCategory]);

  // Filter questions based on type, marks weightage, and search query
  const filteredQuestions = useMemo(() => {
    let list = questions;
    if (activeCategory === "descriptive") {
      list = list.filter((q) => !isMcqQuestion(q));
    } else if (activeCategory === "mcq") {
      list = list.filter((q) => isMcqQuestion(q));
    }

    if (selectedType !== "ALL") {
      list = list.filter((q) => q.q_type === selectedType);
    }

    // Marks filter
    if (selectedMarks !== "ALL") {
      if (selectedMarks === "1") {
        list = list.filter((q) => q.marks === 1);
      } else if (selectedMarks === "2") {
        list = list.filter((q) => q.marks === 2);
      } else if (selectedMarks === "MEDIUM") {
        list = list.filter((q) => q.marks && q.marks >= 3 && q.marks <= 8);
      } else if (selectedMarks === "COMPREHENSIVE") {
        list = list.filter((q) => q.marks && q.marks > 8);
      }
    }

    if (searchQuery.trim()) {
      const qLower = searchQuery.toLowerCase().trim();
      list = list.filter(
        (q) =>
          q.question_text.toLowerCase().includes(qLower) ||
          (q.subject && q.subject.toLowerCase().includes(qLower)) ||
          (q.source_file && q.source_file.toLowerCase().includes(qLower)) ||
          (q.answer_key && q.answer_key.toLowerCase().includes(qLower))
      );
    }
    return list;
  }, [questions, activeCategory, selectedType, selectedMarks, searchQuery]);

  const toggleAnswer = (keyId: string) => {
    setRevealedKeys((prev) => ({ ...prev, [keyId]: !prev[keyId] }));
  };

  const areAllExpanded = useMemo(() => {
    if (filteredQuestions.length === 0) return false;
    const visible = filteredQuestions.slice(0, 50);
    return visible.every((_, idx) => !!revealedKeys[`archive-${idx}-${visible[idx].q_num}`]);
  }, [filteredQuestions, revealedKeys]);

  const toggleExpandAll = () => {
    const visible = filteredQuestions.slice(0, 50);
    if (areAllExpanded) {
      setRevealedKeys({});
    } else {
      const next: Record<string, boolean> = {};
      visible.forEach((q, idx) => {
        if (q.answer_key) {
          next[`archive-${idx}-${q.q_num}`] = true;
        }
      });
      setRevealedKeys(next);
    }
  };

  const types = useMemo(() => {
    const relevant = activeCategory === "descriptive"
      ? questions.filter((q) => !isMcqQuestion(q))
      : activeCategory === "mcq"
      ? questions.filter((q) => isMcqQuestion(q))
      : questions;
    return ["ALL", ...Array.from(new Set(relevant.map((q) => q.q_type)))];
  }, [questions, activeCategory]);

  return (
    <div className="space-y-6">
      {/* Hero Header */}
      <div className="p-4 sm:p-6 rounded-2xl border border-accent/25 bg-linear-to-br from-card via-card to-accent/5 shadow-xs space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start sm:items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-accent/15 border border-accent/30 flex items-center justify-center text-accent shadow-xs shrink-0 mt-0.5 sm:mt-0">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex flex-col sm:flex-row sm:items-center gap-1.5 sm:gap-2">
                <h2 className="text-lg sm:text-xl font-bold tracking-tight text-foreground leading-tight">
                  Authentic Cycle Test Question Archive
                </h2>
                <span className="px-2.5 py-0.5 rounded-md text-[11px] sm:text-xs font-mono font-bold bg-accent/20 border border-accent/30 text-accent w-fit shrink-0">
                  5,536 Verified Questions Across All 43 Subjects
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Past CT1, CT2, CT3, and Model exam questions parsed directly from SRMIST papers with faculty answer keys and interactive MCQ testing.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 self-start md:self-center shrink-0">
            {/* Printable Practice Worksheet Trigger */}
            <button
              type="button"
              onClick={() => setShowPrintModal(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 transition-all cursor-pointer shadow-2xs touch-manipulation"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Printable Worksheet</span>
            </button>

            <span className="hidden sm:flex items-center gap-1.5 font-semibold text-xs text-emerald-500 bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Faculty Solutions
            </span>
          </div>
        </div>

        {/* Section Category Switcher: Normal vs MCQs */}
        <div className="pt-1">
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-1.5 sm:gap-2 p-1 rounded-xl bg-muted/40 border border-border/60 max-w-xl">
            <button
              type="button"
              onClick={() => {
                setActiveCategory("all");
                setSelectedType("ALL");
              }}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 sm:py-1.5 px-3 rounded-lg text-xs font-semibold transition-all cursor-pointer touch-manipulation ${
                activeCategory === "all"
                  ? "bg-background text-foreground shadow-xs border border-border/70 font-bold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>All Questions ({totalAvailable})</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setActiveCategory("descriptive");
                setSelectedType("ALL");
              }}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 sm:py-1.5 px-3 rounded-lg text-xs font-semibold transition-all cursor-pointer touch-manipulation ${
                activeCategory === "descriptive"
                  ? "bg-background text-foreground shadow-xs border border-border/70 text-accent font-bold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <FileText className="w-3.5 h-3.5 text-accent" />
              <span>Normal Questions ({totalDescriptive || 2894})</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setActiveCategory("mcq");
                setSelectedType("ALL");
              }}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 sm:py-1.5 px-3 rounded-lg text-xs font-semibold transition-all cursor-pointer touch-manipulation ${
                activeCategory === "mcq"
                  ? "bg-background text-foreground shadow-xs border border-border/70 text-purple-400 font-bold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <CheckSquare className="w-3.5 h-3.5 text-purple-400" />
              <span>MCQ Testing System ({totalMcqs || 2642})</span>
            </button>
          </div>
        </div>

        {/* Filter Controls Bar */}
        <div className="pt-3 border-t border-border/50 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Subject Selector */}
          <div>
            <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block mb-1.5">
              Subject Filter
            </label>
            <select
              value={selectedSubject}
              onChange={(e) => setSelectedSubject(e.target.value)}
              className="w-full bg-background border border-border rounded-xl px-3 py-2 text-xs font-medium text-foreground focus:ring-1 focus:ring-accent focus:outline-none shadow-2xs"
            >
              <option value="ALL">All Subjects ({totalAvailable > 0 ? totalAvailable : 5536})</option>
              {availableSubjects.map((s) => (
                <option key={s.subject} value={s.subject}>
                  {s.subject} ({s.count} qs)
                </option>
              ))}
            </select>
          </div>

          {/* Assessment Cycle Selector */}
          <div>
            <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block mb-1.5">
              Exam Cycle
            </label>
            <div className="flex items-center gap-1 overflow-x-auto no-scrollbar pb-0.5">
              {[
                { id: "ALL", label: "All" },
                { id: "CT1", label: "CT1" },
                { id: "CT2", label: "CT2" },
                { id: "CT3", label: "CT3/Model" },
              ].map((cyc) => (
                <button
                  key={cyc.id}
                  type="button"
                  onClick={() => setSelectedCycle(cyc.id)}
                  className={`flex-1 min-w-[50px] py-1.5 px-2 rounded-xl text-xs font-semibold text-center transition-all cursor-pointer border touch-manipulation ${
                    selectedCycle === cyc.id
                      ? "bg-accent text-accent-foreground border-accent shadow-xs"
                      : "bg-background border-border hover:bg-muted/30 text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {cyc.label}
                </button>
              ))}
            </div>
          </div>

          {/* Marks Weightage Filter */}
          <div>
            <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block mb-1.5">
              Marks Weightage
            </label>
            <select
              value={selectedMarks}
              onChange={(e) => setSelectedMarks(e.target.value)}
              className="w-full bg-background border border-border rounded-xl px-3 py-2 text-xs font-medium text-foreground focus:ring-1 focus:ring-accent focus:outline-none shadow-2xs"
            >
              <option value="ALL">All Marks (1M, 2M, 5M, 10M+)</option>
              <option value="1">1 Mark (MCQ / Objective)</option>
              <option value="2">2 Marks (Short Answer)</option>
              <option value="MEDIUM">4 – 8 Marks (Medium Answer)</option>
              <option value="COMPREHENSIVE">10 – 15 Marks (Comprehensive)</option>
            </select>
          </div>

          {/* Real-time Search Input */}
          <div>
            <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block mb-1.5">
              Search Questions &amp; Formulas
            </label>
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search keywords, formulas..."
                className="w-full bg-background border border-border rounded-xl px-3 py-2 pl-8 pr-7 text-xs text-foreground placeholder:text-muted-foreground focus:ring-1 focus:ring-accent focus:outline-none shadow-2xs"
              />
              <Search className="w-3.5 h-3.5 text-muted-foreground absolute left-2.5 top-1/2 -translate-y-1/2" />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Section Filter Pills and Expand/Collapse All Actions */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-border/40">
          {activeCategory !== "mcq" && types.length > 2 && (
            <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-1">
              <span className="text-[10px] font-semibold text-muted-foreground mr-1 shrink-0">Section:</span>
              {types.map((t) => {
                const count = t === "ALL" 
                  ? filteredQuestions.length 
                  : filteredQuestions.filter((q) => q.q_type === t).length;
                return (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setSelectedType(t)}
                    className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all cursor-pointer whitespace-nowrap shrink-0 touch-manipulation ${
                      selectedType === t
                        ? "bg-accent/20 border border-accent/40 text-accent font-semibold shadow-2xs"
                        : "bg-muted/40 hover:bg-muted text-muted-foreground"
                    }`}
                  >
                    {t === "ALL" ? `All (${count})` : `${t.replace(/_/g, " ")} (${count})`}
                  </button>
                );
              })}
            </div>
          )}

          {activeCategory !== "mcq" && filteredQuestions.length > 0 && (
            <button
              type="button"
              onClick={toggleExpandAll}
              className="inline-flex items-center gap-1 text-[11px] font-semibold text-accent hover:underline cursor-pointer ml-auto py-1"
            >
              {areAllExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              <span>{areAllExpanded ? "Collapse All Solutions" : "Expand All Faculty Solutions"}</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      {isLoading ? (
        <div className="p-12 text-center rounded-2xl border border-dashed border-border flex flex-col items-center justify-center gap-3 text-muted-foreground">
          <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          <p className="text-xs font-medium">Fetching verified cycle test questions...</p>
        </div>
      ) : activeCategory === "mcq" ? (
        /* DEDICATED INTERACTIVE MCQ TESTING SUITE */
        <McqTestingSuite
          questions={filteredQuestions}
          subjectName={selectedSubject === "ALL" ? "All Subjects" : selectedSubject}
          cycle={selectedCycle === "ALL" ? "Cycle Tests" : selectedCycle}
        />
      ) : filteredQuestions.length === 0 ? (
        <div className="p-10 text-center rounded-2xl border border-dashed border-border bg-card space-y-3">
          <p className="text-sm font-semibold text-foreground">No questions matched the current filters.</p>
          <p className="text-xs text-muted-foreground max-w-md mx-auto">
            Try switching categories, clearing your search query, adjusting marks weightage, or selecting another subject.
          </p>
          <button
            onClick={() => {
              setActiveCategory("all");
              setSelectedCycle("ALL");
              setSelectedType("ALL");
              setSelectedMarks("ALL");
              setSearchQuery("");
            }}
            className="text-xs px-3 py-1.5 bg-accent/10 hover:bg-accent/20 text-accent font-semibold rounded-lg transition-all"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        /* STANDARD DESCRIPTIVE QUESTION LIST */
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground px-1">
            <span>
              Showing <strong className="text-foreground">{Math.min(filteredQuestions.length, 50)}</strong> of{" "}
              <strong className="text-foreground">{filteredQuestions.length}</strong> questions
              {selectedSubject !== "ALL" ? ` for ${selectedSubject}` : ""}
              {activeCategory === "descriptive" ? " (Normal Questions Only)" : ""}
              {selectedMarks !== "ALL" ? ` • ${selectedMarks} Mark Filter Active` : ""}
            </span>
            <span className="font-mono text-[11px]">
              {selectedCycle !== "ALL" ? `Assessment: ${selectedCycle}` : "All Assessment Cycles"}
            </span>
          </div>

          <div className="space-y-3">
            {filteredQuestions.slice(0, 50).map((q, idx) => {
              const qKey = `archive-${idx}-${q.q_num}`;
              const isKeyOpen = !!revealedKeys[qKey];

              return (
                <div
                  key={qKey}
                  className="p-4 sm:p-5 rounded-2xl border border-border/70 bg-card hover:border-accent/35 transition-all space-y-3 shadow-2xs"
                >
                  {/* Top Bar Metadata */}
                  <div className="flex flex-wrap items-center justify-between gap-2 text-[10px]">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="px-2 py-0.5 rounded font-mono font-bold bg-muted text-foreground border border-border/60">
                        Q{q.q_num}
                      </span>
                      <span className="px-2 py-0.5 rounded font-mono font-bold bg-accent/15 text-accent border border-accent/25">
                        {q.marks} {q.marks === 1 ? "Mark" : "Marks"}
                      </span>
                      <span className="px-2 py-0.5 rounded bg-muted/60 text-muted-foreground font-semibold">
                        {q.q_type.replace(/_/g, " ")}
                      </span>
                      <span className="px-2 py-0.5 rounded font-mono font-bold bg-primary/10 text-primary border border-primary/20">
                        {q.cycle}
                      </span>
                      {q.subject && (
                        <span className="px-2 py-0.5 rounded bg-foreground/5 text-foreground/80 font-medium">
                          {q.subject}
                        </span>
                      )}
                    </div>

                    <span
                      className="text-muted-foreground font-mono text-[9px] truncate max-w-[260px]"
                      title={q.source_file}
                    >
                      📄 {q.source_file}
                    </span>
                  </div>

                  {/* Question Content */}
                  <div className="text-xs sm:text-sm text-foreground/95 font-normal leading-relaxed whitespace-pre-line font-sans">
                    <MathText content={q.question_text} />
                  </div>

                  {/* Faculty Solution / Key Accordion */}
                  {q.answer_key ? (
                    <div className="pt-2 border-t border-border/40">
                      <button
                        type="button"
                        onClick={() => toggleAnswer(qKey)}
                        className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400 hover:underline cursor-pointer"
                      >
                        {isKeyOpen ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                        <span>{isKeyOpen ? "Hide Solution" : "Reveal Faculty Answer Key"}</span>
                      </button>

                      {isKeyOpen && (
                        <div className="mt-2.5 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/25 text-emerald-200 text-xs font-mono space-y-1.5 shadow-xs">
                          <div className="flex items-center gap-1.5 font-bold text-xs text-emerald-300">
                            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                            <span>Verified Faculty Answer Key:</span>
                          </div>
                          <div className="whitespace-pre-line text-emerald-100 text-xs leading-relaxed font-sans">
                            <MathText content={q.answer_key} />
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-[10px] text-muted-foreground italic pt-1 border-t border-border/30">
                      Practice Question • Full solved solution available in course repository
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {filteredQuestions.length > 50 && (
            <div className="text-center py-4 border-t border-border/40 text-xs text-muted-foreground">
              Showing 50 of {filteredQuestions.length} questions. Adjust subject, cycle, marks, and category filters to explore more questions.
            </div>
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* PRINTABLE PRACTICE WORKSHEET MODAL / FULL-SCREEN VIEW                 */}
      {/* ===================================================================== */}
      {showPrintModal && (
        <div className="fixed inset-0 z-50 bg-background/95 backdrop-blur-md overflow-y-auto p-4 sm:p-6 md:p-10 flex flex-col items-center">
          {/* Header Action Bar (Hidden when printing via CSS print media) */}
          <div className="w-full max-w-4xl flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-border mb-6 print:hidden">
            <div className="flex items-center gap-2">
              <Printer className="w-5 h-5 text-accent" />
              <h3 className="font-bold text-sm sm:text-base text-foreground">
                Printable Practice Worksheet Preview
              </h3>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <label className="inline-flex items-center gap-2 text-xs font-medium text-foreground cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeSolutionsInPrint}
                  onChange={(e) => setIncludeSolutionsInPrint(e.target.checked)}
                  className="rounded border-border text-accent focus:ring-accent"
                />
                <span>Include Faculty Answer Keys</span>
              </label>

              <button
                type="button"
                onClick={() => window.print()}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-accent text-accent-foreground shadow-sm hover:opacity-90 transition-all cursor-pointer"
              >
                <Printer className="w-4 h-4" />
                <span>Print / Save as PDF</span>
              </button>

              <button
                type="button"
                onClick={() => setShowPrintModal(false)}
                className="px-3 py-2 rounded-xl text-xs font-medium bg-muted hover:bg-muted/80 text-foreground transition-all cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>

          {/* Printable Worksheet Document Container */}
          <div className="w-full max-w-4xl bg-card border border-border/80 rounded-2xl p-6 sm:p-10 shadow-lg text-foreground font-sans space-y-6 print:border-none print:shadow-none print:p-0 print:bg-transparent">
            {/* Institution Letterhead */}
            <div className="text-center border-b-2 border-foreground/20 pb-4 space-y-1">
              <h1 className="text-lg sm:text-xl font-extrabold uppercase tracking-wide">
                SRM INSTITUTE OF SCIENCE AND TECHNOLOGY
              </h1>
              <p className="text-xs uppercase tracking-wider font-semibold text-muted-foreground">
                Faculty of Engineering and Technology • Department of Computer Science &amp; Engineering
              </p>
              <div className="pt-2 text-sm font-bold text-accent">
                {selectedSubject === "ALL" ? "Comprehensive Engineering Examination Worksheet" : selectedSubject}
              </div>
              <div className="flex flex-wrap justify-between text-[11px] font-mono text-muted-foreground pt-2">
                <span>Assessment: {selectedCycle === "ALL" ? "Continuous Assessment (CT1/CT2/Model)" : selectedCycle}</span>
                <span>Time Allowed: 90 Minutes</span>
                <span>Maximum Marks: 50 Marks</span>
              </div>
            </div>

            {/* Exam Instructions */}
            <div className="p-3 rounded-lg bg-muted/20 border border-border/50 text-[11px] space-y-0.5 text-muted-foreground">
              <p className="font-bold text-foreground">Instructions:</p>
              <p>1. Answer all questions clearly. Show detailed formulas and intermediate steps.</p>
              <p>2. Diagrams and sketches should be drawn neatly with proper labeling.</p>
              <p>3. Authentic past examination question set compiled for student practice.</p>
            </div>

            {/* Questions Body */}
            <div className="space-y-5 pt-2">
              {filteredQuestions.slice(0, 30).map((q, qIndex) => (
                <div key={qIndex} className="space-y-1.5 pb-4 border-b border-border/40 last:border-b-0 break-inside-avoid">
                  <div className="flex items-baseline justify-between text-xs font-bold">
                    <span>Question {qIndex + 1} [{q.q_type.replace(/_/g, " ")}]</span>
                    <span className="font-mono text-muted-foreground">[{q.marks} {q.marks === 1 ? "Mark" : "Marks"}]</span>
                  </div>

                  <div className="text-xs sm:text-sm leading-relaxed whitespace-pre-line text-foreground/90 font-sans">
                    <MathText content={q.question_text} />
                  </div>

                  {includeSolutionsInPrint && q.answer_key && (
                    <div className="mt-2 p-2.5 rounded-lg bg-muted/40 border border-border/70 text-[11px] text-foreground/80 space-y-1 font-mono">
                      <div className="font-bold text-accent flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Faculty Solution Key:</span>
                      </div>
                      <div className="whitespace-pre-line text-[11px] font-sans">
                        <MathText content={q.answer_key} />
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Footer */}
            <div className="text-center pt-6 border-t border-border/50 text-[10px] text-muted-foreground font-mono">
              Generated by MintAI Intelligence System • For SRMIST Academic &amp; Examination Practice
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
