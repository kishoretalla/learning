'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { loadApiKey, clearSession, CSRF_HEADER } from '@/lib/session'

type StepStatus = 'pending' | 'running' | 'done' | 'error'

interface Step {
  id: string
  label: string
  status: StepStatus
}

type Stage = 'running' | 'complete' | 'error' | 'no-data'
type ColabStatus = 'idle' | 'loading' | 'ready' | 'unavailable'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const INITIAL_STEPS: Step[] = [
  { id: 'extract',  label: 'Text extracted from PDF',  status: 'done'    },
  { id: 'analyze',  label: 'Analyzing paper with Gemini', status: 'pending' },
  { id: 'generate', label: 'Generating Jupyter notebook',  status: 'pending' },
]

export default function ProcessingPage() {
  const [steps, setSteps] = useState<Step[]>(INITIAL_STEPS)
  const [stage, setStage] = useState<Stage>('running')
  const [errorMsg, setErrorMsg] = useState('')
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
  const [downloadName, setDownloadName] = useState('notebook.ipynb')
  const [colabStatus, setColabStatus] = useState<ColabStatus>('idle')
  const [colabUrl, setColabUrl] = useState<string | null>(null)
  const [mdUrl, setMdUrl] = useState<string | null>(null)
  const [mdName, setMdName] = useState('notebook.md')
  const ranRef = useRef(false)

  const setStepStatus = (id: string, status: StepStatus) =>
    setSteps(prev => prev.map(s => (s.id === id ? { ...s, status } : s)))

  const runPipeline = async () => {
    const extractionRaw = sessionStorage.getItem('extraction_result')
    const apiKey = loadApiKey()

    if (!extractionRaw || !apiKey) {
      setStage('no-data')
      return
    }

    const extraction = JSON.parse(extractionRaw)
    const fullText = (extraction.pages as { text: string }[])
      .map(p => p.text)
      .join('\n\n')
    const filename: string = extraction.filename || 'paper.pdf'

    // ── Step 2: Analyze ──────────────────────────────────────────────────────
    setStepStatus('analyze', 'running')
    let analysis: Record<string, unknown>
    try {
      const res = await fetch(`${API_URL}/api/analyze-paper`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...CSRF_HEADER },
        body: JSON.stringify({ text: fullText, api_key: apiKey, filename }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || res.statusText)
      }
      analysis = await res.json()
      setStepStatus('analyze', 'done')
      sessionStorage.setItem('analysis_result', JSON.stringify(analysis))

      // Kick off Markdown export in parallel with notebook generation
      fetch(`${API_URL}/api/export-markdown`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...CSRF_HEADER },
        body: JSON.stringify({ ...analysis, filename }),
      }).then(async r => {
        if (!r.ok) return
        const blob = await r.blob()
        const cd = r.headers.get('content-disposition') || ''
        const match = cd.match(/filename="?([^"]+)"?/)
        setMdUrl(URL.createObjectURL(blob))
        setMdName(match?.[1] ?? filename.replace('.pdf', '-notebook.md'))
      }).catch(() => {/* non-critical */})
    } catch (e) {
      setStepStatus('analyze', 'error')
      setErrorMsg(e instanceof Error ? e.message : 'Analysis failed.')
      setStage('error')
      return
    }

    // ── Step 3: Generate ─────────────────────────────────────────────────────
    setStepStatus('generate', 'running')
    try {
      const res = await fetch(`${API_URL}/api/generate-notebook`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...CSRF_HEADER },
        body: JSON.stringify({ ...analysis, filename }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || res.statusText)
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const cd = res.headers.get('content-disposition') || ''
      const match = cd.match(/filename="?([^"]+)"?/)
      const name = match?.[1] ?? `${filename.replace('.pdf', '')}-notebook.ipynb`

      setDownloadUrl(url)
      setDownloadName(name)
      setStepStatus('generate', 'done')
      setStage('complete')

      // Attempt Colab link (non-blocking — failure doesn't affect download)
      setColabStatus('loading')
      try {
        const notebookText = await blob.text()
        const colabRes = await fetch(`${API_URL}/api/create-colab-link`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...CSRF_HEADER },
          body: JSON.stringify({ notebook_json: notebookText, filename: name }),
        })
        if (colabRes.ok) {
          const data = await colabRes.json()
          if (data.available) {
            setColabUrl(data.colab_url)
            setColabStatus('ready')
          } else {
            setColabStatus('unavailable')
          }
        } else {
          setColabStatus('unavailable')
        }
      } catch {
        setColabStatus('unavailable')
      }
    } catch (e) {
      setStepStatus('generate', 'error')
      setErrorMsg(e instanceof Error ? e.message : 'Notebook generation failed.')
      setStage('error')
    }
  }

  useEffect(() => {
    if (ranRef.current) return
    ranRef.current = true
    runPipeline()
  }, [])

  const handleRetry = () => {
    ranRef.current = false
    setSteps(INITIAL_STEPS)
    setStage('running')
    setErrorMsg('')
    setDownloadUrl(null)
    ranRef.current = true
    runPipeline()
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-arc-dark via-arc-gray to-arc-dark flex flex-col items-center justify-center p-4 sm:p-6 md:p-8">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-arc-purple opacity-5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/4 left-1/4 w-96 h-96 bg-arc-accent opacity-5 rounded-full blur-3xl"></div>
      </div>

      <div className="relative z-10 w-full max-w-lg mx-auto space-y-8">

        {/* No data */}
        {stage === 'no-data' && (
          <div className="text-center space-y-4" data-testid="no-data-state">
            <div className="text-5xl">📭</div>
            <h1 className="text-2xl font-bold text-arc-light">No paper found</h1>
            <p className="text-arc-light opacity-60 text-sm">
              Please upload a PDF first.
            </p>
            <Link
              href="/upload"
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-arc-purple to-arc-accent text-white font-bold rounded-lg hover:shadow-lg hover:shadow-arc-purple/50 transition-all"
            >
              Upload a paper
            </Link>
          </div>
        )}

        {/* Running / error / complete — all share the step list */}
        {stage !== 'no-data' && (
          <>
            <div className="text-center space-y-2">
              {stage === 'running' && (
                <>
                  <div className="text-4xl animate-spin inline-block">⚙️</div>
                  <h1 className="text-2xl font-bold text-arc-light" data-testid="processing-title">
                    Processing your paper...
                  </h1>
                </>
              )}
              {stage === 'complete' && (
                <>
                  <div className="text-4xl">✅</div>
                  <h1 className="text-2xl font-bold text-arc-light" data-testid="complete-title">
                    Notebook ready!
                  </h1>
                </>
              )}
              {stage === 'error' && (
                <>
                  <div className="text-4xl">❌</div>
                  <h1 className="text-2xl font-bold text-arc-light" data-testid="error-title">
                    Something went wrong
                  </h1>
                </>
              )}
            </div>

            {/* Step list */}
            <div className="space-y-3" data-testid="step-list">
              {steps.map(step => (
                <div
                  key={step.id}
                  data-testid={`step-${step.id}`}
                  className="flex items-center gap-4 p-4 rounded-lg bg-arc-gray/30 border border-arc-purple/10"
                >
                  <StepIcon status={step.status} />
                  <span
                    className={[
                      'text-sm font-medium',
                      step.status === 'done'    ? 'text-arc-light'          : '',
                      step.status === 'running' ? 'text-arc-purple'         : '',
                      step.status === 'pending' ? 'text-arc-light opacity-40' : '',
                      step.status === 'error'   ? 'text-red-400'            : '',
                    ].join(' ')}
                  >
                    {step.label}
                  </span>
                </div>
              ))}
            </div>

            {/* Error message + actions */}
            {stage === 'error' && (
              <div className="space-y-4">
                <div
                  data-testid="error-message"
                  className="p-4 bg-red-900/20 border border-red-500/30 rounded-lg text-red-400 text-sm"
                >
                  {errorMsg}
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={handleRetry}
                    data-testid="retry-button"
                    className="flex-1 px-6 py-3 bg-gradient-to-r from-arc-purple to-arc-accent text-white font-bold rounded-lg hover:shadow-lg hover:shadow-arc-purple/50 transition-all"
                  >
                    Retry
                  </button>
                  <Link
                    href="/upload"
                    className="flex-1 text-center px-6 py-3 border-2 border-arc-purple/50 text-arc-light font-semibold rounded-lg hover:border-arc-purple transition-all"
                  >
                    Upload again
                  </Link>
                </div>
              </div>
            )}

            {/* Success actions */}
            {stage === 'complete' && downloadUrl && (
              <div className="space-y-4" data-testid="success-actions">
                <a
                  href={downloadUrl}
                  download={downloadName}
                  data-testid="download-button"
                  className="flex items-center justify-center gap-2 w-full px-8 py-4 bg-gradient-to-r from-arc-purple to-arc-accent text-white font-bold rounded-lg hover:shadow-lg hover:shadow-arc-purple/50 transform hover:scale-[1.01] transition-all"
                >
                  Download Notebook
                  <span>↓</span>
                </a>
                {mdUrl && (
                  <a
                    href={mdUrl}
                    download={mdName}
                    data-testid="markdown-download-button"
                    className="flex items-center justify-center gap-2 w-full px-8 py-3 border-2 border-arc-purple/40 text-arc-light font-semibold rounded-lg hover:border-arc-purple transition-all text-sm"
                  >
                    Download as Markdown (.md)
                  </a>
                )}
                <ColabButton status={colabStatus} url={colabUrl} />
                <Link
                  href="/upload"
                  className="block text-center text-arc-light opacity-50 hover:opacity-100 transition-opacity text-sm"
                >
                  Convert another paper
                </Link>
              </div>
            )}
          </>
        )}
      </div>
    </main>
  )
}

function StepIcon({ status }: { status: StepStatus }) {
  if (status === 'done')    return <span className="text-green-400 text-lg w-6 shrink-0">✓</span>
  if (status === 'running') return <span className="text-arc-purple text-lg w-6 shrink-0 animate-pulse">●</span>
  if (status === 'error')   return <span className="text-red-400 text-lg w-6 shrink-0">✗</span>
  return <span className="text-arc-light opacity-20 text-lg w-6 shrink-0">○</span>
}

function ColabButton({ status, url }: { status: ColabStatus; url: string | null }) {
  if (status === 'loading') {
    return (
      <div
        data-testid="colab-loading"
        className="flex items-center justify-center gap-2 w-full px-8 py-4 border-2 border-arc-purple/20 text-arc-light/50 font-semibold rounded-lg text-sm"
      >
        <span className="animate-pulse">●</span> Preparing Colab link...
      </div>
    )
  }

  if (status === 'ready' && url) {
    return (
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        data-testid="colab-button"
        className="flex items-center justify-center gap-3 w-full px-8 py-4 bg-[#F9AB00] hover:bg-[#F9AB00]/90 text-[#1a1a1a] font-bold rounded-lg transform hover:scale-[1.01] transition-all"
      >
        {/* Colab badge colours */}
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M16.9 4.8C14.4 2.3 10.6 1.7 7.5 3.3L9 4.8c2-0.8 4.4-0.4 6 1.2 2.2 2.2 2.2 5.8 0 8-1.6 1.6-4 2-6 1.2L7.5 16.7c3.1 1.6 6.9 1 9.4-1.5 3.1-3.1 3.1-8.3 0-11.4zM15 12l-3 3-3-3 3-3 3 3z"/>
        </svg>
        Open in Colab
      </a>
    )
  }

  // unavailable or idle — show helpful fallback
  return (
    <div
      data-testid="colab-unavailable"
      className="w-full px-6 py-4 border border-arc-purple/10 rounded-lg text-arc-light/40 text-xs text-center space-y-1"
    >
      <p className="font-medium text-arc-light/60">Open in Colab manually</p>
      <p>Download the notebook above, then go to <span className="font-mono">colab.research.google.com</span> → File → Upload notebook.</p>
      <p className="opacity-70">To enable auto-links, set <span className="font-mono">GITHUB_TOKEN</span> in your backend.</p>
    </div>
  )
}
