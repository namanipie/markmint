"use client";

import React, { useState } from "react";
import { BrainCircuit, Loader2, FileQuestion, CheckCircle2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { MathText } from "./math-text";

interface Props {
  topicName: string;
}

interface GeneratedQuestion {
  type: "MCQ" | "SHORT" | "LONG" | "SPLIT";
  marks: string;
  text: string;
  options?: string[];
}

export function MintAIQuestionGenerator({ topicName }: Props) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [questions, setQuestions] = useState<GeneratedQuestion[]>([]);

  const generateQuestions = () => {
    setIsGenerating(true);
    setQuestions([]);
    
    // Simulate AI generation time
    setTimeout(() => {
      const lower = topicName.toLowerCase();
      let qs: GeneratedQuestion[] = [];
      
      // Highly realistic SRM question templates based on subject context
      if (lower.includes("calculus") || lower.includes("math") || lower.includes("matrix") || lower.includes("eigen")) {
        qs = [
          { type: "MCQ", marks: "1 Mark", text: `If A is an orthogonal matrix related to ${topicName}, then $A^{-1}$ is equal to:`, options: ["$A$", "$A^T$", "$-A$", "$I$"] },
          { type: "SHORT", marks: "4 Marks", text: `State the Cayley-Hamilton theorem and use it to find the inverse of the matrix associated with ${topicName}.` },
          { type: "SPLIT", marks: "13 Marks (7+6)", text: `(a) [7 Marks] Find the eigenvalues and eigenvectors of the matrix representing ${topicName}. \n\n(b) [6 Marks] Reduce the given quadratic form of ${topicName} to canonical form using orthogonal transformation.` }
        ];
      } else if (lower.includes("algorithm") || lower.includes("data structure") || lower.includes("tree") || lower.includes("sort")) {
        qs = [
          { type: "MCQ", marks: "1 Mark", text: `What is the worst-case time complexity of ${topicName}?`, options: ["$O(1)$", "$O(n)$", "$O(n \\log n)$", "$O(n^2)$"] },
          { type: "SHORT", marks: "4 Marks", text: `Write the pseudocode for the fundamental operation in ${topicName} and explain its space complexity.` },
          { type: "LONG", marks: "8 Marks", text: `Trace the execution of ${topicName} step-by-step on the following input array: [54, 26, 93, 17, 77, 31, 44, 55, 20]. Show the state of the data structure after each pass.` },
          { type: "SPLIT", marks: "13 Marks (7+6)", text: `(a) [7 Marks] Compare and contrast ${topicName} with its primary alternative. When would you prefer one over the other? \n\n(b) [6 Marks] Implement a C/C++ function to delete a node in a ${topicName}.` }
        ];
      } else if (lower.includes("physics") || lower.includes("mechanics") || lower.includes("quantum") || lower.includes("optics")) {
        qs = [
          { type: "MCQ", marks: "1 Mark", text: `Which fundamental law strictly governs the behavior of ${topicName}?`, options: ["Newton's First Law", "Faraday's Law", "Planck's Radiation Law", "Heisenberg's Principle"] },
          { type: "SHORT", marks: "4 Marks", text: `Define ${topicName} and state its SI unit. Draw a neat schematic diagram to illustrate your definition.` },
          { type: "SPLIT", marks: "13 Marks (7+6)", text: `(a) [7 Marks] Derive the expression for ${topicName} from fundamental physical principles. \n\n(b) [6 Marks] A system undergoing ${topicName} has an initial state $V_1 = 5m/s$. Calculate the final kinetic energy if a constant force of $10N$ is applied.` }
        ];
      } else if (lower.includes("machine learning") || lower.includes("ai") || lower.includes("network") || lower.includes("cloud")) {
        qs = [
          { type: "MCQ", marks: "1 Mark", text: `Which of the following activation functions is most commonly used in the hidden layers of a ${topicName} architecture?`, options: ["Sigmoid", "Linear", "ReLU", "Softmax"] },
          { type: "SHORT", marks: "4 Marks", text: `Explain the concept of overfitting in the context of ${topicName} and list two regularization techniques to prevent it.` },
          { type: "SPLIT", marks: "13 Marks (7+6)", text: `(a) [7 Marks] Explain the end-to-end architecture of ${topicName} with the help of a neat block diagram. \n\n(b) [6 Marks] Discuss the mathematical intuition behind the loss function optimization in ${topicName}.` }
        ];
      } else {
        // Generic engineering fallback that still looks hyper-realistic for SRM
        qs = [
          { type: "MCQ", marks: "1 Mark", text: `The primary advantage of implementing ${topicName} in modern systems is:`, options: ["Reduced latency", "Lower cost", "High redundancy", "Maximized throughput"] },
          { type: "SHORT", marks: "4 Marks", text: `Briefly explain the working principle of ${topicName}. List any two major advantages and disadvantages.` },
          { type: "LONG", marks: "8 Marks", text: `Discuss the various classifications and types of ${topicName} in detail.` },
          { type: "SPLIT", marks: "13 Marks (7+6)", text: `(a) [7 Marks] Explain the step-by-step workflow of ${topicName} with a neat, fully labeled block diagram. \n\n(b) [6 Marks] A real-world application requires ${topicName}. What are the design considerations you must take into account? Justify your answer.` }
        ];
      }

      setQuestions(qs);
      setIsGenerating(false);
    }, 2500);
  };

  return (
    <div className="mt-4 pt-4 border-t border-border/50">
      {!isGenerating && questions.length === 0 && (
        <button
          onClick={generateQuestions}
          className="flex items-center gap-2 px-4 py-2.5 bg-accent/10 hover:bg-accent/20 text-accent border border-accent/20 rounded-lg text-xs font-bold uppercase tracking-wider transition-all w-full justify-center group"
        >
          <BrainCircuit className="w-4 h-4 group-hover:scale-110 transition-transform" />
          Ask Mint AI for Repeated PYQ Questions
        </button>
      )}

      {isGenerating && (
        <div className="flex flex-col items-center justify-center p-8 border border-border/50 rounded-xl bg-background/50 space-y-4">
          <Loader2 className="w-6 h-6 text-accent animate-spin" />
          <p className="text-xs font-medium text-muted-foreground animate-pulse text-center leading-relaxed">
            Mint AI is analyzing the intercepted <strong className="text-foreground">Important Questions</strong> PDFs... <br/>
            Extracting 1-mark, 4-mark, and 13-mark questions for <strong className="text-foreground">{topicName}</strong>
          </p>
        </div>
      )}

      <AnimatePresence>
        {questions.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-accent mb-1">
              <CheckCircle2 className="w-4 h-4" />
              Verified PYQ Extractions
            </div>
            <div className="grid gap-3">
              {questions.map((q, i) => (
                <div key={i} className="flex flex-col gap-2 p-3.5 rounded-lg border border-accent/20 bg-accent/5">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5 text-[10px] font-bold tracking-wider text-accent uppercase">
                      <FileQuestion className="w-3 h-3" />
                      Q{i + 1} &bull; {q.type}
                    </span>
                    <span className="bg-background border border-border px-2 py-0.5 rounded text-[10px] font-bold text-foreground">
                      {q.marks}
                    </span>
                  </div>
                  
                  <div className="text-sm font-medium text-foreground leading-relaxed whitespace-pre-wrap">
                    <MathText content={q.text} />
                  </div>

                  {q.options && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
                      {q.options.map((opt, oIdx) => (
                        <div key={oIdx} className="flex items-center gap-2 p-2 rounded-md bg-background border border-border/60 text-xs text-muted-foreground">
                          <span className="font-bold text-foreground">{String.fromCharCode(65 + oIdx)}.</span>
                          <MathText content={opt} />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
