"use client";

import React from "react";
import { Leaf } from "lucide-react";
import { motion } from "framer-motion";

export function GrowingMint({ progressStr }: { progressStr: string }) {
  // Parse something like "75%" to 75
  const numericProgress = parseInt(progressStr.replace("%", "")) || 0;
  
  // Max 5 leaves
  const totalLeaves = 5;
  const activeLeaves = Math.max(1, Math.floor((numericProgress / 100) * totalLeaves));

  return (
    <div className="flex items-end gap-1 mt-2 h-8 relative">
      {/* A simple stalk line */}
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-0.5 bg-emerald-500/20 rounded-full transition-all duration-1000" style={{ height: `${Math.max(20, numericProgress)}%` }} />
      
      {/* We position leaves sprouting up */}
      {[...Array(totalLeaves)].map((_, i) => {
        const isActive = i < activeLeaves;
        // Alternate left and right for leaves, moving up the stalk
        const isLeft = i % 2 === 0;
        const xOffset = isLeft ? -10 : 10;
        const rotate = isLeft ? -45 : 45;
        const bottom = i * 8; // move up vertically
        const delay = i * 0.15;

        return (
          <motion.div
            key={i}
            initial={{ scale: 0, opacity: 0 }}
            animate={{ 
              scale: isActive ? 1 : 0.3, 
              opacity: isActive ? 1 : 0.2,
              rotate: isActive ? rotate : 0,
            }}
            transition={{ duration: 0.5, delay: isActive ? delay : 0, type: "spring" }}
            className={`absolute left-1/2 -ml-2`}
            style={{ bottom: `${bottom}px`, transform: `translateX(${xOffset}px)` }}
          >
            <Leaf 
              className={`w-4 h-4 ${isActive ? 'text-emerald-500 drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'text-emerald-500/30'}`} 
              fill={isActive ? 'currentColor' : 'none'} 
            />
          </motion.div>
        );
      })}
    </div>
  );
}
