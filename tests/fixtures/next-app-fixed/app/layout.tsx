import type { Metadata } from 'next'

export const metadata: Metadata = {
  metadataBase: new URL('https://yourbrand.com'),
  title: {
    default: 'YourBrand -- Scheduling Software for Clinics',
    template: '%s | YourBrand',
  },
  description: 'Appointment scheduling for independent clinics: online booking, text reminders and a waitlist that refills cancelled slots.',
  openGraph: { type: 'website', siteName: 'YourBrand', url: './' },
  twitter: { card: 'summary_large_image' },
  alternates: { canonical: './' },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
