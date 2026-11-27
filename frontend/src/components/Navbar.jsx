import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Bell, Menu, Sparkles, X } from 'lucide-react';
import WingStackLogo from './WingStackLogo';
import GlassButton from './GlassButton';

export default function Navbar({
  variant = 'landing',
  title,
  subtitle,
  user,
  onOpenMobileSidebar,
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  if (variant === 'app') {
    const initials = user?.name
      ?.split(' ')
      .map((part) => part[0])
      .join('')
      .slice(0, 2)
      .toUpperCase();

    return (
      <header className="sticky top-0 z-30 border-b border-honey-200/10 bg-void-950/80 shadow-[0_8px_32px_rgba(0,0,0,0.28)] backdrop-blur-2xl">
        <div className="flex h-16 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3 min-w-0">
            <button
              type="button"
              onClick={onOpenMobileSidebar}
              aria-label="Open navigation menu"
              className="lg:hidden flex h-10 w-10 items-center justify-center rounded-xl border border-honey-200/15 bg-plum-950/50 text-honey-100 hover:border-honey-200/35 hover:bg-plum-900/70 transition-colors"
            >
              <Menu className="h-5 w-5" />
            </button>

            <div className="min-w-0">
              <h1 className="text-base sm:text-lg font-bold text-honey-50 truncate">
                {title || 'Command Center'}
              </h1>
              {subtitle && (
                <p className="hidden sm:block text-xs text-slate-400 truncate">{subtitle}</p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2.5 sm:gap-3 shrink-0">
            <Link
              to="/war-room"
              className="relative flex h-9 w-9 items-center justify-center rounded-xl border border-plum-300/20 bg-plum-950/55 text-slate-300 hover:border-honey-300/30 hover:text-honey-100 hover:bg-plum-900/60 transition-colors"
              title="War Room Alerts"
            >
              <Bell className="h-4 w-4" />
            </Link>

            <Link
              to="/profile"
              className="flex items-center gap-2.5 rounded-xl border border-plum-300/20 bg-plum-950/55 pl-1.5 pr-3 py-1 hover:border-honey-300/30 hover:bg-plum-900/60 transition-colors"
            >
              {initials && (
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-honey-300 to-plum-600 text-xs font-bold text-void-950">
                  {initials}
                </div>
              )}
              <div className="hidden sm:block text-left leading-tight">
                <p className="text-xs font-semibold text-white max-w-[110px] truncate">
                  {user?.name || user?.email}
                </p>
                {user?.targetRole && (
                  <p className="text-[10px] text-honey-200/90 max-w-[110px] truncate">
                    {user.targetRole}
                  </p>
                )}
              </div>
            </Link>
          </div>
        </div>
      </header>
    );
  }

  return (
    <header className="sticky top-0 z-40 border-b border-honey-200/10 bg-void-950/80 backdrop-blur-2xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link to="/" className="shrink-0">
          <WingStackLogo size="sm" />
        </Link>

        <nav className="hidden md:flex items-center gap-7 text-sm font-medium text-slate-400">
          <a href="#features" className="hover:text-honey-100 transition-colors">
            Features
          </a>
          <a href="#how-it-works" className="hover:text-honey-100 transition-colors">
            How It Works
          </a>
          <Link to="/login" className="inline-flex items-center gap-1.5 text-honey-300 hover:text-honey-100 transition-colors">
            <Sparkles className="h-3.5 w-3.5" />
            Enter Workspace
          </Link>
        </nav>

        <div className="hidden md:flex items-center gap-3">
          <Link to="/login">
            <GlassButton variant="primary" size="sm">
              Enter WingStack
            </GlassButton>
          </Link>
        </div>

        <button
          type="button"
          onClick={() => setMobileMenuOpen((prev) => !prev)}
          aria-label="Toggle navigation menu"
          className="md:hidden flex h-10 w-10 items-center justify-center rounded-xl border border-white/12 bg-white/[0.05] text-slate-200"
        >
          {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {mobileMenuOpen && (
        <div className="md:hidden border-t border-honey-200/10 bg-void-900/95 backdrop-blur-2xl px-4 py-4 space-y-3">
          <a
            href="#features"
            onClick={() => setMobileMenuOpen(false)}
            className="block rounded-xl px-3 py-2 text-sm text-slate-200 hover:bg-plum-900/45 hover:text-honey-100"
          >
            Features
          </a>
          <a
            href="#how-it-works"
            onClick={() => setMobileMenuOpen(false)}
            className="block rounded-xl px-3 py-2 text-sm text-slate-200 hover:bg-plum-900/45 hover:text-honey-100"
          >
            How It Works
          </a>
          <div className="pt-2">
            <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
              <GlassButton variant="primary" className="w-full">
                Enter WingStack
              </GlassButton>
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
