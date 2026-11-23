"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Leaf, Menu, X, Search, Wrench, User } from "lucide-react";
import { cn } from "@/lib/utils";
import { preloadCurriculumMetadata } from "@/lib/api";

export function Navbar({ onMenuClick }: { onMenuClick?: () => void }) {
  const pathname = usePathname();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // The 4 core global navigation destinations
  const links = [
    { href: "/", label: "Home" },
    { href: "/courses", label: "Courses" },
    { href: "/mintai", label: "Predictions" },
    { href: "/calculator", label: "Tools" },
  ];

  const handleOpenSearch = () => {
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("open-command-palette"));
      document.dispatchEvent(new KeyboardEvent("keydown", { key: "k", metaKey: true, bubbles: true }));
      document.dispatchEvent(new KeyboardEvent("keydown", { key: "k", ctrlKey: true, bubbles: true }));
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full bg-background/85 backdrop-blur-md border-b border-border transition-colors duration-200">
      <div className="max-w-7xl mx-auto flex h-16 items-center justify-between px-4 sm:px-6 md:px-10">
        
        {/* Left: Brand Logo */}
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-all duration-300">
              <Leaf className="h-4 w-4" />
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-lg font-bold tracking-tight text-foreground">
                MarkMint
              </span>
              <span className="text-[11px] font-medium text-muted-foreground hidden sm:inline">
                SRMIST
              </span>
            </div>
          </Link>

          {/* Desktop Core Navigation Links */}
          <nav className="hidden md:flex items-center gap-1 pl-4 border-l border-border/60">
            {links.map((link) => {
              const isActive =
                link.href === "/"
                  ? pathname === "/"
                  : pathname?.startsWith(link.href) ||
                    (link.href === "/mintai" && (pathname?.startsWith("/dashboard") || pathname?.startsWith("/mintai")));

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
                    "px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all duration-150",
                    isActive
                      ? "bg-secondary text-foreground font-bold shadow-2xs"
                      : "text-muted-foreground hover:text-foreground hover:bg-secondary/60"
                  )}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Right Side: Quick Search & Profile / Mobile Toggle */}
        <div className="flex items-center gap-2.5">
          {/* Quick Search Button */}
          <button
            type="button"
            onClick={handleOpenSearch}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-secondary/80 hover:bg-secondary border border-border/80 text-xs text-muted-foreground hover:text-foreground transition-all cursor-pointer"
            title="Search courses and questions (⌘K)"
          >
            <Search className="w-3.5 h-3.5" />
            <span className="hidden sm:inline text-xs font-medium">Search courses...</span>
            <kbd className="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded bg-background border border-border text-[10px] font-mono font-medium text-muted-foreground">
              ⌘K
            </kbd>
          </button>

          {/* Minimal Student Profile / Guest Indicator */}
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-secondary/50 border border-border/60 text-xs font-medium text-foreground">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[11px] font-semibold text-muted-foreground">B.Tech 2021/2026</span>
          </div>

          {/* Mobile Menu Toggle */}
          <button
            type="button"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="p-2 md:hidden rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
            aria-label="Toggle navigation menu"
          >
            {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

      </div>

      {/* Mobile Menu Dropdown */}
      {isMobileMenuOpen && (
        <div className="md:hidden border-b border-border bg-background p-4 space-y-2 animate-in fade-in-50 duration-150">
          <button
            type="button"
            onClick={() => {
              setIsMobileMenuOpen(false);
              handleOpenSearch();
            }}
            className="w-full flex items-center justify-between p-3 rounded-xl bg-secondary border border-border text-xs font-medium text-muted-foreground"
          >
            <div className="flex items-center gap-2">
              <Search className="w-4 h-4 text-primary" />
              <span>Search courses, codes &amp; PYQs</span>
            </div>
            <kbd className="px-1.5 py-0.5 rounded bg-background border border-border text-[10px] font-mono">⌘K</kbd>
          </button>

          <div className="grid grid-cols-2 gap-1.5 pt-1">
            {links.map((link) => {
              const isActive =
                link.href === "/"
                  ? pathname === "/"
                  : pathname?.startsWith(link.href) ||
                    (link.href === "/mintai" && (pathname?.startsWith("/dashboard") || pathname?.startsWith("/mintai")));

              return (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={cn(
                    "p-3 rounded-xl text-xs font-semibold text-center transition-colors border",
                    isActive
                      ? "bg-primary/10 border-primary/30 text-primary font-bold"
                      : "bg-secondary/60 border-border/60 text-muted-foreground hover:text-foreground hover:bg-secondary"
                  )}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>

          <div className="pt-2 border-t border-border/50 flex items-center justify-between text-[11px] text-muted-foreground px-1">
            <span>SRM Institute of Science &amp; Technology</span>
            <span className="font-mono text-emerald-600 dark:text-emerald-400 font-semibold">Active Session</span>
          </div>
        </div>
      )}
    </header>
  );
}
