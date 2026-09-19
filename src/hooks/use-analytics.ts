import { useRef, useCallback } from "react";
import { trackEvent } from "@/lib/analytics";

export function useAnalytics() {
  const trackedEvents = useRef<Set<string>>(new Set());

  // Track an event only once per key (to prevent React re-render duplicates)
  const trackOnce = useCallback((eventName: string, key: string, properties: Record<string, any> = {}) => {
    const eventKey = `${eventName}:${key}`;
    if (!trackedEvents.current.has(eventKey)) {
      trackedEvents.current.add(eventKey);
      trackEvent(eventName, properties);
    }
  }, []);

  return { trackEvent, trackOnce };
}
