import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Autonomous Data Analyst',
  description: 'AI-powered autonomous data analysis system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
