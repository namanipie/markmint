import type { Metadata } from "next";
import { Geist, Geist_Mono, Dancing_Script } from "next/font/google";
import "./globals.css";
import "katex/dist/katex.min.css";
import { Toaster } from "sonner";
import { CommandPalette } from "@/components/ui/command-palette";
import { GlobalFeatures } from "@/components/ui/GlobalFeatures";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const dancingScript = Dancing_Script({
  variable: "--font-dancing",
  subsets: ["latin"],
  weight: ["400", "700"],
});

import { ThemeProvider } from "@/components/theme-provider";
import { EasterEggManager } from "@/components/ambient/EasterEggManager";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_BASE_URL || "https://markmint.vercel.app"),
  title: "MarkMint | Exam Intelligence & GPA Analytics for SRMIST",
  description: "Forecast high-yield topics using verified historical exam evidence. Calculate your GPA instantly for 40+ engineering branches.",
  alternates: {
    canonical: "/",
  },
  openGraph: {
    title: "MarkMint | SRMIST Academic Intelligence",
    description: "Forecast high-yield topics using verified historical exam evidence. Generate structured study plans and explore past questions.",
    url: "https://markmint.vercel.app",
    siteName: "MarkMint",
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "MarkMint | SRMIST Academic Intelligence",
    description: "Forecast high-yield topics using verified historical exam evidence.",
  },
  verification: {
    google: "xCV7uIaHTrTcL3-G9SqrLSMP3YJQJIi1oPaeNd49f3o",
  }
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
    "query-input": "required name=search_term_string"
  }
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} ${dancingScript.variable} h-full antialiased`} suppressHydrationWarning
    >
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body className="min-h-full flex flex-col bg-background text-foreground relative">        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
        {children}
        <Toaster
          theme="dark"
          position="bottom-right"
          toastOptions={{
            style: {
              background: "#18181b",
              border: "1px solid #27272a",
              color: "#fafafa",
            },
          }}
        />
        <EasterEggManager />
        <GlobalFeatures />
      </ThemeProvider>
      </body>
    </html>
  );
}
