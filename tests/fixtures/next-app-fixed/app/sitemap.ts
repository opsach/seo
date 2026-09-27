import type { MetadataRoute } from 'next'

const pages = [
  { path: '', updated: '2026-06-02' },
  { path: '/about', updated: '2026-03-10' },
]

export default function sitemap(): MetadataRoute.Sitemap {
  return pages.map((p) => ({ url: `https://yourbrand.com${p.path}`, lastModified: new Date(p.updated) }))
}
