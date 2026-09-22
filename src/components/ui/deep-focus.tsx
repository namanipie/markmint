"use client";

import { useState, useEffect, useCallback } from 'react';
import { Moon } from 'lucide-react';

export function DeepFocusToggle() {
  const [isActive, setIsActive] = useState(false);

  const playAmbientChord = useCallback(() => {
    try {
      const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
      const ctx = new AudioContext();
      
      // E minor 9 chord for a very calm, ethereal feel
      // E3 (164.81), G3 (196.00), B3 (246.94), D4 (293.66), F#4 (369.99)
      const chord = [164.81, 196.00, 246.94, 293.66, 369.99];
      
      const masterGain = ctx.createGain();
      masterGain.gain.setValueAtTime(0, ctx.currentTime);
      masterGain.gain.linearRampToValueAtTime(0.15, ctx.currentTime + 1.5); // slow fade in
      masterGain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 6); // very slow fade out
      masterGain.connect(ctx.destination);
      
      // Gentle lowpass filter to make it sound muffled and soothing
      const filter = ctx.createBiquadFilter();
      filter.type = "lowpass";
      filter.frequency.setValueAtTime(800, ctx.currentTime);
      filter.frequency.linearRampToValueAtTime(300, ctx.currentTime + 6);
      filter.connect(masterGain);

      chord.forEach((freq, i) => {
        const osc = ctx.createOscillator();
        osc.type = "sine";
        // Slight organic detune
        osc.frequency.value = freq + (Math.random() * 1.5 - 0.75); 
        
        // Slight stereo spread
        const panner = ctx.createStereoPanner ? ctx.createStereoPanner() : null;
        if (panner) {
          panner.pan.value = (i % 2 === 0 ? -0.4 : 0.4);
          osc.connect(panner);
          panner.connect(filter);
        } else {
          osc.connect(filter);
        }
        
        osc.start();
        osc.stop(ctx.currentTime + 6);
      });
    } catch(e) {}
  }, []);

  const toggle = () => {
    if (!isActive) {
      playAmbientChord();
    }
    setIsActive(!isActive);
  };

  // When active, append a div to body
  useEffect(() => {
    if (isActive) {
      document.body.classList.add("deep-focus-active");
      
      const bg = document.createElement("div");
      bg.id = "deep-focus-bg";
      // Removed blur, just dimming the screen to lower contrast
      bg.className = "fixed inset-0 pointer-events-none z-[40] opacity-0 transition-opacity duration-1000";
      bg.style.backgroundColor = "rgba(0, 0, 0, 0.65)";
      
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
