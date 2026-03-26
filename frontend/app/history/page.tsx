'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { isUserAuthenticated, CSRF_HEADER } from '@/lib/session'

interface AnalysisHistory {
  id: number
  user_id: number
  filename: string
  title?: string
  notebook_filename: string
  created_at: string
}

export default function HistoryPage() {
  const router = useRouter()
  const [histories, setHistories] = useState<AnalysisHistory[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Check authentication
    if (!isUserAuthenticated()) {
      router.push('/login')
      return
    }

    // Fetch user's analyses
    const fetchHistories = async () => {
      setIsLoading(true)
      try {
        const response = await fetch('/api/history', {
          headers: CSRF_HEADER,
          credentials: 'include',
        })

        if (!response.ok) {
          if (response.status === 401) {
            router.push('/login')
            return
          }
          throw new Error(`Failed to load history (${response.status})`)
        }

        const data = await response.json()
        setHistories(data)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load history'
        setError(message)
      } finally {
        setIsLoading(false)
      }
    }

    fetchHistories()
  }, [router])

  return (
    <main className="min-h-screen bg-gradient-to-br from-arc-dark via-arc-gray to-arc-dark">
      {/* Background effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-arc-purple opacity-5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/4 left-1/4 w-96 h-96 bg-arc-accent opacity-5 rounded-full blur-3xl"></div>
      </div>

      {/* Header */}
      <div className="relative z-10 border-b border-arc-purple/20 bg-arc-gray/30 backdrop-blur">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-4xl font-bold text-arc-light">Your Analyses</h1>
              <p className="text-arc-light/60 mt-2">Save and review your research paper analyses</p>
            </div>
            <div className="flex gap-3">
              <Link
                href="/upload"
                className="inline-flex items-center px-6 py-2 bg-arc-purple/20 border border-arc-purple/50 text-arc-light rounded-lg hover:bg-arc-purple/30 transition"
              >
                + New Analysis
              </Link>
              <Link
                href="/upload"
                className="inline-flex items-center px-6 py-2 text-arc-light/60 hover:text-arc-light transition"
              >
                ← Back
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="relative z-10 max-w-6xl mx-auto px-6 py-12">
        {isLoading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-arc-purple"></div>
            <p className="text-arc-light/60 mt-4">Loading your analyses...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 text-red-200">
            {error}
          </div>
        )}

        {!isLoading && histories.length === 0 && (
          <div className="text-center py-12">
            <div className="text-5xl mb-4">📚</div>
            <h2 className="text-2xl font-semibold text-arc-light mb-2">No analyses yet</h2>
            <p className="text-arc-light/60 mb-6">
              Upload a research paper to get started
            </p>
            <Link
              href="/upload"
              className="inline-flex items-center px-8 py-3 bg-gradient-to-r from-arc-purple to-arc-accent text-white font-semibold rounded-lg hover:shadow-lg hover:shadow-arc-purple/50 transition"
            >
              Upload Paper
              <span className="ml-2">→</span>
            </Link>
          </div>
        )}

        {!isLoading && histories.length > 0 && (
          <div className="grid gap-4">
            {histories.map((analysis) => (
              <Link
                key={analysis.id}
                href={`/history/${analysis.id}`}
                className="block bg-arc-gray/40 backdrop-blur border border-arc-purple/30 rounded-lg p-6 hover:border-arc-purple/50 hover:bg-arc-gray/60 transition group"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-arc-light group-hover:text-arc-accent transition">
                      {analysis.title || analysis.filename}
                    </h3>
                    <p className="text-arc-light/60 text-sm mt-1">
                      {analysis.filename}
                    </p>
                    <p className="text-arc-light/50 text-xs mt-2">
                      {new Date(analysis.created_at).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  </div>
                  <div className="text-arc-light/40 group-hover:text-arc-accent transition">
                    →
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </main>
  )
}
