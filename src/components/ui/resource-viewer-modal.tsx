"use client";

import React, { useEffect, useState } from "react";
import { 
  X, 
  ExternalLink, 
  Download, 
  Copy, 
  Check, 
  Play, 
  FileText, 
  Sparkles, 
  BookOpen, 
  Layers, 
  Video, 
  FolderOpen,
  Maximize2
} from "lucide-react";
import { MathText } from "@/components/ui/math-text";
import { 
  getYouTubeEmbedUrl, 
  getDrivePreviewUrl,
  CourseVideoResource,
  CourseFormulaResource,
  CourseNoteResource,
  CourseExamResource
} from "@/lib/course-resources";

export type ResourceViewerItem = 
  | { type: "video"; data: CourseVideoResource; courseName?: string }
  | { type: "formula"; data: CourseFormulaResource; courseName?: string }
  | { type: "note"; data: CourseNoteResource; courseName?: string }
  | { type: "pyq"; data: CourseExamResource; courseName?: string };

interface ResourceViewerModalProps {
  item: ResourceViewerItem | null;
  onClose: () => void;
}

export function ResourceViewerModal({ item, onClose }: ResourceViewerModalProps) {
  const [copied, setCopied] = useState(false);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    if (item) {
      window.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
    }
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "unset";
    };
  }, [item, onClose]);

  if (!item) return null;

  const handleCopyLatex = (latex: string) => {
    navigator.clipboard.writeText(latex);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 md:p-6 bg-background/80 backdrop-blur-md animate-in fade-in duration-200">
      {/* Backdrop tap to close */}
      <div className="absolute inset-0 -z-10" onClick={onClose} />

      <div className="relative w-full max-w-4xl max-h-[92vh] flex flex-col rounded-2xl border border-border/80 bg-card shadow-2xl overflow-hidden transition-all">
        {/* Top Header Bar */}
        <div className="flex items-center justify-between p-3.5 sm:p-4 border-b border-border/60 bg-muted/30">
          <div className="flex items-center gap-2.5 min-w-0 pr-2">
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border ${
              item.type === "video" 
                ? "bg-red-500/10 border-red-500/30 text-red-400"
                : item.type === "formula"
                ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
                : item.type === "pyq"
                ? "bg-accent/10 border-accent/30 text-accent"
                : "bg-blue-500/10 border-blue-500/30 text-blue-400"
            }`}>
              {item.type === "video" && <Video className="w-4 h-4" />}
              {item.type === "formula" && <Sparkles className="w-4 h-4" />}
              {item.type === "pyq" && <FileText className="w-4 h-4" />}
              {item.type === "note" && <FolderOpen className="w-4 h-4" />}
            </div>

            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="text-xs sm:text-sm font-bold text-foreground truncate">
                  {item.data.title}
                </h3>
                {item.courseName && (
                  <span className="hidden sm:inline-block px-2 py-0.5 rounded text-[10px] font-mono bg-accent/10 border border-accent/20 text-accent font-semibold truncate max-w-[180px]">
                    {item.courseName}
                  </span>
                )}
              </div>
              <p className="text-[11px] text-muted-foreground truncate">
                {item.type === "video" && `${item.data.channel} • ${item.data.duration}`}
                {item.type === "formula" && `Unit ${item.data.unit || "Summary"} • Formula Cheat Sheet`}
                {item.type === "note" && `${item.data.source || "Class Material"} • Unit ${item.data.unit || "General"}`}
                {item.type === "pyq" && `${item.data.source || "Official Exam Paper"} • ${item.data.examType || "EndSem"}`}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            {/* Direct Open in new tab button */}
            {item.type === "video" && (
              <a
                href={`https://www.youtube.com/watch?v=${item.data.youtubeId}`}
                target="_blank"
                rel="noopener noreferrer"
                className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-muted hover:bg-muted/80 text-foreground transition-colors"
                title="Open directly on YouTube"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span>YouTube</span>
              </a>
            )}

            {(item.type === "note" || item.type === "pyq") && item.data.url && (
              <a
                href={item.data.url}
                target="_blank"
                rel="noopener noreferrer"
                className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-muted hover:bg-muted/80 text-foreground transition-colors"
                title="Open directly in Google Drive"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span>Drive</span>
              </a>
            )}

            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-colors cursor-pointer"
              aria-label="Close modal"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-3 sm:p-5">
          {/* ============================================================== */}
          {/* 1. YOUTUBE VIDEO VIEWER                                        */}
          {/* ============================================================== */}
          {item.type === "video" && (
            <div className="space-y-4">
              <div className="relative w-full aspect-video rounded-xl overflow-hidden border border-border/80 bg-black shadow-inner">
                <iframe
                  src={getYouTubeEmbedUrl(item.data.youtubeId) || ""}
                  title={item.data.title}
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                  allowFullScreen
                  className="w-full h-full border-0"
                />
              </div>

              {item.data.description && (
                <div className="p-3.5 rounded-xl bg-muted/40 border border-border/60 text-xs text-foreground/90 space-y-1">
                  <div className="flex items-center gap-1.5 font-bold text-accent text-[11px]">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Curated Professor Lecture Notes</span>
                  </div>
                  <p className="leading-relaxed text-muted-foreground">
                    {item.data.description}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* ============================================================== */}
          {/* 2. GOOGLE DRIVE / PDF DOCUMENT VIEWER                          */}
          {/* ============================================================== */}
          {(item.type === "note" || item.type === "pyq") && (
            <div className="space-y-3">
              {getDrivePreviewUrl(item.data.url) ? (
                <div className="relative w-full h-[60vh] sm:h-[68vh] rounded-xl overflow-hidden border border-border/80 bg-muted/20">
                  <iframe
                    src={getDrivePreviewUrl(item.data.url) || ""}
                    title={item.data.title}
                    allow="autoplay"
                    className="w-full h-full border-0"
                  />
                </div>
              ) : (
                <div className="py-16 text-center space-y-4 border border-border/60 rounded-xl bg-muted/20">
                  <FileText className="w-10 h-10 text-muted-foreground mx-auto" />
                  <div className="space-y-1 max-w-sm mx-auto px-4">
                    <h4 className="text-sm font-bold text-foreground">Direct Archive File</h4>
                    <p className="text-xs text-muted-foreground">
                      This material is hosted directly in the course archive. Click below to view or download.
                    </p>
                  </div>
                  <a
                    href={item.data.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-accent text-accent-foreground shadow-md hover:bg-accent/90 transition-all"
                  >
                    <Download className="w-4 h-4" />
                    <span>Download / Open File</span>
                  </a>
                </div>
              )}

              <div className="flex items-center justify-between text-[11px] text-muted-foreground px-1">
                <span>Source: {item.data.source || "SRM Class Archive"}</span>
                <a
                  href={item.data.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-accent font-semibold hover:underline"
                >
                  <ExternalLink className="w-3 h-3" />
                  <span>Open in Google Drive</span>
                </a>
              </div>
            </div>
          )}

          {/* ============================================================== */}
          {/* 3. FORMULA CHEAT SHEET CARD                                    */}
          {/* ============================================================== */}
          {item.type === "formula" && (
            <div className="space-y-4">
              <div className="p-4 sm:p-5 rounded-xl border border-amber-500/25 bg-amber-500/5 space-y-3">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded font-mono font-bold text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      UNIT {item.data.unit || 1}
                    </span>
                    <h4 className="text-sm font-bold text-foreground">
                      {item.data.title}
                    </h4>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleCopyLatex(item.data.latexSnippet)}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-background border border-border/80 hover:border-accent text-muted-foreground hover:text-foreground transition-all cursor-pointer"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copied ? "Copied!" : "Copy LaTeX"}</span>
                  </button>
                </div>

                <p className="text-xs text-muted-foreground leading-relaxed">
                  {item.data.summary}
                </p>

                {/* Formatted Math Card */}
                <div className="p-4 rounded-xl bg-background border border-border/80 text-foreground overflow-x-auto shadow-inner text-sm leading-loose">
                  <MathText content={item.data.latexSnippet} />
                </div>
              </div>

              <div className="p-3 rounded-lg bg-muted/40 border border-border/60 text-[11px] text-muted-foreground flex items-center justify-between">
                <span>💡 Tip: These formulas match questions frequently asked in SRMIST CT1, CT2, and University End-Sem papers.</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
