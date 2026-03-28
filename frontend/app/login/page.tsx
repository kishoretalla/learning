'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { saveAuthUser, CSRF_HEADER } from '@/lib/session'

interface LoginResponse {
  access_token: string
  token_type: string
}

interface UserResponse {
  id: number
  email: string
  full_name?: string
}

export default function LoginPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const from = searchParams.get('from')

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [showSignupSuccessMessage, setShowSignupSuccessMessage] = useState(false)

  const validateForm = (): string | null => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

    if (!email.trim() || !password.trim()) {
      return 'Email and password are required'
    }
    if (!emailRegex.test(email.trim())) {
      return 'Please enter a valid email address'
    }
    return null
  }

  useEffect(() => {
    // Show success message if coming from signup
    if (from === 'signup') {
      setShowSignupSuccessMessage(true)
      const timer = setTimeout(() => {
        setShowSignupSuccessMessage(false)
      }, 5000)
      return () => clearTimeout(timer)
    }
  }, [from])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    const validationError = validateForm()
    if (validationError) {
      setError(validationError)
      return
    }

    setIsLoading(true)

    try {
      // First, login to get the session cookie
      const loginResponse = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...CSRF_HEADER,
        },
        body: JSON.stringify({
          email,
          password,
        }),
        credentials: 'include', // Important: include cookies
      })

      if (!loginResponse.ok) {
        const errorData = await loginResponse.json()
        setError('Invalid email or password')
        return
      }

      // Get the access token (for future use, though session cookie is primary)
      const tokenData: LoginResponse = await loginResponse.json()

      // For now, we'll fetch the current user from a hypothetical endpoint
      // For v2, we can just save the basic info
      saveAuthUser({
        id: 0, // Placeholder, will be resolved from protected endpoint
        email: email,
      })

      // Redirect to upload page
      router.push('/upload')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An unexpected error occurred'
      setError(`Login error: ${message}`)
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
            <h1 className="text-3xl font-bold text-arc-light">Sign In</h1>
            <p className="text-arc-light/60">Access your saved analyses</p>
          </div>

          {/* Success message */}
          {showSignupSuccessMessage && (
            <div className="bg-green-500/20 border border-green-500/50 rounded-lg p-3 text-green-200 text-sm">
              ✓ Account created! Please sign in with your credentials.
            </div>
          )}

          {/* Error message */}
          {error && (
            <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3 text-red-200 text-sm">
              {error}
            </div>
          )}

          {/* Form */}
          <form noValidate onSubmit={handleLogin} className="space-y-4">
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
            </div>

            {/* Submit button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 mt-6 bg-gradient-to-r from-arc-purple to-arc-accent text-white font-semibold rounded-lg hover:shadow-lg hover:shadow-arc-purple/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          {/* Footer */}
          <div className="flex items-center justify-center gap-2">
            <span className="text-arc-light/60 text-sm">Don't have an account?</span>
            <Link
              href="/signup"
              className="text-arc-accent font-semibold hover:text-arc-purple transition"
            >
              Create one
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
