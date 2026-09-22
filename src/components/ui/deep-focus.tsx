"use client";

import { useState, useEffect, useCallback, useRef } from 'react';
import { Moon } from 'lucide-react';

export function DeepFocusToggle() {
  const [isActive, setIsActive] = useState(false);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const masterGainRef = useRef<GainNode | null>(null);
  const isPlayingRef = useRef(false);

  const startGenerativeAmbient = useCallback(() => {
    try {
      const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
      if (!audioCtxRef.current) {
        audioCtxRef.current = new AudioContext();
      }
      const ctx = audioCtxRef.current;
      if (ctx.state === 'suspended') ctx.resume();

      isPlayingRef.current = true;
      
      const masterGain = ctx.createGain();
      masterGain.gain.setValueAtTime(0.5, ctx.currentTime); // overall volume
      masterGain.connect(ctx.destination);
      masterGainRef.current = masterGain;

      // E minor pentatonic scale (very calming, sparse, Minecraft-like)
      // E3, G3, A3, B3, D4, E4, G4, A4, B4, D5
      const scale = [164.81, 196.00, 220.00, 246.94, 293.66, 329.63, 392.00, 440.00, 493.88, 587.33];

      // Reverb/Delay effect network to simulate a huge, ambient cavern
      const delay = ctx.createDelay();
      delay.delayTime.value = 0.8;
      
      const feedback = ctx.createGain();
      feedback.gain.value = 0.55; // High feedback for long reverb tail
      
      const filter = ctx.createBiquadFilter();
      filter.type = "lowpass";
      filter.frequency.value = 1000; // Keep it warm and muffled
      
      delay.connect(feedback);
      feedback.connect(filter);
      filter.connect(delay);
      
      // Wet/Dry mix
      delay.connect(masterGain);

      const playRandomNote = () => {
        if (!isPlayingRef.current) return;

        // Pick a random frequency from the scale
        const freq = scale[Math.floor(Math.random() * scale.length)];
        
        const noteGain = ctx.createGain();
        noteGain.gain.setValueAtTime(0, ctx.currentTime);
        // Soft attack (fade in) over 2 seconds
        noteGain.gain.linearRampToValueAtTime(0.12, ctx.currentTime + 2);
        // Long, slow release (fade out) over 8 seconds
        noteGain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 10);

        const osc = ctx.createOscillator();
        osc.type = "sine";
        osc.frequency.value = freq;
        
        // Add a tiny bit of triangle for harmonics (like an electric piano/bell)
        const harmOsc = ctx.createOscillator();
        harmOsc.type = "triangle";
        harmOsc.frequency.value = freq;
        
        const harmGain = ctx.createGain();
        harmGain.gain.value = 0.05; // Keep harmonics very quiet
        harmOsc.connect(harmGain);
        harmGain.connect(noteGain);

        const panner = ctx.createStereoPanner ? ctx.createStereoPanner() : null;
        if (panner) {
          panner.pan.value = Math.random() * 1.6 - 0.8; // Random pan left/right
          noteGain.connect(panner);
          panner.connect(masterGain); // Dry
          panner.connect(delay); // Wet
        } else {
          noteGain.connect(masterGain);
          noteGain.connect(delay);
        }

        osc.connect(noteGain);
        
        osc.start(ctx.currentTime);
        harmOsc.start(ctx.currentTime);
        
        osc.stop(ctx.currentTime + 10);
        harmOsc.stop(ctx.currentTime + 10);

        // Schedule next note randomly between 2s and 6s
        const nextNoteTime = Math.random() * 4000 + 2000;
        setTimeout(playRandomNote, nextNoteTime);
      };

      // Start the generative sequence
      playRandomNote();
      
      // Also play an initial low base note to ground it immediately
      const baseGain = ctx.createGain();
      baseGain.gain.setValueAtTime(0, ctx.currentTime);
      baseGain.gain.linearRampToValueAtTime(0.08, ctx.currentTime + 4);
      baseGain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 15);
      baseGain.connect(masterGain);
      
      const baseOsc = ctx.createOscillator();
      baseOsc.type = "sine";
      baseOsc.frequency.value = 82.41; // E2 (low E)
      baseOsc.connect(baseGain);
      baseOsc.start(ctx.currentTime);
      baseOsc.stop(ctx.currentTime + 15);

    } catch(e) {}
  }, []);

  const stopGenerativeAmbient = useCallback(() => {
    isPlayingRef.current = false;
    if (audioCtxRef.current && masterGainRef.current) {
      const ctx = audioCtxRef.current;
      const gain = masterGainRef.current;
      
      // Fade out the entire master mix over 3 seconds
      gain.gain.cancelScheduledValues(ctx.currentTime);
      gain.gain.setValueAtTime(gain.gain.value, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 3);
      
      setTimeout(() => {
        if (!isPlayingRef.current) {
          try { gain.disconnect(); } catch(e) {}
        }
      }, 3100);
    }
  }, []);

  const toggle = () => {
    if (!isActive) {
      startGenerativeAmbient();
    } else {
      stopGenerativeAmbient();
    }
    setIsActive(!isActive);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopGenerativeAmbient();
    };
  }, [stopGenerativeAmbient]);

  // When active, append a div to body
  useEffect(() => {
    if (isActive) {
      document.body.classList.add("deep-focus-active");
      
      const bg = document.createElement("div");
      bg.id = "deep-focus-bg";
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
      className={`flex items-center justify-center w-8 h-8 rounded-full transition-all duration-500 ${isActive ? 'bg-indigo-900/50 text-indigo-300 shadow-[0_0_15px_rgba(99,102,241,0.3)]' : 'bg-transparent text-muted-foreground hover:bg-muted/50 hover:text-foreground'}`}
    >
      <Moon className="w-4 h-4" />
    </button>
  );
}
