import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy Policy | MintAI",
  description:
    "Review MintAI's privacy practices, data handling, and telemetry transparency for SRMIST students.",
  alternates: {
    canonical: "https://markmint.vercel.app/privacy",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function PrivacyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
