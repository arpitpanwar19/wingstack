import React, { useCallback, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowUpRight,
  Compass,
  Filter,
  BriefcaseBusiness,
  RefreshCw,
  Search,
  SlidersHorizontal,
  Sparkles,
} from 'lucide-react';
import AppLayout from '../components/AppLayout';
import GlassCard from '../components/GlassCard';
import GlassInput from '../components/GlassInput';
import GlassButton from '../components/GlassButton';
import JobCard from '../components/JobCard';
import LoadingSpinner from '../components/LoadingSpinner';
import Notification from '../components/Notification';
import { useApiResource } from '../hooks/useApiResource';
import {
  getMatchedJobs,
} from '../services/api';
import { useWorkspace } from '../context/WorkspaceContext';

function getMatchScore(job) {
  const rawScore =
    job.match_score ??
    job.role_fit_score ??
    job.fit_score ??
    job.matchPercentage ??
    job.match_percentage;
  const score = Number(rawScore);
  return rawScore !== undefined && rawScore !== null && Number.isFinite(score)
    ? score
    : null;
}

function getSkillNames(value) {
  if (!Array.isArray(value)) return [];
  return value
    .map((skill) => (typeof skill === 'string' ? skill : skill?.name ?? skill?.skill))
    .filter((skill) => typeof skill === 'string');
}

export default function CareerScoutPage() {
  const { profile, clearWorkspace } = useWorkspace();
  const userId = profile?.user_id ?? profile?.id;

  const [searchQuery, setSearchQuery] = useState('');
  const [workMode, setWorkMode] = useState('All');
  const [sourceTier, setSourceTier] = useState('All');
  const [experienceLevel, setExperienceLevel] = useState('All');
  const [minMatch, setMinMatch] = useState(0);
  const [onlyZeroMissing, setOnlyZeroMissing] = useState(false);

  const fetchJobs = useCallback(async () => {
    if (userId === undefined || userId === null) return [];
    const res = await getMatchedJobs(userId);
    const jobs = Array.isArray(res)
      ? res
      : res?.matched_jobs ?? res?.jobs ?? res?.matches ?? res?.data;
    if (!Array.isArray(jobs) || jobs.some((job) => !job || typeof job !== 'object')) {
      throw new Error('Job matching returned an unsupported response format.');
    }
    return jobs;
  }, [userId]);

  const {
    data: jobsData,
    loading,
    error,
    reload,
  } = useApiResource(fetchJobs);

  const jobs = jobsData || [];

  const filteredJobs = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return jobs
      .filter((job) => {
        const matchPct = getMatchScore(job);
        if (minMatch > 0 && (matchPct === null || matchPct < minMatch)) return false;
        const jobWorkMode = job.workMode || job.work_mode || job.work_type || '';
        const jobSourceTier = job.source_tier || job.platform || '';
        if (sourceTier !== 'All' && !jobSourceTier.toLowerCase().includes(sourceTier.toLowerCase())) {
          return false;
        }
        if (workMode !== 'All' && jobWorkMode.toLowerCase() !== workMode.toLowerCase()) {
          return false;
        }
        const jobExperience = job.experienceLevel || job.experience_level || '';
        if (
          experienceLevel !== 'All' &&
          !jobExperience.toLowerCase().includes(experienceLevel.toLowerCase())
        ) {
          return false;
        }
        const missing = getSkillNames(job.missingSkills || job.missing_skills);
        if (onlyZeroMissing && missing.length > 0) return false;

        if (!q) return true;
        const haystack = [
          job.company,
          job.company_name,
          job.role,
          job.title,
          job.job_title,
          job.location,
          job.location_type,
          ...getSkillNames(job.requiredSkills || job.required_skills),
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase();
        return haystack.includes(q);
      })
      .sort(
        (a, b) => (getMatchScore(b) ?? -Infinity) - (getMatchScore(a) ?? -Infinity)
      );
  }, [jobs, searchQuery, workMode, experienceLevel, minMatch, onlyZeroMissing]);

  const resetFilters = () => {
    setSearchQuery('');
    setWorkMode('All');
    setSourceTier('All');
    setExperienceLevel('All');
    setMinMatch(0);
    setOnlyZeroMissing(false);
  };

  return (
    <AppLayout
      title="Career Scout"
      subtitle="Live matched roles from your analyzed profile"
      user={profile}
      onClearWorkspace={clearWorkspace}
    >
      <div className="space-y-6 animate-fade-in-up">
        <section className="relative overflow-hidden rounded-[2rem] border border-honey-200/20 bg-[radial-gradient(ellipse_at_88%_0%,rgba(59,22,58,0.82),transparent_48%),linear-gradient(135deg,#1b111d,#0c090d_72%)] p-6 shadow-[0_30px_90px_rgba(0,0,0,0.42)] sm:p-9">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -right-10 -top-20 h-64 w-64 rounded-full border border-honey-200/10"
          />
          <div className="relative z-10 flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
            <div className="max-w-2xl">
              <p className="eyebrow"><Compass className="h-3.5 w-3.5" /> CAREER SCOUT</p>
              <h2 className="mt-4 text-3xl font-semibold leading-tight tracking-tight text-white sm:text-4xl">
                The right move
                <span className="block text-gradient">starts with signal.</span>
              </h2>
              <p className="mt-3 max-w-xl text-sm leading-6 text-slate-300">
                Retrieve matched roles and fit details from the live job-matching endpoint using your
                analyzed profile ID. No sample listings are shown.
              </p>
            </div>
            <div className="flex items-center gap-3 rounded-2xl border border-plum-300/20 bg-black/25 px-4 py-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-honey-300/20 bg-honey-300/10 text-honey-200">
                <BriefcaseBusiness className="h-5 w-5" />
              </div>
              <div>
                <p className="text-[9px] font-semibold tracking-[0.2em] text-slate-500">MATCH FEED</p>
                <p className="mt-1 text-sm font-medium text-honey-100">
                  {userId === undefined || userId === null ? 'Analyze profile first' : 'Live matching'}
                </p>
              </div>
            </div>
          </div>
        </section>

        {error && (
          <Notification
            type="warning"
            title="Job Matching API Error"
            message={error}
          />
        )}

        {/* Search & Filter Control Glass Panel */}
        <GlassCard glow="blue" className="space-y-5">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div className="flex-1">
              <GlassInput
                icon={Search}
                placeholder="Search by role, company, location, or skill"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            <div className="flex flex-wrap items-center gap-2.5 shrink-0">
              <GlassButton
                variant="secondary"
                size="md"
                icon={RefreshCw}
                onClick={reload}
              >
                Refresh Jobs
              </GlassButton>
              <GlassButton variant="ghost" size="md" onClick={resetFilters}>
                Reset Filters
              </GlassButton>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-3 border-t border-honey-100/10 pt-5 sm:grid-cols-2 lg:grid-cols-5">
            <GlassInput
              label="Source Tier (70+ Boards)"
              as="select"
              icon={BriefcaseBusiness}
              value={sourceTier}
              onChange={(e) => setSourceTier(e.target.value)}
            >
              <option value="All">All Sources</option>
              <option value="Direct ATS">Direct ATS (Greenhouse/Lever/Ashby)</option>
              <option value="Custom Portal">Custom Career Portals (Big Tech/Unicorns)</option>
              <option value="Remote API">Remote Startup APIs</option>
              <option value="Hackathon">Hackathons & Challenges</option>
            </GlassInput>
            <GlassInput
              label="Work Mode"
              as="select"
              icon={Compass}
              value={workMode}
              onChange={(e) => setWorkMode(e.target.value)}
            >
              <option value="All">All Modes</option>
              <option value="Remote">Remote</option>
              <option value="Hybrid">Hybrid</option>
              <option value="On-site">On-site</option>
            </GlassInput>

            <GlassInput
              label="Experience Level"
              as="select"
              icon={SlidersHorizontal}
              value={experienceLevel}
              onChange={(e) => setExperienceLevel(e.target.value)}
            >
              <option value="All">All Levels</option>
              <option value="Entry">Entry / Junior</option>
              <option value="Mid">Mid-Level</option>
              <option value="Senior">Senior</option>
            </GlassInput>

            <GlassInput
              label="Minimum Match %"
              as="select"
              icon={Sparkles}
              value={minMatch}
              onChange={(e) => setMinMatch(Number(e.target.value))}
            >
              <option value={0}>Any Match %</option>
              <option value={70}>70%+ Match</option>
              <option value={80}>80%+ Match</option>
              <option value={85}>85%+ High Fit</option>
            </GlassInput>

            <div className="flex flex-col justify-end">
              <button
                type="button"
                onClick={() => setOnlyZeroMissing((prev) => !prev)}
                className={`flex items-center justify-center gap-2 rounded-xl border px-4 py-3 text-xs font-semibold transition-all ${
                  onlyZeroMissing
                    ? 'border-honey-300/40 bg-honey-300/10 text-honey-100 shadow-[0_0_20px_rgba(240,201,134,0.1)]'
                    : 'border-plum-300/20 bg-black/20 text-slate-300 hover:border-honey-300/25 hover:bg-plum-950/50'
                }`}
              >
                <Filter className="h-4 w-4" />
                <span>{onlyZeroMissing ? 'Zero Missing Skills Only ✓' : 'Zero Missing Skills Only'}</span>
              </button>
            </div>
          </div>
        </GlassCard>

        {/* Result Header */}
        {jobs.length > 0 && <div className="flex items-center justify-between rounded-xl border border-plum-300/15 bg-plum-950/20 px-4 py-3 text-xs sm:text-sm text-slate-400">
          <span>
            Showing <strong className="text-white font-mono">{filteredJobs.length}</strong> of{' '}
            <strong className="text-white font-mono">{jobs.length}</strong> scouted roles
          </span>
          <span className="hidden items-center gap-1.5 sm:inline-flex font-mono text-honey-200">
            Sorted by fit <ArrowUpRight className="h-3.5 w-3.5" />
          </span>
        </div>}

        {loading ? (
          <div className="py-20 flex justify-center">
            <LoadingSpinner size="lg" label="Scouting matched engineering roles..." />
          </div>
        ) : jobs.length === 0 ? (
          <GlassCard glow="purple" className="relative overflow-hidden py-16 text-center">
            <div className="absolute inset-x-1/3 top-0 h-40 bg-plum-700/25 blur-3xl" />
            <div className="relative mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border border-honey-300/20 bg-honey-300/10 text-honey-200">
              <Compass className="h-7 w-7" />
            </div>
            <p className="relative mt-5 text-xl font-semibold text-white">
              {userId === undefined || userId === null ? 'Analyze your profile first' : 'No matched roles returned'}
            </p>
            <p className="relative mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-400">
              {userId === undefined || userId === null
                ? 'Create a profile to receive the user ID required by the live job-matching API.'
                : 'The live API returned no job records for this profile.'}
            </p>
            <div className="relative mt-6">
              {userId === undefined || userId === null ? (
                <Link to="/resume-analyzer">
                  <GlassButton variant="primary">Create profile</GlassButton>
                </Link>
              ) : (
                <GlassButton variant="secondary" icon={RefreshCw} onClick={reload}>
                  Refresh matches
                </GlassButton>
              )}
            </div>
          </GlassCard>
        ) : filteredJobs.length === 0 ? (
          <GlassCard className="space-y-4 py-14 text-center">
            <p className="text-xl font-semibold text-white">No roles match these filters</p>
            <p className="text-sm text-slate-400">
              Try lowering the minimum match percentage or clearing your search query.
            </p>
            <div>
              <GlassButton variant="secondary" onClick={resetFilters}>
                Clear All Filters
              </GlassButton>
            </div>
          </GlassCard>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {filteredJobs.map((job) => (
              <JobCard
                key={job.id ?? job.job_id ?? `${job.company}-${job.role ?? job.title}`}
                job={job}
              />
            ))}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
