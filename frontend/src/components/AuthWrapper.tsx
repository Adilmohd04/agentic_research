'use client';

import { ReactNode } from 'react';
import { SignedIn, SignedOut, SignInButton, SignUpButton } from '@clerk/nextjs';
import { Bot, Sparkles, Zap, Shield } from 'lucide-react';

interface AuthWrapperProps {
  children: ReactNode;
}

export default function AuthWrapper({ children }: AuthWrapperProps) {
  return (
    <>
      <SignedIn>
        {children}
      </SignedIn>
      
      <SignedOut>
        <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
          <div className="flex flex-col items-center justify-center min-h-screen px-4">
            <div className="max-w-md w-full space-y-8 text-center">
              {/* Logo */}
              <div className="flex justify-center">
                <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg">
                  <Bot className="w-8 h-8 text-white" />
                </div>
              </div>

              {/* Title */}
              <div className="space-y-2">
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                  AI Research Assistant
                </h1>
                <p className="text-gray-600 dark:text-gray-400">
                  Your intelligent companion for research, analysis, and insights
                </p>
              </div>

              {/* Features */}
              <div className="grid grid-cols-1 gap-4 py-6">
                <div className="flex items-center space-x-3 p-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
                  <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                    <Sparkles className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div className="text-left">
                    <h3 className="font-medium text-gray-900 dark:text-white">Smart Analysis</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">AI-powered research and insights</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3 p-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
                  <div className="w-8 h-8 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center">
                    <Zap className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div className="text-left">
                    <h3 className="font-medium text-gray-900 dark:text-white">Real-time Voice</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Voice chat and speech recognition</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3 p-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
                  <div className="w-8 h-8 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
                    <Shield className="w-4 h-4 text-green-600 dark:text-green-400" />
                  </div>
                  <div className="text-left">
                    <h3 className="font-medium text-gray-900 dark:text-white">Secure & Private</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Your data is protected and encrypted</p>
                  </div>
                </div>
              </div>

              {/* Auth Buttons */}
              <div className="space-y-4">
                <SignUpButton>
                  <button className="w-full py-3 px-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5">
                    Get Started
                  </button>
                </SignUpButton>
                
                <SignInButton>
                  <button className="w-full py-3 px-4 bg-white dark:bg-gray-800 text-gray-900 dark:text-white font-medium rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                    Sign In
                  </button>
                </SignInButton>
              </div>

              {/* Footer */}
              <p className="text-xs text-gray-500 dark:text-gray-400">
                By signing up, you agree to our terms of service and privacy policy
              </p>
            </div>
          </div>
        </div>
      </SignedOut>
    </>
  );
}