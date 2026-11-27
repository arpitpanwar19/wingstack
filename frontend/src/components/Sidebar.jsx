import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  Compass,
  FileSearch,
  LayoutDashboard,
  RotateCcw,
  Swords,
  User,
  X,
} from 'lucide-react';
import WingStackLogo from './WingStackLogo';

const navItems = [
  { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
  { label: 'Resume Analyzer', to: '/resume-analyzer', icon: FileSearch },
  { label: 'Career Scout', to: '/career-scout', icon: Compass },
  { label: 'War Room', to: '/war-room', icon: Swords },
  { label: 'Profile', to: '/profile', icon: User },
];

export default function Sidebar({
  mobileOpen = false,
  onCloseMobile,
  onClearWorkspace,
}) {
  const navigate = useNavigate();

  const handleClearWorkspace = () => {
    onCloseMobile?.();
    onClearWorkspace?.();
    navigate('/resume-analyzer');
  };

  const sidebarContent = (
    <div className="flex h-full flex-col justify-between border-r border-honey-200/10 bg-gradient-to-b from-void-900/95 via-void-950/95 to-black/95 p-5 backdrop-blur-2xl">
      <div className="space-y-6">
        <div className="flex items-center justify-between px-2 pt-1">
          <NavLink to="/" onClick={onCloseMobile}>
            <WingStackLogo size="sm" showTagline />
          </NavLink>
          <button
            type="button"
            onClick={onCloseMobile}
            aria-label="Close navigation menu"
            className="lg:hidden rounded-lg p-1.5 text-slate-400 hover:bg-white/10 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="space-y-1.5" aria-label="Primary navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={onCloseMobile}
                className={({ isActive }) =>
                  `group flex items-center justify-between gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all duration-200 border ${
                    isActive
                      ? 'bg-gradient-to-r from-honey-300/15 via-plum-800/35 to-transparent border-honey-300/25 text-honey-100 shadow-[inset_3px_0_0_0_rgba(240,201,134,0.8)]'
                      : 'border-transparent text-slate-400 hover:bg-plum-900/35 hover:text-honey-100 hover:border-honey-100/10'
                  }`
                }
              >
                <div className="flex items-center gap-3">
                  <Icon className="h-4 w-4 shrink-0 text-honey-300/80 group-hover:text-honey-200" />
                  <span>{item.label}</span>
                </div>
              </NavLink>
            );
          })}
        </nav>
      </div>

      <div className="space-y-4 pt-5 border-t border-honey-100/10">
        <div className="rounded-2xl border border-plum-300/20 bg-gradient-to-br from-plum-900/50 to-black/30 p-4">
          <p className="eyebrow">WingStack workspace</p>
          <p className="mt-2 text-xs leading-relaxed text-slate-400">
            Profile analysis and partnership details are saved in this browser for your workspace.
          </p>
        </div>
        <button
          type="button"
          onClick={handleClearWorkspace}
          className="flex w-full items-center gap-3 rounded-xl border border-white/[0.08] bg-black/20 px-3.5 py-2.5 text-sm font-medium text-slate-400 hover:bg-plum-900/35 hover:border-honey-300/20 hover:text-honey-100 transition-all"
        >
          <RotateCcw className="h-4 w-4" />
          <span>Clear Workspace</span>
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Rail */}
      <aside className="hidden lg:block lg:w-64 lg:shrink-0 lg:sticky lg:top-0 lg:h-screen">
        {sidebarContent}
      </aside>

      {/* Mobile Slide-Over Drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div
            className="fixed inset-0 bg-black/65 backdrop-blur-sm"
            onClick={onCloseMobile}
            aria-hidden="true"
          />
          <aside className="relative z-10 w-72 max-w-[85vw] h-full">{sidebarContent}</aside>
        </div>
      )}
    </>
  );
}
