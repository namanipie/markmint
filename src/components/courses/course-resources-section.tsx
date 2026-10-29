"use client";

import React, { useState, useMemo } from "react";
import { 
  FileText, 
  Download, 
  ExternalLink, 
  BookOpen, 
  Layers, 
  Sparkles, 
  Filter, 
  Calendar, 
  ShieldCheck,
  FolderOpen
} from "lucide-react";
import { CourseResourceGroup, CourseExamResource, CourseNoteResource } from "@/lib/course-resources";

interface CourseResourcesSectionProps {
  resources: CourseResourceGroup | null;
  courseName: string;
}

export function CourseResourcesSection({ resources, courseName }: CourseResourcesSectionProps) {
  const [activeTab, setActiveTab] = useState<"pyqs" | "notes" | "syllabus">("pyqs");
  const [selectedExamType, setSelectedExamType] = useState<string>("ALL");
  const [selectedUnit, setSelectedUnit] = useState<number | "ALL" | "CT1" | "CT2">("ALL");

  if (!resources || (resources.pyqsCount === 0 && resources.notesCount === 0 && !resources.syllabusUrl)) {
    return null;
  }

  // Filtered PYQs
  const filteredPyqs = useMemo(() => {
    if (!resources.pyqs) return [];
    if (selectedExamType === "ALL") return resources.pyqs;
    return resources.pyqs.filter((p) => p.examType === selectedExamType);
  }, [resources.pyqs, selectedExamType]);

  // Filtered Notes
  const filteredNotes = useMemo(() => {
    if (!resources.notes) return [];
    if (selectedUnit === "ALL") return resources.notes;
    if (selectedUnit === "CT1") return resources.notes.filter((n) => n.unit === 1 || n.unit === 2);
    if (selectedUnit === "CT2") return resources.notes.filter((n) => n.unit === 3 || n.unit === 4);
    return resources.notes.filter((n) => n.unit === selectedUnit);
  }, [resources.notes, selectedUnit]);

  // Counts by portion
  const ct1NotesCount = resources.notes ? resources.notes.filter((n) => n.unit === 1 || n.unit === 2).length : 0;
  const ct2NotesCount = resources.notes ? resources.notes.filter((n) => n.unit === 3 || n.unit === 4).length : 0;

  // Counts by exam type
  const ct1Count = resources.pyqs.filter((p) => p.examType === "CT1").length;
  const ct2Count = resources.pyqs.filter((p) => p.examType === "CT2").length;
  const endsemCount = resources.pyqs.filter((p) => p.examType === "ENDSEM").length;

  return (
    <section id="verified-papers" className="space-y-6 pt-4 border-t border-border/40 scroll-mt-20">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-accent/10 border border-accent/20 text-[11px] font-semibold text-accent uppercase tracking-wider">
            <FolderOpen className="w-3.5 h-3.5" />
            <span>Sourced SRM Class Archives</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
            Verified Past Papers &amp; Professor Materials
          </h2>
          <p className="text-xs sm:text-sm text-muted-foreground">
            Download original historical question papers, faculty answer keys, and unit presentations for <strong className="text-foreground">{courseName}</strong>.
          </p>
        </div>

        {/* Tab switchers */}
        <div className="flex items-center gap-1.5 p-1 bg-muted/20 border border-border/60 rounded-xl self-start sm:self-auto text-xs font-semibold">
          <button
            type="button"
            onClick={() => setActiveTab("pyqs")}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === "pyqs"
                ? "bg-accent text-accent-foreground shadow-2xs font-bold"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Past Papers</span>
            <span className="px-1.5 py-0.2 rounded-full bg-background/20 text-[10px]">
              {resources.pyqsCount}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("notes")}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === "notes"
                ? "bg-accent text-accent-foreground shadow-2xs font-bold"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Slides &amp; Notes</span>
            <span className="px-1.5 py-0.2 rounded-full bg-background/20 text-[10px]">
              {resources.notesCount}
            </span>
          </button>

          {resources.syllabusUrl && (
            <a
              href={resources.syllabusUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1.5 rounded-lg text-muted-foreground hover:text-foreground transition-all flex items-center gap-1.5 cursor-pointer"
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Syllabus PDF</span>
              <ExternalLink className="w-3 h-3 opacity-60" />
            </a>
          )}
        </div>
      </div>

      {/* TAB 1: PAST PAPERS */}
      {activeTab === "pyqs" && (
        <div className="space-y-4">
          {/* Exam Type Sub-filters */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            {[
              { id: "ALL", label: "All Papers", count: resources.pyqsCount },
              { id: "CT1", label: "Cycle Test 1 (CT1)", count: ct1Count },
              { id: "CT2", label: "Cycle Test 2 (CT2)", count: ct2Count },
              { id: "ENDSEM", label: "Semester End", count: endsemCount },
            ].map((f) => (
              <button
                key={f.id}
                type="button"
                onClick={() => setSelectedExamType(f.id)}
                className={`px-3 py-1 rounded-lg border transition-all cursor-pointer ${
                  selectedExamType === f.id
                    ? "bg-secondary text-secondary-foreground border-border font-bold shadow-2xs"
                    : "bg-muted/10 border-border/40 text-muted-foreground hover:text-foreground"
                }`}
              >
                <span>{f.label}</span>
                {f.count > 0 && (
                  <span className="ml-1.5 text-[10px] opacity-70">({f.count})</span>
                )}
              </button>
            ))}
          </div>

          {/* Grid of Papers */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {filteredPyqs.map((p, idx) => {
              const driveId = p.url.match(/([a-zA-Z0-9_\-]{25,})/)?.[1];
              const downloadUrl = driveId
                ? `https://drive.google.com/uc?export=download&id=${driveId}`
                : p.url;

              return (
                <div
                  key={idx}
                  className="p-4 rounded-xl bg-card border border-border/60 hover:border-accent/40 transition-all flex flex-col justify-between gap-3 shadow-2xs group"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between gap-2">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                          p.examType === "CT1"
                            ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"
                            : p.examType === "CT2"
                            ? "bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20"
                            : "bg-accent/10 text-accent border border-accent/20"
                        }`}
                      >
                        {p.examType}
                      </span>

                      {p.year && (
                        <span className="text-[11px] font-mono font-semibold text-muted-foreground">
                          {p.year}
                        </span>
                      )}
                    </div>

                    <h3 className="text-xs sm:text-sm font-semibold text-foreground group-hover:text-accent transition-colors line-clamp-2">
                      {p.title}
                    </h3>

                    <div className="text-[10px] text-muted-foreground flex items-center gap-1">
                      <span>Source:</span>
                      <span className="text-foreground/80 font-medium">{p.source}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 pt-2 border-t border-border/40">
                    <a
                      href={p.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-1 inline-flex items-center justify-center gap-1.5 py-1.5 px-2.5 rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 border border-border/50 text-[11px] font-semibold transition-all cursor-pointer"
                    >
                      <span>View File</span>
                      <ExternalLink className="w-3 h-3 opacity-70" />
                    </a>

                    <a
                      href={downloadUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      download
                      className="inline-flex items-center justify-center p-1.5 rounded-lg bg-muted/30 hover:bg-muted text-muted-foreground hover:text-foreground border border-border/40 transition-all cursor-pointer"
                      title="Download direct file"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>
              );
            })}
          </div>

          {filteredPyqs.length === 0 && (
            <div className="p-8 text-center rounded-xl border border-dashed border-border/60 text-xs text-muted-foreground">
              No papers found matching the &quot;{selectedExamType}&quot; filter. Select &quot;All Papers&quot; to view all available cycles.
            </div>
          )}
        </div>
      )}

      {/* TAB 2: SLIDES & NOTES */}
      {activeTab === "notes" && (
        <div className="space-y-4">
          {/* Unit Filters */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            <button
              type="button"
              onClick={() => setSelectedUnit("ALL")}
              className={`px-3 py-1 rounded-lg border transition-all cursor-pointer ${
                selectedUnit === "ALL"
                  ? "bg-secondary text-secondary-foreground border-border font-bold shadow-2xs"
                  : "bg-muted/10 border-border/40 text-muted-foreground hover:text-foreground"
              }`}
            >
              All Units ({resources.notesCount})
            </button>

            {/* Quick Portion Presets */}
            {ct1NotesCount > 0 && (
              <button
                type="button"
                onClick={() => setSelectedUnit("CT1")}
                className={`px-3 py-1 rounded-lg border transition-all cursor-pointer flex items-center gap-1.5 ${
                  selectedUnit === "CT1"
                    ? "bg-accent text-accent-foreground border-accent font-bold shadow-2xs"
                    : "bg-accent/10 border-accent/25 text-accent hover:bg-accent/20"
                }`}
              >
                <Sparkles className="w-3 h-3" />
                <span>CT1 (Units 1 &amp; 2)</span>
                <span className="text-[10px] opacity-80">({ct1NotesCount})</span>
              </button>
            )}

            {ct2NotesCount > 0 && (
              <button
                type="button"
                onClick={() => setSelectedUnit("CT2")}
                className={`px-3 py-1 rounded-lg border transition-all cursor-pointer flex items-center gap-1.5 ${
                  selectedUnit === "CT2"
                    ? "bg-accent text-accent-foreground border-accent font-bold shadow-2xs"
                    : "bg-accent/10 border-accent/25 text-accent hover:bg-accent/20"
                }`}
              >
                <Sparkles className="w-3 h-3" />
                <span>CT2 (Units 3 &amp; 4)</span>
                <span className="text-[10px] opacity-80">({ct2NotesCount})</span>
              </button>
            )}
            {[1, 2, 3, 4, 5].map((u) => {
              const count = resources.notes.filter((n) => n.unit === u).length;
              return (
                <button
                  key={u}
                  type="button"
                  onClick={() => setSelectedUnit(u)}
                  className={`px-3 py-1 rounded-lg border transition-all cursor-pointer ${
                    selectedUnit === u
                      ? "bg-secondary text-secondary-foreground border-border font-bold shadow-2xs"
                      : "bg-muted/10 border-border/40 text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Unit {u} {count > 0 && <span className="opacity-70">({count})</span>}
                </button>
              );
            })}
          </div>

          {/* Grid of Notes */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {filteredNotes.map((n, idx) => {
              const driveId = n.url.match(/([a-zA-Z0-9_\-]{25,})/)?.[1];
              const downloadUrl = driveId
                ? `https://drive.google.com/uc?export=download&id=${driveId}`
                : n.url;

              return (
                <div
                  key={idx}
                  className="p-4 rounded-xl bg-card border border-border/60 hover:border-accent/40 transition-all flex flex-col justify-between gap-3 shadow-2xs group"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between gap-2">
                      <span className="px-2 py-0.5 rounded bg-accent/10 border border-accent/20 text-accent text-[10px] font-bold uppercase tracking-wider">
                        {n.unit ? `Unit ${n.unit}` : "Course Material"}
                      </span>
                    </div>

                    <h3 className="text-xs sm:text-sm font-semibold text-foreground group-hover:text-accent transition-colors line-clamp-2">
                      {n.title}
                    </h3>

                    <div className="text-[10px] text-muted-foreground flex items-center gap-1">
                      <span>Source:</span>
                      <span className="text-foreground/80 font-medium">{n.source}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 pt-2 border-t border-border/40">
                    <a
                      href={n.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-1 inline-flex items-center justify-center gap-1.5 py-1.5 px-2.5 rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 border border-border/50 text-[11px] font-semibold transition-all cursor-pointer"
                    >
                      <span>Open Document</span>
                      <ExternalLink className="w-3 h-3 opacity-70" />
                    </a>

                    <a
                      href={downloadUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      download
                      className="inline-flex items-center justify-center p-1.5 rounded-lg bg-muted/30 hover:bg-muted text-muted-foreground hover:text-foreground border border-border/40 transition-all cursor-pointer"
                      title="Download"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>
              );
            })}
          </div>

          {filteredNotes.length === 0 && (
            <div className="p-8 text-center rounded-xl border border-dashed border-border/60 text-xs text-muted-foreground">
              No specific slides cataloged for this unit filter. Select &quot;All Units&quot; to browse all available lecture materials.
            </div>
          )}
        </div>
      )}
    </section>
  );
}
