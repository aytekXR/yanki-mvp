import type { Metadata } from 'next'
import type { ReactNode } from 'react'
import './globals.css'

export const metadata: Metadata = {
  title: 'Yanki — how AI answers talk about your brand',
  description: 'See how AI answers talk about your brand.',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-surface-muted font-sans text-surface-foreground antialiased">
        {children}
      </body>
    </html>
  )
}
