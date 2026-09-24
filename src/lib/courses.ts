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

export function getYearForSemester(semester: number): number {
  if (semester === 1 || semester === 2) return 1;
  if (semester === 3 || semester === 4) return 2;
  return Math.max(1, Math.ceil(semester / 2));
}

export function getCoursesByYear(year: number): CourseCatalogItem[] {
  return coursesCatalog.filter((c) => getYearForSemester(c.semester) === year);
}

export interface YearSemesterGroup {
  year: number;
  yearLabel: string;
  semesters: {
    semester: number;
    semesterLabel: string;
    courses: CourseCatalogItem[];
  }[];
}

export function groupCoursesByYearAndSemester(
  courses: CourseCatalogItem[] = coursesCatalog
): YearSemesterGroup[] {
  const groups: YearSemesterGroup[] = [
    {
      year: 1,
      yearLabel: "Year 1",
      semesters: [
        { semester: 1, semesterLabel: "Semester 1", courses: [] },
        { semester: 2, semesterLabel: "Semester 2", courses: [] },
      ],
    },
    {
      year: 2,
      yearLabel: "Year 2",
      semesters: [
        { semester: 3, semesterLabel: "Semester 3", courses: [] },
        { semester: 4, semesterLabel: "Semester 4", courses: [] },
      ],
    },
  ];

  for (const course of courses) {
    let placed = false;
    for (const yg of groups) {
      for (const sg of yg.semesters) {
        if (sg.semester === course.semester) {
          sg.courses.push(course);
          placed = true;
          break;
        }
      }
      if (placed) break;
    }

    if (!placed) {
      // Dynamic grouping for any additional semesters
      const courseYear = getYearForSemester(course.semester);
      let yg = groups.find((g) => g.year === courseYear);
      if (!yg) {
        yg = {
          year: courseYear,
          yearLabel: `Year ${courseYear}`,
          semesters: [],
        };
        groups.push(yg);
      }
      let sg = yg.semesters.find((s) => s.semester === course.semester);
      if (!sg) {
        sg = {
          semester: course.semester,
          semesterLabel: `Semester ${course.semester}`,
          courses: [],
        };
        yg.semesters.push(sg);
      }
      sg.courses.push(course);
    }
  }

  return groups;
}

export function getAllCourseSlugs(): string[] {
  return coursesCatalog.map((c) => c.slug);
}

export function getAllSlugsAndAliases(): string[] {
  const set = new Set<string>();
  for (const c of coursesCatalog) {
    set.add(c.slug);
    for (const a of c.aliases) {
      set.add(a.toLowerCase());
    }
  }
  return Array.from(set);
}

