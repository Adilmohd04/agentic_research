import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import './globals.css'
import Providers from '../components/Providers'

// Force dynamic rendering
export const dynamic = 'force-dynamic'
export const revalidate = 0

const inter = Inter({ 
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter'
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-mono'
})

export const metadata: Metadata = {
  title: 'AI Research Platform - Multi-Agent System',
  description: 'Advanced AI research platform with multi-agent capabilities, voice interaction, and intelligent memory systems',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}