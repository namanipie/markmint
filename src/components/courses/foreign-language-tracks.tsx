"use client";

import { useState } from "react";
import Link from "next/link";
import { CourseTrackCatalogItem } from "@/lib/courses";
import { 
  Languages, 
  ExternalLink, 
  BookOpen, 
  Sparkles, 
  CheckCircle2, 
  ChevronDown, 
  ChevronRight,
  TrendingUp,
  GraduationCap
} from "lucide-react";

interface ForeignLanguageTracksProps {
  tracks: CourseTrackCatalogItem[];
}

export function ForeignLanguageTracks({ tracks }: ForeignLanguageTracksProps) {
  const [selectedKey, setSelectedKey] = useState<string>(tracks[0]?.trackKey || "german");
  const [expandedUnits, setExpandedUnits] = useState<Record<number, boolean>>({ 1: true });

  const activeTrack = tracks.find((t) => t.trackKey === selectedKey) || tracks[0];

  const toggleUnit = (num: number) => {
    setExpandedUnits((prev) => ({ ...prev, [num]: !prev[num] }));
  };

  if (!tracks || tracks.length === 0) {
    return null;
  }

  return (
    <div className="w-full space-y-8">
      {/* Track Selector Tabs */}
      <div className="flex flex-wrap items-center gap-2 p-1.5 bg-secondary/50 rounded-xl border border-border/40">
        {tracks.map((t) => {
          const isSelected = t.trackKey === selectedKey;
          return (
            <button
              key={t.trackKey}
              onClick={() => {
                setSelectedKey(t.trackKey);
                setExpandedUnits({ 1: true });
              }}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isSelected
                  ? "bg-background text-foreground shadow-sm border border-border/80"
                  : "text-muted-foreground hover:text-foreground hover:bg-background/40"
              }`}
            >
              <Languages className={`w-4 h-4 ${isSelected ? "text-accent" : "opacity-60"}`} />
              <span>{t.trackName}</span>
              <span className="text-[11px] font-mono opacity-70">({t.trackCode})</span>
            </button>
          );
        })}
      </div>

      {/* Active Track Card */}
      <div className="bg-card border border-border/60 rounded-2xl p-6 sm:p-8 space-y-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-6 border-b border-border/40">
          <div>
            <div className="flex items-center gap-2.5 text-xs text-muted-foreground font-mono uppercase tracking-wider mb-2">
              <span className="px-2 py-0.5 rounded bg-accent/10 text-accent font-semibold">
                Language Track
              </span>
              <span>{activeTrack.trackCode}</span>
              <span>•</span>
              <span>Regulation 2021</span>
            </div>
            <h3 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
              {activeTrack.trackName} Track
            </h3>
            <p className="text-sm text-muted-foreground mt-1">
              Authoritative curriculum, syllabus units, and verified exam question lineage for {activeTrack.trackName}.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Link
              href={activeTrack.mintAiUrl}
              className="flex items-center gap-2 px-5 py-2.5 bg-foreground text-background text-sm font-medium rounded-lg hover:bg-foreground/90 transition-all active:scale-[0.98]"
            >
              <Sparkles className="w-4 h-4 text-accent" />
              Analyze in MintAI
            </Link>
            <Link
              href={activeTrack.practiceUrl}
              className="flex items-center gap-2 px-4 py-2.5 bg-secondary hover:bg-secondary/80 text-foreground text-sm font-medium rounded-lg border border-border/60 transition-all"
            >
              Practice Questions
              <ExternalLink className="w-3.5 h-3.5 opacity-60" />
            </Link>
          </div>
        </div>

        {/* Track Isolation Notice */}
        <div className="p-3.5 rounded-lg bg-accent/5 border border-accent/20 flex items-start gap-3 text-xs text-muted-foreground leading-relaxed">
          <CheckCircle2 className="w-4 h-4 text-accent shrink-0 mt-0.5" />
          <div>
            <strong className="text-foreground">Isolated Academic Track:</strong> MarkMint strictly isolates {activeTrack.trackName} exam intelligence. Historical exam distributions, frequency patterns, and predictions are not blended with other foreign languages.
          </div>
        </div>

        {/* Track Key Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-secondary/30 border border-border/40">
            <div className="text-xs text-muted-foreground font-medium mb-1">Verified Papers</div>
            <div className="text-2xl font-bold text-foreground">{activeTrack.paperCount}</div>
            <div className="text-[11px] text-muted-foreground mt-0.5">SRMIST Past Exams</div>
          </div>
          <div className="p-4 rounded-xl bg-secondary/30 border border-border/40">
            <div className="text-xs text-muted-foreground font-medium mb-1">Questions Analyzed</div>
            <div className="text-2xl font-bold text-foreground">{activeTrack.questionCount}</div>
            <div className="text-[11px] text-muted-foreground mt-0.5">Indexed from Papers</div>
          </div>
          <div className="p-4 rounded-xl bg-secondary/30 border border-border/40">
            <div className="text-xs text-muted-foreground font-medium mb-1">Syllabus Units</div>
            <div className="text-2xl font-bold text-foreground">{activeTrack.units.length}</div>
            <div className="text-[11px] text-muted-foreground mt-0.5">Authoritative Units</div>
          </div>
          <div className="p-4 rounded-xl bg-secondary/30 border border-border/40">
            <div className="text-xs text-muted-foreground font-medium mb-1">Curriculum Status</div>
            <div className="text-2xl font-bold text-accent">Active</div>
            <div className="text-[11px] text-muted-foreground mt-0.5">Semester 1 & 2</div>
          </div>
        </div>

        {/* High-Yield Topics (if present) */}
        {activeTrack.highYieldTopics && activeTrack.highYieldTopics.length > 0 && (
          <div className="pt-2">
            <div className="flex items-center gap-2 text-sm font-semibold text-foreground mb-3">
              <TrendingUp className="w-4 h-4 text-accent" />
              <span>High-Yield Recurring Topics in {activeTrack.trackName}</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {activeTrack.highYieldTopics.map((top, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl bg-secondary/20 border border-border/40 flex items-start justify-between gap-3 text-xs"
                >
                  <div className="space-y-1">
                    <span className="font-medium text-foreground text-sm line-clamp-1">
                      {top.topic}
                    </span>
                    <span className="inline-block px-2 py-0.5 rounded bg-muted text-muted-foreground text-[10px] font-mono">
                      Unit {top.unitNumber}
                    </span>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="font-semibold text-accent">{top.questionCount} questions</div>
                    <div className="text-[11px] text-muted-foreground">{top.paperCount} papers</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Syllabus Units Accordion */}
        <div className="pt-2">
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground mb-4">
            <BookOpen className="w-4 h-4 text-accent" />
            <span>Authoritative Syllabus Breakdown ({activeTrack.units.length} Units)</span>
          </div>

          <div className="space-y-3">
            {activeTrack.units.map((unit) => {
              const isExpanded = expandedUnits[unit.number];
              return (
                <div
                  key={unit.number}
                  className="border border-border/50 rounded-xl overflow-hidden bg-secondary/15 transition-colors"
                >
                  <button
                    onClick={() => toggleUnit(unit.number)}
                    className="w-full px-5 py-3.5 flex items-center justify-between text-left hover:bg-secondary/30 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <span className="flex items-center justify-center w-7 h-7 rounded-lg bg-accent/10 text-accent font-semibold text-xs shrink-0">
                        U{unit.number}
                      </span>
                      <div>
                        <div className="font-semibold text-foreground text-sm">
                          Unit {unit.number}: {unit.name}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {unit.topicCount} cataloged topics
                        </div>
                      </div>
                    </div>
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4 text-muted-foreground" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-muted-foreground" />
                    )}
                  </button>

                  {isExpanded && unit.topics && unit.topics.length > 0 && (
                    <div className="px-5 pb-4 pt-2 border-t border-border/30 bg-background/40">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
                        {unit.topics.map((t, tidx) => (
                          <div
                            key={tidx}
                            className="flex items-start gap-2 text-xs text-muted-foreground py-1"
                          >
                            <span className="w-1.5 h-1.5 rounded-full bg-accent/60 mt-1.5 shrink-0" />
                            <span>{t}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
