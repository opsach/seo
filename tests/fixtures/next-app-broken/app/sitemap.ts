import type { MetadataRoute } from 'next'
export default function sitemap(): MetadataRoute.Sitemap {
  return ['', '/about'].map((p) => ({ url: `https://yourbrand.com${p}`, lastModified: new Date() }))
}
