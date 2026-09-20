import rawCourses from './courses-catalog.json';

export interface CourseUnitCatalogItem {
  number: number;
  name: string;
  topicCount: number;
  topics: string[];
}

export interface HighYieldTopicItem {
  topic: string;
  unitNumber: number;
  questionCount: number;
  paperCount: number;
}

export interface CourseTrackCatalogItem {
  trackKey: string;
  trackName: string;
  trackCode: string;
  paperCount: number;
  questionCount: number;
  units: CourseUnitCatalogItem[];
  highYieldTopics: HighYieldTopicItem[];
  mintAiUrl: string;
  practiceUrl: string;
}

export interface AssessmentCycleItem {
  cycle: string;
  label: string;
  units: number[];
  coverageDescription: string;
}

export interface CourseCatalogItem {
  id: number;
  slug: string;
  aliases: string[];
  name: string;
  code: string;
  canonicalCode: string;
  semester: number;
  regulation: string;
  credits: number;
  description: string;
  paperCount: number;
  questionCount: number;
  mappedQuestionCount: number;
  mappingRate: number;
  hasTracks: boolean;
  tracks: CourseTrackCatalogItem[];
  units: CourseUnitCatalogItem[];
  assessmentCycles: AssessmentCycleItem[];
  highYieldTopics: HighYieldTopicItem[];
  mintAiUrl: string;
  practiceUrl: string;
}

export const coursesCatalog: CourseCatalogItem[] = rawCourses as CourseCatalogItem[];

// Map of all slugs and aliases to canonical course
const slugToCourseMap = new Map<string, CourseCatalogItem>();
for (const course of coursesCatalog) {
  slugToCourseMap.set(course.slug.toLowerCase(), course);
  for (const alias of course.aliases) {
    slugToCourseMap.set(alias.toLowerCase(), course);
  }
}

export function getAllCourses(): CourseCatalogItem[] {
  return coursesCatalog;
}

export function getCourseBySlug(slug: string): CourseCatalogItem | undefined {
  if (!slug) return undefined;
  return slugToCourseMap.get(slug.toLowerCase().trim());
}

export function getCanonicalSlug(identifier: string): string | undefined {
  const course = getCourseBySlug(identifier);
  return course ? course.slug : undefined;
}

export function getCoursesBySemester(semester: number): CourseCatalogItem[] {
  return coursesCatalog.filter((c) => c.semester === semester);
}

export function getAllCourseSlugs(): string[] {
  return coursesCatalog.map((c) => c.slug);
}
