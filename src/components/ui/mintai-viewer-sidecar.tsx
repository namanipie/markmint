"use client";

import React, { useState } from "react";
import {
  Sparkles,
  Zap,
  HelpCircle,
  BookOpen,
  Send,
  CheckCircle2,
  ExternalLink,
  Layers,
  ArrowRight,
  RotateCcw
} from "lucide-react";
import { MathText } from "@/components/ui/math-text";
import { ResourceViewerItem } from "./resource-viewer-modal";

interface MintAiViewerSidecarProps {
  item: ResourceViewerItem;
  onClose?: () => void;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export function MintAiViewerSidecar({ item }: MintAiViewerSidecarProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: `I'm your **MintAI Copilot** for this resource. Ask me to break down concepts, summarize formulas, or show how this material is tested in SRM examinations.`,
      timestamp: "Just now"
    }
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  // Derive title, unit, and course context
  const resourceTitle = item.data.title;
  const courseName = item.courseName || "SRM Course";
  const unitNumber = "unit" in item.data ? item.data.unit : undefined;

  const handleQuickPrompt = (promptType: "summary" | "formulas" | "pyqs" | "flashcards") => {
    let userPrompt = "";
    let aiResponse = "";

    if (promptType === "summary") {
      userPrompt = `Summarize the key core concepts of "${resourceTitle}".`;
      aiResponse = `### 📌 Core Concept Summary: ${resourceTitle}
- **Primary Objective**: Understand key theoretical derivations, governing equations, and boundary conditions.
- **Syllabus Unit**: ${unitNumber ? `Unit ${unitNumber}` : "General Core Module"} of **${courseName}**.
- **Exam Weightage**: Typically evaluated in Part B (8 or 10-mark multi-step analytical questions) with occasional definitions in Part A.
- **Key Takeaway**: Master the standard 3-step solution pattern: (1) state governing assumptions, (2) substitute values with standard SI units, (3) box your final answer.`;
    } else if (promptType === "formulas") {
      userPrompt = `Extract key formulas and definitions from "${resourceTitle}".`;
      aiResponse = `### 📐 Formulas & Governing Equations:
1. **Fundamental Relation**:
   $$\\mathbf{A} \\mathbf{x} = \\lambda \\mathbf{x}$$
2. **Characteristic Polynomial**:
   $$\\det(\\mathbf{A} - \\lambda \\mathbf{I}) = 0$$
3. **Cayley-Hamilton Theorem Formulation**:
   Every square matrix satisfies its own characteristic equation:
   $$P(\\mathbf{A}) = \\mathbf{0} \\implies \\mathbf{A}^{-1} = -\\frac{1}{a_0} \\sum_{k=1}^n a_k \\mathbf{A}^{k-1}$$
> **Exam Tip**: In SRM papers, partial marks are awarded for correctly stating the determinant equation even if numerical algebra has a minor arithmetic slip.`;
    } else if (promptType === "pyqs") {
      userPrompt = `How is "${resourceTitle}" tested in SRM Cycle Tests and End Semester exams?`;
      aiResponse = `### 🎯 SRM Examination Forensics:
- **Frequent Cycles**: CT1 / CT2 and End Semester Part B.
- **Question Stems Seen in PYQs**:
  1. *"Verify the theorem for the given $3 \\times 3$ system and hence find the inverse."* (~8-10 Marks)
  2. *"State the primary definition and list 3 practical engineering applications."* (~4 Marks)
- **Common Pitfalls**:
  - Skipping the determinant sign inversion for negative eigenvalues.
  - Forgetting units in physical parameters.`;
    } else if (promptType === "flashcards") {
      userPrompt = `Generate 3 quick memory flashcards for "${resourceTitle}".`;
      aiResponse = `### 💡 Quick Memory Cards:
**Card 1**:
- *Prompt*: What is the condition for non-trivial solutions in $(\\mathbf{A} - \\lambda \\mathbf{I})\\mathbf{x} = \\mathbf{0}$?
- *Answer*: The matrix must be singular: $\\det(\\mathbf{A} - \\lambda \\mathbf{I}) = 0$.

**Card 2**:
- *Prompt*: How do you compute $\\mathbf{A}^4$ using Cayley-Hamilton?
- *Answer*: Divide $\\lambda^4$ by the characteristic polynomial $P(\\lambda)$ to express $\\mathbf{A}^4$ as a linear combination of $\\mathbf{A}$ and $\\mathbf{I}$.

**Card 3**:
- *Prompt*: What is the trace property with respect to eigenvalues?
- *Answer*: $\\operatorname{tr}(\\mathbf{A}) = \\sum_{i=1}^n \\lambda_i$.`;
    }

    setMessages((prev) => [
      ...prev,
      { role: "user", content: userPrompt, timestamp: "Just now" },
      { role: "assistant", content: aiResponse, timestamp: "Just now" }
    ]);
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isGenerating) return;

    const userText = inputValue.trim();
    setInputValue("");
    setMessages((prev) => [
      ...prev,
      { role: "user", content: userText, timestamp: "Just now" }
    ]);

    setIsGenerating(true);
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Regarding **"${userText}"** for *${resourceTitle}* (${courseName}):
          
This topic is centrally relevant to SRMIST ${unitNumber ? `Unit ${unitNumber}` : "curriculum"} requirements. For optimal marks in exams:
1. Always write down the standard theoretical definition first.
2. If computing numerical values, keep at least 4 decimal places for intermediate steps.
3. Check the **MintAI Practice Hub** for authentic previous year questions matching this exact query.`,
          timestamp: "Just now"
        }
      ]);
      setIsGenerating(false);
    }, 600);
  };

  return (
    <div className="flex flex-col h-full bg-card border-l border-border/80 text-foreground overflow-hidden">
      {/* Sidecar Top Bar */}
      <div className="p-3.5 border-b border-border/60 bg-muted/20 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="p-1.5 rounded-lg bg-accent/15 text-accent">
            <Sparkles className="w-4 h-4" />
          </span>
          <div>
            <h4 className="text-xs font-bold text-foreground">MintAI Copilot</h4>
            <p className="text-[10px] text-muted-foreground truncate max-w-[180px]">
              Assisting with {resourceTitle}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() =>
            setMessages([
              {
                role: "assistant",
                content: `Chat history reset. How can I assist you with this document?`,
                timestamp: "Just now"
              }
            ])
          }
          className="p-1 rounded-md text-muted-foreground hover:text-foreground text-xs"
          title="Clear Chat"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Quick Action Suggestion Chips */}
      <div className="p-2.5 border-b border-border/40 bg-background/50 flex items-center gap-1.5 overflow-x-auto scrollbar-none">
        <button
          type="button"
          onClick={() => handleQuickPrompt("summary")}
          className="px-2.5 py-1 rounded-lg bg-accent/10 hover:bg-accent/20 text-accent text-[11px] font-semibold shrink-0 transition-colors"
        >
          ⚡ Summarize
        </button>
        <button
          type="button"
          onClick={() => handleQuickPrompt("formulas")}
          className="px-2.5 py-1 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 text-[11px] font-semibold shrink-0 transition-colors"
        >
          📐 Formulas
        </button>
        <button
          type="button"
          onClick={() => handleQuickPrompt("pyqs")}
          className="px-2.5 py-1 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 text-[11px] font-semibold shrink-0 transition-colors"
        >
          🎯 Exam PYQs
        </button>
        <button
          type="button"
          onClick={() => handleQuickPrompt("flashcards")}
          className="px-2.5 py-1 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 text-[11px] font-semibold shrink-0 transition-colors"
        >
          💡 Flashcards
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${
              m.role === "user" ? "items-end" : "items-start"
            }`}
          >
            <div
              className={`p-3 rounded-2xl text-xs max-w-[92%] leading-relaxed ${
                m.role === "user"
                  ? "bg-accent text-accent-foreground font-medium rounded-br-xs"
                  : "bg-muted/40 border border-border/70 text-foreground rounded-bl-xs space-y-1"
              }`}
            >
              <MathText content={m.content} />
            </div>
            <span className="text-[9px] text-muted-foreground mt-0.5 px-1">
              {m.timestamp}
            </span>
          </div>
        ))}
        {isGenerating && (
          <div className="flex items-center gap-2 p-2.5 text-xs text-muted-foreground">
            <Sparkles className="w-3.5 h-3.5 animate-spin text-accent" />
            <span>Analyzing course notes and syllabus patterns...</span>
          </div>
        )}
      </div>

      {/* Footer Input Area */}
      <div className="p-2.5 border-t border-border/60 bg-muted/20">
        <form onSubmit={handleSendMessage} className="flex items-center gap-1.5">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask MintAI about this resource..."
            className="flex-1 px-3 py-2 rounded-xl bg-background border border-border text-xs text-foreground placeholder:text-muted-foreground focus:outline-hidden focus:ring-1 focus:ring-accent"
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isGenerating}
            className="p-2 rounded-xl bg-accent text-accent-foreground disabled:opacity-40 disabled:cursor-not-allowed hover:bg-accent/90 transition-colors"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>
      </div>
    </div>
  );
}
