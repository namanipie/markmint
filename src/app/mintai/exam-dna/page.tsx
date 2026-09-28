"use client";

import React, { useState, useMemo, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { ExamDNAView } from "@/components/analytics/exam-dna-view";
import { coursesCatalog, CourseCatalogItem } from "@/lib/courses";
import { Dna, ChevronRight, BookOpen, Filter, ArrowLeft, Sparkles } from "lucide-react";
import { getStudyContext, updateStudyContext } from "@/lib/study-context";

function ExamDNAContent() {
  const searchParams = useSearchParams();
  const paramCourse = searchParams.get("course") || searchParams.get("course_id");
  const paramCycle = searchParams.get("cycle") || searchParams.get("assessment_cycle");

  // Only show courses with papers in the corpus by default
  const eligibleCourses = useMemo(() => {
    return coursesCatalog.filter((c) => c.paperCount > 0);
  }, []);

  const [selectedCourseId, setSelectedCourseId] = useState<number>(() => {
    if (paramCourse) {
      const match = eligibleCourses.find(
        (c) =>
          String(c.id) === paramCourse ||
          c.code.toLowerCase() === paramCourse.toLowerCase() ||
          c.slug.toLowerCase() === paramCourse.toLowerCase() ||
          c.canonicalCode.toLowerCase() === paramCourse.toLowerCase()
      );
      if (match) return match.id;
    }
    const context = getStudyContext();
    if (context?.course_id) {
      const match = eligibleCourses.find((c) => c.id === context.course_id);
      if (match) return match.id;
    }
    return eligibleCourses[0]?.id || 1;
  });

  const [selectedCycle, setSelectedCycle] = useState<string>(() => {
    if (paramCycle && ["ALL", "ENDSEM", "CT1", "CT2"].includes(paramCycle.toUpperCase())) {
      return paramCycle.toUpperCase();
    }
    const context = getStudyContext();
    if (context?.assessment_cycle && ["ALL", "ENDSEM", "CT1", "CT2"].includes(context.assessment_cycle)) {
      return context.assessment_cycle;
    }
    return "ALL";
  });

  const [selectedTrack, setSelectedTrack] = useState<string>("");
  const [cycleCounts, setCycleCounts] = useState<Record<string, number>>({});

  const currentCourse: CourseCatalogItem | undefined = useMemo(() => {
    return coursesCatalog.find((c) => c.id === selectedCourseId);
  }, [selectedCourseId]);

  // Sync to StudyContext when course changes
  useEffect(() => {
    if (currentCourse) {
      updateStudyContext({
        course_id: currentCourse.id,
        course_name: currentCourse.name,
        course_code: currentCourse.code,
        assessment_cycle: selectedCycle,
      });
    }
  }, [currentCourse, selectedCycle]);

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground font-sans">
      <Navbar />

      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 md:px-10 py-8 space-y-8">
        {/* Breadcrumb Navigation: Reflects authentic hierarchy */}
        <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-xs text-muted-foreground">
          <Link href="/" className="hover:text-foreground transition-colors">
            Home
          </Link>
          <ChevronRight className="w-3.5 h-3.5" />
          <Link href="/dashboard" className="hover:text-foreground transition-colors">
            Dashboard
          </Link>
          <ChevronRight className="w-3.5 h-3.5" />
          <span className="text-foreground font-medium">Historical Evidence</span>
        </nav>

        {/* Header Banner */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-border/40">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent/10 border border-accent/20 text-xs font-semibold text-accent uppercase tracking-wider">
              <Dna className="w-3.5 h-3.5" />
              Historical Exam DNA
            </div>
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-foreground">
              Historical Exam Evidence
            </h1>
            <p className="text-sm text-muted-foreground leading-relaxed">
              This is the empirical past-paper evidence behind MintAI&apos;s exam forecasts. Explore verified assessment blueprints, cognitive demand signals, syllabus unit weightings, and formulation lineage across verified historical papers.
            </p>
          </div>

          {/* Quick Switcher: Back to Forecast */}
          <div className="flex items-center gap-3">
            <Link
              href={`/mintai?course_id=${selectedCourseId}${selectedCycle !== "ALL" ? `&cycle=${selectedCycle}` : ""}`}
              className="px-4 py-2.5 rounded-xl bg-foreground text-background text-xs font-semibold hover:bg-foreground/90 transition-all flex items-center gap-2 shadow-xs group"
            >
              <Sparkles className="w-3.5 h-3.5 text-accent group-hover:rotate-12 transition-transform" />
              <span>View MintAI Forecast for this Course &rarr;</span>
            </Link>
          </div>
        </div>

        {/* Controls Bar: Course & Filter Selection */}
        <div className="bg-card border border-border rounded-xl p-4 shadow-sm flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-accent" />
              <label htmlFor="course-select" className="text-xs font-semibold text-foreground whitespace-nowrap">
                Course:
              </label>
              <select
                id="course-select"
                value={selectedCourseId}
                onChange={(e) => {
                  const newId = Number(e.target.value);
                  setSelectedCourseId(newId);
                  setSelectedTrack("");
                  setCycleCounts({});
                }}
                className="bg-background border border-border rounded-lg px-3 py-1.5 text-xs font-medium focus:ring-2 focus:ring-accent focus:outline-none min-w-[240px]"
              >
                {eligibleCourses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.canonicalCode ? `[${c.canonicalCode}] ` : ""}{c.name} ({c.paperCount} exams)
                  </option>
                ))}
              </select>
            </div>

            {/* Track Selector for multi-track courses */}
            {currentCourse?.hasTracks && currentCourse.tracks.length > 0 && (
              <div className="flex items-center gap-2">
                <label htmlFor="track-select" className="text-xs font-semibold text-foreground whitespace-nowrap">
                  Track:
                </label>
                <select
                  id="track-select"
                  value={selectedTrack}
                  onChange={(e) => {
                    setSelectedTrack(e.target.value);
                    setCycleCounts({});
                  }}
                  className="bg-background border border-border rounded-lg px-3 py-1.5 text-xs font-medium focus:ring-2 focus:ring-accent focus:outline-none"
                >
                  <option value="">All Tracks</option>
                  {currentCourse.tracks.map((t) => (
                    <option key={t.trackKey} value={t.trackKey}>
                      {t.trackName}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* Assessment Cycle Filter with Dynamic Paper Counts */}
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-muted-foreground" />
            <span className="text-xs font-semibold text-foreground">Cycle:</span>
            <div className="flex flex-wrap items-center gap-1 rounded-lg border border-border p-1 bg-muted/20 text-xs">
              {[
                { id: "ALL", label: "All" },
                { id: "ENDSEM", label: "End Semester" },
                { id: "CT1", label: "CT1" },
                { id: "CT2", label: "CT2" },
              ].map(({ id, label }) => {
                const count = cycleCounts[id];
                const isZero = count === 0;
                const isSelected = selectedCycle === id;
                return (
                  <button
                    key={id}
                    onClick={() => setSelectedCycle(id)}
                    className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                      isSelected
                        ? "bg-accent text-accent-foreground font-semibold shadow-sm"
                        : isZero
                        ? "opacity-50 hover:opacity-80 text-muted-foreground border border-dashed border-border/80"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    <span>{label}</span>
                    {count !== undefined && (
                      <span className={`ml-1.5 text-[11px] font-semibold ${isSelected ? "text-accent-foreground/90" : isZero ? "text-muted-foreground" : "text-accent"}`}>
                        ({count})
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Render Live Exam DNA */}
        {currentCourse ? (
          <ExamDNAView
            courseId={currentCourse.id}
            courseName={currentCourse.name}
            canonicalCode={currentCourse.canonicalCode}
            language={selectedTrack || undefined}
            assessmentCycle={selectedCycle}
            onCycleSelect={(cycle) => setSelectedCycle(cycle)}
            onDnaLoaded={(loadedDna) => {
              if (loadedDna?.sample_size?.cycle_paper_counts) {
                setCycleCounts(loadedDna.sample_size.cycle_paper_counts);
              }
            }}
          />
        ) : (
          <div className="p-8 text-center bg-card border border-border rounded-xl">
            <p className="text-sm text-muted-foreground">Please select an engineering course to inspect its Exam DNA.</p>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}

export default function ExamDNAPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-xs text-muted-foreground flex items-center gap-2">
          <Dna className="w-4 h-4 text-accent animate-spin" />
          <span>Loading Exam DNA...</span>
        </div>
      </div>
    }>
      <ExamDNAContent />
    </Suspense>
  );
}
