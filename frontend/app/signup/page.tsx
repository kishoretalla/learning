'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { saveAuthUser, CSRF_HEADER } from '@/lib/session'

interface SignupResponse {
  id: number
  email: string
  full_name?: string
  created_at: string
}

export default function SignupPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const validateForm = (): string | null => {
    if (!email.trim()) return 'Email is required'
    if (!password.trim()) return 'Password is required'
    if (password.length < 8) return 'Password must be at least 8 characters'
    if (password !== confirmPassword) return 'Passwords do not match'
    return null
  }

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    const validationError = validateForm()
    if (validationError) {
      setError(validationError)
      return
    }

    setIsLoading(true)

    try {
      const response = await fetch('/api/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...CSRF_HEADER,
        },
        body: JSON.stringify({
          email,
          password,
          full_name: fullName || undefined,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        const errorMessage = errorData.detail || `Signup failed (${response.status})`
        setError(errorMessage)
        return
      }

      const userData: SignupResponse = await response.json()
      saveAuthUser({
        id: userData.id,
        email: userData.email,
        full_name: userData.full_name,
      })

      // Redirect to login page (need to log in to get session cookie)
      router.push('/login?from=signup')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An unexpected error occurred'
      setError(`Signup error: ${message}`)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-arc-dark via-arc-gray to-arc-dark flex flex-col items-center justify-center p-4">
      {/* Background effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-arc-purple opacity-5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/4 left-1/4 w-96 h-96 bg-arc-accent opacity-5 rounded-full blur-3xl"></div>
      </div>

      {/* Form container */}
      <div className="relative z-10 w-full max-w-md">
        <div className="bg-arc-gray/40 backdrop-blur border border-arc-purple/30 rounded-xl p-8 space-y-6">
          {/* Header */}
          <div className="text-center space-y-2">
            <h1 className="text-3xl font-bold text-arc-light">Create Account</h1>
            <p className="text-arc-light/60">Join us to save your analyses</p>
          </div>

          {/* Error message */}
          {error && (
            <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3 text-red-200 text-sm">
              {error}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSignup} className="space-y-4">
            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-arc-light mb-2">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full px-4 py-2 bg-arc-dark/50 border border-arc-purple/30 rounded-lg text-arc-light placeholder-arc-light/40 focus:outline-none focus:border-arc-purple focus:ring-1 focus:ring-arc-purple/50 transition"
                disabled={isLoading}
              />
            </div>

            {/* Full Name */}
            <div>
              <label className="block text-sm font-medium text-arc-light mb-2">
                Full Name <span className="text-arc-light/50">(optional)</span>
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="John Doe"
                className="w-full px-4 py-2 bg-arc-dark/50 border border-arc-purple/30 rounded-lg text-arc-light placeholder-arc-light/40 focus:outline-none focus:border-arc-purple focus:ring-1 focus:ring-arc-purple/50 transition"
                disabled={isLoading}
              />
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-arc-light mb-2">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-4 py-2 bg-arc-dark/50 border border-arc-purple/30 rounded-lg text-arc-light placeholder-arc-light/40 focus:outline-none focus:border-arc-purple focus:ring-1 focus:ring-arc-purple/50 transition"
                disabled={isLoading}
              />
              <p className="text-xs text-arc-light/50 mt-1">Minimum 8 characters</p>
            </div>

            {/* Confirm Password */}
            <div>
              <label className="block text-sm font-medium text-arc-light mb-2">
                Confirm Password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-4 py-2 bg-arc-dark/50 border border-arc-purple/30 rounded-lg text-arc-light placeholder-arc-light/40 focus:outline-none focus:border-arc-purple focus:ring-1 focus:ring-arc-purple/50 transition"
                disabled={isLoading}
              />
            </div>

            {/* Submit button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 mt-6 bg-gradient-to-r from-arc-purple to-arc-accent text-white font-semibold rounded-lg hover:shadow-lg hover:shadow-arc-purple/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isLoading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          {/* Footer */}
          <div className="flex items-center justify-center gap-2">
            <span className="text-arc-light/60 text-sm">Already have an account?</span>
            <Link
              href="/login"
              className="text-arc-accent font-semibold hover:text-arc-purple transition"
            >
              Sign in
            </Link>
          </div>
        </div>

        {/* Back to home */}
        <div className="mt-6 text-center">
          <Link
            href="/"
            className="text-arc-light/50 hover:text-arc-light transition text-sm"
          >
            ← Back to home
          </Link>
        </div>
      </div>
    </main>
  )
}
