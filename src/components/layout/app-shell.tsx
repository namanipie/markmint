"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  BrainCircuit,
  ListTodo,
  PencilRuler,
  LineChart,
  Menu,
  X,
  Leaf
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/", label: "Home", icon: LayoutDashboard },
  { href: "/mintai", label: "MintAI", icon: BrainCircuit },
  { href: "/study-plan", label: "Study Plan", icon: ListTodo },
  { href: "/practice", label: "Practice", icon: PencilRuler },
  { href: "/analytics", label: "What Repeated?", icon: LineChart },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

  const SidebarContent = () => (
    <div className="flex flex-col h-full bg-card border-r border-border">
      {/* Logo Area */}
      <div className="h-16 flex items-center px-6 border-b border-border/50">
        <Link href="/" className="flex items-center gap-2 group">
          <Leaf className="h-5 w-5 text-primary group-hover:rotate-12 transition-transform duration-300" />
          <span className="text-lg font-bold tracking-tight text-foreground">MarkMint</span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-6 px-3 flex flex-col gap-1.5 overflow-y-auto">
        <div className="px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
          Your Workspace
        </div>
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href));
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors group relative",
                isActive
                  ? "bg-primary/10 text-primary font-semibold"
                  : "text-muted-foreground hover:bg-secondary hover:text-foreground font-medium"
              )}
            >
              {isActive && (
                <motion.div
                  layoutId="sidebar-active-indicator"
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-primary rounded-r-full"
                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
              )}
              <Icon className={cn("h-4 w-4 shrink-0", isActive && "text-primary")} />
              <span className="text-sm">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer Area */}
      <div className="p-4 border-t border-border/50">
        <div className="text-[10px] text-muted-foreground text-center">
          Built for SRMIST students
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex w-full bg-background">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex flex-col w-64 fixed inset-y-0 z-40">
        <SidebarContent />
      </aside>

      {/* Mobile Topbar */}
      <div className="lg:hidden fixed top-0 inset-x-0 h-16 bg-card/90 backdrop-blur-md border-b border-border z-40 flex items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2">
          <Leaf className="h-5 w-5 text-primary" />
          <span className="text-lg font-bold tracking-tight">MarkMint</span>
        </Link>
        <button
          onClick={() => setMobileMenuOpen(true)}
          className="p-2 text-muted-foreground hover:text-foreground rounded-md transition-colors"
        >
          <Menu className="h-5 w-5" />
        </button>
      </div>

      {/* Mobile Menu Overlay */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileMenuOpen(false)}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 lg:hidden"
            />
            <motion.div
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="fixed inset-y-0 left-0 w-3/4 max-w-sm bg-card z-50 lg:hidden shadow-2xl"
            >
              <div className="absolute right-4 top-4">
                <button
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-2 text-muted-foreground hover:text-foreground bg-secondary rounded-full"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
              <SidebarContent />
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <main className="flex-1 lg:pl-64 flex flex-col min-h-screen">
        <div className="flex-1 p-4 lg:p-8 mt-16 lg:mt-0 max-w-6xl w-full mx-auto page-load-animate">
          {children}
        </div>
      </main>
    </div>
  );
}
