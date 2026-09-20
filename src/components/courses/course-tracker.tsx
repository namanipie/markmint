"use client";

import { useEffect } from "react";
import { track } from "@vercel/analytics";

interface CourseTrackerProps {
  courseSlug: string;
  semester?: number;
  hasTracks?: boolean;
}

export function CourseTracker({ courseSlug, semester, hasTracks }: CourseTrackerProps) {
  useEffect(() => {
    try {
      track("course_page_view", {
        course: courseSlug,
        semester: semester ?? 1,
        has_tracks: hasTracks ? "true" : "false",
      });
    } catch {
      // Analytics failure should never break user experience
    }
  }, [courseSlug, semester, hasTracks]);

  return null;
}
