import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Dashboard &bull; Study Intelligence & Exam Overview | MintAI",
  description:
    "Monitor your active SRMIST engineering study context, inspect predictive exam forecasts, review historical exam blueprints, and continue your study plan in MintAI.",
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
