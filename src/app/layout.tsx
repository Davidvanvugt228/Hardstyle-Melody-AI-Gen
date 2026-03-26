import type { Metadata, Viewport } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'RAWGEN — Hardstyle MIDI Generator',
  description: 'AI-powered Hardstyle & Rawstyle MIDI generation. Upload your bassline, get lead, chords, and pads.',
  keywords: ['hardstyle', 'rawstyle', 'MIDI', 'generator', 'music production', 'FL Studio'],
  authors: [{ name: 'RAWGEN' }],
  robots: 'index, follow',
  openGraph: {
    title: 'RAWGEN — Hardstyle MIDI Generator',
    description: 'Upload a bassline. Get professional Hardstyle/Rawstyle MIDI.',
    type: 'website',
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#050508',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="bg-void text-pearl antialiased overflow-x-hidden">
        {/* Ambient scanline */}
        <div className="scanline" aria-hidden="true" />
        {children}
      </body>
    </html>
  )
}
