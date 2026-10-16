import { ImageResponse } from "next/og";

export const alt = "MarkMint - SRMIST Academic Intelligence";
export const size = {
  width: 1200,
  height: 630,
};
export const contentType = "image/png";

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          background: "#0B1110",
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "60px 70px",
          color: "#F3F0E8",
          fontFamily: "sans-serif",
          position: "relative",
        }}
      >
        {/* Ambient glow */}
        <div
          style={{
            position: "absolute",
            top: "-100px",
            left: "50px",
            width: "500px",
            height: "500px",
            borderRadius: "50%",
            background: "rgba(16, 185, 129, 0.14)",
            filter: "blur(90px)",
          }}
        />
        <div
          style={{
            position: "absolute",
            bottom: "-100px",
            right: "50px",
            width: "500px",
            height: "500px",
            borderRadius: "50%",
            background: "rgba(230, 50, 122, 0.12)",
            filter: "blur(90px)",
          }}
        />

        {/* Top: Brand Header */}
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          {/* Leaf Icon SVG */}
          <svg
            width="52"
            height="52"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#10B981"
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z" />
            <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" />
          </svg>
          <span style={{ fontSize: 44, fontWeight: 800, letterSpacing: "-0.03em" }}>MarkMint</span>
          <div
            style={{
              padding: "4px 12px",
              borderRadius: "6px",
              background: "#2C1620",
              border: "1px solid #A0285A",
              color: "#E6327A",
              fontSize: 16,
              fontWeight: 700,
              letterSpacing: "0.08em",
            }}
          >
            BETA
          </div>
        </div>

        {/* Center: Main Headline */}
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ fontSize: 56, fontWeight: 800, letterSpacing: "-0.03em", lineHeight: 1.15 }}>
            Predict your exams with
          </div>
          <div style={{ fontSize: 62, fontWeight: 800, fontStyle: "italic", color: "#10B981", lineHeight: 1.15 }}>
            historical evidence.
          </div>
          <div style={{ fontSize: 24, color: "#B8C2BF", marginTop: "12px", fontWeight: 400 }}>
            Past papers. Real patterns. Smarter preparation for SRMIST students.
          </div>
        </div>

        {/* Bottom: Feature Pills */}
        <div style={{ display: "flex", gap: "16px" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              padding: "10px 22px",
              borderRadius: "9999px",
              background: "#18221D",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              fontSize: 18,
              fontWeight: 600,
              color: "#F3F0E8",
            }}
          >
            9,205 Verified Questions
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              padding: "10px 22px",
              borderRadius: "9999px",
              background: "#18221D",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              fontSize: 18,
              fontWeight: 600,
              color: "#F3F0E8",
            }}
          >
            320 Exam Papers
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              padding: "10px 22px",
              borderRadius: "9999px",
              background: "#18221D",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              fontSize: 18,
              fontWeight: 600,
              color: "#10B981",
            }}
          >
            AI Blueprint Forecasts
          </div>
        </div>
      </div>
    ),
    { ...size }
  );
}
