"use client";

import React, { useState, useEffect, useMemo, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Dna, ArrowLeft, Loader2, ChevronRight } from "lucide-react";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { ExamDNAView } from "@/components/analytics/exam-dna-view";
import { coursesCatalog, CourseCatalogItem } from "@/lib/courses";
import { getStudyContext } from "@/lib/study-context";

function ExamDNAContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [selectedCycle, setSelectedCycle] = useState<string>("ENDSEM");

  // Resolve course from URL param or recent study context
  const courseParam = searchParams.get("course") || searchParams.get("course_id");
  const cycleParam = searchParams.get("cycle") || searchParams.get("assessment_cycle");

  useEffect(() => {
    if (cycleParam && ["ALL", "ENDSEM", "CT1", "CT2"].includes(cycleParam.toUpperCase())) {
      setSelectedCycle(cycleParam.toUpperCase());
    }
  }, [cycleParam]);

  const currentCourse: CourseCatalogItem = useMemo(() => {
    if (courseParam) {
      const match = coursesCatalog.find(
        (c) =>
          String(c.id) === courseParam ||
          c.code.toLowerCase() === courseParam.toLowerCase() ||
          c.canonicalCode.toLowerCase() === courseParam.toLowerCase() ||
          c.slug.toLowerCase() === courseParam.toLowerCase()
      );
      if (match) return match;
    }

    const ctx = getStudyContext();
    if (ctx?.course_id) {
      const matchCtx = coursesCatalog.find((c) => c.id === ctx.course_id);
      if (matchCtx) return matchCtx;
    }

    // Default to first catalog item
    return coursesCatalog[0];
  }, [courseParam]);

  const handleCycleChange = (cycle: string) => {
    setSelectedCycle(cycle);
    if (typeof window !== "undefined") {
      const url = new URL(window.location.href);
      url.searchParams.set("cycle", cycle);
      window.history.replaceState(null, "", url.toString());
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground font-sans">
      <Navbar />

      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 md:px-10 py-6 sm:py-8 space-y-6">
        {/* Top Breadcrumb & Return to Course Workspace */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border/60">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Link href="/" className="hover:text-foreground transition-colors">
                Home
              </Link>
              <ChevronRight className="w-3 h-3" />
              <Link href={`/courses/${currentCourse.slug}`} className="hover:text-foreground transition-colors">
                {currentCourse.name}
              </Link>
              <ChevronRight className="w-3 h-3" />
              <span className="text-foreground font-semibold">Exam DNA Radar</span>
            </div>

            <div className="flex items-center gap-2 pt-1">
              <div className="w-8 h-8 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
                <Dna className="w-4 h-4" />
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                  Exam DNA Analytics: {currentCourse.name}
                </h1>
                <p className="text-xs text-muted-foreground font-mono">
                  [{currentCourse.canonicalCode || currentCourse.code}] • Semester {currentCourse.semester} • {currentCourse.paperCount} Verified Papers
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-center">
            <Link
              href={`/courses/${currentCourse.slug}`}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-secondary text-secondary-foreground hover:bg-secondary/80 text-xs font-semibold border border-border/60 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Course Workspace</span>
            </Link>
          </div>
        </div>

        {/* Full Exam DNA Analytical View */}
        <ExamDNAView
          courseId={currentCourse.id}
          courseName={currentCourse.name}
          canonicalCode={currentCourse.canonicalCode || currentCourse.code}
          assessmentCycle={selectedCycle}
          onCycleSelect={handleCycleChange}
        />
      </main>

      <Footer />
    </div>
  );
}

export default function ExamDNAPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
          <div className="flex items-center gap-3 text-primary">
            <Loader2 className="w-6 h-6 animate-spin" />
            <span className="text-sm font-medium text-muted-foreground">
              Loading Exam DNA Radar...
            </span>
          </div>
        </div>
      }
    >
      <ExamDNAContent />
    </Suspense>
  );
}
