'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
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

export default function AnalysisDetailPage() {
  const router = useRouter()
  const params = useParams()
  const analysisId = params.id as string

  const [analysis, setAnalysis] = useState<AnalysisHistory | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isDownloading, setIsDownloading] = useState(false)

  useEffect(() => {
    // Check authentication
    if (!isUserAuthenticated()) {
      router.push('/login')
      return
    }

    // Fetch analysis details
    const fetchAnalysis = async () => {
      setIsLoading(true)
      try {
        const response = await fetch(`/api/history/${analysisId}`, {
          headers: CSRF_HEADER,
          credentials: 'include',
        })

        if (!response.ok) {
          if (response.status === 401) {
            router.push('/login')
            return
          }
          if (response.status === 403) {
            setError('You do not have access to this analysis')
            return
          }
          if (response.status === 404) {
            setError('Analysis not found')
            return
          }
          throw new Error(`Failed to load analysis (${response.status})`)
        }

        const data = await response.json()
        setAnalysis(data)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load analysis'
        setError(message)
      } finally {
        setIsLoading(false)
      }
    }

    fetchAnalysis()
  }, [analysisId, router])

  const handleDownload = async () => {
    if (!analysis) return

    setIsDownloading(true)
    try {
      // For now, we'd need an endpoint to retrieve/regenerate the notebook
      // This is a placeholder for future implementation
      const link = document.createElement('a')
      link.href = `/api/history/${analysis.id}/download`
      link.download = analysis.notebook_filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download notebook')
    } finally {
      setIsDownloading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-arc-dark via-arc-gray to-arc-dark">
      {/* Background effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-arc-purple opacity-5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/4 left-1/4 w-96 h-96 bg-arc-accent opacity-5 rounded-full blur-3xl"></div>
      </div>

      {/* Header */}
      <div className="relative z-10 border-b border-arc-purple/20 bg-arc-gray/30 backdrop-blur">
        <div className="max-w-4xl mx-auto px-6 py-8">
          <Link
            href="/history"
            className="inline-flex items-center text-arc-light/60 hover:text-arc-light transition mb-4"
          >
            ← Back to analyses
          </Link>
          {analysis && (
            <h1 className="text-3xl font-bold text-arc-light">
              {analysis.title || analysis.filename}
            </h1>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="relative z-10 max-w-4xl mx-auto px-6 py-12">
        {isLoading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-arc-purple"></div>
            <p className="text-arc-light/60 mt-4">Loading analysis...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 text-red-200">
            {error}
          </div>
        )}

        {!isLoading && analysis && (
          <div className="space-y-8">
            {/* Analysis info */}
            <div className="bg-arc-gray/40 backdrop-blur border border-arc-purple/30 rounded-lg p-8 space-y-4">
              <div>
                <label className="text-arc-light/60 text-sm font-medium">Source File</label>
                <p className="text-arc-light text-lg mt-1">{analysis.filename}</p>
              </div>
              <div>
                <label className="text-arc-light/60 text-sm font-medium">Analysis Title</label>
                <p className="text-arc-light text-lg mt-1">
                  {analysis.title || 'Untitled'}
                </p>
              </div>
              <div>
                <label className="text-arc-light/60 text-sm font-medium">Notebook</label>
                <p className="text-arc-light text-lg mt-1 font-mono text-sm">
                  {analysis.notebook_filename}
                </p>
              </div>
              <div>
                <label className="text-arc-light/60 text-sm font-medium">Created</label>
                <p className="text-arc-light text-lg mt-1">
                  {new Date(analysis.created_at).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                  })}
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-4">
              <button
                onClick={handleDownload}
                disabled={isDownloading}
                className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-arc-purple to-arc-accent text-white font-semibold rounded-lg hover:shadow-lg hover:shadow-arc-purple/50 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {isDownloading ? 'Downloading...' : 'Download Notebook'}
                {!isDownloading && <span className="ml-2">↓</span>}
              </button>
              <Link
                href="/upload"
                className="inline-flex items-center px-6 py-3 border border-arc-purple/50 text-arc-light rounded-lg hover:bg-arc-purple/10 transition"
              >
                New Analysis
              </Link>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
