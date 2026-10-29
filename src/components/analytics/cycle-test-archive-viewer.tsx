"use client";

import React, { useState, useEffect, useMemo } from "react";
import { 
  Sparkles, 
  HelpCircle, 
  CheckCircle2, 
  Eye, 
  EyeOff, 
  FileText, 
  Search, 
  BookOpen, 
  Layers, 
  X, 
  ChevronRight,
  Filter,
  Award
} from "lucide-react";
import { MathText } from "@/components/ui/math-text";
import { CycleTestQuestion, getCycleTestQuestions } from "@/lib/api";

interface CycleTestArchiveViewerProps {
  initialSubject?: string;
  initialCycle?: string;
  onSelectCourse?: (subjectName: string) => void;
}

export function CycleTestArchiveViewer({
  initialSubject = "ALL",
  initialCycle = "ALL",
  onSelectCourse,
}: CycleTestArchiveViewerProps) {
  const [selectedSubject, setSelectedSubject] = useState<string>(initialSubject);
  const [selectedCycle, setSelectedCycle] = useState<string>(initialCycle);
  const [selectedType, setSelectedType] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [revealedKeys, setRevealedKeys] = useState<Record<number, boolean>>({});

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [questions, setQuestions] = useState<CycleTestQuestion[]>([]);
  const [availableSubjects, setAvailableSubjects] = useState<{ subject: string; count: number }[]>([]);
  const [totalAvailable, setTotalAvailable] = useState<number>(0);

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

    getCycleTestQuestions(selectedSubject, selectedCycle, 300)
      .then((res) => {
        if (!active) return;
        setQuestions(res.questions || []);
        setTotalAvailable(res.total_available || 0);
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
  }, [selectedSubject, selectedCycle]);

  // Filter questions based on type and search query
  const filteredQuestions = useMemo(() => {
    let list = questions;
    if (selectedType !== "ALL") {
      list = list.filter((q) => q.q_type === selectedType);
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
  }, [questions, selectedType, searchQuery]);

  const toggleAnswer = (idx: number) => {
    setRevealedKeys((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const types = ["ALL", ...Array.from(new Set(questions.map((q) => q.q_type)))];

  return (
    <div className="space-y-6">
      {/* Hero Header */}
      <div className="p-5 sm:p-6 rounded-2xl border border-accent/25 bg-linear-to-br from-card via-card to-accent/5 shadow-xs space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-accent/15 border border-accent/30 flex items-center justify-center text-accent shadow-xs">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg sm:text-xl font-bold tracking-tight text-foreground">
                  Authentic Cycle Test Question Archive
                </h2>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-accent/20 border border-accent/30 text-accent">
                  1,343 Verified Questions
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Past CT1, CT2, CT3, and Model exam questions parsed directly from SRMIST papers with faculty answer keys.
              </p>
            </div>
          </div>

          <div className="inline-flex items-center gap-2 text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5 font-semibold text-emerald-500 bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Verified Faculty Solutions Included
            </span>
          </div>
        </div>

        {/* Filter Controls Bar */}
        <div className="pt-3 border-t border-border/50 grid grid-cols-1 md:grid-cols-3 gap-3">
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
              <option value="ALL">All Subjects ({totalAvailable > 0 ? totalAvailable : 1343})</option>
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
            <div className="flex items-center gap-1.5">
              {[
                { id: "ALL", label: "All Cycles" },
                { id: "CT1", label: "CT1 (Units 1 & 2)" },
                { id: "CT2", label: "CT2 (Units 3 & 4)" },
                { id: "CT3", label: "CT3 / Model" },
              ].map((cyc) => (
                <button
                  key={cyc.id}
                  type="button"
                  onClick={() => setSelectedCycle(cyc.id)}
                  className={`flex-1 py-2 px-2 rounded-xl text-xs font-semibold text-center transition-all cursor-pointer border ${
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
                placeholder="Search by keywords, formulas, concepts..."
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

        {/* Question Type Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          <span className="text-[10px] font-semibold text-muted-foreground mr-1">Type:</span>
          {types.map((t) => {
            const count = t === "ALL" ? questions.length : questions.filter((q) => q.q_type === t).length;
            return (
              <button
                key={t}
                type="button"
                onClick={() => setSelectedType(t)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all cursor-pointer ${
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
      </div>

      {/* Questions Listing */}
      {isLoading ? (
        <div className="p-12 text-center rounded-2xl border border-dashed border-border flex flex-col items-center justify-center gap-3 text-muted-foreground">
          <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          <p className="text-xs font-medium">Fetching verified cycle test questions...</p>
        </div>
      ) : filteredQuestions.length === 0 ? (
        <div className="p-10 text-center rounded-2xl border border-dashed border-border bg-card space-y-3">
          <p className="text-sm font-semibold text-foreground">No questions matched the current filters.</p>
          <p className="text-xs text-muted-foreground max-w-md mx-auto">
            Try switching to &ldquo;All Cycles&rdquo;, clearing your search query, or selecting another subject.
          </p>
          <button
            onClick={() => {
              setSelectedCycle("ALL");
              setSelectedType("ALL");
              setSearchQuery("");
            }}
            className="text-xs px-3 py-1.5 bg-accent/10 hover:bg-accent/20 text-accent font-semibold rounded-lg transition-all"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-muted-foreground px-1">
            <span>
              Showing <strong className="text-foreground">{Math.min(filteredQuestions.length, 50)}</strong> of{" "}
              <strong className="text-foreground">{filteredQuestions.length}</strong> questions
              {selectedSubject !== "ALL" ? ` for ${selectedSubject}` : ""}
            </span>
            <span className="font-mono text-[11px]">
              {selectedCycle !== "ALL" ? `Assessment: ${selectedCycle}` : "All Assessment Cycles"}
            </span>
          </div>

          <div className="space-y-3">
            {filteredQuestions.slice(0, 50).map((q, idx) => {
              const isKeyOpen = !!revealedKeys[idx];
              return (
                <div
                  key={idx}
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
                        onClick={() => toggleAnswer(idx)}
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
                          <div className="whitespace-pre-line text-emerald-100 text-xs leading-relaxed">
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
              Showing 50 of {filteredQuestions.length} questions. Adjust subject and cycle filters to explore more specific question sets.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
