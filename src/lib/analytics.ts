import { track } from "@vercel/analytics";

let sessionIdentifier: string | null = null;

export function getSessionId() {
  if (typeof window === "undefined") return "server";
  if (!sessionIdentifier) {
    sessionIdentifier = Math.random().toString(36).substring(2, 15);
  }
  return sessionIdentifier;
}

export function trackEvent(eventName: string, properties: Record<string, any> = {}) {
  try {
    const payload = {
      ...properties,
      timestamp: new Date().toISOString(),
      session_id: getSessionId(),
      path: typeof window !== "undefined" ? window.location.pathname : "server",
    };

    // Vercel Analytics tracking (fire and forget)
    track(eventName, payload);

    // Debug logging in development without exposing to normal users
    if (process.env.NODE_ENV === "development" || (typeof window !== 'undefined' && window.localStorage.getItem('DEBUG_ANALYTICS') === 'true')) {
      console.debug(`[Analytics] ${eventName}`, payload);
    }
  } catch (error) {
    // Fail silently so we never break the application
    console.error("[Analytics] Tracking failed:", error);
  }
}
