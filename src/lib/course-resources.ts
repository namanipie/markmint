import courseResourcesData from "./course-resources.json";

export interface CourseExamResource {
  title: string;
  examType: "CT1" | "CT2" | "MODEL" | "SURPRISE" | "ENDSEM" | string;
  year?: number | null;
  url: string;
  source: string;
  driveId?: string;
  parentFolder?: string;
}

export interface CourseNoteResource {
  title: string;
  unit?: number | null;
  topicName?: string;
  url: string;
  source: string;
  driveId?: string;
  parentFolder?: string;
  type?: "PPT" | "PDF" | "DOC" | "HANDWRITTEN" | string;
}

export interface CourseVideoResource {
  id: string;
  title: string;
  topicName?: string;
  unit?: number | null;
  youtubeId: string;
  channel: string;
  duration: string;
  description?: string;
}

export interface CourseFormulaResource {
  id: string;
  title: string;
  topicName?: string;
  unit?: number | null;
  summary: string;
  latexSnippet: string;
}

export interface CourseBookResource {
  title: string;
  author?: string;
  edition?: string;
  url: string;
  driveId?: string;
  chapters?: string;
}

export interface CourseResourceGroup {
  courseId: number;
  courseName: string;
  courseCode: string;
  semester: number;
  syllabusUrl?: string | null;
  pyqsCount: number;
  notesCount: number;
  videosCount?: number;
  formulasCount?: number;
  pyqs: CourseExamResource[];
  notes: CourseNoteResource[];
  videos?: CourseVideoResource[];
  formulas?: CourseFormulaResource[];
  books?: CourseBookResource[];
}

export interface TopicResourceBundle {
  courseSlug: string;
  courseName: string;
  topicName: string;
  unit?: number | null;
  hasResources: boolean;
  videos: CourseVideoResource[];
  formulas: CourseFormulaResource[];
  notes: CourseNoteResource[];
  pyqs: CourseExamResource[];
  books: CourseBookResource[];
}

const resourcesMap: Record<string, CourseResourceGroup> = courseResourcesData as any;

/**
 * Extract Google Drive file/folder ID from a sharing URL.
 */
export function extractDriveId(url?: string): string | null {
  if (!url) return null;
  const fileMatch = url.match(/\/file\/d\/([a-zA-Z0-9_-]+)/);
  if (fileMatch) return fileMatch[1];
  const idMatch = url.match(/[?&]id=([a-zA-Z0-9_-]+)/);
  if (idMatch) return idMatch[1];
  const folderMatch = url.match(/\/folders\/([a-zA-Z0-9_-]+)/);
  if (folderMatch) return folderMatch[1];
  return null;
}

/**
 * Generate native Google Drive preview URL suitable for in-app iframe embedding.
 */
export function getDrivePreviewUrl(urlOrDriveId?: string): string | null {
  if (!urlOrDriveId) return null;
  const driveId = urlOrDriveId.includes("drive.google.com")
    ? extractDriveId(urlOrDriveId)
    : urlOrDriveId;
  if (!driveId) return null;
  return `https://drive.google.com/file/d/${driveId}/preview`;
}

/**
 * Generate privacy-enhanced YouTube embed URL.
 */
export function getYouTubeEmbedUrl(youtubeIdOrUrl?: string): string | null {
  if (!youtubeIdOrUrl) return null;
  let id = youtubeIdOrUrl;
  if (youtubeIdOrUrl.includes("youtube.com/watch")) {
    const m = youtubeIdOrUrl.match(/[?&]v=([a-zA-Z0-9_-]+)/);
    if (m) id = m[1];
  } else if (youtubeIdOrUrl.includes("youtu.be/")) {
    const m = youtubeIdOrUrl.match(/youtu\.be\/([a-zA-Z0-9_-]+)/);
    if (m) id = m[1];
  }
  return `https://www.youtube-nocookie.com/embed/${id}?rel=0&modestbranding=1`;
}

/**
 * Get verified PYQs, notes, videos, and syllabus links for any course by slug.
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

/**
 * Find all matching resources (Videos, Formulas, Notes, PYQs) directly mapped to a specific topic name.
 */
export function getTopicResources(
  courseSlugOrId: string | number,
  topicName: string,
  unitNumber?: number | null
): TopicResourceBundle {
  const group = typeof courseSlugOrId === "number"
    ? getCourseResourcesById(courseSlugOrId)
    : getCourseResources(courseSlugOrId);

  const emptyBundle: TopicResourceBundle = {
    courseSlug: typeof courseSlugOrId === "string" ? courseSlugOrId : "",
    courseName: group ? group.courseName : "",
    topicName,
    unit: unitNumber,
    hasResources: false,
    videos: [],
    formulas: [],
    notes: [],
    pyqs: [],
    books: []
  };

  if (!group || !topicName) return emptyBundle;

  const tClean = topicName.toLowerCase().trim();

  // Match videos by topic name, title keyword, or unit fallback
  const directVideos = (group.videos || []).filter((v) => {
    if (v.topicName) {
      const vt = v.topicName.toLowerCase();
      if (vt === tClean || vt.includes(tClean) || tClean.includes(vt)) return true;
    }
    const vTitle = (v.title || "").toLowerCase();
    return vTitle.includes(tClean) || tClean.includes(vTitle);
  });

  const videos = directVideos.length > 0 
    ? directVideos 
    : (unitNumber ? (group.videos || []).filter(v => v.unit === unitNumber) : []);

  // Match formulas by topic name, title keyword, or unit fallback
  const directFormulas = (group.formulas || []).filter((f) => {
    if (f.topicName) {
      const ft = f.topicName.toLowerCase();
      if (ft === tClean || ft.includes(tClean) || tClean.includes(ft)) return true;
    }
    const fTitle = (f.title || "").toLowerCase();
    return fTitle.includes(tClean) || tClean.includes(fTitle);
  });

  const formulas = directFormulas.length > 0
    ? directFormulas
    : (unitNumber ? (group.formulas || []).filter(f => f.unit === unitNumber) : []);

  // Match notes by unit or topic keyword in title
  const notes = (group.notes || []).filter((n) => {
    if (unitNumber && n.unit === unitNumber) return true;
    const nt = (n.title || "").toLowerCase();
    return nt.includes(tClean);
  });

  // Match PYQs by unit or topic keyword in title
  const pyqs = (group.pyqs || []).filter((p) => {
    const pt = (p.title || "").toLowerCase();
    return pt.includes(tClean);
  });

  const books = group.books || [];

  const hasResources = videos.length > 0 || formulas.length > 0 || notes.length > 0 || pyqs.length > 0;

  return {
    courseSlug: typeof courseSlugOrId === "string" ? courseSlugOrId : String(group.courseId),
    courseName: group.courseName,
    topicName,
    unit: unitNumber,
    hasResources,
    videos,
    formulas,
    notes,
    pyqs,
    books
  };
}
