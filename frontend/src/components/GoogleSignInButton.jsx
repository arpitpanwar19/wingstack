import React, { useEffect, useRef, useState } from 'react';

const GOOGLE_ID_SCRIPT = 'https://accounts.google.com/gsi/client';

export default function GoogleSignInButton({ onCredential, disabled = false }) {
  const containerRef = useRef(null);
  const onCredentialRef = useRef(onCredential);
  const [scriptReady, setScriptReady] = useState(false);
  const [scriptError, setScriptError] = useState('');
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID?.trim();

  useEffect(() => {
    onCredentialRef.current = onCredential;
  }, [onCredential]);

  useEffect(() => {
    if (!clientId) return undefined;
    if (window.google?.accounts?.id) {
      setScriptReady(true);
      return undefined;
    }

    let script = document.querySelector(`script[src="${GOOGLE_ID_SCRIPT}"]`);
    if (script?.dataset.loadFailed === 'true') {
      setScriptError('Google Sign-In failed to load. Check the connection and reload.');
      return undefined;
    }
    if (script?.dataset.loaded === 'true') {
      setScriptReady(true);
      return undefined;
    }

    const handleLoad = () => {
      if (window.google?.accounts?.id) {
        script.dataset.loaded = 'true';
        setScriptReady(true);
      } else {
        setScriptError('Google Sign-In did not initialize. Reload and try again.');
      }
    };
    const handleError = () => {
      script.dataset.loadFailed = 'true';
      setScriptError('Google Sign-In failed to load. Check the connection and reload.');
    };

    if (!script) {
      script = document.createElement('script');
      script.src = GOOGLE_ID_SCRIPT;
      script.async = true;
      script.defer = true;
    }
    script.addEventListener('load', handleLoad);
    script.addEventListener('error', handleError);
    if (!script.isConnected) document.head.appendChild(script);

    return () => {
      script.removeEventListener('load', handleLoad);
      script.removeEventListener('error', handleError);
    };
  }, [clientId]);

  useEffect(() => {
    if (!scriptReady || !clientId || !containerRef.current) return undefined;
    const container = containerRef.current;
    try {
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: (response) => {
          if (response?.credential) onCredentialRef.current(response.credential);
        },
        auto_select: false,
      });
      window.google.accounts.id.renderButton(container, {
        theme: 'outline',
        size: 'large',
        text: 'continue_with',
        shape: 'pill',
        width: 320,
      });
    } catch (error) {
      const detail = error instanceof Error ? ` ${error.message}` : '';
      setScriptError(`Google Sign-In could not be initialized.${detail}`);
    }

    return () => container.replaceChildren();
  }, [clientId, scriptReady]);

  if (!clientId) {
    return (
      <p role="alert" className="text-center text-sm text-amber-200">
        Google Sign-In needs VITE_GOOGLE_CLIENT_ID configured.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {scriptError ? (
        <p role="alert" className="text-center text-sm text-rose-200">{scriptError}</p>
      ) : (
        <>
          {!scriptReady && (
            <p className="text-center text-sm text-slate-400" role="status">
              Loading Google Sign-In...
            </p>
          )}
          <div
            ref={containerRef}
            className={`flex min-h-11 justify-center ${disabled ? 'pointer-events-none opacity-50' : ''}`}
            aria-busy={!scriptReady || disabled}
          />
        </>
      )}
    </div>
  );
}
