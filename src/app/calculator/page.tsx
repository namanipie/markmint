"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { TargetMarksCalculator } from "@/components/calculator/target-marks-calculator";
import { ScopeCalculator } from "@/components/calculator/ScopeCalculator";
import { CgpaCalculator } from "@/components/calculator/cgpa-calculator";
import { KMapSolver } from "@/components/tools/kmap-solver";
import { Target, Award, Calculator, Binary, FileText, Sparkles } from "lucide-react";

export type AcademicToolTab = "target" | "sgpa" | "cgpa" | "kmap";

export default function CalculatorPage() {
  const [activeTab, setActiveTab] = useState<AcademicToolTab>("target");

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground relative overflow-hidden">
      <Navbar />
      <main className="flex-1 w-full mx-auto px-4 sm:px-6 md:px-10 pt-8 pb-32 relative z-10 flex flex-col items-center">
        
        {/* Hero Title & Subtitle */}
        <div className="text-center space-y-3 mb-8 max-w-2xl">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-accent/10 border border-accent/20 text-accent text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Academic Intelligence &amp; Engineering Tools</span>
          </div>
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-foreground">
            Academic Suite
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
            Calculate exact End-Sem target marks based on your internals, simulate SGPA/CGPA under SRM regulations, and solve engineering logic maps.
          </p>
        </div>

        {/* Tab Navigation Pill */}
        <div className="flex items-center gap-1.5 p-1.5 bg-muted/20 border border-border/70 rounded-2xl mb-8 max-w-full overflow-x-auto shadow-2xs">
          <button
            type="button"
            onClick={() => setActiveTab("target")}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
              activeTab === "target"
                ? "bg-foreground text-background shadow-xs font-extrabold"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/30"
            }`}
          >
            <Target className="w-4 h-4 text-accent" />
            <span>Target Marks Predictor</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("sgpa")}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
              activeTab === "sgpa"
                ? "bg-foreground text-background shadow-xs font-extrabold"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/30"
            }`}
          >
            <Calculator className="w-4 h-4 text-accent" />
            <span>SGPA Calculator</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("cgpa")}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
              activeTab === "cgpa"
                ? "bg-foreground text-background shadow-xs font-extrabold"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/30"
            }`}
          >
            <Award className="w-4 h-4 text-accent" />
            <span>Cumulative CGPA</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("kmap")}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
              activeTab === "kmap"
                ? "bg-foreground text-background shadow-xs font-extrabold"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/30"
            }`}
          >
            <Binary className="w-4 h-4 text-accent" />
            <span>K-Map Logic Solver</span>
          </button>

          <Link
            href="/tools/pdf"
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap text-muted-foreground hover:text-foreground hover:bg-muted/30 border-l border-border/60 ml-1 pl-3"
          >
            <FileText className="w-4 h-4 text-accent" />
            <span>MintDocs PDF Tools &rarr;</span>
          </Link>
        </div>

        {/* Tab Content Display */}
        <div className="w-full">
          {activeTab === "target" && <TargetMarksCalculator />}
          {activeTab === "sgpa" && <ScopeCalculator />}
          {activeTab === "cgpa" && <CgpaCalculator />}
          {activeTab === "kmap" && <KMapSolver />}
        </div>
      </main>
      <Footer />
    </div>
  );
}
