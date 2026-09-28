import Image from 'next/image'
import { JsonLd } from '@/components/JsonLd'

export default function Home() {
  return (
    <main>
      <JsonLd
        data={{
          '@context': 'https://schema.org',
          '@graph': [
            { '@type': 'Organization', '@id': 'https://yourbrand.com/#organization', name: 'YourBrand', url: 'https://yourbrand.com/' },
            { '@type': 'WebSite', '@id': 'https://yourbrand.com/#website', name: 'YourBrand', url: 'https://yourbrand.com/' },
          ],
        }}
      />
      <h1>Scheduling software for independent clinics</h1>
      <Image src="/hero.png" alt="Front desk checking the day's bookings" width={1200} height={600} />
    </main>
  )
}
