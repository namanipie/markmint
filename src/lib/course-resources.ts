import courseResourcesData from "./course-resources.json";

export interface CourseExamResource {
  title: string;
  examType: "CT1" | "CT2" | "MODEL" | "SURPRISE" | "ENDSEM" | string;
  year?: number | null;
  url: string;
  source: string;
}

export interface CourseNoteResource {
  title: string;
  unit?: number | null;
  url: string;
  source: string;
}

export interface CourseResourceGroup {
  courseId: number;
  courseName: string;
  courseCode: string;
  semester: number;
  syllabusUrl?: string | null;
  pyqsCount: number;
  notesCount: number;
  pyqs: CourseExamResource[];
  notes: CourseNoteResource[];
}

const resourcesMap: Record<string, CourseResourceGroup> = courseResourcesData as any;

/**
 * Get verified PYQs, notes, and syllabus links for any course by slug.
 */
export function getCourseResources(courseSlug: string): CourseResourceGroup | null {
  if (!courseSlug) return null;
  const lower = courseSlug.toLowerCase().trim();
  
  if (resourcesMap[lower]) {
    return resourcesMap[lower];
  }

  // Fuzzy match on slug keys
  const matchKey = Object.keys(resourcesMap).find(
    (k) => k.toLowerCase() === lower || lower.includes(k.toLowerCase()) || k.toLowerCase().includes(lower)
  );

  return matchKey ? resourcesMap[matchKey] : null;
}

/**
 * Get verified resources by course ID
 */
export function getCourseResourcesById(courseId: number): CourseResourceGroup | null {
  if (!courseId) return null;
  const match = Object.values(resourcesMap).find((r) => r.courseId === courseId);
  return match || null;
}
