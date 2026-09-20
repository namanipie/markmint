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
  TrendingUp,
  Filter
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
      if (selectedSemester !== "all" && c.semester !== selectedSemester) {
        return false;
      }

      // Search filter
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase().trim();

      const matchName = c.name.toLowerCase().includes(q);
      const matchCode = c.code.toLowerCase().includes(q);
      const matchCanonical = c.canonicalCode.toLowerCase().includes(q);
      const matchAliases = c.aliases.some((a) => a.toLowerCase().includes(q));
      const matchTopics = c.highYieldTopics.some((t) => t.topic.toLowerCase().includes(q));
      const matchTracks = c.tracks.some((tr) => tr.trackName.toLowerCase().includes(q) || tr.trackCode.toLowerCase().includes(q));

      return matchName || matchCode || matchCanonical || matchAliases || matchTopics || matchTracks;
    });
  }, [courses, searchQuery, selectedSemester]);

  return (
    <div className="w-full space-y-10">
      {/* Top Banner & Stats Overview */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-card border border-border/60 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
            <BookOpen className="w-4 h-4 text-accent" />
            <span>Courses</span>
          </div>
          <div className="text-3xl font-bold text-foreground">{courses.length}</div>
          <div className="text-xs text-muted-foreground mt-1">First-Year B.Tech</div>
        </div>

        <div className="p-5 rounded-2xl bg-card border border-border/60 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
            <FileText className="w-4 h-4 text-accent" />
            <span>Verified Papers</span>
          </div>
          <div className="text-3xl font-bold text-foreground">{totalPapers}+</div>
          <div className="text-xs text-muted-foreground mt-1">SRMIST Past Exams</div>
        </div>

        <div className="p-5 rounded-2xl bg-card border border-border/60 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
            <HelpCircle className="w-4 h-4 text-accent" />
            <span>Exam Questions</span>
          </div>
          <div className="text-3xl font-bold text-foreground">{totalQuestions.toLocaleString()}+</div>
          <div className="text-xs text-muted-foreground mt-1">Indexed & Structured</div>
        </div>

        <div className="p-5 rounded-2xl bg-card border border-border/60 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
            <Languages className="w-4 h-4 text-accent" />
            <span>Multi-Track</span>
          </div>
          <div className="text-3xl font-bold text-foreground">6</div>
          <div className="text-xs text-muted-foreground mt-1">Foreign Language Tracks</div>
        </div>
      </div>

      {/* Filter & Search Controls */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 p-4 rounded-2xl bg-secondary/30 border border-border/60">
        {/* Search input */}
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by course name, code (e.g. 21MAB101T, SPCM, Chemistry)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-background border border-border/60 rounded-xl text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent transition-all"
          />
        </div>

        {/* Semester Filter Tabs */}
        <div className="flex items-center gap-1.5 p-1 bg-background/80 rounded-xl border border-border/50 self-start md:self-auto">
          <button
            onClick={() => setSelectedSemester("all")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              selectedSemester === "all"
                ? "bg-foreground text-background shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            All Semesters ({courses.length})
          </button>
          <button
            onClick={() => setSelectedSemester(1)}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              selectedSemester === 1
                ? "bg-foreground text-background shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Semester 1 ({courses.filter((c) => c.semester === 1).length})
          </button>
          <button
            onClick={() => setSelectedSemester(2)}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              selectedSemester === 2
                ? "bg-foreground text-background shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Semester 2 ({courses.filter((c) => c.semester === 2).length})
          </button>
        </div>
      </div>

      {/* Results Count */}
      <div className="flex items-center justify-between text-xs text-muted-foreground px-1">
        <span>
          Showing <strong className="text-foreground">{filteredCourses.length}</strong> of {courses.length} courses
        </span>
        {searchQuery && (
          <button
            onClick={() => setSearchQuery("")}
            className="text-accent hover:underline font-medium"
          >
            Clear search
          </button>
        )}
      </div>

      {/* Course Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredCourses.map((course) => {
          return (
            <Link
              key={course.id}
              href={`/courses/${course.slug}`}
              className="group flex flex-col justify-between bg-card hover:bg-secondary/20 border border-border/60 hover:border-accent/40 rounded-2xl p-6 transition-all duration-200 hover:shadow-md hover:-translate-y-0.5"
            >
              <div className="space-y-4">
                {/* Badges Bar */}
                <div className="flex items-center justify-between gap-2">
                  <span className="px-2.5 py-1 rounded-md bg-accent/10 text-accent font-semibold text-xs tracking-wide">
                    Semester {course.semester}
                  </span>
                  <div className="flex items-center gap-1.5 text-xs text-muted-foreground font-mono">
                    <span className="px-2 py-0.5 rounded bg-secondary text-secondary-foreground">
                      {course.credits} Credits
                    </span>
                    <span className="px-2 py-0.5 rounded bg-secondary text-secondary-foreground">
                      {course.regulation}
                    </span>
                  </div>
                </div>

                {/* Course Title & Codes */}
                <div>
                  <h3 className="text-lg font-bold tracking-tight text-foreground group-hover:text-accent transition-colors">
                    {course.name}
                  </h3>
                  <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground mt-1">
                    <span>{course.canonicalCode || course.code}</span>
                    {course.canonicalCode && course.canonicalCode !== course.code && (
                      <>
                        <span>•</span>
                        <span>{course.code}</span>
                      </>
                    )}
                  </div>
                </div>

                {/* Description snippet */}
                <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2">
                  {course.description}
                </p>

                {/* Multi-track indicator for Course 8 */}
                {course.hasTracks && (
                  <div className="p-2.5 rounded-xl bg-accent/5 border border-accent/20 flex items-center gap-2 text-xs text-foreground">
                    <Languages className="w-3.5 h-3.5 text-accent shrink-0" />
                    <span className="font-medium">6 Isolated Language Tracks</span>
                  </div>
                )}

                {/* High-Yield Topics Preview */}
                {!course.hasTracks && course.highYieldTopics.length > 0 && (
                  <div className="space-y-1.5 pt-1">
                    <div className="flex items-center gap-1 text-[11px] font-semibold text-muted-foreground">
                      <TrendingUp className="w-3 h-3 text-accent" />
                      <span>Top Recurring Topics:</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {course.highYieldTopics.slice(0, 2).map((t, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded-md bg-secondary text-[11px] text-muted-foreground line-clamp-1 max-w-[200px]"
                        >
                          {t.topic}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Card Footer: Metrics & Link */}
              <div className="pt-6 mt-6 border-t border-border/40 flex items-center justify-between text-xs">
                <div className="flex items-center gap-3 text-muted-foreground">
                  <div>
                    <strong className="text-foreground">{course.paperCount}</strong> papers
                  </div>
                  <span>•</span>
                  <div>
                    <strong className="text-foreground">{course.questionCount}</strong> questions
                  </div>
                  <span>•</span>
                  <div>
                    <strong className="text-foreground">{course.units.length || (course.tracks?.[0]?.units.length ?? 0)}</strong> units
                  </div>
                </div>
                <div className="flex items-center text-accent font-medium group-hover:translate-x-0.5 transition-transform">
                  View <ChevronRight className="w-3.5 h-3.5 ml-0.5" />
                </div>
              </div>
            </Link>
          );
        })}
      </div>

      {filteredCourses.length === 0 && (
        <div className="py-16 text-center space-y-3 bg-secondary/10 rounded-2xl border border-dashed border-border">
          <Search className="w-8 h-8 text-muted-foreground mx-auto opacity-50" />
          <h4 className="text-base font-semibold text-foreground">No courses found</h4>
          <p className="text-xs text-muted-foreground max-w-sm mx-auto">
            We could not find any course matching &ldquo;{searchQuery}&rdquo;. Try searching with subject name or course code like 21MAB101T.
          </p>
          <button
            onClick={() => {
              setSearchQuery("");
              setSelectedSemester("all");
            }}
            className="px-4 py-2 bg-secondary hover:bg-secondary/80 text-foreground text-xs font-medium rounded-lg transition-all"
          >
            Reset Filters
          </button>
        </div>
      )}
    </div>
  );
}
