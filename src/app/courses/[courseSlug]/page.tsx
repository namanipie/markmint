import { Metadata } from "next";
import { notFound, redirect } from "next/navigation";
import Link from "next/link";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { 
  getCourseBySlug, 
  getAllSlugsAndAliases, 
  CourseCatalogItem 
} from "@/lib/courses";
import { findTopicSlug } from "@/lib/topics";
import { ForeignLanguageTracks } from "@/components/courses/foreign-language-tracks";
import { SyllabusUnitExplorer } from "@/components/courses/syllabus-unit-explorer";
import { CourseTracker } from "@/components/courses/course-tracker";
import { MathText } from "@/components/ui/math-text";
import { 
  ChevronRight, 
  FileText, 
  HelpCircle, 
  Layers, 
  TrendingUp, 
  CalendarCheck, 
  BookOpen, 
  CheckCircle2, 
  ArrowRight, 
  ShieldCheck, 
  Sparkles, 
  Dna 
} from "lucide-react";

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
    title: `${courseDisplayName} PYQs, Syllabus & Exam Intelligence | MarkMint`,
    description: `Access verified historical past question papers, syllabus breakdown, high-yield recurring topics, and exam predictions for ${course.name} (${course.code}) at SRMIST on MarkMint.`,
    alternates: {
      canonical: `https://markmint.vercel.app/courses/${course.slug}`,
    },
    openGraph: {
      title: `${courseDisplayName} PYQs & Exam Intelligence | MarkMint`,
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

  // Canonical redirection for aliases (e.g., /courses/spcm -> /courses/semiconductor-physics-and-computational-methods)
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
    <div className="flex min-h-screen flex-col bg-background text-foreground selection:bg-accent/20 font-sans">
      <Navbar />
      <CourseTracker
        courseId={course.id}
        courseName={course.name}
        courseCode={course.canonicalCode || course.code}
        courseSlug={course.slug}
        semester={course.semester}
        hasTracks={course.hasTracks}
      />

      {/* Structured Data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 md:px-10 py-8 space-y-10">
        {/* Breadcrumbs */}
        <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-xs text-muted-foreground">
          <Link href="/" className="hover:text-foreground transition-colors">
            Home
          </Link>
          <ChevronRight className="w-3.5 h-3.5" />
          <Link href="/courses" className="hover:text-foreground transition-colors">
            Courses
          </Link>
          <ChevronRight className="w-3.5 h-3.5" />
          <span className="text-foreground font-medium truncate max-w-[200px] sm:max-w-none">
            {course.name}
          </span>
        </nav>

        {/* Hero Section */}
        <section className="space-y-6 pb-6 border-b border-border/40">
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground font-mono">
            <span className="px-2.5 py-1 rounded-md bg-accent/10 text-accent font-semibold tracking-wide">
              Semester {course.semester}
            </span>
            <span className="px-2.5 py-1 rounded-md bg-secondary text-secondary-foreground font-semibold">
              {course.credits} Credits
            </span>
            <span className="px-2.5 py-1 rounded-md bg-secondary text-secondary-foreground">
              Reg {course.regulation}
            </span>
            <span className="px-2.5 py-1 rounded-md bg-secondary text-secondary-foreground">
              Code: {course.canonicalCode || course.code}
            </span>
          </div>

          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
            <div className="max-w-3xl space-y-3">
              <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-foreground leading-[1.15]">
                {course.name}
              </h1>
              <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
                {course.description}
              </p>
            </div>

            {/* Streamlined Quick Action CTAs */}
            <div className="flex flex-col sm:flex-row lg:flex-col gap-2.5 shrink-0">
              <Link
                href={`/dashboard?course_id=${course.id}#forecast`}
                className="flex items-center justify-center gap-2 px-6 py-3 bg-foreground text-background text-xs sm:text-sm font-semibold rounded-xl hover:bg-foreground/90 transition-all active:scale-[0.98] shadow-xs"
              >
                <Sparkles className="w-4 h-4 text-accent" />
                <span>Analyze in MintAI Forecast</span>
              </Link>
              <Link
                href={`/mintai/exam-dna?course=${course.id}`}
                className="flex items-center justify-center gap-2 px-6 py-3 bg-secondary text-secondary-foreground hover:bg-secondary/80 text-xs sm:text-sm font-semibold rounded-xl border border-border/60 transition-all shadow-2xs"
              >
                <Dna className="w-4 h-4 text-accent" />
                <span>Historical Exam Evidence</span>
              </Link>
            </div>
          </div>
        </section>

        {/* Compact Corpus Metrics Bar */}
        <section className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-4 rounded-xl bg-card border border-border/60 shadow-2xs space-y-1">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              <FileText className="w-3.5 h-3.5 text-accent" />
              <span>Verified Papers</span>
            </div>
            <div className="text-2xl font-bold text-foreground">{course.paperCount}</div>
            <div className="text-[11px] text-muted-foreground">SRMIST Historical Exams</div>
          </div>

          <div className="p-4 rounded-xl bg-card border border-border/60 shadow-2xs space-y-1">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              <HelpCircle className="w-3.5 h-3.5 text-accent" />
              <span>Exam Questions</span>
            </div>
            <div className="text-2xl font-bold text-foreground">{course.questionCount.toLocaleString()}</div>
            <div className="text-[11px] text-muted-foreground">Cataloged &amp; Structured</div>
          </div>

          <div className="p-4 rounded-xl bg-card border border-border/60 shadow-2xs space-y-1">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              <Layers className="w-3.5 h-3.5 text-accent" />
              <span>Syllabus Units</span>
            </div>
            <div className="text-2xl font-bold text-foreground">
              {course.hasTracks ? course.tracks.length * 5 : course.units.length}
            </div>
            <div className="text-[11px] text-muted-foreground">
              {course.hasTracks ? "Across 6 Languages" : "Authoritative Taxonomy"}
            </div>
          </div>

          <div className="p-4 rounded-xl bg-card border border-border/60 shadow-2xs space-y-1">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              <ShieldCheck className="w-4 h-4 text-accent" />
              <span>Curriculum Scope</span>
            </div>
            <div className="text-2xl font-bold text-accent">Active</div>
            <div className="text-[11px] text-muted-foreground">SRMIST B.Tech Reg 2021</div>
          </div>
        </section>

        {/* Assessment Cycles Architecture */}
        {course.assessmentCycles && course.assessmentCycles.length > 0 && (
          <section className="space-y-4">
            <div className="flex items-center gap-2 text-base font-bold text-foreground">
              <CalendarCheck className="w-4 h-4 text-accent" />
              <span>Assessment Architecture &amp; Syllabus Scope</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
              {course.assessmentCycles.map((cycle, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl bg-card border border-border/60 space-y-2 shadow-2xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-foreground text-xs">{cycle.label}</span>
                    <span className="px-2 py-0.5 rounded bg-accent/10 text-accent font-mono text-[11px] font-semibold">
                      {cycle.cycle}
                    </span>
                  </div>
                  <div className="text-xs text-muted-foreground leading-relaxed">
                    Evaluates syllabus {cycle.units.length === 5 ? "Units 1 through 5" : `Units ${cycle.units.join(" & ")}`}.
                  </div>
                  <div className="pt-2 border-t border-border/40 text-[11px] text-muted-foreground leading-relaxed">
                    {cycle.coverageDescription}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Multi-Track vs Single-Track Curriculum */}
        {course.hasTracks ? (
          <section className="space-y-6">
            <div className="space-y-1.5">
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                Authoritative Language Tracks
              </h2>
              <p className="text-xs sm:text-sm text-muted-foreground">
                Foreign Languages encompasses 6 distinct tracks under SRMIST curriculum. Select a track below to view syllabus units, verified questions, and tailored exam predictions.
              </p>
            </div>
            <ForeignLanguageTracks tracks={course.tracks} />
          </section>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Left: Syllabus Units (7 cols) */}
            <section className="lg:col-span-7 space-y-4">
              <div className="space-y-1">
                <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                  Syllabus Units &amp; Topics
                </h2>
                <p className="text-xs sm:text-sm text-muted-foreground">
                  Authoritative SRMIST curriculum breakdown organized by unit and topic.
                </p>
              </div>
              <SyllabusUnitExplorer units={course.units} courseSlug={course.slug} />
            </section>

            {/* Right: High-Yield Topics (5 cols) */}
            <aside className="lg:col-span-5 space-y-4">
              <div className="p-5 rounded-2xl bg-card border border-border/70 space-y-4 shadow-xs">
                <div className="flex items-center gap-2 text-sm font-bold text-foreground">
                  <TrendingUp className="w-4 h-4 text-accent" />
                  <span>High-Yield Recurring Topics</span>
                </div>
                <p className="text-xs text-muted-foreground">
                  Topics with the highest historical recurrence in SRMIST past exam papers for {course.name}.
                </p>

                {course.highYieldTopics && course.highYieldTopics.length > 0 ? (
                  <div className="space-y-2.5">
                    {course.highYieldTopics.map((top, idx) => {
                      const topicSlug = findTopicSlug(course.slug, top.topic);
                      const content = (
                        <div className="p-3 rounded-xl bg-muted/20 hover:bg-muted/40 border border-border/50 hover:border-accent/40 transition-all flex items-start justify-between gap-3 text-xs group cursor-pointer">
                          <div className="space-y-1 min-w-0">
                            <div className="font-semibold text-foreground group-hover:text-accent transition-colors text-xs line-clamp-1">
                              <MathText content={top.topic} inlineOnly />
                            </div>
                            <span className="inline-block px-2 py-0.5 rounded bg-muted text-muted-foreground text-[10px] font-mono">
                              Unit {top.unitNumber}
                            </span>
                          </div>
                          <div className="text-right shrink-0">
                            <div className="font-semibold text-accent">{top.questionCount} questions</div>
                            <div className="text-[10px] text-muted-foreground">{top.paperCount} papers</div>
                          </div>
                        </div>
                      );

                      return topicSlug ? (
                        <Link
                          key={idx}
                          href={`/courses/${course.slug}/topics/${topicSlug}`}
                          className="block"
                        >
                          {content}
                        </Link>
                      ) : (
                        <div key={idx}>{content}</div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="p-4 rounded-xl bg-muted/10 border border-border/40 text-xs text-muted-foreground">
                    Empirical topic mapping is active. Question family repetition analytics are currently calibrated.
                  </div>
                )}

                <div className="pt-3 border-t border-border/40">
                  <Link
                    href={`/dashboard?course_id=${course.id}#forecast`}
                    className="w-full flex items-center justify-center gap-2 py-2.5 bg-foreground text-background text-xs font-semibold rounded-xl hover:bg-foreground/90 transition-all active:scale-[0.98] shadow-xs"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-accent" />
                    <span>View Forecast in MintAI</span>
                  </Link>
                </div>
              </div>
            </aside>
          </div>
        )}

        {/* Bottom CTA Banner */}
        <section className="p-6 sm:p-8 rounded-2xl bg-card border border-border/80 flex flex-col md:flex-row items-center justify-between gap-6 shadow-xs">
          <div className="space-y-1.5 max-w-xl text-center md:text-left">
            <h3 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
              Prepare for your next {course.name} exam
            </h3>
            <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
              Launch MintAI to view probability forecasts, question recurrence matrices, and cycle-specific predictions with verified past paper citations.
            </p>
          </div>

          <Link
            href={`/dashboard?course_id=${course.id}#forecast`}
            className="px-6 py-3 bg-foreground text-background font-semibold rounded-xl hover:bg-foreground/90 transition-all flex items-center gap-2 text-xs sm:text-sm shrink-0 shadow-xs"
          >
            <Sparkles className="w-4 h-4 text-accent" />
            <span>Launch MintAI Engine</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </section>
      </main>

      <Footer />
    </div>
  );
}
