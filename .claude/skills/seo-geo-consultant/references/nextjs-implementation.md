# Next.js SEO Implementation Guide

Production-ready code patterns for implementing SEO in Next.js App Router projects.

## Table of Contents
1. [Metadata API](#metadata-api)
2. [JSON-LD Structured Data](#json-ld)
3. [Sitemap Generation](#sitemap)
4. [robots.txt](#robots)
5. [Open Graph & Twitter Cards](#og-twitter)
6. [Dynamic OG Images](#dynamic-og)
7. [Core Web Vitals](#cwv)
8. [Canonical URLs](#canonical)
9. [International SEO](#i18n)

---

## 1. Metadata API <a name="metadata-api"></a>

### Root Layout (Site-Wide Defaults)

```tsx
// app/layout.tsx
import type { Metadata } from 'next'

export const metadata: Metadata = {
  metadataBase: new URL('https://yourdomain.com'),
  title: {
    template: '%s | YourBrand',
    default: 'YourBrand - One-line value prop',
  },
  description: 'Your 150-160 char meta description with a call-to-action.',
  keywords: ['primary keyword', 'secondary keyword', 'brand name'],
  authors: [{ name: 'Author Name', url: 'https://yourdomain.com' }],
  creator: 'YourBrand',
  publisher: 'YourBrand',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  openGraph: {
    title: 'YourBrand - One-line value prop',
    description: 'Your OG description (can differ from meta description)',
    url: 'https://yourdomain.com',
    siteName: 'YourBrand',
    images: [{ url: '/og-default.png', width: 1200, height: 630, alt: 'YourBrand' }],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'YourBrand',
    description: 'Your Twitter card description',
    creator: '@yourhandle',
    images: ['/og-default.png'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  alternates: {
    canonical: '/',
  },
}
```

### Dynamic Page Metadata

```tsx
// app/blog/[slug]/page.tsx
import type { Metadata, ResolvingMetadata } from 'next'

type Props = {
  params: Promise<{ slug: string }>
}

export async function generateMetadata(
  { params }: Props,
  parent: ResolvingMetadata
): Promise<Metadata> {
  const { slug } = await params
  const post = await getPost(slug)

  return {
    title: post.title,  // uses template: "Post Title | YourBrand"
    description: post.excerpt,
    authors: [{ name: post.author.name }],
    openGraph: {
      title: post.title,
      description: post.excerpt,
      type: 'article',
      publishedTime: post.publishedAt,
      modifiedTime: post.updatedAt,
      authors: [post.author.name],
      images: [{ url: post.coverImage, width: 1200, height: 630, alt: post.title }],
    },
    twitter: {
      card: 'summary_large_image',
      title: post.title,
      description: post.excerpt,
      images: [post.coverImage],
    },
    alternates: {
      canonical: `/blog/${slug}`,
    },
  }
}
```

### Noindex Pages (Admin, Dashboard, Search Results)

```tsx
// app/dashboard/layout.tsx
export const metadata: Metadata = {
  robots: {
    index: false,
    follow: false,
  },
}
```

---

## 2. JSON-LD Structured Data <a name="json-ld"></a>

### Reusable JSON-LD Component

```tsx
// components/JsonLd.tsx
interface JsonLdProps {
  data: Record<string, unknown>
}

export function JsonLd({ data }: JsonLdProps) {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{
        __html: JSON.stringify(data).replace(/</g, '\\u003c'),
      }}
    />
  )
}
```

### Usage with Type Safety

```bash
npm install schema-dts
```

```tsx
// app/page.tsx
import { JsonLd } from '@/components/JsonLd'
import type { Organization, WebSite, WithContext } from 'schema-dts'

export default function HomePage() {
  const orgSchema: WithContext<Organization> = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'YourBrand',
    url: 'https://yourdomain.com',
    logo: 'https://yourdomain.com/logo.png',
    description: 'What your company does',
    sameAs: [
      'https://twitter.com/yourhandle',
      'https://linkedin.com/company/yourcompany',
      'https://github.com/yourcompany',
    ],
    contactPoint: {
      '@type': 'ContactPoint',
      email: 'support@yourdomain.com',
      contactType: 'customer support',
    },
  }

  const websiteSchema: WithContext<WebSite> = {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'YourBrand',
    url: 'https://yourdomain.com',
    potentialAction: {
      '@type': 'SearchAction',
      target: {
        '@type': 'EntryPoint',
        urlTemplate: 'https://yourdomain.com/search?q={search_term_string}',
      },
      'query-input': 'required name=search_term_string',
    } as any,
  }

  return (
    <>
      <JsonLd data={orgSchema} />
      <JsonLd data={websiteSchema} />
      {/* Page content */}
    </>
  )
}
```

See `schema-templates.md` for complete JSON-LD templates for every page type.

---

## 3. Sitemap Generation <a name="sitemap"></a>

### Dynamic Sitemap

```ts
// app/sitemap.ts
import type { MetadataRoute } from 'next'

const BASE_URL = 'https://yourdomain.com'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  // Static pages
  const staticPages: MetadataRoute.Sitemap = [
    { url: BASE_URL, lastModified: new Date(), changeFrequency: 'weekly', priority: 1.0 },
    { url: `${BASE_URL}/pricing`, lastModified: new Date(), changeFrequency: 'monthly', priority: 0.9 },
    { url: `${BASE_URL}/about`, lastModified: new Date(), changeFrequency: 'monthly', priority: 0.7 },
    { url: `${BASE_URL}/contact`, lastModified: new Date(), changeFrequency: 'yearly', priority: 0.5 },
  ]

  // Dynamic pages (e.g., blog posts)
  const posts = await getAllPosts()
  const blogPages: MetadataRoute.Sitemap = posts.map((post) => ({
    url: `${BASE_URL}/blog/${post.slug}`,
    lastModified: new Date(post.updatedAt),
    changeFrequency: 'monthly' as const,
    priority: 0.6,
  }))

  return [...staticPages, ...blogPages]
}
```

### Multiple Sitemaps (Large Sites, 50k+ URLs)

```ts
// app/blog/sitemap.ts
import type { MetadataRoute } from 'next'

export async function generateSitemaps() {
  const totalPosts = await getPostCount()
  const sitemapCount = Math.ceil(totalPosts / 50000)
  return Array.from({ length: sitemapCount }, (_, i) => ({ id: i }))
}

export default async function sitemap(
  props: { id: Promise<string> }
): Promise<MetadataRoute.Sitemap> {
  const id = Number(await props.id)
  const start = id * 50000
  const posts = await getPosts({ offset: start, limit: 50000 })

  return posts.map((post) => ({
    url: `https://yourdomain.com/blog/${post.slug}`,
    lastModified: new Date(post.updatedAt),
  }))
}
```

---

## 4. robots.txt <a name="robots"></a>

### Dynamic robots.txt with AI Crawler Support

```ts
// app/robots.ts
import type { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: ['/api/', '/admin/', '/dashboard/', '/private/'],
      },
      // Explicitly allow AI crawlers (overrides any blanket blocks)
      { userAgent: 'GPTBot', allow: '/' },
      { userAgent: 'OAI-SearchBot', allow: '/' },
      { userAgent: 'ChatGPT-User', allow: '/' },
      { userAgent: 'ClaudeBot', allow: '/' },
      { userAgent: 'Claude-SearchBot', allow: '/' },
      { userAgent: 'Claude-User', allow: '/' },
      { userAgent: 'PerplexityBot', allow: '/' },
      { userAgent: 'Perplexity-User', allow: '/' },
      { userAgent: 'Google-Extended', allow: '/' },
    ],
    sitemap: 'https://yourdomain.com/sitemap.xml',
  }
}
```

---

## 5. Open Graph & Twitter Cards <a name="og-twitter"></a>

### File-Based OG Images (Static)

Place image files directly in route folders:
```
app/
  opengraph-image.png      → Default OG image (1200x630)
  twitter-image.png         → Default Twitter image
  blog/
    [slug]/
      opengraph-image.tsx   → Dynamic per-post OG image
```

### Per-Page OG Configuration

OG and Twitter metadata do NOT inherit from parent title/description. Always set them explicitly in `generateMetadata` or static `metadata` exports. See the dynamic metadata example in section 1.

---

## 6. Dynamic OG Image Generation <a name="dynamic-og"></a>

```tsx
// app/blog/[slug]/opengraph-image.tsx
import { ImageResponse } from 'next/og'

export const alt = 'Blog post preview'
export const size = { width: 1200, height: 630 }
export const contentType = 'image/png'

export default async function Image({ params }: { params: { slug: string } }) {
  const post = await getPost(params.slug)

  return new ImageResponse(
    (
      <div
        style={{
          height: '100%',
          width: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-start',
          justifyContent: 'center',
          backgroundColor: '#0a0a0a',
          padding: '60px 80px',
        }}
      >
        <div style={{ fontSize: 24, color: '#00d4aa', marginBottom: 16 }}>
          yourdomain.com
        </div>
        <div style={{ fontSize: 56, fontWeight: 700, color: '#ffffff', lineHeight: 1.2 }}>
          {post.title}
        </div>
        <div style={{ fontSize: 24, color: '#a0a0a0', marginTop: 24 }}>
          {post.author.name} · {new Date(post.publishedAt).toLocaleDateString()}
        </div>
      </div>
    ),
    { ...size }
  )
}
```

---

## 7. Core Web Vitals <a name="cwv"></a>

### LCP Optimization

```tsx
// Always use next/image with priority for hero images
import Image from 'next/image'

<Image src="/hero.jpg" alt="Hero" width={1200} height={600} priority sizes="100vw" />
```

```tsx
// Use next/font to eliminate font layout shift
import { Inter, JetBrains_Mono } from 'next/font/google'

const inter = Inter({ subsets: ['latin'], display: 'swap', variable: '--font-sans' })
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], display: 'swap', variable: '--font-mono' })

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body>{children}</body>
    </html>
  )
}
```

### INP Optimization

```tsx
// Lazy-load heavy client components
import dynamic from 'next/dynamic'

const HeavyChart = dynamic(() => import('@/components/HeavyChart'), {
  loading: () => <div className="h-64 animate-pulse bg-gray-100 rounded" />,
  ssr: false,
})
```

### CLS Prevention

```tsx
// Always specify dimensions for media
<Image src="/photo.jpg" alt="..." width={800} height={450} />

// Use aspect-ratio for dynamic containers
<div style={{ aspectRatio: '16/9' }}>{/* video embed */}</div>
```

### Streaming with Suspense

```tsx
import { Suspense } from 'react'

export default function Page() {
  return (
    <main>
      <h1>Dashboard</h1>
      <Suspense fallback={<div className="h-32 animate-pulse" />}>
        <SlowDataComponent />
      </Suspense>
    </main>
  )
}
```

---

## 8. Canonical URLs <a name="canonical"></a>

### Per-Page Canonical

```tsx
// Always set canonical on dynamic routes
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params
  return {
    alternates: {
      canonical: `/blog/${slug}`,  // resolved against metadataBase
    },
  }
}
```

### Canonical with Language Alternates

```tsx
export const metadata: Metadata = {
  alternates: {
    canonical: '/pricing',
    languages: {
      'en-US': '/en/pricing',
      'de-DE': '/de/pricing',
      'x-default': '/en/pricing',
    },
  },
}
```

---

## 9. International SEO <a name="i18n"></a>

### Folder Structure

```
app/
  [locale]/
    layout.tsx
    page.tsx
    blog/[slug]/page.tsx
middleware.ts
```

### Middleware for Locale Detection

```ts
// middleware.ts
import { NextRequest, NextResponse } from 'next/server'

const locales = ['en', 'de', 'es']
const defaultLocale = 'en'

function getLocale(request: NextRequest): string {
  const acceptLanguage = request.headers.get('accept-language') || ''
  for (const locale of locales) {
    if (acceptLanguage.includes(locale)) return locale
  }
  return defaultLocale
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const pathnameHasLocale = locales.some(
    (locale) => pathname.startsWith(`/${locale}/`) || pathname === `/${locale}`
  )
  if (pathnameHasLocale) return

  const locale = getLocale(request)
  request.nextUrl.pathname = `/${locale}${pathname}`
  return NextResponse.redirect(request.nextUrl)
}

export const config = {
  matcher: ['/((?!_next|api|favicon.ico|icons|images).*)'],
}
```

### Localized Sitemap with hreflang

```ts
// app/sitemap.ts
import type { MetadataRoute } from 'next'

const BASE_URL = 'https://yourdomain.com'
const locales = ['en', 'de', 'es']

export default function sitemap(): MetadataRoute.Sitemap {
  const routes = ['', '/pricing', '/about', '/blog']

  return routes.flatMap((route) =>
    locales.map((locale) => ({
      url: `${BASE_URL}/${locale}${route}`,
      lastModified: new Date(),
      alternates: {
        languages: Object.fromEntries(
          locales.map((l) => [l, `${BASE_URL}/${l}${route}`])
        ),
      },
    }))
  )
}
```

### Per-Page hreflang Metadata

```tsx
// app/[locale]/page.tsx
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params
  return {
    alternates: {
      canonical: `https://yourdomain.com/${locale}`,
      languages: {
        en: 'https://yourdomain.com/en',
        de: 'https://yourdomain.com/de',
        es: 'https://yourdomain.com/es',
        'x-default': 'https://yourdomain.com/en',
      },
    },
  }
}
```
