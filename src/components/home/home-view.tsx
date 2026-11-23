"use client";

import { useEffect, useState, useMemo, useRef } from "react";
import Link from "next/link";
import { 
  Search, 
  X, 
  ChevronRight, 
  Calculator, 
  FileText, 
  Binary, 
  GraduationCap, 
  Sparkles,
  ArrowRight,
  BookOpen
} from "lucide-react";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { getStudyContext, StudyContext } from "@/lib/study-context";
import { coursesCatalog, CourseCatalogItem } from "@/lib/courses";

export function HomeView() {
  const [studyContext, setStudyContext] = useState<StudyContext | null>(null);
  const [isClient, setIsClient] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [selectedSemester, setSelectedSemester] = useState<string>("ALL");
  const searchContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setIsClient(true);
    setStudyContext(getStudyContext());

    const handleUpdate = () => setStudyContext(getStudyContext());
    window.addEventListener("markmint:study_context_updated", handleUpdate);
    window.addEventListener("markmint:study_context_cleared", handleUpdate);
    return () => {
      window.removeEventListener("markmint:study_context_updated", handleUpdate);
      window.removeEventListener("markmint:study_context_cleared", handleUpdate);
    };
  }, []);

  // Sync initial semester filter from URL query if present
  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const sem = params.get("sem");
    if (sem && ["1", "2", "3", "4", "5", "6", "7", "8"].includes(sem)) {
      setSelectedSemester(sem);
    }
  }, []);

  // Close search dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(e.target as Node)) {
        setIsSearchOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Filter courses for instant search autocomplete
  const searchResults = useMemo(() => {
    if (!searchQuery.trim()) return [];
    const q = searchQuery.toLowerCase().trim();
    return coursesCatalog
      .filter((c) =>
        c.name.toLowerCase().includes(q) ||
        c.code.toLowerCase().includes(q) ||
        (c.canonicalCode && c.canonicalCode.toLowerCase().includes(q))
      )
      .slice(0, 6);
  }, [searchQuery]);

  // Filter courses for semester listing
  const displayedCourses = useMemo(() => {
    if (selectedSemester === "ALL") {
      return coursesCatalog;
    }
    const semNum = parseInt(selectedSemester, 10);
    return coursesCatalog.filter((c) => c.semester === semNum);
  }, [selectedSemester]);

  // Find slug for recent study session course
  const recentCourseSlug = useMemo(() => {
    if (!studyContext?.course_id) return null;
    const found = coursesCatalog.find((c) => c.id === studyContext.course_id);
    return found?.slug || null;
  }, [studyContext]);

  const handleSelectSemester = (sem: string) => {
    setSelectedSemester(sem);
    if (typeof window !== "undefined") {
      const url = new URL(window.location.href);
      if (sem === "ALL") {
        url.searchParams.delete("sem");
      } else {
        url.searchParams.set("sem", sem);
      }
      window.history.replaceState(null, "", url.toString());
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground font-sans selection:bg-primary/10">
      <Navbar />

      <main id="main-content" className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 md:px-10 py-8 sm:py-12 space-y-10 sm:space-y-12">
        
        {/* ========================================================================= */}
        {/* 1. DISCOVERY HERO: Calm Title, Search Bar & Semester Selector              */}
        {/* ========================================================================= */}
        <section className="space-y-6 max-w-3xl">
          <div className="space-y-2">
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-foreground leading-[1.15]">
              Your academic workspace for SRMIST
            </h1>
            <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
              Find verified past examination papers, syllabus units, and empirical topic forecasts across Semesters 1 through 8.
            </p>
          </div>

          {/* Prominent Search Input */}
          <div ref={searchContainerRef} className="relative w-full">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setIsSearchOpen(true);
                }}
                onFocus={() => setIsSearchOpen(true)}
                placeholder="Search by subject name or code (e.g. 21MAB101T, Data Structures, Physics)..."
                className="w-full bg-card border border-border/80 hover:border-primary/50 focus:border-primary rounded-2xl pl-11 pr-10 py-3.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-hidden focus:ring-2 focus:ring-primary/20 shadow-xs transition-all"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => {
                    setSearchQuery("");
                    setIsSearchOpen(false);
                  }}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground p-1"
                  aria-label="Clear search query"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Instant Search Autocomplete Dropdown */}
            {isSearchOpen && searchQuery.trim() && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-card border border-border rounded-2xl shadow-xl z-30 overflow-hidden divide-y divide-border/40 animate-in fade-in-50 duration-150">
                {searchResults.length === 0 ? (
                  <div className="p-4 text-center text-xs text-muted-foreground">
                    No courses matching &ldquo;{searchQuery}&rdquo;
                  </div>
                ) : (
                  searchResults.map((c) => (
                    <Link
                      key={c.id}
                      href={`/courses/${c.slug}`}
                      className="p-3.5 text-xs flex items-center justify-between hover:bg-secondary/60 transition-colors group"
                      onClick={() => setIsSearchOpen(false)}
                    >
                      <div className="space-y-0.5 min-w-0 pr-3">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-mono text-primary font-bold">
                            [{c.canonicalCode || c.code}]
                          </span>
                          <span className="font-semibold text-foreground group-hover:text-primary transition-colors truncate">
                            {c.name}
                          </span>
                        </div>
                        <span className="text-[11px] text-muted-foreground">
                          Semester {c.semester} • {c.credits} Credits • {c.paperCount} Past Papers
                        </span>
                      </div>
                      <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-primary shrink-0 transition-transform group-hover:translate-x-0.5" />
                    </Link>
                  ))
                )}
              </div>
            )}
          </div>

          {/* Continue Learning Pill (If recent course exists) */}
          {isClient && studyContext && studyContext.course_name ? (
            <div className="p-3 rounded-xl bg-secondary/60 border border-border/80 flex items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2 min-w-0">
                <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
                <span className="text-muted-foreground truncate">
                  Recent: <strong className="text-foreground font-semibold">{studyContext.course_name}</strong>
                </span>
              </div>
              <Link
                href={recentCourseSlug ? `/courses/${recentCourseSlug}` : `/mintai?course=${studyContext.course_id}`}
                className="inline-flex items-center gap-1 font-semibold text-primary hover:underline shrink-0"
              >
                <span>Resume Workspace</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          ) : null}
        </section>

        {/* ========================================================================= */}
        {/* 2. SEMESTER SELECTOR & COURSE DIRECTORY                                    */}
        {/* ========================================================================= */}
        <section className="space-y-5">
          {/* Semester Selector Horizontal Strip */}
          <div className="flex items-center justify-between gap-4 border-b border-border/60 pb-3 flex-wrap">
            <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none py-1">
              {["ALL", "1", "2", "3", "4", "5", "6", "7", "8"].map((sem) => {
                const isActive = selectedSemester === sem;
                return (
                  <button
                    key={sem}
                    type="button"
                    onClick={() => handleSelectSemester(sem)}
                    className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all shrink-0 cursor-pointer ${
                      isActive
                        ? "bg-primary text-primary-foreground font-bold shadow-xs"
                        : "bg-secondary/70 hover:bg-secondary text-muted-foreground hover:text-foreground border border-border/60"
                    }`}
                  >
                    {sem === "ALL" ? "All Semesters" : `Semester ${sem}`}
                  </button>
                );
              })}
            </div>

            <span className="text-xs font-mono text-muted-foreground">
              {displayedCourses.length} {displayedCourses.length === 1 ? "Subject" : "Subjects"}
            </span>
          </div>

          {/* Clean Compact Course Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
            {displayedCourses.map((c) => (
              <Link
                key={c.id}
                href={`/courses/${c.slug}`}
                className="group p-4 sm:p-4.5 rounded-2xl bg-card border border-border/80 hover:border-primary/40 hover:shadow-xs transition-all duration-150 flex flex-col justify-between space-y-3 cursor-pointer"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-primary font-bold text-[11px] px-2 py-0.5 rounded-md bg-primary/10">
                      {c.canonicalCode || c.code}
                    </span>
                    <span className="text-[11px] font-medium text-muted-foreground">
                      Sem {c.semester} • {c.credits} Cr
                    </span>
                  </div>

                  <h3 className="font-bold text-foreground text-sm group-hover:text-primary transition-colors line-clamp-2 leading-snug">
                    {c.name}
                  </h3>
                </div>

                <div className="pt-2.5 border-t border-border/50 flex items-center justify-between text-xs text-muted-foreground">
                  <span className="text-[11px]">
                    {c.paperCount > 0 ? `${c.paperCount} Verified Papers` : "Syllabus & Notes"}
                  </span>
                  <span className="inline-flex items-center gap-1 font-semibold text-primary text-[11px] group-hover:translate-x-0.5 transition-transform">
                    <span>Open Workspace</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </section>

        {/* ========================================================================= */}
        {/* 3. RESTRAINED ACADEMIC UTILITIES                                           */}
        {/* ========================================================================= */}
        <section className="pt-6 border-t border-border/60 space-y-4">
          <div className="space-y-1">
            <h2 className="text-lg font-bold tracking-tight text-foreground">
              Academic Utilities &amp; Tools
            </h2>
            <p className="text-xs text-muted-foreground">
              Calculators, document tools, and logic solvers calibrated for SRMIST regulations.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {/* 1. Target Marks Predictor */}
            <Link
              href="/calculator?tab=target"
              className="p-4 rounded-2xl bg-card border border-border/80 hover:border-primary/40 hover:shadow-xs transition-all flex flex-col justify-between space-y-3 group cursor-pointer"
            >
              <div className="space-y-2">
                <div className="w-8 h-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
                  <Calculator className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-foreground group-hover:text-primary transition-colors">
                    Target Marks Predictor
                  </h3>
                  <p className="text-[11px] text-muted-foreground mt-0.5 leading-relaxed line-clamp-2">
                    Calculate exact marks needed in End-Sem to secure O, A+, or A grades.
                  </p>
                </div>
              </div>
              <span className="text-[11px] font-semibold text-primary flex items-center gap-1">
                <span>Calculate Target</span>
                <ChevronRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
              </span>
            </Link>

            {/* 2. Cumulative CGPA Forecaster */}
            <Link
              href="/calculator?tab=cgpa"
              className="p-4 rounded-2xl bg-card border border-border/80 hover:border-primary/40 hover:shadow-xs transition-all flex flex-col justify-between space-y-3 group cursor-pointer"
            >
              <div className="space-y-2">
                <div className="w-8 h-8 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center">
                  <GraduationCap className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-foreground group-hover:text-primary transition-colors">
                    CGPA Forecaster
                  </h3>
                  <p className="text-[11px] text-muted-foreground mt-0.5 leading-relaxed line-clamp-2">
                    Multi-semester credit-weighted GPA simulator and graduation target planner.
                  </p>
                </div>
              </div>
              <span className="text-[11px] font-semibold text-primary flex items-center gap-1">
                <span>Forecast CGPA</span>
                <ChevronRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
              </span>
            </Link>

            {/* 3. MintDocs Wasm PDF Toolkit */}
            <Link
              href="/tools/pdf"
              className="p-4 rounded-2xl bg-card border border-border/80 hover:border-primary/40 hover:shadow-xs transition-all flex flex-col justify-between space-y-3 group cursor-pointer"
            >
              <div className="space-y-2">
                <div className="w-8 h-8 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center">
                  <FileText className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-foreground group-hover:text-primary transition-colors">
                    MintDocs (PDF Tools)
                  </h3>
                  <p className="text-[11px] text-muted-foreground mt-0.5 leading-relaxed line-clamp-2">
                    Merge, split, and convert images to PDF 100% in browser with zero uploads.
                  </p>
                </div>
              </div>
              <span className="text-[11px] font-semibold text-primary flex items-center gap-1">
                <span>Open MintDocs</span>
                <ChevronRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
              </span>
            </Link>

            {/* 4. K-Map Logic Solver */}
            <Link
              href="/calculator?tab=kmap"
              className="p-4 rounded-2xl bg-card border border-border/80 hover:border-primary/40 hover:shadow-xs transition-all flex flex-col justify-between space-y-3 group cursor-pointer"
            >
              <div className="space-y-2">
                <div className="w-8 h-8 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400 flex items-center justify-center">
                  <Binary className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-foreground group-hover:text-primary transition-colors">
                    K-Map Logic Solver
                  </h3>
                  <p className="text-[11px] text-muted-foreground mt-0.5 leading-relaxed line-clamp-2">
                    Interactive 2, 3, and 4-variable Gray-code boolean logic minimization.
                  </p>
                </div>
              </div>
              <span className="text-[11px] font-semibold text-primary flex items-center gap-1">
                <span>Solve K-Map</span>
                <ChevronRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
              </span>
            </Link>
          </div>
        </section>

      </main>

      <Footer />
    </div>
  );
}
