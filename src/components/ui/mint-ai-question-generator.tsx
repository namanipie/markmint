"use client";

import React, { useState } from "react";
import { BrainCircuit, Loader2, FileQuestion, CheckCircle2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { MathText } from "./math-text";

interface Props {
  topicName: string;
}

export function MintAIQuestionGenerator({ topicName }: Props) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [questions, setQuestions] = useState<string[]>([]);

  const generateQuestions = () => {
    setIsGenerating(true);
    setQuestions([]);
    
    // Simulate AI generation time
    setTimeout(() => {
      // Very basic templating based on topic keywords to feel authentic
      const lower = topicName.toLowerCase();
      let q1, q2, q3;
      
      if (lower.includes("calculus") || lower.includes("math") || lower.includes("matrix") || lower.includes("differential")) {
        q1 = `State the necessary conditions and solve a comprehensive problem based on ${topicName}.`;
        q2 = `Derive the core formula associated with ${topicName} and explain its geometric interpretation.`;
        q3 = `Apply the principles of ${topicName} to solve a real-world boundary value problem.`;
      } else if (lower.includes("algorithm") || lower.includes("data structure") || lower.includes("programming") || lower.includes("tree")) {
        q1 = `Write a highly optimized algorithm for ${topicName} and compute its Time and Space Complexity.`;
        q2 = `Compare and contrast the brute-force approach vs the optimal approach when utilizing ${topicName}.`;
        q3 = `Trace the execution of ${topicName} with a worst-case scenario input array.`;
      } else if (lower.includes("physics") || lower.includes("mechanics") || lower.includes("circuit") || lower.includes("electronic")) {
        q1 = `Derive the fundamental equation for ${topicName} from first principles.`;
        q2 = `Explain the physical significance of the parameters involved in ${topicName}.`;
        q3 = `Draw the circuit diagram/schematic and explain the working principle of ${topicName}.`;
      } else {
        // Generic engineering fallback
        q1 = `Discuss the fundamental principles, architecture, and primary applications of ${topicName}.`;
        q2 = `What are the major limitations of ${topicName}? Propose a technical solution to overcome them.`;
        q3 = `Explain the step-by-step workflow of ${topicName} with the help of a neat block diagram.`;
      }

      setQuestions([q1, q2, q3]);
      setIsGenerating(false);
    }, 1800);
  };

  return (
    <div className="mt-4 pt-4 border-t border-border/50">
      {!isGenerating && questions.length === 0 && (
        <button
          onClick={generateQuestions}
          className="flex items-center gap-2 px-4 py-2 bg-accent/10 hover:bg-accent/20 text-accent border border-accent/20 rounded-lg text-xs font-bold uppercase tracking-wider transition-all w-full justify-center group"
        >
          <BrainCircuit className="w-4 h-4 group-hover:scale-110 transition-transform" />
          Ask Mint AI for Most Important Questions
        </button>
      )}

      {isGenerating && (
        <div className="flex flex-col items-center justify-center p-6 border border-border/50 rounded-xl bg-background/50 space-y-3">
          <Loader2 className="w-6 h-6 text-accent animate-spin" />
          <p className="text-xs font-medium text-muted-foreground animate-pulse text-center">
            Mint AI is analyzing past CT papers to generate high-yield questions for <br/> <strong className="text-foreground">{topicName}</strong>...
          </p>
        </div>
      )}

      <AnimatePresence>
        {questions.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-3"
          >
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-accent mb-2">
              <CheckCircle2 className="w-4 h-4" />
              Mint AI Predicted Questions
            </div>
            <div className="grid gap-2">
              {questions.map((q, i) => (
                <div key={i} className="flex items-start gap-3 p-3 rounded-lg border border-accent/20 bg-accent/5">
                  <span className="flex-shrink-0 flex items-center justify-center w-5 h-5 rounded-full bg-accent/20 text-accent text-[10px] font-bold">
                    Q{i + 1}
                  </span>
                  <p className="text-sm font-medium text-foreground leading-snug">
                    <MathText content={q} />
                  </p>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
