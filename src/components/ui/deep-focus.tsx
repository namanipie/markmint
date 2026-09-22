"use client";

import { useState, useEffect, useCallback, useRef } from 'react';
import { Moon } from 'lucide-react';

export function DeepFocusToggle() {
  const [isActive, setIsActive] = useState(false);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const masterGainRef = useRef<GainNode | null>(null);
  const oscillatorsRef = useRef<OscillatorNode[]>([]);

  const stopAmbientSound = useCallback((immediate = false) => {
    if (audioCtxRef.current && masterGainRef.current) {
      const ctx = audioCtxRef.current;
      const gain = masterGainRef.current;
      
      if (immediate) {
        gain.gain.cancelScheduledValues(ctx.currentTime);
        gain.gain.setValueAtTime(0, ctx.currentTime);
        oscillatorsRef.current.forEach(osc => {
          try { osc.stop(); } catch (e) {}
        });
        oscillatorsRef.current = [];
      } else {
        // Smooth 2-second fade out
        gain.gain.cancelScheduledValues(ctx.currentTime);
        gain.gain.setValueAtTime(gain.gain.value, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 2);
        
        setTimeout(() => {
          oscillatorsRef.current.forEach(osc => {
            try { osc.stop(); } catch (e) {}
          });
          oscillatorsRef.current = [];
        }, 2100);
      }
    }
  }, []);

  const startAmbientSound = useCallback(() => {
    try {
      const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
      if (!audioCtxRef.current) {
        audioCtxRef.current = new AudioContext();
      }
      const ctx = audioCtxRef.current;
      
      if (ctx.state === 'suspended') {
        ctx.resume();
      }

      // Clear any existing drones
      stopAmbientSound(true);
      
      // E minor 9 chord for a very calm, ethereal feel
      const chord = [164.81, 196.00, 246.94, 293.66, 369.99];
      
      const masterGain = ctx.createGain();
      masterGain.gain.setValueAtTime(0, ctx.currentTime);
      masterGain.gain.linearRampToValueAtTime(0.08, ctx.currentTime + 3); // 3-second gentle fade in
      masterGain.connect(ctx.destination);
      masterGainRef.current = masterGain;
      
      // Gentle lowpass filter for a muffled, atmospheric sound
      const filter = ctx.createBiquadFilter();
      filter.type = "lowpass";
      filter.frequency.value = 400; // Base cutoff frequency
      filter.connect(masterGain);

      // Create a slow LFO to gently modulate the filter cutoff (breathing effect)
      const lfo = ctx.createOscillator();
      lfo.type = "sine";
      lfo.frequency.value = 0.1; // 1 cycle every 10 seconds
      const lfoGain = ctx.createGain();
      lfoGain.gain.value = 150; // Modulate frequency by +/- 150Hz
      lfo.connect(lfoGain);
      lfoGain.connect(filter.frequency);
      lfo.start();
      oscillatorsRef.current.push(lfo);

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
        oscillatorsRef.current.push(osc);
      });
    } catch(e) {}
  }, [stopAmbientSound]);

  const toggle = () => {
    if (!isActive) {
      startAmbientSound();
    } else {
      stopAmbientSound();
    }
    setIsActive(!isActive);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopAmbientSound(true);
    };
  }, [stopAmbientSound]);

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
      className={`hidden md:flex items-center justify-center w-8 h-8 rounded-full transition-all duration-500 ${isActive ? 'bg-indigo-900/50 text-indigo-300 shadow-[0_0_15px_rgba(99,102,241,0.3)]' : 'bg-transparent text-muted-foreground hover:bg-muted/50 hover:text-foreground'}`}
    >
      <Moon className="w-4 h-4" />
    </button>
  );
}
