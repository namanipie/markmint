"use client";

import React, { useState, useEffect, useMemo } from "react";
import { 
  Sparkles, 
  HelpCircle, 
  ChevronDown, 
  ChevronUp, 
  CheckCircle2, 
  Eye, 
  EyeOff, 
  FileText, 
  Tag, 
  Award,
  Layers,
  Search,
  CheckSquare,
  ListOrdered
} from "lucide-react";
import { CycleTestQuestion, getCycleTestQuestions } from "@/lib/api";

interface CycleTestQuestionsDrawerProps {
  courseName: string;
  cycle?: string; // "CT1", "CT2", "ALL"
  isOpenDefault?: boolean;
}

export function CycleTestQuestionsDrawer({
  courseName,
  cycle = "CT1",
  isOpenDefault = false,
}: CycleTestQuestionsDrawerProps) {
  const [isOpen, setIsOpen] = useState(isOpenDefault);
  const [isLoading, setIsLoading] = useState(false);
  const [questions, setQuestions] = useState<CycleTestQuestion[]>([]);
  const [activeCategory, setActiveCategory] = useState<"descriptive" | "mcq">("descriptive");
  const [selectedType, setSelectedType] = useState<string>("ALL");
  const [revealedKeys, setRevealedKeys] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (isOpenDefault) {
      setIsOpen(true);
    }
  }, [isOpenDefault, cycle]);

  useEffect(() => {
    if (!courseName) return;
    let active = true;
    setIsLoading(true);

    getCycleTestQuestions(courseName, cycle, 100, "all")
      .then((res) => {
        if (active) {
          const qs = res.questions || [];
          setQuestions(qs);
          setIsLoading(false);
          // If there are no descriptive questions, default to mcq
          const hasDesc = qs.some(q => !q.is_mcq && q.q_type !== "MCQ");
          if (!hasDesc && qs.length > 0) {
            setActiveCategory("mcq");
          }
        }
      })
      .catch(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [courseName, cycle]);

  // Separate MCQs completely from normal/descriptive questions
  const descriptiveQuestions = useMemo(
    () => questions.filter((q) => !q.is_mcq && q.q_type !== "MCQ"),
    [questions]
  );

  const mcqQuestions = useMemo(
    () => questions.filter((q) => q.is_mcq || q.q_type === "MCQ"),
    [questions]
  );

  const currentCategoryList = activeCategory === "descriptive" ? descriptiveQuestions : mcqQuestions;

  // Filter pills based on active category
  const types = useMemo(() => {
    return ["ALL", ...Array.from(new Set(currentCategoryList.map((q) => q.q_type)))];
  }, [currentCategoryList]);

  const filteredQuestions = useMemo(() => {
    if (selectedType === "ALL") return currentCategoryList;
    return currentCategoryList.filter((q) => q.q_type === selectedType);
  }, [currentCategoryList, selectedType]);

  const toggleAnswer = (keyId: string) => {
    setRevealedKeys((prev) => ({ ...prev, [keyId]: !prev[keyId] }));
  };

  if (!questions || questions.length === 0) {
    return null;
  }

  return (
    <div className="rounded-2xl border border-accent/25 bg-card/95 shadow-xs overflow-hidden transition-all">
      {/* Drawer Header Toggle */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3.5 sm:p-4 bg-accent/5 hover:bg-accent/10 transition-colors text-left cursor-pointer"
      >
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-accent/20 border border-accent/30 flex items-center justify-center text-accent">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-xs sm:text-sm font-bold text-foreground">
                Authentic {cycle === "ALL" ? "Cycle Test" : cycle} Questions &amp; Answer Keys
              </h4>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-accent/20 border border-accent/30 text-accent">
                {descriptiveQuestions.length} Normal • {mcqQuestions.length} MCQs
              </span>
            </div>
            <p className="text-[11px] text-muted-foreground">
              Real questions extracted directly from SRMIST past {cycle === "ALL" ? "Cycle Test" : cycle} papers with faculty solutions.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 text-xs text-accent font-semibold">
          <span>{isOpen ? "Hide Questions" : "Practice Questions"}</span>
          {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {/* Expanded Question List */}
      {isOpen && (
        <div className="p-4 sm:p-5 border-t border-border/60 space-y-4">
          {/* Main Section Mode Tabs: Normal vs MCQ */}
          <div className="flex items-center gap-2 p-1 rounded-xl bg-muted/30 border border-border/60">
            <button
              type="button"
              onClick={() => {
                setActiveCategory("descriptive");
                setSelectedType("ALL");
              }}
              className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeCategory === "descriptive"
                  ? "bg-background text-foreground shadow-xs border border-border/70"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <FileText className="w-3.5 h-3.5 text-accent" />
              <span>Normal Questions ({descriptiveQuestions.length})</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setActiveCategory("mcq");
                setSelectedType("ALL");
              }}
              className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeCategory === "mcq"
                  ? "bg-background text-foreground shadow-xs border border-border/70"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <CheckSquare className="w-3.5 h-3.5 text-purple-400" />
              <span>Multiple Choice Section ({mcqQuestions.length})</span>
            </button>
          </div>

          {/* Sub-type filter pills (e.g. Part A Short Answer, Part B Medium) */}
          {types.length > 2 && (
            <div className="flex flex-wrap items-center gap-1.5 pt-1">
              <span className="text-[11px] font-semibold text-muted-foreground mr-1">Section:</span>
              {types.map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setSelectedType(t)}
                  className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all cursor-pointer ${
                    selectedType === t
                      ? "bg-accent text-accent-foreground font-semibold shadow-2xs"
                      : "bg-muted/40 hover:bg-muted text-muted-foreground"
                  }`}
                >
                  {t === "ALL" ? `All (${currentCategoryList.length})` : `${t} (${currentCategoryList.filter((q) => q.q_type === t).length})`}
                </button>
              ))}
            </div>
          )}

          {/* Question Cards Grid */}
          <div className="space-y-3">
            {filteredQuestions.length === 0 ? (
              <div className="text-center py-6 text-xs text-muted-foreground">
                No questions found in this category for {cycle}.
              </div>
            ) : (
              filteredQuestions.slice(0, 25).map((q, idx) => {
                const qKey = `${activeCategory}-${idx}-${q.q_num}`;
                const isKeyOpen = !!revealedKeys[qKey];
                const isMcq = q.is_mcq || q.q_type === "MCQ";

                return (
                  <div 
                    key={qKey}
                    className={`p-3.5 rounded-xl border transition-all space-y-2.5 ${
                      isMcq 
                        ? "border-purple-500/20 bg-purple-500/5 hover:border-purple-500/40" 
                        : "border-border/70 bg-background hover:border-accent/30"
                    }`}
                  >
                    {/* Top Badges */}
                    <div className="flex flex-wrap items-center justify-between gap-2 text-[10px]">
                      <div className="flex items-center gap-1.5">
                        <span className="px-2 py-0.5 rounded font-mono font-bold bg-muted text-foreground border border-border/60">
                          Q{q.q_num}
                        </span>
                        <span className={`px-1.5 py-0.5 rounded font-mono font-semibold ${
                          isMcq ? "bg-purple-500/20 text-purple-300" : "bg-accent/10 text-accent"
                        }`}>
                          {q.marks} {q.marks === 1 ? "Mark" : "Marks"}
                        </span>
                        <span className={`px-2 py-0.5 rounded font-medium ${
                          isMcq 
                            ? "bg-purple-500/15 text-purple-300 border border-purple-500/30 font-semibold" 
                            : "bg-muted/60 text-muted-foreground"
                        }`}>
                          {isMcq ? "Multiple Choice (MCQ)" : q.q_type}
                        </span>
                      </div>

                      <span className="text-muted-foreground font-mono text-[9px] truncate max-w-[200px]" title={q.source_file}>
                        📄 {q.source_file}
                      </span>
                    </div>

                    {/* Question Text */}
                    <div className="text-xs text-foreground font-normal leading-relaxed whitespace-pre-line">
                      {q.question_text}
                    </div>

                    {/* Solution / Key Toggle */}
                    {q.answer_key ? (
                      <div className="pt-1">
                        <button
                          type="button"
                          onClick={() => toggleAnswer(qKey)}
                          className={`inline-flex items-center gap-1.5 text-[11px] font-semibold hover:underline cursor-pointer ${
                            isMcq ? "text-purple-400" : "text-accent"
                          }`}
                        >
                          {isKeyOpen ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                          <span>{isKeyOpen ? "Hide Solution" : "Reveal Faculty Answer Key"}</span>
                        </button>

                        {isKeyOpen && (
                          <div className="mt-2 p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-mono space-y-1">
                            <div className="flex items-center gap-1.5 font-bold text-[11px]">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                              <span>Verified Faculty Answer Key:</span>
                            </div>
                            <div className="whitespace-pre-line text-emerald-200 text-xs">
                              {q.answer_key}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="text-[10px] text-muted-foreground italic pt-0.5">
                        Practice Question • Solution available in compiled exam papers
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>

          {filteredQuestions.length > 25 && (
            <div className="text-center pt-2 text-xs text-muted-foreground">
              Showing 25 of {filteredQuestions.length} {activeCategory === "mcq" ? "MCQs" : "normal questions"}. More sets available in full course papers.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
