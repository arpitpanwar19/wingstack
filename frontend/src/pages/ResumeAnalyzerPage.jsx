import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  ArrowRight,
  BriefcaseBusiness,
  CheckCircle2,
  Code2,
  FileSearch,
  FileText,
  Github,
  ScanSearch,
  Sparkles,
  UserRound,
} from 'lucide-react';
import AppLayout from '../components/AppLayout';
import GlassButton from '../components/GlassButton';
import GlassCard from '../components/GlassCard';
import GlassInput from '../components/GlassInput';
import LoadingSpinner from '../components/LoadingSpinner';
import Notification from '../components/Notification';
import ResumeUploader from '../components/ResumeUploader';
import { useWorkspace } from '../context/WorkspaceContext';
import { analyzeProfile, generateSprintRoadmap } from '../services/api';

function getSkillLabels(value) {
  if (Array.isArray(value)) {
    return value
      .map((skill) => (typeof skill === 'string' ? skill : skill?.name ?? skill?.skill))
      .filter((skill) => typeof skill === 'string' && skill.length > 0);
  }
  if (value && typeof value === 'object') {
    return Object.values(value).flat().filter((s) => typeof s === 'string' && s.length > 0);
  }
  return [];
}

export default function ResumeAnalyzerPage() {
  const { profile, analysis: savedAnalysis, saveAnalysis, clearWorkspace } = useWorkspace();
  const [form, setForm] = useState({
    name: profile?.name || '',
    target_role: profile?.targetRole || '',
    intensity_mode: profile?.intensityMode || 'Hell Mode',
    github_username: profile?.githubUsername || '',
    codeforces_handle: profile?.codeforcesHandle || '',
    leetcode_username: profile?.leetcodeUsername || '',
    gfg_handle: profile?.gfgHandle || '',
    codechef_handle: profile?.codechefHandle || '',
    atcoder_handle: profile?.atcoderHandle || '',
    hackerrank_handle: profile?.hackerrankHandle || '',
  });
  const [selectedFile, setSelectedFile] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState('');
  const [submitBanner, setSubmitBanner] = useState('');
  const currentAnalysis = savedAnalysis;

  const handleAnalyzeProfile = async (event) => {
    event.preventDefault();
    setUploadError('');
    setSubmitBanner('');
    setAnalyzing(true);
    setUploadProgress(0);

    try {
      const request = {
        name: form.name.trim(),
        target_role: form.target_role.trim(),
        intensity_mode: form.intensity_mode,
        github_username: form.github_username.trim(),
        codeforces_handle: form.codeforces_handle.trim(),
        leetcode_username: form.leetcode_username.trim(),
        gfg_handle: form.gfg_handle.trim(),
        codechef_handle: form.codechef_handle.trim(),
        atcoder_handle: form.atcoder_handle.trim(),
        hackerrank_handle: form.hackerrank_handle.trim(),
      };
      const result = await analyzeProfile(request, selectedFile, setUploadProgress);
      saveAnalysis(request, result);
      setSubmitBanner(
        selectedFile
          ? `Submitted "${selectedFile.name}" (${result?.resume_chars || 0} chars parsed) + live coding profiles!`
          : 'Submitted live coding & developer profiles for real-time ATS evaluation!'
      );
    } catch (requestError) {
      setUploadError(requestError?.message || 'Resume upload or analysis failed.');
    } finally {
      setAnalyzing(false);
    }
  };

  const responseData =
    currentAnalysis?.analysis && typeof currentAnalysis.analysis === 'object'
      ? currentAnalysis.analysis
      : currentAnalysis;
  const readinessScore = responseData?.readiness_score;
  const topSkills = getSkillLabels(
    responseData?.verified_skills ?? responseData?.verified_skills_by_category ?? responseData?.top_skills
  );
  const missingSkills = getSkillLabels(
    responseData?.missing_skills ?? responseData?.missing_keywords
  );
  const codingStats = responseData?.coding_stats || {};
  const timeline = Array.isArray(responseData?.activity_timeline) ? responseData.activity_timeline : [];
  const maxDaily = Math.max(1, ...timeline.map((d) => d.total || 0));
  const suggestions = Array.isArray(responseData?.resume_suggestions) ? responseData.resume_suggestions : [];

  const [roadmap, setRoadmap] = useState(null);
  const [generatingRoadmap, setGeneratingRoadmap] = useState(false);
  const [roadmapError, setRoadmapError] = useState('');

  const handleGenerateRoadmap = async () => {
    setRoadmapError('');
    setGeneratingRoadmap(true);
    try {
      const data = await generateSprintRoadmap({
        target_role: form.target_role.trim() || profile?.target_role || 'Software Engineer',
        missing_skills: missingSkills,
        intensity_mode: form.intensity_mode || 'Normal Mode',
      });
      setRoadmap(data);
    } catch (err) {
      setRoadmapError(err?.response?.data?.detail || err?.message || 'Failed to generate 14-day sprint roadmap.');
    } finally {
      setGeneratingRoadmap(false);
    }
  };

  return (
    <AppLayout
      title="Readiness Analysis"
      subtitle="Multi-platform live telemetry, resume ATS & 14-day sprint engine"
      user={profile}
      onClearWorkspace={clearWorkspace}
    >
      <div className="space-y-6 animate-fade-in-up">
        <section className="relative overflow-hidden rounded-[2rem] border border-honey-200/20 bg-[radial-gradient(ellipse_at_88%_0%,rgba(59,22,58,0.82),transparent_48%),linear-gradient(135deg,#1b111d,#0c090d_72%)] p-6 shadow-[0_30px_90px_rgba(0,0,0,0.42)] sm:p-9">
          <div className="relative z-10 grid items-center gap-8 lg:grid-cols-[1fr_auto]">
            <div className="max-w-2xl">
              <p className="eyebrow"><FileSearch className="h-3.5 w-3.5" /> MULTI-PLATFORM RESUME & CODING TELEMETRY</p>
              <h2 className="mt-4 text-3xl font-semibold leading-tight tracking-tight text-white sm:text-4xl">
                Real-time proof across
                <span className="block text-gradient">every coding arena.</span>
              </h2>
              <p className="mt-4 max-w-xl text-sm leading-6 text-slate-300">
                Upload your resume PDF and connect GitHub, LeetCode, Codeforces, GeeksforGeeks, CodeChef, AtCoder, and HackerRank for live ATS scoring and daily activity graphs.
              </p>
            </div>
            <div className="hidden h-36 w-36 items-center justify-center rounded-full border border-honey-200/20 bg-black/20 text-honey-200 shadow-[0_0_70px_rgba(59,22,58,0.75)] lg:flex">
              <div className="flex h-24 w-24 items-center justify-center rounded-full border border-plum-300/25 bg-plum-900/35">
                <FileText className="h-9 w-9" />
              </div>
            </div>
          </div>
        </section>

        {uploadError && (
          <Notification
            type="error"
            title="Analysis API Error"
            message={uploadError}
          />
        )}

        {submitBanner && (
          <Notification
            type="success"
            title="Resume & Profiles Processed"
            message={submitBanner}
          />
        )}

        <div className="grid gap-5 lg:grid-cols-12">
          <GlassCard glow="purple" className="space-y-5 lg:col-span-8">
            <div>
              <p className="eyebrow">REAL-TIME PROFILE & RESUME INPUTS</p>
              <h2 className="mt-2 text-xl font-semibold text-white">Connect handles & upload resume PDF</h2>
            </div>
            <div className="gold-rule" />
            <form onSubmit={handleAnalyzeProfile} className="space-y-5">
              <div className="grid gap-4 sm:grid-cols-2">
                <GlassInput
                  label="Full name *"
                  icon={UserRound}
                  value={form.name}
                  onChange={(e) => setForm((c) => ({ ...c, name: e.target.value }))}
                  required
                />
                <GlassInput
                  label="Target role *"
                  icon={BriefcaseBusiness}
                  placeholder="e.g. Software Engineer Intern"
                  value={form.target_role}
                  onChange={(e) => setForm((c) => ({ ...c, target_role: e.target.value }))}
                  required
                />
                <GlassInput
                  label="Intensity mode"
                  as="select"
                  value={form.intensity_mode}
                  onChange={(e) => setForm((c) => ({ ...c, intensity_mode: e.target.value }))}
                >
                  <option value="Hell Mode">Hell Mode</option>
                  <option value="Normal Mode">Normal Mode</option>
                  <option value="Chill Mode">Chill Mode</option>
                </GlassInput>
                <GlassInput
                  label="GitHub username"
                  icon={Github}
                  placeholder="arpitpanwar19"
                  value={form.github_username}
                  onChange={(e) => setForm((c) => ({ ...c, github_username: e.target.value }))}
                />
                <GlassInput
                  label="LeetCode username"
                  icon={Code2}
                  placeholder="leetcode_handle"
                  value={form.leetcode_username}
                  onChange={(e) => setForm((c) => ({ ...c, leetcode_username: e.target.value }))}
                />
                <GlassInput
                  label="Codeforces handle"
                  icon={Code2}
                  placeholder="codeforces_handle"
                  value={form.codeforces_handle}
                  onChange={(e) => setForm((c) => ({ ...c, codeforces_handle: e.target.value }))}
                />
                <GlassInput
                  label="GeeksforGeeks (GFG) handle"
                  icon={Code2}
                  placeholder="gfg_username"
                  value={form.gfg_handle}
                  onChange={(e) => setForm((c) => ({ ...c, gfg_handle: e.target.value }))}
                />
                <GlassInput
                  label="CodeChef handle"
                  icon={Code2}
                  placeholder="codechef_username"
                  value={form.codechef_handle}
                  onChange={(e) => setForm((c) => ({ ...c, codechef_handle: e.target.value }))}
                />
                <GlassInput
                  label="AtCoder handle"
                  icon={Code2}
                  placeholder="atcoder_username"
                  value={form.atcoder_handle}
                  onChange={(e) => setForm((c) => ({ ...c, atcoder_handle: e.target.value }))}
                />
                <GlassInput
                  label="HackerRank handle"
                  icon={Code2}
                  placeholder="hackerrank_username"
                  value={form.hackerrank_handle}
                  onChange={(e) => setForm((c) => ({ ...c, hackerrank_handle: e.target.value }))}
                />
              </div>

              <div className="space-y-2">
                <ResumeUploader
                  selectedFile={selectedFile}
                  onFileSelect={(file) => {
                    setSelectedFile(file);
                    setUploadError('');
                  }}
                  onClear={() => {
                    setSelectedFile(null);
                    setUploadError('');
                    setUploadProgress(0);
                  }}
                  isUploading={analyzing}
                  uploadProgress={uploadProgress}
                />
                {selectedFile && (
                  <p className="flex items-center gap-2 text-xs text-emerald-300">
                    <CheckCircle2 className="h-4 w-4" />
                    Ready to submit resume: <strong>{selectedFile.name}</strong>
                  </p>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-3 pt-1">
                <GlassButton type="submit" variant="primary" size="lg" loading={analyzing} icon={Sparkles}>
                  {selectedFile ? 'Submit Resume & Analyze All Profiles' : 'Submit & Analyze Live Profiles'}
                </GlassButton>
              </div>
            </form>
          </GlassCard>

          <GlassCard className="relative overflow-hidden lg:col-span-4 space-y-4">
            <p className="relative eyebrow"><ScanSearch className="h-3.5 w-3.5" /> LIVE SIGNAL SOURCES</p>
            <h2 className="relative text-xl font-semibold text-white">7 Coding Arenas + ATS</h2>
            <p className="text-xs leading-5 text-slate-400">
              Every handle you enter is queried live on submission to compute your real-time activity timeline and ATS match score:
            </p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {['GitHub Commits', 'LeetCode GraphQL', 'Codeforces API', 'GFG Profile', 'CodeChef Rating', 'AtCoder AC', 'HackerRank Badges', 'PDF ATS Parser'].map((item) => (
                <div key={item} className="rounded-xl border border-honey-200/10 bg-black/25 px-3 py-2 text-slate-200">
                  {item}
                </div>
              ))}
            </div>
          </GlassCard>
        </div>

        {analyzing ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner size="lg" label="Fetching live stats across GitHub, LeetCode, Codeforces, GFG, CodeChef, AtCoder & parsing resume..." />
          </div>
        ) : currentAnalysis ? (
          <>
          <GlassCard glow="blue" className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="eyebrow">LIVE TELEMETRY & ATS VERDICT</p>
                <h2 className="mt-1 text-2xl font-bold text-white">
                  Readiness score: <span className="text-honey-200">{readinessScore}/100</span>
                </h2>
              </div>
              {profile?.user_id !== undefined && (
                <span className="rounded-full border border-honey-300/25 bg-honey-300/10 px-3 py-1 font-mono text-xs text-honey-100">
                  User ID: {profile.user_id} {responseData?.resume_parsed ? '• PDF Parsed ✓' : ''}
                </span>
              )}
            </div>

            {typeof responseData?.summary === 'string' && (
              <p className="text-sm leading-6 text-slate-300">{responseData.summary}</p>
            )}

            {/* Live Multi-Platform Coding Metrics */}
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
              <div className="rounded-xl border border-white/10 bg-black/25 p-3">
                <p className="text-[10px] text-slate-400">GITHUB REPOS</p>
                <p className="mt-1 font-mono text-lg font-bold text-white">{codingStats.github_repos ?? 0}</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-black/25 p-3">
                <p className="text-[10px] text-slate-400">LEETCODE</p>
                <p className="mt-1 font-mono text-lg font-bold text-amber-300">{codingStats.lc_solved ?? 0} AC</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-black/25 p-3">
                <p className="text-[10px] text-slate-400">CODEFORCES</p>
                <p className="mt-1 font-mono text-lg font-bold text-sky-300">{codingStats.cf_rating || codingStats.cf_solved || 0}</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-black/25 p-3">
                <p className="text-[10px] text-slate-400">GFG SOLVED</p>
                <p className="mt-1 font-mono text-lg font-bold text-emerald-300">{codingStats.gfg_solved ?? 0}</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-black/25 p-3">
                <p className="text-[10px] text-slate-400">CODECHEF</p>
                <p className="mt-1 font-mono text-lg font-bold text-orange-300">{codingStats.cc_rating || 0}</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-black/25 p-3">
                <p className="text-[10px] text-slate-400">ATCODER</p>
                <p className="mt-1 font-mono text-lg font-bold text-purple-300">{codingStats.ac_solved ?? 0} AC</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-black/25 p-3">
                <p className="text-[10px] text-slate-400">HACKERRANK</p>
                <p className="mt-1 font-mono text-lg font-bold text-teal-300">{codingStats.hr_badges ?? 0} Badges</p>
              </div>
            </div>

            {/* Real-Time 14-Day Daily Activity Graph */}
            {timeline.length > 0 && (
              <div className="rounded-2xl border border-honey-200/15 bg-black/30 p-4 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-honey-200">
                    <Activity className="h-4 w-4" /> Real-Time 14-Day Daily Activity Graph (GitHub + LeetCode + Codeforces)
                  </p>
                  <div className="flex items-center gap-3 text-[11px] text-slate-400">
                    <span className="inline-flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-emerald-400" /> GitHub</span>
                    <span className="inline-flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-amber-400" /> LeetCode</span>
                    <span className="inline-flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-sky-400" /> Codeforces</span>
                  </div>
                </div>
                <div className="grid grid-cols-14 gap-1.5 items-end h-28 pt-3" style={{ gridTemplateColumns: 'repeat(14, minmax(0, 1fr))' }}>
                  {timeline.map((day) => {
                    const pct = day.total > 0 ? Math.max(14, Math.round((day.total / maxDaily) * 100)) : 6;
                    return (
                      <div key={day.date} className="flex flex-col items-center gap-1 h-full justify-end" title={`${day.date}: GH ${day.github}, LC ${day.leetcode}, CF ${day.codeforces}`}>
                        <span className="text-[9px] font-mono text-slate-400">{day.total || ''}</span>
                        <div className="w-full flex flex-col justify-end rounded-t-md overflow-hidden bg-white/5" style={{ height: `${pct}%` }}>
                          {day.github > 0 && <div style={{ flex: day.github }} className="bg-emerald-400/90 w-full" />}
                          {day.leetcode > 0 && <div style={{ flex: day.leetcode }} className="bg-amber-400/90 w-full" />}
                          {day.codeforces > 0 && <div style={{ flex: day.codeforces }} className="bg-sky-400/90 w-full" />}
                        </div>
                        <span className="text-[9px] font-mono text-slate-500">{day.label}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="grid gap-5 sm:grid-cols-2">
              <div className="rounded-2xl border border-emerald-400/15 bg-emerald-500/[0.04] p-4">
                <h3 className="mb-3 text-sm font-semibold text-emerald-200">Verified skills ({topSkills.length})</h3>
                {topSkills.length ? (
                  <div className="flex flex-wrap gap-2">
                    {topSkills.map((skill) => (
                      <span key={skill} className="rounded-lg border border-emerald-400/25 bg-emerald-400/10 px-2.5 py-1 text-xs font-medium text-emerald-100">
                        {skill}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-400">No verified skills returned.</p>
                )}
              </div>
              <div className="rounded-2xl border border-amber-400/15 bg-amber-500/[0.04] p-4">
                <h3 className="mb-3 text-sm font-semibold text-amber-200">Missing ATS skills ({missingSkills.length})</h3>
                {missingSkills.length ? (
                  <div className="flex flex-wrap gap-2">
                    {missingSkills.map((skill) => (
                      <span key={skill} className="rounded-lg border border-amber-400/25 bg-amber-400/10 px-2.5 py-1 text-xs font-medium text-amber-100">
                        + {skill}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-400">No missing skills returned.</p>
                )}
              </div>
            </div>

            {suggestions.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-honey-200">ATS Resume Bullet Upgrades</h3>
                {suggestions.map((s, idx) => (
                  <div key={idx} className="rounded-xl border border-white/10 bg-black/25 p-3.5 text-xs space-y-1.5">
                    <p className="text-slate-400 line-through">{s.original_bullet}</p>
                    <p className="text-emerald-200 font-medium">{s.improved_bullet}</p>
                    <p className="text-slate-400">{s.reason}</p>
                  </div>
                ))}
              </div>
            )}

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <GlassButton
                type="button"
                onClick={handleGenerateRoadmap}
                loading={generatingRoadmap}
                icon={Sparkles}
              >
                {roadmap ? 'Regenerate 14-Day AI Sprint' : 'Generate 14-Day AI Sprint Roadmap'}
              </GlassButton>
              <Link to="/career-scout">
                <GlassButton variant="secondary" iconRight={ArrowRight}>
                  View Fresh Career Scout Roles
                </GlassButton>
              </Link>
            </div>
            {roadmapError && <p className="text-sm text-rose-300">{roadmapError}</p>}
          </GlassCard>

          {roadmap && (
            <GlassCard glow="purple" className="space-y-6">
              <div className="flex flex-wrap items-start justify-between gap-4 border-b border-white/10 pb-4">
                <div>
                  <p className="eyebrow"><Sparkles className="h-3.5 w-3.5" /> AI SPRINT ROADMAP</p>
                  <h2 className="mt-2 text-2xl font-semibold text-white">
                    {roadmap.sprint_title || '14-Day Skill Gap Sprint'}
                  </h2>
                </div>
                <span className="rounded-full border border-honey-300/30 bg-honey-300/10 px-3 py-1 font-mono text-xs text-honey-200">
                  {form.intensity_mode || 'Normal Mode'}
                </span>
              </div>

              {roadmap.recommended_project && (
                <div className="rounded-2xl border border-honey-300/20 bg-honey-300/5 p-5 space-y-2">
                  <p className="font-mono text-xs uppercase tracking-wider text-honey-200">Capstone Mini-Project</p>
                  <h3 className="text-lg font-semibold text-white">{roadmap.recommended_project.title}</h3>
                  {Array.isArray(roadmap.recommended_project.stack) && (
                    <div className="flex flex-wrap gap-2 pt-1">
                      {roadmap.recommended_project.stack.map((tech) => (
                        <span key={tech} className="rounded-lg border border-white/10 bg-white/5 px-2.5 py-0.5 font-mono text-xs text-slate-200">
                          {tech}
                        </span>
                      ))}
                    </div>
                  )}
                  {roadmap.recommended_project.why_it_helps && (
                    <p className="pt-1 text-sm text-slate-300">{roadmap.recommended_project.why_it_helps}</p>
                  )}
                </div>
              )}

              <div className="grid gap-4 md:grid-cols-2">
                {(roadmap.days || []).map((item) => (
                  <div key={item.day} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 space-y-2">
                    <div className="flex items-center justify-between gap-2">
                      <span className="rounded-lg border border-honey-300/30 bg-honey-300/10 px-2.5 py-0.5 font-mono text-xs font-semibold text-honey-200">
                        Day {item.day}
                      </span>
                      <span className="text-xs font-medium text-plum-200">{item.focus_skill}</span>
                    </div>
                    <p className="text-sm font-medium text-white">{item.task}</p>
                    <p className="text-xs text-slate-400">
                      <span className="font-semibold text-slate-300">Deliverable:</span> {item.deliverable}
                    </p>
                  </div>
                ))}
              </div>
            </GlassCard>
          )}
          </>
        ) : (
          <GlassCard glow="purple" className="relative space-y-3 overflow-hidden py-12 text-center">
            <div className="relative mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-honey-300/20 bg-honey-300/10 text-honey-200">
              <ScanSearch className="h-6 w-6" />
            </div>
            <h2 className="relative text-xl font-semibold text-white">Your analysis space is ready</h2>
            <p className="relative mx-auto max-w-xl text-sm leading-6 text-slate-400">
              Enter your handles and optional resume PDF above, then click Submit to fetch real-time stats across all 7 platforms.
            </p>
          </GlassCard>
        )}
      </div>
    </AppLayout>
  );
}
