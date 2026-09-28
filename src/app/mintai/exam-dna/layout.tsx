import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Historical Exam Evidence | MintAI",
  description:
    "Empirical past-paper evidence, assessment blueprints, cognitive demand signals, and question repetition backing MintAI exam forecasts for SRMIST.",
};

export default function ExamDNALayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
