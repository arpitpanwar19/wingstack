import React from 'react';
import { AlertCircle, Briefcase, ExternalLink, MapPin, Sparkles } from 'lucide-react';
import GlassCard from './GlassCard';

function asSkillNames(value) {
  if (!Array.isArray(value)) return [];
  return value
    .map((skill) => (typeof skill === 'string' ? skill : skill?.name ?? skill?.skill))
    .filter((skill) => typeof skill === 'string' && skill.length > 0);
}

function asText(value) {
  return typeof value === 'string' || typeof value === 'number' ? String(value) : '';
}

export default function JobCard({ job, compact = false }) {
  const rawMatch =
    job.role_fit_score ??
    job.fit_score ??
    job.matchPercentage ??
    job.match_percentage;
  const match = Number(rawMatch);
  const hasMatch = rawMatch !== undefined && rawMatch !== null && Number.isFinite(match);
  const company = asText(job.company ?? job.company_name);
  const role = asText(job.role ?? job.title ?? job.job_title);
  const requiredSkills = asSkillNames(job.requiredSkills ?? job.required_skills);
  const missingSkills = asSkillNames(job.missingSkills ?? job.missing_skills);
  const applyUrl = job.apply_url ?? job.applyUrl ?? job.application_url ?? job.url;
  const outreachPitch = asText(
    job.ai_outreach_pitch ?? job.outreach_pitch ?? job.outreachPitch
  );
  const location = asText(job.location ?? job.location_type);
  const workMode = asText(job.workMode ?? job.work_mode ?? job.work_type);
  const salary = asText(job.salary ?? job.salary_range);
  const description = asText(job.description ?? job.summary);
  const postedAt = asText(job.postedAt ?? job.posted_at);
  const companyInitials = company.slice(0, 2).toUpperCase();

  const matchBadgeStyle =
    match >= 85
      ? 'border-honey-300/40 bg-honey-300/10 text-honey-100 shadow-[0_0_16px_rgba(240,201,134,0.16)]'
      : match >= 70
        ? 'border-plum-300/35 bg-plum-900/45 text-plum-100 shadow-[0_0_16px_rgba(59,22,58,0.28)]'
        : 'border-plum-400/25 bg-black/25 text-slate-300';

  return (
    <GlassCard hover padding={compact ? 'p-4' : 'p-6'} className="flex h-full flex-col justify-between gap-4">
      <div className="space-y-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-start gap-3.5">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-honey-200/15 bg-gradient-to-br from-honey-300/15 via-plum-800/45 to-black text-sm font-bold text-honey-100">
              {companyInitials || <Briefcase className="h-4 w-4" />}
            </div>
            <div className="min-w-0">
              <p className="truncate text-xs font-semibold uppercase tracking-wider text-honey-300/90">
                {company || 'Company not returned'}
              </p>
              <h3 className="truncate text-base font-bold leading-snug text-white sm:text-lg">
                {role || 'Role not returned'}
              </h3>
              <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-400">
                {location && (
                  <span className="inline-flex items-center gap-1">
                    <MapPin className="h-3.5 w-3.5" />
                    {location}
                  </span>
                )}
                {workMode && (
                  <span className="inline-flex items-center gap-1">
                    <Briefcase className="h-3.5 w-3.5" />
                    {workMode}
                  </span>
                )}
                {salary && (
                  <span className="font-mono text-slate-300">
                    {salary}
                  </span>
                )}
              </div>
            </div>
          </div>
          {hasMatch && (
            <div className={`shrink-0 rounded-xl border px-3 py-1.5 text-center backdrop-blur-md ${matchBadgeStyle}`}>
              <div className="flex items-center justify-center gap-1 font-mono text-sm font-bold">
                <Sparkles className="h-3.5 w-3.5" />
                <span>{match}%</span>
              </div>
              <p className="text-[10px] uppercase tracking-wider opacity-85">Match</p>
            </div>
          )}
        </div>

        {!compact && description && (
          <p className="line-clamp-2 text-xs leading-relaxed text-slate-300/90 sm:text-sm">
            {description}
          </p>
        )}

        {outreachPitch && (
          <div className="rounded-xl border border-honey-300/15 bg-honey-300/[0.04] p-3">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-honey-200">
              AI outreach pitch
            </p>
            <p className="mt-1 text-xs leading-relaxed text-slate-300">{outreachPitch}</p>
          </div>
        )}

        {requiredSkills.length > 0 && (
          <div className="space-y-2">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Required Skills
            </p>
            <div className="flex flex-wrap gap-1.5">
              {requiredSkills.map((skill) => {
                const isMissing = missingSkills.some(
                  (missing) => missing.toLowerCase() === skill.toLowerCase()
                );
                return (
                  <span
                    key={skill}
                    className={`rounded-lg border px-2.5 py-1 text-xs font-medium ${
                      isMissing
                        ? 'border-white/10 bg-white/[0.04] text-slate-300'
                        : 'border-honey-300/20 bg-honey-300/[0.06] text-honey-100'
                    }`}
                  >
                    {skill}
                  </span>
                );
              })}
            </div>
          </div>
        )}

        {missingSkills.length > 0 && (
          <div className="space-y-1.5 rounded-xl border border-amber-400/20 bg-amber-500/[0.06] p-3">
            <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-amber-300">
              <AlertCircle className="h-3.5 w-3.5" />
              Missing Skills ({missingSkills.length})
            </p>
            <div className="flex flex-wrap gap-1.5">
              {missingSkills.map((skill) => (
                <span key={skill} className="rounded-md border border-amber-400/25 bg-amber-500/15 px-2 py-0.5 text-[11px] font-medium text-amber-200">
                  + {skill}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between gap-3 border-t border-white/[0.08] pt-3">
        {postedAt && (
          <span className="text-xs text-slate-400">{postedAt}</span>
        )}
        {typeof applyUrl === 'string' && /^https?:\/\//i.test(applyUrl) ? (
          <a
            href={applyUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded-xl border border-honey-100/40 bg-gradient-to-r from-honey-500 via-honey-300 to-honey-200 px-3.5 py-2 text-xs font-semibold text-void-950 transition hover:brightness-105"
          >
            Open application <ExternalLink className="h-4 w-4" />
          </a>
        ) : (
          <span className="text-xs text-slate-500">Apply link not returned</span>
        )}
      </div>
    </GlassCard>
  );
}
