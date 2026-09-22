import { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import { Navbar } from "@/components/layout/navbar";
import { MathText } from "@/components/ui/math-text";
import { CourseLandingTracker } from "@/components/analytics/course-landing-tracker";
import { 
  BookOpen, ArrowRight, CheckCircle2, ShieldCheck, 
  BarChart3, Brain, Database, Target, Sparkles
} from "lucide-react";
import { getCourses, getIntelligenceSnapshot } from "@/lib/api";
import { generateSlug, findCourseBySlug } from "@/lib/slugs";

// Revalidate every 24 hours (86400 seconds) since course data is mostly static
export const revalidate = 86400;

export async function generateStaticParams() {
  try {
    const courses = await getCourses();
    return courses.map((course: any) => ({
      course: generateSlug(course.name),
    }));
  } catch (error) {
    console.error("Failed to fetch courses for static params:", error);
    return [];
  }
}

export async function generateMetadata({ params }: { params: { course: string } }): Promise<Metadata> {
  const { course: courseSlug } = params;
  
  try {
    const courses = await getCourses();
    const course = findCourseBySlug(courseSlug, courses);
    
    if (!course) {
      return {
        title: "Course Not Found | MarkMint",
      };
    }
    
    return {
      title: `${course.name} PYQs & Exam Intelligence | MarkMint`,
      description: `${course.name} previous-year questions, recurring exam patterns, study priorities and practice for SRM students.`,
      alternates: {
        canonical: `https://markmint.vercel.app/srm/${generateSlug(course.name)}`,
      },
      openGraph: {
        title: `${course.name} PYQs & Exam Intelligence | MarkMint`,
        description: `Analyze ${course.name} past papers, find recurring patterns, and prioritize your study schedule.`,
        type: "website",
        url: `https://markmint.vercel.app/srm/${generateSlug(course.name)}`,
      },
    };
  } catch {
    return {
      title: "SRM Course Intelligence | MarkMint",
    };
  }
}

export default async function CourseLandingPage({ params }: { params: { course: string } }) {
  const { course: courseSlug } = params;
  
  let courses = [];
  try {
    courses = await getCourses();
  } catch (err) {
    console.error("Failed to fetch courses");
  }

  const course = findCourseBySlug(courseSlug, courses);
  
  if (!course) {
    notFound();
  }

  // Fetch intelligence snapshot for stats
  let snapshot = null;
  try {
    snapshot = await getIntelligenceSnapshot(course.id);
  } catch (err) {
    // Graceful fallback if snapshot isn't available
    console.error(`Failed to fetch intelligence for course ${course.id}`);
  }

  const totalPapers = snapshot?.exam_history?.total_papers || 0;
  const totalQuestions = snapshot?.exam_history?.total_questions || 0;
  const predictionCount = snapshot?.predictions?.length || 0;
  const isFamilyMode = snapshot?.prediction_mode === "family";
  const years = snapshot?.exam_history?.years || [];
  
  const minYear = years.length > 0 ? Math.min(...years) : null;
  const maxYear = years.length > 0 ? Math.max(...years) : null;
  const yearRange = minYear && maxYear ? (minYear === maxYear ? `${minYear}` : `${minYear}-${maxYear}`) : "Recent Years";

  return (
    <div className="flex flex-col min-h-screen bg-background text-foreground selection:bg-accent/20">
      <Navbar />
      <CourseLandingTracker courseId={course.id} courseSlug={courseSlug} />

      <main className="flex-1 w-full pb-20">
        {/* Hero Section */}
        <div className="relative border-b border-border/40 overflow-hidden">
          <div className="absolute inset-0 bg-accent/5 opacity-20" />
          
          <div className="max-w-5xl mx-auto px-6 pt-24 pb-20 relative z-10 flex flex-col items-center text-center">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-accent/10 text-accent text-xs font-bold uppercase tracking-widest mb-6 border border-accent/20">
              <ShieldCheck className="w-3.5 h-3.5" />
              SRMIST Curriculum
            </div>
            
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-4 leading-tight">
              <MathText content={course.name} />
            </h1>
            
            <div className="flex items-center gap-2 text-muted-foreground font-mono bg-secondary px-3 py-1 rounded mb-8">
              <BookOpen className="w-4 h-4" />
              <span>{course.code || "Course Code"}</span>
            </div>
            
            <p className="text-lg md:text-xl text-muted-foreground max-w-2xl leading-relaxed mb-10">
              Stop guessing what to study. MarkMint analyzes past {course.name} exam papers to reveal exactly which topics and questions are most likely to appear next.
            </p>
            
            <Link 
              href="/mintai"
              className="px-8 py-4 bg-accent text-accent-foreground font-bold text-lg rounded-xl hover:opacity-90 transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5 flex items-center gap-3"
            >
              <Brain className="w-5 h-5" />
              <span>Analyze This Course in MintAI</span>
              <ArrowRight className="w-5 h-5 ml-1" />
            </Link>
          </div>
        </div>

        {/* Intelligence Stats */}
        <div className="max-w-5xl mx-auto px-6 py-20">
          <div className="text-center mb-12">
            <h2 className="text-[10px] font-bold tracking-widest uppercase text-muted-foreground mb-2">Empirical Evidence</h2>
            <h3 className="text-3xl font-bold text-foreground">Data-Driven Intelligence</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-card border border-border rounded-2xl p-6 shadow-sm flex flex-col items-center text-center">
              <div className="w-12 h-12 bg-secondary rounded-xl flex items-center justify-center text-muted-foreground mb-4">
                <Database className="w-6 h-6" />
              </div>
              <div className="text-3xl font-mono font-bold text-foreground mb-1">
                {totalPapers > 0 ? totalPapers : "10+"}
              </div>
              <div className="text-sm text-muted-foreground font-medium uppercase tracking-wider">Past Papers Analyzed</div>
            </div>
            
            <div className="bg-card border border-border rounded-2xl p-6 shadow-sm flex flex-col items-center text-center">
              <div className="w-12 h-12 bg-secondary rounded-xl flex items-center justify-center text-muted-foreground mb-4">
                <Target className="w-6 h-6" />
              </div>
              <div className="text-3xl font-mono font-bold text-foreground mb-1">
                {totalQuestions > 0 ? totalQuestions : "150+"}
              </div>
              <div className="text-sm text-muted-foreground font-medium uppercase tracking-wider">Questions Extracted</div>
            </div>
            
            <div className="bg-card border border-border rounded-2xl p-6 shadow-sm flex flex-col items-center text-center relative overflow-hidden">
              <div className="absolute top-0 right-0 p-2 opacity-10">
                <Sparkles className="w-24 h-24 text-accent" />
              </div>
              <div className="w-12 h-12 bg-accent/10 rounded-xl flex items-center justify-center text-accent mb-4 relative z-10">
                <BarChart3 className="w-6 h-6" />
              </div>
              <div className="text-3xl font-mono font-bold text-accent mb-1 relative z-10">
                {predictionCount > 0 ? predictionCount : "5-15"}
              </div>
              <div className="text-sm text-muted-foreground font-medium uppercase tracking-wider relative z-10">
                {isFamilyMode ? "High-Yield Families" : "Predicted Topics"}
              </div>
            </div>
            
            <div className="bg-card border border-border rounded-2xl p-6 shadow-sm flex flex-col items-center text-center">
              <div className="w-12 h-12 bg-secondary rounded-xl flex items-center justify-center text-muted-foreground mb-4">
                <BookOpen className="w-6 h-6" />
              </div>
              <div className="text-3xl font-mono font-bold text-foreground mb-1">
                {yearRange}
              </div>
              <div className="text-sm text-muted-foreground font-medium uppercase tracking-wider">Historical Range</div>
            </div>
          </div>
        </div>

        {/* Feature Overview */}
        <div className="max-w-5xl mx-auto px-6 py-10">
          <div className="bg-card border border-border rounded-2xl p-8 md:p-12 shadow-sm">
            <h3 className="text-2xl font-bold text-foreground mb-8 text-center">What MarkMint Provides for {course.name}</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="flex gap-4">
                <div className="shrink-0 mt-1">
                  <div className="w-8 h-8 rounded-full bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                </div>
                <div>
                  <h4 className="text-lg font-bold text-foreground mb-2">Topic & Question Repetition</h4>
                  <p className="text-muted-foreground text-sm leading-relaxed">
                    We track exactly how many times specific syllabus topics and exact question families have appeared in past {course.code || course.name} exams.
                  </p>
                </div>
              </div>
              
              <div className="flex gap-4">
                <div className="shrink-0 mt-1">
                  <div className="w-8 h-8 rounded-full bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                </div>
                <div>
                  <h4 className="text-lg font-bold text-foreground mb-2">Predictive Forecasts</h4>
                  <p className="text-muted-foreground text-sm leading-relaxed">
                    Get an evidence-based list of what to study first, organized by priority (Study First, Study Next) based on historical weighting.
                  </p>
                </div>
              </div>
              
              <div className="flex gap-4">
                <div className="shrink-0 mt-1">
                  <div className="w-8 h-8 rounded-full bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                </div>
                <div>
                  <h4 className="text-lg font-bold text-foreground mb-2">Actual Past Exam Questions</h4>
                  <p className="text-muted-foreground text-sm leading-relaxed">
                    Practice directly with the actual questions extracted from previous {course.name} papers, tagged by topic and marks.
                  </p>
                </div>
              </div>
              
              <div className="flex gap-4">
                <div className="shrink-0 mt-1">
                  <div className="w-8 h-8 rounded-full bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                </div>
                <div>
                  <h4 className="text-lg font-bold text-foreground mb-2">Study Intelligence Plan</h4>
                  <p className="text-muted-foreground text-sm leading-relaxed">
                    A personalized checklist to track your preparation coverage against the most heavily tested areas of the syllabus.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
