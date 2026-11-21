"use client";

import React from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { MintDocs } from "@/components/tools/mint-docs";
import { FileText, Sparkles, ShieldCheck, ArrowLeft } from "lucide-react";

export default function MintDocsPage() {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground relative overflow-hidden">
      <Navbar />
      <main className="flex-1 w-full mx-auto px-4 sm:px-6 md:px-10 pt-8 pb-32 relative z-10 flex flex-col items-center">
        
        {/* Navigation Breadcrumb */}
        <div className="w-full max-w-4xl mb-4">
          <Link
            href="/calculator"
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Academic Suite</span>
          </Link>
        </div>

        {/* Hero Title & Subtitle */}
        <div className="text-center space-y-3 mb-8 max-w-2xl">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-accent/10 border border-accent/20 text-accent text-xs font-semibold">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
            <span>100% Client-Side WebAssembly Processing</span>
          </div>
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-foreground">
            MintDocs PDF Suite
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
            Merge exam papers, extract specific units, and convert handwritten assignment photos to PDF instantly in your browser without file size limits or privacy leaks.
          </p>
        </div>

        <MintDocs />
      </main>
      <Footer />
    </div>
  );
}
