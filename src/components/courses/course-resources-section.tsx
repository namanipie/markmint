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
  FolderOpen,
  Video,
  Play,
  Plus,
  Copy,
  Check
} from "lucide-react";
import { 
  CourseResourceGroup, 
  CourseExamResource, 
  CourseNoteResource,
  CourseVideoResource,
  CourseFormulaResource 
} from "@/lib/course-resources";
import { ResourceViewerModal, ResourceViewerItem } from "@/components/ui/resource-viewer-modal";
import { SubmitResourceModal } from "@/components/courses/submit-resource-modal";

interface CourseResourcesSectionProps {
  resources: CourseResourceGroup | null;
  courseName: string;
}

export function CourseResourcesSection({ resources, courseName }: CourseResourcesSectionProps) {
  const [activeTab, setActiveTab] = useState<"pyqs" | "notes" | "videos" | "formulas" | "syllabus">("pyqs");
  const [selectedExamType, setSelectedExamType] = useState<string>("ALL");
  const [selectedUnit, setSelectedUnit] = useState<number | "ALL" | "CT1" | "CT2">("ALL");
  const [activeViewerItem, setActiveViewerItem] = useState<ResourceViewerItem | null>(null);
  const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);

  if (!resources || (resources.pyqsCount === 0 && resources.notesCount === 0 && !resources.syllabusUrl)) {
    return null;
  }

  const isMathCourse = courseName.toLowerCase().includes("calculus") || 
                       courseName.toLowerCase().includes("math") || 
                       courseName.toLowerCase().includes("transform") || 
                       courseName.toLowerCase().includes("probability");

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

  // Videos & Formulas
  const videos = resources.videos || [];
  const formulas = resources.formulas || [];

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
            Study Materials, PYQs &amp; Video Classes
          </h2>
          <p className="text-xs sm:text-sm text-muted-foreground">
            Direct access to professor lecture slides, authentic SRM past question papers, and recommended video playlists for <strong className="text-foreground">{courseName}</strong>.
          </p>
        </div>

        {/* Action button: Share resource */}
        <button
          type="button"
          onClick={() => setIsSubmitModalOpen(true)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-accent text-accent-foreground text-xs font-bold shadow-xs hover:bg-accent/90 transition-all cursor-pointer self-start sm:self-auto shrink-0"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Share Material</span>
        </button>
      </div>

      {/* Primary Tab Switcher */}
      <div className="flex items-center gap-1.5 p-1 bg-muted/20 border border-border/60 rounded-xl overflow-x-auto no-scrollbar text-xs font-semibold">
        <button
          type="button"
          onClick={() => setActiveTab("pyqs")}
          className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
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
          className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
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

        {videos.length > 0 && (
          <button
            type="button"
            onClick={() => setActiveTab("videos")}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
              activeTab === "videos"
                ? "bg-red-500 text-white shadow-2xs font-bold"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Video className="w-3.5 h-3.5" />
            <span>Video Classes</span>
            <span className="px-1.5 py-0.2 rounded-full bg-background/20 text-[10px]">
              {videos.length}
            </span>
          </button>
        )}

        {formulas.length > 0 && (
          <button
            type="button"
            onClick={() => setActiveTab("formulas")}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
              activeTab === "formulas"
                ? "bg-amber-500 text-black shadow-2xs font-bold"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Formula Sheets</span>
            <span className="px-1.5 py-0.2 rounded-full bg-background/20 text-[10px]">
              {formulas.length}
            </span>
          </button>
        )}

        {resources.syllabusUrl && (
          <a
            href={resources.syllabusUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-1.5 rounded-lg text-muted-foreground hover:text-foreground transition-all flex items-center gap-1.5 cursor-pointer whitespace-nowrap ml-auto"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Syllabus PDF</span>
            <ExternalLink className="w-3 h-3 opacity-60" />
          </a>
        )}
      </div>

      {/* =================================================================== */}
      {/* TAB 1: PAST PAPERS                                                  */}
      {/* =================================================================== */}
      {activeTab === "pyqs" && (
        <div className="space-y-4">
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

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {filteredPyqs.map((p, idx) => (
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
                  <button
                    type="button"
                    onClick={() => setActiveViewerItem({ type: "pyq", data: p, courseName })}
                    className="flex-1 inline-flex items-center justify-center gap-1.5 py-1.5 px-2.5 rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 border border-border/50 text-[11px] font-semibold transition-all cursor-pointer"
                  >
                    <span>View In-App</span>
                    <ExternalLink className="w-3 h-3 opacity-70" />
                  </button>

                  <a
                    href={p.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center justify-center p-1.5 rounded-lg bg-muted/30 hover:bg-muted text-muted-foreground hover:text-foreground border border-border/40 transition-all cursor-pointer"
                    title="Open directly in Google Drive"
                  >
                    <Download className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            ))}
          </div>

          {filteredPyqs.length === 0 && (
            <div className="p-8 text-center rounded-xl border border-dashed border-border/60 text-xs text-muted-foreground">
              No papers found matching the &quot;{selectedExamType}&quot; filter. Select &quot;All Papers&quot; to view all available cycles.
            </div>
          )}
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 2: SLIDES & NOTES                                               */}
      {/* =================================================================== */}
      {activeTab === "notes" && (
        <div className="space-y-4">
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

            {ct1NotesCount > 0 && (
              <button
                type="button"
                onClick={() => setSelectedUnit("CT1")}
                className={`px-3 py-1 rounded-lg border transition-all cursor-pointer ${
                  selectedUnit === "CT1"
                    ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30 font-bold"
                    : "bg-muted/10 border-border/40 text-muted-foreground hover:text-foreground"
                }`}
              >
                CT1 Portion (Units 1-2) ({ct1NotesCount})
              </button>
            )}

            {ct2NotesCount > 0 && (
              <button
                type="button"
                onClick={() => setSelectedUnit("CT2")}
                className={`px-3 py-1 rounded-lg border transition-all cursor-pointer ${
                  selectedUnit === "CT2"
                    ? "bg-amber-500/15 text-amber-400 border-amber-500/30 font-bold"
                    : "bg-muted/10 border-border/40 text-muted-foreground hover:text-foreground"
                }`}
              >
                CT2 Portion (Units 3-4) ({ct2NotesCount})
              </button>
            )}

            {[1, 2, 3, 4, 5].map((u) => {
              const count = resources.notes ? resources.notes.filter((n) => n.unit === u).length : 0;
              if (count === 0) return null;
              return (
                <button
                  key={u}
                  type="button"
                  onClick={() => setSelectedUnit(u)}
                  className={`px-2.5 py-1 rounded-lg border transition-all cursor-pointer ${
                    selectedUnit === u
                      ? "bg-secondary text-secondary-foreground border-border font-bold"
                      : "bg-muted/10 border-border/40 text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Unit {u} ({count})
                </button>
              );
            })}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {filteredNotes.map((n, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl bg-card border border-border/60 hover:border-accent/40 transition-all flex flex-col justify-between gap-3 shadow-2xs group"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-blue-500/10 text-blue-400 border border-blue-500/20">
                      {n.unit ? `Unit ${n.unit}` : "Course Notes"}
                    </span>
                    <span className="text-[10px] font-mono text-muted-foreground">
                      {n.type || "PDF / Slides"}
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
                  <button
                    type="button"
                    onClick={() => setActiveViewerItem({ type: "note", data: n, courseName })}
                    className="flex-1 inline-flex items-center justify-center gap-1.5 py-1.5 px-2.5 rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 border border-border/50 text-[11px] font-semibold transition-all cursor-pointer"
                  >
                    <span>Read Notes</span>
                    <ExternalLink className="w-3 h-3 opacity-70" />
                  </button>

                  <a
                    href={n.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center justify-center p-1.5 rounded-lg bg-muted/30 hover:bg-muted text-muted-foreground hover:text-foreground border border-border/40 transition-all cursor-pointer"
                    title="Open file in Drive"
                  >
                    <Download className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 3: VIDEO MASTERCLASSES                                          */}
      {/* =================================================================== */}
      {activeTab === "videos" && videos.length > 0 && (
        <div className="space-y-4">
          <div className="p-3.5 rounded-xl bg-accent/5 border border-accent/20 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
              <span className="font-semibold text-foreground">
                {isMathCourse ? "Official SRMIST Math Faculty Playlists" : "Curated Engineering Video Masterclasses"}
              </span>
            </div>
            <span className="text-muted-foreground text-[11px]">
              {isMathCourse ? "Instructor: Dr. E. Suresh (SRMIST Mathematics)" : "Preferred: Gate Smashers"}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {videos.map((v) => (
              <div
                key={v.id}
                className="p-4 rounded-xl bg-card border border-border/70 hover:border-red-500/50 transition-all flex flex-col justify-between gap-3 shadow-2xs group"
              >
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-red-500/10 text-red-400 border border-red-500/20">
                      {v.duration}
                    </span>
                    <span className="text-[10px] font-bold text-accent">
                      {v.topicName || `Unit ${v.unit}`}
                    </span>
                  </div>

                  <h3 className="text-xs sm:text-sm font-bold text-foreground group-hover:text-red-400 transition-colors line-clamp-2 leading-snug">
                    {v.title}
                  </h3>

                  <div className="text-[11px] text-muted-foreground">
                    <span>Channel: </span>
                    <strong className="text-foreground">{v.channel}</strong>
                  </div>

                  {v.description && (
                    <p className="text-[11px] text-muted-foreground line-clamp-2 leading-relaxed">
                      {v.description}
                    </p>
                  )}
                </div>

                <button
                  type="button"
                  onClick={() => setActiveViewerItem({ type: "video", data: v, courseName })}
                  className="w-full inline-flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500 hover:text-white border border-red-500/30 text-xs font-bold transition-all cursor-pointer"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Watch in MarkMint</span>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 4: FORMULA CHEAT SHEETS                                         */}
      {/* =================================================================== */}
      {activeTab === "formulas" && formulas.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {formulas.map((f) => (
            <div
              key={f.id}
              className="p-4 rounded-xl bg-card border border-amber-500/30 hover:border-amber-500/60 transition-all flex flex-col justify-between gap-3 shadow-2xs"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/10 text-amber-300 border border-amber-500/20">
                    Unit {f.unit || 1} Cheat Sheet
                  </span>
                  <span className="text-[11px] font-bold text-accent">
                    {f.topicName}
                  </span>
                </div>

                <h3 className="text-sm font-bold text-foreground">
                  {f.title}
                </h3>

                <p className="text-xs text-muted-foreground leading-relaxed">
                  {f.summary}
                </p>
              </div>

              <button
                type="button"
                onClick={() => setActiveViewerItem({ type: "formula", data: f, courseName })}
                className="w-full inline-flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-amber-500/10 text-amber-300 hover:bg-amber-500 hover:text-black border border-amber-500/30 text-xs font-bold transition-all cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>View Full Cheat Sheet</span>
              </button>
            </div>
          ))}
        </div>
      )}

      {/* In-App Resource Viewer Modal */}
      <ResourceViewerModal
        item={activeViewerItem}
        onClose={() => setActiveViewerItem(null)}
      />

      {/* Submit Community Resource Modal */}
      <SubmitResourceModal
        isOpen={isSubmitModalOpen}
        onClose={() => setIsSubmitModalOpen(false)}
        courseName={courseName}
      />
    </section>
  );
}
