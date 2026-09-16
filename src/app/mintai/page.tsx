"use client";

import { useState, useEffect } from "react";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { Leaf, Search, AlertCircle, BarChart3, Database, FileText, Activity, Clock, CheckCircle2 } from "lucide-react";
import { 
  getCurriculumBranches, 
  getCurriculumSemesters, 
  getCurriculumSubjects, 
  getPredictions, 
  getExamDNA 
} from "@/lib/api";
import { 
  PredictionResponse, 
  ExamDNAAnalysis, 
  BackendPrediction, 
  CurriculumSubject 
} from "@/lib/types";

type ExamDNAResponse = ExamDNAAnalysis & {
  sample_size?: { exam_types?: unknown[]; papers?: number; questions?: number };
};

const examTypeOrder = (examType: string) => {
  const order: Record<string, number> = { CT1: 1, CT2: 2, CT3: 3, CT4: 4, END_SEM: 5 };
  return order[examType] ?? 99;
};

export default function MintAIPage() {
  // Curriculum hierarchy states from backend
  const [branches, setBranches] = useState<string[]>([]);
  const [semesters, setSemesters] = useState<number[]>([]);
  const [subjects, setSubjects] = useState<CurriculumSubject[]>([]);

  // User selections
  const [selectedBranch, setSelectedBranch] = useState<string>("");
  const [selectedSemester, setSelectedSemester] = useState<string>("");
  const [selectedSubject, setSelectedSubject] = useState<CurriculumSubject | null>(null);
  const [selectedExam, setSelectedExam] = useState<string>("");
  const [examinations, setExaminations] = useState<string[]>([]);

  // Loading & error states
  const [isLoadingBranches, setIsLoadingBranches] = useState(true);
  const [isLoadingSemesters, setIsLoadingSemesters] = useState(false);
  const [isLoadingSubjects, setIsLoadingSubjects] = useState(false);
  const [isLoadingExaminations, setIsLoadingExaminations] = useState(false);

  const [branchLoadError, setBranchLoadError] = useState("");
  const [semesterLoadError, setSemesterLoadError] = useState("");
  const [subjectLoadError, setSubjectLoadError] = useState("");
  const [examLoadError, setExamLoadError] = useState("");

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [hasData, setHasData] = useState(false);
  const [error, setError] = useState("");

  const [predictions, setPredictions] = useState<PredictionResponse | null>(null);
  const [dna, setDna] = useState<ExamDNAAnalysis | null>(null);

  // Analytical readiness derived directly from backend contract
  const isSubjectAvailable = Boolean(
    selectedSubject &&
    selectedSubject.status === "MATCHED" &&
    selectedSubject.course_id !== null &&
    selectedSubject.has_exams === true
  );

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

  // 2. When Branch changes: Load semesters for that branch from backend
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
    setExaminations([]);
    setDna(null);
    setPredictions(null);
    setHasData(false);
    setError("");

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
        console.error(`Failed to load semesters for branch ${selectedBranch}`, err);
        setSemesterLoadError("Unable to load semesters for this branch.");
      })
      .finally(() => {
        if (active) setIsLoadingSemesters(false);
      });

    return () => {
      active = false;
    };
  }, [selectedBranch]);

  // 3. When Semester changes: Load subjects for that branch + semester from backend
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
    setExaminations([]);
    setDna(null);
    setPredictions(null);
    setHasData(false);
    setError("");

    getCurriculumSubjects(selectedBranch, selectedSemester)
      .then((subjectList) => {
        if (!active) return;
        setSubjects(subjectList);
        // Default to first subject if available
        if (subjectList.length > 0) {
          setSelectedSubject(subjectList[0]);
        }
      })
      .catch((err) => {
        if (!active) return;
        console.error(`Failed to load subjects for ${selectedBranch} sem ${selectedSemester}`, err);
        setSubjectLoadError("Unable to load subjects for this semester.");
      })
      .finally(() => {
        if (active) setIsLoadingSubjects(false);
      });

    return () => {
      active = false;
    };
  }, [selectedBranch, selectedSemester]);

  // 4. When Subject changes: If analytically available, fetch actual ExamDNA metadata to drive exam selector
  useEffect(() => {
    setSelectedExam("");
    setExaminations([]);
    setDna(null);
    setPredictions(null);
    setHasData(false);
    setError("");
    setExamLoadError("");

    if (!selectedSubject) return;

    // Guardrail: If subject is UNMATCHED, AMBIGUOUS, or has 0 exams, do NOT call DNA or predictions
    if (!isSubjectAvailable || selectedSubject.course_id === null) {
      return;
    }

    let active = true;
    setIsLoadingExaminations(true);

    getExamDNA(selectedSubject.course_id)
      .then((data) => {
        if (!active) return;
        const rawExamTypes = (data as ExamDNAResponse)?.sample_size?.exam_types || [];
        const examTypes = [...new Set(rawExamTypes)]
          .filter((value): value is string => typeof value === "string" && value.length > 0)
          .sort((a, b) => examTypeOrder(a) - examTypeOrder(b) || a.localeCompare(b));

        setDna(data);
        setExaminations(examTypes);
        if (examTypes.length > 0) {
          setSelectedExam(examTypes[0]);
        }
      })
      .catch((err) => {
        if (!active) return;
        console.error("Failed to retrieve examination metadata", err);
        setExamLoadError("Unable to retrieve examination metadata for this course.");
        setDna(null);
        setExaminations([]);
      })
      .finally(() => {
        if (active) setIsLoadingExaminations(false);
      });

    return () => {
      active = false;
    };
  }, [selectedSubject, isSubjectAvailable]);

  // 5. Forecast submission using resolved backend Course identity
  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSubject || !isSubjectAvailable || selectedSubject.course_id === null || !selectedExam) {
      setError("Select an analytically available course with valid examination papers before running a forecast.");
      return;
    }

    setIsAnalyzing(true);
    setHasData(false);
    setError("");

    try {
      // Execute prediction using resolved backend course_id
      const [predData, dnaData] = await Promise.all([
        getPredictions(selectedSubject.course_id).catch((err) => {
          if (err.status === 404) return null;
          throw err;
        }),
        dna ? Promise.resolve(dna) : getExamDNA(selectedSubject.course_id).catch(() => null)
      ]);

      if (!predData || !predData.predictions) {
        setError("No prediction data generated for this course.");
      } else {
        setPredictions(predData);
        if (dnaData) setDna(dnaData);
        setHasData(true);
        localStorage.setItem(
          "markmint_recent", 
          JSON.stringify({ 
            course: selectedSubject.subject_name,
            course_id: selectedSubject.course_id,
            canonical_code: selectedSubject.canonical_code,
            exam: selectedExam, 
            type: "Forecast" 
          })
        );
      }
    } catch (err: any) {
      setError(err.message || "Failed to fetch predictions. Ensure the backend is running.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground selection:bg-accent/20">
      <Navbar />
      
      <main className="flex-1 w-full max-w-7xl mx-auto px-6 md:px-10 pt-8 pb-32 grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Panel: Configuration */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          <div className="bg-card border border-border rounded-xl p-6 shadow-sm transition-all duration-150">
            <h2 className="text-lg font-bold mb-1 flex items-center gap-2">
              <Leaf className="w-4 h-4 text-accent" />
              Intelligence Engine
            </h2>
            <p className="text-xs text-muted-foreground mb-6">
              Generate deterministic probability forecasts based on historical evidence.
            </p>
            
            <form onSubmit={handleAnalyze} className="space-y-4">
              <div>
                {/* Branch Selector */}
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2 block">
                  Select Branch
                </label>
                <select 
                  value={selectedBranch}
                  onChange={(e) => setSelectedBranch(e.target.value)}
                  disabled={isLoadingBranches || branches.length === 0}
                  className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-accent transition-colors appearance-none mb-4"
                >
                  <option value="" disabled>Select a branch</option>
                  {branches.map((branch) => (
                    <option key={branch} value={branch}>{branch}</option>
                  ))}
                </select>

                {/* Semester Selector */}
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2 block">
                  Select Semester
                </label>
                <select
                  value={selectedSemester}
                  onChange={(e) => setSelectedSemester(e.target.value)}
                  disabled={!selectedBranch || semesters.length === 0 || isLoadingSemesters}
                  className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-accent transition-colors appearance-none mb-4"
                >
                  <option value="" disabled>Select a semester</option>
                  {semesters.map((semester) => (
                    <option key={semester} value={String(semester)}>Semester {semester}</option>
                  ))}
                </select>

                {/* Subject Selector */}
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2 block">
                  Select Subject
                </label>
                <select
                  value={selectedSubject?.curriculum_id || ""}
                  onChange={(e) => {
                    const found = subjects.find((s) => s.curriculum_id === e.target.value) || null;
                    setSelectedSubject(found);
                  }}
                  disabled={!selectedSemester || subjects.length === 0 || isLoadingSubjects}
                  className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-accent transition-colors appearance-none mb-2"
                >
                  <option value="" disabled>Select a subject</option>
                  {subjects.map((sub) => {
                    const code = sub.canonical_code ? ` [${sub.canonical_code}]` : "";
                    const badge = sub.status === "MATCHED" && sub.has_exams
                      ? ""
                      : sub.status === "AMBIGUOUS"
                      ? " (Ambiguous)"
                      : sub.status === "MATCHED" && !sub.has_exams
                      ? " (No Exams)"
                      : " (Awaiting Papers)";
                    return (
                      <option key={sub.curriculum_id} value={sub.curriculum_id}>
                        {sub.subject_name}{code}{badge}
                      </option>
                    );
                  })}
                </select>

                {/* Analytical Readiness Indicator */}
                {selectedSubject && (
                  <div className="mb-4 text-xs">
                    {selectedSubject.status === "MATCHED" && selectedSubject.has_exams && (
                      <span className="text-emerald-500 flex items-center gap-1 font-medium">
                        <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" />
                        Analytically available ({selectedSubject.exam_count} exams, {selectedSubject.question_count} questions)
                      </span>
                    )}
                    {selectedSubject.status === "MATCHED" && !selectedSubject.has_exams && (
                      <span className="text-amber-500 flex items-center gap-1">
                        <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                        Catalog indexed, but 0 historical exam papers available.
                      </span>
                    )}
                    {selectedSubject.status === "AMBIGUOUS" && (
                      <span className="text-amber-500 flex items-center gap-1">
                        <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                        Ambiguous curriculum mapping. Forecasts unavailable.
                      </span>
                    )}
                    {selectedSubject.status === "UNMATCHED" && (
                      <span className="text-muted-foreground flex items-center gap-1">
                        <Database className="w-3.5 h-3.5 opacity-60 flex-shrink-0" />
                        Awaiting historical examination papers.
                      </span>
                    )}
                  </div>
                )}

                {/* Examination Selector */}
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2 block">
                  Select Examination
                </label>
                <select
                  value={selectedExam}
                  onChange={(e) => setSelectedExam(e.target.value)}
                  disabled={!isSubjectAvailable || isLoadingExaminations || examinations.length === 0}
                  className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-accent transition-colors appearance-none"
                >
                  <option value="" disabled>
                    {!isSubjectAvailable
                      ? "Examination selection unavailable"
                      : examinations.length === 0
                      ? "No examination types found"
                      : "Select an examination"}
                  </option>
                  {examinations.map((examType) => (
                    <option key={examType} value={examType}>{examType}</option>
                  ))}
                </select>

                {/* Error & Feedback Messages */}
                {isLoadingBranches && (
                  <p className="mt-2 text-xs text-muted-foreground">Loading curriculum branches...</p>
                )}
                {branchLoadError && (
                  <p className="mt-2 text-xs text-red-400">{branchLoadError}</p>
                )}
                {isLoadingSemesters && (
                  <p className="mt-2 text-xs text-muted-foreground">Loading semesters...</p>
                )}
                {semesterLoadError && (
                  <p className="mt-2 text-xs text-red-400">{semesterLoadError}</p>
                )}
                {isLoadingSubjects && (
                  <p className="mt-2 text-xs text-muted-foreground">Loading subjects from catalog...</p>
                )}
                {subjectLoadError && (
                  <p className="mt-2 text-xs text-red-400">{subjectLoadError}</p>
                )}
                {isSubjectAvailable && isLoadingExaminations && (
                  <p className="mt-2 text-xs text-muted-foreground">Loading examination metadata...</p>
                )}
                {isSubjectAvailable && !isLoadingExaminations && examLoadError && (
                  <p className="mt-2 text-xs text-amber-400">{examLoadError}</p>
                )}
              </div>

              {/* Submit Button */}
              <button 
                type="submit"
                disabled={!isSubjectAvailable || !selectedExam || isAnalyzing}
                className="w-full mt-4 bg-foreground text-background py-2.5 rounded-md text-sm font-medium hover:bg-foreground/90 transition-all duration-150 active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isAnalyzing ? (
                  <>
                    <div className="w-4 h-4 border-2 border-background border-t-transparent rounded-full animate-spin" />
                    Analyzing Evidence...
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4" />
                    Run Forecast
                  </>
                )}
              </button>
            </form>
          </div>

          <div className="bg-accent/5 border border-accent/20 rounded-xl p-5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-accent mb-2 flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              Evidence Rule
            </h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              MintAI relies strictly on deterministic historical extraction. It does not hallucinate probabilities for subjects lacking historical examination papers.
            </p>
          </div>
        </div>

        {/* Right Panel: Data Dashboard & States */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          {error ? (
            <div className="h-full min-h-[400px] border border-red-500/20 bg-red-500/5 rounded-xl flex flex-col items-center justify-center text-center p-8 relative overflow-hidden">
              <img 
                src="/dog-guilty.jpg" 
                alt="Guilty dog" 
                className="w-32 h-32 rounded-full object-cover border-4 border-red-500/20 shadow-lg mb-6 hover:scale-105 transition-transform"
              />
              <h3 className="text-xl font-bold text-red-500 mb-2">Analysis Failed</h3>
              <p className="text-sm text-red-400 max-w-sm mb-2">{error}</p>
              <p className="text-xs text-red-400/70 max-w-sm italic">
                &quot;Sorry, this dog ate your prediction while the backend was asleep. (API Connection Refused)&quot;
              </p>
            </div>
          ) : isAnalyzing ? (
             <div className="h-full min-h-[400px] border border-border rounded-xl p-8 flex flex-col justify-center">
                <div className="max-w-md mx-auto w-full flex flex-col items-center justify-center text-center">
                  <Activity className="w-10 h-10 text-accent animate-pulse mb-4" />
                  <h3 className="text-lg font-bold text-foreground mb-2">Analyzing Evidence Pool</h3>
                  <p className="text-sm text-muted-foreground max-w-sm">
                    Connecting to intelligence layer...
                  </p>
                </div>
             </div>
          ) : predictions ? (
            <div className="flex flex-col gap-8 animate-in fade-in duration-500">
              
              {/* STATE 2: DASHBOARD */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-card border border-border rounded-xl p-5 hover:border-border/80 transition-colors">
                  <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">Data Quality</p>
                  <div className="flex items-end gap-2">
                    <span className="text-2xl font-bold text-foreground capitalize">{predictions.data_quality || "Unknown"}</span>
                  </div>
                </div>
                <div className="bg-card border border-border rounded-xl p-5 hover:border-border/80 transition-colors">
                  <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">Target Year</p>
                  <div className="flex items-end gap-2">
                    <span className="text-2xl font-bold text-foreground">{predictions.target_year || "Latest"}</span>
                  </div>
                </div>
                <div className="bg-card border border-border rounded-xl p-5 hover:border-border/80 transition-colors">
                  <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">Evidence Pool</p>
                  <div className="flex flex-col gap-0.5">
                    <span className="text-sm text-foreground font-medium">{predictions?.evidence || "Analyzing responses..."}</span>
                    <span className="text-sm text-muted-foreground">
                      {predictions?.predictions ? predictions.predictions.reduce((s, p) => s + (p.historyCount || 0), 0) : 0} Questions
                    </span>
                  </div>
                </div>
              </div>

              {/* DNA SUMMARY */}
              {dna && dna.analysis_summary && (
                <div className="bg-card border border-border rounded-xl p-6">
                  <h3 className="font-bold text-lg flex items-center gap-2 mb-3">
                    <Database className="w-5 h-5 text-accent" />
                    ExamDNA Insights
                  </h3>
                  <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
                    {dna.analysis_summary}
                  </p>
                </div>
              )}

              {/* PREDICTION CARDS */}
              <div className="flex flex-col gap-4">
                <h3 className="font-bold text-lg flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-accent" />
                  Forecasted Topics
                </h3>
                
                {predictions.predictions && predictions.predictions.length > 0 ? (
                  predictions.predictions.map((p: BackendPrediction, i: number) => (
                    <div key={i} className="bg-card border border-border rounded-xl p-5 hover:-translate-y-[1px] transition-transform duration-150">
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h4 className="text-lg font-bold text-foreground mb-1">{p.name || "Unknown Topic"}</h4>
                          <div className="flex items-center gap-3 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3 text-accent" /> 
                              Rank #{p.rank}
                            </span>
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" /> 
                              Last: {p.lastSeen || "Unknown"}
                            </span>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-mono font-bold text-accent">{typeof p.confidence === "string" ? p.confidence : (typeof p.confidence === "number" ? Math.round(p.confidence * 100) + "%" : "—")}</div>
                          <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Confidence</div>
                        </div>
                      </div>
                      
                      <div className="w-full bg-background rounded-full h-1.5 mb-4 overflow-hidden">
                        <div 
                          className="bg-accent h-full" 
                          style={{ 
                            width: typeof p.confidence === "number" 
                              ? `${Math.round(p.confidence * 100)}%` 
                              : p.confidence === "LOW" ? "30%" : p.confidence === "MEDIUM" ? "60%" : p.confidence === "HIGH" ? "90%" : "—" 
                          }} 
                        />
                      </div>
                      
                      <div className="flex flex-col gap-2 text-xs text-muted-foreground bg-background rounded-lg px-4 py-3 border border-border/50">
                        <div className="flex items-center justify-between">
                          <span>Appeared <strong>{p.historyCount}</strong> times historically</span>
                          {p.category && (
                            <span className="capitalize text-foreground font-medium">{p.category}</span>
                          )}
                        </div>
                        {p.evidence_details && (
                          <div className="mt-2 pt-2 border-t border-border/50">
                            <div className="flex flex-col gap-1 text-xs text-muted-foreground bg-background/60 rounded-md px-2 py-1.5 border border-border/30">
                              <span className="font-medium text-foreground">Historical Evidence</span>
                              <span>Appeared <strong className="text-foreground">{p.evidence_details.occurrences ?? 0}</strong> time{(p.evidence_details.occurrences || 0) > 1 ? 's' : ''} historically</span>
                              <span>Recent frequency <strong className="text-foreground">{typeof p.evidence_details.recent_freq === 'number' ? (p.evidence_details.recent_freq * 100).toFixed(1) + '%' : '—'}</strong></span>
                              <span>Historical frequency <strong className="text-foreground">{typeof p.evidence_details.hist_freq === 'number' ? (p.evidence_details.hist_freq * 100).toFixed(1) + '%' : '—'}</strong></span>
                              {p.evidence_details.combo !== undefined && (
                                <span>Pattern match <strong className="text-foreground">{p.evidence_details.combo ? 'Confirmed' : 'Not confirmed'}</strong></span>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-muted-foreground border border-dashed border-border rounded-xl">
                    No predictions could be generated from the evidence pool. (Unresolved state)
                  </div>
                )}
                
              </div>
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
              <h3 className="text-lg font-bold text-foreground mb-2">Catalog Indexed — No Examination Papers</h3>
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
                Select an examination type on the left and click <strong>Run Forecast</strong>.
              </p>
            </div>
          ) : (
            <div className="h-full min-h-[400px] border border-dashed border-border rounded-xl flex flex-col items-center justify-center text-center p-8 bg-card/30">
              <Database className="w-10 h-10 text-muted-foreground mb-4 opacity-30" />
              <h3 className="text-lg font-bold text-foreground mb-2">Awaiting Parameters</h3>
              <p className="text-sm text-muted-foreground max-w-sm">
                Select an academic branch, semester, and course on the left to extract the evidence pool.
              </p>
            </div>
          )}
        </div>
      </main>
      
      <Footer />
    </div>
  );
}
