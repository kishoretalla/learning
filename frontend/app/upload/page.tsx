'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import {
  loadApiKey,
  saveApiKey,
  removeApiKey,
  clearSession,
  isSessionActive,
  sessionExpiresAt,
  CSRF_HEADER,
} from '@/lib/session'
import { DemoSection } from './demo-section'

const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10MB

export default function UploadPage() {
  const router = useRouter()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [apiKey, setApiKey] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [sessionActive, setSessionActive] = useState(false)
  const [expiresAt, setExpiresAt] = useState<Date | null>(null)

  useEffect(() => {
    const saved = loadApiKey()
    if (saved) {
      setApiKey(saved)
      setSessionActive(true)
      setExpiresAt(sessionExpiresAt())
    }
  }, [])

  const handleApiKeyChange = (value: string) => {
    setApiKey(value)
    if (value) {
      saveApiKey(value)
      setSessionActive(true)
      setExpiresAt(sessionExpiresAt())
    } else {
      removeApiKey()
      setSessionActive(false)
      setExpiresAt(null)
    }
  }

  const handleClearSession = () => {
    clearSession()
    setApiKey('')
    setFile(null)
    setError(null)
    setSessionActive(false)
    setExpiresAt(null)
  }

  const validateFile = (f: File): string | null => {
    if (!f.name.toLowerCase().endsWith('.pdf')) return 'Only PDF files are supported.'
    if (f.size > MAX_FILE_SIZE) return `File exceeds 10MB limit (${(f.size / 1024 / 1024).toFixed(1)} MB).`
    return null
  }

  const handleFileSelect = (f: File) => {
    const err = validateFile(f)
    if (err) { setError(err); setFile(null) }
    else      { setError(null); setFile(f) }
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) handleFileSelect(dropped)
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback(() => { setIsDragging(false) }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file || !apiKey.trim()) return

    setIsUploading(true)
    setUploadProgress(0)
    setError(null)

    const progressInterval = setInterval(() => {
      setUploadProgress(prev => Math.min(prev + 12, 90))
    }, 200)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('api_key', apiKey)

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/extract-text`, {
        method: 'POST',
        headers: CSRF_HEADER,
        body: formData,
      })

      clearInterval(progressInterval)
      setUploadProgress(100)

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }

      const data = await response.json()
      sessionStorage.setItem('extraction_result', JSON.stringify(data))
      router.push('/processing')
    } catch (err) {
      clearInterval(progressInterval)
      setUploadProgress(0)
      setError(err instanceof Error ? err.message : 'Upload failed. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }

  const canSubmit = apiKey.trim().length > 0 && file !== null && !isUploading

  return (
    <main className="min-h-screen bg-gradient-to-br from-arc-dark via-arc-gray to-arc-dark flex flex-col items-center justify-center p-4 sm:p-6 md:p-8">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-arc-purple opacity-5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/4 left-1/4 w-96 h-96 bg-arc-accent opacity-5 rounded-full blur-3xl"></div>
      </div>

      <div className="relative z-10 w-full max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-arc-light opacity-60 hover:opacity-100 transition-opacity text-sm"
            data-testid="back-link"
          >
            ← Back
          </Link>

          {sessionActive && (
            <button
              type="button"
              onClick={handleClearSession}
              data-testid="clear-session-button"
              className="text-xs text-arc-accent hover:opacity-80 transition-opacity flex items-center gap-1"
            >
              🗑 Clear session
            </button>
          )}
        </div>

        <div className="space-y-2 mb-8">
          <h1 className="text-3xl sm:text-4xl font-bold text-arc-light" data-testid="page-title">
            Convert Your Paper
          </h1>
          <p className="text-arc-light opacity-60">
            Upload a research paper and your Gemini API key to generate a Jupyter notebook.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* API Key */}
          <div className="space-y-2">
            <label htmlFor="api-key" className="block text-sm font-medium text-arc-light opacity-80">
              Gemini API Key
            </label>
            <input
              id="api-key"
              type="password"
              value={apiKey}
              onChange={e => handleApiKeyChange(e.target.value)}
              placeholder="AIza..."
              data-testid="api-key-input"
              className="w-full px-4 py-3 bg-arc-gray border border-arc-purple/20 rounded-lg text-arc-light placeholder-arc-light/30 focus:outline-none focus:border-arc-purple/60 transition-colors font-mono text-sm"
            />
            <div className="flex items-center justify-between">
              <p className="text-xs text-arc-light opacity-40">
                Stored in your browser session only — never persisted to our servers.
              </p>
              {expiresAt && (
                <p
                  className="text-xs text-arc-light opacity-40 shrink-0 ml-2"
                  data-testid="session-expiry"
                >
                  Expires {expiresAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              )}
            </div>
          </div>

          {/* Drop zone */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-arc-light opacity-80">
              Research Paper (PDF, max 10 MB)
            </label>
            <div
              data-testid="drop-zone"
              onClick={() => fileInputRef.current?.click()}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              className={[
                'relative cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-all duration-200',
                isDragging
                  ? 'border-arc-purple bg-arc-purple/10'
                  : file
                  ? 'border-arc-purple/50 bg-arc-gray/50'
                  : 'border-arc-purple/20 bg-arc-gray/20 hover:border-arc-purple/40 hover:bg-arc-gray/30',
              ].join(' ')}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={e => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                data-testid="file-input"
                className="hidden"
              />
              {file ? (
                <div className="space-y-2">
                  <div className="text-2xl">📄</div>
                  <p className="text-arc-light font-medium text-sm" data-testid="file-name">{file.name}</p>
                  <p className="text-arc-light opacity-40 text-xs">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  <button
                    type="button"
                    onClick={e => { e.stopPropagation(); setFile(null); setError(null) }}
                    data-testid="remove-file"
                    className="text-xs text-arc-accent hover:opacity-80 transition-opacity"
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="text-4xl opacity-40">📂</div>
                  <div>
                    <p className="text-arc-light opacity-70 text-sm font-medium">
                      {isDragging ? 'Drop your PDF here' : 'Drag & drop your PDF here'}
                    </p>
                    <p className="text-arc-light opacity-40 text-xs mt-1">or click to browse</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {error && (
            <div data-testid="error-message" className="flex items-start gap-3 p-4 bg-red-900/20 border border-red-500/30 rounded-lg">
              <span className="text-red-400 text-sm">⚠ {error}</span>
            </div>
          )}

          {isUploading && (
            <div className="space-y-2" data-testid="upload-progress">
              <div className="flex justify-between text-xs text-arc-light opacity-60">
                <span>Uploading...</span>
                <span data-testid="progress-value">{uploadProgress}%</span>
              </div>
              <div className="h-1.5 bg-arc-gray rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-arc-purple to-arc-accent rounded-full transition-all duration-200"
                  style={{ width: `${uploadProgress}%` }}
                  data-testid="progress-bar"
                />
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={!canSubmit}
            data-testid="submit-button"
            className="w-full px-8 py-4 bg-gradient-to-r from-arc-purple to-arc-accent text-white font-bold rounded-lg hover:shadow-lg hover:shadow-arc-purple/50 transform hover:scale-[1.01] transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
          >
            {isUploading ? 'Processing...' : 'Generate Notebook →'}
          </button>
        </form>

        <DemoSection apiKey={apiKey} />
      </div>
    </main>
  )
}
