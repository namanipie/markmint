"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  X, 
  Calendar, 
  BookOpen, 
  Layers, 
  Send, 
  CheckCircle2, 
  Sparkles, 
  Megaphone,
  Check,
  AlertCircle,
  HelpCircle,
  Users
} from "lucide-react";
import { CourseCatalogItem } from "@/lib/courses";
import { submitExamAnnouncement } from "@/lib/api";

interface StudentExamScopeModalProps {
  isOpen: boolean;
  onClose: () => void;
  course: CourseCatalogItem | null;
  currentUnits: number[];
  onApplyUnits: (units: number[], examName: string) => void;
}

export function StudentExamScopeModal({
  isOpen,
  onClose,
  course,
  currentUnits,
  onApplyUnits,
}: StudentExamScopeModalProps) {
  const [examType, setExamType] = useState<string>("CT1");
  const [examTitle, setExamTitle] = useState<string>("");
  const [selectedUnits, setSelectedUnits] = useState<number[]>(currentUnits.length > 0 ? currentUnits : [1, 2]);
  const [batchDepartment, setBatchDepartment] = useState<string>("");
  const [examDate, setExamDate] = useState<string>("");
  const [notes, setNotes] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [isSuccess, setIsSuccess] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Sync with currentUnits when opened
  useEffect(() => {
    if (isOpen) {
      if (currentUnits.length > 0) {
        setSelectedUnits(currentUnits);
      }
      setIsSuccess(false);
      setErrorMessage(null);
    }
  }, [isOpen, currentUnits]);

  if (!isOpen || !course) return null;

  const totalUnits = course.units?.length || 5;
  const unitList = course.units && course.units.length > 0
    ? course.units
    : Array.from({ length: totalUnits }, (_, i) => ({
        number: i + 1,
        name: `Unit ${i + 1}`,
        topicCount: 0,
        topics: [],
      }));

  const toggleUnit = (num: number) => {
    setSelectedUnits((prev) =>
      prev.includes(num) ? prev.filter((u) => u !== num) : [...prev, num].sort((a, b) => a - b)
    );
  };

  const selectAll = () => {
    setSelectedUnits(unitList.map((u) => u.number));
  };

  const selectCT1 = () => {
    setSelectedUnits([1, 2].filter((n) => n <= totalUnits));
    setExamType("CT1");
    if (!examTitle) setExamTitle("Cycle Test 1");
  };

  const selectCT2 = () => {
    setSelectedUnits([3, 4].filter((n) => n <= totalUnits));
    setExamType("CT2");
    if (!examTitle) setExamTitle("Cycle Test 2");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedUnits.length === 0) {
      setErrorMessage("Please select at least one unit that will come in your exam.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    const title = examTitle.trim() || (
      examType === "CT1" ? "Cycle Test 1" :
      examType === "CT2" ? "Cycle Test 2" :
      examType === "MODEL" ? "Model Exam" :
      examType === "SURPRISE" ? "Surprise Assessment" :
      examType === "ENDSEM" ? "End Semester Exam" : "Upcoming Examination"
    );

    try {
      await submitExamAnnouncement({
        course_id: course.id,
        course_code: course.code,
        course_name: course.name,
        exam_type: examType,
        exam_title: title,
        units: selectedUnits,
        batch_department: batchDepartment.trim() || undefined,
        announced_date: examDate || undefined,
        notes: notes.trim() || undefined,
      });

      // Save to localStorage for quick restore
      try {
        localStorage.setItem(
          `markmint_exam_scope_${course.id}`,
          JSON.stringify({
            units: selectedUnits,
            examTitle: title,
            updatedAt: new Date().toISOString(),
          })
        );
      } catch (err) {
        // ignore localStorage error
      }

      setIsSuccess(true);
      setTimeout(() => {
        onApplyUnits(selectedUnits, title);
        onClose();
      }, 1400);
    } catch (err: any) {
      // Even if network fails, apply units locally so student is never blocked
      onApplyUnits(selectedUnits, title);
      setIsSuccess(true);
      setTimeout(() => {
        onClose();
      }, 1000);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-background/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        className="relative w-full max-w-xl bg-card border border-border/80 rounded-2xl shadow-2xl overflow-hidden z-10 flex flex-col max-h-[90vh]"
      >
        {/* Header */}
        <div className="p-5 sm:p-6 border-b border-border/60 bg-card shrink-0 flex items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-accent/10 border border-accent/20 text-[11px] font-semibold text-accent uppercase tracking-wider">
              <Megaphone className="w-3 h-3" />
              <span>Exam Portion &amp; Timetable Contribution</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
              What exam are you preparing for?
            </h2>
            <p className="text-xs sm:text-sm text-muted-foreground">
              Select the units announced by your professor for <strong className="text-foreground">{course.name}</strong>.
              MarkMint will tune questions and forecasts for your exact portions!
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-xl transition-colors shrink-0 cursor-pointer"
            aria-label="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Form Body */}
        {isSuccess ? (
          <div className="p-8 text-center space-y-4">
            <div className="w-14 h-14 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 mx-auto flex items-center justify-center">
              <CheckCircle2 className="w-8 h-8 animate-bounce" />
            </div>
            <div className="space-y-1.5">
              <h3 className="text-lg font-bold text-foreground">Exam Portions Calibrated!</h3>
              <p className="text-xs text-muted-foreground max-w-md mx-auto">
                Thank you for contributing! Your forecast and practice questions are now tailored strictly to{" "}
                <strong className="text-foreground">Units {selectedUnits.join(", ")}</strong>.
              </p>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-5 sm:p-6 overflow-y-auto space-y-5">
            {/* 1. Exam Type Presets */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">
                1. Select Exam Type
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {[
                  { id: "CT1", label: "Cycle Test 1 (CT1)", helper: "Units 1 & 2" },
                  { id: "CT2", label: "Cycle Test 2 (CT2)", helper: "Units 3 & 4" },
                  { id: "SURPRISE", label: "Surprise Test", helper: "Specific Unit" },
                  { id: "MODEL", label: "Model Exam", helper: "Full/Selected" },
                  { id: "ENDSEM", label: "Semester End", helper: "All Units 1-5" },
                  { id: "OTHER", label: "Custom / Retest", helper: "Custom Scope" },
                ].map((type) => {
                  const isSelected = examType === type.id;
                  return (
                    <button
                      key={type.id}
                      type="button"
                      onClick={() => {
                        setExamType(type.id);
                        if (type.id === "CT1") selectCT1();
                        else if (type.id === "CT2") selectCT2();
                        else if (type.id === "ENDSEM") selectAll();
                      }}
                      className={`p-2.5 rounded-xl border text-left transition-all cursor-pointer ${
                        isSelected
                          ? "bg-accent/15 border-accent text-foreground shadow-2xs font-semibold"
                          : "bg-muted/15 border-border/60 hover:bg-muted/30 text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      <div className="text-xs font-bold text-foreground">{type.label}</div>
                      <div className="text-[10px] text-muted-foreground">{type.helper}</div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* 2. Interactive Unit Selector Checkboxes */}
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">
                  2. Select Units In Your Exam Portion
                </label>
                <div className="flex items-center gap-2 text-[11px]">
                  <button
                    type="button"
                    onClick={selectAll}
                    className="text-accent hover:underline font-medium"
                  >
                    Select All
                  </button>
                  <span className="text-muted-foreground">•</span>
                  <button
                    type="button"
                    onClick={selectCT1}
                    className="text-muted-foreground hover:text-foreground font-medium"
                  >
                    Units 1 &amp; 2
                  </button>
                  <span className="text-muted-foreground">•</span>
                  <button
                    type="button"
                    onClick={selectCT2}
                    className="text-muted-foreground hover:text-foreground font-medium"
                  >
                    Units 3 &amp; 4
                  </button>
                </div>
              </div>

              <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                {unitList.map((unit) => {
                  const isChecked = selectedUnits.includes(unit.number);
                  return (
                    <div
                      key={unit.number}
                      onClick={() => toggleUnit(unit.number)}
                      className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                        isChecked
                          ? "bg-accent/10 border-accent/80 text-foreground shadow-2xs"
                          : "bg-muted/10 border-border/60 hover:bg-muted/20 text-muted-foreground"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-5 h-5 rounded-md flex items-center justify-center transition-colors ${
                            isChecked
                              ? "bg-accent text-accent-foreground font-bold text-xs"
                              : "border border-border bg-background"
                          }`}
                        >
                          {isChecked && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                        </div>
                        <div>
                          <div className="text-xs font-semibold text-foreground">
                            Unit {unit.number}: {unit.name}
                          </div>
                          {unit.topicCount > 0 && (
                            <div className="text-[11px] text-muted-foreground">
                              {unit.topicCount} cataloged syllabus topics
                            </div>
                          )}
                        </div>
                      </div>
                      <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-muted/40 text-muted-foreground">
                        U{unit.number}
                      </span>
                    </div>
                  );
                })}
              </div>

              {errorMessage && (
                <div className="flex items-center gap-2 p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-xs">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{errorMessage}</span>
                </div>
              )}
            </div>

            {/* 3. Optional Class Context & Notes */}
            <div className="space-y-3 pt-2 border-t border-border/40">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                <Users className="w-3.5 h-3.5 text-accent" />
                <span>3. Help Classmates (Optional Details)</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] text-muted-foreground block mb-1">
                    Branch / Batch / Section
                  </label>
                  <input
                    type="text"
                    value={batchDepartment}
                    onChange={(e) => setBatchDepartment(e.target.value)}
                    placeholder="e.g. CSE Core Batch 2, ECE Sec A"
                    className="w-full bg-muted/20 border border-border/60 rounded-xl px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:ring-1 focus:ring-accent focus:outline-none"
                  />
                </div>

                <div>
                  <label className="text-[11px] text-muted-foreground block mb-1">
                    Exam Date
                  </label>
                  <input
                    type="date"
                    value={examDate}
                    onChange={(e) => setExamDate(e.target.value)}
                    className="w-full bg-muted/20 border border-border/60 rounded-xl px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:ring-1 focus:ring-accent focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] text-muted-foreground block mb-1">
                  Faculty Instructions / Portion Notes
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. Professor mentioned only Cayley-Hamilton Theorem and first 3 topics of Unit 2 will be tested."
                  rows={2}
                  className="w-full bg-muted/20 border border-border/60 rounded-xl px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:ring-1 focus:ring-accent focus:outline-none resize-none"
                />
              </div>
            </div>

            {/* Submit & Apply Buttons */}
            <div className="pt-3 border-t border-border/50 flex flex-col sm:flex-row items-center justify-between gap-3">
              <div className="text-xs text-muted-foreground">
                Scope: <strong className="text-foreground">{selectedUnits.length} unit(s)</strong> selected
              </div>

              <div className="flex items-center gap-2 w-full sm:w-auto">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2.5 rounded-xl border border-border hover:bg-muted/40 text-xs font-semibold text-muted-foreground hover:text-foreground transition-all cursor-pointer flex-1 sm:flex-initial"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || selectedUnits.length === 0}
                  className="px-5 py-2.5 rounded-xl bg-accent text-accent-foreground text-xs font-bold hover:bg-accent/90 transition-all cursor-pointer shadow-xs flex items-center justify-center gap-2 flex-1 sm:flex-initial disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <span>Saving...</span>
                  ) : (
                    <>
                      <Send className="w-3.5 h-3.5" />
                      <span>Calibrate &amp; Apply Scope</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>
        )}
      </motion.div>
    </div>
  );
}
