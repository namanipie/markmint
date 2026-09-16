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

import { CurriculumSubject, CurriculumStats, IntelligenceSnapshot, HistoricalQuestion, SearchResult } from "./types";

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

export async function getIntelligenceSnapshot(
  courseId: string | number,
  targetYear?: number,
  targetExamDate?: string,
  studentId: string = "anonymous"
): Promise<IntelligenceSnapshot> {
  let url = `/intelligence/${encodeURIComponent(String(courseId))}?student_id=${encodeURIComponent(studentId)}`;
  if (targetYear) url += `&target_year=${encodeURIComponent(targetYear)}`;
  if (targetExamDate) url += `&target_exam_date=${encodeURIComponent(targetExamDate)}`;
  return fetchAPI(url);
}

export async function getHistoricalQuestions(
  courseId: string | number,
  topic?: string,
  assessmentType?: string,
  limit: number = 50
): Promise<{ course_id: number; course_name: string; total_returned: number; questions: HistoricalQuestion[] }> {
  let url = `/intelligence/${encodeURIComponent(String(courseId))}/questions?limit=${limit}`;
  if (topic) url += `&topic=${encodeURIComponent(topic)}`;
  if (assessmentType) url += `&assessment_type=${encodeURIComponent(assessmentType)}`;
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

export async function getPredictions(subjectOrCourseId: string | number) {
  return fetchAPI(`/predictions/${encodeURIComponent(String(subjectOrCourseId))}`);
}

export async function getExamPredictions(id: string | number) {
  return fetchAPI(`/predictions/${encodeURIComponent(String(id))}`);
}

export async function getExamQuestions(
  id: string | number,
  page: number = 1,
  size: number = 50
) {
  return fetchAPI(`/exams/${encodeURIComponent(String(id))}/questions?page=${page}&size=${size}`);
}

export async function getExamDNA(course_id: string | number) {
  return fetchAPI(`/analysis/dna?course_id=${encodeURIComponent(String(course_id))}`);
}

export async function getStudyPriorities(course_name: string) {
  return fetchAPI(`/study/priorities/${encodeURIComponent(course_name)}`);
}

export async function getStudyPlan(course_name: string) {
  return fetchAPI(`/study/plan/${encodeURIComponent(course_name)}`);
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

export async function getPractice(subject: string) {
  return fetchAPI(`/practice/${encodeURIComponent(subject)}`);
}

// Global dashboard stats (if backend provides a summary, else we'll fetch courses and use that)
export async function getDashboardStats() {
  try {
    return await fetchAPI("/stats/");
  } catch (e) {
    // Fallback if no global stats endpoint exists
    return null;
  }
}
