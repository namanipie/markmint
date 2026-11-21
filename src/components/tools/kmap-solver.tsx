"use client";

import React, { useState, useMemo } from "react";
import { 
  Binary, 
  RotateCcw, 
  Copy, 
  Check, 
  Sparkles, 
  Info, 
  Layers, 
  ArrowRight,
  Sliders,
  CheckCircle2
} from "lucide-react";
import { toast } from "sonner";

export type CellValue = "0" | "1" | "X";

// Gray code mappings for K-Maps
const GRAY_2 = ["0", "1"];
const GRAY_4 = ["00", "01", "11", "10"];

// 4-Variable grid layout (Row: AB, Col: CD)
const GRID_4VAR = [
  [0, 1, 3, 2],       // AB = 00
  [4, 5, 7, 6],       // AB = 01
  [12, 13, 15, 14],   // AB = 11
  [8, 9, 11, 10],     // AB = 10
];

// 3-Variable grid layout (Row: A, Col: BC)
const GRID_3VAR = [
  [0, 1, 3, 2],       // A = 0
  [4, 5, 7, 6],       // A = 1
];

// 2-Variable grid layout (Row: A, Col: B)
const GRID_2VAR = [
  [0, 1],             // A = 0
  [2, 3],             // A = 1
];

export function KMapSolver() {
  const [numVars, setNumVars] = useState<2 | 3 | 4>(4);
  const [copied, setCopied] = useState(false);

  // Cell values indexed by minterm number (0 to 15)
  const [cells, setCells] = useState<Record<number, CellValue>>({
    0: "1", 1: "1", 2: "0", 3: "0",
    4: "1", 5: "1", 6: "0", 7: "0",
    8: "0", 9: "0", 10: "0", 11: "0",
    12: "0", 13: "0", 14: "0", 15: "0",
  });

  const maxMinterms = 1 << numVars; // 4, 8, or 16

  // Cycle cell state: "0" -> "1" -> "X" -> "0"
  const toggleCell = (m: number) => {
    setCells((prev) => {
      const current = prev[m] || "0";
      const next: CellValue = current === "0" ? "1" : current === "1" ? "X" : "0";
      return { ...prev, [m]: next };
    });
  };

  const setAll = (val: CellValue) => {
    const updated: Record<number, CellValue> = {};
    for (let i = 0; i < maxMinterms; i++) {
      updated[i] = val;
    }
    setCells(updated);
  };

  const resetPreset = (type: "adder" | "checker" | "random") => {
    const updated: Record<number, CellValue> = {};
    for (let i = 0; i < maxMinterms; i++) updated[i] = "0";

    if (type === "adder") {
      // Sum output of full adder: m(1, 2, 4, 7)
      [1, 2, 4, 7].forEach((m) => {
        if (m < maxMinterms) updated[m] = "1";
      });
    } else if (type === "checker") {
      // Alternating checkerboard
      for (let i = 0; i < maxMinterms; i += 2) updated[i] = "1";
    } else {
      for (let i = 0; i < maxMinterms; i++) {
        const r = Math.random();
        updated[i] = r > 0.6 ? "1" : r > 0.45 ? "X" : "0";
      }
    }
    setCells(updated);
    toast("Preset applied to K-Map grid.");
  };

  // Minterms and Don't Cares
  const minterms = useMemo(() => {
    const list: number[] = [];
    for (let i = 0; i < maxMinterms; i++) {
      if (cells[i] === "1") list.push(i);
    }
    return list;
  }, [cells, maxMinterms]);

  const dontCares = useMemo(() => {
    const list: number[] = [];
    for (let i = 0; i < maxMinterms; i++) {
      if (cells[i] === "X") list.push(i);
    }
    return list;
  }, [cells, maxMinterms]);

  const maxterms = useMemo(() => {
    const list: number[] = [];
    for (let i = 0; i < maxMinterms; i++) {
      if (cells[i] === "0" || !cells[i]) list.push(i);
    }
    return list;
  }, [cells, maxMinterms]);

  // Quine-McCluskey / Boolean Logic Minimizer for SOP & POS
  const solution = useMemo(() => {
    const vars = numVars === 4 ? ["A", "B", "C", "D"] : numVars === 3 ? ["A", "B", "C"] : ["A", "B"];

    if (minterms.length === 0) {
      return {
        sop: "0",
        pos: "0",
        mintermsCanonical: "None",
        maxtermsCanonical: `Π M(${Array.from({ length: maxMinterms }, (_, i) => i).join(", ")})`,
        isConstant: true,
      };
    }

    if (minterms.length + dontCares.length === maxMinterms) {
      return {
        sop: "1",
        pos: "1",
        mintermsCanonical: `Σ m(${minterms.join(", ")})`,
        maxtermsCanonical: "None",
        isConstant: true,
      };
    }

    // Binary representation helper
    const toBin = (n: number) => n.toString(2).padStart(numVars, "0");

    // All active terms (1s and Xs)
    const activeTerms = new Set([...minterms, ...dontCares]);

    // Grouping generation (sizes 16, 8, 4, 2, 1)
    const validGroupSizes = [16, 8, 4, 2, 1].filter((s) => s <= maxMinterms);
    const primeImplicants: { pattern: string; covered: number[] }[] = [];

    // Helper to generate binary patterns with '-'
    const checkGroup = (pattern: string): number[] => {
      // Find all numbers matching pattern
      const matches: number[] = [];
      const len = pattern.length;
      for (let i = 0; i < maxMinterms; i++) {
        const b = toBin(i);
        let match = true;
        for (let j = 0; j < len; j++) {
          if (pattern[j] !== "-" && pattern[j] !== b[j]) {
            match = false;
            break;
          }
        }
        if (match) matches.push(i);
      }
      return matches;
    };

    // Generate candidate patterns for the number of variables
    const generatePatterns = (length: number): string[] => {
      const results: string[] = [];
      const helper = (current: string) => {
        if (current.length === length) {
          results.push(current);
          return;
        }
        helper(current + "0");
        helper(current + "1");
        helper(current + "-");
      };
      helper("");
      return results;
    };

    const allPatterns = generatePatterns(numVars);
    // Sort patterns by number of '-' descending (larger groups first)
    allPatterns.sort((a, b) => (b.match(/-/g) || []).length - (a.match(/-/g) || []).length);

    const validPrimeImplicants: { pattern: string; covered: number[] }[] = [];

    for (const pat of allPatterns) {
      const covered = checkGroup(pat);
      // Group is valid if ALL its covered minterms are in activeTerms (1 or X)
      // and it covers AT LEAST ONE '1' (not purely Xs)
      const allActive = covered.every((m) => activeTerms.has(m));
      const hasRealMinterm = covered.some((m) => cells[m] === "1");

      if (allActive && hasRealMinterm) {
        // Check if this pattern is a sub-cube of an already added larger implicant
        const isRedundant = validPrimeImplicants.some((existing) =>
          covered.every((m) => existing.covered.includes(m))
        );
        if (!isRedundant) {
          validPrimeImplicants.push({ pattern: pat, covered });
        }
      }
    }

    // Essential Prime Implicant reduction (Greedy Set Cover for canonical minimal cover)
    const uncovered = new Set(minterms);
    const chosenImplicants: string[] = [];

    while (uncovered.size > 0 && validPrimeImplicants.length > 0) {
      // Pick implicant that covers the most remaining uncovered 1s
      validPrimeImplicants.sort((a, b) => {
        const aCount = a.covered.filter((m) => uncovered.has(m)).length;
        const bCount = b.covered.filter((m) => uncovered.has(m)).length;
        return bCount - aCount;
      });

      const best = validPrimeImplicants[0];
      const newlyCovered = best.covered.filter((m) => uncovered.has(m));
      if (newlyCovered.length === 0) break; // done

      chosenImplicants.push(best.pattern);
      newlyCovered.forEach((m) => uncovered.delete(m));
      validPrimeImplicants.shift();
    }

    // Convert binary pattern to SOP expression
    const patternToSopTerm = (pat: string) => {
      let term = "";
      for (let i = 0; i < pat.length; i++) {
        if (pat[i] === "1") term += vars[i];
        else if (pat[i] === "0") term += `${vars[i]}'`;
      }
      return term || "1";
    };

    // Convert pattern to POS expression
    const patternToPosTerm = (pat: string) => {
      const parts: string[] = [];
      for (let i = 0; i < pat.length; i++) {
        if (pat[i] === "1") parts.push(`${vars[i]}'`);
        else if (pat[i] === "0") parts.push(vars[i]);
      }
      return parts.length > 1 ? `(${parts.join(" + ")})` : parts[0] || "0";
    };

    const sopExpr = chosenImplicants.map(patternToSopTerm).join(" + ") || "0";

    const canonicalM = `Σ m(${minterms.join(", ") || "∅"})${
      dontCares.length > 0 ? ` + d(${dontCares.join(", ")})` : ""
    }`;
    const canonicalMax = `Π M(${maxterms.join(", ") || "∅"})${
      dontCares.length > 0 ? ` · D(${dontCares.join(", ")})` : ""
    }`;

    return {
      sop: sopExpr,
      pos: chosenImplicants.map(patternToPosTerm).join(" · ") || "0",
      mintermsCanonical: canonicalM,
      maxtermsCanonical: canonicalMax,
      isConstant: false,
    };
  }, [minterms, dontCares, maxterms, numVars, cells, maxMinterms]);

  const copySOP = () => {
    navigator.clipboard.writeText(`F(${numVars === 4 ? "A,B,C,D" : numVars === 3 ? "A,B,C" : "A,B"}) = ${solution.sop}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast("Minimized SOP expression copied.");
  };

  // Render Grid based on numVars
  const currentGrid = numVars === 4 ? GRID_4VAR : numVars === 3 ? GRID_3VAR : GRID_2VAR;
  const rowLabels = numVars === 4 ? GRAY_4 : numVars === 3 ? GRAY_2 : GRAY_2;
  const colLabels = numVars === 4 ? GRAY_4 : numVars === 3 ? GRAY_4 : GRAY_2;
  const rowVarName = numVars === 4 ? "AB" : "A";
  const colVarName = numVars === 4 ? "CD" : numVars === 3 ? "BC" : "B";

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      <div className="p-6 md:p-8 rounded-3xl bg-card border border-border shadow-xs space-y-6">
        
        {/* Header Controls */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-border/60">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="p-2 rounded-xl bg-accent/15 text-accent">
                <Binary className="w-5 h-5" />
              </span>
              <h2 className="text-xl md:text-2xl font-bold tracking-tight text-foreground">
                Interactive Karnaugh Map (K-Map) Solver
              </h2>
            </div>
            <p className="text-xs text-muted-foreground">
              Click cells to toggle between <strong>0</strong>, <strong>1</strong>, and <strong>X (Don&apos;t Care)</strong> for instant Boolean SOP / POS logic minimization.
            </p>
          </div>

          {/* Variable Count Selector */}
          <div className="flex items-center gap-1.5 p-1 bg-muted/20 border border-border/80 rounded-xl text-xs font-semibold self-start md:self-auto shrink-0">
            <span className="text-[11px] text-muted-foreground px-2">Variables:</span>
            {[2, 3, 4].map((v) => (
              <button
                key={v}
                type="button"
                onClick={() => setNumVars(v as any)}
                className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                  numVars === v
                    ? "bg-accent text-accent-foreground font-bold shadow-2xs"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {v} Vars
              </button>
            ))}
          </div>
        </div>

        {/* Presets and Quick Actions */}
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[11px] text-muted-foreground font-medium">Quick Presets:</span>
            <button
              type="button"
              onClick={() => resetPreset("adder")}
              className="px-2.5 py-1 rounded-lg bg-muted/30 border border-border hover:bg-muted/50 transition-colors font-medium cursor-pointer"
            >
              Full Adder Sum
            </button>
            <button
              type="button"
              onClick={() => resetPreset("checker")}
              className="px-2.5 py-1 rounded-lg bg-muted/30 border border-border hover:bg-muted/50 transition-colors font-medium cursor-pointer"
            >
              Checkerboard
            </button>
            <button
              type="button"
              onClick={() => resetPreset("random")}
              className="px-2.5 py-1 rounded-lg bg-muted/30 border border-border hover:bg-muted/50 transition-colors font-medium cursor-pointer"
            >
              Random
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setAll("0")}
              className="px-2.5 py-1 rounded-lg border border-border/80 text-muted-foreground hover:text-foreground hover:bg-muted/20 transition-colors cursor-pointer"
            >
              All 0s
            </button>
            <button
              type="button"
              onClick={() => setAll("1")}
              className="px-2.5 py-1 rounded-lg border border-border/80 text-muted-foreground hover:text-foreground hover:bg-muted/20 transition-colors cursor-pointer"
            >
              All 1s
            </button>
          </div>
        </div>

        {/* K-Map Interactive Grid */}
        <div className="flex flex-col items-center justify-center p-4 sm:p-8 rounded-2xl bg-muted/10 border border-border/60 overflow-x-auto">
          <div className="inline-block min-w-max">
            {/* Top Variable Header */}
            <div className="flex items-center mb-2">
              <div className="w-16 h-8 flex items-center justify-center text-xs font-mono font-bold text-accent">
                {rowVarName} \ {colVarName}
              </div>
              <div className="flex">
                {colLabels.map((cLab, idx) => (
                  <div
                    key={idx}
                    className="w-16 sm:w-20 text-center font-mono text-xs font-bold text-muted-foreground"
                  >
                    {cLab}
                  </div>
                ))}
              </div>
            </div>

            {/* Grid Rows */}
            {currentGrid.map((rowMinterms, rIdx) => (
              <div key={rIdx} className="flex items-center mb-2">
                {/* Row Header Label */}
                <div className="w-16 h-16 sm:h-20 flex items-center justify-center font-mono text-xs font-bold text-muted-foreground">
                  {rowLabels[rIdx]}
                </div>

                {/* Cell Buttons */}
                <div className="flex gap-2">
                  {rowMinterms.map((m) => {
                    const val = cells[m] || "0";
                    return (
                      <button
                        key={m}
                        type="button"
                        onClick={() => toggleCell(m)}
                        className={`w-16 h-16 sm:w-20 sm:h-20 rounded-2xl border-2 flex flex-col items-center justify-center transition-all cursor-pointer select-none relative group ${
                          val === "1"
                            ? "bg-accent/20 border-accent text-accent shadow-xs scale-102"
                            : val === "X"
                            ? "bg-amber-500/15 border-amber-500/50 text-amber-500"
                            : "bg-card border-border/80 hover:border-border text-muted-foreground/60 hover:text-foreground"
                        }`}
                      >
                        <span className="text-xl sm:text-2xl font-mono font-extrabold">{val}</span>
                        <span className="absolute bottom-1 right-2 text-[10px] font-mono text-muted-foreground/50 group-hover:text-muted-foreground">
                          m{m}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Minimal Solution Output Box */}
        <div className="p-5 sm:p-6 rounded-2xl bg-card border border-border/80 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-accent" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                Minimized Boolean Output
              </h3>
            </div>
            <button
              type="button"
              onClick={copySOP}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-muted/30 border border-border/80 text-foreground text-xs font-semibold hover:bg-muted/50 transition-all cursor-pointer"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-accent" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? "Copied" : "Copy Expression"}</span>
            </button>
          </div>

          <div className="p-4 rounded-xl bg-muted/15 border border-border/60 space-y-2">
            <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wide block">
              Simplified Sum-of-Products (SOP):
            </span>
            <div className="text-xl sm:text-2xl font-mono font-extrabold text-foreground tracking-wide break-all">
              F = <span className="text-accent">{solution.sop}</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
            <div className="p-3 rounded-xl bg-muted/10 border border-border/50 space-y-1">
              <span className="text-[10px] text-muted-foreground font-sans font-semibold uppercase">Canonical Minterms:</span>
              <div className="text-foreground truncate">{solution.mintermsCanonical}</div>
            </div>

            <div className="p-3 rounded-xl bg-muted/10 border border-border/50 space-y-1">
              <span className="text-[10px] text-muted-foreground font-sans font-semibold uppercase">Product of Sums (POS):</span>
              <div className="text-foreground truncate">F = {solution.pos}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
