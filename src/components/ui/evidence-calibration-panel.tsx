// @ts-nocheck
"use client";

import {
  HelpCircle,
  AlertCircle,
  Info,
  Layers,
  Clock,
  Award,
  Activity,
  Calendar,
  Repeat,
  BookOpen,
} from "lucide-react";
import { MathText } from "@/components/ui/math-text";
import { PredictionItem } from "@/lib/types";

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

interface SupportingQuestion {
  id?: number;
  question_number?: string;
  original_text?: string;
  year?: number;
  marks?: number | null;
  assessment_type?: string | null;
  repeat_type?: string;
}

interface AssessmentBreakdown {
  [cycle: string]: number; // e.g. { "ENDSEM": 3, "CT1": 1 }
}

export interface EvidencePanelData {
  // From PredictionItem
  name: string;
  category: "topic" | "family" | string;
  confidence: "HIGH" | "MEDIUM" | "LOW" | "INSUFFICIENT" | string;
  evidence_sufficiency?: "SUFFICIENT" | "LIMITED" | "INSUFFICIENT" | string;
  papers_analyzed?: number;
  papers_with_topic?: number;
  distinct_paper_count?: number;
  historical_occurrences?: number;
  recent_occurrences?: number;
  last_seen_year?: number | null;
  average_marks?: number | null;
  total_marks_observed?: number | null;
  marks_seen?: number | null;
  repetition_type?: string | null;
  family_id?: number | null;
  reason_codes?: string[];
  explanation?: string;
  supporting_questions?: SupportingQuestion[];
  observed_years?: number[];
  timeline?: { year: number; present: boolean; exam_exists?: boolean }[];
  // Assessment-specific breakdown if available
  assessment_distribution?: AssessmentBreakdown;
}

interface EvidenceCalibratedPanelProps {
  data: EvidencePanelData;
  /** Show supporting historical questions inline */
  showSupportingQuestions?: boolean;
}

// ─────────────────────────────────────────────────────────────────────────────
// Evidence Tier Badge  (never a % of probability)
// ─────────────────────────────────────────────────────────────────────────────

function EvidenceTierBadge({
  sufficiency,
  papers,
}: {
  sufficiency?: string;
  papers?: number;
}) {
  const tier = (sufficiency ?? "").toUpperCase();

  if (tier === "INSUFFICIENT" || (papers != null && papers <= 1)) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-rose-500/10 text-rose-500 border border-rose-500/20">
        <AlertCircle className="w-3 h-3" />
        Evidence Limited · {papers ?? 0} Paper{papers === 1 ? "" : "s"}
      </span>
    );
  }
  if (tier === "LIMITED" || (papers != null && papers <= 2)) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-500/10 text-amber-500 border border-amber-500/20">
        <Info className="w-3 h-3" />
        Limited Evidence · {papers ?? 0} Papers
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
      Verified Evidence · {papers ?? 0} Papers
    </span>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Confidence Row  (text, not %)
// ─────────────────────────────────────────────────────────────────────────────

function confidenceLabel(c: string, papers: number): string {
  const u = c.toUpperCase();
  if (u === "INSUFFICIENT") return "Insufficient — fewer than 2 verified papers";
  if (u === "LOW") return "Low — limited historical sample";
  if (u === "MEDIUM") return "Medium — moderate historical evidence";
  if (u === "HIGH") return "High — strong multi-year historical evidence";
  return c;
}

function confidenceColor(c: string) {
  const u = c.toUpperCase();
  if (u === "HIGH") return "text-emerald-500";
  if (u === "MEDIUM") return "text-amber-500";
  if (u === "LOW") return "text-muted-foreground";
  return "text-rose-500"; // INSUFFICIENT
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Component
// ─────────────────────────────────────────────────────────────────────────────

export function EvidenceCalibratedPanel({
  data,
  showSupportingQuestions = true,
}: EvidenceCalibratedPanelProps) {
  const {
    name,
    category,
    confidence,
    evidence_sufficiency,
    papers_analyzed: totalPapers = 0,
    papers_with_topic,
    distinct_paper_count,
    historical_occurrences: histOcc = 0,
    recent_occurrences: recentOcc = 0,
    last_seen_year: lastSeen,
    average_marks: avgMarks,
    total_marks_observed: totalMarks,
    marks_seen: marksSeen,
    repetition_type: repType,
    family_id: familyId,
    reason_codes: codes = [],
    explanation,
    supporting_questions: supportingQs = [],
    observed_years: obsYears = [],
    timeline,
    assessment_distribution: assessDist,
  } = data;

  const distinctPapers = distinct_paper_count ?? papers_with_topic ?? 0;
  const isFamily = category === "family";
  const isInsufficient =
    (evidence_sufficiency ?? "").toUpperCase() === "INSUFFICIENT" ||
    totalPapers <= 1;
  const isLimited =
    !isInsufficient &&
    ((evidence_sufficiency ?? "").toUpperCase() === "LIMITED" ||
      totalPapers <= 2);
  const hasLongAbsence = codes.includes("LONG_ABSENCE");
  const hasRecentRepeat = codes.includes("RECENTLY_REPEATED");

  // Marks display helper
  const marksDisplay = (() => {
    if (avgMarks != null) return `~${avgMarks} marks avg`;
    if (totalMarks != null && histOcc > 0)
      return `${totalMarks} marks total across ${histOcc} question${histOcc !== 1 ? "s" : ""}`;
    if (marksSeen != null && marksSeen > 0)
      return `${Math.round(marksSeen)} marks observed`;
    return null;
  })();

  // Supporting questions capped at 5 for brevity
  const questionsToShow = (supportingQs || []).slice(0, 5);

  return (
    <div className="rounded-xl border border-accent/20 bg-accent/5 p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <HelpCircle className="w-4 h-4 text-accent shrink-0" />
          <span className="font-bold text-xs text-foreground uppercase tracking-wide">
            Why is MarkMint showing me this?
          </span>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <EvidenceTierBadge
            sufficiency={evidence_sufficiency}
            papers={totalPapers}
          />
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-accent/10 text-accent font-medium border border-accent/20">
            Factual Past Paper Evidence
          </span>
        </div>
      </div>

      {/* Insufficient Evidence Warning */}
      {isInsufficient && (
        <div className="flex items-start gap-2 rounded-lg border border-rose-500/20 bg-rose-500/5 p-3 text-xs">
          <AlertCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-rose-500">
              Evidence Limited:
            </span>{" "}
            <span className="text-muted-foreground">
              Only {totalPapers} examination paper{totalPapers === 1 ? "" : "s"}{" "}
              archived for this course. Predictions require at least 2 historical
              exam papers to be statistically meaningful. Treat this with
              caution.
            </span>
          </div>
        </div>
      )}

      {/* Limited Evidence Notice */}
      {isLimited && !isInsufficient && (
        <div className="flex items-start gap-2 rounded-lg border border-amber-500/20 bg-amber-500/5 p-3 text-xs">
          <Info className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-amber-500">
              Small Historical Sample:
            </span>{" "}
            <span className="text-muted-foreground">
              Only {totalPapers} papers archived. Confidence scores are
              informative but should be interpreted with awareness of limited
              evidence.
            </span>
          </div>
        </div>
      )}

      {/* Plain English Explanation */}
      {explanation && (
        <p className="text-xs text-foreground/90 leading-relaxed bg-background/70 p-2.5 rounded-lg border border-border/40 font-medium">
          {explanation}
        </p>
      )}

      {/* Evidence Checklist */}
      <ul className="space-y-1.5 text-muted-foreground text-xs list-disc list-inside">
        {/* Paper recurrence */}
        <li>
          <strong className="text-foreground">Past Paper Recurrence:</strong>{" "}
          Seen in{" "}
          <span className="font-mono text-foreground font-semibold">
            {distinctPapers} of {totalPapers}
          </span>{" "}
          {isFamily ? "papers containing this question family" : "relevant examination papers"}.
          {totalPapers > 0 && (
            <span className="text-muted-foreground/70">
              {" "}
              ({distinctPapers} paper{distinctPapers !== 1 ? "s" : ""}, not a
              probability percentage)
            </span>
          )}
        </li>

        {/* Last seen */}
        {lastSeen != null && (
          <li>
            <strong className="text-foreground">Last Seen:</strong> Tested in{" "}
            <span className="font-mono text-foreground font-semibold">
              {lastSeen}
            </span>
            {hasLongAbsence && (
              <span className="text-amber-500">
                {" "}· Not seen in recent exam cycles (historical absence).
              </span>
            )}
            {hasRecentRepeat && !hasLongAbsence && (
              <span className="text-emerald-500">
                {" "}· Active in recent exam cycles.
              </span>
            )}
          </li>
        )}

        {/* Marks */}
        {marksDisplay && (
          <li>
            <strong className="text-foreground">Exam Marks:</strong>{" "}
            <span className="font-mono text-foreground font-semibold">
              {marksDisplay}
            </span>
            .
          </li>
        )}

        {/* Question occurrences */}
        {histOcc > 0 && (
          <li>
            <strong className="text-foreground">Historical Questions:</strong>{" "}
            <span className="font-mono text-foreground font-semibold">
              {histOcc}
            </span>{" "}
            question{histOcc !== 1 ? "s" : ""} mapped to this{" "}
            {isFamily ? "family" : "topic"} across the archived exam corpus.
            {recentOcc > 0 && (
              <span className="text-foreground">
                {" "}
                ({recentOcc} in recent exams)
              </span>
            )}
          </li>
        )}

        {/* Assessment-specific distribution */}
        {assessDist &&
          Object.keys(assessDist).length > 0 && (
            <li>
              <strong className="text-foreground">Assessment Cycles:</strong>{" "}
              {Object.entries(assessDist)
                .map(([k, v]) => `${k} (${v}×)`)
                .join(", ")}
              .
            </li>
          )}

        {/* Family recurrence */}
        {isFamily && familyId != null && (
          <li>
            <strong className="text-foreground">Question Family:</strong>{" "}
            Recurring question family (ID #{familyId}).{" "}
            {repType === "EXACT_REPEAT" || repType === "exact_repeat"
              ? "Questions are exact verbatim repeats across exams."
              : repType === "PARAMETER_VARIATION" ||
                repType === "parameter_variation"
              ? "Same structure and formula with different numerical parameters."
              : repType
              ? repType.replace(/_/g, " ")
              : "Structural similarity identified across exam papers."}
          </li>
        )}

        {/* Repetition archetype for topic mode */}
        {!isFamily && repType && (
          <li>
            <strong className="text-foreground">Repetition Archetype:</strong>{" "}
            <span className="text-foreground/80">
              {repType === "EXACT_REPEAT" || repType === "exact_repeat"
                ? "Exact Verbatim Repeat — identical question text appeared across multiple exams."
                : repType === "PARAMETER_VARIATION" ||
                  repType === "parameter_variation"
                ? "Parameter Variation — same formula/structure, different numerical values."
                : repType.replace(/_/g, " ")}
            </span>
          </li>
        )}

        {/* Confidence tier */}
        <li>
          <strong className="text-foreground">Evidence Confidence:</strong>{" "}
          <span className={`font-semibold ${confidenceColor(confidence)}`}>
            {confidenceLabel(confidence, totalPapers)}
          </span>
          . This reflects historical evidence volume, not a prediction of exam
          occurrence.
        </li>
      </ul>

      {/* Evidence Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
        <div className="bg-background/60 p-2.5 rounded border border-border/30">
          <div className="flex items-center gap-1 text-muted-foreground text-[10px] mb-0.5">
            <Layers className="w-3 h-3" />
            Paper Coverage
          </div>
          <div className="font-mono font-bold text-foreground text-sm">
            {totalPapers > 0 ? `${distinctPapers}/${totalPapers}` : "—"}
          </div>
        </div>

        <div className="bg-background/60 p-2.5 rounded border border-border/30">
          <div className="flex items-center gap-1 text-muted-foreground text-[10px] mb-0.5">
            <Activity className="w-3 h-3" />
            Questions
          </div>
          <div className="font-mono font-bold text-foreground text-sm">
            {histOcc > 0 ? `${histOcc} found` : "None mapped"}
          </div>
        </div>

        <div className="bg-background/60 p-2.5 rounded border border-border/30">
          <div className="flex items-center gap-1 text-muted-foreground text-[10px] mb-0.5">
            <Award className="w-3 h-3" />
            Marks Seen
          </div>
          <div className="font-mono font-bold text-foreground text-sm">
            {avgMarks != null
              ? `~${avgMarks} avg`
              : totalMarks != null
              ? `${totalMarks} total`
              : "Unspecified"}
          </div>
        </div>

        <div className="bg-background/60 p-2.5 rounded border border-border/30">
          <div className="flex items-center gap-1 text-muted-foreground text-[10px] mb-0.5">
            <Clock className="w-3 h-3" />
            Last Seen
          </div>
          <div className="font-mono font-bold text-foreground text-sm">
            {lastSeen ?? "—"}
          </div>
        </div>
      </div>

      {/* Supporting Historical Questions (inline, capped at 5) */}
      {showSupportingQuestions && questionsToShow.length > 0 && (
        <div className="space-y-2 pt-1">
          <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
            <BookOpen className="w-3.5 h-3.5 text-accent" />
            <span className="font-semibold uppercase tracking-wider">
              Supporting Historical Questions
            </span>
            <span className="ml-auto font-mono">
              {questionsToShow.length} of {supportingQs.length} shown
            </span>
          </div>
          <div className="space-y-1.5">
            {questionsToShow.map((q, i) => (
              <div
                key={q.id ?? i}
                className="rounded-lg border border-border/40 bg-background/60 p-2.5 space-y-1"
              >
                <div className="flex items-center gap-2 flex-wrap text-[10px] font-mono text-muted-foreground">
                  {q.year != null && (
                    <span className="bg-secondary px-1.5 py-0.5 rounded font-bold text-foreground">
                      {q.year}
                    </span>
                  )}
                  {q.assessment_type && (
                    <span className="px-1.5 py-0.5 rounded bg-secondary/60">
                      {q.assessment_type}
                    </span>
                  )}
                  {q.marks != null && (
                    <span className="px-1.5 py-0.5 rounded bg-accent/10 text-accent font-semibold">
                      {q.marks} Marks
                    </span>
                  )}
                  {q.repeat_type && q.repeat_type !== "singleton" && (
                    <span className="px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-400">
                      {q.repeat_type.replace(/_/g, " ")}
                    </span>
                  )}
                </div>
                {q.original_text && (
                  <div className="text-xs text-foreground/90 leading-relaxed">
                    <MathText content={q.original_text} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Assessment-specific evidence note */}
      {histOcc === 0 && !isInsufficient && (
        <div className="flex items-start gap-2 rounded-lg border border-border/40 bg-secondary/30 p-2.5 text-xs">
          <Info className="w-3.5 h-3.5 text-muted-foreground shrink-0 mt-0.5" />
          <span className="text-muted-foreground">
            This {isFamily ? "family" : "topic"} is part of the syllabus
            taxonomy but has no directly mapped historical exam questions in the
            current assessment scope. It may still appear — check{" "}
            <span className="font-medium text-foreground">
              unobserved topics
            </span>{" "}
            above for context.
          </span>
        </div>
      )}
    </div>
  );
}
