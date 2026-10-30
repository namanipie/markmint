"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import {
  BookOpen,
  Video,
  FileText,
  Sparkles,
  CheckCircle2,
  Clock,
  Search,
  Plus,
  Play,
  Share2,
  ExternalLink,
  Target,
  GraduationCap,
  Layers,
  ChevronRight,
  RotateCcw,
  Maximize2,
  Database,
  Archive,
  Upload,
  Check,
  Activity,
  Flame,
  Award
} from "lucide-react";
import { CourseCatalogItem } from "@/lib/courses";
import {
  getCourseResources,
  getTopicResources,
  CourseResourceGroup,
  CourseVideoResource,
  CourseFormulaResource,
  CourseNoteResource,
  CourseExamResource
} from "@/lib/course-resources";
import { ResourceViewerModal, ResourceViewerItem } from "@/components/ui/resource-viewer-modal";
import { SubmitResourceModal } from "@/components/courses/submit-resource-modal";
import { PortionNotesDrawer } from "@/components/analytics/portion-notes-drawer";
import { useResourceMastery } from "@/hooks/use-resource-mastery";
import { getStudyPlan, updateStudyProgress } from "@/lib/api";
import { MathText } from "@/components/ui/math-text";

export type StudyDestination = "recommended" | "lectures" | "notes" | "progress";

export interface RecommendedTopicItem {
  topicName: string;
  priority?: string;
  reason?: string;
  probability?: number;
  historyCount?: number;
  verifiedVideos: CourseVideoResource[];
  verifiedFormulas: CourseFormulaResource[];
  hasVerifiedResources: boolean;
  [key: string]: any;
}

interface MintAIStudyTabProps {
  currentCourse: CourseCatalogItem | null;
  selectedCycle?: string;
  selectedUnits?: number[];
  initialTopicFilter?: string;
}

export function MintAIStudyTab({
  currentCourse,
  selectedCycle = "ALL",
  selectedUnits,
  initialTopicFilter = ""
}: MintAIStudyTabProps) {
  // 1. Destination State (recommended, lectures, notes, progress)
  const [activeDestination, setActiveDestination] = useState<StudyDestination>("recommended");

  // 2. Modals & Viewer State
  const [activeViewerItem, setActiveViewerItem] = useState<ResourceViewerItem | null>(null);
  const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);

  // 3. Search & Filter State
  const [searchQuery, setSearchQuery] = useState(initialTopicFilter || "");
  const [filterUnit, setFilterUnit] = useState<string>("ALL");
  const [recentResource, setRecentResource] = useState<{
    id: string;
    title: string;
    type: "video" | "formula" | "note" | "pyq";
    data: any;
    timestamp: number;
  } | null>(null);

  // 4. Study Plan API State
  const [studyPlan, setStudyPlan] = useState<any>(null);
  const [isLoadingPlan, setIsLoadingPlan] = useState<boolean>(false);

  // 5. Mastery Hook
  const { isMastered, toggleMastered, getProgress } = useResourceMastery();

  // Sync destination from URL parameter `dest` on mount
  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const destParam = params.get("dest") as StudyDestination | null;
    if (destParam && ["recommended", "lectures", "notes", "progress"].includes(destParam)) {
      setActiveDestination(destParam);
    }

    // Load recent resource from localStorage
    try {
      const storedRecent = localStorage.getItem("markmint_recent_resource");
      if (storedRecent) {
        setRecentResource(JSON.parse(storedRecent));
      }
    } catch {
      // Ignore storage errors
    }
  }, []);

  const handleSelectDestination = (dest: StudyDestination) => {
    setActiveDestination(dest);
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      params.set("tab", "study");
      params.set("dest", dest);
      window.history.replaceState(null, "", `/mintai?${params.toString()}`);
    }
  };

  // Get curated static resources (videos, notes, formulas, syllabus)
  const resources: CourseResourceGroup | null = useMemo(() => {
    if (!currentCourse) return null;
    return getCourseResources(currentCourse.slug || String(currentCourse.id));
  }, [currentCourse]);

  // Fetch AI calibrated study plan
  useEffect(() => {
    if (!currentCourse) return;
    let active = true;
    setIsLoadingPlan(true);

    getStudyPlan(
      currentCourse.name,
      selectedCycle !== "ALL" ? selectedCycle : undefined
    )
      .then((data) => {
        if (!active) return;
        setStudyPlan(data);
      })
      .catch((err) => {
        console.warn("Could not load study plan:", err);
      })
      .finally(() => {
        if (active) setIsLoadingPlan(false);
      });

    return () => {
      active = false;
    };
  }, [currentCourse, selectedCycle]);

  // Handle opening viewer item & persisting as recent
  const handleOpenViewer = useCallback(
    (item: ResourceViewerItem) => {
      setActiveViewerItem(item);
      try {
        const record = {
          id:
            item.type === "video"
              ? item.data.id || item.data.youtubeId
              : item.type === "formula"
              ? item.data.id
              : item.data.url,
          title: item.data.title,
          type: item.type,
          data: item.data,
          timestamp: Date.now()
        };
        localStorage.setItem("markmint_recent_resource", JSON.stringify(record));
        setRecentResource(record);
      } catch {
        // Ignore storage errors
      }
    },
    []
  );

  // Deep linking: read query parameters on mount to auto-open specific resources
  useEffect(() => {
    if (typeof window === "undefined" || !resources || !currentCourse) return;
    const params = new URLSearchParams(window.location.search);
    const vParam = params.get("v");
    const fParam = params.get("f");
    const noteParam = params.get("note");

    if (vParam && resources.videos) {
      const targetVideo = resources.videos.find((v) => v.id === vParam || v.youtubeId === vParam);
      if (targetVideo) {
        handleOpenViewer({ type: "video", data: targetVideo, courseName: currentCourse.name });
      }
    } else if (fParam && resources.formulas) {
      const targetFormula = resources.formulas.find((f) => f.id === fParam);
      if (targetFormula) {
        handleOpenViewer({ type: "formula", data: targetFormula, courseName: currentCourse.name });
      }
    } else if (noteParam && resources.notes) {
      const targetNote = resources.notes.find((n) => n.title.toLowerCase().includes(noteParam.toLowerCase()));
      if (targetNote) {
        handleOpenViewer({ type: "note", data: targetNote, courseName: currentCourse.name });
      }
    }
  }, [resources, currentCourse, handleOpenViewer]);

  // Compute all resource ids for course mastery calculation
  const allCourseResourceIds = useMemo(() => {
    const ids: string[] = [];
    (resources?.videos || []).forEach((v) => ids.push(v.id || v.youtubeId));
    (resources?.formulas || []).forEach((f) => ids.push(f.id));
    (resources?.notes || []).forEach((n) => ids.push(n.url));
    return ids;
  }, [resources]);

  const { completed, total, percentage } = getProgress(allCourseResourceIds);

  // Determine course faculty affiliation (Dr. E. Suresh for math, Gate Smashers for CS)
  const isMathCourse = useMemo(() => {
    if (!currentCourse) return false;
    const n = currentCourse.name.toLowerCase();
    return n.includes("calculus") || n.includes("math") || n.includes("transform") || n.includes("probability");
  }, [currentCourse]);

  // Filtered Videos
  const filteredVideos = useMemo(() => {
    if (!resources?.videos) return [];
    let list = resources.videos;

    if (filterUnit !== "ALL") {
      const uNum = Number(filterUnit);
      if (!isNaN(uNum)) {
        list = list.filter((v) => v.unit === uNum);
      }
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter(
        (v) =>
          v.title.toLowerCase().includes(q) ||
          v.channel.toLowerCase().includes(q) ||
          (v.topicName && v.topicName.toLowerCase().includes(q))
      );
    }
    return list;
  }, [resources?.videos, filterUnit, searchQuery]);

  // Filtered Notes
  const filteredNotes = useMemo(() => {
    if (!resources?.notes) return [];
    let list = resources.notes;

    if (filterUnit !== "ALL") {
      const uNum = Number(filterUnit);
      if (!isNaN(uNum)) {
        list = list.filter((n) => n.unit === uNum);
      }
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter(
        (n) =>
          n.title.toLowerCase().includes(q) ||
          n.source.toLowerCase().includes(q) ||
          (n.topicName && n.topicName.toLowerCase().includes(q))
      );
    }
    return list;
  }, [resources?.notes, filterUnit, searchQuery]);

  // Filtered Formulas
  const filteredFormulas = useMemo(() => {
    if (!resources?.formulas) return [];
    let list = resources.formulas;

    if (filterUnit !== "ALL") {
      const uNum = Number(filterUnit);
      if (!isNaN(uNum)) {
        list = list.filter((f) => f.unit === uNum);
      }
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter(
        (f) =>
          f.title.toLowerCase().includes(q) ||
          f.summary.toLowerCase().includes(q) ||
          (f.topicName && f.topicName.toLowerCase().includes(q))
      );
    }
    return list;
  }, [resources?.formulas, filterUnit, searchQuery]);

  // Recommended Plan Topics (augmented with verified resources)
  const recommendedTopics: RecommendedTopicItem[] = useMemo(() => {
    if (!studyPlan?.topics || !Array.isArray(studyPlan.topics)) return [];
    return studyPlan.topics.map((t: any) => {
      const topicName = t.name || t.topic || "";
      const matchedRes = currentCourse ? getTopicResources(currentCourse.slug || String(currentCourse.id), topicName) : null;
      return {
        ...t,
        topicName,
        verifiedVideos: matchedRes?.videos || [],
        verifiedFormulas: matchedRes?.formulas || [],
        hasVerifiedResources: Boolean(matchedRes?.hasResources)
      };
    });
  }, [studyPlan?.topics, currentCourse]);

  if (!currentCourse) {
    return (
      <div className="p-8 text-center rounded-2xl border border-dashed border-border/80 bg-card/40 space-y-2">
        <BookOpen className="w-8 h-8 text-muted-foreground mx-auto" />
        <p className="text-sm font-semibold text-foreground">Select an engineering course to access study materials</p>
        <p className="text-xs text-muted-foreground">Video lectures, professor slides, formula cards, and study mastery tracking.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ========================================================================= */}
      {/* 1. STUDY HUB CONTROL HEADER                                               */}
      {/* ========================================================================= */}
      <div className="p-5 rounded-2xl bg-card border border-border/80 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border/50 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-accent/10 text-accent">
                <BookOpen className="w-5 h-5" />
              </span>
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                Study Hub &amp; Lecture Materials
              </h2>
            </div>
            <p className="text-xs text-muted-foreground">
              Curated masterclasses and learning assets for <strong className="text-foreground">{currentCourse.name}</strong>. Featuring video lectures from{" "}
              <strong className="text-foreground">
                {isMathCourse ? "Dr. E. Suresh (SRMIST Mathematics)" : "Gate Smashers (Computer Science & Engineering)"}
              </strong>
              , professor slides, and formula sheets.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto shrink-0">
            {/* Share Material Button */}
            <button
              type="button"
              onClick={() => setIsSubmitModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-accent text-accent-foreground text-xs font-bold shadow-xs hover:bg-accent/90 transition-all cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Share Material</span>
            </button>

            {/* Course Mastery Pill */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-muted/30 border border-border/60">
              <div className="w-6 h-6 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold font-mono text-[11px]">
                {percentage}%
              </div>
              <span className="text-xs font-semibold text-foreground">
                {completed}/{total || 1} Mastered
              </span>
            </div>
          </div>
        </div>

        {/* 4-Destination Navigation Tabs */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
          {[
            {
              id: "recommended" as StudyDestination,
              label: "Recommended",
              icon: Target,
              badge: `${recommendedTopics.length || (resources?.videos?.length ? 3 : 0)} Priorities`
            },
            {
              id: "lectures" as StudyDestination,
              label: "Video Lectures",
              icon: Video,
              badge: `${resources?.videos?.length || 0} Videos`
            },
            {
              id: "notes" as StudyDestination,
              label: "Notes & Materials",
              icon: FileText,
              badge: `${(resources?.notes?.length || 0) + (resources?.formulas?.length || 0)} Assets`
            },
            {
              id: "progress" as StudyDestination,
              label: "My Progress",
              icon: CheckCircle2,
              badge: `${percentage}% Ready`
            }
          ].map((dest) => {
            const Icon = dest.icon;
            const isActive = activeDestination === dest.id;
            return (
              <button
                key={dest.id}
                type="button"
                data-dest={dest.id}
                onClick={() => handleSelectDestination(dest.id)}
                className={`flex flex-col sm:flex-row items-center justify-between gap-1.5 p-3 rounded-xl border text-left transition-all cursor-pointer ${
                  isActive
                    ? "bg-foreground text-background shadow-xs font-bold border-foreground"
                    : "bg-muted/20 hover:bg-muted/40 text-muted-foreground hover:text-foreground border-border/70"
                }`}
              >
                <div className="flex items-center gap-2">
                  <Icon className={`w-4 h-4 ${isActive ? "text-accent" : "text-muted-foreground"}`} />
                  <span className="text-xs font-semibold">{dest.label}</span>
                </div>
                <span
                  className={`text-[10px] font-mono px-1.5 py-0.2 rounded ${
                    isActive ? "bg-background/20 text-background font-bold" : "bg-muted text-muted-foreground"
                  }`}
                >
                  {dest.badge}
                </span>
              </button>
            );
          })}
        </div>

        {/* Universal Filter & Search Bar */}
        <div className="pt-3 border-t border-border/50 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-semibold text-muted-foreground mr-1">Portion Unit:</span>
            {["ALL", "1", "2", "3", "4", "5"].map((u) => {
              const isSelected = filterUnit === u;
              return (
                <button
                  key={u}
                  type="button"
                  onClick={() => setFilterUnit(u)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                    isSelected
                      ? "bg-accent text-accent-foreground font-bold shadow-2xs"
                      : "bg-muted/30 border border-border/60 text-muted-foreground hover:text-foreground hover:bg-muted/50"
                  }`}
                >
                  {u === "ALL" ? "All Units" : `Unit ${u}`}
                </button>
              );
            })}
          </div>

          <div className="flex items-center gap-2 flex-1 max-w-sm">
            <div className="relative w-full">
              <Search className="w-3.5 h-3.5 text-muted-foreground absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search lectures, notes, or formulas..."
                className="w-full bg-background border border-border/70 rounded-lg pl-8 pr-3 py-1.5 text-xs focus:ring-1 focus:ring-accent focus:outline-none"
              />
            </div>
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                className="text-muted-foreground hover:text-foreground text-[11px] underline shrink-0 cursor-pointer"
              >
                Clear
              </button>
            )}
          </div>
        </div>

        {/* Quick Resume Card (if student previously accessed a resource) */}
        {recentResource && (
          <div className="p-3 rounded-xl bg-accent/5 border border-accent/20 flex items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2.5 min-w-0">
              <span className="p-1.5 rounded-lg bg-accent/15 text-accent shrink-0">
                <RotateCcw className="w-3.5 h-3.5" />
              </span>
              <div className="truncate">
                <span className="font-semibold text-foreground">Resume Previous Study: </span>
                <span className="text-muted-foreground truncate">{recentResource.title}</span>
              </div>
            </div>

            <button
              type="button"
              onClick={() => handleOpenViewer({ type: recentResource.type, data: recentResource.data, courseName: currentCourse.name })}
              className="inline-flex items-center gap-1 font-bold text-accent hover:underline shrink-0 cursor-pointer"
            >
              <span>Resume</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* DESTINATION 1: RECOMMENDED STUDY SEQUENCE & HIGH YIELD TOPICS            */}
      {/* ========================================================================= */}
      {activeDestination === "recommended" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs px-1">
            <span className="text-muted-foreground">
              Calibrated study plan for <strong>{currentCourse.name}</strong> ({selectedCycle === "ALL" ? "Full Syllabus" : selectedCycle})
            </span>
            <span className="text-[11px] font-mono text-accent">Prioritized by Bayesian Exam Probability</span>
          </div>

          {isLoadingPlan ? (
            <div className="py-16 text-center text-xs text-muted-foreground flex items-center justify-center gap-2">
              <Activity className="w-4 h-4 animate-spin text-accent" />
              <span>Synthesizing high-yield study priorities...</span>
            </div>
          ) : recommendedTopics.length === 0 ? (
            <div className="p-8 text-center rounded-2xl border border-dashed border-border/80 bg-card/40 space-y-2">
              <Target className="w-8 h-8 text-muted-foreground mx-auto" />
              <p className="text-sm font-semibold text-foreground">No priority topics calibrated for this cycle</p>
              <p className="text-xs text-muted-foreground">Browse all video classes in the &ldquo;Video Lectures&rdquo; tab or explore professor slides.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {recommendedTopics.map((topic: RecommendedTopicItem, idx: number) => {
                const priority = topic.priority?.toLowerCase() || "medium";
                const isFirstPriority = priority === "high" || idx === 0;

                return (
                  <div
                    key={idx}
                    className={`p-4 sm:p-5 rounded-2xl border transition-all ${
                      isFirstPriority
                        ? "bg-card border-accent/40 shadow-xs"
                        : "bg-card/70 border-border/70 hover:border-border"
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-border/40">
                      <div className="flex flex-wrap items-center gap-2">
                        <span
                          className={`px-2.5 py-0.5 rounded-md font-mono text-[10px] font-bold uppercase tracking-wider ${
                            isFirstPriority
                              ? "bg-accent/20 text-accent border border-accent/30"
                              : "bg-muted text-muted-foreground"
                          }`}
                        >
                          {priority === "high" ? "Study First" : priority === "medium" ? "Study Next" : "Study Later"}
                        </span>

                        {topic.historyCount && topic.historyCount >= 2 && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md font-mono text-[10px] font-bold bg-red-500/10 text-red-400 border border-red-500/20">
                            <Flame className="w-3 h-3" />
                            <span>{topic.historyCount} Exam Appearances</span>
                          </span>
                        )}

                        {topic.probability && (
                          <span className="px-2 py-0.5 rounded-md font-mono text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            Prob: {(topic.probability * 100).toFixed(0)}%
                          </span>
                        )}
                      </div>

                      <div className="text-xs font-mono text-muted-foreground">
                        Sequence #{idx + 1}
                      </div>
                    </div>

                    {/* Topic Title & Rationale */}
                    <div className="py-3 space-y-1.5">
                      <h3 className="text-base font-bold text-foreground">
                        <MathText content={topic.topicName} />
                      </h3>
                      {topic.reason && (
                        <p className="text-xs text-muted-foreground leading-relaxed">
                          {topic.reason}
                        </p>
                      )}
                    </div>

                    {/* Linked Verified Study Resources */}
                    <div className="pt-3 border-t border-border/40 flex flex-wrap items-center justify-between gap-3 text-xs">
                      <div className="flex flex-wrap items-center gap-2">
                        {topic.verifiedVideos.length > 0 ? (
                          topic.verifiedVideos.map((v: CourseVideoResource) => (
                            <button
                              key={v.id}
                              type="button"
                              onClick={() => handleOpenViewer({ type: "video", data: v, courseName: currentCourse.name })}
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-red-500/10 text-red-400 hover:bg-red-500 hover:text-white border border-red-500/30 font-semibold transition-all cursor-pointer"
                            >
                              <Play className="w-3 h-3 fill-current" />
                              <span>{v.channel.includes("Suresh") ? "Dr. E. Suresh Video" : "Lecture Video"} ({v.duration})</span>
                            </button>
                          ))
                        ) : (
                          <button
                            type="button"
                            onClick={() => {
                              handleSelectDestination("lectures");
                              setSearchQuery(topic.topicName);
                            }}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-muted/40 text-muted-foreground hover:text-foreground border border-border/60 transition-colors cursor-pointer"
                          >
                            <Video className="w-3 h-3" />
                            <span>Find Matching Lectures</span>
                          </button>
                        )}

                        {topic.verifiedFormulas.length > 0 &&
                          topic.verifiedFormulas.map((f: CourseFormulaResource) => (
                            <button
                              key={f.id}
                              type="button"
                              onClick={() => handleOpenViewer({ type: "formula", data: f, courseName: currentCourse.name })}
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500/10 text-amber-300 hover:bg-amber-500 hover:text-black border border-amber-500/30 font-semibold transition-all cursor-pointer"
                            >
                              <Sparkles className="w-3 h-3" />
                              <span>Formula Sheet</span>
                            </button>
                          ))}
                      </div>

                      {/* Topic Completion Checkbox */}
                      <button
                        type="button"
                        onClick={async () => {
                          toggleMastered(`topic-${topic.topicName}`);
                          try {
                            await updateStudyProgress(currentCourse.id, {
                              topic: topic.topicName,
                              action: "complete_topic"
                            });
                          } catch {
                            // Non-blocking
                          }
                        }}
                        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
                          isMastered(`topic-${topic.topicName}`)
                            ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
                            : "bg-muted/20 text-muted-foreground hover:text-foreground border-border/60"
                        }`}
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>{isMastered(`topic-${topic.topicName}`) ? "Mastered" : "Mark Mastered"}</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* DESTINATION 2: VIDEO LECTURES & FACULTY PLAYLISTS                         */}
      {/* ========================================================================= */}
      {activeDestination === "lectures" && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3.5 rounded-xl bg-muted/20 border border-border/60 text-xs">
            <div className="space-y-0.5">
              <span className="font-semibold text-foreground">
                Verified Faculty Lecture Playlists
              </span>
              <p className="text-[11px] text-muted-foreground">
                Official YouTube playlists by{" "}
                <strong className="text-foreground">
                  {isMathCourse ? "Dr. E. Suresh (SRM Faculty)" : "Gate Smashers"}
                </strong>
                , organized unit-by-unit with theater mode.
              </p>
            </div>

            <span className="text-[11px] font-mono text-accent">
              {filteredVideos.length} Available Video Lectures
            </span>
          </div>

          {filteredVideos.length === 0 ? (
            <div className="p-8 text-center rounded-2xl border border-dashed border-border/80 bg-card/40 space-y-2">
              <Video className="w-8 h-8 text-muted-foreground mx-auto" />
              <p className="text-sm font-semibold text-foreground">No lectures found matching this filter</p>
              <p className="text-xs text-muted-foreground">Try clearing search terms or selecting &ldquo;All Units&rdquo;.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {filteredVideos.map((video: CourseVideoResource) => {
                const videoId = video.id || video.youtubeId;
                const mastered = isMastered(videoId);

                return (
                  <div
                    key={videoId}
                    className={`p-4 rounded-2xl border transition-all flex flex-col justify-between gap-3 ${
                      mastered
                        ? "bg-card/40 border-emerald-500/30"
                        : "bg-card border-border/80 hover:border-accent/40 shadow-xs"
                    }`}
                  >
                    <div className="space-y-2">
                      <div className="flex items-center justify-between gap-2 text-[10px] text-muted-foreground">
                        <div className="flex items-center gap-1.5">
                          {video.unit && (
                            <span className="px-2 py-0.5 rounded bg-accent/15 text-accent font-mono font-bold">
                              Unit {video.unit}
                            </span>
                          )}
                          <span className="px-2 py-0.5 rounded bg-muted text-foreground font-mono">
                            {video.channel}
                          </span>
                        </div>
                        <div className="flex items-center gap-1 font-mono text-muted-foreground">
                          <Clock className="w-3 h-3 text-accent" />
                          <span>{video.duration}</span>
                        </div>
                      </div>

                      <h4 className="text-sm font-bold text-foreground leading-snug">
                        {video.title}
                      </h4>

                      {video.description && (
                        <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                          {video.description}
                        </p>
                      )}
                    </div>

                    <div className="pt-2.5 border-t border-border/40 flex items-center justify-between gap-2">
                      <button
                        type="button"
                        onClick={() => handleOpenViewer({ type: "video", data: video, courseName: currentCourse.name })}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-accent text-accent-foreground text-xs font-bold hover:bg-accent/90 transition-all cursor-pointer"
                      >
                        <Play className="w-3.5 h-3.5 fill-current" />
                        <span>Watch Lecture</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => toggleMastered(videoId)}
                        className={`p-2 rounded-xl border transition-colors cursor-pointer ${
                          mastered
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                            : "bg-muted/30 text-muted-foreground border-border/60 hover:text-foreground"
                        }`}
                        title={mastered ? "Marked as Watched" : "Mark as Watched"}
                      >
                        <CheckCircle2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* DESTINATION 3: NOTES, PROFESSOR SLIDES & FORMULA SHEETS                  */}
      {/* ========================================================================= */}
      {activeDestination === "notes" && (
        <div className="space-y-5">
          {/* Sourced Portion Notes Drawer */}
          {resources?.notes && resources.notes.length > 0 && (
            <PortionNotesDrawer
              notes={resources.notes}
              courseName={currentCourse.name}
              selectedUnits={selectedUnits || [1, 2, 3, 4, 5]}
              isCT1={selectedCycle === "CT1"}
              isCT2={selectedCycle === "CT2"}
              courseSlug={currentCourse.slug}
              isOpenDefault={true}
            />
          )}

          {/* Formula Cards Section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between px-1 text-xs">
              <span className="font-semibold text-foreground flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-accent" />
                <span>Formula Cards &amp; Cheat Sheets</span>
              </span>
              <span className="text-[11px] text-muted-foreground font-mono">
                {filteredFormulas.length} Formulas Available
              </span>
            </div>

            {filteredFormulas.length === 0 ? (
              <div className="p-6 text-center rounded-2xl border border-dashed border-border/80 bg-card/40 space-y-1">
                <p className="text-xs text-muted-foreground">No formula cards match your current unit filter.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {filteredFormulas.map((f: CourseFormulaResource) => {
                  const mastered = isMastered(f.id);
                  return (
                    <div
                      key={f.id}
                      className={`p-4 rounded-2xl border transition-all space-y-2.5 ${
                        mastered
                          ? "bg-card/40 border-emerald-500/30"
                          : "bg-card border-border/80 hover:border-accent/40 shadow-xs"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2 text-[10px]">
                        <div className="flex items-center gap-1.5">
                          {f.unit && (
                            <span className="px-2 py-0.5 rounded bg-accent/15 text-accent font-mono font-bold">
                              Unit {f.unit}
                            </span>
                          )}
                          <span className="font-semibold text-foreground">{f.title}</span>
                        </div>

                        <button
                          type="button"
                          onClick={() => toggleMastered(f.id)}
                          className={`p-1 rounded border transition-colors cursor-pointer ${
                            mastered
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                              : "bg-muted/30 text-muted-foreground border-border/60 hover:text-foreground"
                          }`}
                          title={mastered ? "Mastered" : "Mark Mastered"}
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                        </button>
                      </div>

                      <div className="p-3 rounded-xl bg-muted/30 border border-border/50 text-xs font-mono text-foreground overflow-x-auto">
                        <MathText content={f.latexSnippet} />
                      </div>

                      <p className="text-[11px] text-muted-foreground leading-relaxed">
                        {f.summary}
                      </p>

                      <div className="pt-2 border-t border-border/40 flex items-center justify-between text-xs">
                        <button
                          type="button"
                          onClick={() => handleOpenViewer({ type: "formula", data: f, courseName: currentCourse.name })}
                          className="font-semibold text-accent hover:underline cursor-pointer"
                        >
                          Inspect Full Formula Card &rarr;
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* DESTINATION 4: MY PROGRESS & MASTERY CHECKLIST                           */}
      {/* ========================================================================= */}
      {activeDestination === "progress" && (
        <div className="space-y-5">
          {/* Progress Overview Card */}
          <div className="p-5 rounded-2xl bg-card border border-border/80 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-sm font-mono">
                    {percentage}%
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-foreground">Course Revision Completion</h3>
                    <p className="text-xs text-muted-foreground">
                      Track your preparation across lectures, notes, and formula cards for <strong className="text-foreground">{currentCourse.name}</strong>.
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="px-3 py-1 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-bold font-mono">
                  {completed} Completed
                </span>
                <span className="px-3 py-1 rounded-xl bg-muted text-muted-foreground text-xs font-bold font-mono">
                  {(total || 0) - completed} Remaining
                </span>
              </div>
            </div>

            <div className="w-full bg-muted rounded-full h-2.5 overflow-hidden border border-border/40">
              <div
                className="bg-emerald-500 h-full transition-all duration-500 rounded-full"
                style={{ width: `${percentage}%` }}
              />
            </div>
          </div>

          {/* Interactive Checklist of All Course Assets */}
          <div className="space-y-3">
            <div className="flex items-center justify-between px-1 text-xs">
              <span className="font-semibold text-foreground">Preparation Checklist</span>
              <span className="text-[11px] text-muted-foreground">Toggle items to update progress</span>
            </div>

            <div className="space-y-2">
              {allCourseResourceIds.length === 0 ? (
                <div className="p-6 text-center rounded-2xl border border-dashed border-border/80 bg-card/40 space-y-1">
                  <p className="text-xs text-muted-foreground">No materials found for checklist calculation.</p>
                </div>
              ) : (
                allCourseResourceIds.map((id: string, idx: number) => {
                  const mastered = isMastered(id);
                  // Find title
                  const matchedVideo = resources?.videos?.find((v) => (v.id || v.youtubeId) === id);
                  const matchedFormula = resources?.formulas?.find((f) => f.id === id);
                  const matchedNote = resources?.notes?.find((n) => n.url === id);

                  const title = matchedVideo?.title || matchedFormula?.title || matchedNote?.title || `Resource Asset #${idx + 1}`;
                  const typeLabel = matchedVideo ? "Video Lecture" : matchedFormula ? "Formula Card" : "Professor Note";

                  return (
                    <div
                      key={id}
                      className={`p-3.5 rounded-xl border transition-all flex items-center justify-between gap-3 ${
                        mastered
                          ? "bg-emerald-500/5 border-emerald-500/25"
                          : "bg-card border-border/70 hover:border-border"
                      }`}
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <button
                          type="button"
                          onClick={() => toggleMastered(id)}
                          className={`w-5 h-5 rounded-md border flex items-center justify-center transition-colors cursor-pointer shrink-0 ${
                            mastered
                              ? "bg-emerald-500 text-white border-emerald-500"
                              : "border-border/80 hover:border-accent text-transparent"
                          }`}
                        >
                          <Check className="w-3.5 h-3.5 stroke-[3]" />
                        </button>

                        <div className="truncate">
                          <span className={`text-xs font-semibold ${mastered ? "line-through text-muted-foreground" : "text-foreground"}`}>
                            {title}
                          </span>
                          <span className="text-[10px] font-mono ml-2 px-1.5 py-0.2 rounded bg-muted text-muted-foreground">
                            {typeLabel}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        {matchedVideo && (
                          <button
                            type="button"
                            onClick={() => handleOpenViewer({ type: "video", data: matchedVideo, courseName: currentCourse.name })}
                            className="text-xs font-semibold text-accent hover:underline cursor-pointer"
                          >
                            Watch
                          </button>
                        )}
                        {matchedFormula && (
                          <button
                            type="button"
                            onClick={() => handleOpenViewer({ type: "formula", data: matchedFormula, courseName: currentCourse.name })}
                            className="text-xs font-semibold text-amber-400 hover:underline cursor-pointer"
                          >
                            View
                          </button>
                        )}
                        {matchedNote && (
                          <button
                            type="button"
                            onClick={() => handleOpenViewer({ type: "note", data: matchedNote, courseName: currentCourse.name })}
                            className="text-xs font-semibold text-accent hover:underline cursor-pointer"
                          >
                            Read
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 5. INTEGRATED RESOURCE VIEWER MODAL (THEATER MODE & DEEP LINKING)         */}
      {/* ========================================================================= */}
      {activeViewerItem && (
        <ResourceViewerModal
          item={activeViewerItem}
          onClose={() => setActiveViewerItem(null)}
        />
      )}

      {/* ========================================================================= */}
      {/* 6. SUBMIT RESOURCE MODAL (STUDENT CONTRIBUTIONS)                          */}
      {/* ========================================================================= */}
      {isSubmitModalOpen && (
        <SubmitResourceModal
          isOpen={isSubmitModalOpen}
          onClose={() => setIsSubmitModalOpen(false)}
          courseName={currentCourse.name}
          courseCode={currentCourse.canonicalCode || currentCourse.code}
          defaultUnit={1}
        />
      )}
    </div>
  );
}
