"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { ExamDNAView } from "@/components/analytics/exam-dna-view";
import { coursesCatalog, CourseCatalogItem } from "@/lib/courses";
import { Dna, ChevronRight, BookOpen, Filter, Sparkles, Layers } from "lucide-react";

export default function ExamDNAPage() {
  // Only show courses with papers in the corpus by default
  const eligibleCourses = useMemo(() => {
    return coursesCatalog.filter((c) => c.paperCount > 0);
  }, []);

  const [selectedCourseId, setSelectedCourseId] = useState<number>(() => {
    return eligibleCourses[0]?.id || 1;
  });

  const [selectedCycle, setSelectedCycle] = useState<string>("ALL");
  const [selectedTrack, setSelectedTrack] = useState<string>("");

  const currentCourse: CourseCatalogItem | undefined = useMemo(() => {
    return coursesCatalog.find((c) => c.id === selectedCourseId);
  }, [selectedCourseId]);

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground font-sans">
      <Navbar />

      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 md:px-10 py-8 space-y-8">
        {/* Breadcrumb Navigation */}
        <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-xs text-muted-foreground">
          <Link href="/" className="hover:text-foreground transition-colors">
            Home
          </Link>
          <ChevronRight className="w-3.5 h-3.5" />
          <Link href="/courses" className="hover:text-foreground transition-colors">
            Courses
          </Link>
          <ChevronRight className="w-3.5 h-3.5" />
          <span className="text-foreground font-medium">Exam DNA</span>
        </nav>

        {/* Header Banner */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-border/40">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent/10 border border-accent/20 text-xs font-semibold text-accent uppercase tracking-wider">
              <Dna className="w-3.5 h-3.5" />
              Evidence-Based Historical Analytics
            </div>
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-foreground">
              Exam DNA Fingerprint
            </h1>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Explore how university semester exams historically formulate questions. Deep dive into marks distribution, syllabus unit weightings, question types, and recurring formulation stems.
            </p>
          </div>

          {/* Quick Stats */}
          <div className="flex items-center gap-3">
            <div className="px-4 py-2.5 rounded-xl bg-card border border-border text-right shadow-sm">
              <div className="text-xs text-muted-foreground">Cataloged Courses</div>
              <div className="text-lg font-bold text-foreground">{eligibleCourses.length} with PYQs</div>
            </div>
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
                  onChange={(e) => setSelectedTrack(e.target.value)}
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

          {/* Assessment Cycle Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-muted-foreground" />
            <span className="text-xs font-medium text-muted-foreground">Cycle:</span>
            <div className="inline-flex rounded-lg border border-border p-0.5 bg-muted/30 text-xs">
              {(["ALL", "ENDSEM", "CT1", "CT2"] as const).map((cycle) => (
                <button
                  key={cycle}
                  onClick={() => setSelectedCycle(cycle)}
                  className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                    selectedCycle === cycle
                      ? "bg-accent text-accent-foreground font-semibold shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {cycle}
                </button>
              ))}
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
