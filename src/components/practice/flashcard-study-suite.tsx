"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import {
  Sparkles,
  RotateCw,
  ChevronLeft,
  ChevronRight,
  Shuffle,
  RotateCcw,
  Plus,
  CheckCircle2,
  HelpCircle,
  Award,
  Layers,
  BookOpen,
  Filter,
  Check,
  X,
  Volume2
} from "lucide-react";
import { CourseCatalogItem, HighYieldTopicItem } from "@/lib/courses";
import { HistoricalQuestion } from "@/lib/types";
import { MathText } from "@/components/ui/math-text";

export interface FlashcardItem {
  id: string;
  unit: number;
  topic: string;
  question: string;
  answer: string;
  keyPoints?: string[];
  examTip?: string;
  isCustom?: boolean;
}

type LeitnerBox = 1 | 2 | 3; // 1: Learning/Hard, 2: Reviewing/Medium, 3: Mastered

interface FlashcardStudySuiteProps {
  course: CourseCatalogItem;
  pyqs?: HistoricalQuestion[];
  initialUnit?: string;
}

export function FlashcardStudySuite({
  course,
  pyqs = [],
  initialUnit = "ALL"
}: FlashcardStudySuiteProps) {
  // Storage key for Leitner box state
  const storageKey = `markmint_flashcards_v1_${course.slug}`;

  // Default seed generation based on course high-yield topics & units
  const seedCards: FlashcardItem[] = useMemo(() => {
    const list: FlashcardItem[] = [];

    // 1. From High-Yield Topics
    if (course.highYieldTopics && course.highYieldTopics.length > 0) {
      course.highYieldTopics.forEach((t: HighYieldTopicItem, idx: number) => {
        list.push({
          id: `hyt-${idx}`,
          unit: t.unitNumber || 1,
          topic: t.topic,
          question: `What are the core principles and exam definitions associated with "${t.topic}"?`,
          answer: `**${t.topic}** is a high-recurrence exam concept in Unit ${t.unitNumber}. Ensure you are prepared to state definitions, derive formulas, and solve standard numerical variations.`,
          keyPoints: [
            `Appeared across ${t.paperCount} recent exam papers (${t.questionCount} questions).`,
            `Key mathematical formulation and standard boundary conditions.`,
            `Common exam trap: Missing intermediate steps or units.`
          ],
          examTip: `High-yield topic: Master the standard 8-mark or 16-mark derivation for full credit.`
        });
      });
    }

    // 2. From Course Units
    if (course.units && course.units.length > 0) {
      course.units.forEach((u) => {
        if (u.topics && u.topics.length > 0) {
          u.topics.slice(0, 3).forEach((topicStr, topicIdx) => {
            const cardId = `unit-${u.number}-${topicIdx}`;
            if (!list.some((c) => c.topic.toLowerCase() === topicStr.toLowerCase())) {
              list.push({
                id: cardId,
                unit: u.number,
                topic: topicStr,
                question: `Explain the fundamental concept of "${topicStr}" in Unit ${u.number} (${u.name}).`,
                answer: `In **${u.name}**, understanding **${topicStr}** is essential for answering Section B analytical problems and Section A conceptual definitions.`,
                keyPoints: [
                  `Foundational module in ${u.name}.`,
                  `Frequently tested in Cycle Tests (CT1/CT2) and End Semester examinations.`,
                  `Review typical lecture examples and standard formula sheets.`
                ],
                examTip: `Always state assumptions clearly when deriving or computing values for ${topicStr}.`
              });
            }
          });
        }
      });
    }

    // 3. From sample PYQs if available
    if (pyqs.length > 0) {
      pyqs.slice(0, 10).forEach((q, idx) => {
        if (q.original_text && q.original_text.length < 280) {
          list.push({
            id: `pyq-${q.id || idx}`,
            unit: (idx % 5) + 1,
            topic: q.family_name || (Array.isArray(q.topics) ? q.topics[0] : "Exam Question"),
            question: q.original_text,
            answer: `This was an authentic SRM assessment problem from **${q.source_document_title || "Past Year Paper"}**. Review the standard marking scheme for step credits.`,
            keyPoints: [
              `Weightage: ~${q.marks || 8} Marks`,
              `Question Family: ${q.family_name || "Standard Core"}`,
              `Practice writing clean equations and diagrams.`
            ],
            examTip: `Marks are allocated for initial formula statement, substitution, and final boxed answer with units.`
          });
        }
      });
    }

    // Fallback if empty
    if (list.length === 0) {
      list.push({
        id: "fallback-1",
        unit: 1,
        topic: course.name,
        question: `What are the primary learning outcomes for ${course.name}?`,
        answer: `Master the foundational concepts across all 5 units, practice recurring previous year questions, and test yourself with timed problem sets.`,
        keyPoints: [`5 Course Units`, `3 Continuous Assessments (CTs)`, `1 Comprehensive End Semester Exam`],
        examTip: `Focus on high-recurrence topics identified in MarkMint Exam DNA.`
      });
    }

    return list;
  }, [course, pyqs]);

  // Card deck state
  const [cards, setCards] = useState<FlashcardItem[]>(seedCards);
  const [boxState, setBoxState] = useState<Record<string, LeitnerBox>>({});
  const [selectedUnit, setSelectedUnit] = useState<string>(initialUnit);
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [isFlipped, setIsFlipped] = useState<boolean>(false);
  const [isAddingCard, setIsAddingCard] = useState<boolean>(false);

  // New card form
  const [newTopic, setNewTopic] = useState("");
  const [newUnit, setNewUnit] = useState<number>(1);
  const [newQuestion, setNewQuestion] = useState("");
  const [newAnswer, setNewAnswer] = useState("");
  const [newExamTip, setNewExamTip] = useState("");

  // Load box state from localStorage
  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        setBoxState(JSON.parse(saved));
      }
      const savedCustom = localStorage.getItem(`${storageKey}_custom`);
      if (savedCustom) {
        const customCards: FlashcardItem[] = JSON.parse(savedCustom);
        setCards((prev) => [...prev, ...customCards]);
      }
    } catch {
      // ignore JSON errors
    }
  }, [storageKey]);

  // Save box state to localStorage
  const saveBoxState = (newState: Record<string, LeitnerBox>) => {
    setBoxState(newState);
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem(storageKey, JSON.stringify(newState));
      } catch {
        // quota exceeded
      }
    }
  };

  // Filtered cards based on Unit
  const filteredCards = useMemo(() => {
    if (selectedUnit === "ALL") return cards;
    const uNum = parseInt(selectedUnit, 10);
    return cards.filter((c) => c.unit === uNum);
  }, [cards, selectedUnit]);

  // Reset current index when filter changes
  useEffect(() => {
    setCurrentIndex(0);
    setIsFlipped(false);
  }, [selectedUnit]);

  const activeCard: FlashcardItem | undefined = filteredCards[currentIndex];

  // Leitner Statistics
  const stats = useMemo(() => {
    let box1 = 0;
    let box2 = 0;
    let box3 = 0;
    filteredCards.forEach((c) => {
      const b = boxState[c.id] || 1;
      if (b === 1) box1++;
      else if (b === 2) box2++;
      else if (b === 3) box3++;
    });
    const total = filteredCards.length || 1;
    const masteryPct = Math.round((box3 / total) * 100);
    return { box1, box2, box3, total: filteredCards.length, masteryPct };
  }, [filteredCards, boxState]);

  // Actions
  const handleFlip = useCallback(() => {
    setIsFlipped((prev) => !prev);
  }, []);

  const handleNext = useCallback(() => {
    if (currentIndex < filteredCards.length - 1) {
      setCurrentIndex((prev) => prev + 1);
      setIsFlipped(false);
    }
  }, [currentIndex, filteredCards.length]);

  const handlePrev = useCallback(() => {
    if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
      setIsFlipped(false);
    }
  }, [currentIndex]);

  const handleRateCard = useCallback(
    (rating: LeitnerBox) => {
      if (!activeCard) return;
      const updated = { ...boxState, [activeCard.id]: rating };
      saveBoxState(updated);
      handleNext();
    },
    [activeCard, boxState, handleNext]
  );

  const handleShuffle = () => {
    setCards((prev) => {
      const shuffled = [...prev];
      for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
      }
      return shuffled;
    });
    setCurrentIndex(0);
    setIsFlipped(false);
  };

  const handleResetProgress = () => {
    if (confirm("Reset Leitner mastery progress for this course?")) {
      saveBoxState({});
      setCurrentIndex(0);
      setIsFlipped(false);
    }
  };

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (isAddingCard) return;
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      if (e.code === "Space") {
        e.preventDefault();
        handleFlip();
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        handleNext();
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        handlePrev();
      } else if (e.key === "1") {
        handleRateCard(1);
      } else if (e.key === "2") {
        handleRateCard(2);
      } else if (e.key === "3") {
        handleRateCard(3);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleFlip, handleNext, handlePrev, handleRateCard, isAddingCard]);

  // Create custom card
  const handleSaveCustomCard = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newQuestion.trim() || !newAnswer.trim()) return;

    const newCard: FlashcardItem = {
      id: `custom-${Date.now()}`,
      unit: newUnit,
      topic: newTopic.trim() || `Unit ${newUnit} Custom`,
      question: newQuestion.trim(),
      answer: newAnswer.trim(),
      examTip: newExamTip.trim() || undefined,
      isCustom: true
    };

    const updated = [newCard, ...cards];
    setCards(updated);

    if (typeof window !== "undefined") {
      try {
        const savedCustom = localStorage.getItem(`${storageKey}_custom`);
        const existing: FlashcardItem[] = savedCustom ? JSON.parse(savedCustom) : [];
        localStorage.setItem(`${storageKey}_custom`, JSON.stringify([newCard, ...existing]));
      } catch {
        // ignore
      }
    }

    setNewTopic("");
    setNewQuestion("");
    setNewAnswer("");
    setNewExamTip("");
    setIsAddingCard(false);
    setCurrentIndex(0);
    setIsFlipped(false);
  };

  const currentBox = activeCard ? (boxState[activeCard.id] || 1) : 1;

  return (
    <div className="space-y-6">
      {/* ========================================================================= */}
      {/* HEADER CONTROLS & LEITNER STATS                                           */}
      {/* ========================================================================= */}
      <div className="p-5 rounded-2xl bg-card border border-border/80 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/50 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400">
                <Sparkles className="w-5 h-5" />
              </span>
              <h3 className="text-lg sm:text-xl font-bold tracking-tight text-foreground">
                AI Leitner Flashcard Deck
              </h3>
            </div>
            <p className="text-xs text-muted-foreground">
              Spaced repetition flashcards generated from high-yield topics and authentic SRM exam concepts for <strong className="text-foreground">{course.name}</strong>.
            </p>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2 flex-wrap">
            <button
              type="button"
              onClick={handleShuffle}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-secondary/80 hover:bg-secondary text-xs font-semibold text-secondary-foreground transition-colors"
              title="Shuffle Deck"
            >
              <Shuffle className="w-3.5 h-3.5" />
              Shuffle
            </button>
            <button
              type="button"
              onClick={() => setIsAddingCard(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-accent text-accent-foreground text-xs font-bold hover:bg-accent/90 transition-colors shadow-xs"
            >
              <Plus className="w-3.5 h-3.5" />
              Add Card
            </button>
            <button
              type="button"
              onClick={handleResetProgress}
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-muted-foreground hover:text-foreground text-xs font-medium transition-colors"
              title="Reset Mastery"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Leitner Box Status & Mastery Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3 rounded-xl bg-background/60 border border-border/60 flex items-center justify-between">
            <div>
              <p className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider">Overall Mastery</p>
              <p className="text-lg font-black text-foreground">{stats.masteryPct}%</p>
            </div>
            <div className="w-10 h-10 rounded-full border-2 border-indigo-500/30 flex items-center justify-center font-mono font-bold text-xs text-indigo-400">
              {stats.box3}/{stats.total}
            </div>
          </div>

          <div className="p-3 rounded-xl bg-rose-500/5 border border-rose-500/20 flex items-center justify-between">
            <div>
              <p className="text-[10px] uppercase font-bold text-rose-400 tracking-wider">Box 1: Needs Work</p>
              <p className="text-lg font-black text-rose-500">{stats.box1}</p>
            </div>
            <span className="text-xs font-mono text-rose-400/80 px-2 py-0.5 rounded bg-rose-500/10">Key 1</span>
          </div>

          <div className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/20 flex items-center justify-between">
            <div>
              <p className="text-[10px] uppercase font-bold text-amber-400 tracking-wider">Box 2: Reviewing</p>
              <p className="text-lg font-black text-amber-500">{stats.box2}</p>
            </div>
            <span className="text-xs font-mono text-amber-400/80 px-2 py-0.5 rounded bg-amber-500/10">Key 2</span>
          </div>

          <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/20 flex items-center justify-between">
            <div>
              <p className="text-[10px] uppercase font-bold text-emerald-400 tracking-wider">Box 3: Mastered</p>
              <p className="text-lg font-black text-emerald-500">{stats.box3}</p>
            </div>
            <span className="text-xs font-mono text-emerald-400/80 px-2 py-0.5 rounded bg-emerald-500/10">Key 3</span>
          </div>
        </div>

        {/* Unit Filter Chips */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 pt-1 scrollbar-none">
          <span className="text-xs font-semibold text-muted-foreground mr-1 flex items-center gap-1 shrink-0">
            <Filter className="w-3.5 h-3.5" /> Unit:
          </span>
          {["ALL", "1", "2", "3", "4", "5"].map((u) => (
            <button
              key={u}
              type="button"
              onClick={() => setSelectedUnit(u)}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-all shrink-0 ${
                selectedUnit === u
                  ? "bg-accent text-accent-foreground shadow-xs"
                  : "bg-secondary/60 text-muted-foreground hover:bg-secondary hover:text-foreground"
              }`}
            >
              {u === "ALL" ? "All Units" : `Unit ${u}`}
            </button>
          ))}
          <span className="ml-auto text-xs font-mono text-muted-foreground hidden sm:inline">
            Card {filteredCards.length > 0 ? currentIndex + 1 : 0} of {filteredCards.length}
          </span>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 3D FLASHCARD INTERACTIVE CONTAINER                                        */}
      {/* ========================================================================= */}
      {filteredCards.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-card border border-border/80 space-y-3">
          <HelpCircle className="w-10 h-10 text-muted-foreground mx-auto" />
          <h4 className="font-bold text-foreground">No flashcards found for this filter</h4>
          <p className="text-xs text-muted-foreground max-w-sm mx-auto">
            Try switching to &quot;All Units&quot; or click &quot;Add Card&quot; to create a custom study card for this unit.
          </p>
          <button
            type="button"
            onClick={() => setSelectedUnit("ALL")}
            className="px-4 py-2 rounded-xl bg-accent text-accent-foreground text-xs font-bold"
          >
            Show All Units
          </button>
        </div>
      ) : activeCard ? (
        <div className="space-y-4">
          {/* Card Presentation (Perspectived Flip) */}
          <div
            onClick={handleFlip}
            className="group relative w-full min-h-[340px] sm:min-h-[380px] cursor-pointer select-none rounded-3xl transition-all duration-300 transform perspective-1000"
          >
            <div
              className={`relative w-full h-full rounded-3xl p-6 sm:p-8 border transition-all duration-500 shadow-lg ${
                isFlipped
                  ? "bg-gradient-to-br from-card via-card to-indigo-950/20 border-indigo-500/40"
                  : "bg-gradient-to-br from-card via-card to-accent/5 border-border/80 hover:border-accent/40"
              }`}
            >
              {/* Top metadata tags */}
              <div className="flex items-center justify-between gap-2 border-b border-border/40 pb-4 mb-4">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="px-2.5 py-0.5 rounded-md bg-accent/15 text-accent text-xs font-bold">
                    Unit {activeCard.unit}
                  </span>
                  <span className="px-2.5 py-0.5 rounded-md bg-secondary text-secondary-foreground text-xs font-medium max-w-[200px] truncate">
                    {activeCard.topic}
                  </span>
                  {activeCard.isCustom && (
                    <span className="px-2 py-0.5 rounded-md bg-purple-500/15 text-purple-400 text-[10px] font-bold">
                      Custom
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                      currentBox === 3
                        ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                        : currentBox === 2
                        ? "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                        : "bg-rose-500/15 text-rose-400 border border-rose-500/30"
                    }`}
                  >
                    Box {currentBox}: {currentBox === 3 ? "Mastered" : currentBox === 2 ? "Reviewing" : "Learning"}
                  </span>
                  <span className="text-xs font-mono text-muted-foreground">
                    {currentIndex + 1}/{filteredCards.length}
                  </span>
                </div>
              </div>

              {/* Card Body */}
              {!isFlipped ? (
                /* FRONT OF CARD (Question / Concept Prompt) */
                <div className="flex flex-col justify-between min-h-[220px]">
                  <div className="space-y-4">
                    <span className="text-[11px] font-black uppercase tracking-widest text-accent flex items-center gap-1.5">
                      <HelpCircle className="w-3.5 h-3.5" /> Concept &amp; Question Prompt
                    </span>
                    <div className="text-lg sm:text-xl font-bold text-foreground leading-relaxed">
                      <MathText content={activeCard.question} />
                    </div>
                  </div>

                  <div className="pt-6 flex items-center justify-between text-xs text-muted-foreground border-t border-border/30">
                    <span className="flex items-center gap-1.5">
                      <RotateCw className="w-3.5 h-3.5 text-accent animate-spin-slow" />
                      Click or press <strong className="text-foreground">Space</strong> to reveal answer
                    </span>
                    <span className="hidden sm:inline font-mono text-[11px]">
                      Use ← / → keys to navigate
                    </span>
                  </div>
                </div>
              ) : (
                /* BACK OF CARD (Detailed Explanation / Key Points / Exam Tip) */
                <div className="flex flex-col justify-between min-h-[220px] space-y-4">
                  <div className="space-y-3">
                    <span className="text-[11px] font-black uppercase tracking-widest text-emerald-400 flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Core Solution &amp; Key Points
                    </span>

                    <div className="text-sm sm:text-base text-foreground/95 leading-relaxed font-normal">
                      <MathText content={activeCard.answer} />
                    </div>

                    {activeCard.keyPoints && activeCard.keyPoints.length > 0 && (
                      <div className="pt-2 space-y-1.5">
                        <p className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider">Exam Essentials:</p>
                        <ul className="space-y-1 pl-1">
                          {activeCard.keyPoints.map((kp, kIdx) => (
                            <li key={kIdx} className="text-xs text-foreground/80 flex items-start gap-2">
                              <span className="w-1.5 h-1.5 rounded-full bg-accent mt-1.5 shrink-0" />
                              <MathText content={kp} />
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {activeCard.examTip && (
                      <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300">
                        <strong className="text-amber-200">Exam Tip:</strong> {activeCard.examTip}
                      </div>
                    )}
                  </div>

                  <div className="pt-4 flex items-center justify-between text-xs text-muted-foreground border-t border-border/30">
                    <span>Rate your confidence below to schedule spaced repetition</span>
                    <span className="font-mono text-[11px]">Click to flip back</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* ===================================================================== */}
          {/* NAVIGATION & LEITNER RATING TOOLBAR                                   */}
          {/* ===================================================================== */}
          <div className="p-4 rounded-2xl bg-card border border-border/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            {/* Card stepping */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handlePrev}
                disabled={currentIndex === 0}
                className="p-2.5 rounded-xl bg-secondary hover:bg-secondary/80 disabled:opacity-30 disabled:cursor-not-allowed text-foreground transition-colors"
                title="Previous Card (←)"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <button
                type="button"
                onClick={handleFlip}
                className="px-4 py-2.5 rounded-xl bg-secondary/80 hover:bg-secondary text-xs font-bold text-foreground transition-colors flex items-center gap-1.5"
              >
                <RotateCw className="w-4 h-4 text-accent" />
                {isFlipped ? "Show Question" : "Reveal Answer"}
              </button>
              <button
                type="button"
                onClick={handleNext}
                disabled={currentIndex === filteredCards.length - 1}
                className="p-2.5 rounded-xl bg-secondary hover:bg-secondary/80 disabled:opacity-30 disabled:cursor-not-allowed text-foreground transition-colors"
                title="Next Card (→)"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>

            {/* Leitner Box Ratings */}
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-semibold text-muted-foreground mr-1 hidden lg:inline">Move to:</span>
              <button
                type="button"
                onClick={() => handleRateCard(1)}
                className={`px-3 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                  currentBox === 1
                    ? "bg-rose-500 text-white shadow-xs"
                    : "bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 border border-rose-500/30"
                }`}
              >
                <X className="w-3.5 h-3.5" />
                Needs Work (1)
              </button>
              <button
                type="button"
                onClick={() => handleRateCard(2)}
                className={`px-3 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                  currentBox === 2
                    ? "bg-amber-500 text-black shadow-xs"
                    : "bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 border border-amber-500/30"
                }`}
              >
                <RotateCw className="w-3.5 h-3.5" />
                Reviewing (2)
              </button>
              <button
                type="button"
                onClick={() => handleRateCard(3)}
                className={`px-3 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                  currentBox === 3
                    ? "bg-emerald-500 text-black shadow-xs"
                    : "bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 border border-emerald-500/30"
                }`}
              >
                <Check className="w-3.5 h-3.5" />
                Mastered (3)
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {/* ========================================================================= */}
      {/* MODAL: ADD CUSTOM CARD                                                    */}
      {/* ========================================================================= */}
      {isAddingCard && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs">
          <div className="w-full max-w-lg rounded-3xl bg-card border border-border p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-border/50 pb-3">
              <div className="flex items-center gap-2">
                <span className="p-1.5 rounded-lg bg-accent/15 text-accent">
                  <Plus className="w-4 h-4" />
                </span>
                <h4 className="font-bold text-foreground">Add Custom Flashcard</h4>
              </div>
              <button
                type="button"
                onClick={() => setIsAddingCard(false)}
                className="p-1 rounded-lg text-muted-foreground hover:text-foreground"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveCustomCard} className="space-y-4">
              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-1 space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground">Unit</label>
                  <select
                    value={newUnit}
                    onChange={(e) => setNewUnit(parseInt(e.target.value, 10))}
                    className="w-full px-3 py-2 rounded-xl bg-background border border-border text-xs font-medium text-foreground focus:outline-hidden focus:ring-2 focus:ring-accent"
                  >
                    {[1, 2, 3, 4, 5].map((u) => (
                      <option key={u} value={u}>
                        Unit {u}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="col-span-2 space-y-1">
                  <label className="text-xs font-semibold text-muted-foreground">Topic Name</label>
                  <input
                    type="text"
                    value={newTopic}
                    onChange={(e) => setNewTopic(e.target.value)}
                    placeholder="e.g. Cayley-Hamilton Theorem"
                    className="w-full px-3 py-2 rounded-xl bg-background border border-border text-xs text-foreground focus:outline-hidden focus:ring-2 focus:ring-accent"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-muted-foreground">Question / Prompt *</label>
                <textarea
                  rows={3}
                  required
                  value={newQuestion}
                  onChange={(e) => setNewQuestion(e.target.value)}
                  placeholder="State the question or key definition to memorize..."
                  className="w-full px-3 py-2 rounded-xl bg-background border border-border text-xs text-foreground focus:outline-hidden focus:ring-2 focus:ring-accent"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-muted-foreground">Core Answer / Formula *</label>
                <textarea
                  rows={4}
                  required
                  value={newAnswer}
                  onChange={(e) => setNewAnswer(e.target.value)}
                  placeholder="Provide the formula, derivation outline, or solution steps..."
                  className="w-full px-3 py-2 rounded-xl bg-background border border-border text-xs text-foreground focus:outline-hidden focus:ring-2 focus:ring-accent"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-muted-foreground">Exam Tip (Optional)</label>
                <input
                  type="text"
                  value={newExamTip}
                  onChange={(e) => setNewExamTip(e.target.value)}
                  placeholder="e.g. Always state initial conditions..."
                  className="w-full px-3 py-2 rounded-xl bg-background border border-border text-xs text-foreground focus:outline-hidden focus:ring-2 focus:ring-accent"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-border/50">
                <button
                  type="button"
                  onClick={() => setIsAddingCard(false)}
                  className="px-4 py-2 rounded-xl bg-secondary text-secondary-foreground text-xs font-semibold hover:bg-secondary/80"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-accent text-accent-foreground text-xs font-bold hover:bg-accent/90 shadow-xs"
                >
                  Save Flashcard
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
