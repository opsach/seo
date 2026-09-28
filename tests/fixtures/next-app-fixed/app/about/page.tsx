import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'About the team',
  description: 'Why YourBrand exists: a family clinic lost a day a week to phone tag, and every feature since was asked for by a receptionist.',
}

export default function About() {
  return <main><h1>About YourBrand</h1></main>
}
