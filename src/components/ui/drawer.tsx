"use client";

import * as React from "react";
import { X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  children: React.ReactNode;
}

export function Drawer({ isOpen, onClose, title, subtitle, children }: DrawerProps) {
  // ESC to close
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
      // Lock body scroll to prevent double scrolling
      document.body.style.overflow = "hidden";
    }
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [isOpen, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm"
          />
          {/* Drawer Panel */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed inset-y-0 right-0 z-50 w-full md:max-w-xl bg-card border-l border-border shadow-2xl flex flex-col"
          >
            {/* Header */}
            <div className="flex items-start justify-between p-6 border-b border-border bg-card z-10 shrink-0">
              <div className="flex flex-col gap-1 pr-6">
                <h2 className="text-xl font-bold text-foreground leading-tight">{title}</h2>
                {subtitle && <div className="text-sm text-muted-foreground">{subtitle}</div>}
              </div>
              <button
                onClick={onClose}
                className="shrink-0 p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                aria-label="Close panel"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {children}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
