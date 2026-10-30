"use client";

import { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2 } from "lucide-react";

function DashboardRedirectHandler() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const qs = searchParams?.toString();
    const target = qs ? `/mintai?${qs}` : "/mintai";
    router.replace(target);
  }, [router, searchParams]);

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
      <div className="flex items-center gap-3 text-accent">
        <Loader2 className="w-6 h-6 animate-spin" />
        <span className="text-sm font-medium text-muted-foreground">
          Redirecting to MintAI Intelligence Engine...
        </span>
      </div>
    </div>
  );
}

export default function DashboardRedirectPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
          <div className="flex items-center gap-3 text-accent">
            <Loader2 className="w-6 h-6 animate-spin" />
            <span className="text-sm font-medium text-muted-foreground">
              Loading MintAI...
            </span>
          </div>
        </div>
      }
    >
      <DashboardRedirectHandler />
    </Suspense>
  );
}
