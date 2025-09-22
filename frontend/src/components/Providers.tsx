'use client';

import { ReactNode } from 'react';
import { ClerkProvider } from '@clerk/nextjs';

interface ProvidersProps {
  children: ReactNode;
}

export default function Providers({ children }: ProvidersProps) {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
  
  // Always wrap with ClerkProvider, even with empty key for build compatibility
  return (
    <ClerkProvider publishableKey={publishableKey || ''}>
      {children}
    </ClerkProvider>
  );
}


