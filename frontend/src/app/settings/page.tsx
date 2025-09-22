'use client';

import dynamic from 'next/dynamic';

const APIKeyManager = dynamic(() => import('../../components/settings/APIKeyManager'), { ssr: false });

export default function SettingsPage() {
  return (
    <main className="max-w-5xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Settings</h1>
      <APIKeyManager />
    </main>
  );
}


