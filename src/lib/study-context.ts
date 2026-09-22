export type StudyActivityType =
  | "select_course"
  | "open_mintai"
  | "open_topic"
  | "open_question"
  | "start_study_task"
  | "complete_task"
  | "reset_task";

export interface StudyContext {
  course_id: number;
  course_name: string;
  course_code?: string;
  track_id?: number | null;
  track_key?: string | null;
  language?: string | null;
  branch?: string;
  semester?: number;
  assessment_cycle?: string;
  last_topic_id?: number | string | null;
  last_topic_name?: string | null;
  last_activity_type?: StudyActivityType;
  last_activity_at?: string; // ISO 8601 string
  // Local task states keyed by topic name or id
  task_statuses?: Record<string, "NOT_STARTED" | "IN_PROGRESS" | "COMPLETED">;
}

const STORAGE_KEY = "markmint_study_context";

export function getStudyContext(): StudyContext | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object" || !parsed.course_id || !parsed.course_name) {
      return null;
    }
    return parsed as StudyContext;
  } catch {
    return null;
  }
}

export function updateStudyContext(patch: Partial<StudyContext>): StudyContext | null {
  if (typeof window === "undefined") return null;
  try {
    const current = getStudyContext() || ({} as Partial<StudyContext>);
    const updated: StudyContext = {
      ...current,
      ...patch,
      course_id: patch.course_id ?? current.course_id ?? 0,
      course_name: patch.course_name ?? current.course_name ?? "",
      task_statuses: {
        ...(current.task_statuses || {}),
        ...(patch.task_statuses || {}),
      },
      last_activity_at: new Date().toISOString(),
    };

    if (!updated.course_id || !updated.course_name) {
      return null;
    }

    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));

    // Also dispatch a custom storage event so other components on the same tab can react if needed
    window.dispatchEvent(new CustomEvent("markmint:study_context_updated", { detail: updated }));

    return updated;
  } catch {
    return null;
  }
}

export function setTopicTaskStatus(
  topicNameOrId: string,
  status: "NOT_STARTED" | "IN_PROGRESS" | "COMPLETED"
): StudyContext | null {
  const current = getStudyContext();
  if (!current) return null;
  const taskStatuses = { ...(current.task_statuses || {}) };
  taskStatuses[topicNameOrId] = status;
  return updateStudyContext({
    task_statuses: taskStatuses,
    last_topic_name: topicNameOrId,
    last_activity_type: status === "COMPLETED" ? "complete_task" : "start_study_task",
  });
}

export function clearStudyContext(): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem(STORAGE_KEY);
    window.dispatchEvent(new CustomEvent("markmint:study_context_cleared"));
  } catch {
    // Ignore storage errors
  }
}
