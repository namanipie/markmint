import { MetadataRoute } from "next";
import { getAllCourses } from "@/lib/courses";

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = "https://markmint.vercel.app";

  const baseRoutes: MetadataRoute.Sitemap = [
    {
      url: `${baseUrl}`,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 1.0,
    },
    {
      url: `${baseUrl}/mintai`,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 0.9,
    },
    {
      url: `${baseUrl}/courses`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${baseUrl}/study-plan`,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 0.8,
    },
    {
      url: `${baseUrl}/calculator`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${baseUrl}/developers`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.5,
    },
  ];

  // Canonical public course URLs from authoritative catalog
  const courses = getAllCourses();
  const seenSlugs = new Set<string>();
  const courseRoutes: MetadataRoute.Sitemap = [];

  for (const course of courses) {
    if (course.slug && !seenSlugs.has(course.slug)) {
      seenSlugs.add(course.slug);
      courseRoutes.push({
        url: `${baseUrl}/courses/${course.slug}`,
        lastModified: new Date(),
        changeFrequency: "weekly",
        priority: 0.7,
      });
    }
  }

  return [...baseRoutes, ...courseRoutes];
}
