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
  };
  historicalAppearances: number[];
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
  course_id: string;
  course_code: string;
  course_name: string;
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
  historyCount?: number;
  historical_occurrences?: number;
  recent_occurrences?: number;
  last_seen_year?: number | null;
  lastSeen?: string;
  marks_seen?: number;
  family_recurrence_score?: number;
  recent_frequency_score?: number;
  recency_score?: number;
  marks_score?: number;
  evidence_count?: number;
  reason_codes?: string[];
  explanation?: string;
  evidence_details?: any;
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
  repetition_type?: string;
  topics?: string[];
}

export interface CoverageSummary {
  total_predicted_topics: number;
  mastered_topics: number;
  in_progress_topics: number;
  unstudied_topics: number;
  student_preparation_coverage: number;
  coverage_gap_topics: string[];
  high_priority_gap_count: number;
}

export interface ExamSchedulePhase {
  phase: number;
  name: string;
  duration_days: number;
  focus_topics: string[];
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
  predictions: PredictionItem[];
  study_priorities: any[];
  coverage_summary?: CoverageSummary | null;
  exam_schedule?: ExamSchedule | null;
  message?: string;
  metadata?: {
    model_version: string;
    taxonomy_version: string;
    engine_version: string;
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

