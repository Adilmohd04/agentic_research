import { clerkMiddleware } from '@clerk/nextjs/server'
export default clerkMiddleware()

// Keep most routes public until Clerk keys are configured
export const config = {
  matcher: [
    '/protected(.*)'
  ]
}


