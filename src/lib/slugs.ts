export function generateSlug(courseName: string): string {
  if (!courseName) return "";
  const lower = courseName.toLowerCase();
  
  // Custom aliases for clean URLs as requested
  if (lower.includes("calculus")) return "calculus";
  if (lower.includes("chemistry") && !lower.includes("physical")) return "chemistry";
  if (lower.includes("spcm") || lower.includes("semiconductor")) return "spcm";
  if (lower.includes("eee") || lower.includes("electrical")) return "eee";
  if (lower.includes("oodp") || lower.includes("object oriented")) return "oodp";
  if (lower.includes("foreign language")) return "foreign-languages";
  
  // Fallback to standard slugification
  return lower.replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)+/g, '');
}

export function findCourseBySlug(slug: string, courses: any[]) {
  if (!slug || !courses) return null;
  
  // First pass: exact slug match
  for (const course of courses) {
    if (generateSlug(course.name) === slug) {
      return course;
    }
  }
  
  // Second pass: naive fallback if URL used a different format
  for (const course of courses) {
    const fallbackSlug = course.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)+/g, '');
    if (fallbackSlug === slug) return course;
  }
  
  return null;
}
