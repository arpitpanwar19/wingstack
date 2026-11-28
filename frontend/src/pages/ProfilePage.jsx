import React, { useEffect, useState } from 'react';
import {
  ArrowUpRight,
  BriefcaseBusiness,
  CheckCircle2,
  Cloud,
  Code2,
  Database,
  ExternalLink,
  FileText,
  Flame,
  Github,
  Lock,
  Pencil,
  ShieldCheck,
  Sparkles,
  User,
  X,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import AppLayout from '../components/AppLayout';
import GlassButton from '../components/GlassButton';
import GlassCard from '../components/GlassCard';
import GlassInput from '../components/GlassInput';
import Notification from '../components/Notification';
import ResumeUploader from '../components/ResumeUploader';
import { useWorkspace } from '../context/WorkspaceContext';
import { analyzeProfile, getProfileVault } from '../services/api';

const CONNECTOR_FIELDS = [
  { key: 'github_username', camel: 'githubUsername', label: 'GitHub', placeholder: 'arpitpanwar19', icon: Github },
  { key: 'leetcode_username', camel: 'leetcodeUsername', label: 'LeetCode', placeholder: 'leetcode_handle', icon: Code2 },
  { key: 'codeforces_handle', camel: 'codeforcesHandle', label: 'Codeforces', placeholder: 'codeforces_handle', icon: Code2 },
  { key: 'gfg_handle', camel: 'gfgHandle', label: 'GeeksforGeeks (GFG)', placeholder: 'gfg_username', icon: Code2 },
  { key: 'codechef_handle', camel: 'codechefHandle', label: 'CodeChef', placeholder: 'codechef_username', icon: Code2 },
  { key: 'atcoder_handle', camel: 'atcoderHandle', label: 'AtCoder', placeholder: 'atcoder_username', icon: Code2 },
  { key: 'hackerrank_handle', camel: 'hackerrankHandle', label: 'HackerRank', placeholder: 'hackerrank_username', icon: Code2 },
];

export default function ProfilePage() {
  const { profile, clearWorkspace, saveAnalysis, saveProfile } = useWorkspace();
  const hasLiveId = profile?.user_id !== undefined && profile?.user_id !== null && profile?.user_id !== '';

  // Read-only by default once a profile exists; unlocked only when user enters Edit mode
  const [isEditing, setIsEditing] = useState(!hasLiveId);
  const [selectedFile, setSelectedFile] = useState(null);
  const [saving, setSaving] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [notice, setNotice] = useState(null);

  const buildFormFromProfile = (p) => {
    const conn = p?.connectors || {};
    return {
      name: p?.name || '',
      target_role: p?.target_role || p?.targetRole || '',
      intensity_mode: p?.intensity_mode || p?.intensityMode || 'Hell Mode',
      github_username: conn.github_username || p?.githubUsername || p?.github_username || '',
      leetcode_username: conn.leetcode_username || p?.leetcodeUsername || p?.leetcode_username || '',
      codeforces_handle: conn.codeforces_handle || p?.codeforcesHandle || p?.codeforces_handle || '',
      gfg_handle: conn.gfg_handle || p?.gfgHandle || p?.gfg_handle || '',
      codechef_handle: conn.codechef_handle || p?.codechefHandle || p?.codechef_handle || '',
      atcoder_handle: conn.atcoder_handle || p?.atcoderHandle || p?.atcoder_handle || '',
      hackerrank_handle: conn.hackerrank_handle || p?.hackerrankHandle || p?.hackerrank_handle || '',
    };
  };

  const [form, setForm] = useState(() => buildFormFromProfile(profile));

  // Hydrate fresh DynamoDB record & S3 presigned URL on mount if user_id exists
  useEffect(() => {
    let active = true;
    if (!hasLiveId) return;
    getProfileVault(profile.user_id)
      .then((vaultData) => {
        if (!active || !vaultData) return;
        saveProfile({
          ...vaultData,
          targetRole: vaultData.target_role,
          intensityMode: vaultData.intensity_mode,
          githubUsername: vaultData.connectors?.github_username || '',
          codeforcesHandle: vaultData.connectors?.codeforces_handle || '',
          leetcodeUsername: vaultData.connectors?.leetcode_username || '',
          gfgHandle: vaultData.connectors?.gfg_handle || '',
          codechefHandle: vaultData.connectors?.codechef_handle || '',
          atcoderHandle: vaultData.connectors?.atcoder_handle || '',
          hackerrankHandle: vaultData.connectors?.hackerrank_handle || '',
        });
        setForm(buildFormFromProfile(vaultData));
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [hasLiveId, profile?.user_id]);

  const handleOpenEdit = () => {
    setForm(buildFormFromProfile(profile));
    setSelectedFile(null);
    setUploadProgress(0);
    setNotice(null);
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setForm(buildFormFromProfile(profile));
    setSelectedFile(null);
    setUploadProgress(0);
    setIsEditing(false);
  };

  const handleSaveVault = async (event) => {
    event.preventDefault();
    setNotice(null);
    setSaving(true);
    setUploadProgress(0);

    try {
      const payload = {
        ...form,
        name: form.name.trim(),
        target_role: form.target_role.trim(),
        existing_user_id: hasLiveId ? profile.user_id : undefined,
      };
      const result = await analyzeProfile(payload, selectedFile, setUploadProgress);
      saveAnalysis(payload, result);
      setIsEditing(false);
      setSelectedFile(null);
      setNotice({
        type: 'success',
        title: 'Profile & Connectors Locked in AWS Vault',
        message: result?.aws_vault?.dynamodb_synced
          ? 'Synced profile metadata to AWS DynamoDB and stored resume PDF in AWS S3.'
          : 'Profile & connectors verified and locked.',
      });
    } catch (err) {
      setNotice({
        type: 'error',
        title: 'Failed to Update Profile Vault',
        message: err?.message || 'Could not sync profile changes.',
      });
    } finally {
      setSaving(false);
    }
  };

  const activeConnectors = buildFormFromProfile(profile);
  const connectedCount = CONNECTOR_FIELDS.filter((c) => Boolean(activeConnectors[c.key])).length;

  return (
    <AppLayout
      title="Candidate Vault"
      subtitle="AWS DynamoDB & S3 backed identity, resume & coding connectors"
      user={profile}
      onClearWorkspace={clearWorkspace}
    >
      <div className="space-y-6 animate-fade-in-up">
        {/* Hero Header */}
        <section className="relative overflow-hidden rounded-[2rem] border border-honey-200/20 bg-[radial-gradient(ellipse_at_85%_0%,rgba(59,22,58,0.82),transparent_48%),linear-gradient(135deg,#1b111d,#0c090d_72%)] p-6 shadow-[0_30px_90px_rgba(0,0,0,0.42)] sm:p-9">
          <div className="relative z-10 flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
            <div className="max-w-2xl">
              <p className="eyebrow">
                {isEditing ? <Pencil className="h-3.5 w-3.5" /> : <Lock className="h-3.5 w-3.5" />}
                {isEditing ? ' EDIT MODE UNLOCKED' : ' VERIFIED CANDIDATE RECORD'}
              </p>
              <h2 className="mt-4 text-3xl font-semibold leading-tight tracking-tight text-white sm:text-4xl">
                {profile?.name || 'Configure your'}
                <span className="block text-gradient">
                  {profile?.target_role || profile?.targetRole || 'engineering profile.'}
                </span>
              </h2>
              <p className="mt-3 max-w-xl text-sm leading-6 text-slate-300">
                {isEditing
                  ? 'Complete your mandatory profile details, link all active coding arenas, and upload your resume PDF to lock your vault.'
                  : 'Your profile is locked in read-only mode to protect ATS & Career Scout consistency. Use Edit Profile & Connectors to update handles or replace your resume.'}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-3 rounded-2xl border border-honey-300/20 bg-black/30 px-4 py-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-honey-300/25 bg-honey-300/10 text-honey-200">
                  <Database className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-[9px] font-semibold tracking-[0.2em] text-slate-400">AWS VAULT ID</p>
                  <p className="mt-0.5 font-mono text-sm font-semibold text-honey-100">
                    {hasLiveId ? `#${profile.user_id}` : 'UNINITIALIZED'}
                  </p>
                </div>
              </div>

              {hasLiveId && !isEditing && (
                <GlassButton variant="primary" icon={Pencil} onClick={handleOpenEdit}>
                  Edit Profile & Connectors
                </GlassButton>
              )}
            </div>
          </div>
        </section>

        {notice && (
          <Notification
            type={notice.type}
            title={notice.title}
            message={notice.message}
            onClose={() => setNotice(null)}
          />
        )}

        {!isEditing && hasLiveId ? (
          /* -------------------- LOCKED READ-ONLY PROFESSIONAL VIEW -------------------- */
          <div className="grid gap-6 lg:grid-cols-12">
            {/* Core Identity & S3 Resume Vault */}
            <GlassCard glow="purple" className="space-y-6 lg:col-span-5">
              <div className="flex items-center justify-between border-b border-white/10 pb-4">
                <div>
                  <p className="eyebrow">IDENTITY & RESUME VAULT</p>
                  <h3 className="mt-1 text-lg font-semibold text-white">Mandatory Credentials</h3>
                </div>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-400/25 bg-emerald-400/10 px-3 py-1 text-[11px] font-medium text-emerald-200">
                  <Lock className="h-3 w-3" /> Read-Only
                </span>
              </div>

              <div className="space-y-4">
                <div className="rounded-xl border border-white/10 bg-black/25 p-3.5">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Full Name</p>
                  <p className="mt-1 text-base font-semibold text-white">{profile.name}</p>
                </div>

                <div className="rounded-xl border border-white/10 bg-black/25 p-3.5">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Target Role</p>
                  <p className="mt-1 text-base font-semibold text-honey-100">
                    {profile.target_role || profile.targetRole}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-xl border border-white/10 bg-black/25 p-3.5">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Intensity Mode</p>
                    <p className="mt-1 font-mono text-sm font-semibold text-plum-100">
                      {profile.intensity_mode || profile.intensityMode || 'Hell Mode'}
                    </p>
                  </div>
                  <div className="rounded-xl border border-white/10 bg-black/25 p-3.5">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">ATS Readiness</p>
                    <p className="mt-1 font-mono text-sm font-bold text-emerald-300">
                      {profile.readiness_score ?? 75} / 100
                    </p>
                  </div>
                </div>

                {/* AWS S3 Stored Resume Box */}
                <div className="rounded-2xl border border-honey-300/20 bg-honey-300/[0.04] p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="inline-flex items-center gap-2 text-xs font-semibold text-honey-200">
                      <Cloud className="h-4 w-4" /> AWS S3 Resume Vault
                    </span>
                    <span className="font-mono text-[10px] text-slate-400">ap-southeast-2</span>
                  </div>
                  <p className="truncate font-mono text-xs text-slate-300">
                    {profile.resume_filename || 'No PDF uploaded yet'}
                  </p>
                  {profile.resume_url ? (
                    <a
                      href={profile.resume_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1.5 rounded-xl border border-honey-300/30 bg-honey-300/10 px-3.5 py-2 text-xs font-semibold text-honey-100 transition hover:bg-honey-300/20"
                    >
                      <FileText className="h-3.5 w-3.5" />
                      Open Stored Resume PDF
                      <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  ) : (
                    <p className="text-xs text-slate-400">
                      Upload a PDF in Edit Profile & Connectors to store it in S3.
                    </p>
                  )}
                </div>
              </div>

              <div className="flex flex-wrap gap-3 pt-1">
                <Link to="/career-scout">
                  <GlassButton variant="secondary" iconRight={ArrowUpRight}>
                    Open Career Scout
                  </GlassButton>
                </Link>
                <Link to="/resume-analyzer">
                  <GlassButton variant="ghost" iconRight={ArrowUpRight}>
                    View Telemetry Report
                  </GlassButton>
                </Link>
              </div>
            </GlassCard>

            {/* All 7 Platform Connectors (Read-Only Grid) */}
            <GlassCard glow="blue" className="space-y-6 lg:col-span-7">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-4">
                <div>
                  <p className="eyebrow">PLATFORM CONNECTORS ({connectedCount}/7 LINKED)</p>
                  <h3 className="mt-1 text-lg font-semibold text-white">Competitive & Developer Handles</h3>
                </div>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-sky-400/25 bg-sky-400/10 px-3 py-1 font-mono text-[11px] text-sky-200">
                  <ShieldCheck className="h-3.5 w-3.5" /> DynamoDB Synced
                </span>
              </div>

              <div className="grid gap-3.5 sm:grid-cols-2">
                {CONNECTOR_FIELDS.map(({ key, label, icon: Icon }) => {
                  const handle = activeConnectors[key];
                  return (
                    <div
                      key={key}
                      className={`flex items-center justify-between rounded-2xl border p-4 ${
                        handle
                          ? 'border-emerald-400/20 bg-emerald-500/[0.04]'
                          : 'border-white/10 bg-black/20'
                      }`}
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div
                          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border ${
                            handle
                              ? 'border-emerald-400/30 bg-emerald-400/10 text-emerald-200'
                              : 'border-white/10 bg-white/5 text-slate-500'
                          }`}
                        >
                          <Icon className="h-4 w-4" />
                        </div>
                        <div className="min-w-0">
                          <p className="text-xs font-medium text-slate-400">{label}</p>
                          <p className="truncate font-mono text-sm font-semibold text-white">
                            {handle ? `@${handle}` : 'Not linked'}
                          </p>
                        </div>
                      </div>
                      <span
                        className={`shrink-0 rounded-full px-2.5 py-0.5 text-[10px] font-semibold ${
                          handle
                            ? 'border border-emerald-400/30 bg-emerald-400/10 text-emerald-200'
                            : 'border border-white/10 bg-white/5 text-slate-500'
                        }`}
                      >
                        {handle ? 'ACTIVE' : 'EMPTY'}
                      </span>
                    </div>
                  );
                })}
              </div>

              <div className="flex items-center justify-between rounded-2xl border border-plum-300/20 bg-black/25 px-4 py-3.5">
                <p className="text-xs text-slate-300">
                  Need to add a missing coding handle or upload an updated resume?
                </p>
                <GlassButton size="sm" variant="secondary" icon={Pencil} onClick={handleOpenEdit}>
                  Edit Connectors
                </GlassButton>
              </div>
            </GlassCard>
          </div>
        ) : (
          /* -------------------- DEDICATED EDIT PROFILE & CONNECTORS SECTION -------------------- */
          <GlassCard glow="purple" className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 pb-4">
              <div>
                <p className="eyebrow">EDIT PROFILE & CONNECTORS</p>
                <h3 className="mt-1 text-xl font-semibold text-white">
                  Mandatory Details, Coding Connectors & Resume PDF
                </h3>
              </div>
              {hasLiveId && (
                <GlassButton variant="ghost" size="sm" icon={X} onClick={handleCancelEdit}>
                  Cancel & Keep Locked
                </GlassButton>
              )}
            </div>

            <form onSubmit={handleSaveVault} className="space-y-6">
              {/* Mandatory Profile Details */}
              <div className="space-y-3">
                <p className="text-xs font-semibold uppercase tracking-wider text-honey-200">
                  1. Mandatory Identity & Target Role
                </p>
                <div className="grid gap-4 rounded-2xl border border-plum-300/15 bg-black/20 p-4 sm:grid-cols-3 sm:p-5">
                  <GlassInput
                    label="Full Name *"
                    icon={User}
                    placeholder="Arpit Panwar"
                    value={form.name}
                    onChange={(e) => setForm((c) => ({ ...c, name: e.target.value }))}
                    required
                  />
                  <GlassInput
                    label="Target Role *"
                    icon={BriefcaseBusiness}
                    placeholder="Software Engineer Intern"
                    value={form.target_role}
                    onChange={(e) => setForm((c) => ({ ...c, target_role: e.target.value }))}
                    required
                  />
                  <GlassInput
                    label="Intensity Mode *"
                    as="select"
                    icon={Flame}
                    value={form.intensity_mode}
                    onChange={(e) => setForm((c) => ({ ...c, intensity_mode: e.target.value }))}
                  >
                    <option value="Hell Mode">Hell Mode</option>
                    <option value="Normal Mode">Normal Mode</option>
                    <option value="Chill Mode">Chill Mode</option>
                  </GlassInput>
                </div>
              </div>

              {/* All 7 Mandatory/Core Platform Connectors */}
              <div className="space-y-3">
                <p className="text-xs font-semibold uppercase tracking-wider text-honey-200">
                  2. Platform Connectors (GitHub, LeetCode, Codeforces, GFG, CodeChef, AtCoder, HackerRank)
                </p>
                <div className="grid gap-4 rounded-2xl border border-plum-300/15 bg-black/20 p-4 sm:grid-cols-2 lg:grid-cols-3 sm:p-5">
                  {CONNECTOR_FIELDS.map(({ key, label, placeholder, icon }) => (
                    <GlassInput
                      key={key}
                      label={label}
                      icon={icon}
                      placeholder={placeholder}
                      value={form[key]}
                      onChange={(e) => setForm((c) => ({ ...c, [key]: e.target.value }))}
                    />
                  ))}
                </div>
              </div>

              {/* AWS S3 Resume PDF Upload */}
              <div className="space-y-3">
                <p className="text-xs font-semibold uppercase tracking-wider text-honey-200">
                  3. Resume PDF (Stored Encrypted in AWS S3)
                </p>
                <ResumeUploader
                  selectedFile={selectedFile}
                  onFileSelect={(file) => setSelectedFile(file)}
                  onClear={() => {
                    setSelectedFile(null);
                    setUploadProgress(0);
                  }}
                  isUploading={saving}
                  uploadProgress={uploadProgress}
                />
                {selectedFile ? (
                  <p className="flex items-center gap-2 text-xs text-emerald-300">
                    <CheckCircle2 className="h-4 w-4" />
                    New resume ready for AWS S3 upload: <strong>{selectedFile.name}</strong>
                  </p>
                ) : profile?.resume_filename ? (
                  <p className="text-xs text-slate-400">
                    Currently stored in S3: <strong className="text-slate-200">{profile.resume_filename}</strong> (leave empty to keep existing PDF)
                  </p>
                ) : null}
              </div>

              <div className="flex flex-wrap items-center gap-3 pt-2">
                <GlassButton type="submit" variant="primary" size="lg" loading={saving} icon={Sparkles}>
                  Save to AWS Vault & Lock Profile
                </GlassButton>
                {hasLiveId && (
                  <GlassButton type="button" variant="ghost" onClick={handleCancelEdit}>
                    Cancel
                  </GlassButton>
                )}
              </div>
            </form>
          </GlassCard>
        )}
      </div>
    </AppLayout>
  );
}
