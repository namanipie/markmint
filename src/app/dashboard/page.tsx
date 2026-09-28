"use client";

import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  BookOpen,
  Calculator,
  CalendarCheck2,
  Dna,
  Leaf,
  Sparkles,
  Target,
} from "lucide-react";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";

const tools = [
  {
    href: "/mintai",
    label: "MintAI",
    description: "Analyze your course history and explore evidence-backed exam intelligence.",
    icon: Sparkles,
    primary: true,
  },
  {
    href: "/dashboard/exam-dna",
    label: "Exam DNA",
    description: "Explore historical paper structure, question formats, syllabus focus, and recurrence.",
    icon: Dna,
  },
  {
    href: "/study-plan",
    label: "Study Plan",
    description: "Turn your selected course and exam target into a focused study workflow.",
    icon: Target,
  },
  {
    href: "/courses",
    label: "Courses",
    description: "Browse the SRMIST course catalogue and available historical exam evidence.",
    icon: BookOpen,
  },
  {
    href: "/calculator",
    label: "GPA Calculator",
    description: "Calculate your semester GPA and keep the academic admin nonsense contained.",
    icon: Calculator,
  },
];

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-background text-foreground font-sans">
      <Navbar />

      <main className="mx-auto w-full max-w-7xl px-6 py-10 md:px-10 md:py-14">
        <section className="mb-10 max-w-3xl">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-accent/20 bg-accent/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-accent">
            <Leaf className="h-3.5 w-3.5" />
            MintAI Dashboard
          </div>

          <h1 className="text-4xl font-bold tracking-tight md:text-5xl">
            Your academic intelligence hub.
          </h1>

          <p className="mt-4 max-w-2xl text-base leading-relaxed text-muted-foreground md:text-lg">
            One place to move from historical evidence to an actual study workflow.
            MintAI connects your course, exam history, study plan, and analysis without
            making you hunt through five unrelated pages.
          </p>
        </section>

        <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {tools.map((tool) => {
            const Icon = tool.icon;

            return (
              <Link
                key={tool.href}
                href={tool.href}
                className={[
                  "group rounded-2xl border p-6 transition-all duration-200",
                  "hover:-translate-y-0.5 hover:border-accent/40 hover:shadow-lg",
                  tool.primary
                    ? "border-accent/30 bg-accent/5"
                    : "border-border bg-card",
                ].join(" ")}
              >
                <div className="flex items-start justify-between gap-4">
                  <div
                    className={[
                      "flex h-11 w-11 items-center justify-center rounded-xl border",
                      tool.primary
                        ? "border-accent/20 bg-accent/10 text-accent"
                        : "border-border bg-background text-muted-foreground",
                    ].join(" ")}
                  >
                    <Icon className="h-5 w-5" />
                  </div>

                  <ArrowRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-1 group-hover:text-accent" />
                </div>

                <h2 className="mt-6 text-lg font-semibold">{tool.label}</h2>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  {tool.description}
                </p>
              </Link>
            );
          })}
        </section>

        <section className="mt-8 grid gap-4 md:grid-cols-2">
          <Link
            href="/dashboard/exam-dna"
            className="group rounded-2xl border border-border bg-card p-6 transition-all hover:border-accent/40 hover:shadow-lg"
          >
            <div className="flex items-center gap-3">
              <BarChart3 className="h-5 w-5 text-accent" />
              <h2 className="font-semibold">Deep historical analysis</h2>
            </div>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              Jump directly into the full Exam DNA workspace, including assessment
              blueprints, cognitive demand, question formats, syllabus focus, temporal
              trends, and recurrence patterns.
            </p>
            <span className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-accent">
              Open Exam DNA <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </span>
          </Link>

          <Link
            href="/study-plan"
            className="group rounded-2xl border border-border bg-card p-6 transition-all hover:border-accent/40 hover:shadow-lg"
          >
            <div className="flex items-center gap-3">
              <CalendarCheck2 className="h-5 w-5 text-accent" />
              <h2 className="font-semibold">Continue studying</h2>
            </div>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              Move from analysis into an actual plan instead of admiring charts until
              the exam mysteriously arrives.
            </p>
            <span className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-accent">
              Open Study Plan <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </span>
          </Link>
        </section>
      </main>

      <Footer />
    </div>
  );
}
