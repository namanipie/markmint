"use client";

import Link from "next/link";
import { ArrowRight, BookOpen, BrainCircuit, LineChart, PencilRuler, PlayCircle, History } from "lucide-react";

export default function Home() {
  return (
    <div className="flex flex-col gap-12 pb-20">
      {/* Hero Section */}
      <section className="bg-card rounded-3xl p-8 lg:p-12 border border-border shadow-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-primary/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3 pointer-events-none" />
        
        <div className="relative z-10 max-w-2xl space-y-6">
          <div>
            <h1 className="text-4xl lg:text-5xl font-black text-foreground tracking-tight leading-tight mb-2">
              Good morning.
            </h1>
            <p className="text-xl text-muted-foreground">Let's get you ready for your exams.</p>
          </div>
          
          <div className="pt-4">
            <Link 
              href="/mintai" 
              className="inline-flex items-center gap-3 px-6 py-4 rounded-xl bg-primary text-primary-foreground font-bold hover:bg-primary/90 transition-all shadow-md group"
            >
              <span>Choose a subject to begin</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>
      </section>

      {/* Quick Stats */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-card p-6 rounded-2xl border border-border hover:border-primary/30 transition-colors">
          <BookOpen className="w-6 h-6 text-primary mb-4" />
          <div className="text-3xl font-black text-foreground mb-1">40+</div>
          <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Branches</div>
        </div>
        <div className="bg-card p-6 rounded-2xl border border-border hover:border-primary/30 transition-colors">
          <BrainCircuit className="w-6 h-6 text-primary mb-4" />
          <div className="text-3xl font-black text-foreground mb-1">800+</div>
          <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Topics Mapped</div>
        </div>
        <div className="bg-card p-6 rounded-2xl border border-border hover:border-primary/30 transition-colors">
          <LineChart className="w-6 h-6 text-primary mb-4" />
          <div className="text-3xl font-black text-foreground mb-1">500+</div>
          <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Past Papers</div>
        </div>
        <div className="bg-card p-6 rounded-2xl border border-border hover:border-primary/30 transition-colors">
          <PencilRuler className="w-6 h-6 text-primary mb-4" />
          <div className="text-3xl font-black text-foreground mb-1">3k+</div>
          <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Questions</div>
        </div>
      </section>

      {/* What should you do next? */}
      <section className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-foreground">What should you do next?</h2>
          <p className="text-muted-foreground mt-1">Jump right back into your workflow.</p>
        </div>
        
        <div className="grid md:grid-cols-3 gap-6">
          <Link href="/study-plan" className="group bg-card p-6 rounded-2xl border border-border hover:border-primary/50 transition-all flex flex-col h-full">
            <div className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center mb-6 group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
              <PlayCircle className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-foreground mb-2">Continue your Study Plan</h3>
            <p className="text-sm text-muted-foreground flex-1">Follow the curated priority list of topics for your selected subjects.</p>
            <div className="mt-6 flex items-center gap-2 text-sm font-bold text-primary opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all">
              <span>View Plan</span>
              <ArrowRight className="w-4 h-4" />
            </div>
          </Link>
          
          <Link href="/practice" className="group bg-card p-6 rounded-2xl border border-border hover:border-primary/50 transition-all flex flex-col h-full">
            <div className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center mb-6 group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
              <PencilRuler className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-foreground mb-2">Practice a Subject</h3>
            <p className="text-sm text-muted-foreground flex-1">Test your knowledge against real historical exam questions.</p>
            <div className="mt-6 flex items-center gap-2 text-sm font-bold text-primary opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all">
              <span>Start Practicing</span>
              <ArrowRight className="w-4 h-4" />
            </div>
          </Link>

          <Link href="/mintai" className="group bg-card p-6 rounded-2xl border border-border hover:border-primary/50 transition-all flex flex-col h-full">
            <div className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center mb-6 group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
              <History className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-foreground mb-2">Explore Repeated Questions</h3>
            <p className="text-sm text-muted-foreground flex-1">See exactly what questions appear year after year.</p>
            <div className="mt-6 flex items-center gap-2 text-sm font-bold text-primary opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all">
              <span>View Analytics</span>
              <ArrowRight className="w-4 h-4" />
            </div>
          </Link>
        </div>
      </section>
    </div>
  );
}
