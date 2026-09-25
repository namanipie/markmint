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
import { 
  ChevronRight, 
  Sparkles, 
  FileText, 
  HelpCircle, 
  Layers, 
  TrendingUp, 
  CalendarCheck, 
  BookOpen, 
  CheckCircle2, 
  ArrowRight,
  ShieldCheck,
  Zap,
  ExternalLink,
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

      <main className="flex-1 w-full max-w-7xl mx-auto px-6 md:px-10 py-10 space-y-12">
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
        <section className="space-y-6 pb-8 border-b border-border/40">
          <div className="flex flex-wrap items-center gap-2.5 text-xs text-muted-foreground font-mono">
            <span className="px-2.5 py-1 rounded-md bg-accent/10 text-accent font-semibold tracking-wide">
              Semester {course.semester}
            </span>
            <span className="px-2.5 py-1 rounded-md bg-secondary text-secondary-foreground">
              {course.credits} Credits
            </span>
            <span className="px-2.5 py-1 rounded-md bg-secondary text-secondary-foreground">
              {course.regulation} Regulation
            </span>
            <span className="px-2.5 py-1 rounded-md bg-secondary text-secondary-foreground">
              Code: {course.canonicalCode || course.code}
            </span>
          </div>

          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-8">
            <div className="max-w-3xl space-y-4">
              <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-foreground leading-[1.15]">
                {course.name}
              </h1>
              <p className="text-base text-muted-foreground leading-relaxed">
                {course.description}
              </p>
            </div>

            {/* Quick Action CTAs */}
            <div className="flex flex-col sm:flex-row lg:flex-col gap-3 shrink-0">
              <Link
                href={course.mintAiUrl}
                className="flex items-center justify-center gap-2 px-6 py-3.5 bg-foreground text-background text-sm font-medium rounded-xl hover:bg-foreground/90 transition-all active:scale-[0.98] shadow-sm"
              >
                <Sparkles className="w-4 h-4 text-accent" />
                Analyze in MintAI Engine
              </Link>
              <Link
                href={`/dashboard/exam-dna?course=${course.id}`}
                className="flex items-center justify-center gap-2 px-6 py-3.5 bg-accent/10 hover:bg-accent/20 text-accent text-sm font-medium rounded-xl border border-accent/20 transition-all"
              >
                <Dna className="w-4 h-4" />
                View Course Exam DNA
              </Link>
              <Link
                href={course.practiceUrl}
                className="flex items-center justify-center gap-2 px-6 py-3.5 bg-secondary hover:bg-secondary/80 text-foreground text-sm font-medium rounded-xl border border-border/60 transition-all"
              >
                Practice Exam Questions
                <ExternalLink className="w-3.5 h-3.5 opacity-60" />
              </Link>
            </div>
          </div>
        </section>

        {/* Factual Corpus Metrics Bar */}
        <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-5 rounded-2xl bg-card border border-border/60 shadow-sm">
            <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              <FileText className="w-4 h-4 text-accent" />
              <span>Verified Papers</span>
            </div>
            <div className="text-3xl font-bold text-foreground">{course.paperCount}</div>
            <div className="text-xs text-muted-foreground mt-1">SRMIST Historical Exams</div>
          </div>

          <div className="p-5 rounded-2xl bg-card border border-border/60 shadow-sm">
            <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              <HelpCircle className="w-4 h-4 text-accent" />
              <span>Exam Questions</span>
            </div>
            <div className="text-3xl font-bold text-foreground">{course.questionCount.toLocaleString()}</div>
            <div className="text-xs text-muted-foreground mt-1">Cataloged & Structured</div>
          </div>

          <div className="p-5 rounded-2xl bg-card border border-border/60 shadow-sm">
            <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              <Layers className="w-4 h-4 text-accent" />
              <span>Syllabus Units</span>
            </div>
            <div className="text-3xl font-bold text-foreground">
              {course.hasTracks ? course.tracks.length * 5 : course.units.length}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              {course.hasTracks ? "Across 6 Languages" : "Authoritative Taxonomy"}
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-card border border-border/60 shadow-sm">
            <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              <ShieldCheck className="w-4 h-4 text-accent" />
              <span>Curriculum Scope</span>
            </div>
            <div className="text-3xl font-bold text-accent">Active</div>
            <div className="text-xs text-muted-foreground mt-1">SRMIST B.Tech Reg 2021</div>
          </div>
        </section>

        {/* Why MarkMint Intelligence Is Superior Callout */}
        <section className="p-6 sm:p-8 rounded-2xl bg-secondary/25 border border-border/60 space-y-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-accent uppercase tracking-wider">
            <Zap className="w-4 h-4" />
            <span>MarkMint Deep Intelligence Engine</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-foreground">
            More Than Just Downloadable Question Papers
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed max-w-4xl">
            Generic repositories only dump unindexed PDF scans. MarkMint transforms historical exams into structured intelligence: every question is parsed into its syllabus unit, cross-referenced with recurring question families, and weighted across internal assessments (CT1, CT2) and final semester examinations.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
            <div className="flex items-start gap-3 text-xs text-muted-foreground">
              <CheckCircle2 className="w-4 h-4 text-accent shrink-0 mt-0.5" />
              <span>
                <strong className="text-foreground">Cycle-Specific Blueprint:</strong> Separate prediction models for CT1, CT2, and End Semester calibrated to available historical evidence.
              </span>
            </div>
            <div className="flex items-start gap-3 text-xs text-muted-foreground">
              <CheckCircle2 className="w-4 h-4 text-accent shrink-0 mt-0.5" />
              <span>
                <strong className="text-foreground">Question Family Lineage:</strong> Tracks which conceptual question patterns recur year-after-year.
              </span>
            </div>
            <div className="flex items-start gap-3 text-xs text-muted-foreground">
              <CheckCircle2 className="w-4 h-4 text-accent shrink-0 mt-0.5" />
              <span>
                <strong className="text-foreground">Zero Guesswork:</strong> Every forecast includes verifiable historical paper citations.
              </span>
            </div>
          </div>
        </section>

        {/* Exam DNA Callout Section */}
        <section className="p-6 sm:p-8 rounded-2xl bg-card border border-border/80 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-xs font-semibold text-accent uppercase tracking-wider">
                <Dna className="w-4 h-4" />
                <span>Empirical Examination Architecture</span>
              </div>
              <h2 className="text-xl sm:text-2xl font-bold text-foreground">
                {course.name} Exam DNA
              </h2>
              <p className="text-xs sm:text-sm text-muted-foreground">
                How does this course historically ask questions? Grounded strictly in {course.paperCount} verified historical papers ({course.questionCount.toLocaleString()} questions).
              </p>
            </div>

            <Link
              href={`/dashboard/exam-dna?course=${course.id}`}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-accent text-accent-foreground text-xs font-semibold rounded-xl hover:bg-accent/90 transition-all shrink-0 self-start sm:self-auto shadow-sm"
            >
              <span>Explore Full Exam DNA</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-1">
            <div className="p-4 rounded-xl bg-muted/20 border border-border/50 space-y-1.5">
              <div className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-accent" />
                Unit Distribution
              </div>
              <p className="text-xs text-muted-foreground">
                Marks-weighted historical unit contributions across verified papers.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-muted/20 border border-border/50 space-y-1.5">
              <div className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <BookOpen className="w-3.5 h-3.5 text-accent" />
                Question Types
              </div>
              <p className="text-xs text-muted-foreground">
                Factual distribution of classified and unclassified question archetypes.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-muted/20 border border-border/50 space-y-1.5">
              <div className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-accent" />
                Marks Distribution
              </div>
              <p className="text-xs text-muted-foreground">
                Discrete mark tiers and weight frequencies derived from actual exams.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-muted/20 border border-border/50 space-y-1.5">
              <div className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-accent" />
                Question Patterns
              </div>
              <p className="text-xs text-muted-foreground">
                Deterministic formulation stems and recurring question family lineages.
              </p>
            </div>
          </div>
        </section>

        {/* Assessment Cycles Breakdown */}
        {course.assessmentCycles && course.assessmentCycles.length > 0 && (
          <section className="space-y-5">
            <div className="flex items-center gap-2 text-lg font-bold text-foreground">
              <CalendarCheck className="w-5 h-5 text-accent" />
              <span>Assessment Architecture & Syllabus Scope</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {course.assessmentCycles.map((cycle, idx) => (
                <div
                  key={idx}
                  className="p-5 rounded-xl bg-card border border-border/60 space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-foreground text-sm">{cycle.label}</span>
                    <span className="px-2 py-0.5 rounded bg-accent/10 text-accent font-mono text-xs font-semibold">
                      {cycle.cycle}
                    </span>
                  </div>
                  <div className="text-xs text-muted-foreground leading-relaxed">
                    Evaluates syllabus {cycle.units.length === 5 ? "Units 1 through 5" : `Units ${cycle.units.join(" & ")}`}.
                  </div>
                  <div className="pt-2 border-t border-border/40 text-xs text-muted-foreground leading-relaxed">
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
            <div className="space-y-2">
              <h2 className="text-2xl font-bold tracking-tight text-foreground">
                Authoritative Language Tracks
              </h2>
              <p className="text-sm text-muted-foreground">
                Foreign Languages encompasses 6 distinct tracks under SRMIST curriculum. Select a track below to view syllabus units, verified questions, and tailored exam predictions.
              </p>
            </div>
            <ForeignLanguageTracks tracks={course.tracks} />
          </section>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Left: Syllabus Units (7 cols) */}
            <section className="lg:col-span-7 space-y-6">
              <div className="space-y-1">
                <h2 className="text-2xl font-bold tracking-tight text-foreground">
                  Syllabus Units & Topics
                </h2>
                <p className="text-sm text-muted-foreground">
                  Authoritative SRMIST curriculum breakdown organized by unit and topic.
                </p>
              </div>
              <SyllabusUnitExplorer units={course.units} courseSlug={course.slug} />
            </section>

            {/* Right: High-Yield Topics & Quick Actions (5 cols) */}
            <aside className="lg:col-span-5 space-y-6">
              <div className="p-6 rounded-2xl bg-card border border-border/60 space-y-5 shadow-sm">
                <div className="flex items-center gap-2 text-base font-bold text-foreground">
                  <TrendingUp className="w-4 h-4 text-accent" />
                  <span>High-Yield Recurring Topics</span>
                </div>
                <p className="text-xs text-muted-foreground">
                  Topics with the highest historical recurrence in SRMIST past exam papers for {course.name}.
                </p>

                {course.highYieldTopics && course.highYieldTopics.length > 0 ? (
                  <div className="space-y-3">
                    {course.highYieldTopics.map((top, idx) => {
                      const topicSlug = findTopicSlug(course.slug, top.topic);
                      const content = (
                        <div className="p-3.5 rounded-xl bg-secondary/30 hover:bg-secondary/50 border border-border/40 hover:border-accent/40 transition-all flex items-start justify-between gap-3 text-xs group">
                          <div className="space-y-1">
                            <div className="font-semibold text-foreground group-hover:text-accent transition-colors text-sm line-clamp-1">
                              {top.topic}
                            </div>
                            <span className="inline-block px-2 py-0.5 rounded bg-muted text-muted-foreground text-[10px] font-mono">
                              Unit {top.unitNumber}
                            </span>
                          </div>
                          <div className="text-right shrink-0">
                            <div className="font-semibold text-accent">{top.questionCount} questions</div>
                            <div className="text-[11px] text-muted-foreground">{top.paperCount} papers</div>
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
                  <div className="p-4 rounded-xl bg-secondary/20 border border-border/40 text-xs text-muted-foreground">
                    Empirical topic mapping is being processed for this course. Question family repetition analytics are currently active.
                  </div>
                )}

                <div className="pt-3 border-t border-border/40">
                  <Link
                    href={course.mintAiUrl}
                    className="w-full flex items-center justify-center gap-2 py-3 bg-foreground text-background text-xs font-medium rounded-xl hover:bg-foreground/90 transition-all active:scale-[0.98]"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-accent" />
                    View Probability Matrix in MintAI
                  </Link>
                </div>
              </div>
            </aside>
          </div>
        )}

        {/* Bottom CTA Banner */}
        <section className="p-8 sm:p-10 rounded-2xl bg-foreground text-background flex flex-col md:flex-row items-center justify-between gap-6 shadow-md">
          <div className="space-y-2 max-w-xl text-center md:text-left">
            <h3 className="text-2xl font-bold tracking-tight">
              Prepare for your next {course.name} exam
            </h3>
            <p className="text-sm text-background/80 leading-relaxed">
              Launch MintAI to view probability forecasts, question recurrence matrices, and cycle-specific study plans with direct past paper citations.
            </p>
          </div>

          <Link
            href={course.mintAiUrl}
            className="px-6 py-3.5 bg-background text-foreground font-medium rounded-xl hover:bg-background/90 transition-all flex items-center gap-2 text-sm shrink-0"
          >
            Launch MintAI Engine
            <ArrowRight className="w-4 h-4" />
          </Link>
        </section>
      </main>

      <Footer />
    </div>
  );
}
