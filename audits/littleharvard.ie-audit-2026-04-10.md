# SEO Audit: www.littleharvard.ie

**Client:** Little Harvard Childcare Ltd
**URL:** https://www.littleharvard.ie/
**Date:** 2026-04-10
**Auditor:** Moolah Media (Automated)

---

## Executive Summary

Little Harvard Crèche, Montessori and Pre-School operates 13+ locations across Dublin, Kildare, and Wicklow, with expansion planned for Spring/Summer 2026. The website serves as the primary digital presence for enrolment inquiries and location discovery.

This audit identified **critical SEO issues** that are likely suppressing organic visibility and costing the business leads. The most urgent problems are: **duplicate content being indexed**, **thin "coming soon" pages diluting crawl budget**, **no content marketing strategy**, and **weak local SEO signals** for a multi-location business.

**Overall SEO Health: Needs Significant Work**

---

## 1. Site Architecture & Indexation

### 1.1 Indexed Pages Discovered

The following pages were confirmed indexed by Google:

| Page | URL | Status |
|---|---|---|
| Homepage | `/` | Active |
| Old Homepage (DUPLICATE) | `/home-2` | **PROBLEM** |
| Locations Hub | `/locations` | Active |
| Contact | `/contact/` | Active |
| About | `/about` | Active |
| Parents | `/parents` | Active |
| Enrolment T&Cs | `/enrolment-terms-and-conditions` | Active |
| NCS Info | `/national-childcare-scheme-ncs` | Active |
| Testimonial Page | `/testimonials/testimonial-8` | Active |
| Bray | `/bray` | Active |
| Greystones | `/greystones` | Active |
| Santry | `/santry` | Active |
| Blanchardstown | `/blanchardstown` | Active |
| Rathfarnham Barton | `/rathfarnham-barton-drive` | Active |
| Leixlip Captains Hill | `/leixlip-captains-hill` | Active |
| Leixlip Beech Park | `/leixlip-beech-park` | Active |
| Leixlip Greenlane | `/greenlane` | Active |
| ECCE Scholarstown | `/ecce-scholarstown` | Active |
| Coming Soon (generic) | `/coming-soon` | **THIN CONTENT** |
| Coming Soon Ghost Posters | `/coming-soon-p` | **THIN CONTENT** |
| Coming Soon Newtown | `/newtown` | **THIN CONTENT** |
| Coming Soon Clondalkin | `/kilcarbery` | **THIN CONTENT** |
| Coming Soon Balbriggan | `/balbriggan` | **THIN CONTENT** |

### 1.2 Critical Indexation Issues

**ISSUE 1: Duplicate Homepage (`/home-2`) — SEVERITY: HIGH**

Google is indexing a page titled "Home old" at `/home-2`. This is a legacy/duplicate version of the homepage. This causes:
- Duplicate content signals to Google
- Diluted link equity (any links pointing to `/home-2` don't benefit the real homepage)
- Confusion in search results

**Action Required:**
- Add a 301 redirect from `/home-2` to `/`
- Alternatively, add `<meta name="robots" content="noindex">` to `/home-2`
- Submit URL removal request via Google Search Console

**ISSUE 2: Five "Coming Soon" Pages Indexed — SEVERITY: HIGH**

At least 5 placeholder "coming soon" pages are indexed. These have minimal content and hurt overall site quality signals:
- `/coming-soon`
- `/coming-soon-p`
- `/newtown`
- `/kilcarbery`
- `/balbriggan`

**Action Required:**
- Add `noindex` meta tag to all coming soon pages immediately
- Only remove `noindex` when the location page has full, real content
- Consider password-protecting or unlisting these pages until ready

**ISSUE 3: URL Consistency — SEVERITY: LOW**

Some URLs use trailing slashes (`/contact/`) and others don't (`/leixlip-captains-hill`). This can create duplicate URL issues if both versions are accessible.

**Action Required:**
- Pick one convention (trailing slash or not) and enforce it site-wide with 301 redirects
- Set canonical URLs on all pages

---

## 2. Title Tags & Meta Descriptions

### 2.1 Title Tag Analysis

From Google's search index, observed title patterns:

| Page | Title in SERP |
|---|---|
| Homepage | "Little Harvard Crèche, Montessori and Pre-School" |
| Contact | "Contact \| Little Harvard Crèche, Montessori and Pre-School" |
| Locations | "Find Your Nearest Location \| Little Harvard Crèche, Montessori and Pre-School" |
| Leixlip | "Leixlip Captains Hill \| Little Harvard Crèche, Montessori and Pre-School" |
| Bray | "Bray Upper Dargle \| Little Harvard Crèche, Montessori and Pre-School" |
| Santry | "Santry Northwood \| Little Harvard Crèche, Montessori and Pre-School" |
| Blanchardstown | "Blanchardstown Ballycoolin - Little Harvard" |
| Parents | "Parents \| Little Harvard Crèche, Montessori and Pre-School" |

### 2.2 Title Tag Issues — SEVERITY: HIGH

1. **Homepage title is generic** — "Little Harvard Crèche, Montessori and Pre-School" contains no geographic or service-differentiating keywords. It should include location context (e.g., "Dublin, Kildare & Wicklow") and a value proposition.

2. **Location pages miss local keywords** — "Leixlip Captains Hill | Little Harvard..." should be "Crèche & Montessori in Leixlip | Captains Hill | Little Harvard" to target local search queries.

3. **Inconsistent separator** — Most pages use ` | ` but Blanchardstown uses ` - `. Should be consistent.

4. **Brand name takes up too much space** — "Little Harvard Crèche, Montessori and Pre-School" is 50+ characters. This leaves little room for unique keywords in the title. Consider shortening to "Little Harvard" at the end.

### 2.3 Recommended Title Tag Rewrites

| Page | Current | Recommended |
|---|---|---|
| Homepage | Little Harvard Crèche, Montessori and Pre-School | Crèche, Montessori & After School \| Dublin, Kildare & Wicklow \| Little Harvard |
| Bray | Bray Upper Dargle \| Little Harvard... | Crèche & Montessori in Bray, Co. Wicklow \| Little Harvard |
| Santry | Santry Northwood \| Little Harvard... | Crèche & Montessori in Santry, Dublin 9 \| Little Harvard |
| Blanchardstown | Blanchardstown Ballycoolin - Little Harvard | Crèche & Montessori in Blanchardstown, Dublin 15 \| Little Harvard |
| Leixlip | Leixlip Captains Hill \| Little Harvard... | Crèche & Montessori in Leixlip, Co. Kildare \| Little Harvard |
| Contact | Contact \| Little Harvard... | Contact Us \| Enquire About Childcare \| Little Harvard |
| Locations | Find Your Nearest Location \| Little Harvard... | 13+ Crèche Locations in Dublin, Kildare & Wicklow \| Little Harvard |

### 2.4 Meta Descriptions

**Unable to directly verify** meta descriptions due to access restrictions. However, based on Google SERP snippets observed:

- The homepage snippet references "locations across Dublin, Kildare and Wicklow with more locations coming soon" and "outstanding childcare in a safe and stimulating learning environment"
- This is decent but could be more action-oriented with a CTA

**Recommended homepage meta description:**
> "Little Harvard operates 13+ crèche, Montessori & after school locations across Dublin, Kildare & Wicklow. ECCE & NCS approved. Book a visit today. ☎ 01 2116350"

---

## 3. Content Analysis

### 3.1 Content Gaps — SEVERITY: HIGH

**No Blog or Resource Section Detected**

This is the single biggest missed opportunity. A blog targeting parent-relevant queries would:
- Drive organic traffic from informational searches
- Build topical authority for childcare-related keywords
- Support location pages with internal links
- Provide content for social media and email marketing

**Recommended blog topics:**
- "How to Choose a Crèche in Dublin: A Parent's Guide"
- "What is the ECCE Scheme? Everything You Need to Know [2026]"
- "NCS Childcare Subsidy: How to Apply and What You'll Save"
- "Montessori vs Traditional Crèche: What's the Difference?"
- "Starting Crèche: How to Prepare Your Child"
- "What to Look for in an After School Programme"
- Location-specific: "Best Childcare Options in Leixlip" / "Childcare in Bray: What Parents Should Know"

### 3.2 Testimonials Structure — SEVERITY: MEDIUM

Testimonials appear to be on individual pages (e.g., `/testimonials/testimonial-8`). This is problematic:
- Individual testimonial pages are thin content
- They fragment social proof instead of consolidating it
- They don't support the pages that need them (location pages)

**Action Required:**
- Embed testimonials directly on location pages and the homepage
- If individual pages exist, `noindex` them
- Add structured data (Schema.org Review markup) to testimonials

### 3.3 Location Page Content

Each location appears to have its own page, which is correct for local SEO. However, location pages likely need:
- Unique, substantial content (200+ words minimum per page)
- Embedded Google Maps
- Specific address with Eircode
- Local phone number (not just the central enquiry line)
- Staff photos or facility photos
- Specific services available at that location
- Opening hours
- Nearby landmarks/transport links
- Parent testimonials specific to that location
- ECCE/NCS availability confirmation

---

## 4. Local SEO

### 4.1 Google Business Profile — SEVERITY: HIGH

With 13+ physical locations, Google Business Profile (GBP) optimisation is critical. Each location needs:

**Checklist per location:**
- [ ] GBP listing claimed and verified
- [ ] Correct NAP (Name, Address, Phone) matching the website exactly
- [ ] Correct business category: "Child Care Agency" / "Montessori School" / "Preschool"
- [ ] Photos uploaded (exterior, interior, staff, activities)
- [ ] Business hours set correctly
- [ ] Services listed (Crèche, Montessori, After School, ECCE, NCS)
- [ ] Website URL pointing to the specific location page (not homepage)
- [ ] Regular Google Posts (events, updates, enrolment deadlines)
- [ ] Review generation strategy in place
- [ ] Q&A section populated proactively

### 4.2 NAP Consistency

Observed business data across directories:
- **Website:** General Enquiries 01 2116350
- **Golden Pages:** Lists locations individually
- **Cybo:** Lists individual locations
- **ESDA Ireland:** Lists as single entity

**Action Required:**
- Audit all directory listings for NAP consistency
- Ensure each location has consistent Name, Address, and Phone across Google, Golden Pages, Yelp, childcare.ie, and all other directories
- Use local phone numbers where available (e.g., 01 624 7514 for Leixlip)

### 4.3 Directory Presence

**Currently listed on:**
- childcare.ie
- ESDA Ireland (esda.ie)
- Golden Pages (goldenpages.ie)
- Cybo
- SoloCheck (company info)
- LinkedIn
- Facebook
- Instagram

**Should also be listed on:**
- Yelp Ireland
- Trustpilot
- Google Maps (per location)
- Boards.ie (Irish forum — community presence)
- Mums & Tots directories
- Local chamber of commerce websites
- County council childcare directories

### 4.4 Schema Markup — SEVERITY: HIGH

**Unable to verify** if structured data exists, but for a multi-location childcare business, the following Schema.org markup is essential:

```json
{
  "@context": "https://schema.org",
  "@type": "ChildCare",
  "name": "Little Harvard Crèche & Montessori - [Location Name]",
  "address": { ... },
  "telephone": "...",
  "openingHours": "...",
  "geo": { "latitude": ..., "longitude": ... },
  "aggregateRating": { ... },
  "review": [ ... ]
}
```

Each location page should have its own `ChildCare` or `LocalBusiness` Schema with:
- Full address with Eircode
- Geographic coordinates
- Opening hours
- Phone number
- Parent organization reference

---

## 5. Technical SEO

### 5.1 Platform

The site appears to be built on **Squarespace** based on:
- URL patterns (`/home-2` duplicate page naming)
- Page structure conventions
- Squarespace-style coming soon pages

**Squarespace SEO Limitations:**
- Limited control over robots.txt customisation
- No native server-side rendering optimisation
- Limited URL redirect management at scale
- No direct access to .htaccess or server configs
- Limited structured data customisation without code injection
- Auto-generated sitemap (limited control)

### 5.2 robots.txt & Sitemap

**Unable to directly verify** due to access restrictions. For Squarespace sites:
- robots.txt is auto-generated — verify it's not blocking important pages
- Sitemap is typically at `/sitemap.xml` — verify it exists and is submitted to Google Search Console
- Ensure coming-soon pages are excluded from sitemap

**Action Required:**
- Verify robots.txt allows crawling of all important pages
- Submit sitemap to Google Search Console
- Remove `/home-2` and coming-soon pages from sitemap

### 5.3 SSL/HTTPS

The site uses HTTPS (confirmed via URL). Verify:
- All internal links use HTTPS (no mixed content)
- HTTP-to-HTTPS redirect is in place
- HSTS headers are configured

### 5.4 Page Speed & Core Web Vitals

**Unable to run PageSpeed Insights directly.** However, Squarespace sites commonly have:
- LCP issues from large hero images (common on childcare sites with photo-heavy designs)
- CLS from lazy-loaded images without dimensions
- High TBT from third-party scripts (analytics, chat widgets, social embeds)

**Recommended actions regardless:**
- Compress all images to WebP format
- Set explicit width/height on all images
- Lazy-load below-the-fold images
- Minimise third-party scripts
- Use Squarespace's built-in image optimisation
- Test at https://pagespeed.web.dev/ and fix flagged items

### 5.5 Mobile Responsiveness

Squarespace templates are generally mobile-responsive. However, verify:
- Text is readable without zooming
- Tap targets (buttons, links) are appropriately sized
- No horizontal scrolling
- Phone number is clickable (tel: link)
- Contact form works on mobile
- Location maps are interactive on mobile

---

## 6. Keyword Strategy

### 6.1 Primary Keywords (Not Currently Targeted Effectively)

| Keyword | Search Intent | Priority |
|---|---|---|
| creche Dublin | Commercial/Local | HIGH |
| montessori Dublin | Commercial/Local | HIGH |
| childcare Dublin | Commercial/Local | HIGH |
| creche near me | Local | HIGH |
| creche Leixlip | Local | HIGH |
| creche Bray | Local | HIGH |
| creche Blanchardstown | Local | HIGH |
| creche Santry | Local | HIGH |
| montessori Leixlip | Local | HIGH |
| after school Dublin | Commercial/Local | MEDIUM |
| ECCE creche Dublin | Informational/Commercial | MEDIUM |
| NCS childcare Dublin | Informational/Commercial | MEDIUM |
| creche Greystones | Local | MEDIUM |
| creche Rathfarnham | Local | MEDIUM |
| best creche Dublin | Commercial | HIGH |
| childcare costs Dublin | Informational | MEDIUM |
| Montessori vs creche | Informational | LOW |

### 6.2 Long-Tail Opportunities

- "creche open 51 weeks Dublin" (USP — most competitors close more)
- "creche with after school service Dublin"
- "ECCE approved creche [location]"
- "NCS registered creche [location]"
- "new creche opening Balbriggan 2026"
- "childcare Hereford Park Leixlip"

---

## 7. Competitive Landscape

### Key Competitors

| Competitor | Strength |
|---|---|
| childcare.ie | Dominant directory, ranks for nearly all "creche + location" queries |
| Cocoon Childcare | 14 centres, strong brand, likely well-optimised |
| Discoveries Crèche | Multiple Dublin locations |
| Kidorama | Dublin-focused competitor |
| Giraffe Childcare | Large national chain, strong SEO |
| heydublin.ie | Aggregator that ranks for "best creche Dublin" lists |
| bestinireland.com | Ranks for "best preschool Dublin" |

### Competitive Advantage to Leverage

- **13+ locations** — network effect for local SEO
- **51 weeks per year** — unusual USP, should be prominent in all copy
- **20+ years in business** — trust signal, should be in Schema and copy
- **ECCE & NCS approved** — should be in title tags and meta descriptions
- **Active expansion** — news-worthy, could generate PR backlinks

---

## 8. Social Media & Off-Page

### 8.1 Social Presence

| Platform | Handle | Notes |
|---|---|---|
| Facebook | @littleharvard | Active page |
| Instagram | @littleharvard_childcare | Active account |
| LinkedIn | Little Harvard Childcare | Company page |
| Twitter/X | Not found | **Missing** |
| YouTube | Not found | **Missing — opportunity for virtual tours** |
| TikTok | Not found | **Missing — parents are on TikTok** |

### 8.2 Backlink Opportunities

- ESDA Ireland listing (confirmed)
- childcare.ie listing (should be claimed/optimised)
- Local press coverage for new location openings
- Parent bloggers / influencer partnerships
- Local community sponsorships (GAA clubs, schools)
- Kildare Now (confirmed coverage of expansion)
- Irish parenting forums and websites

---

## 9. Priority Action Plan

### Immediate (Week 1-2) — Critical Fixes

| # | Action | Impact | Effort |
|---|---|---|---|
| 1 | 301 redirect `/home-2` to `/` | High | Low |
| 2 | Add `noindex` to all 5 coming-soon pages | High | Low |
| 3 | Add `noindex` to individual testimonial pages | Medium | Low |
| 4 | Fix URL trailing slash inconsistency | Medium | Low |
| 5 | Verify sitemap.xml exists and is submitted to Google Search Console | High | Low |
| 6 | Verify robots.txt is not blocking important content | High | Low |

### Short-Term (Month 1) — On-Page Optimisation

| # | Action | Impact | Effort |
|---|---|---|---|
| 7 | Rewrite all title tags per recommendations in Section 2.3 | High | Medium |
| 8 | Write unique meta descriptions for all pages | High | Medium |
| 9 | Add ChildCare/LocalBusiness Schema to every location page | High | Medium |
| 10 | Enrich location pages with unique content (200+ words each) | High | High |
| 11 | Embed testimonials on location pages and homepage | Medium | Medium |
| 12 | Add FAQ Schema for common parent questions on relevant pages | Medium | Medium |

### Medium-Term (Month 2-3) — Local SEO & Content

| # | Action | Impact | Effort |
|---|---|---|---|
| 13 | Audit and optimise all Google Business Profiles (13+ locations) | High | High |
| 14 | Ensure NAP consistency across all directories | High | Medium |
| 15 | Launch blog with 2 posts/month targeting informational keywords | High | Ongoing |
| 16 | Create dedicated service pages (Crèche, Montessori, After School, ECCE, NCS) | High | Medium |
| 17 | Build local citations on missing directories | Medium | Medium |
| 18 | Implement review generation strategy (ask parents for Google reviews) | High | Low |

### Long-Term (Month 3-6) — Growth

| # | Action | Impact | Effort |
|---|---|---|---|
| 19 | Create YouTube channel with virtual tours of each location | Medium | High |
| 20 | PR campaign for new location openings (backlinks from local press) | High | Medium |
| 21 | Parent resource hub (downloadable guides, checklists) | Medium | High |
| 22 | Internal linking strategy connecting blog to location pages | Medium | Low |
| 23 | Monitor Core Web Vitals and fix any issues flagged | Medium | Medium |
| 24 | Explore moving to a more SEO-flexible platform (WordPress) if Squarespace limits are hit | High | Very High |

---

## 10. Monitoring & KPIs

Track these metrics monthly:

| KPI | Tool | Target |
|---|---|---|
| Organic traffic | Google Analytics | +20% in 6 months |
| Keyword rankings (creche + location) | SEMrush/Ahrefs | Top 5 for each location |
| Google Business Profile views | GBP Dashboard | +30% in 3 months |
| Google Business Profile actions (calls, directions) | GBP Dashboard | +25% in 3 months |
| Number of Google reviews per location | GBP Dashboard | 10+ per location |
| Average review rating | GBP Dashboard | 4.5+ stars |
| Pages indexed (clean) | Google Search Console | Remove thin/duplicate pages |
| Core Web Vitals pass rate | Google Search Console | All green |
| Backlinks | Ahrefs/SEMrush | +20 referring domains in 6 months |
| Enquiry form submissions | Google Analytics | Track as conversion |

---

## Limitations of This Audit

Due to network access restrictions, the following could **not** be directly tested:
- Actual page HTML source code (meta tags, Schema markup, canonical tags)
- robots.txt and sitemap.xml content
- PageSpeed Insights / Core Web Vitals scores
- Mobile rendering and usability
- Actual image alt text and heading structure
- Internal link architecture
- JavaScript rendering issues
- 404 error pages
- Redirect chains

**Recommendation:** Run a full technical crawl using Screaming Frog, Ahrefs Site Audit, or SEMrush Site Audit to surface all technical issues not captured here.

---

*Report generated 2026-04-10 | Moolah Media*
