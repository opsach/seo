import type { Metadata } from 'next'
export const metadata: Metadata = { title: 'Blog post' }
export default function Post() {
  return <article><h1>Post</h1></article>
}
