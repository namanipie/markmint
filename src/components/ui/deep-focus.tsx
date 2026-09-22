"use client";

import { useState, useEffect, useRef } from 'react';
import { Moon } from 'lucide-react';

declare global {
  interface Window {
    YT: any;
    onYouTubeIframeAPIReady: () => void;
  }
}

export function DeepFocusToggle() {
  const [isActive, setIsActive] = useState(false);
  const playerRef = useRef<any>(null);

  useEffect(() => {
    // Load YouTube API script
    if (!window.YT) {
      const tag = document.createElement('script');
      tag.src = 'https://www.youtube.com/iframe_api';
      const firstScriptTag = document.getElementsByTagName('script')[0];
      if (firstScriptTag?.parentNode) {
        firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
      } else {
        document.head.appendChild(tag);
      }

      window.onYouTubeIframeAPIReady = () => {
        initPlayer();
      };
    } else if (window.YT && window.YT.Player && !playerRef.current) {
      initPlayer();
    }

    function initPlayer() {
      if (playerRef.current) return;
      
      playerRef.current = new window.YT.Player('yt-ambient-player', {
        height: '0',
        width: '0',
        videoId: 'vCTRNKPJr40',
        playerVars: {
          autoplay: 0,
          controls: 0,
          loop: 1,
          playlist: 'vCTRNKPJr40', // Needed for loop to work
          playsinline: 1
        }
      });
    }

    return () => {
      if (playerRef.current && typeof playerRef.current.destroy === 'function') {
        try { playerRef.current.destroy(); } catch (e) {}
      }
    };
  }, []);

  const toggle = () => {
    if (!isActive) {
      if (playerRef.current && typeof playerRef.current.playVideo === 'function') {
        playerRef.current.playVideo();
      }
    } else {
      if (playerRef.current && typeof playerRef.current.pauseVideo === 'function') {
        playerRef.current.pauseVideo();
      }
    }
    setIsActive(!isActive);
  };

  // When active, append a div to body
  useEffect(() => {
    if (isActive) {
      document.body.classList.add("deep-focus-active");
      
      const bg = document.createElement("div");
      bg.id = "deep-focus-bg";
      bg.className = "fixed inset-0 pointer-events-none z-[40] opacity-0 transition-opacity duration-1000";
      bg.style.backgroundColor = "rgba(0, 0, 0, 0.65)";
      
      document.body.appendChild(bg);
      
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
    <>
      {/* Wrapper to protect the iframe from React re-renders */}
      <div 
        style={{ position: 'absolute', width: 0, height: 0, overflow: 'hidden' }} 
        aria-hidden="true" 
        dangerouslySetInnerHTML={{ __html: '<div id="yt-ambient-player"></div>' }}
      />
      <button 
        onClick={toggle}
        title="Deep Focus Mode"
        className={`flex items-center justify-center w-8 h-8 rounded-full transition-all duration-500 ${isActive ? 'bg-indigo-900/50 text-indigo-300 shadow-[0_0_15px_rgba(99,102,241,0.3)]' : 'bg-transparent text-muted-foreground hover:bg-muted/50 hover:text-foreground'}`}
      >
        <Moon className="w-4 h-4" />
      </button>
    </>
  );
}
