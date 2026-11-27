import React, { useState } from 'react';
import { AlertTriangle, ArrowUpRight, Github, ShieldAlert, Swords, UsersRound } from 'lucide-react';
import { Link } from 'react-router-dom';
import AppLayout from '../components/AppLayout';
import GlassButton from '../components/GlassButton';
import GlassCard from '../components/GlassCard';
import GlassInput from '../components/GlassInput';
import Notification from '../components/Notification';
import { useWorkspace } from '../context/WorkspaceContext';
import { findPod, simulateMidnight, verifySprintProof } from '../services/api';

function getPartnershipId(partnership) {
  const data = partnership?.data ?? partnership;
  return data?.partnership_id ?? data?.partnership?.partnership_id;
}

export default function WarRoomPage() {
  const { profile, partnership, savePartnership, clearWorkspace } = useWorkspace();
  const userId = profile?.user_id ?? profile?.id;
  const partnershipId = getPartnershipId(partnership);
  const partnershipData = partnership?.data ?? partnership;
  const [proofUrl, setProofUrl] = useState('');
  const [note, setNote] = useState('');
  const [busyAction, setBusyAction] = useState('');
  const [notice, setNotice] = useState(null);
  const [verification, setVerification] = useState(null);
  const [killSwitch, setKillSwitch] = useState(null);

  const handleFindPod = async () => {
    if (userId === undefined || userId === null) return;
    setBusyAction('match');
    setNotice(null);
    try {
      const result = await findPod(userId);
      savePartnership(result);
      setVerification(null);
      setKillSwitch(null);
      setNotice({
        type: 'success',
        title: 'Matching response received',
        message: 'Pod details below are from the live API response.',
      });
    } catch (error) {
      setNotice({ type: 'error', title: 'Pod match failed', message: error.message });
    } finally {
      setBusyAction('');
    }
  };

  const handleVerifyProof = async (event) => {
    event.preventDefault();
    const parsedUserId = Number(userId);
    const parsedPartnershipId = Number(partnershipId);
    if (!Number.isInteger(parsedUserId) || !Number.isInteger(parsedPartnershipId)) {
      setNotice({
        type: 'error',
        title: 'Missing numeric IDs',
        message: 'The API must return numeric user_id and partnership_id values before proof can be submitted.',
      });
      return;
    }

    setBusyAction('verify');
    setNotice(null);
    try {
      const result = await verifySprintProof({
        partnership_id: parsedPartnershipId,
        user_id: parsedUserId,
        proof_url: proofUrl.trim(),
        note: note.trim(),
      });
      setVerification(result);
      if (result && typeof result === 'object') {
        savePartnership({ ...partnership, ...result });
      }
      setNotice({
        type: 'success',
        title: 'Proof response received',
        message: 'Verification status below reflects the live API response.',
      });
    } catch (error) {
      setNotice({ type: 'error', title: 'Proof verification failed', message: error.message });
    } finally {
      setBusyAction('');
    }
  };

  const handleSimulateMidnight = async () => {
    if (!Number.isInteger(Number(partnershipId))) return;
    const confirmed = window.confirm(
      'This sends a forced-miss simulation to the live backend. Continue?'
    );
    if (!confirmed) return;

    setBusyAction('kill-switch');
    setNotice(null);
    try {
      const result = await simulateMidnight(Number(partnershipId), true);
      setKillSwitch(result);
      if (result && typeof result === 'object') {
        savePartnership({ ...partnership, ...result });
      }
      setNotice({
        type: 'warning',
        title: 'Simulation response received',
        message: 'Kill-switch state below reflects the live API response.',
      });
    } catch (error) {
      setNotice({ type: 'error', title: 'Kill-switch request failed', message: error.message });
    } finally {
      setBusyAction('');
    }
  };

  const rawPartnerName =
    partnershipData?.partner_name ??
    partnershipData?.partner?.name ??
    partnershipData?.partner ??
    partnershipData?.name;
  const partnerName =
    typeof rawPartnerName === 'string' || typeof rawPartnerName === 'number'
      ? rawPartnerName
      : 'Partner name not returned';

  return (
    <AppLayout
      title="Accountability War Room"
      subtitle="Live pod matching and sprint proof"
      user={profile}
      onClearWorkspace={clearWorkspace}
    >
      <div className="space-y-6 animate-fade-in-up">
        <section className="relative overflow-hidden rounded-[2rem] border border-honey-200/20 bg-[radial-gradient(ellipse_at_88%_0%,rgba(59,22,58,0.82),transparent_48%),linear-gradient(135deg,#1b111d,#0c090d_72%)] p-6 shadow-[0_30px_90px_rgba(0,0,0,0.42)] sm:p-9">
          <div className="relative z-10 flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
            <div className="max-w-2xl">
              <p className="eyebrow"><Swords className="h-3.5 w-3.5" /> ACCOUNTABILITY PROTOCOL</p>
              <h2 className="mt-4 text-3xl font-semibold leading-tight tracking-tight text-white sm:text-4xl">
                Good work is
                <span className="block text-gradient">better shared.</span>
              </h2>
              <p className="mt-3 max-w-xl text-sm leading-6 text-slate-300">
                Find a wingman, submit proof, and run the midnight simulation through their original
                endpoints. Nothing is shown as verified until the API responds.
              </p>
            </div>
            <div className="flex items-center gap-3 rounded-2xl border border-plum-300/20 bg-black/25 px-4 py-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-honey-300/20 bg-honey-300/10 text-honey-200">
                <ShieldAlert className="h-5 w-5" />
              </div>
              <div>
                <p className="text-[9px] font-semibold tracking-[0.2em] text-slate-500">USER ID</p>
                <p className="mt-1 text-sm font-medium text-honey-100">
                  {userId ?? 'Create profile first'}
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

        {!partnership ? (
          <GlassCard glow="purple" className="relative overflow-hidden py-12 text-center">
            <div className="relative mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border border-honey-300/20 bg-honey-300/10 text-honey-200">
              <UsersRound className="h-7 w-7" />
            </div>
            <h2 className="relative mt-5 text-xl font-semibold text-white">Find your wingman</h2>
            <p className="relative mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-400">
              {userId === undefined || userId === null
                ? 'Run profile analysis first; the returned user ID is required for pod matching.'
                : 'Request a live match. Partner details and streak are shown only if returned by the API.'}
            </p>
            {userId === undefined || userId === null ? (
              <Link to="/resume-analyzer" className="relative mt-5 inline-flex">
                <GlassButton variant="primary">Create profile</GlassButton>
              </Link>
            ) : (
              <GlassButton
                variant="primary"
                icon={UsersRound}
                loading={busyAction === 'match'}
                onClick={handleFindPod}
                className="relative mt-5"
              >
                Find a pod
              </GlassButton>
            )}
          </GlassCard>
        ) : (
          <div className="grid gap-5 lg:grid-cols-2">
            <GlassCard glow="purple" className="space-y-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="eyebrow">LIVE MATCH</p>
                  <h2 className="mt-2 text-xl font-semibold text-white">
                    {partnerName}
                  </h2>
                </div>
                <UsersRound className="h-6 w-6 text-honey-200" />
              </div>
              <dl className="grid grid-cols-2 gap-3">
                <div className="rounded-xl border border-honey-100/10 bg-black/20 p-3">
                  <dt className="text-[10px] tracking-wider text-slate-500">PARTNERSHIP ID</dt>
                  <dd className="mt-1 font-mono text-sm text-honey-100">{partnershipId ?? 'Not returned'}</dd>
                </div>
                <div className="rounded-xl border border-honey-100/10 bg-black/20 p-3">
                  <dt className="text-[10px] tracking-wider text-slate-500">STREAK</dt>
                  <dd className="mt-1 font-mono text-sm text-honey-100">
                    {partnershipData?.updated_streak ?? partnershipData?.streak ?? partnershipData?.streak_days ?? 'Not returned'}
                  </dd>
                </div>
              </dl>
              <GlassButton
                variant="secondary"
                icon={UsersRound}
                loading={busyAction === 'match'}
                onClick={handleFindPod}
              >
                Find another match
              </GlassButton>
            </GlassCard>

            <GlassCard className="space-y-5">
              <div>
                <p className="eyebrow">DAILY PROOF</p>
                <h2 className="mt-2 text-xl font-semibold text-white">Verify sprint progress</h2>
              </div>
              <form onSubmit={handleVerifyProof} className="space-y-4">
                <GlassInput
                  label="Proof URL"
                  icon={Github}
                  type="url"
                  value={proofUrl}
                  onChange={(event) => setProofUrl(event.target.value)}
                  placeholder="https://..."
                  required
                />
                <GlassInput
                  label="Note"
                  as="textarea"
                  value={note}
                  onChange={(event) => setNote(event.target.value)}
                  required
                />
                <GlassButton type="submit" loading={busyAction === 'verify'} icon={ArrowUpRight}>
                  Submit proof
                </GlassButton>
              </form>
              {verification && (
                <div className="rounded-xl border border-honey-300/15 bg-honey-300/[0.04] p-4">
                  <p className="text-xs font-semibold tracking-wider text-honey-200">API VERIFICATION RESPONSE</p>
                  {(verification.updated_streak ?? verification.streak ?? verification.streak_days) !== undefined && (
                    <p className="mt-2 text-sm text-slate-200">
                      Streak: {verification.updated_streak ?? verification.streak ?? verification.streak_days}
                    </p>
                  )}
                  {(verification.ai_feedback ?? verification.message) && (
                    <p className="mt-1 text-sm text-slate-300">{verification.ai_feedback ?? verification.message}</p>
                  )}
                  <details className="mt-3 text-xs text-slate-400">
                    <summary className="cursor-pointer text-honey-200">Full response</summary>
                    <pre className="mt-2 overflow-auto whitespace-pre-wrap break-words">
                      {JSON.stringify(verification, null, 2)}
                    </pre>
                  </details>
                </div>
              )}
            </GlassCard>
          </div>
        )}

        {partnership && Number.isInteger(Number(partnershipId)) && (
          <GlassCard className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-rose-300/20 bg-rose-400/[0.06] text-rose-200">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <p className="font-semibold text-white">Midnight kill-switch simulation</p>
                <p className="mt-1 text-xs leading-5 text-slate-400">
                  Sends <code>force_miss=true</code> to the live backend and may alter sprint state.
                </p>
              </div>
            </div>
            <GlassButton
              variant="danger"
              icon={ShieldAlert}
              loading={busyAction === 'kill-switch'}
              onClick={handleSimulateMidnight}
            >
              Simulate midnight
            </GlassButton>
            {killSwitch && (
              <div className="w-full rounded-xl border border-honey-300/15 bg-honey-300/[0.04] p-4 sm:w-auto">
                <p className="text-xs font-semibold tracking-wider text-honey-200">SIMULATION RESPONSE</p>
                {(killSwitch.alert_state ?? killSwitch.kill_switch_state ?? killSwitch.kill_switch ?? killSwitch.state ?? killSwitch.status) !== undefined && (
                  <p className="mt-2 text-sm text-slate-200">
                    State: {String(killSwitch.alert_state ?? killSwitch.kill_switch_state ?? killSwitch.kill_switch ?? killSwitch.state ?? killSwitch.status)}
                  </p>
                )}
                {killSwitch.message && <p className="mt-1 text-sm text-slate-300">{killSwitch.message}</p>}
                <details className="mt-3 text-xs text-slate-400">
                  <summary className="cursor-pointer text-honey-200">Full response</summary>
                  <pre className="mt-2 overflow-auto whitespace-pre-wrap break-words">
                    {JSON.stringify(killSwitch, null, 2)}
                  </pre>
                </details>
              </div>
            )}
          </GlassCard>
        )}
      </div>
    </AppLayout>
  );
}
