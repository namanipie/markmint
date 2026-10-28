"use client";

import React, { useState, useEffect } from "react";
import { 
  Layers, 
  Check, 
  Megaphone, 
  Calendar, 
  SlidersHorizontal, 
  Sparkles, 
  Users, 
  HelpCircle,
  FileQuestion,
  BookOpen
} from "lucide-react";
import { CourseCatalogItem, CourseUnitCatalogItem } from "@/lib/courses";
import { StudentExamScopeModal } from "./student-exam-scope-modal";
import { getExamAnnouncementsForCourse, ExamAnnouncementItem } from "@/lib/api";

interface ExamUnitSelectorProps {
  course: CourseCatalogItem | null;
  selectedUnits: number[];
  onChangeUnits: (units: number[], examLabel?: string) => void;
  activeCycle?: string;
  onCycleChange?: (cycle: string) => void;
  inScopeTopicCount?: number;
  totalTopicCount?: number;
}

export function ExamUnitSelector({
  course,
  selectedUnits,
  onChangeUnits,
  activeCycle = "ENDSEM",
  onCycleChange,
  inScopeTopicCount,
  totalTopicCount,
}: ExamUnitSelectorProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [classAnnouncements, setClassAnnouncements] = useState<ExamAnnouncementItem[]>([]);
  const [customExamTitle, setCustomExamTitle] = useState<string | null>(null);

  const totalUnits = course?.units?.length || 5;
  const units: CourseUnitCatalogItem[] = course?.units && course.units.length > 0
    ? course.units
    : Array.from({ length: totalUnits }, (_, i) => ({
        number: i + 1,
        name: `Unit ${i + 1}`,
        topicCount: 0,
        topics: [],
      }));

  // Fetch student announcements for this course
  useEffect(() => {
    if (!course?.id) return;
    let active = true;
    getExamAnnouncementsForCourse(course.id, 3)
      .then((items) => {
        if (active) setClassAnnouncements(items);
      })
      .catch(() => {});

    // Check localStorage for saved custom exam scope
    try {
      const saved = localStorage.getItem(`markmint_exam_scope_${course.id}`);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.examTitle) setCustomExamTitle(parsed.examTitle);
      }
    } catch (e) {}

    return () => {
      active = false;
    };
  }, [course?.id]);

  const toggleUnit = (num: number) => {
    let newUnits: number[];
    if (selectedUnits.includes(num)) {
      newUnits = selectedUnits.filter((u) => u !== num);
      if (newUnits.length === 0) newUnits = [num]; // Keep at least one
    } else {
      newUnits = [...selectedUnits, num].sort((a, b) => a - b);
    }
    setCustomExamTitle(null);
    onChangeUnits(newUnits, "Custom Units");
  };

  const handlePresetSelect = (preset: "ALL" | "CT1" | "CT2") => {
    setCustomExamTitle(null);
    if (preset === "ALL") {
      const all = units.map((u) => u.number);
      onChangeUnits(all, "End Semester");
      if (onCycleChange) onCycleChange("ENDSEM");
    } else if (preset === "CT1") {
      const ct1Units = [1, 2].filter((n) => n <= totalUnits);
      onChangeUnits(ct1Units, "Cycle Test 1");
      if (onCycleChange) onCycleChange("CT1");
    } else if (preset === "CT2") {
      const ct2Units = [3, 4].filter((n) => n <= totalUnits);
      onChangeUnits(ct2Units, "Cycle Test 2");
      if (onCycleChange) onCycleChange("CT2");
    }
  };

  const isAllSelected = selectedUnits.length === totalUnits;
  const isCT1Preset = selectedUnits.length === 2 && selectedUnits[0] === 1 && selectedUnits[1] === 2;
  const isCT2Preset = selectedUnits.length === 2 && selectedUnits[0] === 3 && selectedUnits[1] === 4;
  const isCustomPreset = !isAllSelected && !isCT1Preset && !isCT2Preset;

  const activeAnnouncement = classAnnouncements.length > 0 ? classAnnouncements[0] : null;

  return (
    <div className="space-y-3.5 p-4 sm:p-5 rounded-2xl bg-card border border-border/80 shadow-xs">
      {/* Top Row: Presets + Custom Contribution CTA */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center text-accent">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-foreground">Exam Scope &amp; Target Units</h3>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-muted text-muted-foreground border border-border/50">
                {customExamTitle || (isAllSelected ? "Full Syllabus" : isCT1Preset ? "CT1 Scope" : isCT2Preset ? "CT2 Scope" : `Custom (${selectedUnits.length} Units)`)}
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              Select which units are appearing in your exam. Forecasts and practice will focus strictly on those units.
            </p>
          </div>
        </div>

        {/* Action Button: "Let Us Know Which Exam That Is" */}
        <button
          type="button"
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center justify-center gap-2 px-3.5 py-2 rounded-xl bg-accent/10 hover:bg-accent/20 text-accent border border-accent/20 text-xs font-semibold transition-all cursor-pointer shadow-2xs self-start md:self-auto"
        >
          <Megaphone className="w-3.5 h-3.5" />
          <span>Tell us your exam portion</span>
        </button>
      </div>

      {/* Preset Cycle Buttons */}
      <div className="flex flex-wrap items-center gap-1.5 p-1 bg-muted/20 rounded-xl border border-border/50 text-xs w-fit">
        <button
          type="button"
          onClick={() => handlePresetSelect("ALL")}
          className={`px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer ${
            isAllSelected
              ? "bg-accent text-accent-foreground font-semibold shadow-2xs"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          All Units (EndSem)
        </button>
        <button
          type="button"
          onClick={() => handlePresetSelect("CT1")}
          className={`px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer ${
            isCT1Preset
              ? "bg-accent text-accent-foreground font-semibold shadow-2xs"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          CT1 (Units 1 &amp; 2)
        </button>
        <button
          type="button"
          onClick={() => handlePresetSelect("CT2")}
          className={`px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer ${
            isCT2Preset
              ? "bg-accent text-accent-foreground font-semibold shadow-2xs"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          CT2 (Units 3 &amp; 4)
        </button>
        {isCustomPreset && (
          <span className="px-3 py-1.5 rounded-lg font-semibold bg-accent text-accent-foreground shadow-2xs">
            Custom Selection ({selectedUnits.join(", ")})
          </span>
        )}
      </div>

      {/* Interactive Individual Unit Chips */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2 pt-1">
        {units.map((unit) => {
          const isSelected = selectedUnits.includes(unit.number);
          return (
            <button
              key={unit.number}
              type="button"
              onClick={() => toggleUnit(unit.number)}
              title={unit.name}
              className={`p-2.5 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between gap-1.5 group ${
                isSelected
                  ? "bg-accent/15 border-accent text-foreground shadow-2xs"
                  : "bg-muted/10 border-border/60 hover:bg-muted/25 text-muted-foreground opacity-75 hover:opacity-100"
              }`}
            >
              <div className="flex items-center justify-between w-full">
                <span className="text-[11px] font-bold font-mono px-1.5 py-0.5 rounded bg-background/80 border border-border/60 text-foreground">
                  Unit {unit.number}
                </span>
                <div
                  className={`w-4 h-4 rounded-md flex items-center justify-center transition-colors ${
                    isSelected ? "bg-accent text-accent-foreground" : "border border-border/80 bg-background"
                  }`}
                >
                  {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                </div>
              </div>
              <div className="text-[11px] font-semibold text-foreground line-clamp-1 leading-tight">
                {unit.name}
              </div>
              {unit.topicCount > 0 && (
                <div className="text-[10px] text-muted-foreground">
                  {unit.topicCount} syllabus topics
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Classmate Announcement Banner (if available) */}
      {activeAnnouncement && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 rounded-xl bg-accent/5 border border-accent/20 text-xs">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-accent shrink-0" />
            <span className="text-foreground">
              <strong>Classmate Announcement:</strong> {activeAnnouncement.batch_department ? `${activeAnnouncement.batch_department} reported ` : "Reported "}
              {activeAnnouncement.exam_title || activeAnnouncement.exam_type} covers{" "}
              <strong>Units {activeAnnouncement.units.join(", ")}</strong>.
            </span>
          </div>
          <button
            type="button"
            onClick={() => {
              setCustomExamTitle(activeAnnouncement.exam_title || activeAnnouncement.exam_type);
              onChangeUnits(activeAnnouncement.units, activeAnnouncement.exam_title || activeAnnouncement.exam_type);
            }}
            className="text-xs font-bold text-accent hover:underline self-start sm:self-auto shrink-0"
          >
            Apply This Portion &rarr;
          </button>
        </div>
      )}

      {/* Scope Status Info Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-border/40 text-[11px] text-muted-foreground">
        <div>
          Active exam portion:{" "}
          <strong className="text-foreground font-semibold">
            {isAllSelected ? "All 5 Units" : `Units ${selectedUnits.join(", ")}`}
          </strong>
          {inScopeTopicCount != null && (
            <span>
              {" "}• Showing <strong className="text-foreground">{inScopeTopicCount}</strong> high-yield topics
              {totalTopicCount ? ` of ${totalTopicCount} total` : ""}
            </span>
          )}
        </div>
        <div className="text-[10px] text-muted-foreground">
          Tip: Tap any unit chip to add or remove it from your practice test.
        </div>
      </div>

      {/* Modal Dialog */}
      <StudentExamScopeModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        course={course}
        currentUnits={selectedUnits}
        onApplyUnits={(units, title) => {
          setCustomExamTitle(title);
          onChangeUnits(units, title);
        }}
      />
    </div>
  );
}
