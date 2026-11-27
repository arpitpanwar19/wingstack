import React from 'react';
import { BadgeCheck, Code2, Github, MapPin, Target } from 'lucide-react';
import GlassCard from './GlassCard';
import GlassButton from './GlassButton';

export default function ProfileCard({ user, compact = false, onEdit, className = '' }) {
  if (!user) return null;

  const initials = user.name
    ?.split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  return (
    <GlassCard glow="purple" className={`relative overflow-hidden ${className}`}>
      <div className="absolute -right-10 -top-16 h-48 w-48 rounded-full bg-plum-700/25 blur-3xl" />
      <div className="relative flex flex-col justify-between gap-5 sm:flex-row sm:items-center">
        <div className="flex min-w-0 items-center gap-4">
          {initials && (
            <div className="relative flex h-[4.25rem] w-[4.25rem] shrink-0 items-center justify-center rounded-[1.4rem] border border-honey-200/30 bg-gradient-to-br from-honey-300/20 via-plum-800/80 to-black text-lg font-semibold text-honey-100 shadow-[0_0_34px_rgba(59,22,58,0.5)]">
              <span className="absolute inset-1 rounded-[1.05rem] border border-honey-200/10" />
              <span className="relative">{initials}</span>
            </div>
          )}
          <div className="min-w-0 space-y-1">
            <p className="text-[9px] font-semibold tracking-[0.22em] text-honey-300/75">ACCOUNT PROFILE</p>
            <h3 className="truncate text-xl font-semibold text-white sm:text-2xl">
              {user.name || user.email}
            </h3>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-300">
              {user.targetRole && user.targetRole !== 'Student' && (
                <span className="inline-flex items-center gap-1 text-honey-200">
                  <Target className="h-3.5 w-3.5" />
                  {user.targetRole}
                </span>
              )}
              {user.location && (
                <span className="inline-flex items-center gap-1 text-slate-400">
                  <MapPin className="h-3.5 w-3.5" />
                  {user.location}
                </span>
              )}
            </div>
          </div>
        </div>
        {onEdit && (
          <GlassButton
            variant="secondary"
            size="sm"
            onClick={onEdit}
            className="self-start sm:self-center"
          >
            Edit Profile
          </GlassButton>
        )}
      </div>

      {!compact && (
        <div className="relative mt-5 border-t border-honey-100/10 pt-4">
          <p className="max-w-3xl text-sm leading-6 text-slate-300/85">
            {user.bio || 'Add a short professional bio to give your profile more context.'}
          </p>
        </div>
      )}

      <div className="relative mt-4 flex flex-wrap items-center gap-2.5 border-t border-honey-100/10 pt-4">
        <span className="inline-flex items-center gap-1.5 rounded-xl border border-honey-300/20 bg-honey-300/[0.06] px-3 py-1.5 text-xs font-medium text-honey-100">
          <BadgeCheck className="h-3.5 w-3.5" />
          Local profile
        </span>
        {user.githubUsername && (
          <span className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs text-slate-300">
            <Github className="h-3.5 w-3.5" />
            @{user.githubUsername}
          </span>
        )}
        {user.codeforcesHandle && (
          <span className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs text-slate-300">
            <Code2 className="h-3.5 w-3.5" />
            {user.codeforcesHandle}
          </span>
        )}
      </div>
    </GlassCard>
  );
}
