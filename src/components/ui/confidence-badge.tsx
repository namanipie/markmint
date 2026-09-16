import { cn } from "@/lib/utils";

export interface ConfidenceBadgeProps {
  confidence: "HIGH" | "MEDIUM" | "LOW" | "INSUFFICIENT" | number | string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function ConfidenceBadge({ confidence, size = "md", className }: ConfidenceBadgeProps) {
  let colorClass = "bg-muted text-muted-foreground border border-border";
  let displayLabel = String(confidence);

  if (typeof confidence === "string") {
    const upper = confidence.toUpperCase();
    if (upper === "HIGH") {
      colorClass = "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20";
      displayLabel = "High Confidence";
    } else if (upper === "MEDIUM") {
      colorClass = "bg-amber-500/10 text-amber-500 border border-amber-500/20";
      displayLabel = "Medium Confidence";
    } else if (upper === "LOW") {
      colorClass = "bg-muted text-muted-foreground border border-border";
      displayLabel = "Low Confidence";
    } else if (upper === "INSUFFICIENT") {
      colorClass = "bg-rose-500/10 text-rose-500 border border-rose-500/20";
      displayLabel = "Insufficient Evidence";
    }
  } else if (typeof confidence === "number") {
    if (confidence >= 75) {
      colorClass = "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20";
    } else if (confidence >= 50) {
      colorClass = "bg-amber-500/10 text-amber-500 border border-amber-500/20";
    } else {
      colorClass = "bg-rose-500/10 text-rose-500 border border-rose-500/20";
    }
    displayLabel = `${confidence}%`;
  }

  const sizeClass = {
    sm: "px-2 py-0.5 text-xs",
    md: "px-2.5 py-1 text-xs",
    lg: "px-3 py-1.5 text-sm",
  }[size];

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full font-mono font-bold tracking-tight",
        colorClass,
        sizeClass,
        className
      )}
    >
      {displayLabel}
    </span>
  );
}
