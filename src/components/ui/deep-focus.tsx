"use client";

import { useState, useEffect } from 'react';
import { Moon } from 'lucide-react';

export function DeepFocusToggle() {
  const [isActive, setIsActive] = useState(false);

  const toggle = () => {
    setIsActive(!isActive);
  };

  // When active, append a div to body
  useEffect(() => {
    if (isActive) {
      document.body.classList.add("deep-focus-active");
      
      const bg = document.createElement("div");
      bg.id = "deep-focus-bg";
      bg.className = "fixed inset-0 pointer-events-none z-[40] opacity-0 transition-opacity duration-1000 backdrop-blur-[2px]";
      bg.style.background = "radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.05) 0%, rgba(88, 28, 135, 0.15) 50%, rgba(0, 0, 0, 0.7) 100%)";
      
      document.body.appendChild(bg);
      
      // trigger fade in
      requestAnimationFrame(() => {
        bg.style.opacity = "1";
      });
      
      return () => {
        document.body.classList.remove("deep-focus-active");
        const el = document.getElementById("deep-focus-bg");
        if (el) {
          el.style.opacity = "0";
          setTimeout(() => el.remove(), 1000);
        }
      };
    }
  }, [isActive]);

  return (
    <button 
      onClick={toggle}
      title="Deep Focus Mode"
      className={`hidden md:flex items-center justify-center w-8 h-8 rounded-full transition-all duration-500 ${isActive ? 'bg-indigo-900/50 text-indigo-300 shadow-[0_0_15px_rgba(99,102,241,0.3)]' : 'bg-transparent text-muted-foreground hover:bg-muted/50 hover:text-foreground'}`}
    >
      <Moon className="w-4 h-4" />
    </button>
  );
}
