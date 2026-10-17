"use client";

import React, { useState, useEffect } from "react";
import { MathText } from "@/components/ui/math-text";
import { getTopicHistoricalQuestions } from "@/lib/api";
import { TopicHistoricalQuestion } from "@/lib/types";
import { MintAIQuestionGenerator } from "@/components/ui/mint-ai-question-generator";
import { 
  FileCheck2, 
  Sparkles, 
  AlertCircle, 
  RotateCcw, 
  Award, 
  Calendar,
  Layers,
  ChevronDown
} from "lucide-react";

interface TopicQuestionsViewerProps {
  topicName: string;
  courseId?: number;
  courseCode?: string | null;
}

export function TopicQuestionsViewer({ topicName, courseId, courseCode }: TopicQuestionsViewerProps) {
  const [loading, setLoading] = useState<boolean>(true);
  const [questions, setQuestions] = useState<TopicHistoricalQuestion[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showAiGenerator, setShowAiGenerator] = useState<boolean>(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    getTopicHistoricalQuestions(topicName, courseId, courseCode)
      .then(res => {
        if (!active) return;
        setQuestions(res.questions || []);
        setLoading(false);
      })
      .catch(err => {
        if (!active) return;
        setError("Unable to load historical questions for this topic.");
        setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [topicName, courseId, courseCode]);

  return (
    <div className="space-y-4">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-border/40">
        <div className="flex items-center gap-2">
          <FileCheck2 className="w-4 h-4 text-emerald-500" />
          <h4 className="text-xs font-bold uppercase tracking-wider text-foreground">
            Authentic Past Exam Questions
          </h4>
          {!loading && (
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 font-semibold">
              {questions.length} Found
            </span>
          )}
        </div>

        <button
          onClick={() => setShowAiGenerator(!showAiGenerator)}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-accent hover:text-accent/80 transition-colors"
        >
          <Sparkles className="w-3.5 h-3.5" />
          {showAiGenerator ? "Hide AI Variations" : "Generate AI Variations"}
          <ChevronDown className={`w-3.5 h-3.5 transition-transform ${showAiGenerator ? "rotate-180" : ""}`} />
        </button>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="py-8 flex flex-col items-center justify-center gap-2 text-muted-foreground">
          <div className="w-5 h-5 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          <p className="text-xs">Fetching verified past paper questions...</p>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div className="p-3 rounded-lg border border-red-500/20 bg-red-500/5 text-xs text-red-600 dark:text-red-400 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Questions list */}
      {!loading && !error && (
        questions.length === 0 ? (
          <div className="p-5 text-center rounded-xl border border-dashed border-border/80 bg-muted/5 space-y-3">
            <p className="text-xs text-muted-foreground">
              No historical questions directly tagged to this topic yet in the indexed papers.
            </p>
            <p className="text-xs text-foreground font-medium">
              You can generate verified practice questions for this topic using MintAI below.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {questions.map((q, idx) => {
              const repType = q.repetition_type || "singleton";
              return (
                <div
                  key={q.id || idx}
                  className="p-4 rounded-xl border border-border/80 bg-card hover:border-accent/30 transition-all space-y-2 shadow-xs"
                >
                  {/* Badges row */}
                  <div className="flex flex-wrap items-center justify-between gap-2 text-[11px]">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-foreground bg-muted/40 px-2 py-0.5 rounded text-[10px]">
                        Q{q.question_number || idx + 1}
                      </span>
                      {q.year && (
                        <span className="inline-flex items-center gap-1 text-muted-foreground font-medium">
                          <Calendar className="w-3 h-3 opacity-60" />
                          {q.year} {q.term ? q.term : ""}
                        </span>
                      )}
                      {q.section_name && (
                        <span className="text-muted-foreground opacity-80">
                          • {q.section_name}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      {/* Repetition Badge */}
                      {repType === "exact_repeat" && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400">
                          <RotateCcw className="w-2.5 h-2.5" />
                          Exact Repeat
                        </span>
                      )}
                      {repType === "family_repeat" && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-500/10 border border-blue-500/30 text-blue-600 dark:text-blue-400">
                          <Layers className="w-2.5 h-2.5" />
                          Recurring Family
                        </span>
                      )}
                      
                      {/* Marks Badge */}
                      {q.marks !== null && q.marks !== undefined && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md font-bold text-[10px] bg-amber-500/10 border border-amber-500/20 text-amber-700 dark:text-amber-400">
                          <Award className="w-2.5 h-2.5" />
                          {q.marks} {q.marks === 1 ? "Mark" : "Marks"}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Question Text with KaTeX Rendering */}
                  <div className="text-sm text-foreground/90 leading-relaxed font-sans pt-1">
                    <MathText content={q.original_text} />
                  </div>
                </div>
              );
            })}
          </div>
        )
      )}

      {/* Expandable MintAI Variations */}
      {showAiGenerator && (
        <div className="pt-4 border-t border-border/50">
          <div className="mb-3 flex items-center gap-2 text-xs font-semibold text-accent">
            <Sparkles className="w-4 h-4" />
            <span>MintAI Synthetic Variations & Explanations</span>
          </div>
          <MintAIQuestionGenerator topicName={topicName} courseId={courseId} />
        </div>
      )}
    </div>
  );
}
