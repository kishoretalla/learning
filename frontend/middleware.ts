import { NextRequest, NextResponse } from 'next/server'

/**
 * Middleware for protecting routes that require authentication.
 * 
 * Protected routes (require login):
 * - /upload
 * - /processing
 * - /history
 * - /history/[id]
 * 
 * Public routes (no auth required):
 * - / (home)
 * - /signup
 * - /login
 * - /api/* (handled by backend)
 */

// Routes that require authentication
const PROTECTED_ROUTES = ['/upload', '/processing', '/history']

// Routes that should redirect authenticated users away
const AUTH_ROUTES = ['/login', '/signup']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Check if user has session cookie
  const sessionCookie = request.cookies.get('session')
  const hasSession = !!sessionCookie

  // Check if route is protected
  const isProtectedRoute = PROTECTED_ROUTES.some((route) =>
    pathname.startsWith(route)
  )

  // Check if route is an auth route
  const isAuthRoute = AUTH_ROUTES.some((route) => pathname.startsWith(route))

  // Redirect unauthenticated users from protected routes to login
  if (isProtectedRoute && !hasSession) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('from', pathname)
    return NextResponse.redirect(loginUrl)
  }

  // Redirect authenticated users away from auth routes (optional, enhances UX)
  // Commented out to allow users to re-enter auth pages if desired
  // if (isAuthRoute && hasSession) {
  //   return NextResponse.redirect(new URL('/upload', request.url))
  // }

  return NextResponse.next()
}

// Configure which routes the middleware should run on
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}
