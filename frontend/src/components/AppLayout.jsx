import React, { useState } from 'react';
import AmbientBackground from './AmbientBackground';
import Navbar from './Navbar';
import Sidebar from './Sidebar';

export default function AppLayout({
  title,
  subtitle,
  user,
  onClearWorkspace,
  children,
}) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="relative flex min-h-screen text-slate-100">
      <AmbientBackground />

      <Sidebar
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
        onClearWorkspace={onClearWorkspace}
      />

      <div className="flex-1 flex flex-col min-w-0">
        <Navbar
          variant="app"
          title={title}
          subtitle={subtitle}
          user={user}
          onOpenMobileSidebar={() => setMobileOpen(true)}
        />

        <main className="mx-auto w-full max-w-[1480px] flex-1 px-4 py-7 sm:px-7 lg:px-10 lg:py-10">
          {children}
        </main>
      </div>
    </div>
  );
}
