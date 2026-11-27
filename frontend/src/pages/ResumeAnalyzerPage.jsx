import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  BriefcaseBusiness,
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
  if (!Array.isArray(value)) return [];
  return value
    .map((skill) => (typeof skill === 'string' ? skill : skill?.name ?? skill?.skill))
    .filter((skill) => typeof skill === 'string' && skill.length > 0);
}

export default function ResumeAnalyzerPage() {
  const { profile, analysis: savedAnalysis, saveAnalysis, clearWorkspace } = useWorkspace();
  const [form, setForm] = useState({
    name: profile?.name || '',
    target_role: profile?.targetRole || '',
    intensity_mode: profile?.intensityMode || 'Hell Mode',
    github_username: profile?.githubUsername || '',
    codeforces_handle: profile?.codeforcesHandle || '',
  });
  const [selectedFile, setSelectedFile] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState('');
  const currentAnalysis = savedAnalysis;

  const handleAnalyzeProfile = async (event) => {
    event.preventDefault();
    setUploadError('');
    setAnalyzing(true);
    setUploadProgress(0);

    try {
      const request = {
        name: form.name.trim(),
        target_role: form.target_role.trim(),
        intensity_mode: form.intensity_mode,
        github_username: form.github_username.trim(),
        codeforces_handle: form.codeforces_handle.trim(),
      };
      const result = await analyzeProfile(request, selectedFile, setUploadProgress);
      saveAnalysis(request, result);
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
    responseData?.verified_skills ?? responseData?.top_skills
  );
  const missingSkills = getSkillLabels(responseData?.missing_skills);
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
      subtitle="Create your live profile and request an analysis"
      user={profile}
      onClearWorkspace={clearWorkspace}
    >
      <div className="space-y-6 animate-fade-in-up">
        <section className="relative overflow-hidden rounded-[2rem] border border-honey-200/20 bg-[radial-gradient(ellipse_at_88%_0%,rgba(59,22,58,0.82),transparent_48%),linear-gradient(135deg,#1b111d,#0c090d_72%)] p-6 shadow-[0_30px_90px_rgba(0,0,0,0.42)] sm:p-9">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -right-10 -top-20 h-64 w-64 rounded-full border border-honey-200/10"
          />
          <div className="relative z-10 grid items-center gap-8 lg:grid-cols-[1fr_auto]">
            <div className="max-w-2xl">
              <p className="eyebrow"><FileSearch className="h-3.5 w-3.5" /> RESUME INTELLIGENCE</p>
              <h2 className="mt-4 text-3xl font-semibold leading-tight tracking-tight text-white sm:text-4xl">
                Make your experience
                <span className="block text-gradient">easy to recognize.</span>
              </h2>
              <p className="mt-4 max-w-xl text-sm leading-6 text-slate-300">
                Create a live profile using the Railway analysis endpoint. A resume PDF is optional;
                the displayed score and skills come only from the response.
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
            title="Analysis API Unavailable"
            message={uploadError}
          />
        )}

        <div className="grid gap-5 lg:grid-cols-12">
          <GlassCard glow="purple" className="space-y-5 lg:col-span-7">
            <div>
              <p className="eyebrow">YOUR SOURCE DOCUMENT</p>
              <h2 className="mt-2 text-xl font-semibold text-white">Resume input</h2>
              <p className="mt-2 text-sm leading-6 text-slate-400">
                Name and target role are required. Add your handles and an optional PDF to send all
                profile inputs in one multipart request.
              </p>
            </div>
            <div className="gold-rule" />
            <form onSubmit={handleAnalyzeProfile} className="space-y-5">
              <div className="grid gap-4 sm:grid-cols-2">
                <GlassInput
                  label="Full name"
                  icon={UserRound}
                  value={form.name}
                  onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                  required
                />
                <GlassInput
                  label="Target role"
                  icon={BriefcaseBusiness}
                  value={form.target_role}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, target_role: event.target.value }))
                  }
                  required
                />
                <GlassInput
                  label="Intensity mode"
                  as="select"
                  value={form.intensity_mode}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, intensity_mode: event.target.value }))
                  }
                >
                  <option value="Hell Mode">Hell Mode</option>
                  <option value="Normal Mode">Normal Mode</option>
                  <option value="Chill Mode">Chill Mode</option>
                </GlassInput>
                <GlassInput
                  label="GitHub username"
                  icon={Github}
                  value={form.github_username}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, github_username: event.target.value }))
                  }
                />
                <GlassInput
                  label="Codeforces handle"
                  icon={Code2}
                  value={form.codeforces_handle}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, codeforces_handle: event.target.value }))
                  }
                  containerClassName="sm:col-span-2"
                />
              </div>
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
              <GlassButton type="submit" loading={analyzing} icon={Sparkles}>
                Analyze Profile
              </GlassButton>
            </form>
          </GlassCard>

          <GlassCard className="relative overflow-hidden lg:col-span-5">
            <div className="absolute -right-12 -top-12 h-40 w-40 rounded-full bg-plum-700/20 blur-3xl" />
            <p className="relative eyebrow"><ScanSearch className="h-3.5 w-3.5" /> ANALYSIS FLOW</p>
            <h2 className="relative mt-2 text-xl font-semibold text-white">From document to direction</h2>
            <div className="relative mt-6 space-y-4">
              {[
                ['01', 'Choose your PDF', 'A resume file stays local until you submit it.'],
                ['02', 'Request analysis', 'The frontend sends the file to the configured API.'],
                ['03', 'Review returned insights', 'Scores and skills appear only when supplied by the backend.'],
              ].map(([step, title, detail], index) => (
                <div key={step} className="flex gap-3">
                  <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border text-xs font-mono ${
                    index === 0
                      ? 'border-honey-300/30 bg-honey-300/10 text-honey-200'
                      : 'border-plum-300/20 bg-plum-950/45 text-plum-200'
                  }`}>
                    {step}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-100">{title}</p>
                    <p className="mt-1 text-xs leading-5 text-slate-400">{detail}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="relative mt-6 flex items-center gap-2 rounded-xl border border-plum-300/15 bg-black/20 px-3 py-2.5 text-xs text-slate-400">
              <Sparkles className="h-4 w-4 text-honey-300" />
              No analysis is saved until a real API response is received.
            </div>
          </GlassCard>
        </div>

        {analyzing ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner size="lg" label="Analyzing your profile..." />
          </div>
        ) : currentAnalysis ? (
          <>
          <GlassCard glow="blue" className="space-y-5">
            <p className="eyebrow">LIVE SERVICE RESPONSE</p>
            <h2 className="text-xl font-semibold text-white">Backend analysis</h2>
            {(typeof readinessScore === 'number' || typeof readinessScore === 'string') && (
              <p className="text-2xl font-bold text-white">
                Readiness score: {readinessScore}
              </p>
            )}
            {typeof responseData?.summary === 'string' && (
              <p className="text-sm text-slate-300">{responseData.summary}</p>
            )}
            {profile?.user_id !== undefined && (
              <p className="font-mono text-xs text-slate-400">User ID: {profile.user_id}</p>
            )}
            <div className="grid gap-5 sm:grid-cols-2">
              <div>
                <h3 className="mb-2 text-sm font-semibold text-slate-200">Verified skills</h3>
                {topSkills.length ? (
                  <ul className="list-disc space-y-1 pl-5 text-sm text-slate-300">
                    {topSkills.map((skill) => <li key={skill}>{skill}</li>)}
                  </ul>
                ) : (
                  <p className="text-sm text-slate-400">No top skills were returned.</p>
                )}
              </div>
              <div>
                <h3 className="mb-2 text-sm font-semibold text-slate-200">Missing skills</h3>
                {missingSkills.length ? (
                  <ul className="list-disc space-y-1 pl-5 text-sm text-slate-300">
                    {missingSkills.map((skill) => <li key={skill}>{skill}</li>)}
                  </ul>
                ) : (
                  <p className="text-sm text-slate-400">No missing skills were returned.</p>
                )}
              </div>
            </div>
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
                  View Career Scout
                </GlassButton>
              </Link>
            </div>
            {roadmapError && (
              <p className="text-sm text-rose-300">{roadmapError}</p>
            )}
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
                  <p className="font-mono text-xs uppercase tracking-wider text-honey-200">
                    Capstone Mini-Project
                  </p>
                  <h3 className="text-lg font-semibold text-white">
                    {roadmap.recommended_project.title}
                  </h3>
                  {Array.isArray(roadmap.recommended_project.stack) && (
                    <div className="flex flex-wrap gap-2 pt-1">
                      {roadmap.recommended_project.stack.map((tech) => (
                        <span
                          key={tech}
                          className="rounded-lg border border-white/10 bg-white/5 px-2.5 py-0.5 font-mono text-xs text-slate-200"
                        >
                          {tech}
                        </span>
                      ))}
                    </div>
                  )}
                  {roadmap.recommended_project.why_it_helps && (
                    <p className="pt-1 text-sm text-slate-300">
                      {roadmap.recommended_project.why_it_helps}
                    </p>
                  )}
                </div>
              )}

              <div className="grid gap-4 md:grid-cols-2">
                {(roadmap.days || []).map((item) => (
                  <div
                    key={item.day}
                    className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 space-y-2"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="rounded-lg border border-honey-300/30 bg-honey-300/10 px-2.5 py-0.5 font-mono text-xs font-semibold text-honey-200">
                        Day {item.day}
                      </span>
                      <span className="text-xs font-medium text-plum-200">
                        {item.focus_skill}
                      </span>
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
            <div className="absolute inset-x-1/3 top-0 h-32 bg-plum-700/20 blur-3xl" />
            <div className="relative mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-honey-300/20 bg-honey-300/10 text-honey-200">
              <ScanSearch className="h-6 w-6" />
            </div>
            <h2 className="relative text-xl font-semibold text-white">Your analysis space is ready</h2>
            <p className="relative mx-auto max-w-xl text-sm leading-6 text-slate-400">
              Submit your name and target role to create a live profile. The optional PDF and
              handles are sent with the same profile-analysis request.
            </p>
            <Link to="/profile" className="relative inline-flex items-center gap-2 text-sm font-semibold text-honey-200 hover:text-white">
              Review local profile fields <ArrowRight className="h-4 w-4" />
            </Link>
          </GlassCard>
        )}
      </div>
    </AppLayout>
  );
}
