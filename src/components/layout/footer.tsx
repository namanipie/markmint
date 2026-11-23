"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { Leaf } from "lucide-react";

export function Footer() {
  const pathname = usePathname();

  const links = [
    { href: "/", label: "Home" },
    { href: "/courses", label: "Courses" },
    { href: "/mintai", label: "Predictions" },
    { href: "/calculator", label: "Tools" },
    { href: "/tools/pdf", label: "MintDocs" },
    { href: "/privacy", label: "Privacy" },
    { href: "/terms", label: "Terms" },
  ];

  return (
    <footer className="border-t border-border/80 bg-background/60 py-8 mt-auto text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-10 flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
        
        {/* Left: Brand & SRMIST Attribution */}
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <Leaf className="h-4 w-4 text-primary" />
            <span className="font-bold tracking-tight text-foreground">
              MarkMint
            </span>
            <span className="text-[11px] text-muted-foreground">• Academic Intelligence</span>
          </div>
          <p className="text-[11px] text-muted-foreground">
            Course-first academic workspace and verified examination intelligence for SRMIST students.
          </p>
        </div>

        {/* Right: Quick Links */}
        <nav className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-muted-foreground">
          {links.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`hover:text-foreground transition-colors ${
                  isActive ? "text-foreground font-semibold" : ""
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

      </div>
    </footer>
  );
}
