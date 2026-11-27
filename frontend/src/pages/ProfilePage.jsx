import React, { useState } from 'react';
import { ArrowUpRight, BriefcaseBusiness, Code2, Flame, Github, Save, User } from 'lucide-react';
import { Link } from 'react-router-dom';
import AppLayout from '../components/AppLayout';
import GlassButton from '../components/GlassButton';
import GlassCard from '../components/GlassCard';
import GlassInput from '../components/GlassInput';
import Notification from '../components/Notification';
import ProfileCard from '../components/ProfileCard';
import { useWorkspace } from '../context/WorkspaceContext';

export default function ProfilePage() {
  const { profile, clearWorkspace, saveProfile } = useWorkspace();
  const [form, setForm] = useState({
    name: profile?.name || '',
    targetRole: profile?.targetRole || '',
    intensityMode: profile?.intensityMode || 'Hell Mode',
    githubUsername: profile?.githubUsername || '',
    codeforcesHandle: profile?.codeforcesHandle || '',
  });
  const [notice, setNotice] = useState(null);

  const handleSaveProfile = (event) => {
    event.preventDefault();
    saveProfile(form);
    setNotice({
      type: 'success',
      title: 'Saved in this browser',
      message: 'Run profile analysis to send these fields to the live API and refresh your user ID.',
    });
  };

  const displayedProfile = { ...profile, ...form };
  const hasLiveId = profile?.user_id !== undefined && profile?.user_id !== null;

  return (
    <AppLayout
      title="Profile"
      subtitle="Profile-analysis inputs for your live workspace"
      user={displayedProfile}
      onClearWorkspace={clearWorkspace}
    >
      <div className="space-y-6 animate-fade-in-up">
        <section className="relative overflow-hidden rounded-[2rem] border border-honey-200/20 bg-[radial-gradient(ellipse_at_85%_0%,rgba(59,22,58,0.82),transparent_48%),linear-gradient(135deg,#1b111d,#0c090d_72%)] p-6 shadow-[0_30px_90px_rgba(0,0,0,0.42)] sm:p-9">
          <div className="relative z-10 flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
            <div className="max-w-2xl">
              <p className="eyebrow"><User className="h-3.5 w-3.5" /> YOUR WORKSPACE PROFILE</p>
              <h2 className="mt-4 text-3xl font-semibold leading-tight tracking-tight text-white sm:text-4xl">
                The details behind
                <span className="block text-gradient">your next chapter.</span>
              </h2>
              <p className="mt-3 max-w-xl text-sm leading-6 text-slate-300">
                These fields are saved locally. Submit them through profile analysis to send them to
                Railway and receive a live user ID.
              </p>
            </div>
            <div className="flex items-center gap-3 rounded-2xl border border-honey-300/20 bg-black/25 px-4 py-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-honey-300/25 bg-honey-300/10 text-honey-200">
                <User className="h-5 w-5" />
              </div>
              <div>
                <p className="text-[9px] font-semibold tracking-[0.2em] text-slate-500">
                  {hasLiveId ? 'LIVE USER ID' : 'WORKSPACE STATUS'}
                </p>
                <p className="mt-1 text-sm font-medium text-honey-100">
                  {hasLiveId ? profile.user_id : 'Analysis required'}
                </p>
              </div>
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

        {(displayedProfile.name ||
          displayedProfile.githubUsername ||
          displayedProfile.codeforcesHandle) && <ProfileCard user={displayedProfile} />}

        <GlassCard glow="purple" className="space-y-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="eyebrow">PROFILE ANALYSIS INPUTS</p>
              <h2 className="mt-2 text-xl font-semibold text-white">Your details</h2>
            </div>
            <span className="hidden rounded-full border border-plum-300/20 bg-plum-950/45 px-3 py-1 text-[10px] font-semibold tracking-[0.15em] text-plum-100 sm:inline-flex">
              LOCAL DRAFT
            </span>
          </div>

          <form onSubmit={handleSaveProfile} className="space-y-5">
            <div className="grid gap-4 rounded-2xl border border-plum-300/15 bg-black/20 p-4 sm:grid-cols-2 sm:p-5">
              <GlassInput
                label="Full name"
                icon={User}
                value={form.name}
                onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                required
              />
              <GlassInput
                label="Target role"
                icon={BriefcaseBusiness}
                value={form.targetRole}
                onChange={(event) =>
                  setForm((current) => ({ ...current, targetRole: event.target.value }))
                }
                required
              />
              <GlassInput
                label="Intensity mode"
                as="select"
                icon={Flame}
                value={form.intensityMode}
                onChange={(event) =>
                  setForm((current) => ({ ...current, intensityMode: event.target.value }))
                }
              >
                <option value="Hell Mode">Hell Mode</option>
                <option value="Normal Mode">Normal Mode</option>
                <option value="Chill Mode">Chill Mode</option>
              </GlassInput>
              <GlassInput
                label="GitHub username"
                icon={Github}
                value={form.githubUsername}
                onChange={(event) =>
                  setForm((current) => ({ ...current, githubUsername: event.target.value }))
                }
              />
              <GlassInput
                label="Codeforces handle"
                icon={Code2}
                value={form.codeforcesHandle}
                onChange={(event) =>
                  setForm((current) => ({ ...current, codeforcesHandle: event.target.value }))
                }
                containerClassName="sm:col-span-2"
              />
            </div>

            <p className="rounded-xl border border-honey-200/10 bg-honey-300/[0.04] px-4 py-3 text-xs leading-5 text-slate-400">
              Only these fields and the optional PDF are accepted by the profile-analysis endpoint.
              Handles are not shown as continuously synced telemetry.
            </p>

            <div className="flex flex-wrap gap-3">
              <GlassButton type="submit" variant="secondary" icon={Save}>
                Save local draft
              </GlassButton>
              <Link to="/resume-analyzer">
                <GlassButton variant="primary" iconRight={ArrowUpRight}>
                  Run profile analysis
                </GlassButton>
              </Link>
            </div>
          </form>
        </GlassCard>
      </div>
    </AppLayout>
  );
}
