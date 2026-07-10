import type { Metadata } from 'next'
import type { ReactNode } from 'react'
import Link from 'next/link'
import { Sora, IBM_Plex_Mono } from 'next/font/google'
import './globals.css'

// Brandkit v2 §3 webfonts, self-hosted by next/font at build (no runtime CDN,
// no <link> tags). Exposed as CSS variables that tailwind fontFamily consumes.
const sora = Sora({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600'],
  variable: '--font-sans',
  display: 'swap',
})

const plexMono = IBM_Plex_Mono({
  subsets: ['latin'],
  weight: ['400', '500'],
  variable: '--font-mono',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Yanki — how AI answers talk about your brand',
  description: 'See how AI answers talk about your brand.',
  manifest: '/manifest.webmanifest',
  icons: {
    icon: [
      { url: '/yanki-favicon.svg', type: 'image/svg+xml' },
      { url: '/favicon-32.png', sizes: '32x32', type: 'image/png' },
    ],
    apple: [{ url: '/apple-touch-180.png', sizes: '180x180', type: 'image/png' }],
  },
}

// Slim, additive site header rendered on every page above the routed content.
// Brand rules from brandkit v2: surface (white) bar, surface-border bottom
// hairline, one accent. Nav targets are >=40px tall with visible focus rings.
function SiteHeader() {
  return (
    <header className="border-b border-surface-border bg-surface">
      <div className="mx-auto flex max-w-4xl items-center justify-between gap-4 px-4 py-3 sm:px-8">
        <Link
          href="/"
          className="inline-flex items-center rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        >
          {/* Plain img: byte-identical brand SVG, no next/image loader needed. */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/yanki-logo-horizontal.svg"
            alt="Yanki"
            width={125}
            height={32}
            className="h-8 w-auto"
          />
        </Link>
        <nav aria-label="Primary" className="flex items-center gap-1 sm:gap-2">
          <Link
            href="/checker"
            className="inline-flex min-h-[40px] items-center rounded px-2 text-sm font-medium text-surface-subtle hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            Free checker
          </Link>
          <Link
            href="/methodology"
            className="inline-flex min-h-[40px] items-center rounded px-2 text-sm font-medium text-surface-subtle hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            Methodology
          </Link>
        </nav>
      </div>
    </header>
  )
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${sora.variable} ${plexMono.variable}`}>
      <body className="min-h-screen bg-surface-muted font-sans text-surface-foreground antialiased">
        <SiteHeader />
        {children}
      </body>
    </html>
  )
}
