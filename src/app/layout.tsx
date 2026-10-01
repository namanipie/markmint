import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono, Dancing_Script } from "next/font/google";
import "./globals.css";
import "katex/dist/katex.min.css";
import { Toaster } from "sonner";
import { CommandPalette } from "@/components/ui/command-palette";
import { GlobalFeatures } from "@/components/ui/GlobalFeatures";
import { BetaObservabilityProvider } from "@/components/ui/BetaObservabilityProvider";

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
import { Analytics } from "@vercel/analytics/next";
import { SpeedInsights } from "@vercel/speed-insights/next";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_BASE_URL || "https://markmint.vercel.app"),
  title: "MarkMint | Exam Intelligence & GPA Analytics for SRMIST",
  description: "Forecast high-yield topics using verified historical exam evidence. Calculate your GPA instantly for 40+ engineering branches.",
  authors: [
    { name: "Aditya Kajala", url: "https://github.com/adityakajala1" },
    { name: "Naman Kumar", url: "https://github.com/namanipie" }
  ],
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
    title: "MintAI | SRMIST Academic Intelligence",
    description: "Forecast high-yield topics using verified historical exam evidence.",
  },
  verification: {
    google: "xCV7uIaHTrTcL3-G9SqrLSMP3YJQJIi1oPaeNd49f3o",
  },
  appleWebApp: {
    capable: true,
    title: "MintAI",
    statusBarStyle: "black-translucent",
  },
  formatDetection: {
    telephone: false,
  }
};

export const viewport: Viewport = {
  themeColor: "#10b981",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "MarkMint",
    "applicationCategory": "EducationalApplication",
    "operatingSystem": "Web",
    "description": "Academic intelligence and exam analytics platform for SRMIST students.",
    "url": "https://markmint.vercel.app",
    "author": [
      {
        "@type": "Person",
        "name": "Aditya Kajala",
        "jobTitle": "Founder & Lead Frontend Engineer",
        "url": "https://github.com/adityakajala1"
      },
      {
        "@type": "Person",
        "name": "Naman Kumar",
        "jobTitle": "Founder & Lead Backend Engineer",
        "url": "https://github.com/namanipie"
      }
    ],
    "creator": {
      "@type": "Organization",
      "name": "MarkMint",
      "founder": [
        {
          "@type": "Person",
          "name": "Aditya Kajala"
        },
        {
          "@type": "Person",
          "name": "Naman Kumar"
        }
      ]
    }
  };

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
                <GlobalFeatures />
        <BetaObservabilityProvider />
      </ThemeProvider>
      <Analytics />
      <SpeedInsights />
      </body>
    </html>
  );
}
