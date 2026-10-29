"use client";

import React, { useState, useEffect } from "react";
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
  Search
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
  const [selectedType, setSelectedType] = useState<string>("ALL");
  const [revealedKeys, setRevealedKeys] = useState<Record<number, boolean>>({});

  useEffect(() => {
    if (isOpenDefault) {
      setIsOpen(true);
    }
  }, [isOpenDefault, cycle]);

  useEffect(() => {
    if (!courseName) return;
    let active = true;
    setIsLoading(true);

    getCycleTestQuestions(courseName, cycle, 60)
      .then((res) => {
        if (active) {
          setQuestions(res.questions || []);
          setIsLoading(false);
        }
      })
      .catch(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [courseName, cycle]);

  if (!questions || questions.length === 0) {
    return null;
  }

  const filteredQuestions = selectedType === "ALL" 
    ? questions 
    : questions.filter(q => q.q_type === selectedType);

  const toggleAnswer = (idx: number) => {
    setRevealedKeys(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  const types = ["ALL", ...Array.from(new Set(questions.map(q => q.q_type)))];

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
                {questions.length} questions
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
          {/* Filter Pills */}
          <div className="flex flex-wrap items-center gap-1.5 pb-1">
            <span className="text-[11px] font-semibold text-muted-foreground mr-1">Type:</span>
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
                {t === "ALL" ? `All (${questions.length})` : `${t} (${questions.filter(q => q.q_type === t).length})`}
              </button>
            ))}
          </div>

          {/* Question Cards Grid */}
          <div className="space-y-3">
            {filteredQuestions.slice(0, 25).map((q, idx) => {
              const isKeyOpen = !!revealedKeys[idx];
              return (
                <div 
                  key={idx}
                  className="p-3.5 rounded-xl border border-border/70 bg-background hover:border-accent/30 transition-all space-y-2.5"
                >
                  {/* Top Badges */}
                  <div className="flex flex-wrap items-center justify-between gap-2 text-[10px]">
                    <div className="flex items-center gap-1.5">
                      <span className="px-2 py-0.5 rounded font-mono font-bold bg-muted text-foreground border border-border/60">
                        Q{q.q_num}
                      </span>
                      <span className="px-1.5 py-0.5 rounded font-mono bg-accent/10 text-accent font-semibold">
                        {q.marks} {q.marks === 1 ? "Mark" : "Marks"}
                      </span>
                      <span className="px-1.5 py-0.5 rounded bg-muted/60 text-muted-foreground font-medium">
                        {q.q_type}
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
                        onClick={() => toggleAnswer(idx)}
                        className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-accent hover:underline cursor-pointer"
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
            })}
          </div>

          {filteredQuestions.length > 25 && (
            <div className="text-center pt-2 text-xs text-muted-foreground">
              Showing 25 of {filteredQuestions.length} questions. More sets available in full course papers.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
