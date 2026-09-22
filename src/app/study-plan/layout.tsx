import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Study Plan & Exam Preparation Roadmap | MarkMint",
  description:
    "Generate structured study priorities and track revision progress based on verified historical exam evidence.",
  alternates: {
    canonical: "https://markmint.vercel.app/study-plan",
  },
};

export default function StudyPlanLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
