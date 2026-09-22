import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "The Duo | MarkMint Developers",
  description: "Built, designed, engineered, and maintained by SRMIST students.",
  alternates: {
    canonical: "https://markmint.vercel.app/developers",
  },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
