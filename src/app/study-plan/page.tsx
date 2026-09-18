"use client";

import { useState, useEffect } from "react";
import { SubjectSelector } from "@/components/subject-selector";
import { CurriculumSubject, IntelligenceSnapshot } from "@/lib/types";
import { getIntelligenceSnapshot, updateStudyProgress } from "@/lib/api";
import { MathText } from "@/components/ui/math-text";
import { Loader2, CheckCircle2, Circle, ArrowRight } from "lucide-react";
import Link from "next/link";

export default function StudyPlanPage() {
  const [selectedSubject, setSelectedSubject] = useState<CurriculumSubject | null>(null);
  const [snapshot, setSnapshot] = useState<IntelligenceSnapshot | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  useEffect(() => {
    if (!selectedSubject?.course_id || selectedSubject.status !== "MATCHED" || !selectedSubject.has_exams) {
      setSnapshot(null);
      return;
    }

    let active = true;
    setIsAnalyzing(true);
    
    getIntelligenceSnapshot(selectedSubject.course_id, undefined, undefined, "anonymous")
      .then(data => {
        if (active) setSnapshot(data);
      })
      .catch(console.error)
      .finally(() => {
        if (active) setIsAnalyzing(false);
      });

    return () => { active = false; };
  }, [selectedSubject]);

  const handleToggleTopicStatus = async (topicName: string, currentStatus?: string) => {
    if (!selectedSubject?.course_id) return;
    const nextStatus = currentStatus === "COMPLETED" ? "NOT_STARTED" : "COMPLETED";
    try {
      await updateStudyProgress(selectedSubject.course_id, {
        topic: topicName,
        action: nextStatus === "COMPLETED" ? "complete_topic" : "reset_topic",
      });
      const updated = await getIntelligenceSnapshot(selectedSubject.course_id, undefined, undefined, "anonymous");
      setSnapshot(updated);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex flex-col gap-8 pb-20">
      {/* Header Context */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-border/50">
        <div className="space-y-4">
          <div>
            <h1 className="text-3xl font-black text-foreground tracking-tight">Your Study Plan</h1>
            <p className="text-muted-foreground mt-1">Study these high-yield topics first.</p>
          </div>
          <SubjectSelector 
            selectedSubject={selectedSubject} 
            onSelect={(subj) => setSelectedSubject(subj)} 
          />
        </div>
      </div>

      {!selectedSubject ? (
        <div className="h-[400px] flex flex-col items-center justify-center text-center text-muted-foreground">
          <p>Select a subject to view your study plan.</p>
        </div>
      ) : isAnalyzing ? (
        <div className="h-[400px] flex flex-col items-center justify-center gap-4 text-muted-foreground bg-card rounded-3xl border border-border">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="font-medium tracking-widest uppercase text-sm">Generating Plan...</p>
        </div>
      ) : snapshot ? (
        <div className="max-w-3xl space-y-12">
          
          {/* Progress Header */}
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">Study these first</h2>
              <p className="text-muted-foreground">Topics ordered by historical recurrence and weight.</p>
            </div>
            {snapshot.coverage_summary && (
              <div className="text-right">
                <div className="text-3xl font-black text-verified">{snapshot.coverage_summary.student_preparation_coverage}%</div>
                <div className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Prepared</div>
              </div>
            )}
          </div>

          <div className="space-y-4">
            {snapshot.predictions.map((p, idx) => {
              const priorityInfo = p.priority_info;
              const isCompleted = priorityInfo?.student_status === "COMPLETED";
              
              return (
                <div 
                  key={idx}
                  className={`flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl border transition-all ${
                    isCompleted 
                      ? "bg-secondary/50 border-border/50 opacity-60" 
                      : "bg-card border-border hover:border-primary/30 shadow-sm"
                  }`}
                >
                  <div className="flex items-start gap-4">
                    <div className="mt-1 font-mono text-muted-foreground font-bold text-sm">
                      {String(idx + 1).padStart(2, '0')}
                    </div>
                    <div>
                      <h3 className={`text-lg font-bold ${isCompleted ? "line-through text-muted-foreground" : "text-foreground"}`}>
                        <MathText content={p.name} />
                      </h3>
                      {!isCompleted && (
                        <div className="text-sm font-medium text-primary mt-1">
                          {p.category === "family" ? "Recurring Pattern" : "High Priority"}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3 self-start sm:self-auto ml-10 sm:ml-0">
                    <button
                      onClick={() => handleToggleTopicStatus(p.name, priorityInfo?.student_status)}
                      className={`px-4 py-2 rounded-xl font-bold transition-colors flex items-center gap-2 text-sm ${
                        isCompleted
                          ? "bg-verified/10 text-verified hover:bg-verified/20"
                          : "bg-primary text-primary-foreground hover:bg-primary/90"
                      }`}
                    >
                      {isCompleted ? <CheckCircle2 className="w-4 h-4" /> : <Circle className="w-4 h-4" />}
                      <span>{isCompleted ? "Mastered" : "Study"}</span>
                    </button>
                    {!isCompleted && (
                      <Link
                        href={`/practice?subject=${selectedSubject.course_id}`}
                        className="p-2 rounded-xl text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
                      >
                        <ArrowRight className="w-5 h-5" />
                      </Link>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : null}
    </div>
  );
}
