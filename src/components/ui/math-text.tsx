"use client";

import React, { useMemo } from "react";
import katex from "katex";

interface MathTextProps {
  content: string;
  className?: string;
  inlineOnly?: boolean;
}

/**
 * Sanitizes LaTeX input before passing to KaTeX to prevent rendering errors:
 * - Automatically balances unmatched \left and \right delimiters
 * - Strips trailing unescaped backslashes
 */
function sanitizeKatexInput(raw: string): string {
  if (!raw) return "";
  let s = raw.trim();

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

export function MathText({ content, className = "", inlineOnly = false }: MathTextProps) {
  const parts = useMemo(() => {
    if (!content) return [];

    // Robust regex matching:
    // 1. Block math: $$...$$ or \[...\]
    // 2. Explicit LaTeX environments: \begin{...}...\end{...}
    // 3. Inline math: \(...\) or $...$
    // 4. Standalone LaTeX math commands: \frac, \sqrt, trig, integrals, Greek letters, etc.
    const regex = /(\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]|\\begin\{(?:matrix|pmatrix|bmatrix|vmatrix|Vmatrix|cases|aligned|align)\}[\s\S]*?\\end\{(?:matrix|pmatrix|bmatrix|vmatrix|Vmatrix|cases|aligned|align)\}|\\\([\s\S]*?\\\)|(?<!\\)\$((?:\\\\|\\\$|[^\$])+?)(?<!\\)\$|\\(?:frac|sqrt)(?:\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})+(?:[\^_]\{?[a-zA-Z0-9+-]+\}?)?|\\(?:int|iint|iiint|oint|sum|prod|lim|infty|partial|nabla|sin|cos|tan|cot|sec|csc|sinh|cosh|tanh|ln|log|exp|det|vec|hat|bar|dot|ddot|tilde|alpha|beta|gamma|delta|epsilon|varepsilon|zeta|eta|theta|vartheta|iota|kappa|lambda|mu|nu|xi|pi|varpi|rho|varrho|sigma|varsigma|tau|upsilon|phi|varphi|chi|psi|omega|Gamma|Delta|Theta|Lambda|Xi|Pi|Sigma|Upsilon|Phi|Psi|Omega|times|cdot|pm|mp|approx|neq|leq|geq|le|ge|equiv|sim|propto|in|notin|subset|supset|subseteq|supseteq|cap|cup|oplus|otimes|angle|perp|circ|mathbf|mathbb|mathcal|mathrm)(?:\{[^{}]*\}|\[[^\[\]]*\]|\^[a-zA-Z0-9+\-_]|\^\{[^{}]*\}|_[a-zA-Z0-9+\-_]|_\{[^{}]*\}|[a-zA-Z0-9\(\)\,\^\+\-\*\/]+)*)/g;

    const tokens: { type: "text" | "inline-math" | "block-math"; value: string }[] = [];
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
      if (raw.startsWith("$$") && raw.endsWith("$$")) {
        tokens.push({
          type: inlineOnly ? "inline-math" : "block-math",
          value: raw.slice(2, -2).trim(),
        });
      } else if (raw.startsWith("\\[") && raw.endsWith("\\]")) {
        tokens.push({
          type: inlineOnly ? "inline-math" : "block-math",
          value: raw.slice(2, -2).trim(),
        });
      } else if (raw.startsWith("\\begin{") && raw.includes("\\end{")) {
        tokens.push({
          type: inlineOnly ? "inline-math" : "block-math",
          value: raw.trim(),
        });
      } else if (raw.startsWith("\\(") && raw.endsWith("\\)")) {
        tokens.push({
          type: "inline-math",
          value: raw.slice(2, -2).trim(),
        });
      } else if (raw.startsWith("$") && raw.endsWith("$")) {
        tokens.push({
          type: "inline-math",
          value: raw.slice(1, -1).trim(),
        });
      } else {
        tokens.push({
          type: "inline-math",
          value: raw.trim(),
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
        if (part.type === "text") {
          return <React.Fragment key={index}>{part.value}</React.Fragment>;
        }

        try {
          const isDisplay = part.type === "block-math";
          const sanitized = sanitizeKatexInput(part.value);
          const html = katex.renderToString(sanitized, {
            displayMode: isDisplay,
            throwOnError: false,
          });

          if (isDisplay) {
            return (
              <span
                key={index}
                className="my-2 block overflow-x-auto text-center font-serif text-accent"
                dangerouslySetInnerHTML={{ __html: html }}
              />
            );
          }

          return (
            <span
              key={index}
              className="inline-block px-0.5 font-serif"
              dangerouslySetInnerHTML={{ __html: html }}
            />
          );
        } catch {
          return <span key={index}>{part.value}</span>;
        }
      })}
    </span>
  );
}
