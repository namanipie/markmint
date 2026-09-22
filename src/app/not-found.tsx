"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Home } from "lucide-react";

type Stage = "NORMAL" | "ASTEROID" | "DESTRUCTION" | "BEAM" | "VOID" | "RESOLVED";

/* Real Mean, menacing cartoon asteroid with blazing fire tail, angry furrowed brow, glowing molten eyes, and jagged teeth */
function MeanAsteroid({ className }: { className?: string }) {
  return (
    <svg 
      viewBox="0 0 340 240" 
      className={className} 
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
    >
      <defs>
        {/* Fire gradients */}
        <linearGradient id="fireOuter" x1="0%" y1="100%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#ef4444" stopOpacity="0.9" />
          <stop offset="50%" stopColor="#f97316" stopOpacity="0.8" />
          <stop offset="100%" stopColor="#dc2626" stopOpacity="0" />
        </linearGradient>
        <linearGradient id="fireInner" x1="0%" y1="100%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#fef08a" stopOpacity="1" />
          <stop offset="40%" stopColor="#f59e0b" stopOpacity="0.9" />
          <stop offset="100%" stopColor="#ea580c" stopOpacity="0" />
        </linearGradient>
        <linearGradient id="magmaGlow" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#f97316" />
          <stop offset="100%" stopColor="#b91c1c" />
        </linearGradient>
        <radialGradient id="eyeGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#fef08a" />
          <stop offset="60%" stopColor="#f97316" />
          <stop offset="100%" stopColor="#dc2626" />
        </radialGradient>
      </defs>

      {/* --- FLAMING COMET TAILS (Streaming to the top-right) --- */}
      {/* Outer red/orange flames */}
      <path
        d="M 130 110 C 180 90, 240 70, 310 30 C 270 70, 290 100, 335 85 C 275 110, 260 135, 305 145 C 240 145, 210 165, 250 190 C 190 165, 150 155, 120 145 Z"
        fill="url(#fireOuter)"
      />
      {/* Mid yellow/orange fiery core */}
      <path
        d="M 125 115 C 165 100, 210 80, 275 50 C 245 80, 255 105, 295 95 C 245 115, 230 135, 270 140 C 215 140, 185 155, 220 175 C 170 155, 140 145, 115 135 Z"
        fill="url(#fireInner)"
      />
      {/* Flying burning sparks & embers */}
      <circle cx="320" cy="45" r="4" fill="#fef08a" className="animate-pulse" />
      <circle cx="280" cy="25" r="3" fill="#f97316" />
      <circle cx="330" cy="115" r="3.5" fill="#fef08a" />
      <circle cx="295" cy="165" r="4" fill="#ea580c" />
      <circle cx="240" cy="205" r="2.5" fill="#fbbf24" />

      {/* --- ASTEROID CRAGGY MAIN BODY --- */}
      {/* Menacing dark volcanic rock silhouette */}
      <path
        d="M 60 90 C 70 65, 100 50, 130 55 C 155 60, 175 80, 170 110 C 168 135, 175 155, 155 175 C 135 195, 105 195, 80 190 C 55 185, 35 170, 30 145 C 25 125, 40 105, 60 90 Z"
        fill="#1c1917"
        stroke="#292524"
        strokeWidth="3"
      />

      {/* Rock volume highlights & shading */}
      <path
        d="M 62 92 C 72 70, 98 58, 125 62 C 140 65, 150 75, 155 90 C 140 85, 115 88, 95 100 C 75 112, 60 125, 52 145 C 40 135, 45 110, 62 92 Z"
        fill="#292524"
      />

      {/* Glowing molten magma fissures */}
      <path
        d="M 125 65 Q 115 85, 130 100 T 145 125"
        stroke="url(#magmaGlow)"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <path
        d="M 45 115 Q 60 120, 70 135 T 65 160"
        stroke="url(#magmaGlow)"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <path
        d="M 95 185 Q 110 175, 125 180"
        stroke="url(#magmaGlow)"
        strokeWidth="2"
        strokeLinecap="round"
      />

      {/* Craters with fiery depth */}
      <ellipse cx="140" cy="85" rx="10" ry="7" fill="#0c0a09" stroke="#78350f" strokeWidth="1.5" />
      <ellipse cx="141" cy="86" rx="6" ry="4" fill="#451a03" />
      <ellipse cx="48" cy="155" rx="8" ry="6" fill="#0c0a09" stroke="#78350f" strokeWidth="1.5" />

      {/* --- REAL MEAN ANGRY FACE --- */}
      {/* Heavy, jagged, angry slanted brow ridge */}
      <polygon points="45,98 85,112 105,108 85,102 50,92" fill="#0c0a09" />
      <polygon points="105,108 125,112 155,95 145,90 122,104" fill="#0c0a09" />
      
      {/* Fierce angry furrow line between the eyes */}
      <path d="M 100 105 L 105 116 L 110 105" stroke="#ea580c" strokeWidth="2.5" strokeLinecap="round" />

      {/* Left glowing eye (aggressive downward slant) */}
      <polygon points="56,105 84,116 78,124 54,114" fill="#451a03" />
      <polygon points="58,107 82,116 76,122 56,114" fill="url(#eyeGlow)" />
      <ellipse cx="70" cy="115" rx="4" ry="5" fill="#0c0a09" transform="rotate(-15, 70, 115)" />
      <circle cx="68" cy="113" r="1.5" fill="#ffffff" />

      {/* Right glowing eye (aggressive downward slant) */}
      <polygon points="126,116 150,103 148,114 128,123" fill="#451a03" />
      <polygon points="128,116 148,105 146,112 130,121" fill="url(#eyeGlow)" />
      <ellipse cx="138" cy="114" rx="4" ry="5" fill="#0c0a09" transform="rotate(15, 138, 114)" />
      <circle cx="136" cy="112" r="1.5" fill="#ffffff" />

      {/* Menacing snarling mouth with sharp jagged volcanic fangs */}
      {/* Mouth cave with deep lava glow */}
      <path
        d="M 62 142 Q 102 136, 142 140 Q 128 168, 102 170 Q 74 168, 62 142 Z"
        fill="#450a0a"
        stroke="#1c1917"
        strokeWidth="2"
      />
      {/* Fiery lava throat interior */}
      <path
        d="M 72 148 Q 102 144, 132 146 Q 120 162, 102 164 Q 82 162, 72 148 Z"
        fill="url(#magmaGlow)"
        opacity="0.85"
      />

      {/* Top jagged sharp fangs */}
      <polygon points="68,142 74,152 80,143" fill="#fef08a" stroke="#78350f" strokeWidth="1" />
      <polygon points="82,143 88,155 94,143" fill="#fef08a" stroke="#78350f" strokeWidth="1" />
      <polygon points="96,143 102,154 108,143" fill="#fef08a" stroke="#78350f" strokeWidth="1" />
      <polygon points="110,143 116,155 122,143" fill="#fef08a" stroke="#78350f" strokeWidth="1" />
      <polygon points="124,143 130,151 136,142" fill="#fef08a" stroke="#78350f" strokeWidth="1" />

      {/* Bottom jagged sharp fangs */}
      <polygon points="76,165 82,155 88,164" fill="#fef08a" stroke="#78350f" strokeWidth="1" />
      <polygon points="92,166 98,154 104,166" fill="#fef08a" stroke="#78350f" strokeWidth="1" />
      <polygon points="108,166 114,156 120,165" fill="#fef08a" stroke="#78350f" strokeWidth="1" />
    </svg>
  );
}

export default function NotFound() {
  const [stage, setStage] = useState<Stage>("NORMAL");

  useEffect(() => {
    // 1. Wait a moment, then asteroid strikes in
    const t1 = setTimeout(() => setStage("ASTEROID"), 1500);
    // 2. Direct impact! Explosion and site destruction
    const t2 = setTimeout(() => setStage("DESTRUCTION"), 2500);
    // 3. Blinding high beam whiteout flash
    const t3 = setTimeout(() => setStage("BEAM"), 4500);
    // 4. Fade to calm starry void
    const t4 = setTimeout(() => setStage("VOID"), 6000);
    // 5. Show 404 message and Return Home action
    const t5 = setTimeout(() => setStage("RESOLVED"), 8500);

    return () => {
      clearTimeout(t1); 
      clearTimeout(t2); 
      clearTimeout(t3); 
      clearTimeout(t4); 
      clearTimeout(t5);
    };
  }, []);

  return (
    <div className="fixed inset-0 w-full h-full overflow-hidden bg-background font-sans select-none">
      
      <style jsx>{`
        /* Asteroid streak: hurtles down from top-right towards screen center */
        @keyframes asteroidStrike {
          0% { 
            transform: translate(55vw, -130vh) scale(0.6) rotate(15deg); 
            opacity: 0;
          }
          10% {
            opacity: 1;
          }
          85% {
            transform: translate(8vw, -15vh) scale(2.2) rotate(-5deg);
            opacity: 1;
          }
          100% { 
            transform: translate(0, 0) scale(3.5) rotate(-15deg); 
            opacity: 1;
          }
        }
        .animate-asteroid {
          animation: asteroidStrike 1s cubic-bezier(0.45, 0.05, 0.55, 0.95) forwards;
        }

        /* Violent screen-wide earthquake shake upon impact */
        @keyframes violentShake {
          0%, 100% { transform: translate(0, 0) rotate(0deg); }
          10% { transform: translate(-24px, 18px) rotate(-3deg); }
          20% { transform: translate(22px, -20px) rotate(3deg); }
          30% { transform: translate(-18px, -15px) rotate(-2deg); }
          40% { transform: translate(16px, 18px) rotate(2deg); }
          50% { transform: translate(-14px, 12px) rotate(-1deg); }
          60% { transform: translate(12px, -10px) rotate(1deg); }
          70% { transform: translate(-8px, -8px) rotate(-0.5deg); }
          80% { transform: translate(6px, 6px) rotate(0.5deg); }
          90% { transform: translate(-3px, 2px) rotate(0deg); }
        }
        .animate-violent-shake {
          animation: violentShake 2s cubic-bezier(.36,.07,.19,.97) both;
        }

        /* Impact fireball shockwave expanding from impact epicenter */
        @keyframes impactBlast {
          0% { 
            transform: translate(-50%, -50%) scale(0.2); 
            opacity: 1; 
          }
          35% { 
            transform: translate(-50%, -50%) scale(2.8); 
            opacity: 0.95; 
          }
          70% { 
            transform: translate(-50%, -50%) scale(5.5); 
            opacity: 0.7; 
          }
          100% { 
            transform: translate(-50%, -50%) scale(8); 
            opacity: 0; 
          }
        }
        .animate-impact-blast {
          animation: impactBlast 1.4s cubic-bezier(0.1, 0.8, 0.3, 1) forwards;
        }

        @keyframes impactRing {
          0% { 
            transform: translate(-50%, -50%) scale(0.1); 
            opacity: 1; 
            border-width: 12px;
          }
          100% { 
            transform: translate(-50%, -50%) scale(6); 
            opacity: 0; 
            border-width: 1px;
          }
        }
        .animate-impact-ring {
          animation: impactRing 1.2s ease-out forwards;
        }

        /* Deep space starfield drift */
        .stars-bg {
          background: #000 url('data:image/svg+xml;utf8,<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg"><circle cx="20" cy="20" r="1" fill="white"/><circle cx="150" cy="50" r="1.5" fill="white"/><circle cx="80" cy="120" r="1" fill="white"/><circle cx="180" cy="180" r="0.5" fill="white"/></svg>') repeat;
          animation: drift 100s linear infinite;
        }
        @keyframes drift {
          from { background-position: 0 0; }
          to { background-position: -1000px 1000px; }
        }

        /* Peaceful zero-g float for the lost leaf */
        @keyframes floatSpace {
          0%, 100% { transform: translate(-50%, -50%) translateY(0) rotate(0deg); }
          50% { transform: translate(-50%, -50%) translateY(-18px) rotate(8deg); }
        }
        .animate-float-space {
          animation: floatSpace 6s ease-in-out infinite;
        }
      `}</style>

      {/* --- LAYER 1: The Mock Site (Gets Shattered & Blown Apart) --- */}
      <div 
        className={`absolute inset-0 transition-opacity duration-1000 ${(stage === "BEAM" || stage === "VOID" || stage === "RESOLVED") ? "opacity-0 pointer-events-none" : "opacity-100"} ${stage === "DESTRUCTION" ? "animate-violent-shake" : ""}`}
      >
        <div className="flex flex-col h-full opacity-80 pointer-events-none">
          {/* Fake Navbar */}
          <div className={`w-full h-16 border-b border-border/50 flex items-center px-6 gap-6 transition-all duration-1000 ease-out ${stage === "DESTRUCTION" ? "-translate-y-[300px] rotate-[-15deg] opacity-0" : ""}`}>
            <div className="font-bold text-xl tracking-tight text-emerald-500">MarkMint</div>
            <div className="h-4 w-24 bg-muted rounded"></div>
            <div className="h-4 w-16 bg-muted rounded"></div>
          </div>
          
          {/* Fake Dashboard Content */}
          <div className="flex-1 p-8 flex flex-col md:flex-row gap-8 max-w-6xl mx-auto w-full">
            {/* Sidebar */}
            <div className={`w-full md:w-64 space-y-4 transition-all duration-1000 delay-100 ease-out ${stage === "DESTRUCTION" ? "-translate-x-[60vw] rotate-[-55deg] scale-50 opacity-0" : ""}`}>
              <h3 className="font-bold text-lg text-muted-foreground mb-6">Department</h3>
              <div className="p-4 bg-card border rounded-lg font-bold text-accent shadow-sm">Computer Science &amp; Eng.</div>
              <div className="p-4 bg-muted/30 border border-transparent rounded-lg text-muted-foreground">Electrical Eng.</div>
              <div className="p-4 bg-muted/30 border border-transparent rounded-lg text-muted-foreground">Mechanical Eng.</div>
            </div>
            
            {/* Main Area */}
            <div className="flex-1 space-y-6">
              <h1 className={`text-3xl font-bold transition-all duration-1000 delay-75 ease-out ${stage === "DESTRUCTION" ? "translate-y-[-60vh] rotate-[25deg] scale-150 opacity-0" : ""}`}>Current Courses</h1>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className={`p-6 bg-card border rounded-xl shadow-sm transition-all duration-1000 delay-150 ease-out ${stage === "DESTRUCTION" ? "translate-x-[60vw] translate-y-[-30vh] rotate-[140deg] opacity-0" : ""}`}>
                  <div className="h-3 w-12 bg-accent/20 rounded mb-2"></div>
                  <h2 className="font-bold text-xl mb-2">Data Structures</h2>
                  <p className="text-sm text-muted-foreground">3 Credits • Prof. Sharma</p>
                </div>
                
                <div className={`p-6 bg-card border rounded-xl shadow-sm transition-all duration-1000 delay-200 ease-out ${stage === "DESTRUCTION" ? "translate-x-[40vw] translate-y-[50vh] rotate-[-95deg] scale-75 opacity-0" : ""}`}>
                  <div className="h-3 w-12 bg-accent/20 rounded mb-2"></div>
                  <h2 className="font-bold text-xl mb-2">Operating Systems</h2>
                  <p className="text-sm text-muted-foreground">4 Credits • Prof. Verma</p>
                </div>

                <div className={`p-6 bg-card border rounded-xl shadow-sm transition-all duration-1000 delay-300 ease-out ${stage === "DESTRUCTION" ? "translate-x-[-40vw] translate-y-[60vh] rotate-[80deg] opacity-0" : ""}`}>
                  <div className="h-3 w-12 bg-accent/20 rounded mb-2"></div>
                  <h2 className="font-bold text-xl mb-2">Machine Learning</h2>
                  <p className="text-sm text-muted-foreground">3 Credits • Prof. Singh</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* --- LAYER 2: The Real Mean Asteroid Hurtling In --- */}
      {stage === "ASTEROID" && (
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 pointer-events-none animate-asteroid">
          <MeanAsteroid className="w-56 h-40 sm:w-72 sm:h-52 drop-shadow-[0_0_60px_rgba(239,68,68,0.9)] filter drop-shadow-[0_0_100px_rgba(249,115,22,0.8)]" />
        </div>
      )}

      {/* --- LAYER 2B: Direct Impact Explosion Blast Shockwave --- */}
      {stage === "DESTRUCTION" && (
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 pointer-events-none w-1 h-1">
          {/* Central expanding fireball */}
          <div className="animate-impact-blast absolute top-1/2 left-1/2 w-64 h-64 rounded-full bg-gradient-to-r from-red-600 via-orange-500 to-yellow-400 blur-2xl opacity-90" />
          {/* Shockwave pressure ring */}
          <div className="animate-impact-ring absolute top-1/2 left-1/2 w-80 h-80 rounded-full border-yellow-300 border-solid" />
        </div>
      )}

      {/* --- LAYER 3: Blinding Whiteout Flash --- */}
      <div 
        className={`absolute inset-0 bg-white z-[60] pointer-events-none transition-opacity duration-[1200ms] ${stage === "BEAM" ? "opacity-100" : "opacity-0"}`} 
      />

      {/* --- LAYER 4: The Peaceful Void & Lost Leaf --- */}
      <div 
        className={`absolute inset-0 z-[70] stars-bg transition-opacity duration-1000 flex flex-col items-center justify-center ${(stage === "VOID" || stage === "RESOLVED") ? "opacity-100" : "opacity-0 pointer-events-none"}`}
      >
        {/* Floating Lost Leaf */}
        <div className={`absolute top-1/2 left-1/2 animate-float-space transition-all duration-1000 ${stage === "RESOLVED" ? "scale-75 opacity-30 -translate-y-[15vh]" : "scale-100 opacity-85"}`}>
          <div className="relative">
            <div className="absolute inset-0 bg-emerald-500 rounded-full blur-[50px] opacity-30"></div>
            <img 
              src="/secret-leaf.png" 
              alt="Lost Leaf" 
              className="w-24 h-24 sm:w-32 sm:h-32 drop-shadow-[0_0_20px_rgba(16,185,129,0.7)] brightness-110 object-contain" 
            />
          </div>
        </div>

        {/* 404 Text & Home Button */}
        <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 flex flex-col items-center text-center transition-all duration-[2000ms] ease-out ${stage === "RESOLVED" ? "opacity-100 translate-y-0" : "opacity-0 translate-y-20"}`}>
          <h1 className="text-7xl sm:text-9xl font-black text-white tracking-tighter mb-4 drop-shadow-[0_0_30px_rgba(255,255,255,0.3)]">404</h1>
          <p className="text-xl sm:text-2xl text-gray-400 font-light mb-12 tracking-wide">The site was destroyed.</p>
          
          <Link 
            href="/"
            className="group relative flex items-center gap-3 px-8 py-4 bg-white/10 hover:bg-white/20 text-white border border-white/20 rounded-full font-bold transition-all hover:scale-105 active:scale-95 overflow-hidden shadow-lg shadow-emerald-500/10"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/20 to-teal-500/20 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <Home className="w-5 h-5 relative z-10" />
            <span className="relative z-10 tracking-wide">Return to Safety</span>
          </Link>
        </div>
      </div>

    </div>
  );
}
