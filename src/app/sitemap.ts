import { MetadataRoute } from "next";
import { getAllCourses } from "@/lib/courses";
import { getAllTopics } from "@/lib/topics";

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = "https://markmint.vercel.app";
  const now = new Date();

  const staticPages: MetadataRoute.Sitemap = [
    {
      url: baseUrl,
      lastModified: now,
      changeFrequency: "weekly",
      priority: 1.0,
    },
    {
      url: `${baseUrl}/courses`,
      lastModified: now,
      changeFrequency: "daily",
      priority: 0.95,
    },
    {
      url: `${baseUrl}/mintai`,
      lastModified: now,
      changeFrequency: "daily",
      priority: 0.9,
    },
    {
      url: `${baseUrl}/study-plan`,
      lastModified: now,
      changeFrequency: "weekly",
      priority: 0.85,
    },
    {
      url: `${baseUrl}/calculator`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${baseUrl}/developers`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.5,
    },
  ];

  const courses = getAllCourses();
  const coursePages: MetadataRoute.Sitemap = courses.map((course) => ({
    url: `${baseUrl}/courses/${course.slug}`,
    lastModified: now,
    changeFrequency: "weekly",
    priority: 0.85,
  }));

  const languageTrackPages: MetadataRoute.Sitemap = [];
  const foreignLangCourse = courses.find((c) => c.hasTracks && c.tracks?.length > 0);
  if (foreignLangCourse && foreignLangCourse.tracks) {
    for (const track of foreignLangCourse.tracks) {
      languageTrackPages.push({
        url: `${baseUrl}/courses/foreign-languages?track=${track.trackKey}`,
        lastModified: now,
        changeFrequency: "weekly",
        priority: 0.8,
      });
    }
  }

  const topics = getAllTopics();
  const topicPages: MetadataRoute.Sitemap = topics.map((topic) => ({
    url: topic.canonicalUrl,
    lastModified: now,
    changeFrequency: "weekly",
    priority: 0.75,
  }));

  return [...staticPages, ...coursePages, ...languageTrackPages, ...topicPages];
}
