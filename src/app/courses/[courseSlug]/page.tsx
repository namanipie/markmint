import { Suspense } from "react";
import { Metadata } from "next";
import { notFound, redirect } from "next/navigation";
import { Loader2 } from "lucide-react";
import { 
  getCourseBySlug, 
  getAllSlugsAndAliases
} from "@/lib/courses";
import { CourseTracker } from "@/components/courses/course-tracker";
import { MintAIShell } from "@/components/mintai/mintai-shell";

interface PageProps {
  params: Promise<{ courseSlug: string }>;
}

const LANGUAGE_TRACK_ALIASES: Record<string, string> = {
  german: "german",
  french: "french",
  spanish: "spanish",
  japanese: "japanese",
  korean: "korean",
  chinese: "chinese",
  "21leh104t": "german",
  "21leh101t": "french",
  "21leh103t": "spanish",
  "21leh105t": "japanese",
  "21leh102t": "korean",
  "21leh106t": "chinese",
};

export async function generateStaticParams() {
  return getAllSlugsAndAliases().map((slug) => ({
    courseSlug: slug,
  }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { courseSlug } = await params;
  const lower = courseSlug.toLowerCase();
  const course = getCourseBySlug(courseSlug);

  if (!course) {
    return {
      title: "Course Not Found | MarkMint",
      description: "The requested course could not be found in the MarkMint course directory.",
    };
  }

  // Handle language track specific metadata
  if (LANGUAGE_TRACK_ALIASES[lower] && course.tracks) {
    const trackKey = LANGUAGE_TRACK_ALIASES[lower];
    const track = course.tracks.find((t) => t.trackKey === trackKey);
    if (track) {
      return {
        title: `${track.trackName} (${track.trackCode}) PYQs & Syllabus | MarkMint SRMIST`,
        description: `Verified historical exam question papers, authoritative syllabus units, and isolated exam intelligence for ${track.trackName} (${track.trackCode}) at SRMIST.`,
        alternates: {
          canonical: `https://markmint.vercel.app/courses/foreign-languages?track=${track.trackKey}`,
        },
      };
    }
  }

  const courseDisplayName = `${course.name} (${course.canonicalCode || course.code})`;

  return {
    title: `${courseDisplayName} Academic Workspace | MarkMint`,
    description: `Access verified past papers, exam predictions, syllabus notes, and interactive practice for ${course.name} (${course.code}) at SRMIST on MarkMint.`,
    alternates: {
      canonical: `https://markmint.vercel.app/courses/${course.slug}`,
    },
    openGraph: {
      title: `${courseDisplayName} Academic Workspace | MarkMint`,
      description: `Explore verified past papers, syllabus breakdown, and recurring question trends for ${course.name} at SRMIST.`,
      url: `https://markmint.vercel.app/courses/${course.slug}`,
      siteName: "MarkMint",
      type: "article",
    },
  };
}

export default async function CoursePage({ params }: PageProps) {
  const { courseSlug } = await params;
  const lower = courseSlug.toLowerCase();
  const course = getCourseBySlug(courseSlug);

  if (!course) {
    notFound();
  }

  // If visitor navigated to a language track alias, redirect to the track on foreign-languages
  if (LANGUAGE_TRACK_ALIASES[lower]) {
    redirect(`/courses/foreign-languages?track=${LANGUAGE_TRACK_ALIASES[lower]}`);
  }

  // Canonical redirection for aliases
  if (course.slug !== courseSlug) {
    redirect(`/courses/${course.slug}`);
  }

  // Course Structured Data (JSON-LD)
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Course",
    name: course.name,
    description: course.description,
    courseCode: course.canonicalCode || course.code,
    provider: {
      "@type": "Organization",
      name: "MarkMint",
      url: "https://markmint.vercel.app",
    },
    educationalCredentialAwarded: `${course.credits} Credits, SRMIST Regulation ${course.regulation}`,
    hasCourseInstance: {
      "@type": "CourseInstance",
      courseMode: "blended",
      courseWorkload: `Semester ${course.semester}`,
    },
  };

  return (
    <>
      <CourseTracker
        courseId={course.id}
        courseName={course.name}
        courseCode={course.canonicalCode || course.code}
        courseSlug={course.slug}
        semester={course.semester}
        hasTracks={course.hasTracks}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <Suspense
        fallback={
          <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
            <div className="flex items-center gap-3 text-primary">
              <Loader2 className="w-6 h-6 animate-spin" />
              <span className="text-sm font-medium text-muted-foreground">
                Loading {course.name} Workspace...
              </span>
            </div>
          </div>
        }
      >
        <MintAIShell initialCourseId={course.id} />
      </Suspense>
    </>
  );
}
