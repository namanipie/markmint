"use client";

import { useState, useEffect } from "react";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { Drawer } from "@/components/ui/drawer";
import { Combobox } from "@/components/ui/combobox";
import {
  Leaf, Search, AlertCircle, BarChart3, Database, FileText, Activity, Clock,
  CheckCircle2, ChevronDown, ChevronUp, BookOpen, Target, Calendar, HelpCircle,
  X, ShieldCheck, Sparkles, ExternalLink, ArrowRight, Repeat, Layers
} from "lucide-react";
import {
  getCurriculumBranches,
  getCurriculumSemesters,
  getCurriculumSubjects,
  getIntelligenceSnapshot,
  getHistoricalQuestions,
  updateStudyProgress
} from "@/lib/api";
import {
  CurriculumSubject,
  IntelligenceSnapshot,
  PredictionItem,
  HistoricalQuestion,
  CoverageSummary
} from "@/lib/types";
import { RepetitionAnalyticsView } from "@/components/analytics/repetition-analytics-view";
import { TopicIntelligenceModal } from "@/components/analytics/topic-intelligence-modal";
import { FamilyEvidenceModal } from "@/components/analytics/family-evidence-modal";
import { MathText } from "@/components/ui/math-text";
import { useAnalytics } from "@/hooks/use-analytics";

export type MintAIState =
  | "loading_branches"
  | "loading_semesters"
  | "loading_subjects"
  | "loading_intelligence"
  | "branch_error"
  | "semester_error"
  | "subject_error"
  | "analysis_error"
  | "unmatched"
  | "ambiguous"
  | "catalog_only"
  | "insufficient_evidence"
  | "ready"
  | "idle";

export default function MintAIPage() {
  const { trackEvent, trackOnce } = useAnalytics();
  // Curriculum hierarchy states from backend
  const [branches, setBranches] = useState<string[]>([]);
  const [semesters, setSemesters] = useState<number[]>([]);
  const [subjects, setSubjects] = useState<CurriculumSubject[]>([]);

  // User selections
  const [selectedBranch, setSelectedBranch] = useState<string>("");
  const [selectedSemester, setSelectedSemester] = useState<string>("");
  const [selectedSubject, setSelectedSubject] = useState<CurriculumSubject | null>(null);
  const [selectedExam, setSelectedExam] = useState<string>("");
  const [targetExamDate, setTargetExamDate] = useState<string>("");
  const [mainView, setMainView] = useState<"forecast" | "analytics">("forecast");

  // Loading & error states
  const [isLoadingBranches, setIsLoadingBranches] = useState(true);
  const [isLoadingSemesters, setIsLoadingSemesters] = useState(false);
  const [isLoadingSubjects, setIsLoadingSubjects] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const [branchLoadError, setBranchLoadError] = useState("");
  const [semesterLoadError, setSemesterLoadError] = useState("");
  const [subjectLoadError, setSubjectLoadError] = useState("");
  const [error, setError] = useState("");

  // Intelligence data state
  const [snapshot, setSnapshot] = useState<IntelligenceSnapshot | null>(null);
  const [expandedTopic, setExpandedTopic] = useState<string | null>(null);

  // Historical questions modal & filters
  const [isQuestionsModalOpen, setIsQuestionsModalOpen] = useState(false);
  const [selectedTopicForQuestions, setSelectedTopicForQuestions] = useState<string | null>(null);
  const [historicalQuestions, setHistoricalQuestions] = useState<HistoricalQuestion[]>([]);
  const [isLoadingQuestions, setIsLoadingQuestions] = useState(false);
  const [questionFilterYear, setQuestionFilterYear] = useState<string>("");
  const [questionFilterMinMarks, setQuestionFilterMinMarks] = useState<string>("");
  const [questionFilterRepetition, setQuestionFilterRepetition] = useState<string>("");

  // Resources modal
  const [isResourcesModalOpen, setIsResourcesModalOpen] = useState(false);
  const [selectedTopicForResources, setSelectedTopicForResources] = useState<string | null>(null);
  const [topicResources, setTopicResources] = useState<any[]>([]);

  // Topic Intelligence Drilldown Modal
  const [isTopicModalOpen, setIsTopicModalOpen] = useState(false);
  const [selectedTopicIdForModal, setSelectedTopicIdForModal] = useState<number | string | null>(null);
  const [selectedTopicNameForModal, setSelectedTopicNameForModal] = useState<string>("");

  const handleOpenTopicIntelligence = (topicId?: number | string | null, topicName?: string) => {
    setSelectedTopicIdForModal(topicId || null);
    setSelectedTopicNameForModal(topicName || "");
    setIsTopicModalOpen(true);
    trackEvent("why_opened", { type: "topic", item_id: topicId, item_name: topicName, course_id: selectedSubject?.curriculum_id });
  };

  // Family Evidence Drilldown Modal
  const [isFamilyModalOpen, setIsFamilyModalOpen] = useState(false);
  const [selectedFamilyIdForModal, setSelectedFamilyIdForModal] = useState<number | string | null>(null);
  const [selectedFamilyNameForModal, setSelectedFamilyNameForModal] = useState<string>("");

  const handleOpenFamilyEvidence = (familyId?: number | string | null, familyName?: string) => {
    setSelectedFamilyIdForModal(familyId || null);
    setSelectedFamilyNameForModal(familyName || "");
    setIsFamilyModalOpen(true);
    trackEvent("why_opened", { type: "family", item_id: familyId, item_name: familyName, course_id: selectedSubject?.curriculum_id });
  };

  // Subject analytical readiness
  const isSubjectAvailable = Boolean(
    selectedSubject &&
    selectedSubject.status === "MATCHED" &&
    selectedSubject.course_id !== null &&
    selectedSubject.has_exams === true
  );

  // Explicit state derivation eliminating contradictory states
  const currentState: MintAIState = (() => {
    if (isLoadingBranches) return "loading_branches";
    if (branchLoadError) return "branch_error";
    if (isLoadingSemesters) return "loading_semesters";
    if (semesterLoadError) return "semester_error";
    if (isLoadingSubjects) return "loading_subjects";
    if (subjectLoadError) return "subject_error";
    if (isAnalyzing) return "loading_intelligence";
    if (error) return "analysis_error";
    if (!selectedSubject) return "idle";
    if (selectedSubject.status === "UNMATCHED") return "unmatched";
    if (selectedSubject.status === "AMBIGUOUS") return "ambiguous";
    if (snapshot) {
      if (snapshot.data_availability_status === "INSUFFICIENT_EVIDENCE") return "insufficient_evidence";
      if (snapshot.data_availability_status === "CATALOG_ONLY") return "catalog_only";
      if (snapshot.data_availability_status === "READY") return "ready";
    }
    if (selectedSubject.status === "MATCHED" && !selectedSubject.has_exams) return "catalog_only";
    return "idle";
  })();

  // Accessible keyboard listener for modal dialogs (Escape key)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (isQuestionsModalOpen) setIsQuestionsModalOpen(false);
        if (isResourcesModalOpen) setIsResourcesModalOpen(false);
        if (isTopicModalOpen) setIsTopicModalOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isQuestionsModalOpen, isResourcesModalOpen, isTopicModalOpen]);

  // 1. Initial Mount: Load branches from backend
  useEffect(() => {
    let active = true;
    setIsLoadingBranches(true);
    setBranchLoadError("");

    getCurriculumBranches()
      .then((branchList) => {
        if (!active) return;
        setBranches(branchList);
        if (branchList.length > 0) {
          const defaultBranch = branchList.includes("Aerospace Engineering")
            ? "Aerospace Engineering"
            : branchList[0];
          setSelectedBranch(defaultBranch);
        }
      })
      .catch((err) => {
        if (!active) return;
        console.error("Failed to load branches from backend", err);
        setBranchLoadError("Unable to load academic branches. Ensure the backend is running.");
      })
      .finally(() => {
        if (active) setIsLoadingBranches(false);
      });

    return () => {
      active = false;
    };
  }, []);

  // 2. When Branch changes: Load semesters for that branch
  useEffect(() => {
    if (!selectedBranch) {
      setSemesters([]);
      setSelectedSemester("");
      setSubjects([]);
      setSelectedSubject(null);
      return;
    }

    let active = true;
    setIsLoadingSemesters(true);
    setSemesterLoadError("");
    setSelectedSemester("");
    setSubjects([]);
    setSelectedSubject(null);
    setSelectedExam("");
    setSnapshot(null);

    getCurriculumSemesters(selectedBranch)
      .then((semList) => {
        if (!active) return;
        setSemesters(semList);
        if (semList.length > 0) {
          setSelectedSemester(String(semList[0]));
        }
      })
      .catch((err) => {
        if (!active) return;
        console.error(`Failed to load semesters for branch: ${selectedBranch}`, err);
        setSemesterLoadError(`Failed to load semesters for branch: ${selectedBranch}`);
      })
      .finally(() => {
        if (active) setIsLoadingSemesters(false);
      });

    return () => {
      active = false;
    };
  }, [selectedBranch]);

  // 3. When Semester changes: Load subjects for that branch and semester
  useEffect(() => {
    if (!selectedBranch || !selectedSemester) {
      setSubjects([]);
      setSelectedSubject(null);
      return;
    }

    let active = true;
    setIsLoadingSubjects(true);
    setSubjectLoadError("");
    setSelectedSubject(null);
    setSelectedExam("");
    setSnapshot(null);

    getCurriculumSubjects(selectedBranch, selectedSemester)
      .then((subjectList) => {
        if (!active) return;
        setSubjects(subjectList);
        if (subjectList.length > 0) {
          setSelectedSubject(subjectList[0]);
        }
      })
      .catch((err) => {
        if (!active) return;
        console.error(`Failed to load subjects for ${selectedBranch} Sem ${selectedSemester}`, err);
        setSubjectLoadError(`Unable to load subjects for semester ${selectedSemester}`);
      })
      .finally(() => {
        if (active) setIsLoadingSubjects(false);
      });

    return () => {
      active = false;
    };
  }, [selectedBranch, selectedSemester]);

  // 4. Run Full Intelligence Analysis
  const handleAnalyze = async () => {
    if (!selectedSubject) return;

    // Guard against running predictions on unverified courses
    if (selectedSubject.status !== "MATCHED" || !selectedSubject.course_id || !selectedSubject.has_exams) {
      return;
    }

    setIsAnalyzing(true);
    setError("");

    try {
      const data = await getIntelligenceSnapshot(
        selectedSubject.course_id,
        undefined,
        targetExamDate || undefined,
        "anonymous"
      );
      setSnapshot(data);
      if (data.available_assessment_types && data.available_assessment_types.length > 0 && !selectedExam) {
        setSelectedExam(data.available_assessment_types[0]);
      }
    } catch (err: any) {
      console.error("Intelligence snapshot generation failed", err);
      setError(err?.message || "Failed to synthesize academic intelligence.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  // 5. Open Historical Questions for a Topic or Question Family
  const handleViewQuestions = async (topicName?: string, familyId?: number | null, familyName?: string) => {
    if (!selectedSubject || !selectedSubject.course_id) return;
    setIsLoadingQuestions(true);
    setSelectedTopicForQuestions(familyName || topicName || null);
    setQuestionFilterYear("");
    setQuestionFilterMinMarks("");
    setQuestionFilterRepetition("");
    setIsQuestionsModalOpen(true);

    try {
      const res = await getHistoricalQuestions(
        selectedSubject.course_id,
        familyId ? undefined : topicName,
        selectedExam || undefined,
        50,
        familyId ? { family_id: familyId } : (familyName ? { family_name: familyName } : undefined)
      );
      setHistoricalQuestions(res.questions || []);
    } catch (err) {
      console.error("Failed to load historical questions", err);
      setHistoricalQuestions([]);
    } finally {
      setIsLoadingQuestions(false);
    }
  };

  // Filtered questions for modal
  const filteredQuestions = historicalQuestions.filter((q) => {
    if (questionFilterYear && String(q.year) !== questionFilterYear) return false;
    if (questionFilterMinMarks && (q.marks ?? 0) < Number(questionFilterMinMarks)) return false;
    if (questionFilterRepetition && q.repetition_type !== questionFilterRepetition) return false;
    return true;
  });

  const availableQuestionYears = Array.from(
    new Set(historicalQuestions.map((q) => q.year).filter((y): y is number => y !== null && y !== undefined))
  ).sort((a, b) => b - a);

  const availableRepetitionTypes = Array.from(
    new Set(historicalQuestions.map((q) => q.repetition_type).filter((t): t is string => Boolean(t)))
  );

  // 6. Open Resources for a Topic
  const handleViewResources = (topicName: string, resources: any[]) => {
    setSelectedTopicForResources(topicName);
    setTopicResources(resources || []);
    setIsResourcesModalOpen(true);
  };

  // 7. Toggle Student Mastery State
  const handleToggleTopicStatus = async (topicName: string, currentStatus?: string) => {
    if (!selectedSubject || !selectedSubject.course_id) return;
    const nextStatus = currentStatus === "COMPLETED" ? "NOT_STARTED" : "COMPLETED";

    try {
      await updateStudyProgress(selectedSubject.course_id, {
        topic: topicName,
        action: nextStatus === "COMPLETED" ? "complete_topic" : "reset_topic",
      });
      // Refresh snapshot to show re-evaluated priority and coverage
      const updated = await getIntelligenceSnapshot(
        selectedSubject.course_id,
        undefined,
        targetExamDate || undefined,
        "anonymous"
      );
      setSnapshot(updated);
    } catch (err) {
      console.error("Failed to update topic progress", err);
    }
  };

  // Find priority details for a topic from snapshot.study_priorities
  const getTopicPriorityInfo = (topicName: string) => {
    if (!snapshot?.study_priorities) return null;
    return snapshot.study_priorities.find((p: any) => p.topic === topicName) || null;
  };

  return (
    <div className="flex flex-col min-h-screen bg-background text-foreground">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
        <h1 className="sr-only">MintAI Prediction Engine</h1>
        {/* Left Sidebar: Controls & Hierarchy */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
            <div className="mb-6">
              <h2 className="text-[10px] font-bold tracking-widest uppercase text-muted-foreground mb-1">Your Subject</h2>
              <h3 className="text-lg font-bold text-foreground">Choose your course to see what has appeared in past exams.</h3>
            </div>

            {/* Error notifications */}
            {branchLoadError && (
              <div className="mb-4 p-3 bg-destructive/10 border border-destructive/20 text-destructive text-xs rounded-lg flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{branchLoadError}</span>
              </div>
            )}

            <div className="space-y-4">
              {/* Branch Selector */}
              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-1">
                  Academic Branch
                </label>
                <Combobox
                  options={branches.map((b) => ({ value: b, label: b }))}
                  value={selectedBranch}
                  onChange={(val: string) => setSelectedBranch(val)}
                  placeholder={isLoadingBranches ? "Loading branches..." : "Search branches..."}
                  disabled={isLoadingBranches || branches.length === 0}
                />
              </div>

              {/* Semester Selector */}
              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-1">
                  Semester
                </label>
                <Combobox
                  options={semesters.map((s) => ({ value: String(s), label: `Semester ${s}` }))}
                  value={selectedSemester}
                  onChange={(val: string) => setSelectedSemester(val)}
                  placeholder={isLoadingSemesters ? "Loading semesters..." : "Select semester..."}
                  disabled={isLoadingSemesters || semesters.length === 0}
                />
              </div>

              {/* Subject Selector */}
              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-1">
                  Course / Subject
                </label>
                <Combobox
                  options={subjects.map((s) => ({ 
                    value: String(s.curriculum_id), 
                    label: `${s.canonical_code ? `[${s.canonical_code}] ` : ""}${s.subject_name}${s.status === "MATCHED" && s.has_exams ? ` (${s.exam_count} exams)` : s.status === "AMBIGUOUS" ? " [Ambiguous]" : " [Awaiting Papers]"}` 
                  }))}
                  value={selectedSubject?.curriculum_id ? String(selectedSubject.curriculum_id) : ""}
                  onChange={(val: string) => {
                    const match = subjects.find((s) => String(s.curriculum_id) === String(val));
                    setSelectedSubject(match || null);
                    setSnapshot(null);
                    if (match) trackEvent("course_selected", { course_id: match.curriculum_id, course_name: match.subject_name });
                  }}
                  placeholder={isLoadingSubjects ? "Loading courses..." : "Search courses..."}
                  disabled={isLoadingSubjects || subjects.length === 0}
                />
              </div>

              {/* Target Exam Date (Optional) */}
              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-1">
                  Target Exam Date <span className="text-[10px] text-muted-foreground/60">(Optional)</span>
                </label>
                <div className="relative">
                  <input
                    type="date"
                    aria-label="Target Exam Date"
                    className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-accent font-mono text-xs"
                    value={targetExamDate}
                    onChange={(e) => setTargetExamDate(e.target.value)}
                  />
                </div>
              </div>

              {/* Assessment Type (Dynamic from Snapshot or DNA) */}
              {snapshot?.available_assessment_types && snapshot.available_assessment_types.length > 0 && (
                <div>
                  <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-1">
                    Assessment Cycle
                  </label>
                  <select
                    aria-label="Assessment Cycle"
                    className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-accent font-mono"
                    value={selectedExam}
                    onChange={(e) => setSelectedExam(e.target.value)}
                  >
                    {snapshot.available_assessment_types.map((et) => (
                      <option key={et} value={et}>
                        {et}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Action Button */}
              <button
                className="w-full bg-accent text-accent-foreground font-semibold py-2.5 rounded-lg transition-opacity hover:opacity-90 flex items-center justify-center gap-2 mt-4 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
                onClick={handleAnalyze}
                disabled={!isSubjectAvailable || isAnalyzing}
              >
                {isAnalyzing ? (
                  <>
                    <Activity className="w-4 h-4 animate-spin" />
                    <span>Synthesizing Intelligence...</span>
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4" />
                    <span>Generate Forecast</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Canonical Identity Card */}
          {selectedSubject && (
            <div className="bg-card border border-border rounded-xl p-5 shadow-sm text-xs space-y-2">
              <div className="flex items-center justify-between pb-2 border-b border-border">
                <span className="font-semibold text-muted-foreground uppercase tracking-wider text-[10px]">Academic Registry</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                  selectedSubject.status === "MATCHED" && selectedSubject.has_exams
                    ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
                    : selectedSubject.status === "AMBIGUOUS"
                    ? "bg-amber-500/10 text-amber-500 border border-amber-500/20"
                    : "bg-muted text-muted-foreground"
                }`}>
                  {selectedSubject.status}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Curriculum ID:</span>
                <span className="font-mono">{selectedSubject.curriculum_id}</span>
              </div>
              {selectedSubject.canonical_code && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Canonical Code:</span>
                  <span className="font-mono font-bold text-accent">{selectedSubject.canonical_code}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-muted-foreground">Historical Exams:</span>
                <span className="font-mono font-bold">{selectedSubject.exam_count}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Historical Questions:</span>
                <span className="font-mono">{selectedSubject.question_count}</span>
              </div>
              {selectedSubject.has_exams && (
                <div className="pt-2 border-t border-border/50 space-y-1.5">
                  <button
                    onClick={() => setMainView("analytics")}
                    className="w-full text-accent hover:underline flex items-center justify-center gap-1.5 font-medium text-xs py-1.5 rounded bg-accent/5 hover:bg-accent/10 border border-accent/20 transition-colors"
                  >
                    <Repeat className="w-3.5 h-3.5" />
                    <span>What Repeated (&ldquo;What Repeated?&rdquo;)</span>
                  </button>
                  <button
                    onClick={() => handleViewQuestions()}
                    className="w-full text-muted-foreground hover:text-foreground hover:underline flex items-center justify-center gap-1 text-[11px] py-0.5"
                  >
                    <BookOpen className="w-3 h-3" />
                    <span>Browse All Historical Questions {selectedExam ? `(${selectedExam})` : ''}</span>
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Main Panel */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          {error && (
            <div className="p-4 bg-destructive/10 border border-destructive/20 text-destructive rounded-xl flex items-center gap-3">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <div>
                <h4 className="font-semibold text-sm">Forecast Synthesis Error</h4>
                <p className="text-xs opacity-90">{error}</p>
              </div>
            </div>
          )}

          {/* Top Switcher: Forecast vs What Repeated */}
          {selectedSubject?.has_exams && selectedSubject.course_id && (
            <div className="flex items-center gap-2 border-b border-border pb-3">
              <button
                onClick={() => setMainView("forecast")}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
                  mainView === "forecast"
                    ? "bg-accent text-accent-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground bg-muted/40"
                }`}
              >
                <Target className="w-3.5 h-3.5" />
                <span>What to Study &amp; Study Plan</span>
              </button>
              <button
                onClick={() => setMainView("analytics")}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
                  mainView === "analytics"
                    ? "bg-accent text-accent-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground bg-muted/40"
                }`}
              >
                <Repeat className="w-3.5 h-3.5" />
                <span>What Repeated (&ldquo;What Repeated?&rdquo;)</span>
                <span className="px-1.5 py-0.2 rounded text-[10px] bg-emerald-500/10 text-emerald-500 font-mono font-bold">
                  Factual
                </span>
              </button>
            </div>
          )}

          {mainView === "analytics" && selectedSubject?.has_exams && selectedSubject.course_id ? (
            <RepetitionAnalyticsView
              courseId={selectedSubject.course_id}
              courseName={selectedSubject.subject_name}
              canonicalCode={selectedSubject.canonical_code}
              onSelectTopic={(topicName) => {
                setMainView("forecast");
                setExpandedTopic(topicName);
              }}
            />
          ) : (
            <>
              {snapshot && snapshot.data_availability_status === "READY" ? (() => {
                const isFamilyMode = snapshot.prediction_mode === "family";

                return (
            <div className="flex flex-col gap-6">
              {/* Preparation & Coverage / Evidence Meter */}
              {isFamilyMode ? (
                <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Layers className="w-4 h-4 text-accent" />
                      <h3 className="text-sm font-bold tracking-tight">Empirical Evidence &amp; Question Family Scope</h3>
                    </div>
                    <div className="font-mono text-xs px-2.5 py-0.5 rounded bg-accent/10 text-accent font-semibold border border-accent/20">
                      {snapshot.predictions.length} High-Yield Families
                    </div>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
                    <div className="bg-background/60 p-2.5 rounded-lg border border-border/40">
                      <div className="text-muted-foreground text-[10px] uppercase">High-Yield Families</div>
                      <div className="font-mono font-bold text-base text-accent">{snapshot.predictions.length}</div>
                    </div>
                    <div className="bg-background/60 p-2.5 rounded-lg border border-border/40">
                      <div className="text-muted-foreground text-[10px] uppercase">Multi-Repeat Families</div>
                      <div className="font-mono font-bold text-base text-emerald-500">
                        {snapshot.predictions.filter((p) => (p.distinct_paper_count ?? 0) >= 2 || (p.historical_occurrences ?? 0) >= 2).length}
                      </div>
                    </div>
                    <div className="bg-background/60 p-2.5 rounded-lg border border-border/40">
                      <div className="text-muted-foreground text-[10px] uppercase">Exams Analyzed</div>
                      <div className="font-mono font-bold text-base text-foreground">
                        {snapshot.exam_history?.historical_papers_analyzed ?? snapshot.exam_history?.total_papers ?? 0}
                      </div>
                    </div>
                    <div className="bg-background/60 p-2.5 rounded-lg border border-border/40">
                      <div className="text-muted-foreground text-[10px] uppercase">Verified Questions</div>
                      <div className="font-mono font-bold text-base text-foreground">
                        {snapshot.exam_history?.total_questions ?? 0}
                      </div>
                    </div>
                  </div>

                  {/* Truthful Taxonomy Availability Banner */}
                  <div className="mt-3 pt-3 border-t border-border/40 text-xs text-muted-foreground flex items-center gap-2">
                    <span className="inline-block w-1.5 h-1.5 rounded-full bg-accent shrink-0" />
                    {snapshot.has_topic_taxonomy ? (
                      <span>
                        <strong>Topic taxonomy active ({snapshot.taxonomy_topic_count ?? 0} syllabus topics cataloged):</strong> Topic-level predictions are not currently available for this course. Historical Question Family recurrence is available.
                      </span>
                    ) : (
                      <span>
                        <strong>Syllabus taxonomy pending:</strong> Detailed syllabus topic taxonomy is currently being cataloged for this course. Historical Question Family recurrence analytics are active and verified.
                      </span>
                    )}
                  </div>
                </div>
              ) : snapshot.coverage_summary ? (
                <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Target className="w-4 h-4 text-accent" />
                      <h3 className="text-sm font-bold tracking-tight">Your Progress</h3>
                    </div>
                    <div className="font-mono font-bold text-sm text-accent">
                      {snapshot.coverage_summary.student_preparation_coverage}% Prepared
                    </div>
                  </div>

                  <div className="w-full bg-background rounded-full h-2 mb-3 overflow-hidden border border-border">
                    <div
                      className="bg-accent h-full transition-all duration-500"
                      style={{ width: `${snapshot.coverage_summary.student_preparation_coverage}%` }}
                    />
                  </div>

                  <div className="grid grid-cols-4 gap-2 text-center text-xs">
                    <div className="bg-background/60 p-2 rounded border border-border/40">
                      <div className="text-muted-foreground text-[10px] uppercase">Predicted</div>
                      <div className="font-mono font-bold">{snapshot.coverage_summary.total_predicted_topics}</div>
                    </div>
                    <div className="bg-background/60 p-2 rounded border border-border/40">
                      <div className="text-muted-foreground text-[10px] uppercase">Mastered</div>
                      <div className="font-mono font-bold text-emerald-500">{snapshot.coverage_summary.mastered_topics}</div>
                    </div>
                    <div className="bg-background/60 p-2 rounded border border-border/40">
                      <div className="text-muted-foreground text-[10px] uppercase">In Progress</div>
                      <div className="font-mono font-bold text-amber-500">{snapshot.coverage_summary.in_progress_topics}</div>
                    </div>
                    <div className="bg-background/60 p-2 rounded border border-border/40">
                      <div className="text-muted-foreground text-[10px] uppercase">Gap Count</div>
                      <div className="font-mono font-bold text-rose-500">{snapshot.coverage_summary.high_priority_gap_count}</div>
                    </div>
                  </div>
                </div>
              ) : null}

              {/* Exam Date Schedule (if date provided) */}
              {snapshot.exam_schedule && snapshot.exam_schedule.phases && (
                <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-accent" />
                      <h3 className="text-sm font-bold">Exam Date-Aware Revision Schedule</h3>
                    </div>
                    <span className="text-xs font-mono text-accent">
                      {snapshot.exam_schedule.days_remaining} Days Remaining
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
                    {snapshot.exam_schedule.phases.map((ph: any) => (
                      <div key={ph.phase} className="bg-background/70 border border-border/60 rounded-lg p-3 text-xs space-y-1">
                        <div className="flex items-center justify-between text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">
                          <span>Phase {ph.phase}</span>
                          <span className="font-mono">{ph.duration_days} Days</span>
                        </div>
                        <div className="font-bold text-foreground">{ph.name}</div>
                        <p className="text-[11px] text-muted-foreground">{ph.description}</p>
                        {ph.focus_topics && ph.focus_topics.length > 0 && (
                          <div className="pt-1 text-[10px] text-accent truncate">
                            Focus: {ph.focus_topics.map((t: any) => typeof t === "string" ? t : (t.topic_name || t.topic_id || "")).join(", ")}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Predictions List */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold tracking-tight">
                    {isFamilyMode ? "Predicted High-Yield Question Families" : "Study These First"}
                  </h3>
                  {snapshot.metadata && (
                    <span className="text-[10px] font-mono text-muted-foreground">
                      Engine: {snapshot.metadata.engine_version} | Model: {snapshot.metadata.model_version}
                    </span>
                  )}
                </div>

                {snapshot.predictions && snapshot.predictions.length > 0 ? (
                  snapshot.predictions.map((p: PredictionItem, idx: number) => {
                    const isFamily = p.category === "family";
                    const priorityInfo = getTopicPriorityInfo(p.name);
                    const isExpanded = expandedTopic === p.name;
                    const studentStatus = priorityInfo?.student_status || "NOT_STARTED";
                    const priorityBand = priorityInfo?.priority || "MEDIUM";
                    const distinctPapers = p.distinct_paper_count ?? p.papers_with_topic ?? 0;
                    const totalPapers = p.papers_analyzed ?? snapshot.exam_history?.total_papers ?? 0;
                    const marksStr = p.average_marks ? `~${p.average_marks} marks` : (p.total_marks_observed ? `~${Math.round(p.total_marks_observed)} marks` : p.marks_seen ? `~${Math.round(p.marks_seen)} marks` : "");

                    let explanation = "";
                    if (distinctPapers >= 4) {
                      explanation = "A highly recurring pattern across multiple past exams.";
                    } else if (distinctPapers > 1) {
                      explanation = "This has appeared in several past exam papers.";
                    } else if (distinctPapers === 1) {
                      explanation = "This appeared exactly once in the papers we analysed.";
                    } else {
                      explanation = "Predicted as highly probable based on syllabus weighting.";
                    }

                    const percent = totalPapers > 0 ? Math.min(100, Math.round((distinctPapers / totalPapers) * 100)) : 0;
                    const totalBlocks = 12;
                    const filledBlocks = Math.round((percent / 100) * totalBlocks);
                    const visualBar = "?".repeat(filledBlocks) + "?".repeat(totalBlocks - filledBlocks);

                    let priorityLabel = "";
                    if (priorityInfo?.priority_tier === "P0" || p.confidence === "HIGH") priorityLabel = "Study First";
                    else if (priorityInfo?.priority_tier === "P1" || p.confidence === "MEDIUM") priorityLabel = "Study Next";
                    else if (priorityInfo?.priority_tier === "P2" || p.confidence === "LOW") priorityLabel = "Study Later";

                    return (
                      <div
                        key={p.family_id ? `fam-${p.family_id}` : idx}
                        className="bg-card rounded-2xl p-6 border border-border shadow-sm hover:shadow-md transition-all relative group overflow-hidden mb-4 cursor-pointer"
                          onClick={() => trackOnce("prediction_opened", String(p.name), { course_id: selectedSubject?.curriculum_id, item_name: p.name })}
                      >
                        {p.confidence === "HIGH" && (
                          <div className="absolute left-0 top-0 bottom-0 w-1 bg-emerald-500" />
                        )}
                        <div className="flex flex-col md:flex-row gap-6">
                          <div className="flex-1 space-y-4">
                            <div className="space-y-1.5">
                              <div className="flex items-center gap-3 mb-1">
                                <span className="font-mono text-xs font-bold text-muted-foreground">#{p.rank}</span>
                                {priorityLabel && (
                                  <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${priorityLabel === 'Study First' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-secondary text-muted-foreground'}`}>
                                    {priorityLabel}
                                  </span>
                                )}
                              </div>
                              <h4 className="text-xl font-bold text-foreground leading-tight pr-4">
                                <MathText content={p.name} />
                              </h4>
                              <div className="flex items-center gap-3 text-sm font-medium text-muted-foreground mt-2">
                                {distinctPapers > 0 && (
                                  <span className={distinctPapers >= 3 ? "text-accent" : ""}>
                                    Seen in {distinctPapers} {totalPapers > 0 ? `of ${totalPapers}` : ''} past {distinctPapers === 1 ? "paper" : "papers"}
                                  </span>
                                )}
                                {distinctPapers > 0 && marksStr && <span className="w-1 h-1 rounded-full bg-border" />}
                                {marksStr && <span>{marksStr}</span>}
                              </div>
                            </div>
                            
                            <div className="flex items-center gap-4 text-sm text-muted-foreground">
                              {distinctPapers > 0 && (
                                <div className="font-mono text-xs tracking-widest flex" title={`${percent}% paper coverage`}>
                                  <span className="text-accent/60">{visualBar.substring(0, filledBlocks)}</span>
                                  <span className="text-border">{visualBar.substring(filledBlocks)}</span>
                                </div>
                              )}
                              <p className="text-sm text-foreground/80 max-w-xl">
                                {explanation}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-end md:items-center gap-3 shrink-0 mt-2 md:mt-0">
                            <button
                              onClick={() => isFamily ? handleOpenFamilyEvidence(p.family_id, p.name) : handleOpenTopicIntelligence(p.topic_id, p.name)}
                              className="px-4 py-2.5 rounded-xl font-bold bg-secondary text-foreground hover:bg-secondary/80 transition-colors flex items-center gap-2 text-sm"
                            >
                              <span>Why?</span>
                            </button>
                            
                            <button
                              onClick={() => handleViewQuestions(isFamily ? undefined : p.name, isFamily ? p.family_id : undefined, p.name)}
                              className="px-4 py-2.5 rounded-xl font-bold bg-accent text-accent-foreground hover:opacity-90 transition-opacity flex items-center gap-2 text-sm shadow-sm"
                            >
                              <span>Practice {selectedExam ? `(${selectedExam})` : ''}</span>
                              <ArrowRight className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    )
                  })
                ) : (
                  <div className="border border-dashed border-border/80 bg-card/60 rounded-xl p-6 text-center space-y-3">
                    <div className="inline-flex p-2.5 rounded-full bg-accent/10 text-accent mb-1">
                      <Repeat className="w-5 h-5" />
                    </div>
                    <h4 className="text-sm font-semibold text-foreground">
                      {snapshot?.has_topic_taxonomy
                        ? "Topic Predictions Currently Unavailable"
                        : "Topic Predictions Pending Syllabus Taxonomy"}
                    </h4>
                    <p className="text-xs text-muted-foreground max-w-md mx-auto leading-relaxed">
                      {snapshot?.has_topic_taxonomy
                        ? `${snapshot.taxonomy_topic_count ?? "Cataloged"} syllabus topics exist for this course, but question-to-topic prediction mappings are not currently available. Question Family recurrence analytics and empirical paper patterns are fully active and verified.`
                        : "Detailed syllabus topic taxonomy is currently being cataloged for this course. Question Family recurrence analytics and empirical paper patterns are fully active and verified."}
                    </p>
                    <div className="pt-2">
                      <button
                        onClick={() => setMainView("analytics")}
                        className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-accent text-accent-foreground text-xs font-semibold hover:bg-accent/90 transition-colors cursor-pointer"
                      >
                        <Repeat className="w-3.5 h-3.5" />
                        <span>Explore What Repeated</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })() : snapshot && snapshot.data_availability_status === "INSUFFICIENT_EVIDENCE" ? (
            <div className="h-full min-h-[400px] border border-dashed border-amber-500/30 bg-amber-500/5 rounded-xl flex flex-col items-center justify-center text-center p-8">
              <AlertCircle className="w-10 h-10 text-amber-500 mb-4" />
              <h3 className="text-lg font-bold text-foreground mb-2">Insufficient Examination Volume</h3>
              <p className="text-sm text-muted-foreground max-w-sm mb-2">
                Only {selectedSubject?.exam_count || 1} examination paper(s) indexed for <strong>{selectedSubject?.subject_name}</strong>.
              </p>
              <p className="text-xs text-muted-foreground/80 max-w-sm mb-4">
                MarkMint requires at least 2 historical examination cycles to compute reliable probabilistic forecasts.
              </p>
              <button
                onClick={() => handleViewQuestions()}
                className="px-4 py-2 bg-background border border-border rounded-lg text-xs font-semibold hover:border-accent flex items-center gap-2"
              >
                <BookOpen className="w-4 h-4 text-accent" />
                <span>Browse {selectedSubject?.question_count || 0} Historical Questions {selectedExam ? `for ${selectedExam}` : ''}</span>
              </button>
            </div>
          ) : selectedSubject?.status === "AMBIGUOUS" ? (
            <div className="h-full min-h-[400px] border border-amber-500/20 bg-amber-500/5 rounded-xl flex flex-col items-center justify-center text-center p-8">
              <AlertCircle className="w-10 h-10 text-amber-500 mb-4" />
              <h3 className="text-lg font-bold text-foreground mb-2">Ambiguous Course Mapping</h3>
              <p className="text-sm text-muted-foreground max-w-md mb-3">
                <strong>{selectedSubject.subject_name}</strong> maps to multiple candidate academic subjects in the syllabus catalog.
              </p>
              {selectedSubject.notes && (
                <p className="text-xs text-amber-500/90 max-w-md italic bg-amber-500/10 rounded-md p-3 mb-3 border border-amber-500/20">
                  {selectedSubject.notes}
                </p>
              )}
              <p className="text-xs text-muted-foreground max-w-sm">
                No deterministic forecast can be synthesized without an explicit canonical course mapping.
              </p>
            </div>
          ) : selectedSubject?.status === "UNMATCHED" ? (
            <div className="h-full min-h-[400px] border border-dashed border-border rounded-xl flex flex-col items-center justify-center text-center p-8 bg-card/30">
              <Database className="w-10 h-10 text-muted-foreground mb-4 opacity-30" />
              <h3 className="text-lg font-bold text-foreground mb-2">Awaiting Historical Evidence</h3>
              <p className="text-sm text-muted-foreground max-w-sm mb-2">
                No historical examination papers have been indexed for <strong>{selectedSubject.subject_name}</strong> yet.
              </p>
              <p className="text-xs text-muted-foreground/70 max-w-sm">
                MarkMint&apos;s deterministic engine only computes probabilities when verified university exam papers exist.
              </p>
            </div>
          ) : selectedSubject?.status === "MATCHED" && !selectedSubject.has_exams ? (
            <div className="h-full min-h-[400px] border border-dashed border-border rounded-xl flex flex-col items-center justify-center text-center p-8 bg-card/30">
              <FileText className="w-10 h-10 text-muted-foreground mb-4 opacity-30" />
              <h3 className="text-lg font-bold text-foreground mb-2">No Past Papers Found</h3>
              <p className="text-sm text-muted-foreground max-w-sm mb-2">
                <strong>{selectedSubject.subject_name}</strong> is verified in the academic registry, but 0 historical examination papers are currently uploaded.
              </p>
              <p className="text-xs text-muted-foreground/70 max-w-sm">
                Historical intelligence will unlock automatically when past papers are ingested for this course.
              </p>
            </div>
          ) : isSubjectAvailable ? (
            <div className="h-full min-h-[400px] border border-dashed border-border rounded-xl flex flex-col items-center justify-center text-center p-8 bg-card/30">
              <Database className="w-10 h-10 text-accent mb-4 opacity-70" />
              <h3 className="text-lg font-bold text-foreground mb-2">Evidence Pool Ready</h3>
              <p className="text-sm text-muted-foreground max-w-sm mb-3">
                Verified historical papers ({selectedSubject?.exam_count} exams, {selectedSubject?.question_count} questions) loaded for <strong>{selectedSubject?.subject_name}</strong>.
              </p>
              <p className="text-xs text-muted-foreground/80">
                Click <strong>Generate Forecast</strong> on the left to extract explainable predictions and study priorities.
              </p>
            </div>
          ) : (
            <div className="h-full min-h-[400px] rounded-xl flex flex-col justify-center p-8 lg:p-12 bg-card border border-border shadow-sm">
              <div className="max-w-xl">
                <h3 className="text-2xl font-bold text-foreground mb-4">MintAI Prediction Engine</h3>
                <p className="text-base text-muted-foreground mb-10 leading-relaxed">
                  Select a course from the curriculum catalog to unlock highly probable examination topics based on deterministic historical patterns.
                </p>
                
                <div className="flex flex-col gap-6">
                  <div className="flex items-start gap-4">
                    <div className="flex items-center justify-center w-8 h-8 rounded-full bg-accent/10 text-accent font-bold text-sm shrink-0 border border-accent/20">1</div>
                    <div>
                      <h4 className="text-sm font-bold text-foreground">Select Scope</h4>
                      <p className="text-sm text-muted-foreground mt-0.5">Choose your academic branch, semester, and target course.</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-4 opacity-70">
                    <div className="flex items-center justify-center w-8 h-8 rounded-full bg-secondary text-muted-foreground font-bold text-sm shrink-0 border border-border">2</div>
                    <div>
                      <h4 className="text-sm font-bold text-foreground">Analyze Evidence</h4>
                      <p className="text-sm text-muted-foreground mt-0.5">Explore recurring exam patterns and historical frequency.</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-4 opacity-70">
                    <div className="flex items-center justify-center w-8 h-8 rounded-full bg-secondary text-muted-foreground font-bold text-sm shrink-0 border border-border">3</div>
                    <div>
                      <h4 className="text-sm font-bold text-foreground">Study & Practice</h4>
                      <p className="text-sm text-muted-foreground mt-0.5">Focus on high-yield topics directly matched to syllabus objectives.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
          </>
        )}
      </div>
    </main>

      {/* Historical Questions Modal */}
      <Drawer
        isOpen={isQuestionsModalOpen}
        onClose={() => setIsQuestionsModalOpen(false)}
        title="Verified Historical Questions"
        subtitle={
          selectedTopicForQuestions
            ? `Showing past examination questions mapped to: ${selectedTopicForQuestions}`
            : `Course wide question archive for: ${selectedSubject?.subject_name}`
        }
      >
        <div className="flex flex-col h-full">

            <div className="p-4 border-b border-border/60 bg-card/50 flex flex-wrap items-center justify-between gap-3 text-xs">
              <div className="flex flex-wrap items-center gap-2">
                {/* Year Filter */}
                {availableQuestionYears.length > 0 && (
                  <select
                    aria-label="Filter by Year"
                    value={questionFilterYear}
                    onChange={(e) => setQuestionFilterYear(e.target.value)}
                    className="bg-background border border-border rounded-md px-2.5 py-1 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-accent"
                  >
                    <option value="">All Years</option>
                    {availableQuestionYears.map((y) => (
                      <option key={y} value={String(y)}>
                        {y}
                      </option>
                    ))}
                  </select>
                )}

                {/* Min Marks Filter */}
                <select
                  aria-label="Filter by Minimum Marks"
                  value={questionFilterMinMarks}
                  onChange={(e) => setQuestionFilterMinMarks(e.target.value)}
                  className="bg-background border border-border rounded-md px-2.5 py-1 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-accent"
                >
                  <option value="">All Marks</option>
                  <option value="2">≥ 2 Marks</option>
                  <option value="5">≥ 5 Marks</option>
                  <option value="10">≥ 10 Marks</option>
                  <option value="15">≥ 15 Marks</option>
                </select>

                {/* Repetition Filter */}
                {availableRepetitionTypes.length > 0 && (
                  <select
                    aria-label="Filter by Repetition Type"
                    value={questionFilterRepetition}
                    onChange={(e) => setQuestionFilterRepetition(e.target.value)}
                    className="bg-background border border-border rounded-md px-2.5 py-1 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-accent"
                  >
                    <option value="">All Repetition Types</option>
                    {availableRepetitionTypes.map((rt) => (
                      <option key={rt} value={rt}>
                        {rt.replace(/_/g, " ")}
                      </option>
                    ))}
                  </select>
                )}

                {(questionFilterYear || questionFilterMinMarks || questionFilterRepetition) && (
                  <button
                    onClick={() => {
                      setQuestionFilterYear("");
                      setQuestionFilterMinMarks("");
                      setQuestionFilterRepetition("");
                    }}
                    className="text-muted-foreground hover:text-foreground text-[11px] underline ml-1"
                  >
                    Clear Filters
                  </button>
                )}
              </div>

              <span className="text-[11px] font-mono text-muted-foreground">
                Showing {filteredQuestions.length} of {historicalQuestions.length} questions
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              {isLoadingQuestions ? (
                <div className="flex flex-col items-center justify-center py-12 gap-2 text-muted-foreground">
                  <Activity className="w-6 h-6 animate-spin text-accent" />
                  <span className="text-xs">Querying historical question repository...</span>
                </div>
              ) : filteredQuestions.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground text-xs">
                  No historical questions match the current filters.
                </div>
              ) : (
                filteredQuestions.map((q) => (
                  <div
                    key={q.id}
                    className="p-4 bg-background/80 border border-border/60 rounded-lg text-xs space-y-2.5"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2 text-[11px]">
                      <div className="flex flex-wrap items-center gap-1.5">
                        <span className="font-mono font-bold text-accent">Q{q.question_number}</span>
                        {q.year && <span className="text-muted-foreground font-mono">[{q.year}]</span>}
                        {q.assessment_type && (
                          <span className="px-1.5 py-0.5 bg-muted rounded font-mono text-[10px]">
                            {q.assessment_type}
                          </span>
                        )}
                        {q.repetition_type && (
                          <span className="px-1.5 py-0.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded font-mono text-[10px] uppercase">
                            {q.repetition_type.replace(/_/g, " ")}
                          </span>
                        )}
                        {q.family_name && (
                          <span className="px-1.5 py-0.5 bg-accent/10 text-accent rounded font-mono text-[10px]">
                            {q.family_name}
                          </span>
                        )}
                      </div>
                      <div className="font-mono font-bold text-foreground">
                        {q.marks ? `${q.marks} Marks` : "Marks Unspecified"}
                      </div>
                    </div>

                    <div className="text-foreground leading-relaxed font-sans text-xs">
                      <MathText content={q.original_text} />
                    </div>

                    {(q.family_recurrence_history || q.source_document_title) && (
                      <div className="pt-2 border-t border-border/40 flex flex-wrap items-center justify-between gap-2 text-[10px] text-muted-foreground">
                        {q.family_recurrence_history && (
                          <span className="font-mono">
                            Recurrence: <strong className="text-accent">{q.family_recurrence_history}</strong>
                          </span>
                        )}
                        {q.source_document_title && (
                          <span className="truncate max-w-[280px]">
                            Paper: {q.source_document_title}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
        </div>
      </Drawer>

      {/* Study Resources Modal */}
      <Drawer
        isOpen={isResourcesModalOpen}
        onClose={() => setIsResourcesModalOpen(false)}
        title="Linked Study Resources"
        subtitle={`Topic: ${selectedTopicForResources}`}
      >
        <div className="flex-1 overflow-y-auto p-5 space-y-3">
              {topicResources.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground text-xs">
                  No lecture notes or study documents linked to this topic yet.
                </div>
              ) : (
                topicResources.map((res: any, idx: number) => (
                  <div key={idx} className="p-4 bg-background border border-border rounded-lg text-xs space-y-2">
                    <div className="flex items-center justify-between font-medium">
                      <span className="text-foreground font-bold">{res.title}</span>
                      <span className="text-[10px] font-mono uppercase text-muted-foreground">
                        {res.resource_type || "Document"}
                      </span>
                    </div>
                    {res.content && (
                      <p className="text-muted-foreground text-[11px] leading-relaxed italic bg-card/60 p-2 rounded border border-border/30">
                        &ldquo;{res.content}&rdquo;
                      </p>
                    )}
                    <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1 border-t border-border/30">
                      <span>Source: {res.source || "Local Ingestion"}</span>
                      {res.page_number && <span>Page {res.page_number}</span>}
                    </div>
                  </div>
                ))
              )}
            </div>
          </Drawer>

      {/* Topic Intelligence Drilldown Modal */}
      {selectedSubject?.course_id && (
        <TopicIntelligenceModal
          isOpen={isTopicModalOpen}
          onClose={() => setIsTopicModalOpen(false)}
          courseId={selectedSubject.course_id}
          topicId={selectedTopicIdForModal}
          initialTopicName={selectedTopicNameForModal}
        />
      )}

      {/* Question Family Evidence Modal */}
      {selectedSubject?.course_id && (
        <FamilyEvidenceModal
          isOpen={isFamilyModalOpen}
          onClose={() => setIsFamilyModalOpen(false)}
          courseId={selectedSubject.course_id}
          familyId={selectedFamilyIdForModal}
          initialFamilyName={selectedFamilyNameForModal}
          onViewQuestions={(famId, famName) => handleViewQuestions(undefined, famId, famName)}
        />
      )}

      <Footer />
    </div>
  );
}
