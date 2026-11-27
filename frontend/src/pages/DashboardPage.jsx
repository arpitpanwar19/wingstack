import React from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowUpRight,
  Compass,
  FileSearch,
  ShieldCheck,
  Sparkles,
  Swords,
} from 'lucide-react';
import AppLayout from '../components/AppLayout';
import GlassButton from '../components/GlassButton';
import GlassCard from '../components/GlassCard';
import { useWorkspace } from '../context/WorkspaceContext';

const workflows = [
  {
    label: '01 / RESUME INTELLIGENCE',
    title: 'Understand your signal',
    description: 'Create a profile and receive live readiness and skills data.',
    to: '/resume-analyzer',
    action: 'Open analyzer',
    icon: FileSearch,
    status: 'POST /api/profile/analyze',
  },
  {
    label: '02 / CAREER SCOUT',
    title: 'Find the right next move',
    description: 'Fetch live matched roles using the user ID returned by profile analysis.',
    to: '/career-scout',
    action: 'Explore roles',
    icon: Compass,
    status: 'GET /api/jobs/match/{user_id}',
  },
  {
    label: '03 / ACCOUNTABILITY',
    title: 'Build momentum together',
    description: 'Find a partner, submit proof, and run a confirmed midnight simulation.',
    to: '/war-room',
    action: 'View War Room',
    icon: Swords,
    status: 'LIVE POD + SPRINT APIs',
  },
];

export default function DashboardPage() {
  const { profile, clearWorkspace } = useWorkspace();
  const displayName = profile?.name || 'your next chapter';

  return (
    <AppLayout
      title="Workspace"
      subtitle="Your live WingStack agent workspace"
      user={profile}
      onClearWorkspace={clearWorkspace}
    >
      <div className="space-y-8 animate-fade-in-up">
        <section className="relative overflow-hidden rounded-[2rem] border border-honey-200/20 bg-[radial-gradient(ellipse_at_78%_0%,rgba(59,22,58,0.8),transparent_52%),linear-gradient(135deg,#1b111d,#0c090d_72%)] p-6 shadow-[0_30px_90px_rgba(0,0,0,0.5)] sm:p-10 lg:p-12">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -right-20 -top-32 h-80 w-80 rounded-full border border-honey-200/10"
          />
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -right-8 -top-20 h-56 w-56 rounded-full border border-plum-300/20"
          />
          <div
            aria-hidden="true"
            className="pointer-events-none absolute right-8 top-12 h-24 w-24 rounded-full bg-honey-300/10 blur-3xl"
          />

          <div className="relative z-10 grid items-end gap-10 lg:grid-cols-[1.25fr_0.75fr]">
            <div className="max-w-2xl">
              <p className="eyebrow">
                <span className="h-1.5 w-1.5 rounded-full bg-honey-300 shadow-[0_0_12px_rgba(240,201,134,0.8)]" />
                PERSONAL CAREER WORKSPACE
              </p>
              <h2 className="mt-5 text-4xl font-semibold leading-[1.08] tracking-tight text-white sm:text-5xl">
                {profile ? 'Welcome back,' : 'Start building'}
                <span className="mt-1 block text-gradient">{displayName}</span>
              </h2>
              <p className="mt-5 max-w-xl text-sm leading-7 text-slate-300 sm:text-base">
                {profile
                  ? 'Your profile ID unlocks live job matches and pod workflows. Analysis results and partnership details are saved in this browser.'
                  : 'Run a live profile analysis to get the user ID required by job matching and pod workflows.'}
              </p>
              <div className="mt-7 flex flex-wrap gap-3">
                <Link to="/resume-analyzer">
                  <GlassButton variant="primary" icon={FileSearch}>
                    Run readiness analysis
                  </GlassButton>
                </Link>
                <Link to="/resume-analyzer">
                  <GlassButton variant="secondary" iconRight={ArrowUpRight}>
                    Resume workspace
                  </GlassButton>
                </Link>
              </div>
            </div>

            <div className="glass-subtle relative overflow-hidden rounded-3xl p-5 sm:p-6">
              <div className="absolute -right-12 -top-12 h-36 w-36 rounded-full bg-honey-300/10 blur-3xl" />
              <div className="relative flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-honey-300/25 bg-honey-300/10 text-honey-200">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <div>
                  <p className="eyebrow">WORKSPACE STATUS</p>
                  <p className="mt-1 text-lg font-semibold text-white">
                    {profile?.user_id ?? 'No profile ID yet'}
                  </p>
                </div>
              </div>
              <div className="gold-rule my-5" />
              <p className="relative text-sm leading-6 text-slate-400">
                {profile
                  ? 'This numeric ID was returned by the profile-analysis API and is used by downstream endpoints.'
                  : 'The profile-analysis endpoint creates the ID used by the other live agent endpoints.'}
              </p>
              <Link
                to={profile ? '/profile' : '/resume-analyzer'}
                className="relative mt-5 inline-flex items-center gap-2 text-sm font-semibold text-honey-200 transition-colors hover:text-white"
              >
                {profile ? 'Review your profile' : 'Create your profile'} <ArrowUpRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </section>

        <section className="space-y-4">
          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
            <div>
              <p className="eyebrow">THE WINGSTACK SYSTEM</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-white">
                Your next moves
              </h2>
            </div>
            <p className="max-w-md text-sm leading-6 text-slate-400">
              Each module calls its original Railway endpoint directly—no orchestrator route or sample records.
            </p>
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            {workflows.map((workflow) => {
              const Icon = workflow.icon;
              return (
                <GlassCard
                  key={workflow.label}
                  hover
                  className="group flex min-h-64 flex-col justify-between p-5 sm:p-6"
                >
                  <div>
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-honey-300/20 bg-plum-900/50 text-honey-200">
                        <Icon className="h-5 w-5" />
                      </div>
                      <span className="rounded-full border border-plum-300/20 bg-black/20 px-2.5 py-1 text-[9px] font-semibold tracking-[0.16em] text-honey-200/80">
                        {workflow.status}
                      </span>
                    </div>
                    <p className="mt-5 text-[10px] font-semibold tracking-[0.2em] text-honey-300/70">
                      {workflow.label}
                    </p>
                    <h3 className="mt-2 text-xl font-semibold text-white">{workflow.title}</h3>
                    <p className="mt-2 text-sm leading-6 text-slate-400">
                      {workflow.description}
                    </p>
                  </div>
                  <Link
                    to={workflow.to}
                    className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-honey-200 transition-all group-hover:gap-3"
                  >
                    {workflow.action}
                    <ArrowUpRight className="h-4 w-4" />
                  </Link>
                </GlassCard>
              );
            })}
          </div>
        </section>

        <div className="flex items-center gap-3 rounded-2xl border border-plum-300/15 bg-plum-950/25 px-5 py-4">
          <Sparkles className="h-4 w-4 shrink-0 text-honey-300" />
          <p className="text-xs leading-5 text-slate-400">
            Agent data will appear here only after the backend returns it. Your workspace is not populated with example users, jobs, or scores.
          </p>
        </div>
      </div>
    </AppLayout>
  );
}
