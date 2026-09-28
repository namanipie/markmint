import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  compress: true,
  outputFileTracingExcludes: {
    "*": [
      "./backend/**/*",
      "./data/**/*",
      "./scripts/**/*",
      "./corpus/**/*",
      "./**/*.db",
      "./**/*.sqlite",
      "./**/*.sqlite3",
      "./**/*.dump",
      "./**/*.pdf",
    ],
  },

  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "X-DNS-Prefetch-Control",
            value: "on",
          },
          {
            key: "Strict-Transport-Security",
            value: "max-age=63072000; includeSubDomains; preload",
          },
          {
            key: "X-Frame-Options",
            value: "SAMEORIGIN",
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=(), browsing-topics=()",
          },
        ],
      },
    ];
  },

  async redirects() {
    return [
      {
        source: "/dashboard/exam-dna",
        destination: "/mintai/exam-dna",
        permanent: true,
      },
      {
        source: "/mintai",
        destination: "/dashboard",
        permanent: false,
      },
    ];
  },

  devIndicators: {
  },
};

export default nextConfig;
