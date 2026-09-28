"use client";

import React, { useMemo } from "react";
import katex from "katex";

interface MathTextProps {
  content: string;
  className?: string;
  inlineOnly?: boolean;
}

export function MathText({ content, className = "", inlineOnly = false }: MathTextProps) {
  const parts = useMemo(() => {
    if (!content) return [];

    // Robust regex matching:
    // 1. Block math: $$...$$ or \[...\]
    // 2. Explicit LaTeX environments: \begin{...}...\end{...}
    // 3. Inline math: \(...\) or $...$
    // 4. Standalone LaTeX math commands: \frac{...}{...}, \sqrt{...}
    const regex = /(\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]|\\begin\{(?:matrix|pmatrix|bmatrix|vmatrix|Vmatrix|cases|aligned|align)\}[\s\S]*?\\end\{(?:matrix|pmatrix|bmatrix|vmatrix|Vmatrix|cases|aligned|align)\}|\\\([\s\S]*?\\\)|(?<!\\)\$((?:\\\\|\\\$|[^\$])+?)(?<!\\)\$|\\(?:frac|sqrt)(?:\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})+(?:[\^_]\{?[a-zA-Z0-9+-]+\}?)?)/g;

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
          const html = katex.renderToString(part.value, {
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
