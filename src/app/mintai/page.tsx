"use client";

import { useState, useEffect } from "react";
import { 
  getIntelligenceSnapshot, 
  getHistoricalQuestions,
  updateStudyProgress
} from "@/lib/api";
import { 
  CurriculumSubject, 
  IntelligenceSnapshot, 
  PredictionItem,
  HistoricalQuestion
} from "@/lib/types";
import { SubjectSelector } from "@/components/subject-selector";
import { PredictionCard } from "@/components/mintai/prediction-card";
import { FamilyEvidenceModal } from "@/components/analytics/family-evidence-modal";
import { TopicIntelligenceModal } from "@/components/analytics/topic-intelligence-modal";
import { Drawer } from "@/components/ui/drawer";
import { MathText } from "@/components/ui/math-text";
import { Loader2, Layers, History, Sparkles, BookOpen } from "lucide-react";
import Link from "next/link";

export default function MintAIPage() {
  const [selectedSubject, setSelectedSubject] = useState<CurriculumSubject | null>(null);
  const [snapshot, setSnapshot] = useState<IntelligenceSnapshot | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [mainView, setMainView] = useState<"forecast" | "repetition">("forecast");
  const [expandedTopic, setExpandedTopic] = useState<string | null>(null);

  // Modal States
  const [isQuestionsModalOpen, setIsQuestionsModalOpen] = useState(false);
  const [selectedTopicForQuestions, setSelectedTopicForQuestions] = useState<string | null>(null);
  const [historicalQuestions, setHistoricalQuestions] = useState<HistoricalQuestion[]>([]);
  const [isLoadingQuestions, setIsLoadingQuestions] = useState(false);
  
  const [isTopicModalOpen, setIsTopicModalOpen] = useState(false);
  const [selectedTopicIdForModal, setSelectedTopicIdForModal] = useState<number | string | null>(null);
  const [selectedTopicNameForModal, setSelectedTopicNameForModal] = useState<string>("");

  const [isFamilyModalOpen, setIsFamilyModalOpen] = useState(false);
  const [selectedFamilyIdForModal, setSelectedFamilyIdForModal] = useState<number | string | null>(null);
  const [selectedFamilyNameForModal, setSelectedFamilyNameForModal] = useState<string>("");

  // Fetch Snapshot when Subject changes
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

  const handleOpenFamilyEvidence = (familyId: number | string | null, familyName?: string) => {
    setSelectedFamilyIdForModal(familyId);
    setSelectedFamilyNameForModal(familyName || "");
    setIsFamilyModalOpen(true);
  };

  const handleOpenTopicIntelligence = (topicId?: number | string | null, topicName?: string) => {
    setSelectedTopicIdForModal(topicId || null);
    setSelectedTopicNameForModal(topicName || "");
    setIsTopicModalOpen(true);
  };

  const handleViewQuestions = async (topicName?: string, familyId?: number | null, familyName?: string) => {
    if (!selectedSubject?.course_id) return;
    setIsLoadingQuestions(true);
    setSelectedTopicForQuestions(familyName || topicName || null);
    setIsQuestionsModalOpen(true);
    
    try {
      const res = await getHistoricalQuestions(
        selectedSubject.course_id,
        familyId ? undefined : topicName,
        undefined,
        50,
        familyId ? { family_id: familyId } : (familyName ? { family_name: familyName } : undefined)
      );
      setHistoricalQuestions(res.questions || []);
    } catch (err) {
      console.error(err);
      setHistoricalQuestions([]);
    } finally {
      setIsLoadingQuestions(false);
    }
  };

  return (
    <div className="flex flex-col gap-8 pb-20">
      {/* Header Context */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-border/50">
        <div className="space-y-4">
          <div>
            <h1 className="text-3xl font-black text-foreground tracking-tight">MintAI Workspace</h1>
            <p className="text-muted-foreground mt-1">Syllabus topics + past exam evidence.</p>
          </div>
          <SubjectSelector 
            selectedSubject={selectedSubject} 
            onSelect={(subj) => setSelectedSubject(subj)} 
          />
        </div>
        
        {/* Top View Switcher */}
        {selectedSubject?.has_exams && snapshot && (
          <div className="flex bg-secondary p-1 rounded-xl">
            <button
              onClick={() => setMainView("forecast")}
              className={`px-6 py-2.5 rounded-lg text-sm font-bold transition-all ${
                mainView === "forecast" ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              What to Study
            </button>
            <button
              onClick={() => setMainView("repetition")}
              className={`px-6 py-2.5 rounded-lg text-sm font-bold transition-all ${
                mainView === "repetition" ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              What Repeated?
            </button>
          </div>
        )}
      </div>

      {/* Main Content Area */}
      {!selectedSubject ? (
        <div className="h-[400px] rounded-3xl flex flex-col justify-center p-8 lg:p-12 bg-card border border-border shadow-sm">
          <div className="max-w-xl">
            <h3 className="text-2xl font-bold text-foreground mb-4">Good morning. Let's get you ready.</h3>
            <p className="text-base text-muted-foreground mb-10 leading-relaxed">
              Select a course from the curriculum catalog above to unlock highly probable examination topics based on deterministic historical patterns.
            </p>
            <div className="flex flex-col gap-6">
              <div className="flex items-start gap-4">
                <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary font-bold text-sm shrink-0 border border-primary/20">1</div>
                <div>
                  <h4 className="text-sm font-bold text-foreground">Select Subject</h4>
                  <p className="text-sm text-muted-foreground mt-0.5">Choose your target course to extract the evidence pool.</p>
                </div>
              </div>
              <div className="flex items-start gap-4 opacity-70">
                <div className="flex items-center justify-center w-8 h-8 rounded-full bg-secondary text-muted-foreground font-bold text-sm shrink-0 border border-border">2</div>
                <div>
                  <h4 className="text-sm font-bold text-foreground">Analyze Patterns</h4>
                  <p className="text-sm text-muted-foreground mt-0.5">Explore recurring exam questions and historical frequency.</p>
                </div>
              </div>
              <div className="flex items-start gap-4 opacity-70">
                <div className="flex items-center justify-center w-8 h-8 rounded-full bg-secondary text-muted-foreground font-bold text-sm shrink-0 border border-border">3</div>
                <div>
                  <h4 className="text-sm font-bold text-foreground">Practice</h4>
                  <p className="text-sm text-muted-foreground mt-0.5">Focus on high-yield topics directly matched to syllabus objectives.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : isAnalyzing ? (
        <div className="h-[400px] flex flex-col items-center justify-center gap-4 text-muted-foreground bg-card rounded-3xl border border-border">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="font-medium tracking-widest uppercase text-sm">Processing Evidence Pool...</p>
        </div>
      ) : selectedSubject.status === "AMBIGUOUS" ? (
        <div className="h-[400px] bg-warning/5 border border-warning/20 rounded-3xl flex flex-col justify-center p-8 lg:p-12">
          <h3 className="text-xl font-bold text-warning mb-2">Ambiguous Course Mapping</h3>
          <p className="text-muted-foreground max-w-md">{selectedSubject.notes || "This course maps to multiple candidate subjects."}</p>
        </div>
      ) : selectedSubject.status === "MATCHED" && !selectedSubject.has_exams ? (
        <div className="h-[400px] bg-card border border-border rounded-3xl flex flex-col justify-center p-8 lg:p-12">
          <h3 className="text-xl font-bold text-foreground mb-2">Awaiting Past Papers</h3>
          <p className="text-muted-foreground max-w-md">The course is verified, but 0 historical examination papers are currently uploaded to extract patterns from.</p>
        </div>
      ) : snapshot && mainView === "forecast" ? (
        <div className="space-y-8">
          
          {/* Summary Dashboard Header */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-card p-5 rounded-2xl border border-border">
              <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">Past Papers</div>
              <div className="text-3xl font-black">{snapshot.exam_history?.historical_papers_analyzed || snapshot.exam_history?.total_papers || 0}</div>
            </div>
            <div className="bg-card p-5 rounded-2xl border border-border">
              <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">Topics Found</div>
              <div className="text-3xl font-black">{snapshot.predictions.length}</div>
            </div>
            <div className="bg-card p-5 rounded-2xl border border-border">
              <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">Total Questions</div>
              <div className="text-3xl font-black">{snapshot.exam_history?.total_questions || 0}</div>
            </div>
            <div className="bg-card p-5 rounded-2xl border border-border flex flex-col justify-between">
              <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">Your Progress</div>
              {snapshot.coverage_summary && snapshot.coverage_summary.mastered_topics > 0 ? (
                <div className="text-3xl font-black text-verified">{snapshot.coverage_summary.student_preparation_coverage}%</div>
              ) : (
                <div className="text-sm font-medium text-muted-foreground leading-tight">You haven't studied these topics yet.</div>
              )}
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-3 mb-2">
              <Sparkles className="w-5 h-5 text-primary" />
              <h2 className="text-2xl font-bold">What should I study first?</h2>
            </div>
            <p className="text-muted-foreground mb-6">Based on patterns in past exam papers.</p>
            
            <div className="grid grid-cols-1 gap-4">
              {snapshot.predictions.map((p, idx) => {
                const isFamilyMode = snapshot.prediction_mode === "family";
                const isFamily = p.category === "family";
                const priorityInfo = p.priority_info;
                
                return (
                  <PredictionCard
                    key={p.family_id ? `fam-${p.family_id}` : idx}
                    prediction={p}
                    isFamilyMode={isFamilyMode}
                    totalPapersAnalyzed={snapshot.exam_history?.historical_papers_analyzed || 1}
                    studentStatus={priorityInfo?.student_status}
                    onMarkDone={!isFamily ? () => handleToggleTopicStatus(p.name, priorityInfo?.student_status) : undefined}
                    onWhyClick={() => isFamily ? handleOpenFamilyEvidence(p.family_id ?? null, p.name) : handleOpenTopicIntelligence(p.topic_id ?? null, p.name)}
                    onPracticeClick={() => handleViewQuestions(isFamily ? undefined : p.name, isFamily ? (p.family_id ?? null) : undefined, p.name)}
                  />
                );
              })}
            </div>
          </div>
        </div>
      ) : snapshot && mainView === "repetition" ? (
        <div className="bg-card rounded-3xl border border-border p-8 lg:p-12">
          <div className="flex items-center gap-3 mb-2">
            <History className="w-6 h-6 text-primary" />
            <h2 className="text-2xl font-bold">What Repeated?</h2>
          </div>
          <p className="text-muted-foreground mb-10">See the questions and topics that have appeared across past exams.</p>
          
          <div className="relative border-l-2 border-border/50 ml-4 space-y-10 py-4">
            {snapshot.predictions
              .filter(p => (p.distinct_paper_count ?? 0) >= 2 || (p.historical_occurrences ?? 0) >= 2)
              .slice(0, 10)
              .map((p, i) => (
              <div key={i} className="relative pl-8">
                <div className="absolute -left-[9px] top-1.5 w-4 h-4 rounded-full bg-card border-2 border-primary" />
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <h4 className="text-lg font-bold text-foreground"><MathText content={p.name} /></h4>
                    <div className="text-sm font-medium text-primary mt-1">Appeared in {p.distinct_paper_count ?? p.papers_with_topic} papers</div>
                  </div>
                  <button 
                    onClick={() => p.category === "family" ? handleOpenFamilyEvidence(p.family_id ?? null, p.name) : handleOpenTopicIntelligence(p.topic_id ?? null, p.name)}
                    className="text-xs font-bold uppercase tracking-wider text-muted-foreground hover:text-foreground bg-secondary px-4 py-2 rounded-lg transition-colors self-start sm:self-auto"
                  >
                    View History
                  </button>
                </div>
              </div>
            ))}
            
            {snapshot.predictions.filter(p => (p.distinct_paper_count ?? 0) >= 2 || (p.historical_occurrences ?? 0) >= 2).length === 0 && (
              <div className="pl-8 text-muted-foreground">No significant repetitions found in the current evidence pool.</div>
            )}
          </div>
        </div>
      ) : null}

      {/* Historical Questions Drawer */}
      <Drawer
        isOpen={isQuestionsModalOpen}
        onClose={() => setIsQuestionsModalOpen(false)}
        title="Past Exam Questions"
        subtitle={selectedTopicForQuestions ? `Mapped to: ${selectedTopicForQuestions}` : `Course archive for: ${selectedSubject?.subject_name}`}
      >
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {isLoadingQuestions ? (
            <div className="flex justify-center py-10"><Loader2 className="w-8 h-8 animate-spin text-muted-foreground" /></div>
          ) : historicalQuestions.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">No questions found.</div>
          ) : (
            <div className="space-y-4">
              {historicalQuestions.map((q, i) => (
                <div key={i} className="bg-background rounded-2xl p-5 border border-border">
                  <div className="flex justify-between items-start mb-3">
                    <span className="text-xs font-bold uppercase text-muted-foreground">Question {i+1}</span>
                    {q.marks && <span className="text-xs font-bold bg-secondary px-2 py-1 rounded-md">{q.marks} Marks</span>}
                  </div>
                  <div className="text-sm leading-relaxed"><MathText content={q.original_text} /></div>
                  {(q.source_document_title || q.year) && (
                    <div className="mt-4 pt-4 border-t border-border/50 text-[11px] text-muted-foreground flex gap-4">
                      {q.year && <span>Year: {q.year}</span>}
                      {q.source_document_title && <span>Paper: {q.source_document_title}</span>}
                    </div>
                  )}
                </div>
              ))}
              
              <div className="pt-4">
                <Link href="/practice" className="block w-full text-center py-3 rounded-xl bg-primary text-primary-foreground font-bold hover:bg-primary/90 transition-colors">
                  Open in Practice Mode
                </Link>
              </div>
            </div>
          )}
        </div>
      </Drawer>

      {selectedSubject?.course_id && (
        <TopicIntelligenceModal
          isOpen={isTopicModalOpen}
          onClose={() => setIsTopicModalOpen(false)}
          courseId={selectedSubject.course_id}
          topicId={selectedTopicIdForModal}
          initialTopicName={selectedTopicNameForModal}
        />
      )}

      {selectedSubject?.course_id && (
        <FamilyEvidenceModal
          isOpen={isFamilyModalOpen}
          onClose={() => setIsFamilyModalOpen(false)}
          courseId={selectedSubject.course_id}
          familyId={selectedFamilyIdForModal}
          initialFamilyName={selectedFamilyNameForModal}
          onViewQuestions={(famId, famName) => handleViewQuestions(undefined, famId, famName)}
        />
      )}
    </div>
  );
}
