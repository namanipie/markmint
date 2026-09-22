"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { initErrorObservability, trackBetaEvent } from "@/lib/telemetry";

export function BetaObservabilityProvider() {
  const pathname = usePathname();

  useEffect(() => {
    initErrorObservability();
  }, []);

  useEffect(() => {
    if (pathname === "/") {
      trackBetaEvent("landing", { route: "/" });
    }
  }, [pathname]);

  return null;
}
