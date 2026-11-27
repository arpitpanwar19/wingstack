import React from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Compass,
  FileSearch,
  Layers,
  Sparkles,
  Swords,
  Terminal,
} from 'lucide-react';
import AmbientBackground from '../components/AmbientBackground';
import Navbar from '../components/Navbar';
import GlassCard from '../components/GlassCard';
import GlassButton from '../components/GlassButton';
import WingStackLogo from '../components/WingStackLogo';

const features = [
  {
    icon: FileSearch,
    title: 'AI Resume Intelligence',
    description:
      'Submit profile fields and an optional PDF to POST /api/profile/analyze.',
    accent: 'text-honey-100 border-honey-300/25 bg-honey-300/10',
  },
  {
    icon: Compass,
    title: 'Career Scout Engine',
    description:
      'Fetch personalized roles from GET /api/jobs/match/{user_id}.',
    accent: 'text-plum-100 border-plum-300/25 bg-plum-800/35',
  },
  {
    icon: Swords,
    title: 'Accountability War Room',
    description:
      'Use the live pod match, proof verification, and midnight simulation endpoints.',
    accent: 'text-honey-200 border-honey-200/20 bg-plum-900/45',
  },
  {
    icon: Terminal,
    title: 'GitHub & Codeforces Handles',
    description:
      'Handles are sent with profile analysis; continuous telemetry is not implied.',
    accent: 'text-slate-200 border-honey-100/15 bg-black/25',
  },
];

const workflowSteps = [
  {
    step: '01',
    title: 'Create Profile',
    detail:
      'Send name, target role, handles, and optional resume to the live profile-analysis endpoint.',
  },
  {
    step: '02',
    title: 'Match Jobs & Peers',
    detail:
      'Pass the returned user_id to the original job-match and pod-match endpoints.',
  },
  {
    step: '03',
    title: 'Verify Sprint Proof',
    detail:
      'Submit a proof URL and note, then optionally run the confirmed midnight simulation.',
  },
];

export default function LandingPage() {
  return (
    <div className="relative min-h-screen flex flex-col text-slate-100">
      <AmbientBackground />
      <Navbar variant="landing" />

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative mx-auto max-w-7xl px-4 pt-14 pb-20 sm:px-6 lg:px-8 lg:pt-20 lg:pb-28">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-center">
            <div className="lg:col-span-7 space-y-7">
              <div className="inline-flex items-center gap-2 rounded-full border border-honey-300/25 bg-honey-300/[0.06] px-4 py-1.5 text-xs font-semibold tracking-wide text-honey-100 backdrop-blur-xl">
                <Sparkles className="h-3.5 w-3.5 text-honey-200" />
                <span>LIVE WINGSTACK AGENT WORKSPACE</span>
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.08] text-white">
                Career tools,{' '}
                <span className="text-gradient">built around your profile.</span>
              </h1>

              <p className="text-base sm:text-lg text-slate-300/90 max-w-2xl leading-relaxed">
                Create a profile and use the five original Railway endpoints for readiness analysis,
                job matching, pod matching, proof verification, and the midnight demo.
              </p>

              <div className="flex flex-wrap items-center gap-4 pt-1">
                <Link to="/login">
                  <GlassButton size="lg" variant="primary" iconRight={ArrowRight}>
                    Enter WingStack
                  </GlassButton>
                </Link>
              </div>

              <div className="flex flex-wrap items-center gap-x-6 gap-y-2 pt-2 text-xs sm:text-sm text-slate-400">
                <span className="inline-flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  Direct API Calls
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-honey-200" />
                  Profile Storage
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <AlertTriangle className="h-4 w-4 text-amber-400" />
                  Five Original Endpoints
                </span>
              </div>
            </div>

            {/* WingStack introduction */}
            <div className="lg:col-span-5">
              <GlassCard glow="purple" className="space-y-5 animate-float">
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-honey-300/25 bg-honey-300/10 text-honey-200">
                    <Sparkles className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-[11px] font-mono uppercase tracking-wider text-honey-200">
                      Welcome to WingStack
                    </p>
                    <h2 className="mt-1 text-lg font-bold text-white">
                      Original agent endpoints, no orchestrator.
                    </h2>
                  </div>
                </div>

                <p className="text-sm leading-relaxed text-slate-300/90">
                  Analyze once to get a user_id, then pass that ID to job matching and pod matching.
                </p>

                <div className="space-y-3">
                  <div className="flex items-start gap-3 rounded-xl border border-white/[0.08] bg-white/[0.03] p-3">
                    <FileSearch className="mt-0.5 h-4 w-4 shrink-0 text-honey-200" />
                    <p className="text-xs leading-relaxed text-slate-300">
                      <span className="font-semibold text-white">Manage your profile</span>
                      <br />
                      Create a profile with an optional PDF and handles.
                    </p>
                  </div>
                  <div className="flex items-start gap-3 rounded-xl border border-white/[0.08] bg-white/[0.03] p-3">
                    <Compass className="mt-0.5 h-4 w-4 shrink-0 text-plum-200" />
                    <p className="text-xs leading-relaxed text-slate-300">
                      <span className="font-semibold text-white">Job matching</span>
                      <br />
                      Uses GET /api/jobs/match/{'{user_id}'}.
                    </p>
                  </div>
                  <div className="flex items-start gap-3 rounded-xl border border-white/[0.08] bg-white/[0.03] p-3">
                    <Swords className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" />
                    <p className="text-xs leading-relaxed text-slate-300">
                      <span className="font-semibold text-white">Sprint accountability</span>
                      <br />
                      Uses the pod match, sprint verify, and simulate-midnight endpoints.
                    </p>
                  </div>
                </div>
              </GlassCard>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-12">
            <span className="glass-pill text-honey-200">
              <Layers className="h-3.5 w-3.5" />
              Feature Status
            </span>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-white">
              Original endpoint integration
            </h2>
            <p className="text-sm sm:text-base text-slate-400">
              The Railway OpenAPI lists the five agent endpoints below; the app calls them directly.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((item) => {
              const Icon = item.icon;
              return (
                <GlassCard key={item.title} hover className="flex flex-col gap-4">
                  <div
                    className={`flex h-12 w-12 items-center justify-center rounded-xl border ${item.accent}`}
                  >
                    <Icon className="h-6 w-6" />
                  </div>
                  <h3 className="text-lg font-bold text-white">{item.title}</h3>
                  <p className="text-sm text-slate-300/85 leading-relaxed">
                    {item.description}
                  </p>
                </GlassCard>
              );
            })}
          </div>
        </section>

        {/* How It Works Section */}
        <section id="how-it-works" className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
          <GlassCard glow="purple" padding="p-6 sm:p-10">
            <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6 mb-10">
              <div className="space-y-2 max-w-xl">
                <p className="text-xs font-mono uppercase tracking-[0.2em] text-honey-200">
                  Current Integration Status
                </p>
                <h2 className="text-2xl sm:text-3xl font-bold text-white">
                  Five APIs and the user_id workflow
                </h2>
              </div>
              <Link to="/dashboard">
                <GlassButton variant="primary" size="md" iconRight={ArrowRight}>
                  Open Workspace
                </GlassButton>
              </Link>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
              {workflowSteps.map((item) => (
                <div
                  key={item.step}
                  className="rounded-2xl border border-honey-100/10 bg-black/20 p-5 space-y-3 transition-all hover:border-honey-300/25 hover:bg-plum-950/25"
                >
                  <span className="inline-block rounded-lg border border-honey-300/20 bg-honey-300/[0.06] px-2.5 py-1 font-mono text-xs font-bold tracking-widest text-honey-200">
                    STEP {item.step}
                  </span>
                  <h3 className="text-base font-bold text-white">{item.title}</h3>
                  <p className="text-xs sm:text-sm text-slate-300/85 leading-relaxed">
                    {item.detail}
                  </p>
                </div>
              ))}
            </div>
          </GlassCard>
        </section>
      </main>

      {/* Glass Footer */}
      <footer className="mt-12 border-t border-honey-200/10 bg-void-950/70 backdrop-blur-xl">
        <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-2">
            <WingStackLogo size="sm" showTagline />
            <p className="text-xs text-slate-400">Career workflow prototype.</p>
          </div>

          <div className="flex flex-wrap items-center gap-6 text-xs sm:text-sm text-slate-400">
            <Link to="/dashboard" className="hover:text-white transition-colors">
              Student Dashboard
            </Link>
            <Link to="/career-scout" className="hover:text-white transition-colors">
              Career Scout
            </Link>
            <Link to="/war-room" className="hover:text-white transition-colors">
              War Room
            </Link>
          </div>

          <p className="text-xs text-slate-500 font-mono">
            © {new Date().getFullYear()} WingStack Protocol
          </p>
        </div>
      </footer>
    </div>
  );
}
