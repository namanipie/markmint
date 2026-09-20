import { Metadata } from "next";
import { notFound } from "next/navigation";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { 
  getLanguageTrackTopic, 
  getAllLanguageTopicParams, 
  getTopicsForLanguageTrack 
} from "@/lib/topics";
import { TopicDetailView } from "@/components/courses/topic-detail-view";
import { CourseTracker } from "@/components/courses/course-tracker";

interface PageProps {
  params: Promise<{
    language: string;
    topic: string;
  }>;
}

export async function generateStaticParams() {
  return getAllLanguageTopicParams();
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { language, topic: topicSlug } = await params;
  const topic = getLanguageTrackTopic(language, topicSlug);

  if (!topic) {
    return {
      title: "Language Topic Not Found | MarkMint",
      description: "The requested language track topic could not be found.",
    };
  }

  const title = `${topic.name} - ${topic.languageName} (${topic.trackCode}) PYQs & Topics | MarkMint`;
  const description = `Language-isolated past exam papers, appearance counts, and question lineage for ${topic.name} under Unit ${topic.unitNumber} (${topic.unitName}) of ${topic.languageName} at SRMIST.`;

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

export default async function LanguageTopicPage({ params }: PageProps) {
  const { language, topic: topicSlug } = await params;
  const topic = getLanguageTrackTopic(language, topicSlug);

  if (!topic) {
    notFound();
  }

  // Sibling topics strictly isolated to this language track and unit
  const trackTopics = getTopicsForLanguageTrack(language);
  const siblingTopics = trackTopics.filter((t) => t.unitNumber === topic.unitNumber);

  // Structured Data (JSON-LD)
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "LearningResource",
    name: topic.name,
    description: topic.description,
    educationalLevel: "Undergraduate Foreign Language Track",
    learningResourceType: "Past Examination Question Analysis",
    about: {
      "@type": "Course",
      name: `Foreign Languages - ${topic.languageName}`,
      courseCode: topic.trackCode,
      provider: {
        "@type": "Organization",
        name: "MarkMint",
        url: "https://markmint.vercel.app",
      },
    },
    isPartOf: {
      "@type": "Course",
      name: "Foreign Languages",
      url: "https://markmint.vercel.app/courses/foreign-languages",
    },
  };

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground selection:bg-accent/20 font-sans">
      <Navbar />
      <CourseTracker courseSlug={`foreign-languages-${topic.languageKey}`} />

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
