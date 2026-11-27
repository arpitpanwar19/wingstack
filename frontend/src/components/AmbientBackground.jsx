import React from 'react';

export default function AmbientBackground() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-void-950">
    {/* Base deep gradient */}
      <div
        className="absolute inset-0"
        style={{
          background:
            'radial-gradient(ellipse 80% 60% at 50% -10%, rgba(240, 201, 134, 0.1), transparent 70%), radial-gradient(ellipse 65% 55% at 85% 95%, rgba(59, 22, 58, 0.38), transparent 65%), #09070a',
        }}
      />

      {/* Subtle architectural grid */}
      <div className="bg-cyber-grid absolute inset-0 opacity-60 [mask-image:radial-gradient(ellipse_at_center,black_30%,transparent_80%)]" />

      {/* Top-left honey glow orb */}
      <div
        className="animate-pulse-glow absolute -top-36 -left-32 h-[34rem] w-[34rem] rounded-full blur-[120px]"
        style={{ background: 'rgba(240, 201, 134, 0.16)' }}
      />

      {/* Center-right plum nebula orb */}
      <div
        className="animate-pulse-glow absolute top-1/4 -right-36 h-[32rem] w-[32rem] rounded-full blur-[130px]"
        style={{ background: 'rgba(59, 22, 58, 0.34)', animationDelay: '2s' }}
      />

      {/* Bottom-left muted honey accent orb */}
      <div
        className="animate-pulse-glow absolute -bottom-44 left-1/4 h-[28rem] w-[28rem] rounded-full blur-[130px]"
        style={{ background: 'rgba(226, 183, 110, 0.12)', animationDelay: '4s' }}
      />
    </div>
  );
}
