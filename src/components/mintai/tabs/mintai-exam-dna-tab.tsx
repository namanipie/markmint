"use client";

import React from "react";
import { ExamDNAView } from "@/components/analytics/exam-dna-view";
import { CourseCatalogItem } from "@/lib/courses";
import { Dna } from "lucide-react";

interface MintAIExamDNATabProps {
  currentCourse: CourseCatalogItem | null;
  selectedCycle: string;
}

export function MintAIExamDNATab({ currentCourse, selectedCycle }: MintAIExamDNATabProps) {
  if (!currentCourse) {
    return (
      <div className="p-8 text-center rounded-2xl border border-dashed border-border/80 bg-card/40 space-y-2">
        <Dna className="w-8 h-8 text-muted-foreground mx-auto" />
        <p className="text-sm font-semibold text-foreground">Select a course to view its Exam DNA</p>
        <p className="text-xs text-muted-foreground">Historical paper corpus analytics, unit weightages, and Bloom's taxonomy demand.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-border/50 space-y-1">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center text-accent">
            <Dna className="w-4 h-4" />
          </div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
            Exam DNA Intelligence Radar
          </h2>
        </div>
        <p className="text-xs text-muted-foreground">
          Empirical historical paper analysis, unit mark weightages, question family archetypes, and cognitive demand patterns for{" "}
          <strong className="text-foreground">{currentCourse.name}</strong>.
        </p>
      </div>

      <ExamDNAView
        courseId={currentCourse.id}
        courseName={currentCourse.name}
        canonicalCode={currentCourse.canonicalCode || currentCourse.code}
        assessmentCycle={selectedCycle}
      />
    </div>
  );
}
