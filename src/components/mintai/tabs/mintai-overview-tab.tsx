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
  ChevronRight,
  Loader2, 
  BookOpen, 
  Video, 
  Play, 
  FileCheck2,
  AlertCircle,
  Layers,
  TrendingUp,
  BarChart3,
  ArrowRight,
  ExternalLink
} from "lucide-react";
import { MathText } from "@/components/ui/math-text";
import { Drawer } from "@/components/ui/drawer";
import { ExamDNAView } from "@/components/analytics/exam-dna-view";
import { TopicQuestionsViewer } from "@/components/ui/topic-questions-viewer";
import { MintAIQuestionGenerator } from "@/components/ui/mint-ai-question-generator";
import { ResourceViewerModal, ResourceViewerItem } from "@/components/ui/resource-viewer-modal";
import { getTopicResources } from "@/lib/course-resources";
import { CourseCatalogItem } from "@/lib/courses";

export interface EmpiricalUnitBreakdownItem {
  rank: number;
  unit_number: number;
  unit_name: string;
  question_count: number;
  marks: number;
  percentage_of_marks: number;
  percentage_of_questions: number;
  paper_coverage: number;
  is_baseline?: boolean;
}

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
  empiricalUnitBreakdown?: EmpiricalUnitBreakdownItem[];
  evidenceStatus?: string;
  assessmentScope?: any;
  onToggleUnit?: (unitNumber: number) => void;
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
  empiricalUnitBreakdown = [],
  evidenceStatus,
  assessmentScope,
  onToggleUnit,
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
  const [expandedTopicNames, setExpandedTopicNames] = useState<Record<string, boolean>>({});
  const [isDnaPreviewOpen, setIsDnaPreviewOpen] = useState<boolean>(false);

  const toggleTopicExpand = (topicName: string) => {
    setExpandedTopicNames((prev) => ({
      ...prev,
      [topicName]: !prev[topicName],
    }));
  };

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

  const isBaseline = React.useMemo(() => {
    return (
      evidenceStatus === "SYLLABUS_FALLBACK" ||
      (empiricalUnitBreakdown.length > 0 && empiricalUnitBreakdown.every((u) => u.is_baseline))
    );
  }, [evidenceStatus, empiricalUnitBreakdown]);

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

      {/* Empirical Unit Priority Section (No hardcoding - purely data-driven from this exam's papers) */}
      {isBaseline ? (
        <div className="p-4 sm:p-5 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-500 border border-amber-500/30 font-bold text-[11px] uppercase tracking-wide">
                Syllabus-Derived Baseline
              </span>
              <span className="text-xs font-semibold text-foreground">
                0 historical {cycleDisplayLabel} papers in archive
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              Empirical evidence for {cycleDisplayLabel} is currently calibrated directly from the official SRMIST curriculum guidelines for{" "}
              <strong className="text-foreground">
                Units {empiricalUnitBreakdown.map((u) => u.unit_number).join(" & ") || selectedUnits.join(" & ")}
              </strong>.
            </p>
          </div>
          <div className="flex items-center gap-2 flex-wrap shrink-0">
            {empiricalUnitBreakdown.map((u) => (
              <div
                key={u.unit_number}
                className="px-3 py-1.5 rounded-xl bg-card border border-border text-foreground font-mono text-xs flex items-center gap-2"
              >
                <span className="font-bold text-accent">Unit {u.unit_number}</span>
                <span className="text-muted-foreground text-[11px]">({u.percentage_of_marks}% Target)</span>
              </div>
            ))}
          </div>
        </div>
      ) : empiricalUnitBreakdown && empiricalUnitBreakdown.length > 0 ? (
        <div className="p-4 sm:p-5 rounded-2xl bg-card/70 border border-border/80 space-y-3.5 shadow-2xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="space-y-0.5">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-accent" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                  Empirical Unit Priority • {cycleDisplayLabel}
                </h3>
              </div>
              <p className="text-xs text-foreground font-semibold">
                Ranked by question volume and marks on verified {cycleDisplayLabel} papers
              </p>
            </div>
            <span className="text-[11px] text-muted-foreground font-mono">
              Click unit card to toggle filter
            </span>
          </div>

          {/* Ranked Unit Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5">
            {empiricalUnitBreakdown.map((u) => {
              const isSelected = selectedUnits.includes(u.unit_number);
              return (
                <button
                  key={u.unit_number}
                  type="button"
                  onClick={() => onToggleUnit?.(u.unit_number)}
                  className={`p-3 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between gap-2.5 ${
                    isSelected
                      ? "bg-accent/10 border-accent/50 shadow-2xs ring-1 ring-accent/30"
                      : "bg-muted/15 border-border/60 hover:border-border hover:bg-muted/25 opacity-70"
                  }`}
                >
                  <div className="flex items-center justify-between gap-1.5">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <span className="inline-flex items-center justify-center w-5 h-5 rounded-md bg-accent/20 text-accent font-mono text-[10px] font-bold shrink-0">
                        U{u.unit_number}
                      </span>
                      <span className="text-xs font-bold text-foreground truncate" title={u.unit_name}>
                        {u.unit_name || `Unit ${u.unit_number}`}
                      </span>
                    </div>
                    <span className="text-xs font-mono font-bold text-accent shrink-0">
                      {u.percentage_of_marks}%
                    </span>
                  </div>

                  {/* Visual Progress Bar */}
                  <div className="w-full bg-muted/40 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-accent h-1.5 rounded-full transition-all"
                      style={{ width: `${Math.min(100, Math.max(5, u.percentage_of_marks))}%` }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-muted-foreground font-mono">
                    <span>{u.question_count} Qs</span>
                    <span>{u.marks} marks</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      ) : null}

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
              const isExpanded = Boolean(expandedTopicNames[item.name]);
              const isHighPriority =
                (item.probability != null && item.probability >= 70) ||
                (item.paperCoverage != null && item.paperCoverage >= 0.65) ||
                item.isFamily;

              return (
                <div
                  key={item.name || idx}
                  className={`p-4 sm:p-5 rounded-2xl bg-card border transition-all flex flex-col justify-between gap-3 shadow-2xs group ${
                    isExpanded ? "border-primary/50 ring-1 ring-primary/20" : "border-border/80 hover:border-primary/40"
                  }`}
                >
                  <div className="space-y-2.5">
                    {/* Header: Unit + Priority + Expand Indicator */}
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-1.5">
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-secondary text-foreground font-mono">
                          Unit {item.unitNumber}
                        </span>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            isHighPriority
                              ? "bg-primary/10 text-primary border border-primary/20"
                              : "bg-secondary text-muted-foreground"
                          }`}
                        >
                          {isHighPriority ? "High Priority ⭐" : "Core Topic"}
                        </span>
                        {item.is_baseline_fallback && (
                          <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-500">
                            Syllabus Scope
                          </span>
                        )}
                      </div>

                      <button
                        type="button"
                        onClick={() => toggleTopicExpand(item.name)}
                        className="inline-flex items-center gap-1 text-[11px] font-semibold text-muted-foreground hover:text-foreground p-1 transition-colors cursor-pointer"
                        title={isExpanded ? "Collapse details" : "Expand analytical evidence"}
                      >
                        <span className="text-[10px] hidden sm:inline">{isExpanded ? "Less" : "Details"}</span>
                        {isExpanded ? <ChevronUp className="w-3.5 h-3.5 text-primary" /> : <ChevronDown className="w-3.5 h-3.5" />}
                      </button>
                    </div>

                    {/* Question / Topic Title with LaTeX Math */}
                    <div
                      onClick={() => toggleTopicExpand(item.name)}
                      className="cursor-pointer select-none"
                    >
                      <h4 className="text-sm font-bold text-foreground group-hover:text-primary transition-colors line-clamp-2 leading-snug">
                        <MathText content={item.name} inlineOnly />
                      </h4>
                    </div>

                    {/* One Concise Evidence Indicator (Always visible) */}
                    <div className="text-[11px] text-muted-foreground font-mono flex items-center justify-between">
                      <span>
                        {item.is_baseline_fallback
                          ? `SRMIST curriculum baseline • ${cycleDisplayLabel}`
                          : item.papersWithItem && item.totalPapers
                          ? `In ${item.papersWithItem}/${item.totalPapers} recent ${cycleDisplayLabel} papers (${Math.round((item.paperCoverage || 0) * 100)}%)`
                          : `${item.historicalOccurrences || 1} historical occurrences`}
                      </span>
                    </div>

                    {/* Progressive Disclosure Section (Revealed on click) */}
                    {isExpanded && (
                      <div className="pt-3 border-t border-border/50 space-y-3 animate-in fade-in-50 duration-150">
                        {/* Probability & Archetype */}
                        <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                          {item.probability != null ? (
                            <div className="space-y-1 w-full sm:w-auto">
                              <div className="flex items-center justify-between gap-4 text-[11px] font-mono">
                                <span className="text-muted-foreground">Calibrated Recurrence:</span>
                                <span className="font-bold text-primary">{item.probability}%</span>
                              </div>
                              <div className="w-full sm:w-48 bg-secondary rounded-full h-1.5 overflow-hidden">
                                <div
                                  className="bg-primary h-1.5 rounded-full transition-all"
                                  style={{ width: `${item.probability}%` }}
                                />
                              </div>
                            </div>
                          ) : null}

                          {item.isFamily && (
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20 font-mono">
                              {item.repetition_type === "EXACT" ? "Exact Repeat Archetype" : "Recurring Question Family"}
                            </span>
                          )}
                        </div>

                        {/* Concise Explanation */}
                        {item.explanation && (
                          <p className="text-xs text-muted-foreground leading-relaxed">
                            {cleanExplanation(item.explanation)}
                          </p>
                        )}

                        {/* Actions */}
                        <div className="pt-1 flex items-center justify-end gap-2 flex-wrap">
                          {hasVideo && (
                            <button
                              type="button"
                              onClick={() => handleWatchTopicLecture(item.name, item.unitNumber)}
                              className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-500 text-xs font-semibold border border-red-500/20 transition-all cursor-pointer"
                            >
                              <Play className="w-3 h-3 fill-current" />
                              <span>Watch Lecture</span>
                            </button>
                          )}

                          <button
                            type="button"
                            onClick={() => {
                              setActivePracticeTopic(item);
                              setDrawerActiveTab("pyq");
                            }}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-primary text-primary-foreground font-bold text-xs hover:bg-primary/90 transition-all cursor-pointer shadow-2xs"
                          >
                            <Sparkles className="w-3.5 h-3.5" />
                            <span>Practice Matching Questions</span>
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Dedicated Exam DNA Radar Integration Banner */}
          <div className="p-4 sm:p-5 rounded-2xl bg-secondary/50 border border-border/80 flex flex-col md:flex-row md:items-center justify-between gap-4 mt-6">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shrink-0">
                <Dna className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-foreground">
                  Exam DNA &amp; Cognitive Demand Radar
                </h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Deep Bloom&apos;s taxonomy demand, empirical unit weightage evolution, and historical backtesting for <strong className="text-foreground">{currentCourse.name}</strong>.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0 self-start md:self-auto">
              <button
                type="button"
                onClick={() => setIsDnaPreviewOpen(true)}
                className="px-3.5 py-2 rounded-xl bg-card border border-border text-xs font-semibold hover:bg-secondary text-foreground transition-colors cursor-pointer"
              >
                Quick Preview
              </button>
              <Link
                href={`/mintai/exam-dna?course=${currentCourse.id}&cycle=${selectedCycle}`}
                className="px-4 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-bold hover:bg-primary/90 transition-all flex items-center gap-1.5 shadow-2xs"
              >
                <span>Full Analytics</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
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

      {/* Exam DNA Quick Preview Drawer */}
      <Drawer
        isOpen={isDnaPreviewOpen}
        onClose={() => setIsDnaPreviewOpen(false)}
        title={
          <div className="flex items-center gap-2">
            <Dna className="w-5 h-5 text-primary" />
            <span>Exam DNA Radar Preview: {currentCourse?.name}</span>
          </div>
        }
        subtitle={
          <div className="flex items-center gap-2 text-xs text-muted-foreground pt-0.5">
            <span>Cycle: {cycleDisplayLabel}</span>
            <span>•</span>
            <Link
              href={`/mintai/exam-dna?course=${currentCourse?.id}&cycle=${selectedCycle}`}
              className="text-primary font-semibold hover:underline inline-flex items-center gap-1"
            >
              <span>Open Full Dedicated Page</span>
              <ExternalLink className="w-3 h-3" />
            </Link>
          </div>
        }
      >
        {currentCourse && (
          <div className="p-1 space-y-4">
            <ExamDNAView
              courseId={currentCourse.id}
              courseName={currentCourse.name}
              canonicalCode={currentCourse.canonicalCode || currentCourse.code}
              assessmentCycle={selectedCycle}
            />
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
