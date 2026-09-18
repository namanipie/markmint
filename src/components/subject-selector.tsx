"use client";

import { useState, useEffect } from "react";
import { 
  getCurriculumBranches, 
  getCurriculumSemesters, 
  getCurriculumSubjects 
} from "@/lib/api";
import { CurriculumSubject } from "@/lib/types";
import { Search, ChevronRight, BookOpen, AlertCircle, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface SubjectSelectorProps {
  selectedSubject: CurriculumSubject | null;
  onSelect: (subject: CurriculumSubject) => void;
  branchOverride?: string;
  semesterOverride?: string;
}

export function SubjectSelector({ selectedSubject, onSelect }: SubjectSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [step, setStep] = useState<"BRANCH" | "SEMESTER" | "SUBJECT">("BRANCH");
  
  const [branches, setBranches] = useState<string[]>([]);
  const [semesters, setSemesters] = useState<number[]>([]);
  const [subjects, setSubjects] = useState<CurriculumSubject[]>([]);
  
  const [activeBranch, setActiveBranch] = useState<string>("");
  const [activeSemester, setActiveSemester] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isOpen && branches.length === 0) {
      setIsLoading(true);
      getCurriculumBranches()
        .then(setBranches)
        .catch(console.error)
        .finally(() => setIsLoading(false));
    }
  }, [isOpen, branches.length]);

  useEffect(() => {
    if (activeBranch) {
      setIsLoading(true);
      getCurriculumSemesters(activeBranch)
        .then(setSemesters)
        .catch(console.error)
        .finally(() => setIsLoading(false));
    }
  }, [activeBranch]);

  useEffect(() => {
    if (activeBranch && activeSemester) {
      setIsLoading(true);
      getCurriculumSubjects(activeBranch, activeSemester)
        .then(setSubjects)
        .catch(console.error)
        .finally(() => setIsLoading(false));
    }
  }, [activeBranch, activeSemester]);

  const handleSelectBranch = (branch: string) => {
    setActiveBranch(branch);
    setSearchQuery("");
    setStep("SEMESTER");
  };

  const handleSelectSemester = (sem: number) => {
    setActiveSemester(String(sem));
    setSearchQuery("");
    setStep("SUBJECT");
  };

  const handleSelectSubject = (sub: CurriculumSubject) => {
    onSelect(sub);
    setIsOpen(false);
    setTimeout(() => setStep("BRANCH"), 300);
  };

  const filteredBranches = branches.filter(b => b.toLowerCase().includes(searchQuery.toLowerCase()));
  const filteredSubjects = subjects.filter(s => 
    s.subject_name.toLowerCase().includes(searchQuery.toLowerCase()) || 
    (s.canonical_code && s.canonical_code.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <>
      <button 
        onClick={() => setIsOpen(true)}
        className="w-full sm:w-auto min-w-[280px] bg-card hover:bg-secondary transition-colors border border-border shadow-sm rounded-xl p-4 text-left flex flex-col gap-1 cursor-pointer group"
      >
        <span className="text-[10px] uppercase tracking-widest text-muted-foreground font-semibold">Your Subject</span>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          {selectedSubject ? (
            <div>
              <div className="font-bold text-base text-foreground leading-tight">{selectedSubject.subject_name}</div>
              <div className="text-xs text-muted-foreground font-mono mt-0.5">
                {selectedSubject.canonical_code && `[${selectedSubject.canonical_code}] `}
                Semester {activeSemester || "Selected"}
              </div>
            </div>
          ) : (
            <div className="font-bold text-base text-muted-foreground">Select a course to begin</div>
          )}
          <div className="text-xs font-semibold text-primary bg-primary/10 px-2 py-1 rounded self-start sm:self-auto group-hover:bg-primary/20 transition-colors">
            Change
          </div>
        </div>
      </button>

      <AnimatePresence>
        {isOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }} 
              animate={{ opacity: 1 }} 
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="absolute inset-0 bg-background/80 backdrop-blur-sm"
            />
            
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="relative w-full max-w-xl bg-card border border-border rounded-2xl shadow-xl overflow-hidden flex flex-col max-h-[80vh]"
            >
              <div className="p-5 pb-3 border-b border-border/50 bg-background/50">
                <div className="flex justify-between items-center mb-2">
                  <h2 className="text-lg font-bold">
                    {step === "BRANCH" && "Select Academic Branch"}
                    {step === "SEMESTER" && "Select Semester"}
                    {step === "SUBJECT" && "Select Course"}
                  </h2>
                  <button onClick={() => setIsOpen(false)} className="p-1.5 rounded-md hover:bg-secondary text-muted-foreground">
                    <X className="w-5 h-5" />
                  </button>
                </div>
                
                {(step === "SEMESTER" || step === "SUBJECT") && (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground mt-2 font-medium">
                    <button onClick={() => setStep("BRANCH")} className="hover:text-foreground hover:underline">
                      {activeBranch || "Branch"}
                    </button>
                    <ChevronRight className="w-3 h-3" />
                    {step === "SUBJECT" && (
                      <>
                        <button onClick={() => setStep("SEMESTER")} className="hover:text-foreground hover:underline">
                          Sem {activeSemester}
                        </button>
                        <ChevronRight className="w-3 h-3" />
                        <span className="text-foreground">Course</span>
                      </>
                    )}
                  </div>
                )}
                
                {(step === "BRANCH" || step === "SUBJECT") && (
                  <div className="relative mt-3">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <input 
                      type="text"
                      placeholder={step === "BRANCH" ? "Search branches..." : "Search courses by name or code..."}
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full bg-background border border-border rounded-lg pl-9 pr-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                  </div>
                )}
              </div>
              
              <div className="flex-1 overflow-y-auto p-2">
                {isLoading ? (
                  <div className="flex h-32 items-center justify-center text-muted-foreground text-sm font-medium">
                    <div className="animate-pulse">Loading directory...</div>
                  </div>
                ) : (
                  <AnimatePresence mode="wait">
                    <motion.div 
                      key={step}
                      initial={{ opacity: 0, x: 10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      transition={{ duration: 0.2 }}
                      className="flex flex-col gap-1"
                    >
                      {step === "BRANCH" && (
                        filteredBranches.map(b => (
                          <button
                            key={b}
                            onClick={() => handleSelectBranch(b)}
                            className="text-left px-4 py-3 rounded-xl hover:bg-secondary flex items-center justify-between group transition-colors"
                          >
                            <span className="font-medium">{b}</span>
                            <ChevronRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                          </button>
                        ))
                      )}
                      
                      {step === "SEMESTER" && (
                        <div className="grid grid-cols-2 gap-2 p-2">
                          {semesters.map(s => (
                            <button
                              key={s}
                              onClick={() => handleSelectSemester(s)}
                              className="p-4 rounded-xl border border-border bg-background hover:border-primary hover:bg-primary/5 transition-colors text-center flex flex-col items-center justify-center gap-1"
                            >
                              <span className="text-2xl font-bold text-foreground">{s}</span>
                              <span className="text-[10px] uppercase tracking-widest text-muted-foreground font-semibold">Semester</span>
                            </button>
                          ))}
                        </div>
                      )}
                      
                      {step === "SUBJECT" && (
                        filteredSubjects.length === 0 ? (
                          <div className="flex flex-col items-center justify-center h-32 text-center text-muted-foreground py-10">
                            <BookOpen className="w-8 h-8 mb-2 opacity-20" />
                            <p className="text-sm">No courses found matching "{searchQuery}"</p>
                          </div>
                        ) : (
                          filteredSubjects.map(sub => (
                            <button
                              key={sub.curriculum_id}
                              onClick={() => handleSelectSubject(sub)}
                              className={`text-left p-4 rounded-xl border mb-2 transition-colors flex flex-col gap-2 ${
                                sub.status === "MATCHED" && sub.has_exams 
                                  ? "border-border bg-background hover:border-primary/50 hover:bg-primary/5 cursor-pointer" 
                                  : "border-border/50 bg-background/50 hover:bg-secondary opacity-70 cursor-pointer"
                              }`}
                            >
                              <div>
                                <div className="font-bold text-sm text-foreground flex items-center gap-2">
                                  {sub.subject_name}
                                  {sub.status === "MATCHED" && sub.has_exams && (
                                    <span className="px-1.5 py-0.5 rounded-full bg-verified/10 text-verified text-[9px] uppercase tracking-wider">
                                      Verified
                                    </span>
                                  )}
                                </div>
                                <div className="text-xs text-muted-foreground font-mono mt-1">
                                  {sub.canonical_code && `[${sub.canonical_code}]`}
                                </div>
                              </div>
                              
                              {sub.status === "MATCHED" && sub.has_exams ? (
                                <div className="text-[11px] text-muted-foreground flex items-center gap-1.5">
                                  <BookOpen className="w-3.5 h-3.5 text-primary" />
                                  <span>{sub.exam_count} past papers • {sub.question_count} questions</span>
                                </div>
                              ) : sub.status === "AMBIGUOUS" ? (
                                <div className="text-[11px] text-warning flex items-center gap-1.5">
                                  <AlertCircle className="w-3 h-3" />
                                  <span>Ambiguous syllabus mapping</span>
                                </div>
                              ) : (
                                <div className="text-[11px] text-muted-foreground flex items-center gap-1.5">
                                  <AlertCircle className="w-3 h-3" />
                                  <span>No past papers available yet</span>
                                </div>
                              )}
                            </button>
                          ))
                        )
                      )}
                    </motion.div>
                  </AnimatePresence>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}
