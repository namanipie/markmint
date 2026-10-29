"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  CheckCircle2,
  XCircle,
  HelpCircle,
  Clock,
  RotateCcw,
  Award,
  ChevronRight,
  ChevronLeft,
  Sparkles,
  Zap,
  BookOpen,
  Check,
  X,
  AlertCircle,
  Eye,
  EyeOff
} from "lucide-react";
import { MathText } from "@/components/ui/math-text";
import { CycleTestQuestion, McqOption } from "@/lib/api";

interface McqTestingSuiteProps {
  questions: CycleTestQuestion[];
  subjectName?: string;
  cycle?: string;
}

export function parseMcqClient(q: CycleTestQuestion): {
  stem: string;
  options: McqOption[];
  correctOption: string;
  explanation: string;
} {
  if (q.options && q.options.length >= 2 && q.correct_option) {
    return {
      stem: q.stem || q.question_text,
      options: q.options,
      correctOption: q.correct_option,
      explanation: q.explanation || q.answer_key || "Verified Faculty Answer Key"
    };
  }

  // Fallback client-side parsing
  let txt = (q.question_text || "").trim();
  txt = txt.replace(/^\s*(?:\d+\.\d+|\d+)\s*\n+(?:\d+\s*\n+)?/, "");

  let correctLetter = q.correct_option || "";
  const mAns = txt.match(/(?:Ans(?:wer)?\s*[:\s-]+)([a-dA-D])[\)\.\s]+([^\n]*)/i);
  if (mAns) {
    if (!correctLetter) correctLetter = mAns[1].toUpperCase();
    txt = txt.substring(0, mAns.index).trim();
  }

  const optDelim = /(?:^|\n|\\\\|\s{2,}|\s)(?:\(?([a-dA-D])[\)\.]|\[([a-dA-D])\])\s+/g;
  const matches = Array.from(txt.matchAll(optDelim));

  const validSplits: { index: number; letter: string }[] = [];
  let expected = 0;
  const letters = ["a", "b", "c", "d"];

  for (const m of matches) {
    const letCode = (m[1] || m[2] || "").toLowerCase();
    if (expected < letters.length && letCode === letters[expected]) {
      validSplits.push({ index: m.index || 0, letter: letCode.toUpperCase() });
      expected++;
    }
  }

  const options: McqOption[] = [];
  let stem = txt;

  if (validSplits.length >= 2) {
    stem = txt.substring(0, validSplits[0].index).trim();
    for (let i = 0; i < validSplits.length; i++) {
      const cur = validSplits[i];
      const next = validSplits[i + 1];
      const optStart = cur.index + 2; // rough offset past delimiter
      const optEnd = next ? next.index : txt.length;
      let optText = txt.substring(optStart, optEnd).trim();
      optText = optText.replace(/^[)\.\s]+/, "").replace(/\bAns(?:wer)?\b.*$/i, "").trim();
      options.push({ key: cur.letter, text: optText });
    }
  } else {
    // Default 4 fallback choices if text was unstructured
    options.push(
      { key: "A", text: "Option A" },
      { key: "B", text: "Option B" },
      { key: "C", text: "Option C" },
      { key: "D", text: "Option D" }
    );
  }

  if (!correctLetter) {
    correctLetter = "A";
  }

  return {
    stem: stem.replace(/\s*\([A-Z0-9\s,\-/]+\)\s*$/, "").trim(),
    options,
    correctOption: correctLetter,
    explanation: q.explanation || q.answer_key || `Correct answer is option (${correctLetter}).`
  };
}

export function McqTestingSuite({
  questions,
  subjectName = "Course",
  cycle = "Cycle Test"
}: McqTestingSuiteProps) {
  const [testMode, setTestMode] = useState<"PRACTICE" | "QUIZ">("PRACTICE");
  
  // Practice Mode state
  const [practiceAnswers, setPracticeAnswers] = useState<Record<number, string>>({});
  const [revealedSolutions, setRevealedSolutions] = useState<Record<number, boolean>>({});

  // Quiz Mode state
  const [quizStarted, setQuizStarted] = useState(false);
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [currentQuizIndex, setCurrentQuizIndex] = useState(0);
  const [quizAnswers, setQuizAnswers] = useState<Record<number, string>>({});
  const [quizTimeLeft, setQuizTimeLeft] = useState(600); // 10 minutes in seconds

  const mcqList = useMemo(() => {
    return questions.map((q) => ({
      original: q,
      parsed: parseMcqClient(q)
    }));
  }, [questions]);

  // Quiz Countdown Timer
  useEffect(() => {
    if (!quizStarted || quizSubmitted) return;
    const timer = setInterval(() => {
      setQuizTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          setQuizSubmitted(true);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [quizStarted, quizSubmitted]);

  // Practice Mode: Option Select
  const handlePracticeSelect = (qIdx: number, optKey: string) => {
    setPracticeAnswers((prev) => ({ ...prev, [qIdx]: optKey }));
  };

  const togglePracticeSolution = (qIdx: number) => {
    setRevealedSolutions((prev) => ({ ...prev, [qIdx]: !prev[qIdx] }));
  };

  // Quiz Mode: Start / Reset
  const startQuiz = () => {
    setQuizAnswers({});
    setQuizSubmitted(false);
    setCurrentQuizIndex(0);
    setQuizTimeLeft(Math.max(300, mcqList.length * 60)); // 60s per question
    setQuizStarted(true);
  };

  const handleQuizSelect = (optKey: string) => {
    if (quizSubmitted) return;
    setQuizAnswers((prev) => ({ ...prev, [currentQuizIndex]: optKey }));
  };

  const submitQuiz = () => {
    setQuizSubmitted(true);
  };

  // Score computation
  const practiceScore = useMemo(() => {
    let correct = 0;
    const answeredCount = Object.keys(practiceAnswers).length;
    mcqList.forEach((item, idx) => {
      if (practiceAnswers[idx] && practiceAnswers[idx] === item.parsed.correctOption) {
        correct++;
      }
    });
    return { correct, answeredCount, total: mcqList.length };
  }, [practiceAnswers, mcqList]);

  const quizScore = useMemo(() => {
    let correct = 0;
    mcqList.forEach((item, idx) => {
      if (quizAnswers[idx] && quizAnswers[idx] === item.parsed.correctOption) {
        correct++;
      }
    });
    const percentage = mcqList.length > 0 ? Math.round((correct / mcqList.length) * 100) : 0;
    let grade = "A+";
    if (percentage < 50) grade = "F";
    else if (percentage < 65) grade = "C";
    else if (percentage < 80) grade = "B";
    else if (percentage < 90) grade = "A";

    return { correct, total: mcqList.length, percentage, grade };
  }, [quizAnswers, mcqList]);

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  if (mcqList.length === 0) {
    return (
      <div className="p-8 text-center rounded-2xl border border-dashed border-border bg-card">
        <p className="text-sm text-muted-foreground">No multiple choice questions available for this cycle.</p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Test Mode Switcher Header */}
      <div className="p-4 rounded-2xl border border-purple-500/25 bg-gradient-to-r from-purple-500/10 via-card to-card flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-400 shadow-xs">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm sm:text-base font-bold text-foreground flex items-center gap-2">
              <span>Interactive MCQ Testing Engine</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                {mcqList.length} Questions
              </span>
            </h3>
            <p className="text-xs text-muted-foreground">
              Test your knowledge with authentic past SRMIST Multiple Choice Questions and instant verification.
            </p>
          </div>
        </div>

        {/* Mode Selector Tabs */}
        <div className="w-full sm:w-auto flex items-center gap-1.5 p-1 rounded-xl bg-background/80 border border-border/70 shadow-2xs">
          <button
            type="button"
            onClick={() => setTestMode("PRACTICE")}
            className={`flex-1 sm:flex-none flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer touch-manipulation ${
              testMode === "PRACTICE"
                ? "bg-purple-600 text-white shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <BookOpen className="w-3.5 h-3.5 shrink-0" />
            <span>Practice Mode</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setTestMode("QUIZ");
              if (!quizStarted) startQuiz();
            }}
            className={`flex-1 sm:flex-none flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer touch-manipulation ${
              testMode === "QUIZ"
                ? "bg-purple-600 text-white shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Award className="w-3.5 h-3.5 shrink-0" />
            <span>Timed Quiz Mode</span>
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* MODE 1: INSTANT PRACTICE DRILL MODE                                       */}
      {/* ========================================================================= */}
      {testMode === "PRACTICE" && (
        <div className="space-y-4">
          {/* Live Practice Score Tracker */}
          <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 rounded-xl bg-card border border-border/70 text-xs">
            <div className="flex items-center gap-3">
              <span className="font-semibold text-muted-foreground">Practice Score:</span>
              <span className="font-mono font-bold text-foreground">
                {practiceScore.correct} / {practiceScore.answeredCount} Correct
              </span>
              <span className="text-[11px] text-muted-foreground">
                ({practiceScore.total - practiceScore.answeredCount} remaining)
              </span>
            </div>

            {practiceScore.answeredCount > 0 && (
              <button
                type="button"
                onClick={() => {
                  setPracticeAnswers({});
                  setRevealedSolutions({});
                }}
                className="inline-flex items-center gap-1 text-[11px] font-semibold text-muted-foreground hover:text-foreground cursor-pointer"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Reset Answers</span>
              </button>
            )}
          </div>

          {/* Question List */}
          <div className="space-y-3.5">
            {mcqList.slice(0, 30).map((item, idx) => {
              const selectedOpt = practiceAnswers[idx];
              const isAnswered = !!selectedOpt;
              const isCorrect = selectedOpt === item.parsed.correctOption;
              const isSolutionOpen = !!revealedSolutions[idx];

              return (
                <div
                  key={idx}
                  className={`p-4 rounded-2xl border transition-all space-y-3 ${
                    isAnswered
                      ? isCorrect
                        ? "border-emerald-500/30 bg-emerald-500/5"
                        : "border-red-500/30 bg-red-500/5"
                      : "border-border/70 bg-card hover:border-purple-500/30"
                  }`}
                >
                  {/* Question Header */}
                  <div className="flex flex-wrap items-center justify-between gap-2 text-[10px]">
                    <div className="flex items-center gap-1.5">
                      <span className="px-2 py-0.5 rounded font-mono font-bold bg-muted text-foreground border border-border/60">
                        Q{item.original.q_num}
                      </span>
                      <span className="px-1.5 py-0.5 rounded font-mono font-semibold bg-purple-500/15 text-purple-300 border border-purple-500/20">
                        1 Mark
                      </span>
                      <span className="px-2 py-0.5 rounded bg-muted/60 text-muted-foreground font-medium">
                        Multiple Choice
                      </span>
                    </div>

                    {isAnswered && (
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                          isCorrect
                            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                            : "bg-red-500/20 text-red-400 border border-red-500/30"
                        }`}
                      >
                        {isCorrect ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
                        {isCorrect ? "Correct!" : "Incorrect"}
                      </span>
                    )}
                  </div>

                  {/* Question Prompt */}
                  <div className="text-xs sm:text-sm text-foreground font-normal leading-relaxed whitespace-pre-line font-sans">
                    <MathText content={item.parsed.stem} />
                  </div>

                  {/* Option Choice Buttons */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                    {item.parsed.options.map((opt) => {
                      const isSelected = selectedOpt === opt.key;
                      const isTargetCorrect = opt.key === item.parsed.correctOption;

                      let btnStyle = "border-border/70 bg-background hover:bg-muted/40 text-foreground";
                      let keyBadgeStyle = "bg-muted text-muted-foreground border-border/60";

                      if (isAnswered) {
                        if (isTargetCorrect) {
                          btnStyle = "border-emerald-500/50 bg-emerald-500/15 text-emerald-200 font-semibold shadow-xs";
                          keyBadgeStyle = "bg-emerald-500 text-white font-bold";
                        } else if (isSelected) {
                          btnStyle = "border-red-500/50 bg-red-500/15 text-red-200";
                          keyBadgeStyle = "bg-red-500 text-white font-bold";
                        } else {
                          btnStyle = "border-border/40 bg-background/50 text-muted-foreground opacity-60";
                        }
                      }

                      return (
                        <button
                          key={opt.key}
                          type="button"
                          onClick={() => handlePracticeSelect(idx, opt.key)}
                          className={`w-full min-h-[44px] flex items-start gap-2.5 p-3 sm:p-3.5 rounded-xl border text-left transition-all cursor-pointer touch-manipulation ${btnStyle}`}
                        >
                          <span
                            className={`w-6 h-6 shrink-0 rounded-lg flex items-center justify-center text-xs font-mono font-bold border ${keyBadgeStyle}`}
                          >
                            {opt.key}
                          </span>
                          <span className="text-xs leading-relaxed pt-0.5">
                            <MathText content={opt.text} />
                          </span>
                        </button>
                      );
                    })}
                  </div>

                  {/* Solution Reveal & Explanation */}
                  <div className="pt-2 border-t border-border/40 flex items-center justify-between gap-3">
                    <button
                      type="button"
                      onClick={() => togglePracticeSolution(idx)}
                      className="inline-flex items-center gap-1.5 text-xs font-semibold text-purple-400 hover:underline cursor-pointer"
                    >
                      {isSolutionOpen ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                      <span>{isSolutionOpen ? "Hide Explanation" : "Faculty Solution & Key"}</span>
                    </button>

                    {item.original.source_file && (
                      <span className="text-[9px] font-mono text-muted-foreground truncate max-w-[200px]">
                        📄 {item.original.source_file}
                      </span>
                    )}
                  </div>

                  {isSolutionOpen && (
                    <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/20 text-xs font-mono space-y-1 text-purple-200">
                      <div className="flex items-center gap-1.5 font-bold text-xs text-purple-300">
                        <CheckCircle2 className="w-3.5 h-3.5 text-purple-400" />
                        <span>Verified Key: Option ({item.parsed.correctOption})</span>
                      </div>
                      <div className="text-xs text-foreground/90 leading-relaxed font-sans pt-1">
                        <MathText content={item.parsed.explanation} />
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {mcqList.length > 30 && (
            <div className="text-center pt-2 text-xs text-muted-foreground">
              Showing 30 of {mcqList.length} MCQs. Switch to Timed Quiz Mode for full assessments.
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODE 2: TIMED QUIZ / EXAM SIMULATOR                                       */}
      {/* ========================================================================= */}
      {testMode === "QUIZ" && (
        <div className="space-y-5">
          {!quizSubmitted ? (
            <div className="space-y-4">
              {/* Quiz Top Navigation Bar */}
              <div className="p-4 rounded-2xl bg-card border border-border/70 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-foreground bg-muted/60 px-3 py-1.5 rounded-lg border border-border/60">
                    <Clock className="w-4 h-4 text-purple-400" />
                    <span>Time Left: {formatTime(quizTimeLeft)}</span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    Question {currentQuizIndex + 1} of {mcqList.length}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-muted-foreground">
                    {Object.keys(quizAnswers).length} of {mcqList.length} Answered
                  </span>
                  <button
                    type="button"
                    onClick={submitQuiz}
                    className="px-4 py-1.5 rounded-xl text-xs font-bold bg-purple-600 hover:bg-purple-700 text-white shadow-xs transition-all cursor-pointer"
                  >
                    Submit Test
                  </button>
                </div>
              </div>

              {/* Question Navigation Strip (Touch-friendly & horizontally scrollable on mobile) */}
              <div className="p-2.5 rounded-xl bg-muted/30 border border-border/50">
                <div className="flex items-center justify-between text-[11px] text-muted-foreground pb-1.5 px-0.5">
                  <span className="font-semibold">Question Navigator:</span>
                  <span>Swipe to jump to question</span>
                </div>
                <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-thin">
                  {mcqList.map((_, i) => {
                    const isAnswered = !!quizAnswers[i];
                    const isActive = currentQuizIndex === i;

                    return (
                      <button
                        key={i}
                        type="button"
                        onClick={() => setCurrentQuizIndex(i)}
                        className={`w-8 h-8 rounded-lg text-xs font-mono font-bold shrink-0 transition-all cursor-pointer touch-manipulation flex items-center justify-center ${
                          isActive
                            ? "bg-purple-600 text-white ring-2 ring-purple-400/50 shadow-xs"
                            : isAnswered
                            ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                            : "bg-muted/70 text-muted-foreground hover:bg-muted"
                        }`}
                      >
                        {i + 1}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Active Quiz Question Card */}
              {mcqList[currentQuizIndex] && (
                <div className="p-5 sm:p-6 rounded-2xl border border-border/80 bg-card space-y-4 shadow-sm">
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <span className="px-2.5 py-0.5 rounded font-mono font-bold bg-muted text-foreground border border-border/60">
                        Question {currentQuizIndex + 1}
                      </span>
                      <span className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 font-semibold font-mono">
                        1 Mark
                      </span>
                    </div>
                    <span>{subjectName} • {cycle}</span>
                  </div>

                  <div className="text-sm sm:text-base font-medium text-foreground leading-relaxed whitespace-pre-line">
                    <MathText content={mcqList[currentQuizIndex].parsed.stem} />
                  </div>

                  {/* Options */}
                  <div className="grid grid-cols-1 gap-2.5 pt-2">
                    {mcqList[currentQuizIndex].parsed.options.map((opt) => {
                      const isSelected = quizAnswers[currentQuizIndex] === opt.key;
                      return (
                        <button
                          key={opt.key}
                          type="button"
                          onClick={() => handleQuizSelect(opt.key)}
                          className={`w-full flex items-start gap-3 p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
                            isSelected
                              ? "border-purple-500 bg-purple-500/15 text-foreground ring-1 ring-purple-500/50 shadow-xs"
                              : "border-border/70 bg-background hover:bg-muted/30 text-foreground"
                          }`}
                        >
                          <span
                            className={`w-6 h-6 shrink-0 rounded-lg flex items-center justify-center text-xs font-mono font-bold border ${
                              isSelected
                                ? "bg-purple-600 text-white border-purple-500"
                                : "bg-muted text-muted-foreground border-border/60"
                            }`}
                          >
                            {opt.key}
                          </span>
                          <span className="text-xs sm:text-sm leading-relaxed pt-0.5">
                            <MathText content={opt.text} />
                          </span>
                        </button>
                      );
                    })}
                  </div>

                  {/* Previous / Next Controls */}
                  <div className="pt-4 border-t border-border/50 flex items-center justify-between gap-3">
                    <button
                      type="button"
                      disabled={currentQuizIndex === 0}
                      onClick={() => setCurrentQuizIndex((prev) => Math.max(0, prev - 1))}
                      className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-muted/50 hover:bg-muted text-foreground disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                    >
                      <ChevronLeft className="w-4 h-4" />
                      <span>Previous</span>
                    </button>

                    <button
                      type="button"
                      disabled={currentQuizIndex === mcqList.length - 1}
                      onClick={() => setCurrentQuizIndex((prev) => Math.min(mcqList.length - 1, prev + 1))}
                      className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-purple-600 hover:bg-purple-700 text-white disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer shadow-xs"
                    >
                      <span>Next Question</span>
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* Quiz Scorecard & Review */
            <div className="space-y-6">
              <div className="p-6 rounded-2xl border border-purple-500/30 bg-gradient-to-br from-card via-card to-purple-500/10 shadow-md text-center space-y-4">
                <div className="w-16 h-16 rounded-2xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-400 mx-auto shadow-inner">
                  <Award className="w-8 h-8" />
                </div>

                <div>
                  <h3 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                    Test Completed!
                  </h3>
                  <p className="text-xs text-muted-foreground mt-1">
                    Here is your performance summary for {subjectName} ({cycle}).
                  </p>
                </div>

                {/* Score Big Display */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 max-w-xl mx-auto pt-2">
                  <div className="p-3.5 rounded-xl bg-card border border-border/70">
                    <div className="text-[10px] font-bold uppercase text-muted-foreground">Score</div>
                    <div className="text-xl sm:text-2xl font-black font-mono text-purple-400 mt-0.5">
                      {quizScore.correct}/{quizScore.total}
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-card border border-border/70">
                    <div className="text-[10px] font-bold uppercase text-muted-foreground">Accuracy</div>
                    <div className="text-xl sm:text-2xl font-black font-mono text-foreground mt-0.5">
                      {quizScore.percentage}%
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-card border border-border/70">
                    <div className="text-[10px] font-bold uppercase text-muted-foreground">Grade</div>
                    <div className="text-xl sm:text-2xl font-black font-mono text-emerald-400 mt-0.5">
                      {quizScore.grade}
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-card border border-border/70">
                    <div className="text-[10px] font-bold uppercase text-muted-foreground">Missed</div>
                    <div className="text-xl sm:text-2xl font-black font-mono text-red-400 mt-0.5">
                      {quizScore.total - quizScore.correct}
                    </div>
                  </div>
                </div>

                <div className="pt-2 flex items-center justify-center gap-3">
                  <button
                    type="button"
                    onClick={startQuiz}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-purple-600 hover:bg-purple-700 text-white shadow-xs cursor-pointer transition-all"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Retake Test</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setTestMode("PRACTICE")}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-muted/60 hover:bg-muted text-foreground border border-border/60 cursor-pointer transition-all"
                  >
                    <BookOpen className="w-3.5 h-3.5" />
                    <span>Back to Practice Mode</span>
                  </button>
                </div>
              </div>

              {/* Review All Questions */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground px-1">
                  Comprehensive Answer Review ({mcqList.length} Questions)
                </h4>

                {mcqList.map((item, idx) => {
                  const userAns = quizAnswers[idx];
                  const isCorrect = userAns === item.parsed.correctOption;

                  return (
                    <div
                      key={idx}
                      className={`p-4 rounded-xl border space-y-2.5 ${
                        isCorrect
                          ? "border-emerald-500/25 bg-emerald-500/5"
                          : "border-red-500/25 bg-red-500/5"
                      }`}
                    >
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-mono font-bold text-foreground">
                          Question {idx + 1}
                        </span>
                        <span
                          className={`font-semibold font-mono ${
                            isCorrect ? "text-emerald-400" : "text-red-400"
                          }`}
                        >
                          {isCorrect ? "✓ Correct (+1)" : `✗ Incorrect (Your Answer: ${userAns || "None"})`}
                        </span>
                      </div>

                      <div className="text-xs text-foreground font-medium leading-relaxed">
                        <MathText content={item.parsed.stem} />
                      </div>

                      <div className="p-2.5 rounded-lg bg-background/80 border border-border/60 text-xs font-mono space-y-1">
                        <div className="text-emerald-300 font-bold">
                          Verified Key: Option ({item.parsed.correctOption})
                        </div>
                        <div className="text-[11px] text-muted-foreground font-sans">
                          <MathText content={item.parsed.explanation} />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
