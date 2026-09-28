"use client";

import { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2 } from "lucide-react";

function MintAIRedirectContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const params = searchParams?.toString();
    const target = params ? `/dashboard?${params}#forecast` : `/dashboard#forecast`;
    router.replace(target);
  }, [router, searchParams]);

  return (
    <div className="min-h-screen bg-[#070b12] flex flex-col items-center justify-center p-4">
      <div className="flex items-center gap-3 text-emerald-400">
        <Loader2 className="w-6 h-6 animate-spin" />
        <span className="text-sm font-medium text-slate-300">
          Redirecting to MintAI Forecast Dashboard...
        </span>
      </div>
    </div>
  );
}

export default function MintAIRedirectPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#070b12] flex flex-col items-center justify-center p-4">
          <div className="flex items-center gap-3 text-emerald-400">
            <Loader2 className="w-6 h-6 animate-spin" />
            <span className="text-sm font-medium text-slate-300">
              Loading MintAI...
            </span>
          </div>
        </div>
      }
    >
      <MintAIRedirectContent />
    </Suspense>
  );
}
