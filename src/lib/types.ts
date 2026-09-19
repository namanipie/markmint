export interface TopicStat {
  topic: string;
  frequency: number;
  confidence: number;
  unit: number;
}

export interface Question {
  id: string;
  text: string;
  topic: string;
  unit: number;
  marks: number;
  year: number;
  type: string[];
  difficulty: number;
  confidence: number;
  source?: string;
}

export interface Prediction {
  topic: string;
  probability: number;
  confidence: number;
  evidence: {
    papers_present: number;
    total_papers: number;
    long_answer_count: number;
    historicalYears?: number[];
  };
  historicalAppearances: number[];
  timeline?: { year: number; present: boolean }[];
  reason_codes?: string[];
  explanation?: string;
}

export interface DashboardStats {
  papersAnalyzed: number;
  totalQuestions: number;
  topicsDetected: number;
  predictionConfidence: number;
}

export interface CourseInfo {
  id: string;
  name: string;
  code: string;
  semester: number;
  examType: string;
  academicYear: string;
  department: string;
}

export interface TopicFrequency {
  topic: string;
  frequency: number;
  year?: number;
}

export interface MarksDistribution {
  marks: number;
  count: number;
  label: string;
}

export interface UnitDistribution {
  unit: number;
  name: string;
  weight: number;
  questionCount: number;
}

export interface QuestionTypeBreakdown {
  type: string;
  count: number;
  percentage: number;
}

export interface HeatmapCell {
  topic: string;
  year: number;
  frequency: number;
}

export interface HistoricalTrend {
  year: number;
  [topic: string]: number;
}

export interface MarksPattern {
  year: number;
  '2marks': number;
  '5marks': number;
  '10marks': number;
  '15marks': number;
}

export interface UnitWeight {
  unit: number;
  name: string;
  weight: number;
  topicCount: number;
}

export interface ConfidenceGroup {
  level: 'high' | 'medium' | 'low';
  topics: string[];
  evidenceCount: number;
  description: string;
}

export interface QuestionFamily {
  id: string;
  label: string;
  type: 'root' | 'topic' | 'subtopic' | 'question-type';
  children?: QuestionFamily[];
  questions?: Question[];
}

export interface StudyPlanInput {
  timeAvailable: number;
  targetMarks: number;
  currentMastery: number;
}

export interface StudyDay {
  day: number;
  tasks: StudyTask[];
}

export interface StudyTask {
  topic: string;
  hours: number;
  type: 'study' | 'practice' | 'mock-test' | 'revision';
  priority: 'high' | 'medium' | 'low';
}

export interface StudyPlan {
  totalDays: number;
  totalHours: number;
  days: StudyDay[];
  recommendations: string[];
}

export type FilterState = {
  unit: number | null;
  topic: string | null;
  marks: number | null;
  year: number | null;
  questionType: string | null;
  search: string;
};

export type HeatmapData = HeatmapCell;
export type TrendData = HistoricalTrend;

export interface BackendCourse {
  id: number;
  code: string;
  name: string;
  canonical_code?: string | null;
  department?: string | null;
  regulation_year?: number | null;
}

export interface BackendPrediction {
  rank: number;
  name: string;
  score: number;
  confidence: string;
  category: string;
  historyCount: number;
  lastSeen: string;
  evidence_details: {
    combo?: boolean;
    recent_freq?: number;
    hist_freq?: number;
    occurrences?: number;
  };
}

export interface PredictionResponse {
  subject: string;
  target_year: string;
  predictions: BackendPrediction[];
  evidence: any;
  data_quality: string;
}

export interface ExamDNAAnalysis {
  course_id: string;
  analysis_summary: string;
  topic_distribution: any;
  recurring_families: any[];
}


export interface StudyResource {
  id?: string;
  title: string;
  url: string;
  source: 'local' | 'studique' | 'student' | 'pyq' | string;
  type?: string;
  description?: string;
}

export interface StudyTopicPlan {
  name: string;
  probability: number;
  priority: 'High' | 'Medium' | 'Low' | string;
  reason: string;
  resources: StudyResource[];
  historyCount?: number;
  evidence_details?: string;
}

export interface StudyPlanResponse {
  course_name: string;
  course_id?: number;
  plan_mode?: "topic" | "family" | string;
  overall_probability?: number;
  topics: StudyTopicPlan[];
  resources?: StudyResource[];
  student_resources?: StudyResource[];
  progress?: string | number;
  empty?: boolean;
}

export interface StudyUploadResponse {
  status: string;
  document_id: string;
  mapped_topics: string[];
  message?: string;
}

export interface CurriculumSubject {
  curriculum_id: string;
  subject_name: string;
  credits: number;
  course_id: number | null;
  canonical_code: string | null;
  status: "MATCHED" | "UNMATCHED" | "AMBIGUOUS" | string;
  has_exams: boolean;
  exam_count: number;
  question_count: number;
  notes: string | null;
}

export interface CurriculumStats {
  total_entries: number;
  branches_count: number;
  matched_entries: number;
  ambiguous_entries: number;
  unmatched_entries: number;
  backend_courses_count: number;
}

export interface PredictionItem {
  rank: number;
  name: string;
  category: "topic" | "family" | "unit" | string;
  score: number;
  prediction_score: number;
  probability: number;
  confidence: "HIGH" | "MEDIUM" | "LOW" | "INSUFFICIENT" | string;
  score_semantics?: string;
  calibration_method?: string;
  evidence_sufficiency?: string;
  papers_analyzed?: number;
  papers_with_topic?: number;
  distinct_paper_count?: number;
  papers_with_family?: number;
  paper_coverage?: number;
  supporting_questions?: any[];
  supporting_question_ids?: number[];
  historyCount?: number;
  historical_occurrences?: number;
  recent_occurrences?: number;
  last_seen_year?: number | null;
  lastSeen?: string;
  marks_seen?: number | null;
  average_marks?: number | null;
  total_marks_observed?: number | null;
  repetition_type?: string | null;
  family_recurrence_score?: number;
  recent_frequency_score?: number;
  recency_score?: number;
  marks_score?: number;
  evidence_count?: number;
  reason_codes?: string[];
  explanation?: string;
  evidence_details?: any;
  topic_id?: number;
  family_id?: number | null;
  timeline?: TimelineEntry[];
  historical_years?: number[];
  observed_years?: number[];
}

export interface TimelineEntry {
  year: number;
  exam_exists?: boolean;
  topic_present?: boolean;
  family_present?: boolean;
  present: boolean;
  status?: "TOPIC_PRESENT" | "TOPIC_ABSENT" | "FAMILY_PRESENT" | "FAMILY_ABSENT" | "NO_EXAM_RECORDED" | string;
}

export interface HistoricalQuestion {
  id: number;
  question_number: string;
  original_text: string;
  normalized_text?: string | null;
  marks?: number | null;
  is_alternative: boolean;
  difficulty?: number | null;
  question_type?: string | null;
  cognitive_level?: string | null;
  exam_id?: number | null;
  year?: number | null;
  assessment_type?: string | null;
  term?: string | null;
  family_id?: number | null;
  family_name?: string | null;
  family_recurrence_history?: number[];
  source_document_title?: string | null;
  source_document_url?: string | null;
  repetition_type?: string;
  topics?: string[];
}

export interface CoverageSummary {
  total_predicted_topics: number;
  mastered_topics: number;
  in_progress_topics: number;
  unstudied_topics: number;
  mastered_topic_count?: number;
  in_progress_count?: number;
  unstudied_count?: number;
  student_preparation_coverage: number;
  coverage_gap_topics: string[];
  high_priority_gap_count: number;
}

export interface ExamSchedulePhase {
  phase: number;
  name: string;
  duration_days: number;
  focus_topics: (string | { topic_id?: number | null; topic_name: string })[];
  description: string;
}

export interface ExamSchedule {
  target_exam_date: string;
  days_remaining: number;
  status: string;
  recommended_daily_topics: number;
  phases: ExamSchedulePhase[];
}

export interface IntelligenceSnapshot {
  data_availability_status: "READY" | "CATALOG_ONLY" | "AMBIGUOUS" | "UNMATCHED" | "INSUFFICIENT_EVIDENCE" | string;
  prediction_mode?: "topic" | "family" | "insufficient" | string;
  has_topic_taxonomy?: boolean;
  taxonomy_topic_count?: number;
  topic_predictions_count?: number;
  family_predictions_count?: number;
  course?: {
    id: number;
    name: string;
    code: string;
    canonical_code?: string | null;
    department?: string | null;
    regulation_year?: number | null;
  } | null;
  curriculum?: {
    curriculum_id?: string | null;
    subject_name: string;
    branch_name?: string | null;
    semester?: number | null;
    credits: number;
    status: string;
    notes?: string | null;
  } | null;
  exam_history?: {
    total_papers: number;
    historical_papers_analyzed: number;
    total_questions: number;
    years: number[];
    available_assessment_types: string[];
    target_year?: number;
  } | null;
  available_assessment_types?: string[];
  assessment_cycle?: string;
  available_assessment_cycles?: string[];
  assessment_component?: string;
  assessment_label?: string;
  assessment_scope?: {
    student_cycle: string;
    component_code?: string;
    component_label?: string;
    student_label?: string;
    role?: string;
    marks?: number | null;
    source_document?: string | null;
    unit_numbers?: number[];
    total_in_scope_topics?: number;
    observed_in_scope_topics?: number;
    unobserved_in_scope_topics?: Array<{
      name: string;
      status: string;
      message: string;
    }>;
  } | null;
  predictions: PredictionItem[];
  family_predictions?: PredictionItem[];
  topic_predictions?: PredictionItem[];
  study_priorities: any[];
  coverage_summary?: CoverageSummary | null;
  exam_schedule?: ExamSchedule | null;
  message?: string;
  metadata?: {
    model_version: string;
    taxonomy_version: string;
    engine_version: string;
    corpus_version?: string;
    calibration_method?: string;
    score_semantics?: string;
    latency_ms?: number;
    sufficiency?: string;
    generated_at: string;
  };
}

export interface SearchResult {
  id: number;
  result_type: "exam_question" | "study_material" | "concept" | "question_family" | "analysis_finding" | "course" | "topic" | "exam" | string;
  title: string;
  text_snippet: string;
  subject?: string | null;
  unit?: string | null;
  topic?: string | null;
  year?: number | null;
  exam_type?: string | null;
  relevance_score: number;
  provenance_url?: string | null;
  attribution?: string | null;
  metadata?: Record<string, any> | null;
}

export interface RepetitionOverview {
  course_id: number;
  course_name: string;
  code: string;
  canonical_code: string;
  readiness_status: string;
  total_papers: number;
  total_questions: number;
  years: number[];
  time_range: string;
  assessment_types: string[];
  marks_summary: {
    min_question_marks: number;
    max_question_marks: number;
    avg_question_marks: number;
    total_marks_analyzed: number;
    total_marks?: number;
    avg_marks?: number;
    max_marks?: number;
  };
  top_repeated_topics: {
    topic_id: number;
    topic_name: string;
    occurrences: number;
    paper_count: number;
    paper_coverage: number;
    total_marks: number;
    recurrence_status: string;
  }[];
  top_repeated_families: {
    family_id: number;
    canonical_name: string;
    occurrences: number;
    paper_count: number;
    repetition_type: string;
  }[];
}

export interface TopicRepetitionItem {
  topic_id: number;
  topic_name: string;
  unit_name: string;
  unit_number: number;
  occurrence_count: number;
  paper_count: number;
  paper_coverage: number;
  total_marks: number;
  average_marks: number;
  max_marks: number;
  first_seen_year: number | null;
  last_seen_year: number | null;
  recent_occurrence_count: number;
  recurrence_status: "RECENTLY_RECURRING" | "HISTORICALLY_STABLE" | "DORMANT" | "LIMITED_EVIDENCE" | "NEVER_EXAMINED";
  assessment_type_breakdown: Record<string, number>;
}

export interface TopicRepetitionResponse {
  course_id: number;
  course_name: string;
  total_papers_analyzed: number;
  total_topics: number;
  topics_with_questions: number;
  filters_applied: {
    year?: number | null;
    assessment_type?: string | null;
    unit?: number | null;
    min_marks?: number | null;
    max_marks?: number | null;
  };
  topics: TopicRepetitionItem[];
}

export interface FamilyAppearanceItem {
  question_id: number;
  question_number: string;
  year: number | null;
  assessment_type: string | null;
  term: string | null;
  marks: number;
  is_alternative: boolean;
  original_text: string;
  normalized_text: string;
}

export interface FamilyRepeatItem {
  family_id: number;
  canonical_name: string;
  repetition_type: "exact_repetition" | "parameter_variation" | "conceptual_variant" | "singleton" | string;
  occurrence_count: number;
  appearances_count: number;
  paper_count: number;
  first_seen_year: number | null;
  last_seen_year: number | null;
  assessment_history: string[];
  marks_history: { label: string; marks: number; year: number | null }[];
  appearances: FamilyAppearanceItem[];
  timeline?: TimelineEntry[];
}

export interface FamilyRepeatResponse {
  course_id: number;
  course_name: string;
  total_papers: number;
  total_families_found: number;
  multi_repeat_families_count: number;
  observed_years?: number[];
  unobserved_years?: number[];
  gap_years?: number[];
  families: FamilyRepeatItem[];
}

export interface RepeatedQuestionsResponse {
  course_id: number;
  course_name: string;
  total_exact_repeats: number;
  total_family_repeats: number;
  total_concept_variants: number;
  exact_repeats: {
    repetition_type: "EXACT_REPEAT";
    family_id: number;
    canonical_name: string;
    repeat_count: number;
    paper_count: number;
    years_seen: number[];
    questions: {
      question_id: number;
      question_number: string;
      year: number | null;
      assessment_type: string | null;
      marks: number;
      original_text: string;
    }[];
  }[];
}

export interface EvolutionTimelineEntry {
  year: number;
  exam_exists?: boolean;
  gap?: boolean;
  status?: string;
  description?: string;
  paper_count: number;
  papers_count: number;
  assessment_types: string[];
  total_questions: number;
  total_marks: number;
  topics: {
    name: string;
    question_count: number;
    marks: number;
    is_new: boolean;
  }[];
  active_topics: {
    name: string;
    question_count: number;
    marks: number;
    is_new: boolean;
  }[];
  new_topics_introduced: string[];
  discontinued_topics: string[];
}

export interface EvolutionResponse {
  course_id: number;
  course_name: string;
  timeline_years: number[];
  observed_years?: number[];
  unobserved_years?: number[];
  gap_years?: number[];
  gap_entries?: EvolutionTimelineEntry[];
  timeline: EvolutionTimelineEntry[];
}

export interface MarksAnalyticsResponse {
  course_id: number;
  course_name: string;
  total_questions_analyzed: number;
  total_marks: number;
  avg_question_marks: number;
  common_marks: { marks: number; count: number; percentage: number }[];
  marks_by_assessment_type: Record<string, number>;
  topic_mark_shares: { topic_name: string; marks: number; percentage: number }[];
}

export interface AssessmentTypePaperCount {
  type: string;
  paper_count: number;
}

export interface TopicAssessmentBreakdown {
  papers_present: number;
  total_papers: number;
  paper_frequency: number;
  question_count: number;
  total_marks: number;
}

export interface AssessmentComparisonTopic {
  topic_id: number;
  topic_name: string;
  unit_name: string;
  unit_number: number;
  assessment_breakdown: Record<string, TopicAssessmentBreakdown>;
  bias: "CLASS_TEST_LEANING" | "END_SEM_LEANING" | "UNIVERSAL" | "BALANCED" | "UNEXAMINED";
  is_universal: boolean;
}

export interface AssessmentComparisonResponse {
  course_id: number;
  course_name: string;
  assessment_types: AssessmentTypePaperCount[];
  total_papers: number;
  topics: AssessmentComparisonTopic[];
}

export interface PastQuestionItem {
  id: number;
  question_number: string;
  year: number | null;
  assessment_type: string;
  marks: number | null;
  is_alternative: boolean;
  original_text: string;
  difficulty: number | null;
  family_id: number | null;
  family_name: string | null;
  repeat_type: "EXACT_REPEAT" | "FAMILY_REPEAT" | "SINGLETON";
}

export interface TopicIntelligenceResponse {
  course_id: number;
  course_name: string;
  topic_id: number;
  topic_name: string;
  unit: {
    name: string;
    number: number;
  };
  repetition_metrics: {
    paper_count: number;
    total_papers: number;
    paper_coverage: number;
    question_count: number;
    total_marks: number;
    average_marks: number;
    max_marks: number;
    first_seen_year: number | null;
    last_seen_year: number | null;
    assessment_distribution: Record<string, number>;
  };
  question_families: {
    family_id: number;
    canonical_name: string;
    repetition_type: string;
    question_count: number;
    years: number[];
  }[];
  past_questions: PastQuestionItem[];
  forecast: {
    probability: number;
    confidence: string;
    reason_codes: string[];
    rationale: string;
    historical_years: number[];
  };
  personalization: {
    student_id: string;
    status: "NOT_STARTED" | "IN_PROGRESS" | "MASTERED";
    practice_attempted: number;
    practice_correct: number;
    priority_score: number;
    recommended_action: string;
  };
  timeline?: TimelineEntry[];
  observed_years?: number[];
  unobserved_years?: number[];
  gap_years?: number[];
}

export interface SingleFamilyAppearance {
  question_id: number;
  question_number: string;
  year: number | null;
  assessment_type: string | null;
  term?: string | null;
  exam_id?: number | null;
  marks: number | null;
  is_alternative: boolean;
  original_text: string;
  normalized_text?: string | null;
  repetition_type: string;
  source_document_title?: string | null;
  source_document_url?: string | null;
}

export interface SingleFamilyResponse {
  course_id: number;
  course_name: string;
  family_id: number;
  canonical_name: string;
  repetition_type: string;
  occurrence_count: number;
  distinct_paper_count: number;
  total_papers_analyzed: number;
  paper_coverage: number;
  first_seen_year: number | null;
  last_seen_year: number | null;
  observed_years: number[];
  assessment_history: string[];
  average_marks: number | null;
  total_marks_observed: number | null;
  appearances: SingleFamilyAppearance[];
  timeline: TimelineEntry[];
}
