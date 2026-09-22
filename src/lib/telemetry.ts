/**
 * MarkMint Phase 13: Anonymous Beta Telemetry & Observability
 * 
 * Strictly anonymous - ZERO PII (no names, emails, IPs, or question text).
 * Measures the beta funnel, tracks UX friction, records micro-feedback,
 * and monitors runtime client errors safely.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
const SESSION_STORAGE_KEY = "mm_beta_sid";
const FEEDBACK_STORAGE_KEY = "mm_beta_feedback_given";

/**
 * Returns a stable anonymous session ID persisted in localStorage.
 * Format: anon_xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
 */
export function getAnonymousSessionId(): string {
  if (typeof window === "undefined") return "server_anonymous";
  try {
    let sid = localStorage.getItem(SESSION_STORAGE_KEY);
    if (!sid) {
      sid = "anon_" + (typeof crypto !== "undefined" && crypto.randomUUID 
        ? crypto.randomUUID() 
        : Math.random().toString(36).substring(2, 15) + Date.now().toString(36));
      localStorage.setItem(SESSION_STORAGE_KEY, sid);
    }
    return sid;
  } catch (e) {
    return "ephemeral_anonymous";
  }
}

/**
 * Check if the user has already given micro-feedback in this browser.
 */
export function hasGivenBetaFeedback(): boolean {
  if (typeof window === "undefined") return true;
  try {
    return localStorage.getItem(FEEDBACK_STORAGE_KEY) === "true";
  } catch (e) {
    return false;
  }
}

export function markBetaFeedbackGiven(): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(FEEDBACK_STORAGE_KEY, "true");
  } catch (e) {}
}

export interface TelemetryPayload {
  route?: string | null;
  course_id?: number | null;
  course_code?: string | null;
  assessment_cycle?: string | null;
  metadata?: Record<string, any> | null;
}

/**
 * Records a funnel event (landing, course_selection, assessment_selection, intelligence_view, etc.)
 */
export async function trackBetaEvent(
  eventName: string,
  payload: TelemetryPayload = {}
): Promise<void> {
  if (typeof window === "undefined") return;

  const currentRoute = payload.route || window.location.pathname;
  const eventItem = {
    session_id: getAnonymousSessionId(),
    event_name: eventName,
    route: currentRoute,
    course_id: payload.course_id,
    course_code: payload.course_code,
    assessment_cycle: payload.assessment_cycle,
    metadata: payload.metadata || {},
  };

  const body = JSON.stringify({ events: [eventItem] });

  try {
    // Prefer sendBeacon for non-blocking transport if available
    if (navigator.sendBeacon) {
      const blob = new Blob([body], { type: "application/json" });
      const ok = navigator.sendBeacon(`${API_BASE}/analytics/events`, blob);
      if (ok) return;
    }

    // Fallback to fetch
    await fetch(`${API_BASE}/analytics/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      keepalive: true,
    });
  } catch (err) {
    // Fail silently so student experience is never impacted
  }
}

/**
 * Convenience method for tracking friction events (e.g. course_selection_abandoned, practice_empty)
 */
export function trackFrictionEvent(
  frictionType:
    | "course_selection_abandoned"
    | "assessment_selection_abandoned"
    | "practice_empty"
    | "study_plan_empty"
    | "prediction_no_evidence"
    | "api_error"
    | "page_error",
  payload: TelemetryPayload = {}
): void {
  trackBetaEvent(frictionType, payload);
}

/**
 * Submits anonymous student micro-feedback ("Was this useful? [Yes] [No]")
 */
export async function submitBetaFeedback(
  useful: boolean,
  confusionReason?: string,
  context?: { route?: string; course_code?: string }
): Promise<boolean> {
  const sessionId = getAnonymousSessionId();
  const route = context?.route || (typeof window !== "undefined" ? window.location.pathname : undefined);

  try {
    const res = await fetch(`${API_BASE}/analytics/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        useful,
        confusion_reason: confusionReason ? confusionReason.trim().slice(0, 500) : null,
        route,
        course_code: context?.course_code,
      }),
    });
    if (res.ok) {
      markBetaFeedbackGiven();
      return true;
    }
    return false;
  } catch (err) {
    return false;
  }
}

/**
 * Reports a client-side runtime error strictly stripped of sensitive data.
 */
export async function reportBetaError(
  errorType: string,
  message?: string,
  route?: string,
  context?: Record<string, any>
): Promise<void> {
  if (typeof window === "undefined") return;

  const currentRoute = route || window.location.pathname;
  const safeMessage = (message || "Unknown error")
    .replace(/[\w\.-]+@[\w\.-]+\.\w+/g, "[REDACTED_EMAIL]")
    .replace(/(bearer|token|secret|password)[\s:=]+[\w\.-]+/gi, "[REDACTED_AUTH]")
    .slice(0, 500);

  const payload = {
    session_id: getAnonymousSessionId(),
    route: currentRoute,
    error_type: errorType.slice(0, 64),
    message: safeMessage,
    context: context ? JSON.parse(JSON.stringify(context)) : {},
  };

  try {
    await fetch(`${API_BASE}/analytics/errors`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      keepalive: true,
    });
  } catch (e) {
    // Suppress error logging failure
  }
}

/**
 * Initializes global client error listeners once per window session.
 */
let errorListenersInitialized = false;

export function initErrorObservability(): void {
  if (typeof window === "undefined" || errorListenersInitialized) return;
  errorListenersInitialized = true;

  window.addEventListener("error", (event) => {
    reportBetaError(
      "UncaughtException",
      event.message || "Script error",
      window.location.pathname,
      {
        filename: event.filename ? event.filename.split("/").pop() : undefined,
        lineno: event.lineno,
        colno: event.colno,
      }
    );
  });

  window.addEventListener("unhandledrejection", (event) => {
    const reasonMsg = event.reason instanceof Error ? event.reason.message : String(event.reason);
    reportBetaError(
      "UnhandledPromiseRejection",
      reasonMsg,
      window.location.pathname
    );
  });
}
