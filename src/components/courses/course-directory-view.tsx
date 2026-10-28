"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { CourseCatalogItem } from "@/lib/courses";
import { 
  Search, 
  BookOpen, 
  FileText, 
  HelpCircle, 
  Layers, 
  ChevronRight, 
  Languages, 
  Sparkles,
  X
} from "lucide-react";

interface CourseDirectoryViewProps {
  courses: CourseCatalogItem[];
}

export function CourseDirectoryView({ courses }: CourseDirectoryViewProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSemester, setSelectedSemester] = useState<number | "all">("all");

  const totalPapers = useMemo(() => courses.reduce((acc, c) => acc + c.paperCount, 0), [courses]);
  const totalQuestions = useMemo(() => courses.reduce((acc, c) => acc + c.questionCount, 0), [courses]);

  const filteredCourses = useMemo(() => {
    return courses.filter((c) => {
      // Semester filter
      if (selectedSemester !== "all") {
        if (c.semester !== selectedSemester) {
          return false;
        }
      }

      // Search filter
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase().trim();

      const matchName = c.name.toLowerCase().includes(q);
      const matchCode = c.code.toLowerCase().includes(q);
      const matchCanonical = c.canonicalCode.toLowerCase().includes(q);
      const matchAliases = c.aliases.some((a) => a.toLowerCase().includes(q));
      const matchTopics = c.highYieldTopics.some((t) => t.topic.toLowerCase().includes(q));

      return matchName || matchCode || matchCanonical || matchAliases || matchTopics;
    });
  }, [courses, searchQuery, selectedSemester]);

  return (
    <div className="w-full space-y-8">
      {/* Compact Stat Overview Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-4 rounded-xl bg-card border border-border/60 shadow-2xs space-y-1">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            <BookOpen className="w-3.5 h-3.5 text-accent" />
            <span>Courses</span>
          </div>
          <div className="text-2xl font-bold text-foreground">{courses.length}</div>
          <div className="text-[11px] text-muted-foreground">Engineering Subjects</div>
        </div>

        <div className="p-4 rounded-xl bg-card border border-border/60 shadow-2xs space-y-1">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            <FileText className="w-3.5 h-3.5 text-accent" />
            <span>Verified Papers</span>
          </div>
          <div className="text-2xl font-bold text-foreground">{totalPapers}+</div>
          <div className="text-[11px] text-muted-foreground">SRMIST Past Exams</div>
        </div>

        <div className="p-4 rounded-xl bg-card border border-border/60 shadow-2xs space-y-1">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            <HelpCircle className="w-3.5 h-3.5 text-accent" />
            <span>Exam Questions</span>
          </div>
          <div className="text-2xl font-bold text-foreground">{totalQuestions.toLocaleString()}+</div>
          <div className="text-[11px] text-muted-foreground">Cataloged &amp; Classified</div>
        </div>

        <div className="p-4 rounded-xl bg-card border border-border/60 shadow-2xs space-y-1">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            <Layers className="w-3.5 h-3.5 text-accent" />
            <span>Curriculum</span>
          </div>
          <div className="text-2xl font-bold text-foreground">Sem 1–8</div>
          <div className="text-[11px] text-muted-foreground">Regulation 2021 Scope</div>
        </div>
      </div>

      {/* Direct Search & Tactile Semester Segmented Controls */}
      <div className="space-y-4 p-4 rounded-2xl bg-card border border-border/80 shadow-xs">
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          {/* Search input */}
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Instant search by name or code (e.g. 21MAB101T, 21CSC201J, DSA, Physics)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-9 py-2.5 bg-muted/20 border border-border/60 rounded-xl text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent focus:border-accent transition-all text-foreground"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground p-1"
                aria-label="Clear search"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Tactile Semester Tabs (1-Click Switch for Semesters 1 through 8) */}
          <div className="flex items-center gap-1 p-1 bg-muted/30 rounded-xl border border-border/50 overflow-x-auto max-w-full scrollbar-none shrink-0">
            {[
              { key: "all" as const, label: "All Semesters" },
              { key: 1, label: "Sem 1" },
              { key: 2, label: "Sem 2" },
              { key: 3, label: "Sem 3" },
              { key: 4, label: "Sem 4" },
              { key: 5, label: "Sem 5" },
              { key: 6, label: "Sem 6" },
              { key: 7, label: "Sem 7" },
              { key: 8, label: "Sem 8" },
            ].map((tab) => {
              const isSelected = selectedSemester === tab.key;
              return (
                <button
                  key={String(tab.key)}
                  type="button"
                  onClick={() => setSelectedSemester(tab.key)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                    isSelected
                      ? "bg-accent text-accent-foreground shadow-2xs"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Results Counter & Clear Filter */}
        <div className="flex items-center justify-between text-xs text-muted-foreground pt-1 border-t border-border/40">
          <span>
            Showing <strong className="text-foreground font-semibold">{filteredCourses.length}</strong> of {courses.length} courses
          </span>
          {(searchQuery || selectedSemester !== "all") && (
            <button
              type="button"
              onClick={() => {
                setSearchQuery("");
                setSelectedSemester("all");
              }}
              className="text-accent hover:underline font-semibold cursor-pointer"
            >
              Reset all filters
            </button>
          )}
        </div>
      </div>

      {/* Streamlined Course Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredCourses.map((course) => {
          return (
            <div
              key={course.id}
              className="group flex flex-col justify-between bg-card hover:border-accent/40 border border-border/80 rounded-2xl p-5 transition-all duration-150 hover:shadow-xs shadow-2xs space-y-4"
            >
              <div className="space-y-3">
                {/* Header: Code & Semester */}
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-accent text-xs font-bold px-2 py-0.5 rounded-md bg-accent/10 border border-accent/20">
                    {course.canonicalCode || course.code}
                  </span>
                  <div className="flex items-center gap-1.5 text-xs text-muted-foreground font-mono">
                    <span className="px-2 py-0.5 rounded bg-muted text-muted-foreground font-semibold text-[11px]">
                      Sem {course.semester}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-muted text-muted-foreground text-[11px]">
                      {course.credits} Credits
                    </span>
                  </div>
                </div>

                {/* Course Name */}
                <Link href={`/courses/${course.slug}`}>
                  <h3 className="text-base font-bold tracking-tight text-foreground group-hover:text-accent transition-colors line-clamp-1">
                    {course.name}
                  </h3>
                </Link>

                {/* Brief Description */}
                <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2">
                  {course.description}
                </p>

                {/* Multi-track indicator if foreign languages */}
                {course.hasTracks && (
                  <div className="p-2 rounded-lg bg-accent/5 border border-accent/20 flex items-center gap-2 text-[11px] text-accent font-medium">
                    <Languages className="w-3.5 h-3.5 shrink-0" />
                    <span>6 Isolated Language Tracks (German, French, Spanish, Japanese, Korean, Chinese)</span>
                  </div>
                )}
              </div>

              {/* Card Footer: Evidence Info & Direct MintAI Button */}
              <div className="pt-3 border-t border-border/40 flex items-center justify-between gap-2 text-xs">
                <span className="text-[11px] text-muted-foreground font-mono truncate">
                  <strong className="text-foreground">{course.paperCount}</strong> papers •{" "}
                  <strong className="text-foreground">{course.questionCount}</strong> questions
                </span>

                <div className="flex items-center gap-2 shrink-0">
                  <Link
                    href={`/dashboard?course_id=${course.id}#forecast`}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-accent/10 hover:bg-accent/20 text-accent font-semibold text-xs border border-accent/20 transition-all cursor-pointer"
                  >
                    <Sparkles className="w-3 h-3" />
                    <span>MintAI</span>
                  </Link>

                  <Link
                    href={`/courses/${course.slug}`}
                    className="p-1.5 text-muted-foreground hover:text-foreground transition-colors"
                    title="View syllabus & details"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {filteredCourses.length === 0 && (
        <div className="py-16 text-center space-y-3 bg-muted/10 rounded-2xl border border-dashed border-border/80 p-8">
          <Search className="w-8 h-8 text-muted-foreground mx-auto opacity-50" />
          <h4 className="text-base font-semibold text-foreground">No courses found</h4>
          <p className="text-xs text-muted-foreground max-w-sm mx-auto">
            No engineering subjects match &ldquo;{searchQuery}&rdquo;. Try searching with subject title or course code like 21MAB101T.
          </p>
          <button
            type="button"
            onClick={() => {
              setSearchQuery("");
              setSelectedSemester("all");
            }}
            className="px-4 py-2 bg-secondary hover:bg-secondary/80 text-foreground text-xs font-semibold rounded-lg transition-all cursor-pointer"
          >
            Reset Filters
          </button>
        </div>
      )}
    </div>
  );
}
