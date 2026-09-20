"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import {
  getCurriculumBranches,
  getCurriculumSemesters,
  getCurriculumSubjects,
  validateSubmissionPreview,
  createPaperSubmission,
  listPaperSubmissions,
  approvePaperSubmission,
  rejectPaperSubmission,
  getSubmissionReviewSummary,
  getSubmissionByTracking,
} from "@/lib/api";
import {
  CurriculumSubject,
  SubmissionPreview,
  PaperSubmissionRecord,
  AdminReviewSummary,
  SubmitterFeedback,
} from "@/lib/types";
import {
  ChevronRight,
  Upload,
  FileText,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ShieldCheck,
  Eye,
  RefreshCw,
  Clock,
  ArrowRight,
  Sparkles,
  Search,
  Filter,
  Info,
  ChevronDown,
  ChevronUp,
  Layers,
  Database,
  Hash,
} from "lucide-react";

const ASSESSMENT_OPTIONS = [
  { id: "Cycle Test 1", label: "Cycle Test 1 (CT-1)" },
  { id: "Cycle Test 2", label: "Cycle Test 2 (CT-2)" },
  { id: "Model Exam", label: "Model Examination" },
  { id: "End Semester", label: "End Semester Examination" },
  { id: "Not Sure", label: "Not Sure / Other" },
];

export default function SubmitPaperPage() {
  const [activeTab, setActiveTab] = useState<"submit" | "track" | "moderation">("submit");

  // Step state
  const [branches, setBranches] = useState<string[]>([]);
  const [selectedBranch, setSelectedBranch] = useState<string>("");
  const [semesters, setSemesters] = useState<number[]>([]);
  const [selectedSemester, setSelectedSemester] = useState<number | "">("");
  const [subjects, setSubjects] = useState<CurriculumSubject[]>([]);
  const [selectedSubject, setSelectedSubject] = useState<CurriculumSubject | null>(null);
  const [selectedAssessment, setSelectedAssessment] = useState<string>("");
  const [subjectSearch, setSubjectSearch] = useState<string>("");

  // File state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewLoading, setPreviewLoading] = useState<boolean>(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<SubmissionPreview | null>(null);
  const [showSnippet, setShowSnippet] = useState<boolean>(false);

  // Submitting state
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submittedRecord, setSubmittedRecord] = useState<PaperSubmissionRecord | null>(null);

  // Submitter tracking state
  const [trackingCode, setTrackingCode] = useState<string>("");
  const [trackingLoading, setTrackingLoading] = useState<boolean>(false);
  const [trackingResult, setTrackingResult] = useState<SubmitterFeedback | null>(null);
  const [trackingError, setTrackingError] = useState<string | null>(null);

  // Moderation desk state
  const [moderationList, setModerationList] = useState<PaperSubmissionRecord[]>([]);
  const [moderationLoading, setModerationLoading] = useState<boolean>(false);
  const [moderationFilter, setModerationFilter] = useState<string>("ALL");
  const [actionProcessingId, setActionProcessingId] = useState<number | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [expandedSubId, setExpandedSubId] = useState<number | null>(null);
  const [reviewSummaries, setReviewSummaries] = useState<Record<number, AdminReviewSummary>>({});
  const [reviewLoadingId, setReviewLoadingId] = useState<number | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load branches on mount
  useEffect(() => {
    async function loadBranches() {
      try {
        const b = await getCurriculumBranches();
        setBranches(b);
        if (b.length > 0) {
          // Default to CSE if available
          const cse = b.find((x) => x.toLowerCase().includes("computer science")) || b[0];
          setSelectedBranch(cse);
        }
      } catch (e) {
        console.error("Failed to load branches:", e);
      }
    }
    loadBranches();
  }, []);

  // Load semesters when branch changes
  useEffect(() => {
    if (!selectedBranch) return;
    async function loadSemesters() {
      try {
        const s = await getCurriculumSemesters(selectedBranch);
        setSemesters(s);
        if (s.length > 0) {
          setSelectedSemester(s[0]);
        }
      } catch (e) {
        console.error("Failed to load semesters:", e);
      }
    }
    loadSemesters();
  }, [selectedBranch]);

  // Load subjects when branch or semester changes
  useEffect(() => {
    if (!selectedBranch || selectedSemester === "") return;
    async function loadSubjects() {
      try {
        const subs = await getCurriculumSubjects(selectedBranch, selectedSemester);
        setSubjects(subs);
        setSelectedSubject(null);
        setPreviewData(null);
      } catch (e) {
        console.error("Failed to load subjects:", e);
      }
    }
    loadSubjects();
  }, [selectedBranch, selectedSemester]);

  // Trigger analysis when file changes or subject changes
  const handleFileChange = async (file: File) => {
    setSelectedFile(file);
    setPreviewError(null);
    setPreviewData(null);

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setPreviewError("Please select a valid PDF examination document.");
      return;
    }

    if (file.size > 20 * 1024 * 1024) {
      setPreviewError("File size exceeds the 20MB limit.");
      return;
    }

    setPreviewLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      if (selectedSubject?.course_id) {
        formData.append("course_id", String(selectedSubject.course_id));
      }
      if (selectedAssessment && selectedAssessment !== "Not Sure") {
        formData.append("declared_assessment", selectedAssessment);
      }

      const preview = await validateSubmissionPreview(formData);
      setPreviewData(preview);
    } catch (err: any) {
      setPreviewError(err.message || "Failed to analyze examination document.");
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async () => {
    if (!selectedFile) {
      setSubmitError("Please select a PDF file to submit.");
      return;
    }
    if (!selectedSubject) {
      setSubmitError("Please select a target subject.");
      return;
    }

    setSubmitting(true);
    setSubmitError(null);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("subject_name", selectedSubject.subject_name);
      if (selectedBranch) formData.append("branch_name", selectedBranch);
      if (selectedSemester !== "") formData.append("semester", String(selectedSemester));
      if (selectedSubject.course_id) formData.append("course_id", String(selectedSubject.course_id));
      if (selectedAssessment) formData.append("declared_assessment", selectedAssessment);

      // Generate anonymous session token stored in browser session storage
      let sessionToken = sessionStorage.getItem("mm_uploader_session");
      if (!sessionToken) {
        sessionToken = "session_" + Math.random().toString(36).substring(2, 15);
        sessionStorage.setItem("mm_uploader_session", sessionToken);
      }
      formData.append("uploader_session_id", sessionToken);

      const record = await createPaperSubmission(formData);
      setSubmittedRecord(record);
    } catch (err: any) {
      setSubmitError(err.message || "Failed to submit examination paper.");
    } finally {
      setSubmitting(false);
    }
  };

  // Moderation desk actions
  const loadModerationItems = async () => {
    setModerationLoading(true);
    setActionMessage(null);
    try {
      const filter = moderationFilter === "ALL" ? undefined : moderationFilter;
      const list = await listPaperSubmissions(filter);
      setModerationList(list);
    } catch (e: any) {
      setActionMessage("Failed to fetch moderation queue: " + e.message);
    } finally {
      setModerationLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "moderation") {
      loadModerationItems();
    }
  }, [activeTab, moderationFilter]);

  const handleApprove = async (id: number) => {
    setActionProcessingId(id);
    setActionMessage(null);
    try {
      const res = await approvePaperSubmission(id, { reviewer: "moderation_desk" });
      if (res.result?.review_summary) {
        setReviewSummaries((prev) => ({ ...prev, [id]: res.result.review_summary }));
      }
      setActionMessage(`Approved submission #${id}! Ingested ${res.result?.questions_ingested ?? 0} questions into production.`);
      loadModerationItems();
    } catch (e: any) {
      setActionMessage(`Approval failed: ${e.message}`);
    } finally {
      setActionProcessingId(null);
    }
  };

  const handleReject = async (id: number) => {
    const reason = prompt("Enter rejection reason for audit log (e.g. illegible scan, wrong exam paper):");
    if (!reason) return;

    setActionProcessingId(id);
    setActionMessage(null);
    try {
      await rejectPaperSubmission(id, reason, "moderation_desk");
      setActionMessage(`Rejected submission #${id} with reason: "${reason}"`);
      loadModerationItems();
    } catch (e: any) {
      setActionMessage(`Rejection failed: ${e.message}`);
    } finally {
      setActionProcessingId(null);
    }
  };

  const loadReviewSummary = async (id: number) => {
    if (reviewSummaries[id]) return;
    setReviewLoadingId(id);
    try {
      const summary = await getSubmissionReviewSummary(id);
      setReviewSummaries((prev) => ({ ...prev, [id]: summary }));
    } catch (e) {
      console.error("Failed to load review summary:", e);
    } finally {
      setReviewLoadingId(null);
    }
  };

  const handleTrackSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!trackingCode.trim()) return;
    setTrackingLoading(true);
    setTrackingError(null);
    setTrackingResult(null);
    try {
      const res = await getSubmissionByTracking(trackingCode.trim());
      setTrackingResult(res);
    } catch (e: any) {
      setTrackingError(e.message || "Tracking ID not found. Please check and try again.");
    } finally {
      setTrackingLoading(false);
    }
  };

  const resetForm = () => {
    setSelectedFile(null);
    setPreviewData(null);
    setSubmittedRecord(null);
    setPreviewError(null);
    setSubmitError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const filteredSubjects = subjects.filter((s) =>
    s.subject_name.toLowerCase().includes(subjectSearch.toLowerCase()) ||
    (s.canonical_code || "").toLowerCase().includes(subjectSearch.toLowerCase())
  );

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground selection:bg-accent/20 font-sans">
      <Navbar />

      <main className="flex-1 w-full max-w-6xl mx-auto px-6 md:px-10 py-10 space-y-10">
        {/* Breadcrumbs */}
        <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-xs text-muted-foreground">
          <Link href="/" className="hover:text-foreground transition-colors">Home</Link>
          <ChevronRight className="w-3.5 h-3.5" />
          <span className="text-foreground font-medium">Submit Paper</span>
        </nav>

        {/* Hero Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-border/40">
          <div className="max-w-2xl space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent/10 border border-accent/20 text-xs font-semibold text-accent uppercase tracking-wider">
              <Sparkles className="w-3.5 h-3.5" />
              Verified Exam Paper Submission Pipeline
            </div>
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-foreground">
              Contribute Exam Papers
            </h1>
            <p className="text-sm md:text-base text-muted-foreground leading-relaxed">
              Submit missing recent examination papers (Cycle Tests, Model, End Semester). Uploads undergo automated validation, duplicate checks, and consistency verification before being approved into the MarkMint intelligence corpus.
            </p>
          </div>

          {/* Privacy & Provenance badge */}
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-card/60 border border-border/60 text-xs text-muted-foreground">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Privacy Guaranteed: No student PII collected.</span>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-2 border-b border-border/40">
          <button
            onClick={() => setActiveTab("submit")}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
              activeTab === "submit"
                ? "border-accent text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            Submit a Paper
          </button>
          <button
            onClick={() => setActiveTab("track")}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === "track"
                ? "border-accent text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <span>Track Submission</span>
          </button>
          <button
            onClick={() => setActiveTab("moderation")}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === "moderation"
                ? "border-accent text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <span>Moderation Desk</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground font-mono">
              Admin
            </span>
          </button>
        </div>

        {/* SUBMISSION STEPPER VIEW */}
        {activeTab === "submit" && (
          <div className="space-y-8">
            {submittedRecord ? (
              /* Success State */
              <div className="p-8 rounded-2xl bg-card border border-emerald-500/30 text-center space-y-6 max-w-xl mx-auto">
                <div className="w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
                  <CheckCircle2 className="w-8 h-8" />
                </div>
                <div className="space-y-2">
                  <h2 className="text-2xl font-bold text-foreground">Paper Submitted for Verification</h2>
                  <p className="text-sm text-muted-foreground">
                    Thank you! Your submission has been securely recorded and queued for moderation review.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-background/60 border border-border/60 text-left space-y-2 text-xs font-mono">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Tracking ID:</span>
                    <span className="text-foreground font-bold">#SUB-{submittedRecord.id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Status:</span>
                    <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 font-sans font-semibold">
                      {submittedRecord.status}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Subject:</span>
                    <span className="text-foreground font-sans">{submittedRecord.subject_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Detected Cycle:</span>
                    <span className="text-foreground font-sans">{submittedRecord.detected_assessment || "Pending"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Detected Year:</span>
                    <span className="text-foreground font-sans">{submittedRecord.detected_year || "Pending"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">File Hash:</span>
                    <span className="text-muted-foreground truncate max-w-[240px]">{submittedRecord.file_hash}</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-muted/40 border border-border/40 text-xs text-muted-foreground text-left flex gap-2">
                  <Info className="w-4 h-4 text-accent shrink-0 mt-0.5" />
                  <span>
                    Submissions are kept isolated from the production corpus. Once verified by academic moderation, questions are extracted, classified to syllabus topics, and added to MarkMint intelligence.
                  </span>
                </div>

                <div className="flex items-center justify-center gap-4 pt-2">
                  <button
                    onClick={resetForm}
                    className="px-4 py-2 text-sm font-medium rounded-lg bg-accent text-accent-foreground hover:bg-accent/90 transition-colors"
                  >
                    Submit Another Paper
                  </button>
                  <Link
                    href="/courses"
                    className="px-4 py-2 text-sm font-medium rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors"
                  >
                    Explore Courses
                  </Link>
                </div>
              </div>
            ) : (
              /* Multi-step Form */
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Left Column: Flow steps 1 to 5 */}
                <div className="lg:col-span-7 space-y-6">
                  {/* Step 1 & 2: Branch & Semester */}
                  <div className="p-6 rounded-xl bg-card border border-border/60 space-y-4">
                    <h2 className="text-base font-semibold text-foreground flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-accent/20 text-accent text-xs flex items-center justify-center font-mono font-bold">1</span>
                      Academic Branch & Semester
                    </h2>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs text-muted-foreground block mb-1">Branch</label>
                        <select
                          value={selectedBranch}
                          onChange={(e) => setSelectedBranch(e.target.value)}
                          className="w-full px-3 py-2 rounded-lg bg-background border border-border/80 text-sm focus:outline-none focus:ring-1 focus:ring-accent"
                        >
                          {branches.map((b) => (
                            <option key={b} value={b}>{b}</option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="text-xs text-muted-foreground block mb-1">Semester</label>
                        <select
                          value={selectedSemester}
                          onChange={(e) => setSelectedSemester(Number(e.target.value))}
                          className="w-full px-3 py-2 rounded-lg bg-background border border-border/80 text-sm focus:outline-none focus:ring-1 focus:ring-accent"
                        >
                          {semesters.map((s) => (
                            <option key={s} value={s}>Semester {s}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </div>

                  {/* Step 3: Subject Selection */}
                  <div className="p-6 rounded-xl bg-card border border-border/60 space-y-4">
                    <h2 className="text-base font-semibold text-foreground flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-accent/20 text-accent text-xs flex items-center justify-center font-mono font-bold">2</span>
                      Select Course / Subject
                    </h2>

                    <div className="relative">
                      <Search className="w-4 h-4 text-muted-foreground absolute left-3 top-2.5" />
                      <input
                        type="text"
                        placeholder="Search by course code or subject title..."
                        value={subjectSearch}
                        onChange={(e) => setSubjectSearch(e.target.value)}
                        className="w-full pl-9 pr-3 py-2 rounded-lg bg-background border border-border/80 text-sm focus:outline-none focus:ring-1 focus:ring-accent"
                      />
                    </div>

                    <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1">
                      {filteredSubjects.length === 0 ? (
                        <p className="text-xs text-muted-foreground py-4 text-center">No subjects found matching query.</p>
                      ) : (
                        filteredSubjects.map((sub) => {
                          const isSelected = selectedSubject?.curriculum_id === sub.curriculum_id;
                          return (
                            <button
                              key={sub.curriculum_id}
                              type="button"
                              onClick={() => setSelectedSubject(sub)}
                              className={`w-full text-left p-3 rounded-lg border text-xs flex items-center justify-between transition-all ${
                                isSelected
                                  ? "bg-accent/10 border-accent text-accent-foreground font-semibold"
                                  : "bg-background/40 border-border/40 text-foreground hover:bg-muted/40"
                              }`}
                            >
                              <div className="space-y-0.5">
                                <div className="font-medium text-foreground">{sub.subject_name}</div>
                                <div className="text-[11px] text-muted-foreground font-mono">{sub.canonical_code || "SRMIST Curriculum"}</div>
                              </div>
                              {isSelected && <CheckCircle2 className="w-4 h-4 text-accent shrink-0" />}
                            </button>
                          );
                        })
                      )}
                    </div>
                  </div>

                  {/* Step 4: Assessment Type */}
                  <div className="p-6 rounded-xl bg-card border border-border/60 space-y-4">
                    <h2 className="text-base font-semibold text-foreground flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-accent/20 text-accent text-xs flex items-center justify-center font-mono font-bold">3</span>
                      Assessment Cycle (Optional / If Known)
                    </h2>

                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                      {ASSESSMENT_OPTIONS.map((opt) => (
                        <button
                          key={opt.id}
                          type="button"
                          onClick={() => setSelectedAssessment(opt.id)}
                          className={`p-2.5 rounded-lg border text-xs text-center transition-all ${
                            selectedAssessment === opt.id
                              ? "bg-accent/10 border-accent text-accent font-semibold"
                              : "bg-background/40 border-border/40 text-muted-foreground hover:text-foreground hover:bg-muted/40"
                          }`}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Step 5: File Upload Dropzone */}
                  <div className="p-6 rounded-xl bg-card border border-border/60 space-y-4">
                    <h2 className="text-base font-semibold text-foreground flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-accent/20 text-accent text-xs flex items-center justify-center font-mono font-bold">4</span>
                      Upload PDF Question Paper
                    </h2>

                    <div
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={handleDrop}
                      onClick={() => fileInputRef.current?.click()}
                      className="border-2 border-dashed border-border/80 hover:border-accent/60 rounded-xl p-8 text-center cursor-pointer transition-colors bg-background/40 flex flex-col items-center justify-center gap-3"
                    >
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="application/pdf"
                        className="hidden"
                        onChange={(e) => {
                          if (e.target.files && e.target.files[0]) {
                            handleFileChange(e.target.files[0]);
                          }
                        }}
                      />
                      <div className="w-12 h-12 rounded-full bg-accent/10 text-accent flex items-center justify-center">
                        <Upload className="w-6 h-6" />
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm font-medium text-foreground">
                          {selectedFile ? selectedFile.name : "Click to select or drag and drop paper PDF"}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Standard PDF format up to 20MB. Clear digital or high-resolution scans preferred.
                        </p>
                      </div>
                    </div>

                    {previewLoading && (
                      <div className="flex items-center gap-2 text-xs text-accent py-2 justify-center">
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>Validating PDF format and extracting preview heuristics...</span>
                      </div>
                    )}

                    {previewError && (
                      <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
                        <XCircle className="w-4 h-4 shrink-0" />
                        <span>{previewError}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Right Column: Steps 6, 7, 8: Document Analysis, Extraction Preview & Submit */}
                <div className="lg:col-span-5 space-y-6">
                  <div className="p-6 rounded-xl bg-card border border-border/60 space-y-5 sticky top-6">
                    <h2 className="text-base font-semibold text-foreground flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-accent/20 text-accent text-xs flex items-center justify-center font-mono font-bold">5</span>
                      Document Extraction & Consistency Preview
                    </h2>

                    {!previewData && !previewLoading && (
                      <div className="py-12 text-center text-xs text-muted-foreground space-y-2">
                        <FileText className="w-10 h-10 mx-auto text-muted-foreground/40" />
                        <p>Select a subject and upload a PDF to see automated extraction preview.</p>
                      </div>
                    )}

                    {previewData && (
                      <div className="space-y-4">
                        {/* Duplicate Alert Banner */}
                        {previewData.is_duplicate && (
                          <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs space-y-1">
                            <div className="flex items-center gap-2 font-semibold">
                              <AlertTriangle className="w-4 h-4 shrink-0" />
                              <span>Duplicate Document Detected</span>
                            </div>
                            <p className="text-[11px] leading-relaxed text-amber-200/80">
                              {previewData.duplicate_message}
                            </p>
                          </div>
                        )}

                        {/* Consistency Status Banner */}
                        <div
                          className={`p-3.5 rounded-lg border text-xs space-y-1.5 ${
                            previewData.consistency_status === "CONSISTENT"
                              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                              : previewData.consistency_status === "MISMATCH"
                              ? "bg-red-500/10 border-red-500/30 text-red-300"
                              : "bg-amber-500/10 border-amber-500/30 text-amber-300"
                          }`}
                        >
                          <div className="flex items-center justify-between font-semibold">
                            <span className="flex items-center gap-1.5">
                              {previewData.consistency_status === "CONSISTENT" && <CheckCircle2 className="w-4 h-4" />}
                              {previewData.consistency_status === "MISMATCH" && <XCircle className="w-4 h-4" />}
                              {previewData.consistency_status === "UNCERTAIN" && <AlertTriangle className="w-4 h-4" />}
                              <span>Consistency: {previewData.consistency_status}</span>
                            </span>
                            <span className="font-mono text-[11px]">
                              {Math.round(previewData.consistency_score * 100)}% match
                            </span>
                          </div>
                          {previewData.consistency_notes && (
                            <p className="text-[11px] leading-relaxed opacity-90">
                              {previewData.consistency_notes}
                            </p>
                          )}
                        </div>

                        {/* File Metadata Details */}
                        <div className="p-3 rounded-lg bg-background/60 border border-border/60 text-xs space-y-2">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Filename:</span>
                            <span className="font-medium text-foreground truncate max-w-[200px]">{previewData.filename}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Size / Pages:</span>
                            <span className="text-foreground">
                              {(previewData.file_size / (1024 * 1024)).toFixed(2)} MB &bull; {previewData.page_count} pages
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Detected Code:</span>
                            <span className="font-mono font-semibold text-accent">
                              {previewData.detected_course_code || "Not detected"}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Detected Cycle:</span>
                            <span className="text-foreground">{previewData.detected_assessment || "Not detected"}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Detected Year:</span>
                            <span className="text-foreground">{previewData.detected_year || "Not detected"}</span>
                          </div>
                        </div>

                        {/* Collapsible Text Snippet */}
                        <div className="border border-border/40 rounded-lg overflow-hidden">
                          <button
                            type="button"
                            onClick={() => setShowSnippet(!showSnippet)}
                            className="w-full p-2.5 text-xs bg-muted/20 hover:bg-muted/40 text-muted-foreground flex items-center justify-between transition-colors"
                          >
                            <span className="flex items-center gap-1.5">
                              <Eye className="w-3.5 h-3.5" />
                              <span>Extracted Text Preview</span>
                            </span>
                            {showSnippet ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                          </button>
                          {showSnippet && (
                            <pre className="p-3 text-[11px] font-mono text-muted-foreground bg-background/80 overflow-x-auto max-h-48 whitespace-pre-wrap leading-relaxed">
                              {previewData.extracted_snippet || "No text extracted."}
                            </pre>
                          )}
                        </div>

                        {/* Submit Button */}
                        {submitError && (
                          <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
                            {submitError}
                          </div>
                        )}

                        <div className="pt-2 space-y-2">
                          <button
                            type="button"
                            onClick={handleSubmit}
                            disabled={submitting || !selectedFile || !selectedSubject}
                            className="w-full py-3 px-4 rounded-xl bg-accent text-accent-foreground font-semibold text-sm hover:bg-accent/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md shadow-accent/10 flex items-center justify-center gap-2"
                          >
                            {submitting ? (
                              <>
                                <RefreshCw className="w-4 h-4 animate-spin" />
                                <span>Submitting to Moderation...</span>
                              </>
                            ) : (
                              <>
                                <span>Submit Paper for Review</span>
                                <ArrowRight className="w-4 h-4" />
                              </>
                            )}
                          </button>
                          <p className="text-[11px] text-muted-foreground text-center">
                            By submitting, you certify this is an authentic examination question paper.
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* SUBMITTER TRACKING VIEW */}
        {activeTab === "track" && (
          <div className="space-y-6 max-w-xl mx-auto py-6">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold text-foreground">Track Your Paper Submission</h2>
              <p className="text-xs text-muted-foreground">
                Enter the tracking code provided when you submitted your examination paper (e.g. #SUB-12).
              </p>
            </div>

            <form onSubmit={handleTrackSearch} className="flex gap-2">
              <div className="relative flex-1">
                <Hash className="w-4 h-4 text-muted-foreground absolute left-3 top-3.5" />
                <input
                  type="text"
                  placeholder="e.g. #SUB-12 or 12"
                  value={trackingCode}
                  onChange={(e) => setTrackingCode(e.target.value)}
                  className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-card border border-border text-sm focus:outline-none focus:ring-1 focus:ring-accent"
                />
              </div>
              <button
                type="submit"
                disabled={trackingLoading || !trackingCode.trim()}
                className="px-5 py-2.5 rounded-xl bg-accent text-accent-foreground font-semibold text-sm hover:bg-accent/90 disabled:opacity-50 transition-colors flex items-center gap-2 cursor-pointer"
              >
                {trackingLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                <span>Check Status</span>
              </button>
            </form>

            {trackingError && (
              <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{trackingError}</span>
              </div>
            )}

            {trackingResult && (
              <div className="p-6 rounded-2xl bg-card border border-border/80 space-y-5 shadow-sm">
                <div className="flex items-center justify-between flex-wrap gap-2 pb-3 border-b border-border/40">
                  <div className="space-y-0.5">
                    <span className="font-mono text-xs text-muted-foreground">Reference</span>
                    <h3 className="font-mono font-bold text-foreground text-base">{trackingResult.tracking_id}</h3>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      trackingResult.status === "APPROVED"
                        ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                        : trackingResult.status === "REJECTED"
                        ? "bg-red-500/15 text-red-400 border border-red-500/30"
                        : "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                    }`}
                  >
                    {trackingResult.status_badge}
                  </span>
                </div>

                {/* Submitter-safe notification message */}
                <div className="p-3.5 rounded-xl bg-background/60 border border-border/40 space-y-1.5 text-xs">
                  <p className="text-foreground leading-relaxed font-medium">
                    {trackingResult.status_message}
                  </p>
                  {trackingResult.actionable_tip && (
                    <p className="text-muted-foreground italic text-[11px]">
                      Tip: {trackingResult.actionable_tip}
                    </p>
                  )}
                </div>

                {/* Submitted Paper Details */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-lg bg-background/40 border border-border/30">
                    <span className="text-[10px] text-muted-foreground block">Subject</span>
                    <span className="font-semibold text-foreground">{trackingResult.subject_name}</span>
                  </div>
                  <div className="p-3 rounded-lg bg-background/40 border border-border/30">
                    <span className="text-[10px] text-muted-foreground block">Uploaded File</span>
                    <span className="truncate block font-mono text-foreground">{trackingResult.original_filename}</span>
                  </div>
                </div>

                {/* Corpus Contribution Badge */}
                {trackingResult.is_contributed_to_corpus && (
                  <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2 font-medium">
                    <CheckCircle2 className="w-4 h-4 shrink-0" />
                    <span>Your contributed paper is active in the production corpus and contributes to MarkMint predictions!</span>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* MODERATION DESK VIEW */}
        {activeTab === "moderation" && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
              <div className="space-y-1">
                <h2 className="text-xl font-bold text-foreground">Moderation Queue</h2>
                <p className="text-xs text-muted-foreground">
                  Review submitted examination papers. Approve to promote into production corpus, or reject with audit reason.
                </p>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5 text-xs">
                  <Filter className="w-3.5 h-3.5 text-muted-foreground" />
                  <select
                    value={moderationFilter}
                    onChange={(e) => setModerationFilter(e.target.value)}
                    className="px-2.5 py-1.5 rounded-lg bg-background border border-border/80 text-xs focus:outline-none focus:ring-1 focus:ring-accent"
                  >
                    <option value="ALL">All Submissions</option>
                    <option value="PENDING">Pending Review</option>
                    <option value="REVIEW">Under Review</option>
                    <option value="APPROVED">Approved</option>
                    <option value="REJECTED">Rejected</option>
                  </select>
                </div>

                <button
                  onClick={loadModerationItems}
                  className="p-2 rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 text-xs transition-colors"
                  title="Refresh queue"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${moderationLoading ? "animate-spin" : ""}`} />
                </button>
              </div>
            </div>

            {actionMessage && (
              <div className="p-3.5 rounded-xl bg-accent/10 border border-accent/20 text-accent text-xs font-medium">
                {actionMessage}
              </div>
            )}

            {moderationLoading ? (
              <div className="py-16 text-center text-xs text-muted-foreground space-y-2">
                <RefreshCw className="w-6 h-6 animate-spin mx-auto text-accent" />
                <p>Loading moderation queue...</p>
              </div>
            ) : moderationList.length === 0 ? (
              <div className="py-16 text-center text-xs text-muted-foreground p-8 rounded-xl bg-card border border-border/60">
                <p>No submissions found in this status filter.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {moderationList.map((sub) => {
                  const isExpanded = expandedSubId === sub.id;
                  const isProcessing = actionProcessingId === sub.id;

                  return (
                    <div
                      key={sub.id}
                      className="p-5 rounded-xl bg-card border border-border/60 space-y-4 transition-all"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-bold text-foreground text-sm">#SUB-{sub.id}</span>
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                sub.status === "APPROVED"
                                  ? "bg-emerald-500/10 text-emerald-400"
                                  : sub.status === "REJECTED"
                                  ? "bg-red-500/10 text-red-400"
                                  : "bg-amber-500/10 text-amber-400"
                              }`}
                            >
                              {sub.status}
                            </span>
                            {sub.is_duplicate && (
                              <span className="px-2 py-0.5 rounded bg-orange-500/10 text-orange-400 text-[10px] font-semibold">
                                Duplicate
                              </span>
                            )}
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                sub.consistency_status === "CONSISTENT"
                                  ? "bg-emerald-500/10 text-emerald-400"
                                  : sub.consistency_status === "MISMATCH"
                                  ? "bg-red-500/10 text-red-400"
                                  : "bg-amber-500/10 text-amber-400"
                              }`}
                            >
                              {sub.consistency_status}
                            </span>
                          </div>
                          <h3 className="text-sm font-semibold text-foreground">{sub.original_filename}</h3>
                          <p className="text-xs text-muted-foreground">
                            {sub.subject_name} &bull; {sub.branch_name || "Any Branch"} (Sem {sub.semester || "?"})
                          </p>
                        </div>

                        {/* Actions for PENDING submissions */}
                        {sub.status === "PENDING" && (
                          <div className="flex items-center gap-2 self-start">
                            <button
                              type="button"
                              onClick={() => handleApprove(sub.id)}
                              disabled={isProcessing}
                              className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold disabled:opacity-50 transition-colors flex items-center gap-1.5"
                            >
                              {isProcessing ? (
                                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                              ) : (
                                <CheckCircle2 className="w-3.5 h-3.5" />
                              )}
                              <span>Approve & Ingest</span>
                            </button>
                            <button
                              type="button"
                              onClick={() => handleReject(sub.id)}
                              disabled={isProcessing}
                              className="px-3 py-1.5 rounded-lg bg-red-600/80 hover:bg-red-600 text-white text-xs font-semibold disabled:opacity-50 transition-colors flex items-center gap-1.5"
                            >
                              <XCircle className="w-3.5 h-3.5" />
                              <span>Reject</span>
                            </button>
                          </div>
                        )}

                        {/* Status message for APPROVED or REJECTED */}
                        {sub.status === "APPROVED" && sub.ingested_document_id && (
                          <div className="text-xs text-emerald-400 font-mono">
                            Ingested as Document #{sub.ingested_document_id}
                          </div>
                        )}
                        {sub.status === "REJECTED" && sub.rejection_reason && (
                          <div className="text-xs text-red-400 max-w-xs truncate" title={sub.rejection_reason}>
                            Reason: {sub.rejection_reason}
                          </div>
                        )}
                      </div>

                      {/* Extracted Metadata Grid */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3 rounded-lg bg-background/60 border border-border/40 text-xs">
                        <div>
                          <span className="text-muted-foreground block text-[10px]">Detected Code</span>
                          <span className="font-mono text-accent font-semibold">{sub.detected_course_code || "N/A"}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground block text-[10px]">Detected Year</span>
                          <span>{sub.detected_year || "N/A"}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground block text-[10px]">Assessment Cycle</span>
                          <span>{sub.declared_assessment || sub.detected_assessment || "N/A"}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground block text-[10px]">Pages / Size</span>
                          <span>{sub.page_count} pages &bull; {(sub.file_size / (1024 * 1024)).toFixed(2)} MB</span>
                        </div>
                      </div>

                      {/* Toggle Extracted Text and Audit Summary */}
                      <div className="space-y-3 pt-1">
                        <div className="flex items-center gap-3">
                          <button
                            type="button"
                            onClick={() => {
                              if (!isExpanded) {
                                loadReviewSummary(sub.id);
                                setExpandedSubId(sub.id);
                              } else {
                                setExpandedSubId(null);
                              }
                            }}
                            className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 cursor-pointer"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            <span>{isExpanded ? "Collapse Details" : "View Audit & Extracted Text"}</span>
                          </button>
                        </div>

                        {isExpanded && (
                          <div className="space-y-4 pt-2 border-t border-border/40">
                            {/* Admin Review Summary Card */}
                            <div className="p-4 rounded-xl bg-accent/5 border border-accent/20 space-y-3 text-xs">
                              <div className="flex items-center justify-between flex-wrap gap-2">
                                <div className="flex items-center gap-2">
                                  <ShieldCheck className="w-4 h-4 text-accent" />
                                  <span className="font-bold text-foreground">Admin Review Summary</span>
                                </div>
                                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-accent/10 text-accent font-semibold">
                                  Corpus Growth Audit
                                </span>
                              </div>

                              {reviewLoadingId === sub.id && !reviewSummaries[sub.id] ? (
                                <div className="flex items-center gap-2 text-muted-foreground text-xs py-2">
                                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                                  <span>Loading structured review summary...</span>
                                </div>
                              ) : reviewSummaries[sub.id] ? (
                                (() => {
                                  const r = reviewSummaries[sub.id];
                                  return (
                                    <div className="space-y-3">
                                      {/* Primary 4-Stat Grid */}
                                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                                        <div className="p-2.5 rounded-lg bg-background/60 border border-border/40">
                                          <span className="text-[10px] text-muted-foreground block">Course</span>
                                          <span className="font-semibold text-foreground truncate block">
                                            {r.course ? `${r.course.code} - ${r.course.name}` : sub.subject_name}
                                          </span>
                                        </div>
                                        <div className="p-2.5 rounded-lg bg-background/60 border border-border/40">
                                          <span className="text-[10px] text-muted-foreground block">Track</span>
                                          <span className="font-semibold text-foreground">
                                            {r.track ? `${r.track.name} (${r.track.key})` : "General (N/A)"}
                                          </span>
                                        </div>
                                        <div className="p-2.5 rounded-lg bg-background/60 border border-border/40">
                                          <span className="text-[10px] text-muted-foreground block">Assessment / Year</span>
                                          <span className="font-semibold text-foreground">
                                            {r.assessment} &bull; {r.year || "Unknown Year"}
                                          </span>
                                        </div>
                                        <div className="p-2.5 rounded-lg bg-background/60 border border-border/40">
                                          <span className="text-[10px] text-muted-foreground block">Duplicate State</span>
                                          <span
                                            className={`font-semibold ${
                                              r.duplicate_state.status === "UNIQUE"
                                                ? "text-emerald-400"
                                                : "text-amber-400"
                                            }`}
                                          >
                                            {r.duplicate_state.status}
                                          </span>
                                        </div>
                                      </div>

                                      {/* Question Ingestion & Mapping Row */}
                                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                                        <div className="p-2.5 rounded-lg bg-background/60 border border-border/40">
                                          <span className="text-[10px] text-muted-foreground block">Question Count</span>
                                          <span className="font-mono font-bold text-foreground">
                                            {r.question_count.total} total ({r.question_count.mapped} mapped, {r.question_count.unmapped} unmapped)
                                          </span>
                                        </div>
                                        <div className="p-2.5 rounded-lg bg-background/60 border border-border/40">
                                          <span className="text-[10px] text-muted-foreground block">Mapping Rate</span>
                                          <span className="font-mono font-bold text-accent">
                                            {r.mapping_rate_formatted}
                                          </span>
                                        </div>
                                        <div className="p-2.5 rounded-lg bg-background/60 border border-border/40 sm:col-span-1 col-span-2">
                                          <span className="text-[10px] text-muted-foreground block">Approval State</span>
                                          <span className="font-semibold text-foreground">
                                            {r.approval_state.status} {r.approval_state.reviewed_by ? `by ${r.approval_state.reviewed_by}` : ""}
                                          </span>
                                        </div>
                                      </div>

                                      {/* Provenance Box */}
                                      <div className="p-2.5 rounded-lg bg-background/40 border border-border/30 text-[11px] space-y-1 font-mono">
                                        <div className="flex justify-between flex-wrap text-muted-foreground">
                                          <span>Provenance Source: <strong className="text-foreground">{r.provenance.source}</strong></span>
                                          <span>File Size: {(r.provenance.file_size / (1024 * 1024)).toFixed(2)} MB</span>
                                        </div>
                                        <div className="text-muted-foreground truncate">
                                          File Hash: {r.provenance.file_hash}
                                        </div>
                                        {r.provenance.uploader_session_id && (
                                          <div className="text-muted-foreground truncate">
                                            Session ID: {r.provenance.uploader_session_id}
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  );
                                })()
                              ) : null}
                            </div>

                            {sub.consistency_notes && (
                              <p className="text-xs text-muted-foreground italic">
                                Consistency Note: {sub.consistency_notes}
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}
