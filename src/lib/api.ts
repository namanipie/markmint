const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

async function fetchAPI(path: string, options?: RequestInit) {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    let errorDetail = `${res.status} ${res.statusText}`;
    try {
      const data = await res.json();
      if (data?.detail) {
        errorDetail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      } else if (data?.message) {
        errorDetail = data.message;
      }
    } catch {
      // ignore json parse error on non-json error responses
    }
    const err = new Error(errorDetail);
    (err as any).status = res.status;
    throw err;
  }
  return res.json();
}

import {
  CurriculumSubject,
  CurriculumStats,
  IntelligenceSnapshot,
  HistoricalQuestion,
  SearchResult,
  RepetitionOverview,
  TopicRepetitionResponse,
  FamilyRepeatResponse,
  RepeatedQuestionsResponse,
  EvolutionResponse,
  MarksAnalyticsResponse,
  AssessmentComparisonResponse,
  TopicIntelligenceResponse,
  SingleFamilyResponse,
  CourseTrack,
  SubmissionPreview,
  PaperSubmissionRecord,
  AdminReviewSummary,
  SubmitterFeedback
} from "./types";

// Real Backend Endpoints
export async function getCurriculumBranches(): Promise<string[]> {
  return fetchAPI("/curriculum/branches");
}

export async function getCurriculumSemesters(branch: string): Promise<number[]> {
  return fetchAPI(`/curriculum/branches/${encodeURIComponent(branch)}/semesters`);
}

export async function getCurriculumSubjects(
  branch: string, 
  semester: number | string
): Promise<CurriculumSubject[]> {
  return fetchAPI(
    `/curriculum/branches/${encodeURIComponent(branch)}/semesters/${encodeURIComponent(String(semester))}`
  );
}

export async function getCurriculumStats(): Promise<CurriculumStats> {
  return fetchAPI("/curriculum/stats");
}

export async function getCourseTracks(courseId: string | number): Promise<CourseTrack[]> {
  return fetchAPI(`/courses/${encodeURIComponent(String(courseId))}/tracks`);
}

export async function getIntelligenceSnapshot(
  courseId: string | number,
  targetYear?: number,
  targetExamDate?: string,
  studentId: string = "anonymous",
  assessmentCycle?: string,
  language?: string
): Promise<IntelligenceSnapshot> {
  let url = `/intelligence/${encodeURIComponent(String(courseId))}?student_id=${encodeURIComponent(studentId)}`;
  if (targetYear) url += `&target_year=${encodeURIComponent(targetYear)}`;
  if (targetExamDate) url += `&target_exam_date=${encodeURIComponent(targetExamDate)}`;
  if (assessmentCycle && assessmentCycle !== "ALL") {
    url += `&assessment_cycle=${encodeURIComponent(assessmentCycle)}`;
  }
  if (language) {
    url += `&language=${encodeURIComponent(language)}`;
  }
  return fetchAPI(url);
}

export async function getHistoricalQuestions(
  courseId: string | number,
  topic?: string,
  assessmentType?: string,
  limit: number = 50,
  filters?: {
    year?: number;
    min_marks?: number;
    max_marks?: number;
    family_id?: number;
    family_name?: string;
    repetition_type?: string;
    assessment_cycle?: string;
    language?: string;
  }
): Promise<{ course_id: number; course_name: string; total_returned: number; questions: HistoricalQuestion[] }> {
  let url = `/intelligence/${encodeURIComponent(String(courseId))}/questions?limit=${limit}`;
  if (topic) url += `&topic=${encodeURIComponent(topic)}`;
  const activeCycle = filters?.assessment_cycle || assessmentType;
  if (activeCycle && activeCycle !== "ALL") {
    url += `&assessment_cycle=${encodeURIComponent(activeCycle)}`;
  }
  if (filters?.year) url += `&year=${encodeURIComponent(filters.year)}`;
  if (filters?.min_marks !== undefined) url += `&min_marks=${encodeURIComponent(filters.min_marks)}`;
  if (filters?.max_marks !== undefined) url += `&max_marks=${encodeURIComponent(filters.max_marks)}`;
  if (filters?.family_id) url += `&family_id=${encodeURIComponent(filters.family_id)}`;
  if (filters?.family_name) url += `&family_name=${encodeURIComponent(filters.family_name)}`;
  if (filters?.repetition_type) url += `&repetition_type=${encodeURIComponent(filters.repetition_type)}`;
  if (filters?.language) url += `&language=${encodeURIComponent(filters.language)}`;
  return fetchAPI(url);
}

export async function getModelPerformance(): Promise<any> {
  return fetchAPI("/intelligence/model-performance");
}

export async function getCorpusHealth(): Promise<any> {
  return fetchAPI("/intelligence/corpus-health");
}

export async function searchIntelligence(query: { raw_query: string; limit?: number }): Promise<SearchResult[]> {
  return fetchAPI("/search/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(query),
  });
}

export async function getCourses() {
  return fetchAPI("/courses/");
}

export async function getCourse(id: string | number) {
  return fetchAPI(`/courses/${id}`);
}

export async function getPredictions(subjectOrCourseId: string | number, assessmentCycle?: string, language?: string) {
  let url = `/predictions/${encodeURIComponent(String(subjectOrCourseId))}`;
  const params: string[] = [];
  if (assessmentCycle && assessmentCycle !== "ALL") {
    params.push(`assessment_cycle=${encodeURIComponent(assessmentCycle)}`);
  }
  if (language) {
    params.push(`language=${encodeURIComponent(language)}`);
  }
  if (params.length > 0) {
    url += `?${params.join("&")}`;
  }
  return fetchAPI(url);
}

export async function getExamPredictions(id: string | number, assessmentCycle?: string, language?: string) {
  let url = `/predictions/${encodeURIComponent(String(id))}`;
  const params: string[] = [];
  if (assessmentCycle && assessmentCycle !== "ALL") {
    params.push(`assessment_cycle=${encodeURIComponent(assessmentCycle)}`);
  }
  if (language) {
    params.push(`language=${encodeURIComponent(language)}`);
  }
  if (params.length > 0) {
    url += `?${params.join("&")}`;
  }
  return fetchAPI(url);
}

export async function getExamQuestions(
  id: string | number,
  page: number = 1,
  size: number = 50
) {
  return fetchAPI(`/exams/${encodeURIComponent(String(id))}/questions?page=${page}&size=${size}`);
}

export async function getExamDNA(course_id: string | number, assessmentCycle?: string) {
  let url = `/analysis/dna?course_id=${encodeURIComponent(String(course_id))}`;
  if (assessmentCycle && assessmentCycle !== "ALL") {
    url += `&assessment_cycle=${encodeURIComponent(assessmentCycle)}`;
  }
  return fetchAPI(url);
}

export async function getStudyPriorities(course_name: string, assessmentCycle?: string, language?: string) {
  let url = `/study/priorities/${encodeURIComponent(course_name)}`;
  const params: string[] = [];
  if (assessmentCycle && assessmentCycle !== "ALL") {
    params.push(`assessment_cycle=${encodeURIComponent(assessmentCycle)}`);
  }
  if (language) {
    params.push(`language=${encodeURIComponent(language)}`);
  }
  if (params.length > 0) {
    url += `?${params.join("&")}`;
  }
  return fetchAPI(url);
}

export async function getStudyPlan(course_name: string, assessmentCycle?: string) {
  let url = `/study/plan/${encodeURIComponent(course_name)}`;
  if (assessmentCycle && assessmentCycle !== "ALL") {
    url += `?assessment_cycle=${encodeURIComponent(assessmentCycle)}`;
  }
  return fetchAPI(url);
}

export async function getStudyResources(course_name: string, topic_name: string) {
  return fetchAPI(`/study/resources/${encodeURIComponent(course_name)}/${encodeURIComponent(topic_name)}`);
}

export async function uploadStudyNotes(formData: FormData) {
  const res = await fetch(`${API_BASE}/study/uploads`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    let errorDetail = `Upload failed: ${res.status}`;
    try {
      const data = await res.json();
      if (data?.detail) errorDetail = data.detail;
    } catch {
      // ignore json error
    }
    const err = new Error(errorDetail);
    (err as any).status = res.status;
    throw err;
  }
  return res.json();
}

export async function updateStudyProgress(course_id: string | number, data: any) {
  return fetchAPI(`/study/progress/${course_id}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function getPractice(subject: string, assessmentCycle?: string, language?: string) {
  let url = `/practice/${encodeURIComponent(subject)}`;
  const params: string[] = [];
  if (assessmentCycle && assessmentCycle !== "ALL") {
    params.push(`assessment_cycle=${encodeURIComponent(assessmentCycle)}`);
  }
  if (language) {
    params.push(`language=${encodeURIComponent(language)}`);
  }
  if (params.length > 0) {
    url += `?${params.join("&")}`;
  }
  return fetchAPI(url);
}

// Global dashboard stats (if backend provides a summary, else we'll fetch courses and use that)
export async function getDashboardStats() {
  try {
    return await fetchAPI("/stats/");
  } catch {
    // Fallback if no global stats endpoint exists
    return null;
  }
}

// Repetition Analytics Suite
export async function getRepetitionOverview(courseId: string | number, language?: string): Promise<RepetitionOverview> {
  let url = `/analytics/${encodeURIComponent(String(courseId))}/overview`;
  if (language) url += `?language=${encodeURIComponent(language)}`;
  return fetchAPI(url);
}

export async function getTopicRepetition(
  courseId: string | number,
  filters?: {
    year?: number;
    assessmentType?: string;
    unit?: number;
    minMarks?: number;
    maxMarks?: number;
    language?: string;
  }
): Promise<TopicRepetitionResponse> {
  const url = `/analytics/${encodeURIComponent(String(courseId))}/topics?`;
  const params: string[] = [];
  if (filters?.year) params.push(`year=${encodeURIComponent(filters.year)}`);
  if (filters?.assessmentType) params.push(`assessment_type=${encodeURIComponent(filters.assessmentType)}`);
  if (filters?.unit) params.push(`unit=${encodeURIComponent(filters.unit)}`);
  if (filters?.minMarks !== undefined) params.push(`min_marks=${encodeURIComponent(filters.minMarks)}`);
  if (filters?.maxMarks !== undefined) params.push(`max_marks=${encodeURIComponent(filters.maxMarks)}`);
  if (filters?.language) params.push(`language=${encodeURIComponent(filters.language)}`);
  return fetchAPI(url + params.join("&"));
}

export async function getQuestionFamilies(
  courseId: string | number,
  filters?: {
    assessmentType?: string;
    topicId?: number;
    minOccurrences?: number;
  }
): Promise<FamilyRepeatResponse> {
  const url = `/analytics/${encodeURIComponent(String(courseId))}/families?`;
  const params: string[] = [];
  if (filters?.assessmentType) params.push(`assessment_type=${encodeURIComponent(filters.assessmentType)}`);
  if (filters?.topicId) params.push(`topic_id=${encodeURIComponent(filters.topicId)}`);
  if (filters?.minOccurrences) params.push(`min_occurrences=${encodeURIComponent(filters.minOccurrences)}`);
  return fetchAPI(url + params.join("&"));
}

export async function getRepeatedQuestions(courseId: string | number): Promise<RepeatedQuestionsResponse> {
  return fetchAPI(`/analytics/${encodeURIComponent(String(courseId))}/questions/repeated`);
}

export async function getCourseEvolution(courseId: string | number): Promise<EvolutionResponse> {
  return fetchAPI(`/analytics/${encodeURIComponent(String(courseId))}/evolution`);
}

export async function getMarksAnalytics(courseId: string | number): Promise<MarksAnalyticsResponse> {
  return fetchAPI(`/analytics/${encodeURIComponent(String(courseId))}/marks`);
}

export async function getAssessmentComparison(
  courseId: string | number
): Promise<AssessmentComparisonResponse> {
  return fetchAPI(`/analytics/${encodeURIComponent(String(courseId))}/assessment-comparison`);
}

export async function getTopicIntelligence(
  courseId: string | number,
  topicId: string | number,
  studentId: string = "default_student"
): Promise<TopicIntelligenceResponse> {
  return fetchAPI(
    `/analytics/${encodeURIComponent(String(courseId))}/topics/${encodeURIComponent(
      String(topicId)
    )}/intelligence?student_id=${encodeURIComponent(studentId)}`
  );
}

export async function getSingleFamilyEvidence(
  courseId: string | number,
  familyId: string | number
): Promise<SingleFamilyResponse> {
  return fetchAPI(
    `/analytics/${encodeURIComponent(String(courseId))}/families/${encodeURIComponent(String(familyId))}`
  );
}

// Student Paper Submission & Moderation Pipeline
export async function validateSubmissionPreview(formData: FormData): Promise<SubmissionPreview> {
  const res = await fetch(`${API_BASE}/submissions/validate-preview`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    let errorMsg = `${res.status} ${res.statusText}`;
    try {
      const err = await res.json();
      if (err.detail) errorMsg = typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail);
    } catch {}
    throw new Error(errorMsg);
  }
  return res.json();
}

export async function createPaperSubmission(formData: FormData): Promise<PaperSubmissionRecord> {
  const res = await fetch(`${API_BASE}/submissions`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    let errorMsg = `${res.status} ${res.statusText}`;
    try {
      const err = await res.json();
      if (err.detail) errorMsg = typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail);
    } catch {}
    throw new Error(errorMsg);
  }
  return res.json();
}

export async function listPaperSubmissions(
  status?: string,
  courseId?: number
): Promise<PaperSubmissionRecord[]> {
  const params: string[] = [];
  if (status) params.push(`status=${encodeURIComponent(status)}`);
  if (courseId) params.push(`course_id=${encodeURIComponent(courseId)}`);
  const query = params.length > 0 ? `?${params.join("&")}` : "";
  return fetchAPI(`/submissions${query}`);
}

export async function getPaperSubmission(id: number): Promise<PaperSubmissionRecord> {
  return fetchAPI(`/submissions/${encodeURIComponent(id)}`);
}

export async function approvePaperSubmission(
  id: number,
  payload?: {
    reviewer?: string;
    override_course_id?: number;
    override_assessment?: string;
    override_year?: number;
  }
): Promise<{ status: string; result: any }> {
  return fetchAPI(`/submissions/${encodeURIComponent(id)}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || { reviewer: "moderator" }),
  });
}

export async function rejectPaperSubmission(
  id: number,
  reason: string,
  reviewer: string = "moderator"
): Promise<{ status: string; result: any }> {
  return fetchAPI(`/submissions/${encodeURIComponent(id)}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason, reviewer }),
  });
}

export async function getSubmissionReviewSummary(id: number): Promise<AdminReviewSummary> {
  return fetchAPI(`/submissions/${encodeURIComponent(id)}/review-summary`);
}

export async function getSubmissionFeedback(id: number): Promise<SubmitterFeedback> {
  return fetchAPI(`/submissions/${encodeURIComponent(id)}/feedback`);
}

export async function getSubmissionByTracking(tracking: string): Promise<SubmitterFeedback> {
  return fetchAPI(`/submissions/tracking/${encodeURIComponent(tracking)}`);
}



