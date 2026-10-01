import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Restricted Access",
  robots: {
    index: false,
    follow: false,
  },
};

export default function ModsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
