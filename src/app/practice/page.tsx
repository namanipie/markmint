"use client";

import { useState, useEffect } from "react";
import { SubjectSelector } from "@/components/subject-selector";
import { CurriculumSubject, HistoricalQuestion } from "@/lib/types";
import { getHistoricalQuestions } from "@/lib/api";
import { MathText } from "@/components/ui/math-text";
import { Loader2, ArrowRight, ArrowLeft, RefreshCw, Layers } from "lucide-react";

export default function PracticePage() {
  const [selectedSubject, setSelectedSubject] = useState<CurriculumSubject | null>(null);
  const [questions, setQuestions] = useState<HistoricalQuestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  
  // Practice state
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);

  useEffect(() => {
    if (!selectedSubject?.course_id || selectedSubject.status !== "MATCHED" || !selectedSubject.has_exams) {
      setQuestions([]);
      return;
    }

    let active = true;
    setIsLoading(true);
    
    getHistoricalQuestions(selectedSubject.course_id, undefined, undefined, 50)
      .then(res => {
        if (active) {
          // Shuffle questions for practice
          const shuffled = [...(res.questions || [])].sort(() => 0.5 - Math.random());
          setQuestions(shuffled);
          setCurrentIndex(0);
          setShowAnswer(false);
        }
      })
      .catch(console.error)
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => { active = false; };
  }, [selectedSubject]);

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(curr => curr + 1);
      setShowAnswer(false);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(curr => curr - 1);
      setShowAnswer(false);
    }
  };

  const currentQ = questions[currentIndex];

  return (
    <div className="flex flex-col gap-8 pb-20 min-h-[calc(100vh-8rem)]">
      {/* Header Context */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-border/50">
        <div className="space-y-4">
          <div>
            <h1 className="text-3xl font-black text-foreground tracking-tight">Practice</h1>
            <p className="text-muted-foreground mt-1">Test your knowledge against real historical exam questions.</p>
          </div>
          <SubjectSelector 
            selectedSubject={selectedSubject} 
            onSelect={(subj) => setSelectedSubject(subj)} 
          />
        </div>
      </div>

      {!selectedSubject ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center text-muted-foreground">
          <p>Select a subject to start practicing.</p>
        </div>
      ) : isLoading ? (
        <div className="flex-1 flex flex-col items-center justify-center gap-4 text-muted-foreground bg-card rounded-3xl border border-border">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="font-medium tracking-widest uppercase text-sm">Loading Question Bank...</p>
        </div>
      ) : questions.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center text-muted-foreground bg-card rounded-3xl border border-border">
          <Layers className="w-10 h-10 mb-4 opacity-20" />
          <p>No questions available for this subject.</p>
        </div>
      ) : (
        <div className="flex-1 flex flex-col max-w-3xl mx-auto w-full">
          <div className="flex items-center justify-between mb-6">
            <span className="text-sm font-bold text-muted-foreground uppercase tracking-wider">
              Question {currentIndex + 1} of {questions.length}
            </span>
            <div className="flex gap-2">
              <button 
                onClick={handlePrev}
                disabled={currentIndex === 0}
                className="p-2 rounded-lg bg-secondary text-muted-foreground disabled:opacity-30 hover:bg-secondary/80 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <button 
                onClick={handleNext}
                disabled={currentIndex === questions.length - 1}
                className="p-2 rounded-lg bg-secondary text-muted-foreground disabled:opacity-30 hover:bg-secondary/80 transition-colors"
              >
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          </div>

          <div className="bg-card rounded-3xl p-8 md:p-12 border border-border shadow-sm min-h-[300px] flex flex-col">
            <div className="flex justify-between items-start mb-8">
              {currentQ.marks && (
                <span className="text-xs font-bold bg-secondary px-3 py-1.5 rounded-lg">{currentQ.marks} Marks</span>
              )}
              {currentQ.source_document_title && (
                <span className="text-[11px] font-medium text-muted-foreground">{currentQ.source_document_title}</span>
              )}
            </div>
            
            <div className="text-xl md:text-2xl leading-relaxed font-medium mb-12 flex-1">
              <MathText content={currentQ.original_text} />
            </div>

            <div className="pt-8 border-t border-border/50 flex flex-col sm:flex-row gap-4 justify-between items-center mt-auto">
              {currentQ.mapped_topic_name && (
                <div className="text-sm text-muted-foreground">
                  <span className="font-bold">Topic:</span> {currentQ.mapped_topic_name}
                </div>
              )}
              
              <button
                onClick={() => setShowAnswer(!showAnswer)}
                className="px-6 py-3 rounded-xl font-bold bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-sm w-full sm:w-auto"
              >
                {showAnswer ? "Hide Notes" : "Reveal Notes"}
              </button>
            </div>
            
            {showAnswer && (
              <div className="mt-8 p-6 bg-secondary/50 rounded-2xl border border-border/50 animate-in fade-in slide-in-from-top-4 duration-300">
                <h4 className="text-sm font-bold uppercase tracking-wider text-muted-foreground mb-2">Study Notes</h4>
                <p className="text-sm text-foreground/80">
                  This question tests your understanding of {currentQ.mapped_topic_name || "the core concepts"}. 
                  Make sure to outline your answer clearly, state any assumptions, and provide step-by-step mathematical proofs if applicable.
                </p>
                {/* Real answers aren't in the DB, so we provide AI-like context here */}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
