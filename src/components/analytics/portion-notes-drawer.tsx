"use client";

import React, { useState } from "react";
import { 
  BookOpen, 
  ChevronDown, 
  ChevronUp, 
  ExternalLink, 
  Download, 
  FileText, 
  Sparkles,
  FolderOpen
} from "lucide-react";
import { CourseNoteResource } from "@/lib/course-resources";

interface PortionNotesDrawerProps {
  notes: CourseNoteResource[];
  courseName: string;
  selectedUnits: number[];
  isCT1?: boolean;
  isCT2?: boolean;
  courseSlug?: string;
  isOpenDefault?: boolean;
}

export function PortionNotesDrawer({
  notes,
  courseName,
  selectedUnits,
  isCT1 = false,
  isCT2 = false,
  courseSlug,
  isOpenDefault = false,
}: PortionNotesDrawerProps) {
  const [isOpen, setIsOpen] = useState(isOpenDefault);
  const [selectedUnitFilter, setSelectedUnitFilter] = useState<number | "ALL">("ALL");

  if (!notes || notes.length === 0) {
    return null;
  }

  const portionLabel = isCT1 
    ? "CT1 Portion (Units 1 & 2)" 
    : isCT2 
    ? "CT2 Portion (Units 3 & 4)" 
    : `Units ${selectedUnits.join(", ")}`;

  const filteredNotes = selectedUnitFilter === "ALL" 
    ? notes 
    : notes.filter(n => n.unit === selectedUnitFilter);

  // Available in-scope units that have notes
  const availableUnits = Array.from(
    new Set(notes.map(n => n.unit).filter((u): u is number => u != null))
  ).sort((a, b) => a - b);

  return (
    <div className="rounded-2xl border border-accent/25 bg-card/95 shadow-xs overflow-hidden transition-all">
      {/* Drawer Header Toggle */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3.5 sm:p-4 bg-accent/5 hover:bg-accent/10 transition-colors text-left cursor-pointer"
      >
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-accent/20 border border-accent/30 flex items-center justify-center text-accent">
            <BookOpen className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-xs sm:text-sm font-bold text-foreground">
                Professor Slides &amp; Notes &bull; {portionLabel}
              </h4>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-accent/20 border border-accent/30 text-accent">
                {notes.length} {notes.length === 1 ? "file" : "files"}
              </span>
            </div>
            <p className="text-[11px] text-muted-foreground">
              Official faculty presentations, chapter notes, and unit study guides matched to your selected portion.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 text-xs text-accent font-semibold">
          <span>{isOpen ? "Hide Notes" : "View Slides & Notes"}</span>
          {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {/* Expanded Notes Grid */}
      {isOpen && (
        <div className="p-4 sm:p-5 border-t border-border/60 space-y-4">
          {/* Unit Sub-filter Pills */}
          {availableUnits.length > 1 && (
            <div className="flex flex-wrap items-center gap-1.5 pb-1">
              <span className="text-[11px] font-semibold text-muted-foreground mr-1">Filter Unit:</span>
              <button
                type="button"
                onClick={() => setSelectedUnitFilter("ALL")}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all cursor-pointer ${
                  selectedUnitFilter === "ALL"
                    ? "bg-accent text-accent-foreground font-semibold shadow-2xs"
                    : "bg-muted/40 hover:bg-muted text-muted-foreground"
                }`}
              >
                All In-Scope ({notes.length})
              </button>
              {availableUnits.map((u) => {
                const count = notes.filter(n => n.unit === u).length;
                return (
                  <button
                    key={u}
                    type="button"
                    onClick={() => setSelectedUnitFilter(u)}
                    className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all cursor-pointer ${
                      selectedUnitFilter === u
                        ? "bg-accent text-accent-foreground font-semibold shadow-2xs"
                        : "bg-muted/40 hover:bg-muted text-muted-foreground"
                    }`}
                  >
                    Unit {u} ({count})
                  </button>
                );
              })}
            </div>
          )}

          {/* Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {filteredNotes.map((n, idx) => {
              const driveId = n.url.match(/([a-zA-Z0-9_\-]{25,})/)?.[1];
              const downloadUrl = driveId
                ? `https://drive.google.com/uc?export=download&id=${driveId}`
                : n.url;

              return (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl border border-border/70 bg-background hover:border-accent/40 transition-all flex flex-col justify-between gap-2.5 shadow-2xs group"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between gap-2">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-accent/10 border border-accent/25 text-accent">
                        {n.unit ? `Unit ${n.unit}` : "Course Material"}
                      </span>
                      <span className="text-muted-foreground font-mono text-[9px] truncate max-w-[120px]" title={n.source}>
                        {n.source}
                      </span>
                    </div>

                    <h5 className="text-xs font-semibold text-foreground group-hover:text-accent transition-colors line-clamp-2">
                      {n.title}
                    </h5>
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
                      title="Download direct file"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>
              );
            })}
          </div>

          {courseSlug && (
            <div className="text-right pt-2 border-t border-border/40">
              <a
                href={`/courses/${courseSlug}#verified-papers`}
                className="inline-flex items-center gap-1 text-xs text-accent hover:underline font-semibold"
              >
                <span>Browse all {courseName} course materials on course page</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
