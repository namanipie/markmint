"use client";

import React, { useMemo } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";

interface MathTextProps {
  content: string;
  className?: string;
  inlineOnly?: boolean;
}

/**
 * Sanitizes LaTeX input before passing to KaTeX to prevent rendering errors:
 * - Automatically balances unmatched \left and \right delimiters
 * - Strips trailing unescaped backslashes
 * - Strips redundant internal dollar signs
 */
function sanitizeKatexInput(raw: string): string {
  if (!raw) return "";
  let s = raw.trim();

  // Strip outer single/double dollar signs if wrapped
  if (s.startsWith("$$") && s.endsWith("$$")) {
    s = s.slice(2, -2).trim();
  } else if (s.startsWith("$") && s.endsWith("$") && s.length > 1) {
    s = s.slice(1, -1).trim();
  } else if (s.startsWith("\\[") && s.endsWith("\\]")) {
    s = s.slice(2, -2).trim();
  } else if (s.startsWith("\\(") && s.endsWith("\\)")) {
    s = s.slice(2, -2).trim();
  }

  // Remove stray internal dollar signs
  s = s.replace(/(?<!\\)\$/g, "");

  // Strip trailing unescaped backslashes (e.g. "x\")
  s = s.replace(/\\+$/, "");

  // Auto-balance \left and \right
  if (s.includes("\\left") || s.includes("\\right")) {
    const leftMatches = s.match(/\\left[\(\[\{\.]/g) || [];
    const rightMatches = s.match(/\\right[\)\]\}\.]/g) || [];
    if (leftMatches.length > rightMatches.length) {
      s = s.replace(/\\left\(/g, "(")
           .replace(/\\left\[/g, "[")
           .replace(/\\left\\\{/g, "\\{");
    } else if (rightMatches.length > leftMatches.length) {
      s = s.replace(/\\right\)/g, ")")
           .replace(/\\right\]/g, "]")
           .replace(/\\right\\\}/g, "\\}");
    }
  }

  return s;
}

/**
 * Checks if a string is likely an isolated mathematical formula/option
 */
function isPureFormula(str: string): boolean {
  const s = str.trim();
  if (!s) return false;
  
  // Explicit math markers
  if ((s.startsWith("$") && s.endsWith("$")) || (s.startsWith("\\[") && s.endsWith("\\]")) || (s.startsWith("\\(") && s.endsWith("\\)"))) {
    return true;
  }
  
  // Contains common math indicators
  const hasMathChars = s.includes("\\") || s.includes("^") || s.includes("_") || s.includes("=") || s.includes("\\pm") || s.includes("\\sqrt");
  if (!hasMathChars) return false;

  // Should not contain common English prose words (4+ letters without math meaning)
  const englishWords = s.match(/\b[a-zA-Z]{4,}\b/g) || [];
  const mathKeywords = new Set([
    "frac", "sqrt", "times", "cdot", "approx", "alpha", "beta", "gamma", "delta",
    "theta", "lambda", "omega", "sigma", "infty", "partial", "nabla", "sinh", "cosh",
    "tanh", "left", "right", "begin", "pmatrix", "matrix", "cases"
  ]);
  const nonMathWords = englishWords.filter(w => !mathKeywords.has(w.toLowerCase()));
  
  return nonMathWords.length <= 1;
}

export function MathText({ content, className = "", inlineOnly = false }: MathTextProps) {
  const parts = useMemo(() => {
    if (!content) return [];

    const trimmed = content.trim();

    // 1. Fast Path: If entire string is a formula or option, attempt to render directly
    if (isPureFormula(trimmed)) {
      try {
        const sanitized = sanitizeKatexInput(trimmed);
        const html = katex.renderToString(sanitized, {
          displayMode: false,
          throwOnError: true,
        });
        return [{ type: "inline-math" as const, value: sanitized, html }];
      } catch {
        // Fall back to tokenization
      }
    }

    // 2. Tokenized Path: Parse mixed text & math equations
    // Matches:
    // - Block math: $$...$$ or \[...\]
    // - LaTeX environments: \begin{...}...\end{...}
    // - Inline math: \(...\) or $...$
    // - LaTeX commands: \frac, \sqrt, \pm, \int, \cos, \sin, \tan, etc.
    // - Algebraic equations: (D^2 - 4)y = 0, y = Ae^{2x} + Be^{-2x}, etc.
    const regex = /(\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]|\\begin\{(?:matrix|pmatrix|bmatrix|vmatrix|Vmatrix|cases|aligned|align)\}[\s\S]*?\\end\{(?:matrix|pmatrix|bmatrix|vmatrix|Vmatrix|cases|aligned|align)\}|\\\([\s\S]*?\\\)|(?<!\\)\$((?:\\\\|\\\$|[^\$])+?)(?<!\\)\$|\\(?:frac|sqrt)(?:\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})+(?:[\^_]\{?[a-zA-Z0-9+-]+\}?)?|\\(?:int|iint|iiint|oint|sum|prod|lim|infty|partial|nabla|sin|cos|tan|cot|sec|csc|sinh|cosh|tanh|ln|log|exp|det|vec|hat|bar|dot|ddot|tilde|alpha|beta|gamma|delta|epsilon|varepsilon|zeta|eta|theta|vartheta|iota|kappa|lambda|mu|nu|xi|pi|varpi|rho|varrho|sigma|varsigma|tau|upsilon|phi|varphi|chi|psi|omega|Gamma|Delta|Theta|Lambda|Xi|Pi|Sigma|Upsilon|Phi|Psi|Omega|times|cdot|pm|mp|approx|neq|leq|geq|le|ge|equiv|sim|propto|in|notin|subset|supset|subseteq|supseteq|cap|cup|oplus|otimes|angle|perp|circ|mathbf|mathbb|mathcal|mathrm)(?:\{[^{}]*\}|\[[^\[\]]*\]|\^[a-zA-Z0-9+\-_]|\^\{[^{}]*\}|_[a-zA-Z0-9+\-_]|_\{[^{}]*\}|[a-zA-Z0-9\(\)\,\^\+\-\*\/]+)*|(?:\(?[a-zA-Z0-9\^_\+\-\*\/\{\}]+\)?\s*[\=\+\-]\s*)+[a-zA-Z0-9\^_\+\-\*\/\{\}\(\)]+|\(?[a-zA-Z0-9]+\^[a-zA-Z0-9\{\}\+\-]+\)?(?:[a-zA-Z0-9\(\)\+\-\*\/\s\=]+)?)/g;

    const tokens: { type: "text" | "inline-math" | "block-math"; value: string; html?: string }[] = [];
    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while ((match = regex.exec(content)) !== null) {
      if (match.index > lastIndex) {
        tokens.push({
          type: "text",
          value: content.slice(lastIndex, match.index),
        });
      }

      const raw = match[0];
      let val = raw;
      let isDisplay = false;
      let isMath = true;

      if (raw.startsWith("$$") && raw.endsWith("$$")) {
        isDisplay = !inlineOnly;
        val = raw.slice(2, -2).trim();
      } else if (raw.startsWith("\\[") && raw.endsWith("\\]")) {
        isDisplay = !inlineOnly;
        val = raw.slice(2, -2).trim();
      } else if (raw.startsWith("\\begin{") && raw.includes("\\end{")) {
        isDisplay = !inlineOnly;
        val = raw.trim();
      } else if (raw.startsWith("\\(") && raw.endsWith("\\)")) {
        val = raw.slice(2, -2).trim();
      } else if (raw.startsWith("$") && raw.endsWith("$")) {
        val = raw.slice(1, -1).trim();
      } else {
        // Standalone candidate: verify it has math properties
        if (!val.includes("\\") && !val.includes("^") && !val.includes("_") && !(val.includes("=") && /[0-9]/.test(val))) {
          isMath = false;
        }
      }

      if (isMath) {
        try {
          const sanitized = sanitizeKatexInput(val);
          const html = katex.renderToString(sanitized, {
            displayMode: isDisplay,
            throwOnError: true,
          });
          tokens.push({
            type: isDisplay ? "block-math" : "inline-math",
            value: sanitized,
            html,
          });
        } catch {
          // If KaTeX fails, output raw string
          tokens.push({
            type: "text",
            value: raw,
          });
        }
      } else {
        tokens.push({
          type: "text",
          value: raw,
        });
      }

      lastIndex = regex.lastIndex;
    }

    if (lastIndex < content.length) {
      tokens.push({
        type: "text",
        value: content.slice(lastIndex),
      });
    }

    return tokens;
  }, [content, inlineOnly]);

  return (
    <span className={`math-text-container ${className}`}>
      {parts.map((part, index) => {
        if (part.type === "text" || !part.html) {
          return <React.Fragment key={index}>{part.value}</React.Fragment>;
        }

        if (part.type === "block-math") {
          return (
            <span
              key={index}
              className="my-2 block overflow-x-auto text-center font-serif text-accent"
              dangerouslySetInnerHTML={{ __html: part.html }}
            />
          );
        }

        return (
          <span
            key={index}
            className="inline-block px-0.5 font-serif"
            dangerouslySetInnerHTML={{ __html: part.html }}
          />
        );
      })}
    </span>
  );
}
