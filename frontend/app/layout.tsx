import '@/app/globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Research Paper → Jupyter Notebook',
  description: 'Convert research papers into executable Jupyter notebooks',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-arc-dark text-arc-light">{children}</body>
    </html>
  )
}
