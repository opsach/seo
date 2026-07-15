# JSON-LD Schema Templates

Copy-paste templates for common page types. All use JSON-LD format with `schema-dts` types. Replace placeholder values with actual data.

Install type safety: `npm install schema-dts`

## Table of Contents
1. [Organization (Homepage)](#organization)
2. [WebSite with SearchAction](#website)
3. [SoftwareApplication (SaaS Product)](#software)
4. [Product with Pricing](#product)
5. [Article / BlogPosting](#article)
6. [FAQPage](#faq)
7. [BreadcrumbList](#breadcrumb)
8. [Person (Author)](#person)
9. [HowTo (Tutorial)](#howto)
10. [LocalBusiness (Local Clients)](#localbusiness)
11. [Combining Multiple Schemas](#combining)

---

## 1. Organization <a name="organization"></a>

Use on: Homepage, About page, or root layout.

```tsx
import type { Organization, WithContext } from 'schema-dts'

const organizationSchema: WithContext<Organization> = {
  '@context': 'https://schema.org',
  '@type': 'Organization',
  name: 'YourBrand',
  url: 'https://yourdomain.com',
  logo: 'https://yourdomain.com/logo.png',
  description: 'One or two sentences describing what your company does.',
  foundingDate: '2022',
  sameAs: [
    'https://twitter.com/yourhandle',
    'https://linkedin.com/company/yourcompany',
    'https://github.com/yourcompany',
  ],
  contactPoint: {
    '@type': 'ContactPoint',
    email: 'support@yourdomain.com',
    contactType: 'customer support',
    availableLanguage: ['English'],
  },
}
```

---

## 2. WebSite with SearchAction <a name="website"></a>

Use on: Homepage. Enables sitelinks search box in Google.

```tsx
import type { WebSite, WithContext } from 'schema-dts'

const websiteSchema: WithContext<WebSite> = {
  '@context': 'https://schema.org',
  '@type': 'WebSite',
  name: 'YourBrand',
  url: 'https://yourdomain.com',
  description: 'Brief description of your website.',
  potentialAction: {
    '@type': 'SearchAction',
    target: {
      '@type': 'EntryPoint',
      urlTemplate: 'https://yourdomain.com/search?q={search_term_string}',
    },
    'query-input': 'required name=search_term_string',
  } as any,
}
```

---

## 3. SoftwareApplication (SaaS Product) <a name="software"></a>

Use on: Product pages, feature pages for SaaS products.

```tsx
import type { SoftwareApplication, WithContext } from 'schema-dts'

const softwareSchema: WithContext<SoftwareApplication> = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'YourProduct',
  url: 'https://yourdomain.com/product',
  description: 'What your software does in 1-2 sentences.',
  applicationCategory: 'BusinessApplication',  // or DeveloperApplication, DesignApplication, etc.
  operatingSystem: 'Web',
  offers: {
    '@type': 'AggregateOffer',
    priceCurrency: 'USD',
    lowPrice: '0',       // Free tier
    highPrice: '299',     // Highest tier
    offerCount: '3',      // Number of plans
  },
  // WARNING: only include aggregateRating if you have REAL reviews that are
  // visible on the page. Fabricated or off-page rating markup violates
  // Google's structured data policies and can trigger a manual action.
  aggregateRating: {
    '@type': 'AggregateRating',
    ratingValue: '4.8',   // must match ratings shown on the page
    ratingCount: '150',
    bestRating: '5',
    worstRating: '1',
  },
  author: {
    '@type': 'Organization',
    name: 'YourBrand',
    url: 'https://yourdomain.com',
  },
  screenshot: 'https://yourdomain.com/product-screenshot.png',
  featureList: [
    'Feature one description',
    'Feature two description',
    'Feature three description',
  ],
}
```

---

## 4. Product with Pricing <a name="product"></a>

Use on: Pricing pages. Create one Product per plan.

```tsx
import type { Product, WithContext } from 'schema-dts'

const pricingSchema: WithContext<Product> = {
  '@context': 'https://schema.org',
  '@type': 'Product',
  name: 'YourProduct Pro Plan',
  description: 'Professional plan with advanced features.',
  brand: {
    '@type': 'Brand',
    name: 'YourBrand',
  },
  offers: {
    '@type': 'Offer',
    url: 'https://yourdomain.com/pricing',
    priceCurrency: 'USD',
    price: '49',
    priceValidUntil: '2026-12-31',
    availability: 'https://schema.org/InStock',
    itemCondition: 'https://schema.org/NewCondition',
  },
}
```

---

## 5. Article / BlogPosting <a name="article"></a>

Use on: Blog posts, guides, thought leadership content.

```tsx
import type { BlogPosting, WithContext } from 'schema-dts'

function createArticleSchema(post: {
  title: string
  description: string
  slug: string
  author: { name: string; url: string }
  publishedAt: string
  updatedAt: string
  coverImage: string
  tags: string[]
}): WithContext<BlogPosting> {
  return {
    '@context': 'https://schema.org',
    '@type': 'BlogPosting',
    headline: post.title,
    description: post.description,
    url: `https://yourdomain.com/blog/${post.slug}`,
    image: post.coverImage,
    datePublished: post.publishedAt,
    dateModified: post.updatedAt,
    author: {
      '@type': 'Person',
      name: post.author.name,
      url: post.author.url,
    },
    publisher: {
      '@type': 'Organization',
      name: 'YourBrand',
      logo: {
        '@type': 'ImageObject',
        url: 'https://yourdomain.com/logo.png',
      },
    },
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': `https://yourdomain.com/blog/${post.slug}`,
    },
    keywords: post.tags.join(', '),
  }
}
```

---

## 6. FAQPage <a name="faq"></a>

Use on: FAQ pages, pricing pages with FAQ sections, any page with Q&A content.

> **Expectation note:** Google removed FAQ rich results for most sites in 2023
> (now limited to well-known government/health sites). Implement FAQPage for
> **GEO/AI extractability and content structure**, not for Google rich snippets.

```tsx
import type { FAQPage, WithContext } from 'schema-dts'

function createFAQSchema(
  faqs: Array<{ question: string; answer: string }>
): WithContext<FAQPage> {
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faqs.map((faq) => ({
      '@type': 'Question' as const,
      name: faq.question,
      acceptedAnswer: {
        '@type': 'Answer' as const,
        text: faq.answer,
      },
    })),
  }
}

// Usage:
const faqSchema = createFAQSchema([
  {
    question: 'What is YourProduct?',
    answer: 'YourProduct is a cloud-based platform that helps teams...',
  },
  {
    question: 'How much does it cost?',
    answer: 'YourProduct offers a free tier for up to 3 users. Pro plans start at $49/month.',
  },
  {
    question: 'Do you offer a free trial?',
    answer: 'Yes, all paid plans include a 14-day free trial with full access to all features.',
  },
])
```

---

## 7. BreadcrumbList <a name="breadcrumb"></a>

Use on: Any interior page to help search engines understand site hierarchy.

```tsx
import type { BreadcrumbList, WithContext } from 'schema-dts'

function createBreadcrumbSchema(
  items: Array<{ name: string; url: string }>
): WithContext<BreadcrumbList> {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, index) => ({
      '@type': 'ListItem' as const,
      position: index + 1,
      name: item.name,
      item: item.url,
    })),
  }
}

// Usage:
const breadcrumbSchema = createBreadcrumbSchema([
  { name: 'Home', url: 'https://yourdomain.com' },
  { name: 'Blog', url: 'https://yourdomain.com/blog' },
  { name: 'Post Title', url: 'https://yourdomain.com/blog/post-slug' },
])
```

---

## 8. Person (Author) <a name="person"></a>

Use on: Author pages, team pages. Strengthens E-E-A-T signals.

```tsx
import type { Person, WithContext } from 'schema-dts'

const authorSchema: WithContext<Person> = {
  '@context': 'https://schema.org',
  '@type': 'Person',
  name: 'Jane Smith',
  url: 'https://yourdomain.com/team/jane-smith',
  image: 'https://yourdomain.com/team/jane-smith.jpg',
  jobTitle: 'Head of Data Engineering',
  worksFor: {
    '@type': 'Organization',
    name: 'YourBrand',
    url: 'https://yourdomain.com',
  },
  sameAs: [
    'https://linkedin.com/in/janesmith',
    'https://twitter.com/janesmith',
    'https://github.com/janesmith',
  ],
  description: 'Jane is a data engineering leader with 12 years of experience building scalable data platforms.',
}
```

---

## 9. HowTo (Tutorial) <a name="howto"></a>

Use on: Tutorial pages, step-by-step guides, getting-started docs.

> **Expectation note:** Google deprecated HowTo rich results in 2023. HowTo
> markup no longer produces visual snippets in Google Search -- keep it for
> AI/GEO parseability and other consumers, but do not promise clients a
> rich-result appearance from it.

```tsx
import type { HowTo, WithContext } from 'schema-dts'

const howToSchema: WithContext<HowTo> = {
  '@context': 'https://schema.org',
  '@type': 'HowTo',
  name: 'How to Set Up a Data Pipeline with YourProduct',
  description: 'Learn how to create your first data pipeline in under 10 minutes.',
  totalTime: 'PT10M',
  step: [
    {
      '@type': 'HowToStep',
      name: 'Create an account',
      text: 'Sign up at yourdomain.com and complete the onboarding wizard.',
      url: 'https://yourdomain.com/docs/getting-started#step-1',
    },
    {
      '@type': 'HowToStep',
      name: 'Connect your data source',
      text: 'Navigate to Settings > Connections and add your database credentials.',
      url: 'https://yourdomain.com/docs/getting-started#step-2',
    },
    {
      '@type': 'HowToStep',
      name: 'Define your pipeline',
      text: 'Use the visual editor to drag and connect transformation nodes.',
      url: 'https://yourdomain.com/docs/getting-started#step-3',
    },
  ],
}
```

---

## 10. LocalBusiness (Local Clients) <a name="localbusiness"></a>

Use on: Homepage/contact/location pages of local businesses (restaurants, agencies, clinics, shops). This is the highest-impact schema for local SEO and for "best [category] near [city]" AI queries.

```tsx
import type { Restaurant, WithContext } from 'schema-dts'

// Use the most specific subtype available: Restaurant, Dentist, LegalService,
// AutoRepair, etc. Fall back to LocalBusiness if nothing fits.
const localBusinessSchema: WithContext<Restaurant> = {
  '@context': 'https://schema.org',
  '@type': 'Restaurant',
  name: 'Business Name',
  url: 'https://yourdomain.com',
  image: 'https://yourdomain.com/storefront.jpg',
  telephone: '+1-555-555-5555',      // must match the number shown on-page
  priceRange: '$$',
  servesCuisine: 'Italian',           // Restaurant-specific
  address: {
    '@type': 'PostalAddress',
    streetAddress: '123 Main Street',
    addressLocality: 'Austin',
    addressRegion: 'TX',
    postalCode: '78701',
    addressCountry: 'US',
  },
  geo: {
    '@type': 'GeoCoordinates',
    latitude: 30.2672,
    longitude: -97.7431,
  },
  openingHoursSpecification: [
    {
      '@type': 'OpeningHoursSpecification',
      dayOfWeek: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
      opens: '11:00',
      closes: '22:00',
    },
    {
      '@type': 'OpeningHoursSpecification',
      dayOfWeek: ['Saturday', 'Sunday'],
      opens: '10:00',
      closes: '23:00',
    },
  ],
  sameAs: [
    'https://www.google.com/maps/place/...',   // Google Business Profile
    'https://www.yelp.com/biz/...',
    'https://www.facebook.com/...',
    'https://www.instagram.com/...',
  ],
  menu: 'https://yourdomain.com/menu',          // Restaurant-specific
  acceptsReservations: 'https://yourdomain.com/reservations',
}
```

**NAP rule:** Name, Address, Phone in this markup must exactly match the
on-page content, the Google Business Profile, and every directory listing.
Inconsistent NAP is the most common local SEO failure.

---

## 11. Combining Multiple Schemas <a name="combining"></a>

Most pages should have 2-3 schemas. Use the JsonLd component for each:

```tsx
// app/blog/[slug]/page.tsx
import { JsonLd } from '@/components/JsonLd'

export default async function BlogPost({ params }: Props) {
  const post = await getPost(params.slug)

  const articleSchema = createArticleSchema(post)
  const breadcrumbSchema = createBreadcrumbSchema([
    { name: 'Home', url: 'https://yourdomain.com' },
    { name: 'Blog', url: 'https://yourdomain.com/blog' },
    { name: post.title, url: `https://yourdomain.com/blog/${post.slug}` },
  ])

  return (
    <>
      <JsonLd data={articleSchema} />
      <JsonLd data={breadcrumbSchema} />
      <article>{/* content */}</article>
    </>
  )
}
```

### Common Page Type Combinations

| Page | Schema 1 | Schema 2 | Schema 3 |
|------|----------|----------|----------|
| Homepage | Organization | WebSite | -- |
| Local business homepage | LocalBusiness (specific subtype) | WebSite | FAQPage (if FAQ exists) |
| Product page | SoftwareApplication | BreadcrumbList | FAQPage (if FAQ exists) |
| Pricing page | Product (per plan) | FAQPage | BreadcrumbList |
| Blog post | BlogPosting | BreadcrumbList | -- |
| Docs / Tutorial | HowTo or TechArticle | BreadcrumbList | -- |
| Author page | Person | BreadcrumbList | -- |
| FAQ page | FAQPage | BreadcrumbList | -- |
| Comparison page | Product (multiple) | FAQPage | BreadcrumbList |
