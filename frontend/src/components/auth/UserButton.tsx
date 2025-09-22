'use client';

import { UserButton as ClerkUserButton, useUser } from '@clerk/nextjs';
import { Settings, LogOut } from 'lucide-react';
import { useState } from 'react';

export default function UserButton() {
  const { user } = useUser();
  const [showSettings, setShowSettings] = useState(false);

  return (
    <div className="relative">
      <ClerkUserButton
        appearance={{
          elements: {
            avatarBox: "w-10 h-10",
            userButtonPopoverCard: "bg-white dark:bg-gray-800 shadow-xl",
            userButtonPopoverActionButton: "hover:bg-gray-100 dark:hover:bg-gray-700",
          }
        }}
        afterSignOutUrl="/"
      />
    </div>
  );
}
