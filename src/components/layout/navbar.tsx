"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Leaf, Menu, X, Flame } from "lucide-react";
import { HangingLamp } from "@/components/ambient/HangingLamp";
import { cn } from "@/lib/utils";
import { useStreak } from "@/hooks/use-streak";
import { DeepFocusToggle } from "@/components/ui/deep-focus";

import { preloadCurriculumMetadata } from "@/lib/api";

export function Navbar({ onMenuClick }: { onMenuClick?: () => void }) {
  const pathname = usePathname();
  const streak = useStreak();

  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    

  const links = [
    { href: "/", label: "Home" },
    { href: "/courses", label: "Courses" },
    { href: "/mintai", label: "MintAI" },
    { href: "/study-plan", label: "Study Plan" },
    { href: "/calculator", label: "Calculator" },
    { href: "/developers", label: "Developers" },
  ];

  return (
    <header className="relative z-50 flex h-16 items-center justify-between bg-background/90 backdrop-blur-md px-6 md:px-10 transition-all duration-300 border-b border-border/40">
      <div className="flex items-center justify-between w-full">
        
        {/* Left: Logo & SRMIST Tag */}
        <div className="flex flex-col items-start justify-center">
          <Link href="/" className="flex items-center gap-2 group">
            <Leaf className="h-6 w-6 text-accent group-hover:rotate-12 transition-transform duration-300" />
            <span className="text-xl md:text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              MarkMint
              <span className="px-2 py-0.5 rounded-full border border-accent/20 bg-accent/5 text-accent text-[10px] font-medium tracking-wide translate-y-[1px]">v1.0</span>
            </span>
          </Link>
            <span className="text-[10px] tracking-widest text-muted-foreground mt-0.5 ml-8 hidden sm:inline-block">
              For SRMIST Students
            </span>
          </div>

        {/* Center: Navigation */}
        
        <nav className="hidden md:flex items-center gap-8">
          {links.map((link) => {
            const isActive =
              pathname === link.href ||
              (link.href !== "/" && pathname?.startsWith(link.href));
            return (
              <Link
                key={link.href}
                href={link.href}
                onMouseEnter={() => {
                  if (link.href === "/mintai") {
                    preloadCurriculumMetadata();
                  }
                }}
                className={cn(
                  "text-sm font-medium transition-colors hover:text-foreground",
                  isActive
                    ? "text-foreground border-b-2 border-accent pb-1"
                    : "text-muted-foreground"
                )}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
        
        <div className="hidden md:flex items-center gap-3 ml-6 pl-6 border-l border-border/40">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-orange-500/10 border border-orange-500/20" title={`${streak} Day Study Streak`}>
            <Flame className={`w-3.5 h-3.5 ${streak > 2 ? 'text-orange-500 animate-pulse' : 'text-orange-500/80'}`} />
            <span className="text-xs font-bold text-orange-500">{streak}</span>
          </div>
          <DeepFocusToggle />
        </div>
        
        {/* Mobile Menu Toggle */}
        <div className="md:hidden">
          <button onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)} className="p-2 text-muted-foreground hover:text-foreground transition-colors">
            {isMobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

      </div>

      {/* The Hanging Lamp - Flush against the absolute right edge */}
      <div className="absolute right-0 top-1/2 -translate-y-1/2">
        <HangingLamp />
      </div>

      {/* Mobile Menu Dropdown (#5) */}
      {isMobileMenuOpen && (
        <div className="absolute top-20 left-0 w-full bg-background border-b border-border shadow-lg flex flex-col p-4 md:hidden no-print z-40">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setIsMobileMenuOpen(false)}
              className="py-3 px-4 text-sm font-medium border-b border-border/50 text-foreground hover:bg-accent/10 transition-colors"
            >
              {link.label}
            </Link>
          ))}

        </div>
      )}

    </header>
  );
}