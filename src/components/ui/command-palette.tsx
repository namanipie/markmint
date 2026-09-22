"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { Search, Calculator, Activity, Code, BookOpen, FileText, Loader2, Leaf } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { searchIntelligence } from "@/lib/api";
import { SearchResult } from "@/lib/types";

interface CommandItem {
  id: string;
  title: string;
  snippet?: string;
  icon: any;
  href: string;
  category: string;
}

const DEFAULT_COMMANDS: CommandItem[] = [
  { id: "mintai", title: "MintAI Intelligence Engine", icon: Leaf, href: "/mintai", category: "App" },
  { id: "calc", title: "Mint+ GPA Calculator", icon: Calculator, href: "/calculator", category: "App" },
  { id: "study", title: "Study Intelligence & Personalization", icon: BookOpen, href: "/study-plan", category: "App" },
  { id: "dev", title: "The Duo (Developers)", icon: Code, href: "/developers", category: "App" },
];

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const [searchResults, setSearchResults] = useState<CommandItem[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  useEffect(() => {
    if (!query.trim()) {
      setSearchResults(DEFAULT_COMMANDS);
      setIsSearching(false);
      return;
    }

    let active = true;
    setIsSearching(true);
    const timer = setTimeout(() => {
      searchIntelligence({ raw_query: query.trim(), limit: 8 })
        .then((results: SearchResult[]) => {
          if (!active) return;
          if (results && results.length > 0) {
            const mapped: CommandItem[] = results.map((r) => {
              let icon = BookOpen;
              let href = "/mintai";
              let cat = "Result";
              if (r.result_type === "course") {
                icon = BookOpen;
                href = `/mintai?course_id=${r.id}`;
                cat = "Course";
              } else if (r.result_type === "topic") {
                icon = Leaf;
                href = `/mintai?topic=${encodeURIComponent(r.title)}`;
                cat = "Topic";
              } else if (r.result_type === "exam_question") {
                icon = FileText;
                href = `/mintai`;
                cat = "Exam Question";
              } else if (r.result_type === "study_material") {
                icon = BookOpen;
                href = `/study-plan`;
                cat = "Study Material";
              } else if (r.result_type === "question_family") {
                icon = Activity;
                href = `/mintai`;
                cat = "Question Family";
              }
              return {
                id: `${r.result_type}-${r.id}`,
                title: r.title,
                snippet: r.text_snippet,
                icon,
                href,
                category: cat,
              };
            });
            setSearchResults(mapped);
          } else {
            // Fallback to filtering default commands
            const localFiltered = DEFAULT_COMMANDS.filter((cmd) =>
              cmd.title.toLowerCase().includes(query.toLowerCase())
            );
            setSearchResults(localFiltered);
          }
        })
        .catch(() => {
          if (!active) return;
          const localFiltered = DEFAULT_COMMANDS.filter((cmd) =>
            cmd.title.toLowerCase().includes(query.toLowerCase())
          );
          setSearchResults(localFiltered);
        })
        .finally(() => {
          if (active) setIsSearching(false);
        });
    }, 200);

    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [query]);

  const itemsToDisplay = searchResults;

  useEffect(() => {
    setActiveIndex(0);
  }, [query]);

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [open]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((prev) => (prev + 1) % itemsToDisplay.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((prev) => (prev - 1 + itemsToDisplay.length) % itemsToDisplay.length);
    } else if (e.key === "Enter" && itemsToDisplay.length > 0) {
      e.preventDefault();
      router.push(itemsToDisplay[activeIndex].href);
      setOpen(false);
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 bg-background/80 backdrop-blur-sm z-[100]"
            onClick={() => setOpen(false)}
          />
          <div className="fixed inset-0 z-[101] flex items-start justify-center pt-[15vh] pointer-events-none">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -10 }}
              transition={{ duration: 0.15 }}
              className="w-full max-w-xl bg-card border border-border rounded-xl shadow-2xl overflow-hidden pointer-events-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center px-4 border-b border-border">
                {isSearching ? (
                  <Loader2 className="w-5 h-5 text-accent animate-spin mr-3" />
                ) : (
                  <Search className="w-5 h-5 text-muted-foreground mr-3" />
                )}
                <input
                  ref={inputRef}
                  type="text"
                  placeholder="Search courses, topics, questions, study notes..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  className="w-full bg-transparent border-none py-4 text-sm focus:outline-none text-foreground placeholder:text-muted-foreground"
                />
                <div className="text-[10px] text-muted-foreground font-mono bg-accent/10 px-2 py-1 rounded">ESC</div>
              </div>

              <div className="max-h-[60vh] overflow-y-auto py-2">
                {itemsToDisplay.length === 0 ? (
                  <div className="px-6 py-12 text-center text-sm text-muted-foreground">
                    No results found for &ldquo;{query}&rdquo;
                  </div>
                ) : (
                  itemsToDisplay.map((cmd, idx) => {
                    const active = idx === activeIndex;
                    const Icon = cmd.icon;
                    return (
                      <div
                        key={cmd.id}
                        onMouseEnter={() => setActiveIndex(idx)}
                        onClick={() => {
                          router.push(cmd.href);
                          setOpen(false);
                        }}
                        className={`flex items-start gap-3 px-4 py-3 mx-2 rounded-lg cursor-pointer transition-colors ${
                          active ? "bg-accent/10 text-accent" : "text-muted-foreground hover:bg-muted/50"
                        }`}
                      >
                        <Icon className="w-4 h-4 mt-0.5 shrink-0" />
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-foreground truncate">
                            {cmd.title}
                          </div>
                          {cmd.snippet && (
                            <div className="text-xs text-muted-foreground/80 line-clamp-1 pt-0.5">
                              {cmd.snippet}
                            </div>
                          )}
                        </div>
                        <span className="ml-2 text-[10px] font-mono uppercase bg-muted/80 px-2 py-0.5 rounded shrink-0">
                          {cmd.category}
                        </span>
                      </div>
                    );
                  })
                )}
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
