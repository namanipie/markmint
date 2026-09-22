import { Metadata } from "next";
import { notFound, redirect } from "next/navigation";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { 
  getTopic, 
  getAllStandardTopicParams, 
  getTopicsForUnit, 
  getAllTopics 
} from "@/lib/topics";
import { getCourseBySlug } from "@/lib/courses";
import { TopicDetailView } from "@/components/courses/topic-detail-view";
import { CourseTracker } from "@/components/courses/course-tracker";

interface PageProps {
  params: Promise<{
    courseSlug: string;
    topicSlug: string;
  }>;
}

export async function generateStaticParams() {
  return getAllStandardTopicParams();
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { courseSlug, topicSlug } = await params;
  const canonicalCourse = getCourseBySlug(courseSlug);
  const resolvedCourseSlug = canonicalCourse ? canonicalCourse.slug : courseSlug;
  const topic = getTopic(resolvedCourseSlug, topicSlug);

  if (!topic) {
    return {
      title: "Topic Not Found | MarkMint",
      description: "The requested curriculum topic could not be found.",
    };
  }

  const title = `${topic.name} - ${topic.courseName} (${topic.canonicalCode || topic.courseCode}) PYQs | MarkMint`;
  const description = `Historical past exam papers, appearance counts, assessment cycle weightage, and recurring questions for ${topic.name} under Unit ${topic.unitNumber} (${topic.unitName}) of ${topic.courseName} at SRMIST.`;

  return {
    title,
    description,
    alternates: {
      canonical: topic.canonicalUrl,
    },
    openGraph: {
      title,
      description,
      url: topic.canonicalUrl,
      siteName: "MarkMint",
      type: "article",
    },
  };
}

export default async function CourseTopicPage({ params }: PageProps) {
  const { courseSlug, topicSlug } = await params;
  const canonicalCourse = getCourseBySlug(courseSlug);

  if (!canonicalCourse) {
    notFound();
  }

  // Handle course alias redirect (e.g. /courses/calc/topics/... -> /courses/calculus-and-linear-algebra/topics/...)
  if (canonicalCourse.slug !== courseSlug) {
    redirect(`/courses/${canonicalCourse.slug}/topics/${topicSlug}`);
  }

  // If someone accessed a foreign language topic via standard route, redirect to language-isolated route
  if (courseSlug === "foreign-languages") {
    const allTopics = getAllTopics();
    const flTopic = allTopics.find(
      (t) => t.isLanguageTrack && t.slug.toLowerCase() === topicSlug.toLowerCase()
    );
    if (flTopic && flTopic.languageKey) {
      redirect(`/courses/foreign-languages/${flTopic.languageKey}/topics/${flTopic.slug}`);
    }
  }

  const topic = getTopic(canonicalCourse.slug, topicSlug);

  if (!topic) {
    notFound();
  }

  const siblingTopics = getTopicsForUnit(topic.courseSlug, topic.unitNumber);

  // Structured Data (JSON-LD)
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "LearningResource",
    name: topic.name,
    description: topic.description,
    educationalLevel: "Undergraduate Engineering (B.Tech)",
    learningResourceType: "Past Examination Question Analysis",
    about: {
      "@type": "Course",
      name: topic.courseName,
      courseCode: topic.canonicalCode || topic.courseCode,
      provider: {
        "@type": "Organization",
        name: "MarkMint",
        url: "https://markmint.vercel.app",
      },
    },
    isPartOf: {
      "@type": "Course",
      name: topic.courseName,
      url: `https://markmint.vercel.app/courses/${topic.courseSlug}`,
    },
  };

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground selection:bg-accent/20 font-sans">
      <Navbar />
      <CourseTracker courseSlug={topic.courseSlug} />

      {/* Structured Data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <main className="flex-1 w-full max-w-7xl mx-auto px-6 md:px-10 py-10">
        <TopicDetailView topic={topic} siblingTopics={siblingTopics} />
      </main>

      <Footer />
    </div>
  );
}
