"use client";

import { useState, useEffect, useRef, useMemo } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import {
  getCourses,
  getIntelligenceSnapshot,
  getCourseTracks,
  getStudyPlan,
  uploadStudyNotes,
  updateStudyProgress,
} from "@/lib/api";
import { BackendCourse, CourseTrack, IntelligenceSnapshot } from "@/lib/types";
import {
  BookOpen,
  Target,
  Zap,
  CheckCircle2,
  Clock,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Layers,
  ArrowRight,
  Loader2,
  AlertCircle,
  FileText,
  Upload,
  FileUp,
  Archive,
  Database,
  ExternalLink,
  Sparkles,
} from "lucide-react";
import { MathText } from "@/components/ui/math-text";
import {
  getStudyContext,
  updateStudyContext,
  setTopicTaskStatus,
  StudyContext,
} from "@/lib/study-context";

interface StudyTarget {
  id: string;
  name: string;
  priority: "HIGH" | "MEDIUM" | "LOW";
  category: "topic" | "family";
  reason: string;
  score: number;
  distinctPapers?: number;
  totalPapers?: number;
  occurrences?: number;
  resources: Array<{
    id?: string;
    title: string;
    source: string;
    url?: string;
    question_count?: number;
  }>;
}

export default function StudyPlanPage() {
  const [courses, setCourses] = useState<BackendCourse[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<string>("");
  const [selectedCourseObj, setSelectedCourseObj] = useState<BackendCourse | null>(null);

  // Tracks for multi-track courses (e.g. Course 8 Foreign Languages)
  const [availableTracks, setAvailableTracks] = useState<CourseTrack[]>([]);
  const [selectedLanguage, setSelectedLanguage] = useState<string>("");

  // Assessment Cycle (ALL, CT1, CT2, ENDSEM)
  const [selectedCycle, setSelectedCycle] = useState<string>("ALL");

  // Focus topic from query param (e.g. redirected from MintAI "Study this")
  const [focusedTopic, setFocusedTopic] = useState<string | null>(null);

  // Loading & data states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [targets, setTargets] = useState<StudyTarget[]>([]);
  const [planMode, setPlanMode] = useState<"topic" | "family" | "standard">("topic");

  // Task statuses: topicName -> "NOT_STARTED" | "IN_PROGRESS" | "COMPLETED"
  const [taskStatuses, setTaskStatuses] = useState<Record<string, "NOT_STARTED" | "IN_PROGRESS" | "COMPLETED">>({});

  // Filter tab for targets
  const [statusFilter, setStatusFilter] = useState<"ALL" | "HIGH" | "MEDIUM" | "COMPLETED">("ALL");

  // Upload notes states (subtle, non-intrusive)
  const [showUpload, setShowUpload] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [uploadError, setUploadError] = useState("");
  const [studentResources, setStudentResources] = useState<any[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Initial mount: load course list and resolve context
  useEffect(() => {
    getCourses()
      .then(async (data) => {
        const courseList = Array.isArray(data) ? data : data.items || data.courses || [];
        setCourses(courseList);

        // Check URL query parameters first
        const urlParams = typeof window !== "undefined" ? new URLSearchParams(window.location.search) : null;
        const paramCourseId = urlParams?.get("course_id");
        const paramCycle = urlParams?.get("cycle");
        const paramLang = urlParams?.get("language");
        const paramTopic = urlParams?.get("topic");

        if (paramTopic) {
          setFocusedTopic(paramTopic);
        }
        if (paramCycle) {
          setSelectedCycle(paramCycle);
        }

        // Determine target course: URL param -> saved study context -> first course
        const targetCourseId =
          paramCourseId || (getStudyContext()?.course_id ? String(getStudyContext()?.course_id) : "");

        if (targetCourseId) {
          const match = courseList.find((c: BackendCourse) => String(c.id) === String(targetCourseId));
          if (match) {
            setSelectedCourseId(String(match.id));
            setSelectedCourseObj(match);

            // Handle multi-track
            let lang = paramLang || getStudyContext()?.language || "";
            if (match.has_tracks || match.id === 8) {
              try {
                const tracks = await getCourseTracks(match.id);
                setAvailableTracks(tracks);
                if (!lang && tracks.length > 0) {
                  lang = tracks[0].track_key;
                }
                setSelectedLanguage(lang);
              } catch (e) {
                console.error("Failed to load course tracks", e);
              }
            }

            // Load plan for this course
            loadStudyRoadmap(match, paramCycle || "ALL", lang);
          }
        }
      })
      .catch((err) => {
        console.error("Failed to load courses catalog", err);
      });
  }, []);

  // Restore client-persisted task statuses
  useEffect(() => {
    const ctx = getStudyContext();
    if (ctx?.task_statuses) {
      setTaskStatuses(ctx.task_statuses);
    }
  }, [selectedCourseId]);

  // Unified loader: attempts getIntelligenceSnapshot, falls back to getStudyPlan
  const loadStudyRoadmap = async (course: BackendCourse, cycle: string, language?: string) => {
    setLoading(true);
    setError("");
    setTargets([]);

    try {
      // 1. Try to fetch unified intelligence snapshot
      let snapshotData: IntelligenceSnapshot | null = null;
      try {
        snapshotData = await getIntelligenceSnapshot(
          course.id,
          undefined,
          undefined,
          "anonymous",
          cycle !== "ALL" ? cycle : undefined,
          language || undefined
        );
      } catch (snapshotErr) {
        console.warn("Snapshot unavailable, falling back to study priorities", snapshotErr);
      }

      if (snapshotData && (snapshotData.study_priorities?.length || snapshotData.predictions?.length)) {
        const mode = (snapshotData.prediction_mode as any) || "topic";
        setPlanMode(mode);

        // Build normalized study targets
        const normalizedTargets: StudyTarget[] = [];

        if (snapshotData.study_priorities && snapshotData.study_priorities.length > 0) {
          snapshotData.study_priorities.forEach((p: any, idx: number) => {
            const topicName = p.topic || p.name || `Target #${idx + 1}`;
            const rawPriority = (p.priority || "MEDIUM").toUpperCase();
            const normalizedPriority: "HIGH" | "MEDIUM" | "LOW" =
              rawPriority.includes("HIGH") ? "HIGH" : rawPriority.includes("LOW") ? "LOW" : "MEDIUM";

            // Clean working resources only
            const validResources = (p.resources || [])
              .filter((r: any) => r && (r.title || r.url))
              .map((r: any, rIdx: number) => ({
                id: r.id || `res-${rIdx}`,
                title: r.title || "Study Material",
                source: r.source || "MarkMint",
                url: r.url,
                question_count: r.question_count,
              }));

            const reasonsText = Array.isArray(p.reasons) && p.reasons.length > 0
              ? p.reasons.join(" ")
              : p.reason || "Exam-calibrated priority target based on historical paper frequency.";

            normalizedTargets.push({
              id: String(p.topic_id || idx),
              name: topicName,
              priority: normalizedPriority,
              category: "topic",
              reason: reasonsText,
              score: p.prediction_score ?? p.probability ?? 0,
              resources: validResources,
            });
          });
        } else if (snapshotData.predictions && snapshotData.predictions.length > 0) {
          // Use predictions if study_priorities is empty
          snapshotData.predictions.forEach((p: any, idx: number) => {
            const isFam = p.category === "family";
            const distinctP = p.distinct_paper_count ?? p.papers_with_topic ?? 1;
            const totalP = p.papers_analyzed ?? snapshotData?.exam_history?.total_papers ?? 0;
            const normalizedPriority: "HIGH" | "MEDIUM" | "LOW" =
              p.confidence === "HIGH" || distinctP >= 3 ? "HIGH" : p.confidence === "LOW" ? "LOW" : "MEDIUM";

            const famReason = isFam
              ? `Recurring question pattern examined across ${distinctP} past papers with ${p.historical_occurrences ?? p.historyCount ?? distinctP} total questions.`
              : p.explanation || `Tested in ${distinctP} past papers.`;

            normalizedTargets.push({
              id: String(p.family_id || p.topic_id || idx),
              name: p.name,
              priority: normalizedPriority,
              category: isFam ? "family" : "topic",
              reason: famReason,
              score: p.prediction_score ?? p.score ?? 0,
              distinctPapers: distinctP,
              totalPapers: totalP,
              occurrences: p.historical_occurrences ?? p.historyCount,
              resources: isFam
                ? [
                    {
                      id: `fam-${p.family_id}`,
                      title: `Past Exam Questions (${distinctP} papers)`,
                      source: "pyq",
                      question_count: p.historical_occurrences ?? p.historyCount,
                    },
                  ]
                : [],
            });
          });
        }

        setTargets(normalizedTargets);
      } else {
        // Fall back to getStudyPlan endpoint
        const fallbackData = await getStudyPlan(course.name, cycle !== "ALL" ? cycle : undefined);
        if (fallbackData && fallbackData.topics && fallbackData.topics.length > 0) {
          setPlanMode(fallbackData.plan_mode || "topic");
          const normalizedTargets: StudyTarget[] = fallbackData.topics.map((t: any, idx: number) => {
            const rawPriority = (t.priority || "Medium").toUpperCase();
            const normalizedPriority: "HIGH" | "MEDIUM" | "LOW" =
              rawPriority.includes("HIGH") ? "HIGH" : rawPriority.includes("LOW") ? "LOW" : "MEDIUM";

            return {
              id: String(t.family_id || idx),
              name: t.name || t.topic || `Target #${idx + 1}`,
              priority: normalizedPriority,
              category: fallbackData.plan_mode === "family" ? "family" : "topic",
              reason: t.reason || "High-frequency target identified from past examinations.",
              score: t.probability ?? t.prediction_score ?? 0,
              distinctPapers: t.distinct_paper_count,
              occurrences: t.historical_occurrences ?? t.historyCount,
              resources: (t.resources || []).filter((r: any) => r && r.title),
            };
          });
          setTargets(normalizedTargets);
          if (fallbackData.student_resources) {
            setStudentResources(fallbackData.student_resources);
          }
        } else {
          setTargets([]);
        }
      }

      // Record study context update
      updateStudyContext({
        course_id: course.id,
        course_name: course.name,
        course_code: course.code,
        language: language || null,
        assessment_cycle: cycle,
        last_activity_type: "select_course",
      });
    } catch (err: any) {
      console.error("Failed to load study plan", err);
      setError(err?.message || "Failed to load study roadmap. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Handle course switch
  const handleCourseSelect = async (courseId: string) => {
    setSelectedCourseId(courseId);
    const course = courses.find((c) => String(c.id) === courseId);
    if (!course) return;

    setSelectedCourseObj(course);
    setUploadResult(null);
    setUploadError("");

    let lang = "";
    if (course.has_tracks || course.id === 8) {
      try {
        const tracks = await getCourseTracks(course.id);
        setAvailableTracks(tracks);
        lang = tracks.length > 0 ? tracks[0].track_key : "";
        setSelectedLanguage(lang);
      } catch (e) {
        console.error("Failed to load tracks for selected course", e);
      }
    } else {
      setAvailableTracks([]);
      setSelectedLanguage("");
    }

    loadStudyRoadmap(course, selectedCycle, lang);
  };

  // Handle track/language switch
  const handleLanguageSelect = (newLang: string) => {
    setSelectedLanguage(newLang);
    if (selectedCourseObj) {
      loadStudyRoadmap(selectedCourseObj, selectedCycle, newLang);
    }
  };

  // Handle assessment cycle switch
  const handleCycleSelect = (newCycle: string) => {
    setSelectedCycle(newCycle);
    if (selectedCourseObj) {
      loadStudyRoadmap(selectedCourseObj, newCycle, selectedLanguage);
    }
  };

  // 3-State Task Status Toggle
  const handleSetStatus = async (
    topicName: string,
    newStatus: "NOT_STARTED" | "IN_PROGRESS" | "COMPLETED"
  ) => {
    // 1. Update local state immediately for instant feedback
    setTaskStatuses((prev) => ({
      ...prev,
      [topicName]: newStatus,
    }));

    // 2. Persist in study context (localStorage)
    setTopicTaskStatus(topicName, newStatus);

    // 3. Persist in backend if course is resolved
    if (selectedCourseObj) {
      try {
        const action =
          newStatus === "COMPLETED"
            ? "complete_topic"
            : newStatus === "NOT_STARTED"
            ? "reset_topic"
            : "view_resource";

        await updateStudyProgress(selectedCourseObj.id, {
          topic: topicName,
          action,
          status: newStatus,
        });
      } catch (e) {
        console.warn("Backend progress recording deferred", e);
      }
    }
  };

  // Handle subtle note upload
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !selectedCourseObj) return;

    setUploading(true);
    setUploadError("");
    setUploadResult(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("course_id", String(selectedCourseObj.id));
    formData.append("course_name", selectedCourseObj.name);

    try {
      const result = await uploadStudyNotes(formData);
      setUploadResult(result);
      // Refresh roadmap to incorporate newly mapped lecture material
      loadStudyRoadmap(selectedCourseObj, selectedCycle, selectedLanguage);
    } catch (err: any) {
      setUploadError(err?.message || "Upload failed. Only PDFs up to 20MB are supported.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  // Progress metrics calculation
  const totalCount = targets.length;
  const completedCount = useMemo(() => {
    return targets.filter((t) => taskStatuses[t.name] === "COMPLETED").length;
  }, [targets, taskStatuses]);

  const inProgressCount = useMemo(() => {
    return targets.filter((t) => taskStatuses[t.name] === "IN_PROGRESS").length;
  }, [targets, taskStatuses]);

  const completionPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  // Filtered targets
  const filteredTargets = useMemo(() => {
    if (statusFilter === "HIGH") {
      return targets.filter((t) => t.priority === "HIGH");
    }
    if (statusFilter === "MEDIUM") {
      return targets.filter((t) => t.priority === "MEDIUM");
    }
    if (statusFilter === "COMPLETED") {
      return targets.filter((t) => taskStatuses[t.name] === "COMPLETED");
    }
    return targets;
  }, [targets, statusFilter, taskStatuses]);

  return (
    <div className="min-h-screen flex flex-col bg-background selection:bg-accent/20 font-sans">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 md:px-10 py-8 space-y-8">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-4 border-b border-border/40">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-accent" />
              <p className="text-xs font-semibold tracking-wider uppercase text-muted-foreground">
                Action Roadmap
              </p>
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              Study Plan
            </h1>
            <p className="text-sm text-muted-foreground">
              Know what to study next based on verified historical exam frequencies.
            </p>
          </div>

          {/* Quick link to MintAI with context preserved */}
          {selectedCourseObj && (
            <Link
              href={`/mintai?course_id=${selectedCourseObj.id}${selectedLanguage ? `&language=${encodeURIComponent(selectedLanguage)}` : ""}${selectedCycle !== "ALL" ? `&cycle=${encodeURIComponent(selectedCycle)}` : ""}`}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-accent hover:underline shrink-0"
            >
              <span>Inspect Forecast in MintAI</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          )}
        </div>

        {/* Course & Context Selector Header */}
        <section className="bg-card border border-border/70 rounded-2xl p-5 space-y-4 shadow-sm">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 flex-1">
              {/* Course Dropdown */}
              <div className="flex-1 min-w-[240px]">
                <label className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1 block">
                  Course
                </label>
                <select
                  value={selectedCourseId}
                  onChange={(e) => handleCourseSelect(e.target.value)}
                  className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:border-accent transition-colors"
                >
                  <option value="" disabled>
                    Choose a course to plan...
                  </option>
                  {courses.map((c) => (
                    <option key={c.id} value={String(c.id)}>
                      {c.code} — {c.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Language Track (for Course 8 Foreign Languages) */}
              {availableTracks.length > 0 && (
                <div className="min-w-[180px]">
                  <label className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1 block">
                    Language Track
                  </label>
                  <select
                    value={selectedLanguage}
                    onChange={(e) => handleLanguageSelect(e.target.value)}
                    className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:border-accent transition-colors"
                  >
                    {availableTracks.map((t) => (
                      <option key={t.track_key} value={t.track_key}>
                        {t.track_name} ({t.track_code})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Assessment Cycle Selector */}
              <div className="min-w-[150px]">
                <label className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1 block">
                  Target Exam
                </label>
                <select
                  value={selectedCycle}
                  onChange={(e) => handleCycleSelect(e.target.value)}
                  className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:border-accent transition-colors"
                >
                  <option value="ALL">All Cycles</option>
                  <option value="CT1">Cycle Test 1 (CT1)</option>
                  <option value="CT2">Cycle Test 2 (CT2)</option>
                  <option value="ENDSEM">End Semester</option>
                </select>
              </div>
            </div>

            {selectedCourseObj && (
              <div className="flex items-center gap-2 pt-2 lg:pt-0 shrink-0">
                <span className="px-2.5 py-1 rounded text-xs font-mono font-semibold bg-secondary text-secondary-foreground border border-border/50">
                  {selectedCourseObj.code}
                </span>
                {selectedLanguage && (
                  <span className="px-2.5 py-1 rounded text-xs font-semibold bg-accent/15 text-accent border border-accent/20">
                    {selectedLanguage}
                  </span>
                )}
              </div>
            )}
          </div>
        </section>

        {/* State 1: No Course Selected */}
        {!selectedCourseObj ? (
          <div className="border border-dashed border-border/70 rounded-2xl p-12 text-center space-y-4 bg-card/30 max-w-2xl mx-auto">
            <div className="w-12 h-12 rounded-full bg-accent/10 text-accent flex items-center justify-center mx-auto">
              <BookOpen className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <h3 className="text-lg font-bold text-foreground">Select a course to start your study plan</h3>
              <p className="text-sm text-muted-foreground max-w-md mx-auto">
                Each study plan translates recurring question patterns and syllabus priorities into an actionable step-by-step checklist.
              </p>
            </div>
            <div className="pt-2 flex flex-wrap justify-center gap-2">
              {courses.slice(0, 5).map((c) => (
                <button
                  key={c.id}
                  onClick={() => handleCourseSelect(String(c.id))}
                  className="px-3 py-1.5 rounded-lg border border-border bg-card text-xs font-medium hover:border-accent/50 hover:text-accent transition-colors"
                >
                  {c.code}
                </button>
              ))}
            </div>
          </div>
        ) : loading ? (
          <div className="flex flex-col justify-center items-center py-24 min-h-[360px] border border-border rounded-2xl bg-card/40 space-y-3">
            <Loader2 className="w-8 h-8 animate-spin text-accent" />
            <p className="text-sm text-muted-foreground">Calibrating study plan priorities...</p>
          </div>
        ) : error ? (
          <div className="border border-red-500/20 bg-red-500/5 rounded-2xl p-8 text-center space-y-2">
            <AlertCircle className="w-8 h-8 text-red-500 mx-auto opacity-80" />
            <h3 className="text-base font-bold text-red-500">Failed to load plan</h3>
            <p className="text-sm text-red-400 max-w-md mx-auto">{error}</p>
          </div>
        ) : targets.length === 0 ? (
          <div className="border border-dashed border-border rounded-2xl p-12 text-center space-y-3 bg-card/30">
            <Target className="w-8 h-8 text-muted-foreground mx-auto opacity-40" />
            <h3 className="text-base font-bold text-foreground">No Study Targets Available</h3>
            <p className="text-sm text-muted-foreground max-w-sm mx-auto">
              Historical exam evidence for this selection is currently being processed. Check back shortly.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Progress Summary Card */}
            <section className="bg-card border border-border/80 rounded-2xl p-6 shadow-sm space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Study Progress
                  </h3>
                  <div className="flex items-baseline gap-2 mt-1">
                    <span className="text-3xl font-mono font-bold text-foreground">
                      {completionPercent}%
                    </span>
                    <span className="text-xs text-muted-foreground">
                      ({completedCount} of {totalCount} completed)
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-4 text-xs font-mono">
                  <span className="flex items-center gap-1.5 text-emerald-500 font-medium">
                    <CheckCircle2 className="w-4 h-4" />
                    {completedCount} Completed
                  </span>
                  <span className="flex items-center gap-1.5 text-amber-500 font-medium">
                    <Clock className="w-4 h-4" />
                    {inProgressCount} In Progress
                  </span>
                  <span className="flex items-center gap-1.5 text-muted-foreground">
                    <Target className="w-4 h-4" />
                    {totalCount - completedCount - inProgressCount} Not Started
                  </span>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-secondary/80 h-2.5 rounded-full overflow-hidden">
                <div
                  className="bg-accent h-full transition-all duration-300 rounded-full"
                  style={{ width: `${completionPercent}%` }}
                />
              </div>
            </section>

            {/* Filter Tabs & Count */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
              <div className="flex items-center gap-1.5 bg-secondary/50 p-1 rounded-lg border border-border/40 self-start">
                <button
                  onClick={() => setStatusFilter("ALL")}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                    statusFilter === "ALL"
                      ? "bg-background text-foreground shadow-sm font-semibold"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  All ({targets.length})
                </button>
                <button
                  onClick={() => setStatusFilter("HIGH")}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                    statusFilter === "HIGH"
                      ? "bg-background text-foreground shadow-sm font-semibold"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  High Priority ({targets.filter((t) => t.priority === "HIGH").length})
                </button>
                <button
                  onClick={() => setStatusFilter("MEDIUM")}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                    statusFilter === "MEDIUM"
                      ? "bg-background text-foreground shadow-sm font-semibold"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Medium ({targets.filter((t) => t.priority === "MEDIUM").length})
                </button>
                <button
                  onClick={() => setStatusFilter("COMPLETED")}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                    statusFilter === "COMPLETED"
                      ? "bg-background text-foreground shadow-sm font-semibold"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Completed ({completedCount})
                </button>
              </div>

              <div className="text-xs text-muted-foreground">
                Showing {filteredTargets.length} study {planMode === "family" ? "question families" : "topics"}
              </div>
            </div>

            {/* Study Target Cards List */}
            <div className="space-y-4">
              {filteredTargets.map((target, idx) => {
                const currentStatus = taskStatuses[target.name] || "NOT_STARTED";
                const isFocused = focusedTopic === target.name;

                return (
                  <div
                    key={target.id || idx}
                    className={`bg-card border rounded-2xl p-5 transition-all space-y-4 ${
                      isFocused
                        ? "border-accent ring-1 ring-accent/40 shadow-md"
                        : currentStatus === "COMPLETED"
                        ? "border-emerald-500/30 bg-emerald-500/[0.02]"
                        : "border-border hover:border-border/90"
                    }`}
                  >
                    {/* Header: Priority pill, category, and 3-state control */}
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                      <div className="space-y-1.5 flex-1 pr-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider ${
                              target.priority === "HIGH"
                                ? "bg-accent/15 text-accent border border-accent/25"
                                : "bg-primary/15 text-primary border border-primary/25"
                            }`}
                          >
                            {target.priority} Priority
                          </span>

                          {target.category === "family" && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-secondary text-secondary-foreground border border-border">
                              <Layers className="w-3 h-3" /> Question Family
                            </span>
                          )}

                          {isFocused && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-accent text-accent-foreground animate-pulse">
                              Selected Target
                            </span>
                          )}
                        </div>

                        <h4 className="text-lg font-bold text-foreground leading-snug">
                          <MathText content={target.name} />
                        </h4>
                      </div>

                      {/* 3-State Task Controls */}
                      <div className="flex items-center gap-1 bg-secondary/60 p-1 rounded-xl border border-border/50 shrink-0 self-start sm:self-auto">
                        <button
                          onClick={() => handleSetStatus(target.name, "NOT_STARTED")}
                          className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                            currentStatus === "NOT_STARTED"
                              ? "bg-background text-foreground shadow-sm font-semibold"
                              : "text-muted-foreground hover:text-foreground"
                          }`}
                          title="Mark as not yet started"
                        >
                          Not Started
                        </button>
                        <button
                          onClick={() => handleSetStatus(target.name, "IN_PROGRESS")}
                          className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                            currentStatus === "IN_PROGRESS"
                              ? "bg-amber-500/20 text-amber-400 font-semibold shadow-sm border border-amber-500/30"
                              : "text-muted-foreground hover:text-foreground"
                          }`}
                          title="Mark as currently studying"
                        >
                          In Progress
                        </button>
                        <button
                          onClick={() => handleSetStatus(target.name, "COMPLETED")}
                          className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                            currentStatus === "COMPLETED"
                              ? "bg-emerald-500/20 text-emerald-400 font-semibold shadow-sm border border-emerald-500/30"
                              : "text-muted-foreground hover:text-foreground"
                          }`}
                          title="Mark as mastered / completed"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5 inline mr-1" />
                          Done
                        </button>
                      </div>
                    </div>

                    {/* Why study this? */}
                    {target.reason && (
                      <div className="text-xs text-muted-foreground bg-background/60 rounded-xl p-3 border border-border/40">
                        <span className="font-semibold text-foreground block mb-0.5 uppercase tracking-wider text-[10px]">
                          Why focus here:
                        </span>
                        <span>{target.reason}</span>
                      </div>
                    )}

                    {/* Resources: only display if working resources actually exist */}
                    {target.resources && target.resources.length > 0 && (
                      <div className="pt-2 border-t border-border/40 space-y-2">
                        <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                          Study Materials & Questions
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {target.resources.map((res, rIdx) => (
                            <div
                              key={res.id || rIdx}
                              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-background border border-border text-xs text-foreground"
                            >
                              <FileText className="w-3.5 h-3.5 text-accent shrink-0" />
                              {res.url ? (
                                <a
                                  href={res.url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="hover:text-accent font-medium transition-colors"
                                >
                                  {res.title}
                                </a>
                              ) : (
                                <span className="font-medium">{res.title}</span>
                              )}
                              {res.question_count && (
                                <span className="text-[10px] font-mono text-muted-foreground">
                                  ({res.question_count} Qs)
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Subtle, Collapsible "Add your own notes" Section */}
            <div className="pt-4">
              <div className="border border-border/60 rounded-2xl p-5 bg-card/40 transition-all space-y-4">
                <button
                  onClick={() => setShowUpload(!showUpload)}
                  className="flex items-center justify-between w-full text-left font-medium text-sm text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                >
                  <span className="flex items-center gap-2">
                    <FileUp className="w-4 h-4 text-accent" />
                    <span>Add your own lecture notes or syllabus material (optional)</span>
                  </span>
                  {showUpload ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>

                {showUpload && (
                  <div className="pt-3 border-t border-border/40 space-y-4">
                    <p className="text-xs text-muted-foreground">
                      Upload your class notes (PDF up to 20MB). We will automatically map the content to your course topics.
                    </p>

                    <label className="flex flex-col items-center justify-center w-full h-28 border-2 border-dashed border-border/70 rounded-xl cursor-pointer hover:bg-background/40 hover:border-accent/40 transition-colors">
                      <div className="flex flex-col items-center justify-center py-4">
                        {uploading ? (
                          <Loader2 className="w-6 h-6 text-accent animate-spin mb-1.5" />
                        ) : (
                          <Upload className="w-6 h-6 text-muted-foreground mb-1.5" />
                        )}
                        <p className="text-xs text-muted-foreground font-medium">
                          {uploading ? "Processing PDF..." : "Click or drag PDF to upload"}
                        </p>
                      </div>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept=".pdf"
                        className="hidden"
                        onChange={handleFileUpload}
                        disabled={uploading}
                      />
                    </label>

                    {uploadError && (
                      <div className="text-xs text-red-500 bg-red-500/10 p-2.5 rounded-lg border border-red-500/20">
                        {uploadError}
                      </div>
                    )}

                    {uploadResult && (
                      <div className="text-xs text-emerald-400 bg-emerald-500/10 p-3 rounded-lg border border-emerald-500/20">
                        <strong className="block mb-0.5 flex items-center gap-1.5 font-bold">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Successfully Processed
                        </strong>
                        Mapped to your active study targets.
                      </div>
                    )}

                    {studentResources.length > 0 && (
                      <div className="pt-2 space-y-2">
                        <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                          Your Uploaded Files
                        </p>
                        <ul className="space-y-1.5">
                          {studentResources.map((res: any, idx: number) => (
                            <li key={idx} className="flex items-center gap-2 text-xs text-muted-foreground">
                              <FileText className="w-3.5 h-3.5 text-accent shrink-0" />
                              <span className="font-medium text-foreground">{res.title || "Uploaded Document"}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}
