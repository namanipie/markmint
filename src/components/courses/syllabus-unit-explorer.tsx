"use client";

import { useState } from "react";
import { CourseUnitCatalogItem } from "@/lib/courses";
import { BookOpen, ChevronDown, ChevronRight } from "lucide-react";

interface SyllabusUnitExplorerProps {
  units: CourseUnitCatalogItem[];
}

export function SyllabusUnitExplorer({ units }: SyllabusUnitExplorerProps) {
  const [expandedUnits, setExpandedUnits] = useState<Record<number, boolean>>({ 1: true, 2: true });

  const toggleUnit = (num: number) => {
    setExpandedUnits((prev) => ({ ...prev, [num]: !prev[num] }));
  };

  const expandAll = () => {
    const all: Record<number, boolean> = {};
    units.forEach((u) => {
      all[u.number] = true;
    });
    setExpandedUnits(all);
  };

  const collapseAll = () => {
    setExpandedUnits({});
  };

  if (!units || units.length === 0) {
    return (
      <div className="p-6 rounded-2xl border border-dashed border-border text-center text-sm text-muted-foreground">
        Curriculum taxonomy onboarding in progress. Question family frequency analysis remains fully active.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
          <BookOpen className="w-4 h-4 text-accent" />
          <span>Curriculum Units ({units.length} Units)</span>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <button
            onClick={expandAll}
            className="text-muted-foreground hover:text-foreground transition-colors font-medium"
          >
            Expand all
          </button>
          <span className="text-border">•</span>
          <button
            onClick={collapseAll}
            className="text-muted-foreground hover:text-foreground transition-colors font-medium"
          >
            Collapse all
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {units.map((unit) => {
          const isExpanded = expandedUnits[unit.number];
          return (
            <div
              key={unit.number}
              className="border border-border/50 rounded-xl overflow-hidden bg-secondary/15 transition-colors"
            >
              <button
                onClick={() => toggleUnit(unit.number)}
                className="w-full px-5 py-4 flex items-center justify-between text-left hover:bg-secondary/30 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-accent/10 text-accent font-semibold text-xs shrink-0">
                    U{unit.number}
                  </span>
                  <div>
                    <div className="font-semibold text-foreground text-sm">
                      Unit {unit.number}: {unit.name}
                    </div>
                    <div className="text-xs text-muted-foreground mt-0.5">
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
                <div className="px-5 pb-4 pt-3 border-t border-border/30 bg-background/50">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {unit.topics.map((t, idx) => (
                      <div
                        key={idx}
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
  );
}
