import { MetadataRoute } from 'next'

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'MarkMint | SRM Study Hub',
    short_name: 'MarkMint',
    description: 'Exam Intelligence & GPA Analytics for SRMIST',
    start_url: '/',
    display: 'standalone',
    background_color: '#09090b', // Tailwind zinc-950 (background)
    theme_color: '#10b981', // Tailwind emerald-500 (brand color)
    icons: [
      {
        src: '/icon?size=192',
        sizes: '192x192',
        type: 'image/png',
      },
      {
        src: '/icon?size=512',
        sizes: '512x512',
        type: 'image/png',
      },
    ],
  }
}
