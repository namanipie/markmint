"use client";

import React, { useState, useEffect } from "react";
import { Plus, Trash2, Copy, Check, RotateCcw, Award, TrendingUp, Layers } from "lucide-react";
import { toast } from "sonner";

interface SemesterGPA {
  id: string;
  semesterName: string;
  sgpa: number;
  credits: number;
}

export function CgpaCalculator() {
  const [semesters, setSemesters] = useState<SemesterGPA[]>([
    { id: "1", semesterName: "Semester 1", sgpa: 8.5, credits: 21 },
    { id: "2", semesterName: "Semester 2", sgpa: 8.8, credits: 22 },
  ]);
  const [copied, setCopied] = useState(false);

  // Load from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem("mintai_cgpa_memory");
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setSemesters(parsed);
        }
      }
    } catch {
      // ignore storage errors
    }
  }, []);

  // Save to localStorage
  useEffect(() => {
    try {
      localStorage.setItem("mintai_cgpa_memory", JSON.stringify(semesters));
    } catch {
      // ignore
    }
  }, [semesters]);

  const addSemester = () => {
    const nextNum = semesters.length + 1;
    setSemesters([
      ...semesters,
      {
        id: Math.random().toString(),
        semesterName: `Semester ${nextNum}`,
        sgpa: 8.0,
        credits: 21,
      },
    ]);
  };

  const removeSemester = (id: string) => {
    if (semesters.length <= 1) {
      toast("Keep at least one semester in the simulator.");
      return;
    }
    setSemesters(semesters.filter((s) => s.id !== id));
  };

  const updateSemester = (id: string, field: "sgpa" | "credits" | "semesterName", val: any) => {
    setSemesters(
      semesters.map((s) => (s.id === id ? { ...s, [field]: val } : s))
    );
  };

  const resetSemesters = () => {
    setSemesters([
      { id: "1", semesterName: "Semester 1", sgpa: 8.5, credits: 21 },
      { id: "2", semesterName: "Semester 2", sgpa: 8.8, credits: 22 },
    ]);
    toast("Reset to default semester template.");
  };

  // Formula: CGPA = Sum(SGPA_i * Credits_i) / Sum(Credits_i)
  const totalCredits = semesters.reduce((acc, curr) => acc + (Number(curr.credits) || 0), 0);
  const totalWeightedPoints = semesters.reduce(
    (acc, curr) => acc + (Number(curr.sgpa) || 0) * (Number(curr.credits) || 0),
    0
  );
  const cgpa = totalCredits > 0 ? (totalWeightedPoints / totalCredits).toFixed(2) : "0.00";

  const copyResults = () => {
    navigator.clipboard.writeText(`MintAI Cumulative GPA: ${cgpa} across ${totalCredits} credits.`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast("CGPA summary copied to clipboard.");
  };

  return (
    <div className="w-full max-w-3xl mx-auto space-y-6">
      <div className="p-6 md:p-8 rounded-3xl bg-card border border-border shadow-xs space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-border/60">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="p-2 rounded-xl bg-accent/15 text-accent">
                <Award className="w-5 h-5" />
              </span>
              <h2 className="text-xl font-bold tracking-tight text-foreground">
                Cumulative CGPA Forecaster
              </h2>
            </div>
            <p className="text-xs text-muted-foreground">
              Calculate weighted Cumulative Grade Point Average across completed and upcoming semesters.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={resetSemesters}
              className="p-2 rounded-xl border border-border/80 text-muted-foreground hover:text-foreground hover:bg-muted/20 text-xs font-semibold transition-all cursor-pointer inline-flex items-center gap-1.5"
              title="Reset Semesters"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>
            <button
              type="button"
              onClick={copyResults}
              className="p-2 px-3 rounded-xl bg-muted/30 border border-border/80 text-foreground text-xs font-semibold hover:bg-muted/50 transition-all cursor-pointer inline-flex items-center gap-1.5"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-accent" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? "Copied" : "Copy"}</span>
            </button>
          </div>
        </div>

        {/* Semester Table Header */}
        <div className="grid grid-cols-12 gap-3 px-2 text-[11px] font-bold text-muted-foreground uppercase tracking-wider">
          <div className="col-span-5">Semester Label</div>
          <div className="col-span-3 text-center">Semester Credits</div>
          <div className="col-span-3 text-center">Earned SGPA</div>
          <div className="col-span-1"></div>
        </div>

        {/* Semesters Rows */}
        <div className="space-y-2.5">
          {semesters.map((s, idx) => (
            <div key={s.id} className="grid grid-cols-12 gap-3 items-center p-2 rounded-2xl bg-muted/10 border border-border/50">
              <div className="col-span-5">
                <input
                  type="text"
                  value={s.semesterName}
                  onChange={(e) => updateSemester(s.id, "semesterName", e.target.value)}
                  className="w-full bg-background border border-border rounded-xl px-3 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-accent"
                  placeholder={`Semester ${idx + 1}`}
                />
              </div>

              <div className="col-span-3">
                <input
                  type="number"
                  min="1"
                  max="40"
                  value={s.credits}
                  onChange={(e) => updateSemester(s.id, "credits", parseFloat(e.target.value) || 0)}
                  className="w-full bg-background border border-border rounded-xl px-3 py-2 text-xs font-mono font-bold text-center focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>

              <div className="col-span-3">
                <input
                  type="number"
                  min="0"
                  max="10"
                  step="0.01"
                  value={s.sgpa}
                  onChange={(e) => updateSemester(s.id, "sgpa", parseFloat(e.target.value) || 0)}
                  className="w-full bg-background border border-border rounded-xl px-3 py-2 text-xs font-mono font-bold text-center text-accent focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>

              <div className="col-span-1 flex justify-center">
                <button
                  type="button"
                  onClick={() => removeSemester(s.id)}
                  className="p-1.5 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors cursor-pointer"
                  title="Remove Semester"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Add Semester Button */}
        <button
          type="button"
          onClick={addSemester}
          className="w-full py-3 rounded-2xl border-2 border-dashed border-border/80 hover:border-accent/50 hover:bg-accent/5 text-muted-foreground hover:text-foreground text-xs font-semibold transition-all flex items-center justify-center gap-2 cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>Add Next Semester</span>
        </button>

        {/* CGPA Summary Banner */}
        <div className="pt-6 border-t border-border/60 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              Cumulative Result
            </h3>
            <p className="text-xs text-muted-foreground font-mono">
              Formula: &Sigma;(SGPA &times; Credits) &divide; {totalCredits} Total Credits
            </p>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              <span className="text-[10px] font-mono text-muted-foreground block">WEIGHTED CGPA</span>
              <span className="text-4xl sm:text-5xl font-extrabold text-accent font-mono tracking-tight">
                {cgpa}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
