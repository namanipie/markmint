"use client";

import { useEffect } from "react";
import { track } from "@vercel/analytics";
import { updateStudyContext } from "@/lib/study-context";

interface CourseTrackerProps {
  courseId?: number;
  courseName?: string;
  courseCode?: string;
  courseSlug: string;
  semester?: number;
  hasTracks?: boolean;
}

export function CourseTracker({
  courseId,
  courseName,
  courseCode,
  courseSlug,
  semester,
  hasTracks,
}: CourseTrackerProps) {
  useEffect(() => {
    try {
      track("course_page_view", {
        course: courseSlug,
        semester: semester ?? 1,
        has_tracks: hasTracks ? "true" : "false",
      });

      if (courseId && courseName) {
        updateStudyContext({
          course_id: courseId,
          course_name: courseName,
          course_code: courseCode,
          semester: semester ?? 1,
          last_activity_type: "select_course",
        });
      }
    } catch {
      // Analytics failure should never break user experience
    }
  }, [courseId, courseName, courseCode, courseSlug, semester, hasTracks]);

  return null;
}
