import rawTopics from './topics-catalog.json';

export interface PaperOccurrence {
  id: number;
  title: string;
  year: number;
  term: string;
  assessmentType: string;
}

export interface QuestionFamilyOccurrence {
  id: number;
  name: string;
  repetitionType: string;
  count: number;
}

export interface SampleQuestionItem {
  id: number;
  text: string;
  marks: number;
  year: number;
  assessmentType: string;
}

export interface TopicCatalogItem {
  id: number;
  slug: string;
  name: string;
  description: string;
  courseId: number;
  courseSlug: string;
  courseName: string;
  courseCode: string;
  canonicalCode: string;
  isLanguageTrack: boolean;
  languageKey: string | null;
  languageName: string | null;
  trackCode: string | null;
  unitNumber: number;
  unitName: string;
  appearanceCount: number;
  paperCount: number;
  papers: PaperOccurrence[];
  assessmentAppearances: {
    CT1: number;
    CT2: number;
    EndSem: number;
    Internal: number;
    Other: number;
  };
  marksDistribution: Record<string, number>;
  questionFamilies: QuestionFamilyOccurrence[];
  sampleQuestions: SampleQuestionItem[];
  practiceUrl: string;
  mintAiUrl: string;
  canonicalUrl: string;
}

export const topicsCatalog: TopicCatalogItem[] = rawTopics as TopicCatalogItem[];

const standardTopicMap = new Map<string, TopicCatalogItem>();
const languageTopicMap = new Map<string, TopicCatalogItem>();
const topicNameToSlugMap = new Map<string, string>();

for (const t of topicsCatalog) {
  if (t.isLanguageTrack && t.languageKey) {
    const key = `${t.languageKey.toLowerCase()}:${t.slug.toLowerCase()}`;
    languageTopicMap.set(key, t);
    topicNameToSlugMap.set(`${t.languageKey.toLowerCase()}:${t.name.toLowerCase()}`, t.slug);
  } else {
    const key = `${t.courseSlug.toLowerCase()}:${t.slug.toLowerCase()}`;
    standardTopicMap.set(key, t);
    topicNameToSlugMap.set(`${t.courseSlug.toLowerCase()}:${t.name.toLowerCase()}`, t.slug);
  }
}

export function findTopicSlug(scope: string, topicName: string): string | undefined {
  if (!scope || !topicName) return undefined;
  return topicNameToSlugMap.get(`${scope.toLowerCase().trim()}:${topicName.toLowerCase().trim()}`);
}

export function getAllTopics(): TopicCatalogItem[] {
  return topicsCatalog;
}

export function getTopic(courseSlug: string, topicSlug: string): TopicCatalogItem | undefined {
  if (!courseSlug || !topicSlug) return undefined;
  return standardTopicMap.get(`${courseSlug.toLowerCase().trim()}:${topicSlug.toLowerCase().trim()}`);
}

export function getLanguageTrackTopic(languageKey: string, topicSlug: string): TopicCatalogItem | undefined {
  if (!languageKey || !topicSlug) return undefined;
  return languageTopicMap.get(`${languageKey.toLowerCase().trim()}:${topicSlug.toLowerCase().trim()}`);
}

export function getTopicsForCourse(courseSlug: string): TopicCatalogItem[] {
  const norm = courseSlug.toLowerCase().trim();
  return topicsCatalog.filter((t) => !t.isLanguageTrack && t.courseSlug.toLowerCase() === norm);
}

export function getTopicsForLanguageTrack(languageKey: string): TopicCatalogItem[] {
  const norm = languageKey.toLowerCase().trim();
  return topicsCatalog.filter((t) => t.isLanguageTrack && t.languageKey?.toLowerCase() === norm);
}

export function getTopicsForUnit(courseSlug: string, unitNumber: number): TopicCatalogItem[] {
  return getTopicsForCourse(courseSlug).filter((t) => t.unitNumber === unitNumber);
}

export function getAllStandardTopicParams(): { courseSlug: string; topicSlug: string }[] {
  return topicsCatalog
    .filter((t) => !t.isLanguageTrack)
    .map((t) => ({
      courseSlug: t.courseSlug,
      topicSlug: t.slug,
    }));
}

export function getAllLanguageTopicParams(): { language: string; topic: string }[] {
  return topicsCatalog
    .filter((t) => t.isLanguageTrack && t.languageKey)
    .map((t) => ({
      language: t.languageKey as string,
      topic: t.slug,
    }));
}
