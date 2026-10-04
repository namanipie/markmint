import type { Metadata } from "next";
import { HomeView } from "@/components/home/home-view";

export const metadata: Metadata = {
  title: "MintAI | Exam Intelligence for SRMIST",
  description:
    "MintAI helps SRMIST students study from historical exam evidence, course intelligence, and focused study workflows.",
  alternates: {
    canonical: "https://markmint.vercel.app/",
  },
};

const jsonLd = [
  {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": "MarkMint",
    "url": "https://markmint.vercel.app",
    "description": "MintAi predicts your CT, FT, and End Sem question papers for SRMIST.",
    "potentialAction": {
      "@type": "SearchAction",
      "target": "https://markmint.vercel.app/mintai?course={search_term_string}",
      "query-input": "required name=search_term_string",
    }
  },
  {
    "@context": "https://schema.org",
    "@type": "Person",
    "name": "Aditya Kajala",
    "url": "https://markmint.vercel.app",
    "jobTitle": "Founder & Frontend Engineer",
    "worksFor": {
      "@type": "Organization",
      "name": "MarkMint",
      "url": "https://markmint.vercel.app"
    },
    "sameAs": [
      "https://www.linkedin.com/in/adityakajala",
      "https://github.com/adityakajala1"
    ]
  },
  {
    "@context": "https://schema.org",
    "@type": "Person",
    "name": "Naman Kumar",
    "jobTitle": "Founder & Developer",
    "worksFor": {
      "@type": "Organization",
      "name": "MarkMint"
    }
  }
];

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
