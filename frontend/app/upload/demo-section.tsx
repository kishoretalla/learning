'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { saveApiKey, CSRF_HEADER } from '@/lib/session'

interface DemoPaper {
  id: string
  title: string
  description: string
  topic: string
  year: number
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function DemoSection({ apiKey }: { apiKey: string }) {
  const router = useRouter()
  const [papers, setPapers] = useState<DemoPaper[]>([])
  const [loading, setLoading] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${API_URL}/api/demo-papers`)
      .then(r => r.json())
      .then(setPapers)
      .catch(() => {/* backend not running — silently hide section */})
  }, [])

  if (papers.length === 0) return null

  const handleTry = async (paper: DemoPaper) => {
    if (!apiKey.trim()) {
      setError('Enter your Gemini API key first.')
      return
    }
    setError(null)
    setLoading(paper.id)
    try {
      const res = await fetch(`${API_URL}/api/demo-papers/${paper.id}/extract`, {
        method: 'POST',
        headers: CSRF_HEADER,
      })
      if (!res.ok) throw new Error('Failed to load demo paper.')
      const data = await res.json()
      sessionStorage.setItem('extraction_result', JSON.stringify(data))
      saveApiKey(apiKey)
      router.push('/processing')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load demo paper.')
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="space-y-3" data-testid="demo-section">
      <div className="flex items-center gap-3">
        <div className="flex-1 h-px bg-arc-purple/10" />
        <span className="text-xs text-arc-light opacity-40 shrink-0">or try a demo paper</span>
        <div className="flex-1 h-px bg-arc-purple/10" />
      </div>

      {error && (
        <p className="text-red-400 text-xs text-center" data-testid="demo-error">{error}</p>
      )}

      <div className="grid gap-3">
        {papers.map(paper => (
          <div
            key={paper.id}
            data-testid={`demo-paper-${paper.id}`}
            className="flex items-start justify-between gap-4 p-4 rounded-lg bg-arc-gray/20 border border-arc-purple/10 hover:border-arc-purple/30 transition-colors"
          >
            <div className="space-y-1 min-w-0">
              <p className="text-arc-light font-medium text-sm leading-tight">{paper.title}</p>
              <p className="text-arc-light opacity-50 text-xs leading-snug">{paper.description}</p>
              <span className="inline-block text-xs text-arc-purple opacity-70">{paper.topic} · {paper.year}</span>
            </div>
            <button
              type="button"
              onClick={() => handleTry(paper)}
              disabled={loading === paper.id}
              data-testid={`try-demo-${paper.id}`}
              className="shrink-0 px-3 py-1.5 text-xs font-semibold bg-arc-purple/20 hover:bg-arc-purple/30 text-arc-purple rounded-md transition-colors disabled:opacity-50"
            >
              {loading === paper.id ? '...' : 'Try →'}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
