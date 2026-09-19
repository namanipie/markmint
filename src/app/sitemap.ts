import { MetadataRoute } from 'next'
import { getCourses } from '@/lib/api'
import { generateSlug } from '@/lib/slugs'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = 'https://markmint.vercel.app'
  
  // Base routes
  const routes: MetadataRoute.Sitemap = [
    {
      url: `${baseUrl}`,
      lastModified: new Date(),
      changeFrequency: 'daily',
      priority: 1,
    },
    {
      url: `${baseUrl}/mintai`,
      lastModified: new Date(),
      changeFrequency: 'always',
      priority: 0.9,
    },
    {
      url: `${baseUrl}/study-plan`,
      lastModified: new Date(),
      changeFrequency: 'always',
      priority: 0.8,
    },
    {
      url: `${baseUrl}/practice`,
      lastModified: new Date(),
      changeFrequency: 'always',
      priority: 0.8,
    }
  ]

  // Dynamic course routes
  try {
    const courses = await getCourses()
    
    if (courses && Array.isArray(courses)) {
      const courseRoutes = courses.map((course: any) => ({
        url: `${baseUrl}/srm/${generateSlug(course.name)}`,
        lastModified: new Date(),
        changeFrequency: 'weekly' as const,
        priority: 0.7,
      }))
      
      return [...routes, ...courseRoutes]
    }
  } catch (error) {
    console.error('Failed to generate sitemap for courses:', error)
  }

  return routes
}
