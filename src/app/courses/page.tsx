import { Metadata } from "next";
import Link from "next/link";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { getAllCourses } from "@/lib/courses";
import { CourseDirectoryView } from "@/components/courses/course-directory-view";
import { ChevronRight, Leaf, BookOpen, Sparkles } from "lucide-react";

export const metadata: Metadata = {
  title: "Engineering Courses & Exam Intelligence Directory | MarkMint SRMIST",
  description:
    "Explore all 23 SRMIST B.Tech Semester 1 & 2 engineering courses. Access verified historical past question papers, syllabus topic breakdowns, high-yield exam predictions, and assessment blueprints.",
  alternates: {
    canonical: "https://markmint.vercel.app/courses",
  },
  openGraph: {
    title: "Engineering Courses & Exam Intelligence Directory | MarkMint SRMIST",
    description:
      "Explore all 23 SRMIST B.Tech Semester 1 & 2 engineering courses. Access verified historical past question papers, syllabus topic breakdowns, and exam predictions.",
    url: "https://markmint.vercel.app/courses",
    siteName: "MarkMint",
    type: "website",
  },
};

export default function CoursesPage() {
  const courses = getAllCourses();

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground selection:bg-accent/20 font-sans">
      <Navbar />

      <main className="flex-1 w-full max-w-7xl mx-auto px-6 md:px-10 py-10 space-y-12">
        {/* Breadcrumbs */}
        <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-xs text-muted-foreground">
          <Link href="/" className="hover:text-foreground transition-colors">
            Home
          </Link>
          <ChevronRight className="w-3.5 h-3.5" />
          <span className="text-foreground font-medium">Courses</span>
        </nav>

        {/* Hero Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-border/40">
          <div className="max-w-2xl space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent/10 border border-accent/20 text-xs font-semibold text-accent uppercase tracking-wider">
              <Sparkles className="w-3.5 h-3.5" />
              SRMIST Regulation 2021 Curriculum
            </div>
            <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground">
              Course Discovery & Exam Intelligence
            </h1>
            <p className="text-base text-muted-foreground leading-relaxed">
              Authoritative syllabus breakdowns, past question papers, and empirical recurrence intelligence for all First-Year Engineering courses at SRMIST.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/mintai"
              className="px-5 py-3 bg-foreground text-background text-sm font-medium rounded-xl hover:bg-foreground/90 transition-all active:scale-[0.98] flex items-center gap-2 shadow-sm"
            >
              <Leaf className="w-4 h-4 text-accent" />
              Open MintAI Engine
            </Link>
          </div>
        </div>

        {/* Client Interactive Directory */}
        <CourseDirectoryView courses={courses} />
      </main>

      <Footer />
    </div>
  );
}
