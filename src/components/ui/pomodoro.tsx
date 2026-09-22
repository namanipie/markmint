"use client";

import React, { useState, useEffect } from "react";
import { Play, Pause, RotateCcw } from "lucide-react";
import confetti from "canvas-confetti";
import { useUiSounds } from "@/hooks/use-ui-sounds";

export function MintFlowPomodoro() {
  const [timeLeft, setTimeLeft] = useState(25 * 60);
  const [isActive, setIsActive] = useState(false);
  const { playChime, playPop } = useUiSounds();

  useEffect(() => {
    let interval: any = null;
    if (isActive && timeLeft > 0) {
      interval = setInterval(() => {
        setTimeLeft((time) => time - 1);
      }, 1000);
    } else if (timeLeft === 0 && isActive) {
      setIsActive(false);
      playChime();
      confetti({
        particleCount: 150,
        spread: 80,
        origin: { y: 0.5 },
        colors: ['#10b981', '#34d399', '#f472b6']
      });
    }
    return () => clearInterval(interval);
  }, [isActive, timeLeft, playChime]);

  const toggle = () => {
    playPop();
    setIsActive(!isActive);
  };
  const reset = () => {
    playPop();
    setIsActive(false);
    setTimeLeft(25 * 60);
  };

  const mins = Math.floor(timeLeft / 60).toString().padStart(2, "0");
  const secs = (timeLeft % 60).toString().padStart(2, "0");
  const progress = ((25 * 60 - timeLeft) / (25 * 60)) * 100;
  
  // SVG Circle calculations
  const radius = 24;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  return (
    <div className="flex items-center gap-4 bg-card border border-border p-3 rounded-full shadow-sm w-fit">
      <div className="relative w-14 h-14 flex items-center justify-center">
        {/* Background circle */}
        <svg className="w-14 h-14 -rotate-90" viewBox="0 0 56 56">
          <circle cx="28" cy="28" r="24" stroke="currentColor" strokeWidth="3" fill="none" className="text-muted/30" />
          <circle 
            cx="28" 
            cy="28" 
            r="24" 
            stroke="currentColor" 
            strokeWidth="3" 
            fill="none" 
            className="text-accent transition-all duration-1000 ease-linear"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center text-xs font-mono font-bold">
          {mins}:{secs}
        </div>
      </div>
      
      <div className="flex flex-col justify-center">
        <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Mint Flow</span>
        <div className="flex items-center gap-2 mt-1">
          <button onClick={toggle} className="w-6 h-6 rounded-full bg-accent/10 hover:bg-accent/20 flex items-center justify-center text-accent transition-colors">
            {isActive ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3 ml-0.5" />}
          </button>
          <button onClick={reset} className="w-6 h-6 rounded-full bg-muted/50 hover:bg-muted flex items-center justify-center text-muted-foreground transition-colors">
            <RotateCcw className="w-3 h-3" />
          </button>
        </div>
      </div>
    </div>
  );
}
