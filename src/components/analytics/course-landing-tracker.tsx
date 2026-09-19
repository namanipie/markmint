"use client";

import { useEffect } from "react";
import { useAnalytics } from "@/hooks/use-analytics";

export function CourseLandingTracker({ courseId, courseSlug }: { courseId: string | number, courseSlug: string }) {
  const { trackOnce } = useAnalytics();
  
  useEffect(() => {
    trackOnce("course_landing_view", courseSlug, {
      course_id: courseId,
      course_slug: courseSlug
    });
  }, [courseId, courseSlug, trackOnce]);
  
  return null;
}
