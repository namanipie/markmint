"use client";

import { useState, useEffect } from "react";
import { Navbar } from "@/components/layout/navbar";
import { PageHeader } from "@/components/layout/page-header";
import { Combobox } from "@/components/ui/combobox";
import { CurriculumSubject, HistoricalQuestion } from "@/lib/types";
import { getCurriculumBranches, getCurriculumSemesters, getCurriculumSubjects, getHistoricalQuestions } from "@/lib/api";
import { MathText } from "@/components/ui/math-text";
import { Activity, Search, AlertCircle, BookOpen } from "lucide-react";
import Link from "next/link";

export default function PracticePage() {
  const [branches, setBranches] = useState<string[]>([]);
  const [semesters, setSemesters] = useState<number[]>([]);
  const [subjects, setSubjects] = useState<CurriculumSubject[]>([]);

  const [selectedBranch, setSelectedBranch] = useState<string>("");
  const [selectedSemester, setSelectedSemester] = useState<string>("");
  const [selectedSubject, setSelectedSubject] = useState<CurriculumSubject | null>(null);

  const [questions, setQuestions] = useState<HistoricalQuestion[]>([]);
  const [isLoadingQuestions, setIsLoadingQuestions] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  useEffect(() => {
    let active = true;
    getCurriculumBranches().then((branchList) => {
      if (!active) return;
      setBranches(branchList);
      if (branchList.length > 0) {
        setSelectedBranch(branchList.includes("Aerospace Engineering") ? "Aerospace Engineering" : branchList[0]);
      }
    }).catch(console.error);
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!selectedBranch) return;
    let active = true;
    setSemesters([]);
    setSelectedSemester("");
    setSubjects([]);
    setSelectedSubject(null);
    getCurriculumSemesters(selectedBranch).then(res => {
      if(active) setSemesters(res);
    }).catch(console.error);
    return () => { active = false; };
  }, [selectedBranch]);

  useEffect(() => {
    if (!selectedBranch || !selectedSemester) return;
    let active = true;
    setSubjects([]);
    setSelectedSubject(null);
    getCurriculumSubjects(selectedBranch, selectedSemester).then(res => {
      if(active) setSubjects(res);
    }).catch(console.error);
    return () => { active = false; };
  }, [selectedBranch, selectedSemester]);

  const handleFetchQuestions = async () => {
    if (!selectedSubject?.course_id) return;
    setIsLoadingQuestions(true);
    setHasSearched(true);
    try {
      const res = await getHistoricalQuestions(selectedSubject.course_id, undefined, undefined, 50);
      setQuestions(res.questions || []);
    } catch (err) {
      console.error(err);
      setQuestions([]);
    } finally {
      setIsLoadingQuestions(false);
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-background text-foreground">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
        <h1 className="sr-only">MarkMint Practice</h1>
        
        {/* Left Sidebar */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
            <div className="mb-6">
              <h2 className="text-[10px] font-bold tracking-widest uppercase text-muted-foreground mb-1">Your Subject</h2>
              <h3 className="text-xl font-bold text-foreground mb-1">Select Course</h3>
              <p className="text-xs text-muted-foreground mb-4 leading-relaxed">Choose your course to test your knowledge against past exams.</p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-1">Academic Branch</label>
                <Combobox
                  options={branches.map((b) => ({ value: b, label: b }))}
                  value={selectedBranch}
                  onChange={setSelectedBranch}
                  placeholder="Select branch..."
                  disabled={branches.length === 0}
                />
              </div>

              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-1">Semester</label>
                <Combobox
                  options={semesters.map((s) => ({ value: String(s), label: `Semester ${s}` }))}
                  value={selectedSemester}
                  onChange={setSelectedSemester}
                  placeholder="Select semester..."
                  disabled={semesters.length === 0}
                />
              </div>

              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-1">Course / Subject</label>
                <Combobox
                  options={subjects.map((s) => ({ value: s.subject_name, label: s.subject_name }))}
                  value={selectedSubject?.subject_name || ""}
                  onChange={(val) => {
                    const subj = subjects.find((s) => s.subject_name === val);
                    setSelectedSubject(subj || null);
                    setHasSearched(false);
                  }}
                  placeholder="Select course..."
                  disabled={subjects.length === 0}
                />
              </div>
            </div>

            <button
              className="w-full bg-accent text-accent-foreground font-semibold py-2.5 rounded-lg transition-opacity hover:opacity-90 flex items-center justify-center gap-2 mt-6 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
              onClick={handleFetchQuestions}
              disabled={!selectedSubject?.has_exams || isLoadingQuestions}
            >
              {isLoadingQuestions ? (
                <><Activity className="w-4 h-4 animate-spin" /><span>Loading Questions...</span></>
              ) : (
                <><Search className="w-4 h-4" /><span>Start Practice</span></>
              )}
            </button>
          </div>
        </div>

        {/* Right Content Area */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          <div className="flex items-center justify-between border-b border-border pb-4">
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <BookOpen className="w-6 h-6 text-accent" />
              Past Exam Questions
            </h2>
          </div>

          {!hasSearched ? (
            <div className="h-full min-h-[400px] border border-dashed border-border/80 bg-card/60 rounded-xl flex flex-col items-center justify-center text-center p-8">
              <div className="inline-flex p-3 rounded-full bg-secondary text-muted-foreground mb-4">
                <BookOpen className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-foreground mb-2">Ready to Practice?</h3>
              <p className="text-sm text-muted-foreground max-w-md">
                Select your course from the left panel and click Start Practice to test your knowledge against real questions from past exam papers.
              </p>
            </div>
          ) : isLoadingQuestions ? (
            <div className="h-full min-h-[400px] border border-dashed border-border/80 bg-card/60 rounded-xl flex flex-col items-center justify-center text-center p-8">
              <Activity className="w-8 h-8 text-accent animate-spin mb-4" />
              <p className="text-sm text-muted-foreground font-medium uppercase tracking-widest">Loading Question Bank</p>
            </div>
          ) : questions.length === 0 ? (
            <div className="h-full min-h-[400px] border border-dashed border-border/80 bg-card/60 rounded-xl flex flex-col items-center justify-center text-center p-8">
              <div className="inline-flex p-3 rounded-full bg-secondary text-muted-foreground mb-4">
                <AlertCircle className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-foreground mb-2">No Questions Found</h3>
              <p className="text-sm text-muted-foreground max-w-md">
                We couldn't find any historical questions for this course. Try selecting another course or check back later.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {questions.map((q, idx) => (
                <div key={idx} className="bg-card rounded-xl p-6 border border-border shadow-sm relative group overflow-hidden">
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-accent/20" />
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-bold text-muted-foreground">Q{idx + 1}</span>
                      {q.topics?.[0] && (
                        <span className="bg-secondary text-muted-foreground text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded">
                          {q.topics?.[0]}
                        </span>
                      )}
                    </div>
                    {q.marks && (
                      <span className="bg-emerald-500/10 text-emerald-500 text-xs font-bold px-2.5 py-1 rounded-md">
                        {q.marks} Marks
                      </span>
                    )}
                  </div>
                  
                  <div className="text-base text-foreground leading-relaxed mb-6 font-medium">
                    <MathText content={q.original_text} />
                  </div>
                  
                  <div className="flex flex-wrap gap-4 pt-4 border-t border-border/50 text-[11px] text-muted-foreground font-mono">
                    {q.year && <span>Year: {q.year}</span>}
                    {q.source_document_title && <span>Paper: {q.source_document_title}</span>}
                    {q.repetition_type && <span>Type: {q.repetition_type}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
