"use client";

import { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Dna } from "lucide-react";

function RedirectHandler() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const qs = searchParams.toString();
    const destination = qs ? `/mintai/exam-dna?${qs}` : "/mintai/exam-dna";
    router.replace(destination);
  }, [router, searchParams]);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-xs text-muted-foreground flex items-center gap-2">
        <Dna className="w-4 h-4 text-accent animate-spin" />
        <span>Redirecting to MintAI Exam DNA...</span>
      </div>
    </div>
  );
}

export default function DashboardExamDNARedirect() {
  return (
    <Suspense fallback={null}>
      <RedirectHandler />
    </Suspense>
  );
}
