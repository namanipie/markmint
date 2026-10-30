"use client";

import React, { useState } from "react";
import Link from "next/link";
import { 
  Sparkles, 
  Dna, 
  ShieldCheck, 
  FileText, 
  Check, 
  ChevronDown, 
  ChevronUp, 
  Loader2, 
  BookOpen, 
  Video, 
  Play, 
  FileCheck2,
  AlertCircle
} from "lucide-react";
import { MathText } from "@/components/ui/math-text";
import { Drawer } from "@/components/ui/drawer";
import { TopicQuestionsViewer } from "@/components/ui/topic-questions-viewer";
import { MintAIQuestionGenerator } from "@/components/ui/mint-ai-question-generator";
import { ResourceViewerModal, ResourceViewerItem } from "@/components/ui/resource-viewer-modal";
import { getTopicResources } from "@/lib/course-resources";
import { CourseCatalogItem } from "@/lib/courses";

interface MintAIOverviewTabProps {
  currentCourse: CourseCatalogItem | null;
  selectedCycle: string;
  selectedUnits: number[];
  displayedForecastItems: any[];
  filteredForecastItems: any[];
  forecastFilter: "ALL" | "TOPIC" | "FAMILY";
  setForecastFilter: (filter: "ALL" | "TOPIC" | "FAMILY") => void;
  showAllSignals: boolean;
  setShowAllSignals: React.Dispatch<React.SetStateAction<boolean>>;
  isLoadingIntelligence: boolean;
  onSwitchTab: (tab: "overview" | "dna" | "practice" | "study", topicName?: string) => void;
  onOpenCourseModal: () => void;
}

function cleanExplanation(text?: string | null): string {
  if (!text) return "";
  return text
    .replace(/\(\s*\d+\s*marks\s+across\s+(\d+)\s*question\(s\)\s*\)/gi, "across $1 historical questions")
    .replace(/\(\s*across\s+(\d+)\s*question\(s\)\s*\)/gi, "across $1 historical questions")
    .replace(/\s*representing\s+\d+\s*marks\.?/gi, ".")
    .replace(/\(\s*\d+\s*marks\s+total\s*\)/gi, "")
    .replace(/\s*and\s+\d+\s*marks/gi, "")
    .replace(/\(\s*\d+\s*marks\s*\)/gi, "")
    .replace(/\s{2,}/g, " ")
    .replace(/\s+\./g, ".")
    .trim();
}

export function MintAIOverviewTab({
  currentCourse,
  selectedCycle,
  selectedUnits,
  displayedForecastItems,
  filteredForecastItems,
  forecastFilter,
  setForecastFilter,
  showAllSignals,
  setShowAllSignals,
  isLoadingIntelligence,
  onSwitchTab,
  onOpenCourseModal,
}: MintAIOverviewTabProps) {
  // Slide-over Practice Drawer state
  const [activePracticeTopic, setActivePracticeTopic] = useState<{
    name: string;
    rank?: number;
    probability?: number | null;
    isFamily?: boolean;
    repetition_type?: string | null;
    historicalOccurrences?: number;
    totalMarksObserved?: number | null;
    paperCoverage?: number;
    papersWithItem?: number;
    totalPapers?: number;
    explanation?: string;
  } | null>(null);

  const [drawerActiveTab, setDrawerActiveTab] = useState<"pyq" | "ai">("pyq");
  const [viewerItem, setViewerItem] = useState<ResourceViewerItem | null>(null);

  const cycleDisplayLabel = React.useMemo(() => {
    switch (selectedCycle) {
      case "ENDSEM":
        return "End Semester";
      case "CT1":
        return "Cycle Test 1";
      case "CT2":
        return "Cycle Test 2";
      default:
        return "All Cycles";
    }
  }, [selectedCycle]);

  // Handle video modal launch for a topic
  const handleWatchTopicLecture = (topicName: string, unitNumber?: number) => {
    if (!currentCourse) return;
    const resources = getTopicResources(currentCourse.slug || currentCourse.id, topicName, unitNumber);
    if (resources?.videos && resources.videos.length > 0) {
      setViewerItem({
        type: "video",
        data: resources.videos[0],
        courseName: currentCourse.name,
      });
    } else {
      // If no single video, switch to Study tab
      onSwitchTab("study", topicName);
    }
  };

  if (!currentCourse) {
    return (
      <div className="p-8 sm:p-12 rounded-2xl border border-dashed border-border/80 bg-card/60 text-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center text-accent mx-auto">
          <BookOpen className="w-6 h-6" />
        </div>
        <div className="max-w-md mx-auto space-y-1.5">
          <h3 className="text-lg font-bold text-foreground">Select a Course to View Predictions</h3>
          <p className="text-xs text-muted-foreground">
            Choose your engineering subject to calibrate Bayesian exam probabilities, unit weightages, and recurring question patterns.
          </p>
        </div>
        <button
          type="button"
          onClick={onOpenCourseModal}
          className="px-5 py-2.5 rounded-xl bg-foreground text-background text-xs font-semibold hover:bg-foreground/90 transition-all shadow-xs cursor-pointer inline-flex items-center gap-2"
        >
          <Sparkles className="w-4 h-4 text-accent" />
          <span>Select Course Now</span>
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Forecast Section Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border/50">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <span>Exam Forecast &amp; Priority Queue</span>
              {isLoadingIntelligence && <Loader2 className="w-4 h-4 text-accent animate-spin" />}
            </h2>
          </div>
          <p className="text-xs text-muted-foreground">
            Ranked by Bayesian recurrence probability, historical appearance frequency, and SRMIST syllabus weightings for{" "}
            <strong className="text-foreground">{currentCourse.name}</strong> ({cycleDisplayLabel}).
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 p-1 bg-muted/20 border border-border/60 rounded-xl text-xs font-semibold self-start md:self-auto shrink-0">
          <button
            type="button"
            onClick={() => setForecastFilter("ALL")}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
              forecastFilter === "ALL"
                ? "bg-accent text-accent-foreground font-bold shadow-2xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            All Signals ({filteredForecastItems.length})
          </button>
          <button
            type="button"
            onClick={() => setForecastFilter("TOPIC")}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
              forecastFilter === "TOPIC"
                ? "bg-accent text-accent-foreground font-bold shadow-2xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Core Topics
          </button>
          <button
            type="button"
            onClick={() => setForecastFilter("FAMILY")}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
              forecastFilter === "FAMILY"
                ? "bg-accent text-accent-foreground font-bold shadow-2xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Question Families
          </button>
        </div>
      </div>

      {/* Forecast Cards Grid */}
      {filteredForecastItems.length === 0 ? (
        <div className="p-8 sm:p-12 text-center rounded-2xl border border-dashed border-border/70 bg-card/40 space-y-3">
          <AlertCircle className="w-8 h-8 text-muted-foreground mx-auto" />
          <p className="text-xs text-muted-foreground">
            No signals match the active filter or selected units ({selectedUnits.join(", ")}).
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {displayedForecastItems.map((item: any, idx: number) => {
              const topicRes = getTopicResources(currentCourse.slug || currentCourse.id, item.name, item.unitNumber);
              const hasVideo = Boolean(topicRes?.videos && topicRes.videos.length > 0);

              return (
                <div
                  key={item.name || idx}
                  className="p-4 sm:p-5 rounded-2xl bg-card border border-border/80 hover:border-accent/40 transition-all flex flex-col justify-between gap-3 shadow-2xs group"
                >
                  <div className="space-y-2.5">
                    {/* Header: Rank + Unit + Probability + Family */}
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-1.5">
                        <span className="inline-flex items-center justify-center w-6 h-6 rounded-md bg-accent/15 text-accent font-mono text-xs font-bold shrink-0">
                          #{item.rank || idx + 1}
                        </span>
                        {item.unitNumber && (
                          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-accent/10 text-accent border border-accent/20">
                            Unit {item.unitNumber}
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-1.5 flex-wrap justify-end">
                        {item.isFamily && (
                          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground border border-border">
                            {item.repetition_type === "EXACT" ? "Exact Repeat Family" : "Recurring Family"}
                          </span>
                        )}

                        {item.probability != null && (
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded-full border font-mono ${
                              item.probability >= 70
                                ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"
                                : "bg-accent/10 text-accent border-accent/20"
                            }`}
                          >
                            {item.probability}% Calibrated P
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Question / Topic Title with LaTeX Math */}
                    <div>
                      <div className="text-sm font-bold text-foreground group-hover:text-accent transition-colors line-clamp-2 leading-snug">
                        <MathText content={item.name} inlineOnly />
                      </div>
                      {item.explanation && (
                        <p className="text-xs text-muted-foreground pt-1 line-clamp-2 leading-relaxed">
                          {cleanExplanation(item.explanation)}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Evidence Proof Line & Action Buttons */}
                  <div className="pt-2.5 border-t border-border/40 flex items-center justify-between gap-2">
                    <span className="text-[11px] text-muted-foreground font-mono truncate">
                      {item.papersWithItem && item.totalPapers
                        ? `${item.papersWithItem}/${item.totalPapers} papers (${Math.round((item.paperCoverage || 0) * 100)}%)`
                        : `${item.historicalOccurrences} occurrences`}
                    </span>

                    <div className="flex items-center gap-1.5 shrink-0">
                      {hasVideo && (
                        <button
                          type="button"
                          onClick={() => handleWatchTopicLecture(item.name, item.unitNumber)}
                          className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs font-semibold border border-red-500/20 transition-all cursor-pointer"
                          title="Watch faculty video lecture for this topic"
                        >
                          <Play className="w-3 h-3 fill-current" />
                          <span className="hidden sm:inline">Watch</span>
                        </button>
                      )}

                      <button
                        type="button"
                        onClick={() => {
                          setActivePracticeTopic(item);
                          setDrawerActiveTab("pyq");
                        }}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent/10 hover:bg-accent/20 text-accent font-semibold text-xs border border-accent/20 transition-all cursor-pointer shadow-2xs"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Practice</span>
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Show More / Show Less Toggle & Jump Links */}
          <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-xs text-muted-foreground flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-accent shrink-0" />
              <span>Forecast derived strictly from verified historical exams without speculation.</span>
            </div>

            <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto justify-end">
              {filteredForecastItems.length > 4 && (
                <button
                  type="button"
                  onClick={() => setShowAllSignals((prev) => !prev)}
                  className="w-full sm:w-auto px-4 py-2 rounded-xl bg-foreground text-background text-xs font-semibold hover:bg-foreground/90 transition-all flex items-center justify-center gap-2 shadow-xs cursor-pointer"
                >
                  <span>{showAllSignals ? "Show Top 4 Signals" : `Show All ${filteredForecastItems.length} Signals`}</span>
                  {showAllSignals ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                </button>
              )}

              <button
                type="button"
                onClick={() => onSwitchTab("dna")}
                className="w-full sm:w-auto px-4 py-2 rounded-xl bg-secondary text-secondary-foreground hover:bg-secondary/80 border border-border text-xs font-semibold transition-all flex items-center justify-center gap-2 shadow-2xs cursor-pointer"
              >
                <Dna className="w-3.5 h-3.5 text-accent" />
                <span>Explore Exam DNA &rarr;</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Slide-over Practice Drawer */}
      <Drawer
        isOpen={!!activePracticeTopic}
        onClose={() => setActivePracticeTopic(null)}
        title={
          <div className="flex items-center gap-2">
            {activePracticeTopic?.rank && (
              <span className="inline-flex items-center justify-center px-2 py-0.5 rounded-md bg-accent/15 text-accent font-mono text-xs font-bold shrink-0">
                #{activePracticeTopic.rank}
              </span>
            )}
            <div className="line-clamp-2">
              <MathText content={activePracticeTopic?.name || ""} inlineOnly />
            </div>
          </div>
        }
        subtitle={
          <div className="flex items-center gap-2 text-xs text-muted-foreground pt-1 flex-wrap">
            <span>{currentCourse?.name}</span>
            <span>•</span>
            <span>{cycleDisplayLabel}</span>
            {activePracticeTopic?.probability != null && (
              <>
                <span>•</span>
                <span className="font-semibold text-emerald-600 dark:text-emerald-400 font-mono">
                  {activePracticeTopic.probability}% Calibrated P
                </span>
              </>
            )}
          </div>
        }
      >
        {currentCourse && (
          <div className="space-y-5">
            {/* Drawer Tabs: Verified PYQs vs AI Practice Generator */}
            <div className="grid grid-cols-2 rounded-lg border border-border p-1 bg-muted/20 text-xs">
              <button
                type="button"
                onClick={() => setDrawerActiveTab("pyq")}
                className={`py-2 px-3 rounded-md text-xs font-semibold transition-all flex items-center justify-center gap-2 cursor-pointer ${
                  drawerActiveTab === "pyq"
                    ? "bg-accent text-accent-foreground shadow-2xs"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Past Exam Questions</span>
              </button>

              <button
                type="button"
                onClick={() => setDrawerActiveTab("ai")}
                className={`py-2 px-3 rounded-md text-xs font-semibold transition-all flex items-center justify-center gap-2 cursor-pointer ${
                  drawerActiveTab === "ai"
                    ? "bg-accent text-accent-foreground shadow-2xs"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>AI Practice Questions</span>
              </button>
            </div>

            {/* Drawer Content */}
            {drawerActiveTab === "pyq" ? (
              <TopicQuestionsViewer
                topicName={activePracticeTopic?.name || ""}
                courseId={currentCourse.id}
                courseCode={currentCourse.canonicalCode || currentCourse.code}
              />
            ) : (
              <div className="space-y-4">
                <div className="p-3 rounded-xl bg-accent/5 border border-accent/20 text-xs text-muted-foreground">
                  MintAI generates practice problems strictly aligned with the assessment patterns of{" "}
                  <strong className="text-foreground">{currentCourse.name}</strong>.
                </div>
                <MintAIQuestionGenerator
                  topicName={activePracticeTopic?.name || ""}
                  courseId={currentCourse.id}
                  cycle={selectedCycle}
                />
              </div>
            )}
          </div>
        )}
      </Drawer>

      {/* In-App Resource Viewer Modal */}
      <ResourceViewerModal
        item={viewerItem}
        onClose={() => setViewerItem(null)}
      />
    </div>
  );
}
