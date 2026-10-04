"use client";

import React, { useState } from "react";
import { BrainCircuit, Loader2, FileQuestion, CheckCircle2, Sparkles, AlertCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { MathText } from "./math-text";
import { generateTopicQuestions, GeneratedQuestionItem, QuestionGenerationResponse } from "@/lib/api";

interface Props {
  topicName: string;
  courseId?: number;
  trackId?: number;
  cycle?: string;
}

export function MintAIQuestionGenerator({ topicName, courseId, trackId, cycle }: Props) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationResult, setGenerationResult] = useState<QuestionGenerationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateQuestions = async () => {
    setIsGenerating(true);
    setError(null);
    try {
      const res = await generateTopicQuestions({
        topic: topicName,
        course_id: courseId,
        track_id: trackId,
        cycle: cycle,
      });
      setGenerationResult(res);
    } catch (err: any) {
      setError(err?.message || "Failed to generate practice questions. Please try again.");
    } finally {
      setIsGenerating(false);
    }
  };

  const questions = generationResult?.questions || [];

  return (
    <div className="mt-4 pt-4 border-t border-border/50">
      {!isGenerating && questions.length === 0 && (
        <button
          onClick={handleGenerateQuestions}
          className="flex items-center gap-2 px-4 py-2.5 bg-accent/10 hover:bg-accent/20 text-accent border border-accent/20 rounded-lg text-xs font-bold uppercase tracking-wider transition-all w-full justify-center group"
        >
          <BrainCircuit className="w-4 h-4 group-hover:scale-110 transition-transform" />
          Generate Exam Practice Questions
        </button>
      )}

      {isGenerating && (
        <div className="flex flex-col items-center justify-center p-8 border border-border/50 rounded-xl bg-background/50 space-y-4">
          <Loader2 className="w-6 h-6 text-accent animate-spin" />
          <p className="text-xs font-medium text-muted-foreground text-center leading-relaxed">
            Mint AI is formulating exam-aligned practice questions for <strong className="text-foreground">{topicName}</strong>... <br/>
            Evaluating 1-mark, 4-mark, and 13-mark assessment structures.
          </p>
        </div>
      )}

      {error && (
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <AnimatePresence>
        {questions.length > 0 && generationResult && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <div className="flex items-center justify-between flex-wrap gap-2 mb-1">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider">
                {generationResult.is_synthetic ? (
                  <span className="flex items-center gap-1.5 text-amber-500">
                    <Sparkles className="w-4 h-4" />
                    Syllabus Practice (AI-Generated)
                  </span>
                ) : (
                  <span className="flex items-center gap-1.5 text-emerald-500">
                    <CheckCircle2 className="w-4 h-4" />
                    Verified Past Exam Questions
                  </span>
                )}
              </div>
              <span className="text-[10px] text-muted-foreground font-mono">
                {generationResult.evidence_count > 0
                  ? `${generationResult.evidence_count} historical matches`
                  : "Taxonomy-derived"}
              </span>
            </div>

            <div className="grid gap-3">
              {questions.map((q: GeneratedQuestionItem, i: number) => (
                <div key={i} className="flex flex-col gap-2 p-3.5 rounded-lg border border-accent/20 bg-accent/5">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-2">
                      <span className="flex items-center gap-1 text-[10px] font-bold tracking-wider text-accent uppercase">
                        <FileQuestion className="w-3 h-3" />
                        Q{i + 1} &bull; {q.type}
                      </span>
                      {q.is_synthetic ? (
                        <span className="bg-amber-500/10 text-amber-500 border border-amber-500/20 px-1.5 py-0.5 rounded text-[9px] font-semibold">
                          Synthetic Practice
                        </span>
                      ) : (
                        <span className="bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 px-1.5 py-0.5 rounded text-[9px] font-semibold">
                          Verified SRM {q.exam_year || "PYQ"}
                        </span>
                      )}
                    </div>
                    <span className="bg-background border border-border px-2 py-0.5 rounded text-[10px] font-bold text-foreground">
                      {q.marks}
                    </span>
                  </div>
                  
                  <div className="text-sm font-medium text-foreground leading-relaxed whitespace-pre-wrap">
                    <MathText content={q.text} />
                  </div>

                  {q.options && q.options.length > 0 && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
                      {q.options.map((opt: string, oIdx: number) => (
                        <div key={oIdx} className="flex items-center gap-2 p-2 rounded-md bg-background border border-border/60 text-xs text-muted-foreground">
                          <span className="font-bold text-foreground">{String.fromCharCode(65 + oIdx)}.</span>
                          <MathText content={opt} />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {generationResult.disclaimer && (
              <p className="text-[11px] text-muted-foreground italic leading-relaxed pt-1 border-t border-border/30">
                *{generationResult.disclaimer}
              </p>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
