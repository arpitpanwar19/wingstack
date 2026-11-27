import React, { useState } from 'react';
import { ShieldCheck, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import AmbientBackground from '../components/AmbientBackground';
import GlassCard from '../components/GlassCard';
import GoogleSignInButton from '../components/GoogleSignInButton';
import Notification from '../components/Notification';
import WingStackLogo from '../components/WingStackLogo';
import { authenticateWithGoogle } from '../services/api';

export default function LoginPage() {
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const handleGoogleCredential = async (credential) => {
    setBusy(true);
    setError('');
    try {
      await authenticateWithGoogle(credential);
      navigate('/resume-analyzer');
    } catch (requestError) {
      setError(
        requestError?.isEndpointMissing
          ? 'Google token verification is unavailable at the configured auth API. Ensure POST /api/auth/google is deployed and VITE_GOOGLE_AUTH_API_BASE_URL points to it.'
          : requestError?.message || 'Google sign-in could not be verified.'
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-12 text-slate-100">
      <AmbientBackground />
      <main className="relative z-10 mx-auto w-full max-w-lg space-y-7">
        <div className="flex flex-col items-center space-y-4 text-center">
          <WingStackLogo size="lg" />
          <p className="eyebrow">
            <span className="h-1.5 w-1.5 rounded-full bg-honey-300" />
            A MORE CONSIDERED CAREER WORKSPACE
          </p>
          <h1 className="max-w-md text-3xl font-semibold leading-tight tracking-tight text-white sm:text-4xl">
            Build your next move
            <span className="block text-gradient">with intention.</span>
          </h1>
          <p className="max-w-md text-sm leading-6 text-slate-400">
            Start with your profile. Its live user ID unlocks job matching, pod matching, and sprint
            workflows.
          </p>
        </div>

        <GlassCard glow="purple" padding="p-6 sm:p-8" className="space-y-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="eyebrow">WELCOME TO WINGSTACK</p>
              <h2 className="mt-2 text-2xl font-semibold text-white">Enter your workspace</h2>
              <p className="mt-1 text-sm text-slate-400">Continue with your Google account.</p>
            </div>
            <div className="hidden h-12 w-12 items-center justify-center rounded-2xl border border-honey-300/20 bg-honey-300/10 text-honey-200 sm:flex">
              <ShieldCheck className="h-5 w-5" />
            </div>
          </div>

          {error && (
            <Notification
              type="error"
              title="Google verification failed"
              message={error}
            />
          )}

          <div className="rounded-2xl border border-honey-200/10 bg-black/20 p-4">
            <div className="flex items-center gap-2 text-xs font-semibold tracking-wide text-honey-100">
              <Sparkles className="h-4 w-4 text-honey-200" />
              Google account verification
            </div>
            <p className="mt-2 text-xs leading-5 text-slate-400">
              Google verifies the account in the browser; WingStack then asks its API to validate
              the returned credential.
            </p>
          </div>

          <GoogleSignInButton onCredential={handleGoogleCredential} disabled={busy} />

          <p className="border-t border-honey-100/10 pt-4 text-center text-xs leading-5 text-slate-500">
            After verification, profile analysis creates the separate user ID used by agent workflows.
          </p>
        </GlassCard>
      </main>
    </div>
  );
}
