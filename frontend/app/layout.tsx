import type { Metadata } from 'next'
import type { ReactNode } from 'react'
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
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${sora.variable} ${plexMono.variable}`}>
      <body className="min-h-screen bg-surface-muted font-sans text-surface-foreground antialiased">
        {children}
      </body>
    </html>
  )
}
