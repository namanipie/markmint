"use client";

import { useEffect, useState, useMemo, useRef } from "react";
import Link from "next/link";
import { 
  Leaf, 
  ChevronRight, 
  BookOpen, 
  Clock, 
  CheckCircle2, 
  ArrowRight, 
  Target, 
  Search, 
  Sparkles,
  Dna,
  X
} from "lucide-react";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { getStudyContext, StudyContext } from "@/lib/study-context";
import { MagneticButton } from "@/components/ui/magnetic-button";
import { coursesCatalog, CourseCatalogItem } from "@/lib/courses";

export function HomeView() {
  const [studyContext, setStudyContext] = useState<StudyContext | null>(null);
  const [isClient, setIsClient] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearchOpen, setIsSearchOpen] = useState(false);
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

  // Filter courses for instant search
  const searchResults = useMemo(() => {
    if (!searchQuery.trim()) return [];
    const q = searchQuery.toLowerCase().trim();
    return coursesCatalog
      .filter((c) =>
        c.name.toLowerCase().includes(q) ||
        c.code.toLowerCase().includes(q) ||
        (c.canonicalCode && c.canonicalCode.toLowerCase().includes(q))
      )
      .slice(0, 5);
  }, [searchQuery]);

  // Featured engineering subjects from official verified catalog
  const featuredCourses = useMemo(() => {
    return coursesCatalog.filter((c) => c.paperCount > 0).slice(0, 6);
  }, []);

  // Compute completed tasks summary if available
  const completedCount = studyContext?.task_statuses
    ? Object.values(studyContext.task_statuses).filter((s) => s === "COMPLETED").length
    : 0;

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground selection:bg-accent/20 font-sans">
      <Navbar />
      
      <main id="main-content" className="flex-1 flex flex-col items-start justify-start w-full px-6 md:px-10 pt-4 pb-16">
        
        {/* --- HERO SECTION --- */}
        <section className="relative z-10 w-full pt-8 pb-10 flex flex-col md:flex-row items-center justify-between gap-12">
          
          {/* Left: Text Content */}
          <div className="w-full md:w-3/5 flex flex-col items-start">
            <p className="text-xs font-semibold tracking-[0.2em] uppercase text-muted-foreground mb-6 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-accent animate-pulse"></span>
              MarkMint v2.0 • SRMIST Semesters 1–8 Academic Intelligence
            </p>
            
            <h1 className="text-5xl md:text-[64px] font-bold tracking-tight text-foreground leading-[1.1] mb-6">
              Predict your exams with <br/>
              <span className="text-accent italic font-serif">historical evidence.</span>
            </h1>
            
            <p className="text-base sm:text-lg text-muted-foreground max-w-xl leading-relaxed mb-8">
              MintAI analyzes verified previous year papers, recurring question families, section blueprints, and syllabus weighting to forecast high-yield exam topics for engineering students at SRMIST.
            </p>

            {/* Instant Course Search Box */}
            <div ref={searchContainerRef} className="relative w-full max-w-lg mb-8">
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setIsSearchOpen(true);
                  }}
                  onFocus={() => setIsSearchOpen(true)}
                  placeholder="Instant search your course (e.g. Data Structures, 18CSC201J, Physics)..."
                  className="w-full bg-card border border-border/80 hover:border-accent/40 rounded-xl pl-10 pr-10 py-3 text-sm placeholder:text-muted-foreground text-foreground focus:ring-2 focus:ring-accent/30 focus:outline-none transition-all shadow-xs"
                />
                {searchQuery && (
                  <button
                    type="button"
                    onClick={() => {
                      setSearchQuery("");
                      setIsSearchOpen(false);
                    }}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground p-1"
                    aria-label="Clear search"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>

              {/* Instant Search Dropdown */}
              {isSearchOpen && searchQuery.trim() && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-card border border-border rounded-xl shadow-xl z-30 overflow-hidden divide-y divide-border/40 animate-in fade-in-50 zoom-in-95">
                  {searchResults.length === 0 ? (
                    <div className="p-4 text-center text-xs text-muted-foreground">
                      No engineering subjects matching &ldquo;{searchQuery}&rdquo;
                    </div>
                  ) : (
                    searchResults.map((c) => (
                      <Link
                        key={c.id}
                        href={`/dashboard?course_id=${c.id}#forecast`}
                        className="p-3 text-xs flex items-center justify-between hover:bg-muted/40 transition-colors group"
                        onClick={() => setIsSearchOpen(false)}
                      >
                        <div className="space-y-0.5">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-accent font-semibold">[{c.canonicalCode || c.code}]</span>
                            <span className="font-medium text-foreground group-hover:text-accent transition-colors">{c.name}</span>
                          </div>
                          <span className="text-[11px] text-muted-foreground">Semester {c.semester}</span>
                        </div>
                        <div className="flex items-center gap-2 text-muted-foreground group-hover:text-accent shrink-0">
                          <span className="text-[11px] font-mono">{c.paperCount} exams</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </div>
                      </Link>
                    ))
                  )}
                </div>
              )}
            </div>
            
            {/* Streamlined Primary Action Buttons */}
            <div className="flex flex-col sm:flex-row items-center gap-3.5 w-full sm:w-auto">
              <MagneticButton className="relative group w-full sm:w-auto" intensity={0.15}>
                <div className="absolute -inset-1 bg-gradient-to-r from-emerald-500 via-emerald-400 to-emerald-600 rounded-lg blur-lg opacity-25 group-hover:opacity-60 transition duration-1000 group-hover:duration-200 animate-pulse"></div>
                
                <Link 
                  href="/dashboard"
                  className="relative flex items-center justify-center gap-2.5 w-full sm:w-auto px-7 py-3.5 bg-foreground text-background rounded-xl hover:bg-foreground/90 transition-all active:scale-[0.98] font-semibold text-sm shadow-sm"
                >
                  <Sparkles className="w-4 h-4 text-accent" />
                  <span>Open MintAI Intelligence</span>
                </Link>
              </MagneticButton>

              <Link 
                href="/courses"
                className="flex items-center justify-center gap-2 w-full sm:w-auto px-6 py-3.5 bg-secondary text-secondary-foreground hover:bg-secondary/80 rounded-xl transition-all active:scale-[0.98] font-medium text-sm border border-border/60"
              >
                <BookOpen className="w-4 h-4 text-muted-foreground" />
                <span>Browse 43 Courses</span>
              </Link>
            </div>
          </div>

          {/* Right: Botanical Mint Graphic */}
          <div className="w-full md:w-2/5 flex justify-center md:justify-end items-center relative hidden sm:flex pointer-events-none">
            <div className="relative flex items-center justify-center w-full max-w-[360px] aspect-square">
              <div className="absolute inset-0 bg-accent/5 rounded-full blur-3xl opacity-50" />
              <Leaf 
                className="w-40 h-40 md:w-56 md:h-56 text-accent/60 -rotate-12 transition-transform duration-700" 
                strokeWidth={0.5} 
              />
              <Leaf 
                className="absolute top-[25%] right-[20%] w-20 h-20 md:w-28 md:h-28 text-accent/30 rotate-[45deg]" 
                strokeWidth={1} 
              />
            </div>
          </div>
        </section>

        {/* --- RECENT STUDY SESSION --- */}
        {isClient && studyContext && studyContext.course_id ? (
          <section className="w-full max-w-2xl mt-1 mb-8 p-5 rounded-2xl bg-card border border-border/80 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
                <h2 className="text-xs font-semibold tracking-wider uppercase text-muted-foreground">
                  Recent Course
                </h2>
              </div>
              {studyContext.assessment_cycle && studyContext.assessment_cycle !== "ALL" && (
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-accent/15 text-accent border border-accent/20">
                  Target: {studyContext.assessment_cycle}
                </span>
              )}
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-1">
              <div className="space-y-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="font-bold text-foreground text-base truncate">
                    {studyContext.course_name}
                  </h3>
                  {studyContext.course_code && (
                    <span className="text-xs font-mono text-muted-foreground">
                      ({studyContext.course_code})
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2 text-xs text-muted-foreground flex-wrap">
                  {studyContext.last_topic_name ? (
                    <span className="flex items-center gap-1.5 text-foreground truncate">
                      <Target className="w-3.5 h-3.5 text-accent shrink-0" />
                      <span>Last viewed: <strong className="font-medium text-accent">{studyContext.last_topic_name}</strong></span>
                    </span>
                  ) : (
                    <span className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5" />
                      <span>Active preparation session</span>
                    </span>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <Link
                  href={`/dashboard?course_id=${studyContext.course_id}${studyContext.assessment_cycle ? `&cycle=${encodeURIComponent(studyContext.assessment_cycle)}` : ""}#forecast`}
                  className="px-4 py-2 bg-foreground text-background font-semibold rounded-lg hover:bg-foreground/90 transition-all text-xs flex items-center gap-1.5 active:scale-95 shadow-xs"
                >
                  <Sparkles className="w-3.5 h-3.5 text-accent" />
                  <span>View Forecast</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
                <Link
                  href={`/mintai/exam-dna?course=${studyContext.course_id}${studyContext.assessment_cycle ? `&cycle=${encodeURIComponent(studyContext.assessment_cycle)}` : ""}`}
                  className="px-3.5 py-2 bg-secondary text-secondary-foreground hover:bg-secondary/80 font-medium rounded-lg transition-all text-xs border border-border/60 flex items-center gap-1.5"
                >
                  <Dna className="w-3.5 h-3.5 text-accent" />
                  <span>Exam DNA</span>
                </Link>
              </div>
            </div>
          </section>
        ) : null}

        {/* --- FEATURED ENGINEERING COURSES --- */}
        <section className="w-full pt-8 pb-4 border-t border-border/40 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div className="space-y-1">
              <p className="text-xs font-semibold tracking-wider uppercase text-muted-foreground">
                Authoritative Curriculum &amp; Past Exams
              </p>
              <h2 className="text-2xl font-bold tracking-tight text-foreground">
                Explore Engineering Courses &amp; Exam Intelligence
              </h2>
            </div>
            <Link
              href="/courses"
              className="inline-flex items-center gap-1.5 text-sm font-semibold text-accent hover:underline"
            >
              <span>View all 43 courses</span>
              <ChevronRight className="w-4 h-4" />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {featuredCourses.map((c) => (
              <div
                key={c.id}
                className="group p-5 rounded-2xl bg-card border border-border/60 hover:border-accent/40 transition-all duration-150 flex flex-col justify-between shadow-xs"
              >
                <div>
                  <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
                    <span className="font-mono text-accent font-semibold">[{c.canonicalCode || c.code}]</span>
                    <span className="px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground text-[10px] font-medium">
                      Sem {c.semester}
                    </span>
                  </div>
                  <h3 className="font-bold text-foreground text-sm group-hover:text-accent transition-colors line-clamp-1">
                    {c.name}
                  </h3>
                  <p className="text-xs text-muted-foreground line-clamp-2 mt-1.5">
                    {c.description}
                  </p>
                </div>

                <div className="pt-4 mt-4 border-t border-border/40 flex items-center justify-between text-xs">
                  <span className="text-muted-foreground font-mono text-[11px]">
                    {c.paperCount} Papers • {c.questionCount} Questions
                  </span>
                  <div className="flex items-center gap-2">
                    <Link
                      href={`/dashboard?course_id=${c.id}#forecast`}
                      className="px-2.5 py-1 rounded-lg bg-accent/10 hover:bg-accent/20 text-accent font-semibold text-xs border border-accent/20 transition-all flex items-center gap-1"
                    >
                      <Sparkles className="w-3 h-3" />
                      <span>Forecast</span>
                    </Link>
                    <Link
                      href={`/courses/${c.slug}`}
                      className="p-1 text-muted-foreground hover:text-foreground transition-colors"
                      title="View syllabus & details"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

      </main>

      <Footer />
    </div>
  );
}
