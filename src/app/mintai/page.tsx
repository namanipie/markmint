"use client";

import { useState, useEffect } from "react";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { Leaf, Search, AlertCircle, BarChart3, Database, FileText, Activity, Clock, ShieldCheck, CheckCircle2 } from "lucide-react";
import { getCourses, getPredictions, getExamDNA } from "@/lib/api";
import { BackendCourse, PredictionResponse, ExamDNAAnalysis, BackendPrediction } from "@/lib/types";
import { CURRICULUM } from "@/lib/curriculumData";

type CourseRecord = BackendCourse & {
  id?: number | string;
  name?: string;
  code?: string;
};

type CurriculumSubject = {
  id: string;
  name: string;
  credits?: number;
};

type ExamDNAResponse = ExamDNAAnalysis & {
  sample_size?: { exam_types?: unknown[] };
};

const normalizeName = (value: string) => value.toLowerCase().replace(/[^a-z0-9]+/g, "");

const examTypeOrder = (examType: string) => {
  const order: Record<string, number> = { CT1: 1, CT2: 2, CT3: 3, CT4: 4, END_SEM: 5 };
  return order[examType] ?? 99;
};

const supportedExamTypes = ["CT1", "CT2", "CT3", "CT4", "END_SEM"];

export default function MintAIPage() {
  const [courses, setCourses] = useState<CourseRecord[]>([]);
  const [selectedBranch, setSelectedBranch] = useState("Computer Science and Engineering");
  const [selectedSemester, setSelectedSemester] = useState("1");
  const [selectedCourse, setSelectedCourse] = useState("");
  const [selectedExam, setSelectedExam] = useState("");
  const [examinations, setExaminations] = useState<string[]>([]);
  const [isLoadingCourses, setIsLoadingCourses] = useState(true);
  const [isLoadingExaminations, setIsLoadingExaminations] = useState(false);
  const [courseLoadError, setCourseLoadError] = useState("");
  const [examLoadError, setExamLoadError] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [hasData, setHasData] = useState(false);
  const [error, setError] = useState("");

  const [predictions, setPredictions] = useState<PredictionResponse | null>(null);
  const [dna, setDna] = useState<ExamDNAAnalysis | null>(null);

  const branches = Object.keys(CURRICULUM).sort();
  const semesters = selectedBranch
    ? Object.keys(CURRICULUM[selectedBranch] || {}).sort((a, b) => Number(a) - Number(b))
    : [];
  const curriculumSubjects = (CURRICULUM[selectedBranch]?.[selectedSemester] || []) as CurriculumSubject[];
  const availableSubjects = curriculumSubjects
    .map((subject) => ({
      subject,
      course: courses.find((course) => normalizeName(course.name || course.course_name) === normalizeName(subject.name)),
    }))
    .filter((entry): entry is { subject: CurriculumSubject; course: CourseRecord } => Boolean(entry.course));
  const selectedCourseRecord = availableSubjects.find(
    ({ course }) => String(course.id ?? course.course_id) === selectedCourse,
  )?.course;
  const selectedCourseId = selectedCourseRecord
    ? String(selectedCourseRecord.id ?? selectedCourseRecord.course_id)
    : "";
  const selectedSubject = selectedCourseRecord?.name || selectedCourseRecord?.course_name || "";

  useEffect(() => {
    getCourses().then((data) => {
      // Data might be an array or an object with an array
      const courseList = Array.isArray(data) ? data : (data.items || data.courses || []);
      setCourses(courseList as CourseRecord[]);
      setCourseLoadError("");
    }).catch(err => {
      console.error("Failed to load courses", err);
      setCourseLoadError("Unable to load courses. Please try again.");
    }).finally(() => setIsLoadingCourses(false));
  }, []);

  useEffect(() => {
    if (!selectedCourseRecord) {
      return;
    }

    let active = true;
    getExamDNA(selectedCourseId)
      .then((data) => {
        if (!active) return;
        const rawExamTypes = (data as ExamDNAResponse).sample_size?.exam_types || [];
        const examTypes = [...new Set(rawExamTypes)].sort(
          (a, b) => String(a).localeCompare(String(b)),
        ).filter((value): value is string => typeof value === "string" && value.length > 0)
          .sort((a, b) => examTypeOrder(a) - examTypeOrder(b) || a.localeCompare(b));
        setDna(data);
        setExaminations(examTypes);
        setSelectedExam("");
      })
      .catch((err) => {
        if (!active) return;
        console.error("Failed to load examinations", err);
        setExamLoadError("Course-specific examination data is unavailable; showing supported examination types.");
        setDna(null);
        setExaminations(supportedExamTypes);
      })
      .finally(() => {
        if (active) setIsLoadingExaminations(false);
      });

    return () => {
      active = false;
    };
  }, [selectedCourseId, selectedCourseRecord]);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourseRecord || !selectedExam) {
      setError("Select a valid subject and examination before running a forecast.");
      return;
    }
    
    setIsAnalyzing(true);
    setHasData(false);
    setError("");
    
    console.log("=== MINTAI API TRACE ===");
    console.log("Course record:", selectedCourseRecord);
    console.log("Course.id:", selectedCourseRecord?.id ?? selectedCourseId);
    console.log("Course.code:", selectedCourseRecord?.code || (selectedCourseRecord as any)?.course_code || "N/A");
    console.log("Course.name:", selectedCourseRecord?.name || selectedCourseRecord?.course_name || selectedSubject);
    console.log("Prediction URL:", `/api/predictions/${encodeURIComponent(selectedSubject)}`);
    console.log("DNA URL:", `/api/analysis/dna?course_id=${selectedCourseId}`);
    console.log("========================");
    console.log("=== RUN FORECAST DEBUG ===");
    console.log("selectedBranch:", selectedBranch);
    console.log("selectedSemester:", selectedSemester);
    console.log("selectedCourse (React state):", selectedCourse);
    console.log("selectedExam:", selectedExam);
    console.log("matched course object:", selectedCourseRecord);
    console.log("course.id:", selectedCourseRecord.id);
    console.log("course.code:", selectedCourseRecord.code || (selectedCourseRecord as any).course_code);
    console.log("course.name:", selectedCourseRecord.name || (selectedCourseRecord as any).course_name);
    console.log("final prediction URL:", `/api/predictions/${encodeURIComponent(selectedSubject)}`);
    console.log("==========================");

    try {
      // The prediction API accepts the course name; the examination remains frontend context.
      const [predData, dnaData] = await Promise.all([
        getPredictions(selectedSubject).catch(e => {
            if(e.status === 404) return null;
            throw e;
        }),
        getExamDNA(selectedCourseId).catch(e => null)
      ]);
      
      if (!predData) {
        setError("No prediction data found for this course. Try another one.");
      } else {
        setPredictions(predData);
        setDna(dnaData);
        setHasData(true);
        localStorage.setItem("markmint_recent", JSON.stringify({ course: selectedSubject, exam: selectedExam, type: "Forecast" }));
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
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2 block">
                  Select Branch
                </label>
                <select 
                  value={selectedBranch}
                  onChange={(e) => {
                    setSelectedBranch(e.target.value);
                    setSelectedSemester("");
                    setSelectedCourse("");
                    setSelectedExam("");
                    setIsLoadingExaminations(false);
                    setExaminations([]);
                    setExamLoadError("");
                    setDna(null);
                  }}
                  disabled={isLoadingCourses || branches.length === 0}
                  className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-accent transition-colors appearance-none mb-4"
                >
                  <option value="" disabled>Select a branch</option>
                  {branches.map((branch) => (
                    <option key={branch} value={branch}>{branch}</option>
                  ))}
                </select>

                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2 block">
                  Select Semester
                </label>
                <select
                  value={selectedSemester}
                  onChange={(e) => {
                    setSelectedSemester(e.target.value);
                    setSelectedCourse("");
                    setSelectedExam("");
                    setIsLoadingExaminations(false);
                    setExaminations([]);
                    setExamLoadError("");
                    setDna(null);
                  }}
                  disabled={!selectedBranch || semesters.length === 0}
                  className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-accent transition-colors appearance-none mb-4"
                >
                  <option value="" disabled>Select a semester</option>
                  {semesters.map((semester) => (
                    <option key={semester} value={semester}>Semester {semester}</option>
                  ))}
                </select>

                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2 block">
                  Select Subject
                </label>
                <select
                  value={selectedCourse}
                  onChange={(e) => {
                    setSelectedCourse(e.target.value);
                    setSelectedExam("");
                    setIsLoadingExaminations(true);
                    setExaminations([]);
                    setDna(null);
                    setExamLoadError("");
                  }}
                  disabled={!selectedSemester || availableSubjects.length === 0 || isLoadingCourses}
                  className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-accent transition-colors appearance-none mb-4"
                >
                  <option value="" disabled>Select a subject</option>
                  {availableSubjects.map(({ subject, course }) => {
                    const courseId = String(course.id ?? course.course_id);
                    const courseCode = course.code || course.course_code || "";
                    const courseName = course.name || course.course_name || subject.name;
                    return (
                      <option key={courseId} value={courseId}>
                        {courseCode ? `${courseName} (${courseCode})` : courseName}
                      </option>
                    );
                  })}
                </select>

                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2 block">
                  Select Examination
                </label>
                <select
                  value={selectedExam}
                  onChange={(e) => setSelectedExam(e.target.value)}
                  disabled={!selectedCourse || isLoadingExaminations || examinations.length === 0}
                  className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-accent transition-colors appearance-none"
                >
                  <option value="" disabled>Select an examination</option>
                  {examinations.map((examType) => (
                    <option key={examType} value={examType}>{examType}</option>
                  ))}
                </select>

                {isLoadingCourses && (
                  <p className="mt-2 text-xs text-muted-foreground">Loading courses...</p>
                )}
                {!isLoadingCourses && courseLoadError && (
                  <p className="mt-2 text-xs text-red-400">{courseLoadError}</p>
                )}
                {!isLoadingCourses && selectedBranch && semesters.length === 0 && (
                  <p className="mt-2 text-xs text-muted-foreground">No semesters available for this branch.</p>
                )}
                {!isLoadingCourses && selectedSemester && availableSubjects.length === 0 && (
                  <p className="mt-2 text-xs text-muted-foreground">No subjects available for this semester.</p>
                )}
                {selectedCourse && isLoadingExaminations && (
                  <p className="mt-2 text-xs text-muted-foreground">Loading examinations...</p>
                )}
                {selectedCourse && !isLoadingExaminations && examLoadError && (
                  <p className="mt-2 text-xs text-amber-400">{examLoadError}</p>
                )}
                {selectedCourse && !isLoadingExaminations && !examLoadError && examinations.length === 0 && (
                  <p className="mt-2 text-xs text-muted-foreground">No examinations available for this subject.</p>
                )}
              </div>

              <button 
                type="submit"
                disabled={!selectedCourse || !selectedExam || isAnalyzing || Boolean(courseLoadError)}
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
              MintAI relies strictly on deterministic historical extraction. It does not hallucinate probabilities. The unresolved questions are intentional.
            </p>
          </div>
        </div>

        {/* Right Panel: Data Dashboard */}
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
                "Sorry, this dog ate your prediction while the backend was asleep. (API Connection Refused)"
              </p>
            </div>
          ) : !hasData && !isAnalyzing ? (
            <div className="h-full min-h-[400px] border border-dashed border-border rounded-xl flex flex-col items-center justify-center text-center p-8 bg-card/30">
              <Database className="w-10 h-10 text-muted-foreground mb-4 opacity-30" />
              <h3 className="text-lg font-bold text-foreground mb-2">Awaiting Parameters</h3>
              <p className="text-sm text-muted-foreground max-w-sm">
                No historical papers available yet. Select a course on the left to extract the evidence pool.
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
                    <span className="text-sm text-muted-foreground">{predictions?.predictions ? predictions.predictions.reduce((s,p) => s + (p.historyCount||0), 0) : 0} Questions</span>
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
                        <div className="bg-accent h-full" style={{ width: (typeof p.confidence === "number" ? Math.round(p.confidence * 100) + "%" : (p.confidence === "LOW" ? "30%" : p.confidence === "MEDIUM" ? "60%" : p.confidence === "HIGH" ? "90%" : "—")) }}></div>
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
          ) : null}
        </div>
      </main>
      
      <Footer />
    </div>
  );
}
