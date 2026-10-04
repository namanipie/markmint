"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { MathText } from "@/components/ui/math-text";
import { getCurriculumBranches, getCurriculumSubjects } from "@/lib/api";
import { CurriculumSubject } from "@/lib/types";
import { coursesCatalog } from "@/lib/courses";
import { 
  ChevronRight, 
  BookOpen, 
  Layers, 
  FileQuestion, 
  ChevronDown,
  Target,
  Loader2,
  ListChecks,
  Database
} from "lucide-react";

import { MintAIQuestionGenerator } from "@/components/ui/mint-ai-question-generator";

export default function QuestionBankPage() {
  const [branches, setBranches] = useState<string[]>([]);
  const [selectedBranch, setSelectedBranch] = useState<string>("Computer Science and Engineering");
  const [selectedSemester, setSelectedSemester] = useState<number>(1);
  const [semesterSubjects, setSemesterSubjects] = useState<CurriculumSubject[]>([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState<number | string | null>(null);
  
  const [expandedUnit, setExpandedUnit] = useState<number | null>(null);
  const [expandedTopic, setExpandedTopic] = useState<string | null>(null);

  // Load branches
  useEffect(() => {
    getCurriculumBranches().then(data => {
      if (data && data.length > 0) {
        setBranches(data);
      }
    });
  }, []);

  // Load subjects when branch/semester changes
  useEffect(() => {
    if (selectedBranch && selectedSemester) {
      getCurriculumSubjects(selectedBranch, selectedSemester).then(subjects => {
        setSemesterSubjects(subjects || []);
        setSelectedSubjectId(null);
      });
    }
  }, [selectedBranch, selectedSemester]);

  const activeSubject = useMemo(() => {
    if (!selectedSubjectId) return null;
    const verifiedCourse = coursesCatalog.find(c => String(c.id) === String(selectedSubjectId));
    const currSub = semesterSubjects.find(s => String(s.curriculum_id) === String(selectedSubjectId) || String(s.course_id) === String(selectedSubjectId));
    
    if (verifiedCourse) return { ...verifiedCourse, courseId: verifiedCourse.id, isUnverified: false };
    
    if (currSub) {
      return {
        id: currSub.curriculum_id,
        courseId: currSub.course_id || undefined,
        name: currSub.subject_name,
        canonicalCode: currSub.canonical_code,
        units: [],
        questionCount: currSub.question_count || 0,
        isUnverified: true
      };
    }
    return null;
  }, [selectedSubjectId, semesterSubjects]);

  const handleSubjectClick = (id: number | string) => {
    setSelectedSubjectId(id);
    setExpandedUnit(null);
    setExpandedTopic(null);
  };

  const handleTopicClick = (topic: string) => {
    if (expandedTopic === topic) {
      setExpandedTopic(null);
      return;
    }
    setExpandedTopic(topic);
  };

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground font-sans">
      <Navbar />

      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 md:px-10 py-6 md:py-8 space-y-8">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-accent/10 border border-accent/20 text-[11px] font-semibold text-accent uppercase tracking-wider mb-2">
            <Database className="w-3.5 h-3.5" />
            Universal Question Bank
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            Topic-Wise Question Bank
          </h1>
          <p className="text-sm text-muted-foreground max-w-2xl">
            Select your semester and subject to drill down into unit-wise topics. MintAI will instantly organize and generate 1-mark MCQs, 4-mark, 8-mark, and 13-mark questions for any topic.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 items-start">
          
          {/* Left Sidebar: Selectors */}
          <div className="lg:col-span-1 space-y-6 sticky top-24">
            
            {/* Branch Selection */}
            <div className="space-y-3">
              <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                1. Select Program
              </label>
              <select
                value={selectedBranch}
                onChange={(e) => {
                  setSelectedBranch(e.target.value);
                  setSelectedSubjectId(null);
                }}
                className="w-full bg-background border border-border rounded-lg px-3 py-2.5 text-sm font-medium text-foreground focus:ring-1 focus:ring-accent focus:outline-none shadow-sm"
              >
                {branches.length === 0 && <option value={selectedBranch}>{selectedBranch}</option>}
                {branches.map((b) => (
                  <option key={b} value={b}>
                    {b}
                  </option>
                ))}
              </select>
            </div>

            {/* Semester Selection */}
            <div className="space-y-3">
              <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                2. Select Semester
              </label>
              <div className="grid grid-cols-2 gap-2">
                {[1, 2, 3, 4, 5, 6, 7, 8].map(sem => (
                  <button
                    key={sem}
                    onClick={() => {
                      setSelectedSemester(sem);
                      setSelectedSubjectId(null);
                    }}
                    className={`py-2 px-3 rounded-lg text-sm font-medium transition-all border ${
                      selectedSemester === sem 
                        ? "bg-accent/15 border-accent text-accent shadow-sm"
                        : "bg-background border-border hover:bg-muted/30 hover:border-border/80 text-muted-foreground"
                    }`}
                  >
                    Semester {sem}
                  </button>
                ))}
              </div>
            </div>

            {/* Subject Selection */}
            <div className="space-y-3">
              <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                3. Select Subject
              </label>
              {semesterSubjects.length === 0 ? (
                <div className="p-4 text-center rounded-lg border border-dashed border-border text-xs text-muted-foreground">
                  No verified subjects found for Semester {selectedSemester} yet.
                </div>
              ) : (
                <div className="space-y-2">
                  {semesterSubjects.map(sub => {
                    const subId = sub.course_id || sub.curriculum_id;
                    return (
                      <button
                        key={subId}
                        onClick={() => handleSubjectClick(subId)}
                        className={`w-full text-left py-2.5 px-3 rounded-lg text-xs transition-all border flex items-center justify-between group ${
                          selectedSubjectId === subId 
                            ? "bg-primary/10 border-primary text-foreground shadow-sm font-semibold"
                            : "bg-background border-border hover:bg-muted/30 text-muted-foreground hover:text-foreground"
                        }`}
                      >
                        <span className="line-clamp-1 pr-2">{sub.subject_name}</span>
                        <ChevronRight className={`w-3.5 h-3.5 flex-shrink-0 ${selectedSubjectId === subId ? 'text-primary' : 'opacity-0 group-hover:opacity-100'}`} />
                      </button>
                    )
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Right Panel: Content Explorer */}
          <div className="lg:col-span-3">
            {!activeSubject ? (
              <div className="h-full min-h-[400px] flex flex-col items-center justify-center border border-dashed border-border rounded-2xl bg-muted/5 text-muted-foreground space-y-4">
                <Layers className="w-10 h-10 opacity-20" />
                <p className="text-sm font-medium">Select a subject from the sidebar to explore units.</p>
              </div>
            ) : (
              <div className="space-y-6">
                
                {/* Subject Header */}
                <div className="p-5 rounded-xl border border-border bg-card shadow-sm flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <BookOpen className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-foreground">
                      {activeSubject.canonicalCode ? `[${activeSubject.canonicalCode}] ` : ""}{activeSubject.name}
                    </h2>
                    <p className="text-xs text-muted-foreground mt-1">
                      {activeSubject.units?.length || 0} Units • {activeSubject.questionCount || 0} Total Questions
                    </p>
                  </div>
                </div>

                {/* Units List */}
                <div className="space-y-3">
                  {!activeSubject.units || activeSubject.units.length === 0 ? (
                    <div className="p-8 text-center border border-dashed border-border rounded-xl bg-card space-y-4">
                      <div className="space-y-1">
                        <p className="text-sm font-semibold text-foreground">Syllabus Taxonomy Pending Formal Verification</p>
                        <p className="text-xs text-muted-foreground max-w-md mx-auto">
                          Detailed unit and topic breakdowns for {activeSubject.name} are currently undergoing syllabus verification against official SRM regulations.
                        </p>
                      </div>
                      <div className="max-w-md mx-auto pt-2">
                        <MintAIQuestionGenerator topicName={activeSubject.name} courseId={activeSubject.courseId} />
                      </div>
                    </div>
                  ) : (
                    activeSubject.units.map(unit => (
                      <div key={unit.number} className="border border-border/80 rounded-xl overflow-hidden bg-background">
                        {/* Unit Header (Click to expand) */}
                        <button
                          onClick={() => setExpandedUnit(expandedUnit === unit.number ? null : unit.number)}
                          className={`w-full flex items-center justify-between p-4 transition-colors ${
                            expandedUnit === unit.number ? "bg-muted/20" : "hover:bg-muted/10"
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <span className="flex items-center justify-center w-7 h-7 rounded-md bg-foreground/5 font-mono text-xs font-bold text-foreground">
                              U{unit.number}
                            </span>
                            <span className="font-semibold text-foreground text-sm sm:text-base text-left">
                              {unit.name}
                            </span>
                          </div>
                          <ChevronDown className={`w-4 h-4 text-muted-foreground transition-transform ${
                            expandedUnit === unit.number ? "rotate-180" : ""
                          }`} />
                        </button>

                        {/* Topics List (Expanded) */}
                        {expandedUnit === unit.number && (
                          <div className="border-t border-border/50 p-4 bg-muted/5 space-y-2">
                            {unit.topics.length === 0 ? (
                              <p className="text-xs text-muted-foreground py-2 text-center">No topics mapped yet.</p>
                            ) : (
                              unit.topics.map((topic, tIdx) => (
                                <div key={tIdx} className="bg-background border border-border rounded-lg overflow-hidden">
                                  
                                  {/* Topic Button */}
                                  <button
                                    onClick={() => handleTopicClick(topic)}
                                    className="w-full flex items-center justify-between p-3 text-sm hover:bg-accent/5 hover:border-accent/30 transition-all text-left"
                                  >
                                    <span className="font-medium flex items-center gap-2">
                                      <Target className="w-3.5 h-3.5 text-accent opacity-70" />
                                      <MathText content={topic} inlineOnly />
                                    </span>
                                    {expandedTopic === topic ? (
                                      <span className="text-[10px] font-bold uppercase tracking-wider text-accent bg-accent/10 px-2 py-0.5 rounded">
                                        Close
                                      </span>
                                    ) : (
                                      <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground bg-muted/20 px-2 py-0.5 rounded group-hover:bg-accent/10 group-hover:text-accent">
                                        View Questions
                                      </span>
                                    )}
                                  </button>

                                  {/* Generated Questions (Expanded) */}
                                  {expandedTopic === topic && (
                                    <div className="border-t border-border/50 p-4">
                                      <MintAIQuestionGenerator topicName={topic} courseId={activeSubject.courseId} />
                                    </div>
                                  )}
                                </div>
                              ))
                            )}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>

              </div>
            )}
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
