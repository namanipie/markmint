import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Strict regex requiring punctuation (. ) : -) or parentheses to avoid stripping word quantities like "15 samples..."
const QUESTION_PREFIX_REGEX = /^\s*(?:Q(?:uestion)?\.?\s*\d{1,3}\s*[\.\:\)\-]\s*(?:\([a-zA-Z0-9]+\)|[a-zA-Z][\.\:\)\-])?\s*|\d{1,3}\s*[\.\:\)]\s*(?:\([a-zA-Z0-9]+\)|[a-zA-Z][\.\:\)\-])?\s*|\d{1,3}\s*\([a-zA-Z0-9]+\)[\.\:\-]?\s*|\d{1,3}[a-zA-Z][\.\:\)\-]\s*|\([a-zA-Z0-9]{1,3}\)\s*|[a-zA-Z][\.\)]\s+)/i;

/**
 * Strips redundant leading question numbers/labels (e.g., '1.', 'Q1.', '21(a)', '(a)')
 * from question text for clean, duplicate-free UI presentation.
 * Preserves mathematical expressions, code syntax (e.g. `a[0]`), word problem quantities (e.g. "15 samples"),
 * and question stem content.
 */
export function cleanQuestionText(text?: string | null): string {
  if (!text) return "";
  const trimmed = text.trim();
  const cleaned = trimmed.replace(QUESTION_PREFIX_REGEX, "").trim();

  // Guard: if stripping left nothing meaningful or only punctuation, fallback to original
  if (cleaned.length < 2 || /^[\d\s\.\:\)\-]+$/.test(cleaned)) {
    return trimmed;
  }
  return cleaned;
}
