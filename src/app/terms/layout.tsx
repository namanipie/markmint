import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms and Conditions | MarkMint",
  description:
    "Review the terms and conditions, acceptable use policies, and academic disclaimers for using MarkMint.",
  alternates: {
    canonical: "https://markmint.vercel.app/terms",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function TermsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
