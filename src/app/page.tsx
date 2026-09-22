import type { Metadata } from "next";
import { HomeView } from "@/components/home/home-view";

export const metadata: Metadata = {
  title: "MarkMint | Exam Intelligence & GPA Analytics for SRMIST",
  description:
    "Forecast high-yield topics using verified historical exam evidence. Calculate your GPA instantly for 40+ engineering branches.",
  alternates: {
    canonical: "https://markmint.vercel.app/",
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "MarkMint",
  "url": "https://markmint.vercel.app",
  "description": "MintAi predicts your CT, FT, and End Sem question papers for SRMIST.",
  "potentialAction": {
    "@type": "SearchAction",
    "target": "https://markmint.vercel.app/mintai?course={search_term_string}",
    "query-input": "required name=search_term_string",
  },
};

export default function Home() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <HomeView />
    </>
  );
}
