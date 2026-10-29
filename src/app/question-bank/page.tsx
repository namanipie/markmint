"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { MathText } from "@/components/ui/math-text";
import { getCurriculumBranches, getCurriculumSubjects, searchIntelligence } from "@/lib/api";
import { CurriculumSubject, SearchResult } from "@/lib/types";
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
  Database,
  Search,
  X,
  Sparkles,
  RotateCcw,
  Award,
  Calendar
} from "lucide-react";

import { MintAIQuestionGenerator } from "@/components/ui/mint-ai-question-generator";
import { TopicQuestionsViewer } from "@/components/ui/topic-questions-viewer";
import { CycleTestArchiveViewer } from "@/components/analytics/cycle-test-archive-viewer";

export default function QuestionBankPage() {
  const [branches, setBranches] = useState<string[]>([]);
  const [selectedBranch, setSelectedBranch] = useState<string>("Computer Science and Engineering");
  const [selectedSemester, setSelectedSemester] = useState<number>(1);
  const [semesterSubjects, setSemesterSubjects] = useState<CurriculumSubject[]>([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState<number | string | null>(null);
  
  const [expandedUnit, setExpandedUnit] = useState<number | null>(null);
  const [expandedTopic, setExpandedTopic] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"SYLLABUS" | "CYCLE_TESTS">("SYLLABUS");
  const [isSidebarOpenMobile, setIsSidebarOpenMobile] = useState<boolean>(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const tab = params.get("tab") || params.get("view");
      if (tab === "cycle-tests" || tab === "cycle_tests" || params.get("cycle")) {
        setActiveTab("CYCLE_TESTS");
      }
    }
  }, []);

  // Search Radar state
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [showSearchResults, setShowSearchResults] = useState<boolean>(false);

  // Handle search with debouncing
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setShowSearchResults(false);
      return;
    }

    const timer = setTimeout(() => {
      setIsSearching(true);
      searchIntelligence({
        raw_query: searchQuery.trim(),
        limit: 12,
      })
        .then((res) => {
          setSearchResults(res || []);
          setShowSearchResults(true);
          setIsSearching(false);
        })
        .catch(() => {
          setIsSearching(false);
        });
    }, 280);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  const quickPills = [
    "Eigenvalues",
    "\\int f(x) dx",
    "Finite Automata",
    "TCP 3-Way Handshake",
    "Deadlock Avoidance",
    "Gantt Chart",
    "Round Robin",
    "Normal Forms BCNF",
  ];

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
    setIsSidebarOpenMobile(false);
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
            Select your semester and subject to drill down into unit-wise topics, or explore 5,536 authentic Cycle Test questions with faculty answer keys and dedicated MCQ sections.
          </p>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 border-b border-border/60 pb-3">
          <button
            type="button"
            onClick={() => setActiveTab("SYLLABUS")}
            className={`flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer touch-manipulation ${
              activeTab === "SYLLABUS"
                ? "bg-primary text-primary-foreground shadow-xs font-bold"
                : "bg-muted/40 hover:bg-muted text-muted-foreground hover:text-foreground"
            }`}
          >
            <BookOpen className="w-4 h-4 shrink-0" />
            <span>Syllabus Taxonomy &amp; Units</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("CYCLE_TESTS")}
            className={`flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer border touch-manipulation ${
              activeTab === "CYCLE_TESTS"
                ? "bg-accent text-accent-foreground border-accent shadow-xs font-bold"
                : "bg-accent/10 hover:bg-accent/20 border-accent/25 text-accent"
            }`}
          >
            <Sparkles className="w-4 h-4 shrink-0" />
            <span>⚡ Cycle Test Archive</span>
            <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold border ${activeTab === "CYCLE_TESTS" ? "bg-black/25 text-white border-white/20" : "bg-accent/20 border-accent/30 text-accent"}`}>
              5,536 Questions &amp; Keys
            </span>
          </button>
        </div>

        {activeTab === "CYCLE_TESTS" ? (
          <CycleTestArchiveViewer
            initialSubject={activeSubject?.name || "ALL"}
          />
        ) : (
          <>
        {/* Search Radar: Universal Question & Formula Search */}
        <div className="p-4 sm:p-5 rounded-2xl border border-border/80 bg-card shadow-xs space-y-3">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Search className="w-4 h-4 text-accent" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">
                Search Radar • 11,498 Authentic Questions
              </h3>
            </div>
            {isSearching && (
              <span className="inline-flex items-center gap-1 text-[11px] text-accent">
                <Loader2 className="w-3 h-3 animate-spin" />
                Searching...
              </span>
            )}
          </div>

          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by keywords, topic, or LaTeX formula (e.g. 'eigenvalues', '\begin{pmatrix}', 'Gantt chart', 'TCP')..."
              className="w-full bg-background border border-border rounded-xl px-4 py-2.5 pl-10 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:ring-1 focus:ring-accent focus:outline-none shadow-xs"
            />
            <Search className="w-4 h-4 text-muted-foreground absolute left-3.5 top-1/2 -translate-y-1/2" />
            {searchQuery && (
              <button
                onClick={() => {
                  setSearchQuery("");
                  setSearchResults([]);
                  setShowSearchResults(false);
                }}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Quick Formula / Topic Pills */}
          <div className="flex flex-wrap items-center gap-1.5 pt-1">
            <span className="text-[11px] font-semibold text-muted-foreground mr-1">Quick:</span>
            {quickPills.map((pill) => (
              <button
                key={pill}
                onClick={() => setSearchQuery(pill)}
                className="text-[11px] px-2.5 py-1 rounded-lg bg-muted/40 hover:bg-accent/10 border border-border/60 hover:border-accent/30 text-muted-foreground hover:text-accent transition-all font-mono"
              >
                {pill}
              </button>
            ))}
          </div>

          {/* Search Results Drawer */}
          {showSearchResults && (
            <div className="mt-4 pt-3 border-t border-border/50 space-y-3">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>Found {searchResults.length} matching questions across the academic corpus:</span>
                <button
                  onClick={() => setShowSearchResults(false)}
                  className="text-xs text-accent hover:underline"
                >
                  Close Results
                </button>
              </div>

              {searchResults.length === 0 ? (
                <p className="text-xs text-muted-foreground py-3 text-center">
                  No questions directly matched &ldquo;{searchQuery}&rdquo;. Try another formula or keyword.
                </p>
              ) : (
                <div className="space-y-2.5 max-h-[420px] overflow-y-auto pr-1">
                  {searchResults.map((res, rIdx) => (
                    <div
                      key={res.id || rIdx}
                      className="p-3.5 rounded-xl border border-border/80 bg-background hover:border-accent/40 transition-all space-y-1.5 shadow-2xs"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-1.5 text-[11px]">
                        <div className="flex items-center gap-2">
                          {res.subject && (
                            <span className="px-2 py-0.5 rounded-md bg-primary/10 text-primary font-semibold text-[10px]">
                              {res.subject}
                            </span>
                          )}
                          {res.topic && (
                            <span className="text-muted-foreground font-medium">
                              • {res.topic}
                            </span>
                          )}
                          {res.year && (
                            <span className="text-muted-foreground">
                              • {res.year}
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-2">
                          {res.metadata?.repetition_type === "exact_repeat" && (
                            <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">
                              <RotateCcw className="w-2.5 h-2.5" />
                              Repeat
                            </span>
                          )}
                          {res.metadata?.marks && (
                            <span className="text-[10px] font-bold text-amber-600 dark:text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded">
                              {res.metadata.marks} Marks
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="text-xs text-foreground/90 leading-relaxed font-sans">
                        <MathText content={res.text_snippet} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 lg:gap-8 items-start">
          
          {/* Mobile Accordion Toggle for Selectors */}
          <div className="lg:hidden col-span-1 p-3.5 rounded-xl border border-border/70 bg-card shadow-2xs space-y-2">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-[10px] uppercase font-bold text-muted-foreground block">Curriculum Filter:</span>
                <span className="text-xs font-bold text-foreground">
                  {selectedBranch.split(" ")[0]} • Sem {selectedSemester} • {activeSubject?.name || "Choose Subject"}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setIsSidebarOpenMobile(!isSidebarOpenMobile)}
                className="px-3 py-1.5 rounded-lg bg-accent/15 border border-accent/25 text-accent text-xs font-bold hover:bg-accent/25 transition-all cursor-pointer touch-manipulation"
              >
                {isSidebarOpenMobile ? "Hide Selectors" : "Change Subject"}
              </button>
            </div>
          </div>

          {/* Left Sidebar: Selectors */}
          <div className={`lg:col-span-1 space-y-6 sticky top-24 ${isSidebarOpenMobile ? 'block' : 'hidden lg:block'}`}>
            
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
                <div className="p-5 rounded-xl border border-border bg-card shadow-sm flex flex-wrap items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
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

                  <button
                    type="button"
                    onClick={() => setActiveTab("CYCLE_TESTS")}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent/10 hover:bg-accent/20 text-accent font-semibold text-xs border border-accent/25 transition-all cursor-pointer"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>View Authentic CT Papers &amp; Solutions &rarr;</span>
                  </button>
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

                                  {/* Authentic & Practice Questions (Expanded) */}
                                  {expandedTopic === topic && (
                                    <div className="border-t border-border/50 p-4">
                                      <TopicQuestionsViewer
                                        topicName={topic}
                                        courseId={activeSubject.courseId}
                                        courseCode={activeSubject.canonicalCode}
                                      />
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
          </>
        )}
      </main>

      <Footer />
    </div>
  );
}
