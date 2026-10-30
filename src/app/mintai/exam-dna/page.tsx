"use client";

import { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Dna } from "lucide-react";

function ExamDNARedirectHandler() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const params = new URLSearchParams(searchParams?.toString() || "");
    params.set("tab", "dna");
    router.replace(`/mintai?${params.toString()}`);
  }, [router, searchParams]);

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
      <div className="flex items-center gap-3 text-accent">
        <Dna className="w-6 h-6 animate-spin" />
        <span className="text-sm font-medium text-muted-foreground">
          Loading MintAI Exam DNA Intelligence...
        </span>
      </div>
    </div>
  );
}

export default function ExamDNAPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
          <div className="flex items-center gap-3 text-accent">
            <Dna className="w-6 h-6 animate-spin" />
            <span className="text-sm font-medium text-muted-foreground">
              Loading Exam DNA...
            </span>
          </div>
        </div>
      }
    >
      <ExamDNARedirectHandler />
    </Suspense>
  );
}
