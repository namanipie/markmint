import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Exam DNA &bull; Historical Examination Analytics | MintAI",
  description:
    "Explore empirical assessment blueprints, cognitive demand signals, syllabus unit weightings, and formulation lineage across verified historical papers in MintAI.",
};

export default function ExamDNALayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
