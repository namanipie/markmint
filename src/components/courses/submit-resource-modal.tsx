"use client";

import React, { useState } from "react";
import { 
  X, 
  Upload, 
  Link as LinkIcon, 
  Sparkles, 
  CheckCircle2, 
  AlertCircle,
  Video,
  FileText,
  FolderOpen
} from "lucide-react";

interface SubmitResourceModalProps {
  isOpen: boolean;
  onClose: () => void;
  courseName: string;
  courseCode?: string;
  defaultUnit?: number | null;
}

export function SubmitResourceModal({
  isOpen,
  onClose,
  courseName,
  courseCode,
  defaultUnit = 1,
}: SubmitResourceModalProps) {
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const [type, setType] = useState<"video" | "notes" | "formula" | "pyq">("video");
  const [unit, setUnit] = useState<number>(defaultUnit || 1);
  const [channelOrAuthor, setChannelOrAuthor] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !url.trim()) {
      setError("Please fill in both the title and the resource link.");
      return;
    }

    if (!url.startsWith("http://") && !url.startsWith("https://")) {
      setError("Please enter a valid HTTP or HTTPS link.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    // Save submission to localStorage
    try {
      const existingSubmissions = JSON.parse(
        localStorage.getItem("markmint_community_resources") || "[]"
      );
      const newSubmission = {
        id: `res-${Date.now()}`,
        courseName,
        courseCode,
        title: title.trim(),
        url: url.trim(),
        type,
        unit,
        channelOrAuthor: channelOrAuthor.trim(),
        submittedAt: new Date().toISOString(),
        status: "PENDING_REVIEW"
      };
      existingSubmissions.push(newSubmission);
      localStorage.setItem("markmint_community_resources", JSON.stringify(existingSubmissions));

      setIsSubmitting(false);
      setIsSuccess(true);
      setTimeout(() => {
        setIsSuccess(false);
        setTitle("");
        setUrl("");
        setChannelOrAuthor("");
        onClose();
      }, 2000);
    } catch {
      setIsSubmitting(false);
      setError("Failed to save submission. Please try again.");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-background/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="absolute inset-0 -z-10" onClick={onClose} />

      <div className="relative w-full max-w-lg rounded-2xl border border-border/80 bg-card shadow-2xl overflow-hidden p-5 sm:p-6 space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-border/60">
          <div className="space-y-0.5">
            <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-accent/10 text-accent text-[10px] font-bold uppercase tracking-wider">
              <Sparkles className="w-3 h-3" />
              <span>Crowdsource verified notes</span>
            </div>
            <h3 className="text-base sm:text-lg font-bold text-foreground">
              Share Study Resource
            </h3>
            <p className="text-xs text-muted-foreground">
              Helping SRMIST students excel in <strong className="text-foreground">{courseName}</strong>
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Success State */}
        {isSuccess ? (
          <div className="py-8 text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h4 className="text-base font-bold text-foreground">
              Resource Submitted Successfully!
            </h4>
            <p className="text-xs text-muted-foreground max-w-xs mx-auto">
              Thank you for contributing! Your link has been submitted for peer verification and will appear for your batchmates shortly.
            </p>
          </div>
        ) : (
          /* Submission Form */
          <form onSubmit={handleSubmit} className="space-y-4 text-xs">
            {error && (
              <div className="p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Type Selector */}
            <div className="space-y-1.5">
              <label className="font-semibold text-foreground">Resource Format</label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: "video" as const, label: "YouTube Video", icon: Video },
                  { id: "notes" as const, label: "Drive / PPT Notes", icon: FolderOpen },
                  { id: "pyq" as const, label: "Past Exam Paper", icon: FileText },
                ].map((t) => {
                  const Icon = t.icon;
                  return (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => setType(t.id)}
                      className={`flex flex-col items-center justify-center gap-1.5 p-2.5 rounded-xl border text-center transition-all cursor-pointer ${
                        type === t.id
                          ? "bg-accent/15 border-accent text-accent font-bold shadow-xs"
                          : "bg-muted/30 border-border/60 text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      <span className="text-[11px]">{t.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Title */}
            <div className="space-y-1.5">
              <label className="font-semibold text-foreground">Resource Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Dr. E. Suresh Unit 1 Cayley-Hamilton Shortcut / Unit 2 Notes"
                className="w-full px-3 py-2 rounded-xl bg-muted/40 border border-border/80 text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-accent"
                required
              />
            </div>

            {/* URL */}
            <div className="space-y-1.5">
              <label className="font-semibold text-foreground">Link (YouTube or Google Drive)</label>
              <div className="relative">
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://www.youtube.com/watch?v=... or https://drive.google.com/..."
                  className="w-full pl-8 pr-3 py-2 rounded-xl bg-muted/40 border border-border/80 text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-accent"
                  required
                />
                <LinkIcon className="w-3.5 h-3.5 text-muted-foreground absolute left-2.5 top-1/2 -translate-y-1/2" />
              </div>
            </div>

            {/* Unit & Channel row */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="font-semibold text-foreground">Syllabus Unit</label>
                <select
                  value={unit}
                  onChange={(e) => setUnit(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl bg-muted/40 border border-border/80 text-foreground focus:outline-none focus:border-accent"
                >
                  <option value={1}>Unit 1</option>
                  <option value={2}>Unit 2</option>
                  <option value={3}>Unit 3</option>
                  <option value={4}>Unit 4</option>
                  <option value={5}>Unit 5</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="font-semibold text-foreground">Author / Channel (Optional)</label>
                <input
                  type="text"
                  value={channelOrAuthor}
                  onChange={(e) => setChannelOrAuthor(e.target.value)}
                  placeholder="e.g. Dr. E. Suresh / Gate Smashers"
                  className="w-full px-3 py-2 rounded-xl bg-muted/40 border border-border/80 text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-accent"
                />
              </div>
            </div>

            {/* Submit Button */}
            <div className="pt-2 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-5 py-2 rounded-xl text-xs font-bold bg-accent text-accent-foreground hover:bg-accent/90 shadow-md transition-all cursor-pointer disabled:opacity-50"
              >
                {isSubmitting ? "Submitting..." : "Submit Resource"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
