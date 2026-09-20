"use client";

import React, { useState, useEffect } from "react";
import {
  Repeat,
  Layers,
  Calendar,
  TrendingUp,
  BarChart2,
  Filter,
  CheckCircle2,
  Clock,
  Sparkles,
  BookOpen,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Hash,
  ArrowRight,
  HelpCircle,
  FileText
} from "lucide-react";
import {
  getRepetitionOverview,
  getTopicRepetition,
  getQuestionFamilies,
  getRepeatedQuestions,
  getCourseEvolution,
  getMarksAnalytics,
  getAssessmentComparison
} from "@/lib/api";
import {
  RepetitionOverview,
  TopicRepetitionResponse,
  TopicRepetitionItem,
  FamilyRepeatResponse,
  FamilyRepeatItem,
  RepeatedQuestionsResponse,
  EvolutionResponse,
  MarksAnalyticsResponse,
  AssessmentComparisonResponse
} from "@/lib/types";
import { TopicIntelligenceModal } from "./topic-intelligence-modal";
import { MathText } from "@/components/ui/math-text";

interface RepetitionAnalyticsViewProps {
  courseId: number | string;
  courseName: string;
  canonicalCode?: string | null;
  language?: string;
  onSelectTopic?: (topicName: string) => void;
}

type AnalyticsTab = "topics" | "families" | "assessment" | "evolution" | "marks";

export function RepetitionAnalyticsView({
  courseId,
  courseName,
  canonicalCode,
  language,
  onSelectTopic
}: RepetitionAnalyticsViewProps) {
  const [activeTab, setActiveTab] = useState<AnalyticsTab>("topics");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [overview, setOverview] = useState<RepetitionOverview | null>(null);
  const [topicData, setTopicData] = useState<TopicRepetitionResponse | null>(null);
  const [familyData, setFamilyData] = useState<FamilyRepeatResponse | null>(null);
  const [repeatedQuestions, setRepeatedQuestions] = useState<RepeatedQuestionsResponse | null>(null);
  const [evolutionData, setEvolutionData] = useState<EvolutionResponse | null>(null);
  const [marksData, setMarksData] = useState<MarksAnalyticsResponse | null>(null);
  const [assessmentData, setAssessmentData] = useState<AssessmentComparisonResponse | null>(null);

  // Topic Intelligence Drilldown Modal State
  const [isTopicModalOpen, setIsTopicModalOpen] = useState(false);
  const [selectedTopicIdForModal, setSelectedTopicIdForModal] = useState<number | null>(null);
  const [selectedTopicNameForModal, setSelectedTopicNameForModal] = useState<string>("");

  const handleOpenTopic = (topicId: number, topicName: string) => {
    setSelectedTopicIdForModal(topicId);
    setSelectedTopicNameForModal(topicName);
    setIsTopicModalOpen(true);
    if (onSelectTopic) onSelectTopic(topicName);
  };

  // Interactive filters
  const [filterYear, setFilterYear] = useState<string>("ALL");
  const [filterAssessmentType, setFilterAssessmentType] = useState<string>("ALL");
  const [filterUnit, setFilterUnit] = useState<string>("ALL");
  const [filterMinMarks, setFilterMinMarks] = useState<string>("ALL");
  const [familyRepeatOnly, setFamilyRepeatOnly] = useState<boolean>(true);
  const [familySearchQuery, setFamilySearchQuery] = useState<string>("");
  const [expandedFamilyId, setExpandedFamilyId] = useState<number | null>(null);

  // Load initial overview & active tab data
  useEffect(() => {
    let active = true;
    setIsLoading(true);
    setError(null);

    Promise.all([
      getRepetitionOverview(courseId, language),
      getTopicRepetition(courseId, { language }),
      getQuestionFamilies(courseId),
      getRepeatedQuestions(courseId),
      getCourseEvolution(courseId),
      getMarksAnalytics(courseId),
      getAssessmentComparison(courseId)
    ])
      .then(([ov, top, fam, rep, evo, mrk, asmt]) => {
        if (!active) return;
        setOverview(ov);
        setTopicData(top);
        setFamilyData(fam);
        setRepeatedQuestions(rep);
        setEvolutionData(evo);
        setMarksData(mrk);
        setAssessmentData(asmt);
      })
      .catch((err) => {
        if (!active) return;
        console.error("Failed to load repetition analytics", err);
        setError("Unable to load repetition analytics for this subject.");
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [courseId, language]);

  // Handle dynamic filter changes for topics
  const handleApplyTopicFilters = () => {
    const filters: any = {};
    if (language) filters.language = language;
    if (filterYear !== "ALL") filters.year = parseInt(filterYear, 10);
    if (filterAssessmentType !== "ALL") filters.assessmentType = filterAssessmentType;
    if (filterUnit !== "ALL") filters.unit = parseInt(filterUnit, 10);
    if (filterMinMarks !== "ALL") filters.minMarks = parseFloat(filterMinMarks);

    getTopicRepetition(courseId, filters)
      .then((res) => setTopicData(res))
      .catch((err) => console.error("Filter topics failed", err));
  };

  useEffect(() => {
    if (!overview) return;
    handleApplyTopicFilters();
  }, [filterYear, filterAssessmentType, filterUnit, filterMinMarks]);

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-xl p-8 text-center space-y-3">
        <div className="inline-block animate-spin text-accent">
          <Repeat className="w-8 h-8" />
        </div>
        <h3 className="text-sm font-semibold">Computing Historical Repetition Engine...</h3>
        <p className="text-xs text-muted-foreground">
          Cross-referencing examination question recurrence, paper coverage, and canonical families.
        </p>
      </div>
    );
  }

  if (error || !overview) {
    return (
      <div className="p-5 bg-destructive/10 border border-destructive/20 text-destructive rounded-xl flex items-center gap-3">
        <AlertCircle className="w-5 h-5 shrink-0" />
        <div>
          <h4 className="font-semibold text-sm">Repetition Analytics Unavailable</h4>
          <p className="text-xs opacity-90">{error || "No data available."}</p>
        </div>
      </div>
    );
  }

  // Filtered families
  const displayedFamilies = (familyData?.families || []).filter((f) => {
    if (familyRepeatOnly && f.occurrence_count < 2) return false;
    if (familySearchQuery.trim()) {
      const q = familySearchQuery.toLowerCase();
      const inCanonical = f.canonical_name.toLowerCase().includes(q);
      const inAppearances = f.appearances?.some((a) => a.original_text.toLowerCase().includes(q));
      if (!inCanonical && !inAppearances) return false;
    }
    return true;
  });

  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm space-y-6">
      {/* Subject Header & Repetition High-Level Metrics */}
      <div className="p-6 border-b border-border bg-muted/20">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-accent/10 text-accent border border-accent/20">
                EMPIRICAL EXAMINATION RECURRENCE
              </span>
              {canonicalCode && (
                <span className="font-mono text-xs text-muted-foreground">
                  [{canonicalCode}]
                </span>
              )}
            </div>
            <h2 className="text-xl font-bold tracking-tight text-foreground mt-1">
              Question Recurrence &amp; Longitudinal Patterns: {courseName}
            </h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Empirical evidence from {overview.total_papers} verified examination papers spanning{" "}
              {overview.time_range}.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <div className="bg-background/80 border border-border rounded-lg px-3 py-2 text-center">
              <div className="text-[10px] text-muted-foreground uppercase font-mono">Papers</div>
              <div className="text-base font-bold font-mono text-accent">{overview.total_papers}</div>
            </div>
            <div className="bg-background/80 border border-border rounded-lg px-3 py-2 text-center">
              <div className="text-[10px] text-muted-foreground uppercase font-mono">Questions</div>
              <div className="text-base font-bold font-mono">{overview.total_questions}</div>
            </div>
            <div className="bg-background/80 border border-border rounded-lg px-3 py-2 text-center">
              <div className="text-[10px] text-muted-foreground uppercase font-mono">Repeated Families</div>
              <div className="text-base font-bold font-mono text-emerald-500">
                {overview.top_repeated_families.length}
              </div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 mt-6 pt-4 border-t border-border/50 overflow-x-auto">
          <button
            onClick={() => setActiveTab("topics")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "topics"
                ? "bg-accent text-accent-foreground font-semibold shadow-sm"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
            }`}
          >
            <Repeat className="w-3.5 h-3.5" />
            <span>Topic Repetition</span>
            <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-background/30 font-mono">
              {topicData?.topics_with_questions || 0}
            </span>
          </button>

          <button
            onClick={() => setActiveTab("families")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "families"
                ? "bg-accent text-accent-foreground font-semibold shadow-sm"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Question Families</span>
            <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-background/30 font-mono">
              {familyData?.multi_repeat_families_count || 0}
            </span>
          </button>

          <button
            onClick={() => setActiveTab("assessment")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "assessment"
                ? "bg-accent text-accent-foreground font-semibold shadow-sm"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
            }`}
          >
            <BarChart2 className="w-3.5 h-3.5" />
            <span>Assessment Comparison</span>
            <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-background/30 font-mono">
              CT vs EndSem
            </span>
          </button>

          <button
            onClick={() => setActiveTab("evolution")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "evolution"
                ? "bg-accent text-accent-foreground font-semibold shadow-sm"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
            }`}
          >
            <TrendingUp className="w-3.5 h-3.5" />
            <span>Evolution Timeline</span>
            <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-background/30 font-mono">
              {overview.years.length} yrs
            </span>
          </button>

          <button
            onClick={() => setActiveTab("marks")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "marks"
                ? "bg-accent text-accent-foreground font-semibold shadow-sm"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
            }`}
          >
            <BarChart2 className="w-3.5 h-3.5" />
            <span>Marks & Weight Distribution</span>
          </button>
        </div>
      </div>

      {/* Main Tab Content */}
      <div className="p-6 pt-0 space-y-6">
        {/* TAB 1: TOPIC REPETITION VIEW */}
        {activeTab === "topics" && (
          <div className="space-y-4">
            {/* Filter Bar */}
            <div className="flex flex-wrap items-center gap-3 p-3 bg-background/50 border border-border/80 rounded-lg text-xs">
              <div className="flex items-center gap-1.5 text-muted-foreground font-medium mr-1">
                <Filter className="w-3.5 h-3.5" />
                <span>Filters:</span>
              </div>

              {/* Year Filter */}
              <div className="flex items-center gap-1">
                <span className="text-muted-foreground text-[11px]">Year:</span>
                <select
                  value={filterYear}
                  onChange={(e) => setFilterYear(e.target.value)}
                  className="bg-background border border-border rounded px-2 py-1 text-xs focus:ring-1 focus:ring-accent"
                >
                  <option value="ALL">All Years ({overview.years.join(", ")})</option>
                  {overview.years.map((yr) => (
                    <option key={yr} value={String(yr)}>
                      {yr}
                    </option>
                  ))}
                </select>
              </div>

              {/* Assessment Type Filter */}
              <div className="flex items-center gap-1">
                <span className="text-muted-foreground text-[11px]">Type:</span>
                <select
                  value={filterAssessmentType}
                  onChange={(e) => setFilterAssessmentType(e.target.value)}
                  className="bg-background border border-border rounded px-2 py-1 text-xs focus:ring-1 focus:ring-accent"
                >
                  <option value="ALL">All Exam Types</option>
                  {overview.assessment_types.map((at) => (
                    <option key={at} value={at}>
                      {at}
                    </option>
                  ))}
                </select>
              </div>

              {/* Unit Filter */}
              <div className="flex items-center gap-1">
                <span className="text-muted-foreground text-[11px]">Unit:</span>
                <select
                  value={filterUnit}
                  onChange={(e) => setFilterUnit(e.target.value)}
                  className="bg-background border border-border rounded px-2 py-1 text-xs focus:ring-1 focus:ring-accent"
                >
                  <option value="ALL">All Units</option>
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((u) => (
                    <option key={u} value={String(u)}>
                      Unit {u}
                    </option>
                  ))}
                </select>
              </div>

              {/* Min Marks Filter */}
              <div className="flex items-center gap-1">
                <span className="text-muted-foreground text-[11px]">Min Marks:</span>
                <select
                  value={filterMinMarks}
                  onChange={(e) => setFilterMinMarks(e.target.value)}
                  className="bg-background border border-border rounded px-2 py-1 text-xs focus:ring-1 focus:ring-accent"
                >
                  <option value="ALL">Any Marks</option>
                  <option value="2">2+ Marks</option>
                  <option value="5">5+ Marks</option>
                  <option value="10">10+ Marks</option>
                  <option value="12">12+ Marks</option>
                </select>
              </div>

              {(filterYear !== "ALL" ||
                filterAssessmentType !== "ALL" ||
                filterUnit !== "ALL" ||
                filterMinMarks !== "ALL") && (
                <button
                  onClick={() => {
                    setFilterYear("ALL");
                    setFilterAssessmentType("ALL");
                    setFilterUnit("ALL");
                    setFilterMinMarks("ALL");
                  }}
                  className="text-xs text-accent hover:underline ml-auto"
                >
                  Reset Filters
                </button>
              )}
            </div>

            {/* Topics List */}
            {(!topicData || topicData.topics.length === 0) && overview && overview.total_questions > 0 ? (
              <div className="bg-card border border-border/80 rounded-xl p-8 text-center space-y-3">
                <div className="inline-flex p-3 rounded-full bg-accent/10 text-accent mb-1">
                  <Layers className="w-6 h-6" />
                </div>
                <h4 className="text-sm font-semibold text-foreground">
                  Topic Taxonomy Pending Cataloging
                </h4>
                <p className="text-xs text-muted-foreground max-w-md mx-auto leading-relaxed">
                  Topic-level syllabus taxonomy is pending cataloging for this course. Question Family recurrence is active with {overview.total_questions} verified questions across {overview.top_repeated_families.length} families.
                </p>
                <div className="pt-2">
                  <button
                    onClick={() => setActiveTab("families")}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-accent text-accent-foreground text-xs font-semibold hover:bg-accent/90 transition-colors cursor-pointer"
                  >
                    <span>View Question Families</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="text-xs text-muted-foreground flex justify-between items-center px-1">
                  <span>
                    Showing {topicData?.topics.length || 0} topics sorted by paper recurrence & marks weight
                  </span>
                  <span className="font-mono text-[10px]">Coverage = Papers Present / Analyzed</span>
                </div>

                <div className="grid grid-cols-1 gap-2.5">
                  {(topicData?.topics || []).map((t) => {
                  const coveragePercent = Math.round(t.paper_coverage * 100);
                  const isHighYield = t.paper_count >= 2 || coveragePercent >= 50;

                  return (
                    <div
                      key={t.topic_id}
                      className={`p-4 rounded-xl border transition-all ${
                        isHighYield
                          ? "bg-card border-accent/25 hover:border-accent/40 shadow-xs"
                          : "bg-card/60 border-border/80 hover:border-border"
                      }`}
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-muted text-muted-foreground">
                              Unit {t.unit_number}
                            </span>
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                                t.recurrence_status === "RECENTLY_RECURRING"
                                  ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
                                  : t.recurrence_status === "HISTORICALLY_STABLE"
                                  ? "bg-blue-500/10 text-blue-500 border border-blue-500/20"
                                  : t.recurrence_status === "DORMANT"
                                  ? "bg-amber-500/10 text-amber-500 border border-amber-500/20"
                                  : "bg-muted text-muted-foreground"
                              }`}
                            >
                              {t.recurrence_status.replace(/_/g, " ")}
                            </span>
                            {t.recent_occurrence_count > 0 && (
                              <span className="text-[10px] text-emerald-500 font-semibold flex items-center gap-0.5">
                                <Sparkles className="w-3 h-3" /> Recent exam presence
                              </span>
                            )}
                          </div>
                          <button
                            onClick={() => handleOpenTopic(t.topic_id, t.topic_name)}
                            className="text-sm font-bold text-foreground hover:text-accent hover:underline text-left mt-1 flex items-center gap-1.5 group cursor-pointer"
                          >
                            <span>{t.topic_name}</span>
                            <Sparkles className="w-3 h-3 opacity-0 group-hover:opacity-100 text-accent transition-opacity" />
                          </button>
                          <div className="text-[11px] text-muted-foreground mt-0.5">
                            {t.unit_name}
                          </div>
                        </div>

                        {/* Metric Badges */}
                        <div className="flex items-center gap-3">
                          <div className="text-right">
                            <div className="text-xs font-bold font-mono text-accent">
                              {coveragePercent}% ({t.paper_count}/{topicData?.total_papers_analyzed} papers)
                            </div>
                            <div className="text-[10px] text-muted-foreground">
                              {t.occurrence_count} questions • {t.total_marks} marks total
                            </div>
                          </div>

                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleOpenTopic(t.topic_id, t.topic_name)}
                              className="px-2.5 py-1 rounded bg-accent/10 hover:bg-accent/20 text-accent text-xs font-medium flex items-center gap-1 shrink-0 border border-accent/20 cursor-pointer"
                            >
                              <Sparkles className="w-3 h-3" />
                              <span>Intelligence</span>
                            </button>
                            {onSelectTopic && (
                              <button
                                onClick={() => onSelectTopic(t.topic_name)}
                                className="px-2.5 py-1 rounded bg-secondary hover:bg-secondary/80 text-secondary-foreground text-xs font-medium flex items-center gap-1 shrink-0"
                              >
                                <span>Study</span>
                                <ArrowRight className="w-3 h-3" />
                              </button>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Paper appearances bar */}
                      <div className="mt-3 pt-3 border-t border-border/40 flex items-center justify-between text-[11px] text-muted-foreground">
                        <div className="flex items-center gap-2">
                          <Clock className="w-3 h-3" />
                          <span>
                            First seen: {t.first_seen_year || "Historical"} • Last seen:{" "}
                            {t.last_seen_year || "Historical"}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5 font-mono text-[10px]">
                          {Object.entries(t.assessment_type_breakdown).map(([atype, count]) => (
                            <span key={atype} className="px-1.5 py-0.5 bg-background border border-border rounded">
                              {atype}: {count}
                            </span>
                          ))}
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

        {/* TAB 2: QUESTION FAMILIES EXPLORER */}
        {activeTab === "families" && (
          <div className="space-y-4">
            <div className="p-3 bg-background/50 border border-border rounded-lg text-xs space-y-3">
              <div className="text-muted-foreground text-[11px]">
                Question Families &amp; Repeat Types: Grouping exact repeats, numerical variants, and canonical prompts across examination cycles.
              </div>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-2 flex-1 max-w-md">
                  <input
                    type="text"
                    value={familySearchQuery}
                    onChange={(e) => setFamilySearchQuery(e.target.value)}
                    placeholder="Search question prompts or keywords..."
                    className="w-full bg-background border border-border rounded-md px-3 py-1.5 text-xs focus:ring-1 focus:ring-accent focus:outline-none"
                  />
                  {familySearchQuery && (
                    <button
                      onClick={() => setFamilySearchQuery("")}
                      className="text-muted-foreground hover:text-foreground text-[11px] underline shrink-0 cursor-pointer"
                    >
                      Clear
                    </button>
                  )}
                </div>
                <label className="flex items-center gap-2 cursor-pointer select-none shrink-0">
                  <input
                    type="checkbox"
                    checked={familyRepeatOnly}
                    onChange={(e) => setFamilyRepeatOnly(e.target.checked)}
                    className="rounded border-border text-accent focus:ring-accent"
                  />
                  <span className="font-medium text-xs">Multi-repeat only (2+ appearances)</span>
                </label>
              </div>
            </div>

            <div className="space-y-3">
              {displayedFamilies.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground text-xs">
                  {familySearchQuery
                    ? "No question families match your search query."
                    : "No multi-repeat question families match the criteria."}
                </div>
              ) : (
                displayedFamilies.map((fam) => {
                  const isExpanded = expandedFamilyId === fam.family_id;
                  return (
                    <div
                      key={fam.family_id}
                      className="border border-border rounded-xl bg-card overflow-hidden transition-all"
                    >
                      <div
                        onClick={() => setExpandedFamilyId(isExpanded ? null : fam.family_id)}
                        className="p-4 cursor-pointer hover:bg-muted/20 flex items-start justify-between gap-4"
                      >
                        <div className="space-y-1.5 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-secondary text-secondary-foreground">
                              Family #{fam.family_id}
                            </span>
                            {fam.repetition_type === "EXACT_REPEAT" ? (
                              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20">
                                Exact Repeat
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-accent/10 text-accent border border-accent/20">
                                {fam.repetition_type.replace(/_/g, " ")}
                              </span>
                            )}
                            <span className="text-xs font-mono font-bold text-emerald-500">
                              {fam.occurrence_count} Appearances across {fam.paper_count} Exams
                            </span>
                          </div>

                          <div className="text-sm font-semibold text-foreground">
                            <MathText content={fam.canonical_name} />
                          </div>

                          <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
                            <span>Years: {fam.first_seen_year} → {fam.last_seen_year}</span>
                            <span>•</span>
                            <span>Exams: {fam.assessment_history.join(", ") || "General"}</span>
                          </div>

                          {fam.timeline && fam.timeline.length > 0 && (
                            <div className="flex flex-wrap items-center gap-1 pt-1">
                              {fam.timeline.map((entry) => (
                                <span
                                  key={entry.year}
                                  title={
                                    entry.present
                                      ? `Family tested in ${entry.year}`
                                      : entry.exam_exists === false
                                      ? `No exam held in ${entry.year} (gap year)`
                                      : `Exam held in ${entry.year}, but this question family was not examined`
                                  }
                                  className={`inline-flex items-center gap-1 px-1.5 py-0.2 rounded font-mono text-[10px] ${
                                    entry.present
                                      ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                                      : "bg-muted/30 text-muted-foreground/50 border border-border/30"
                                  }`}
                                >
                                  <span className={`h-1 w-1 rounded-full ${entry.present ? "bg-emerald-500" : "bg-muted-foreground/30"}`} />
                                  {entry.year}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>

                        <div className="flex items-center gap-2">
                          <div className="text-right font-mono text-xs text-muted-foreground">
                            {fam.appearances.length} questions
                          </div>
                          {isExpanded ? (
                            <ChevronUp className="w-4 h-4 text-muted-foreground" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-muted-foreground" />
                          )}
                        </div>
                      </div>

                      {/* Expanded Question Appearances */}
                      {isExpanded && (
                        <div className="p-4 pt-0 border-t border-border/50 bg-background/30 space-y-3 mt-2">
                          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider pt-2">
                            Chronological Appearances in SRM Papers:
                          </div>

                          <div className="space-y-2">
                            {fam.appearances.map((app, idx) => (
                              <div
                                key={app.question_id || idx}
                                className="p-3 rounded-lg bg-card border border-border/70 text-xs space-y-1.5"
                              >
                                <div className="flex items-center justify-between text-muted-foreground text-[11px]">
                                  <div className="flex items-center gap-2 font-mono">
                                    <span className="font-bold text-accent">
                                      {app.year || "Historical"} {app.assessment_type || app.term || "Exam"}
                                    </span>
                                    <span>•</span>
                                    <span>Q#{app.question_number}</span>
                                    {app.is_alternative && (
                                      <span className="text-amber-500 font-semibold">[Alternative Choice]</span>
                                    )}
                                  </div>
                                  <span className="font-bold font-mono px-1.5 py-0.5 rounded bg-muted text-foreground">
                                    {app.marks} Marks
                                  </span>
                                </div>

                                <div className="text-foreground leading-relaxed pt-1">
                                  <MathText content={app.original_text} />
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}

        {/* TAB 3: EVOLUTION TIMELINE VIEW */}
        {activeTab === "evolution" && (
          <div className="space-y-4">
            <div className="p-4 bg-muted/20 border border-border rounded-xl text-xs space-y-1">
              <h4 className="font-semibold text-foreground">Curriculum Coverage Evolution</h4>
              <p className="text-muted-foreground">
                Tracks examination topics tested across SRM academic cycles. Identifies newly introduced syllabus areas vs discontinued or stable topics.
              </p>
            </div>

            <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-3 before:bottom-3 before:w-0.5 before:bg-border">
              {(evolutionData?.timeline || []).map((yrEntry) => (
                <div key={yrEntry.year} className="relative space-y-2">
                  <div className="absolute -left-[23px] top-1.5 w-3 h-3 rounded-full bg-accent border-2 border-background" />

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-base font-bold font-mono text-accent">
                        {yrEntry.year}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        ({yrEntry.paper_count} {yrEntry.paper_count === 1 ? "paper" : "papers"} •{" "}
                        {yrEntry.assessment_types.join(", ")})
                      </span>
                    </div>
                    <div className="text-xs font-mono font-bold text-foreground">
                      {yrEntry.total_questions} Questions • {yrEntry.total_marks} Marks
                    </div>
                  </div>

                  <div className="p-4 rounded-xl bg-card border border-border space-y-3">
                    {yrEntry.new_topics_introduced.length > 0 && (
                      <div>
                        <div className="text-[10px] font-mono uppercase font-bold text-emerald-500 mb-1">
                          Newly Introduced in {yrEntry.year}:
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {yrEntry.new_topics_introduced.map((nt) => (
                            <span
                              key={nt}
                              className="px-2 py-0.5 rounded text-[11px] bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
                            >
                              + {nt}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    <div>
                      <div className="text-[10px] font-mono uppercase font-bold text-muted-foreground mb-1">
                        All Topics Tested:
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                        {yrEntry.topics.map((t) => (
                          <div
                            key={t.name}
                            className="p-2 rounded bg-background border border-border/50 flex justify-between items-center"
                          >
                            <span className="font-medium text-foreground">{t.name}</span>
                            <span className="font-mono text-[10px] text-muted-foreground">
                              {t.question_count} Qs ({t.marks}m)
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 4: MARKS & WEIGHT DISTRIBUTION VIEW */}
        {activeTab === "marks" && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-4 bg-muted/20 border border-border rounded-xl">
                <div className="text-muted-foreground text-[10px] uppercase font-mono">Total Questions</div>
                <div className="text-2xl font-bold font-mono mt-1 text-foreground">
                  {marksData?.total_questions_analyzed}
                </div>
                <div className="text-[11px] text-muted-foreground mt-1">Non-alternative basis</div>
              </div>
              <div className="p-4 bg-muted/20 border border-border rounded-xl">
                <div className="text-muted-foreground text-[10px] uppercase font-mono">Total Marks Cataloged</div>
                <div className="text-2xl font-bold font-mono mt-1 text-accent">
                  {marksData?.total_marks}
                </div>
                <div className="text-[11px] text-muted-foreground mt-1">
                  Avg question weight: {marksData?.avg_question_marks} marks
                </div>
              </div>
              <div className="p-4 bg-muted/20 border border-border rounded-xl">
                <div className="text-muted-foreground text-[10px] uppercase font-mono">Assessment Types</div>
                <div className="text-sm font-bold font-mono mt-1 text-foreground">
                  {Object.keys(marksData?.marks_by_assessment_type || {}).join(", ")}
                </div>
                <div className="text-[11px] text-muted-foreground mt-1">
                  End Sem vs Cycle Tests
                </div>
              </div>
            </div>

            {/* Standard Mark Buckets */}
            <div className="p-5 bg-card border border-border rounded-xl space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                Standard SRM Question Mark Buckets
              </h4>
              <div className="space-y-2">
                {(marksData?.common_marks || []).map((b) => (
                  <div key={b.marks} className="space-y-1 text-xs">
                    <div className="flex justify-between font-mono">
                      <span>{b.marks} Marks Questions</span>
                      <span className="font-bold text-accent">
                        {b.count} questions ({b.percentage}%)
                      </span>
                    </div>
                    <div className="w-full bg-background rounded-full h-2 overflow-hidden border border-border">
                      <div
                        className="bg-accent h-full transition-all duration-300"
                        style={{ width: `${b.percentage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Topic Mark Shares */}
            <div className="p-5 bg-card border border-border rounded-xl space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                Highest-Yielding Topics by Aggregate Marks Weight
              </h4>
              <div className="space-y-2">
                {(marksData?.topic_mark_shares || []).slice(0, 10).map((ts) => (
                  <div key={ts.topic_name} className="space-y-1 text-xs">
                    <div className="flex justify-between">
                      <span className="font-medium text-foreground">{ts.topic_name}</span>
                      <span className="font-mono font-bold text-accent">
                        {ts.marks} marks ({ts.percentage}%)
                      </span>
                    </div>
                    <div className="w-full bg-background rounded-full h-1.5 overflow-hidden border border-border">
                      <div
                        className="bg-emerald-500 h-full transition-all duration-300"
                        style={{ width: `${ts.percentage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Topic Intelligence Drilldown Modal */}
      <TopicIntelligenceModal
        isOpen={isTopicModalOpen}
        onClose={() => setIsTopicModalOpen(false)}
        courseId={courseId}
        topicId={selectedTopicIdForModal}
        initialTopicName={selectedTopicNameForModal}
      />
    </div>
  );
}
