import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "MintAi | Historical Exam Intelligence & Evidence-Based Forecasting",
  description: "Forecast high-yield topics using verified historical exam evidence. Analyze recurrence patterns and explore authentic past question papers.",
  alternates: {
    canonical: "https://markmint.vercel.app/mintai",
  },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
