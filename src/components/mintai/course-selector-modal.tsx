"use client";

import React, { useState, useMemo, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, X, BookOpen, Check, Layers, ChevronRight } from "lucide-react";
import { CourseCatalogItem } from "@/lib/courses";
import { CurriculumSubject } from "@/lib/types";

interface CourseSelectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedCourseId: number | null;
  onSelectCourse: (courseId: number) => void;
  branches: string[];
  selectedBranch: string;
  onBranchChange: (branch: string) => void;
  semesters: number[];
  selectedSemester: number;
  onSemesterChange: (semester: number) => void;
  semesterSubjects: CurriculumSubject[];
  eligibleCourses: CourseCatalogItem[];
}

export function CourseSelectorModal({
  isOpen,
  onClose,
  selectedCourseId,
  onSelectCourse,
  branches,
  selectedBranch,
  onBranchChange,
  semesters,
  selectedSemester,
  onSemesterChange,
  semesterSubjects,
  eligibleCourses,
}: CourseSelectorModalProps) {
  const [courseSearchQuery, setCourseSearchQuery] = useState("");

  // Lock scroll on open
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && selectedCourseId) {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
    }
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [isOpen, selectedCourseId, onClose]);

  // Instant Search Across All Courses
  const searchedCourses = useMemo(() => {
    if (!courseSearchQuery.trim()) return [];
    const q = courseSearchQuery.toLowerCase().trim();
    return eligibleCourses.filter((c) => {
      const matchName = c.name.toLowerCase().includes(q);
      const matchCode = c.code.toLowerCase().includes(q);
      const matchCanonical = c.canonicalCode?.toLowerCase().includes(q);
      const matchAlias = c.aliases?.some((a) => a.toLowerCase().includes(q));
      return matchName || matchCode || matchCanonical || matchAlias;
    });
  }, [eligibleCourses, courseSearchQuery]);

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => {
              if (selectedCourseId) onClose();
            }}
            className="fixed inset-0 bg-background/80 backdrop-blur-sm"
          />

          {/* Modal Dialog Card */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ type: "spring", damping: 25, stiffness: 250 }}
            className="relative w-full max-w-2xl bg-card border border-border/80 rounded-2xl shadow-2xl overflow-hidden z-10 flex flex-col max-h-[88vh]"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="p-5 sm:p-6 border-b border-border/60 bg-card shrink-0 flex items-start justify-between gap-4">
              <div className="space-y-1">
                <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-accent/10 border border-accent/20 text-[11px] font-semibold text-accent uppercase tracking-wider">
                  Academic Setup
                </div>
                <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                  Select Your Course
                </h2>
                <p className="text-xs sm:text-sm text-muted-foreground">
                  Choose your engineering department and semester or search any of our cataloged courses.
                </p>
              </div>

              {selectedCourseId && (
                <button
                  type="button"
                  onClick={onClose}
                  className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-xl transition-colors shrink-0 cursor-pointer"
                  aria-label="Close dialog"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>

            {/* Modal Body */}
            <div className="p-5 sm:p-6 overflow-y-auto space-y-5">
              {/* Instant Search Bar */}
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="text"
                  value={courseSearchQuery}
                  onChange={(e) => setCourseSearchQuery(e.target.value)}
                  placeholder="Instant search courses (e.g. Calculus, DSA, OS, 21MAB101T)..."
                  className="w-full bg-muted/20 border border-border rounded-xl pl-10 pr-10 py-2.5 text-sm placeholder:text-muted-foreground text-foreground focus:ring-1 focus:ring-accent focus:outline-none transition-all"
                  autoFocus
                />
                {courseSearchQuery && (
                  <button
                    type="button"
                    onClick={() => setCourseSearchQuery("")}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground p-1"
                    aria-label="Clear search"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>

              {/* If Searching: Display Instant Search Results */}
              {courseSearchQuery.trim() ? (
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-muted-foreground flex items-center justify-between">
                    <span>{searchedCourses.length} courses matching &ldquo;{courseSearchQuery}&rdquo;</span>
                    <span className="text-[10px] font-mono">Click course to select</span>
                  </div>
                  <div className="max-h-72 overflow-y-auto space-y-1.5 pr-1">
                    {searchedCourses.length === 0 ? (
                      <div className="p-8 text-center text-xs text-muted-foreground bg-muted/10 rounded-xl border border-dashed border-border/80">
                        No engineering courses matching &ldquo;{courseSearchQuery}&rdquo;
                      </div>
                    ) : (
                      searchedCourses.map((c) => {
                        const isSelected = c.id === selectedCourseId;
                        return (
                          <button
                            key={c.id}
                            type="button"
                            onClick={() => {
                              onSelectCourse(c.id);
                              onClose();
                            }}
                            className={`w-full p-3 rounded-xl border text-left flex items-center justify-between gap-3 transition-all cursor-pointer ${
                              isSelected
                                ? "bg-accent/15 border-accent text-foreground shadow-2xs"
                                : "bg-card hover:bg-muted/30 border-border/70 text-foreground"
                            }`}
                          >
                            <div className="min-w-0">
                              <div className="font-semibold text-sm truncate flex items-center gap-2">
                                <span>{c.name}</span>
                                {c.canonicalCode && (
                                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-muted text-muted-foreground">
                                    {c.canonicalCode}
                                  </span>
                                )}
                              </div>
                              <div className="text-[11px] text-muted-foreground flex items-center gap-2 pt-0.5">
                                <span>{c.paperCount} verified exams</span>
                                <span>•</span>
                                <span>{c.questionCount} questions</span>
                              </div>
                            </div>
                            <div className="shrink-0 flex items-center gap-1.5 text-xs text-accent font-semibold">
                              {isSelected ? (
                                <span className="inline-flex items-center gap-1 text-accent font-bold">
                                  <Check className="w-4 h-4" /> Selected
                                </span>
                              ) : (
                                <span>Select &rarr;</span>
                              )}
                            </div>
                          </button>
                        );
                      })
                    )}
                  </div>
                </div>
              ) : (
                /* Standard Curriculum Cascade */
                <div className="space-y-4">
                  {/* Branch Selector */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      Department / Specialization
                    </label>
                    <select
                      value={selectedBranch}
                      onChange={(e) => onBranchChange(e.target.value)}
                      className="w-full bg-background border border-border rounded-xl px-3.5 py-2.5 text-sm text-foreground focus:ring-1 focus:ring-accent focus:outline-none transition-all cursor-pointer"
                    >
                      {branches.map((b) => (
                        <option key={b} value={b}>
                          {b}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Semester Pills (1 - 8) */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      Semester
                    </label>
                    <div className="grid grid-cols-4 sm:grid-cols-8 gap-1.5">
                      {semesters.map((s) => (
                        <button
                          key={s}
                          type="button"
                          onClick={() => onSemesterChange(s)}
                          className={`py-2 px-1 rounded-xl text-xs font-bold transition-all cursor-pointer flex flex-col items-center justify-center gap-0.5 ${
                            selectedSemester === s
                              ? "bg-accent text-accent-foreground shadow-2xs font-extrabold"
                              : "bg-muted/30 hover:bg-muted/60 text-muted-foreground hover:text-foreground border border-border/50"
                          }`}
                        >
                          <span>Sem {s}</span>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Available Subjects for this Branch & Semester */}
                  <div className="space-y-2 pt-2">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                        Available Semester {selectedSemester} Subjects
                      </label>
                      <span className="text-[10px] text-muted-foreground font-mono">
                        {semesterSubjects.length} courses in curriculum
                      </span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-60 overflow-y-auto pr-1">
                      {semesterSubjects.length === 0 ? (
                        <div className="col-span-full p-6 text-center text-xs text-muted-foreground bg-muted/10 rounded-xl border border-dashed border-border/80">
                          Loading semester curriculum...
                        </div>
                      ) : (
                        semesterSubjects.map((s) => {
                          const courseId = s.course_id;
                          const verifiedCatalogItem = eligibleCourses.find(
                            (c) => c.id === courseId || c.canonicalCode === s.canonical_code
                          );
                          const resolvedId = courseId || verifiedCatalogItem?.id || null;
                          const isSelected = resolvedId === selectedCourseId;

                          return (
                            <button
                              key={s.canonical_code || s.subject_name}
                              type="button"
                              onClick={() => {
                                if (resolvedId) {
                                  onSelectCourse(resolvedId);
                                  onClose();
                                }
                              }}
                              disabled={!resolvedId}
                              className={`p-3 rounded-xl border text-left flex flex-col justify-between gap-1.5 transition-all ${
                                !resolvedId
                                  ? "opacity-50 cursor-not-allowed bg-muted/5 border-border/40"
                                  : isSelected
                                  ? "bg-accent/15 border-accent text-foreground shadow-2xs cursor-pointer"
                                  : "bg-card hover:bg-muted/30 border-border/70 text-foreground cursor-pointer"
                              }`}
                            >
                              <div className="flex items-start justify-between gap-2">
                                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-muted text-muted-foreground font-semibold">
                                  {s.canonical_code}
                                </span>
                                {isSelected && (
                                  <span className="w-4 h-4 rounded-full bg-accent text-accent-foreground flex items-center justify-center">
                                    <Check className="w-2.5 h-2.5 stroke-[3]" />
                                  </span>
                                )}
                              </div>
                              <div className="font-semibold text-xs leading-snug line-clamp-2">
                                {s.subject_name}
                              </div>
                              <div className="text-[10px] text-muted-foreground pt-0.5 flex items-center justify-between">
                                <span>
                                  {verifiedCatalogItem
                                    ? `${verifiedCatalogItem.paperCount} verified exams`
                                    : "Corpus parsing active"}
                                </span>
                              </div>
                            </button>
                          );
                        })
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 bg-muted/20 border-t border-border/60 shrink-0 flex items-center justify-between text-xs text-muted-foreground">
              <span>SRMIST Regulation 2021 Architecture</span>
              {selectedCourseId && (
                <button
                  type="button"
                  onClick={onClose}
                  className="font-semibold text-accent hover:underline cursor-pointer"
                >
                  Continue with Current Course &rarr;
                </button>
              )}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
