/* eslint-disable @next/next/no-img-element */
"use client";

import { useState } from "react";

export default function PosterPage() {
  const [activeTab, setActiveTab] = useState<"promotional" | "technical">("promotional");

  return (
    <div className="min-h-screen bg-[#040605] text-white flex flex-col items-center py-8 px-4 font-sans">
      
      {/* Top Floating Control Bar */}
      <div className="sticky top-4 z-50 flex flex-wrap items-center justify-between gap-4 bg-[#0d1410]/95 backdrop-blur-md border border-[#E6327A]/30 px-6 py-3 rounded-full shadow-2xl mb-8 max-w-4xl w-full">
        
        {/* Tab Switcher */}
        <div className="flex items-center gap-2 bg-[#141e18] p-1 rounded-full border border-white/10">
          <button
            onClick={() => setActiveTab("promotional")}
            className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all ${
              activeTab === "promotional"
                ? "bg-[#E6327A] text-white shadow-[0_0_12px_rgba(230,50,122,0.4)]"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Promotional Edition (MintAI)
          </button>
          <button
            onClick={() => setActiveTab("technical")}
            className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all ${
              activeTab === "technical"
                ? "bg-[#8B5CF6] text-white shadow-[0_0_12px_rgba(139,92,246,0.4)]"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Technical Blueprint
          </button>
        </div>

        {/* Quick Actions */}
        <div className="flex items-center gap-3">
          {activeTab === "promotional" ? (
            <>
              <a
                href="/promotional-poster.png"
                download="MarkMint-Promotional-Poster-A4.png"
                className="px-3 py-1.5 rounded-full bg-white/10 hover:bg-white/15 text-xs font-semibold text-white border border-white/10 transition-colors"
              >
                Download 300 DPI PNG
              </a>
              <a
                href="/promotional-poster.svg"
                target="_blank"
                className="px-3 py-1.5 rounded-full bg-white/10 hover:bg-white/15 text-xs font-semibold text-white border border-white/10 transition-colors"
              >
                Vector SVG
              </a>
              <a
                href="/promotional-poster.html"
                target="_blank"
                className="px-3.5 py-1.5 rounded-full bg-[#E6327A] hover:bg-[#FF2E7E] text-xs font-semibold text-white shadow-[0_0_14px_rgba(230,50,122,0.4)] transition-all"
              >
                Print / PDF (A4)
              </a>
            </>
          ) : (
            <>
              <a
                href="/poster.png"
                download="MarkMint-A4-Poster-Clean.png"
                className="px-3 py-1.5 rounded-full bg-white/10 hover:bg-white/15 text-xs font-semibold text-white border border-white/10 transition-colors"
              >
                Download Clean PNG
              </a>
              <a
                href="/poster-with-qr.png"
                download="MarkMint-A4-Poster-With-QR.png"
                className="px-3 py-1.5 rounded-full bg-white/10 hover:bg-white/15 text-xs font-semibold text-white border border-white/10 transition-colors"
              >
                Download With QR
              </a>
              <a
                href="/poster.html"
                target="_blank"
                className="px-3.5 py-1.5 rounded-full bg-[#8B5CF6] hover:bg-[#7C3AED] text-xs font-semibold text-white shadow-[0_0_14px_rgba(139,92,246,0.4)] transition-all"
              >
                Print / PDF (A4)
              </a>
            </>
          )}
        </div>
      </div>

      {/* Poster Preview Frame */}
      <div className="w-full max-w-[820px] shadow-2xl rounded-xl overflow-hidden border border-white/10 bg-[#070b09]">
        {activeTab === "promotional" ? (
          <img
            src="/promotional-poster.png"
            alt="MarkMint Promotional Poster - A4 Portrait"
            className="w-full h-auto object-contain block"
          />
        ) : (
          <img
            src="/poster.png"
            alt="MarkMint Technical Poster - A4 Portrait"
            className="w-full h-auto object-contain block"
          />
        )}
      </div>

      <div className="mt-8 text-center text-xs font-mono text-slate-500 max-w-lg leading-relaxed">
        Standard ISO 216 A4 Portrait (210 × 297 mm) · 300 DPI High-Contrast Print Specification · Built for SRMIST Campus Circulation
      </div>
    </div>
  );
}
