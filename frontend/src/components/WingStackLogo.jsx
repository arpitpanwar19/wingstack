import React from 'react';

export default function WingStackLogo({ size = 'md', showTagline = false, className = '' }) {
  const sizes = {
    sm: { box: 'h-5 w-14', text: 'text-base' },
    md: { box: 'h-6 w-16', text: 'text-lg' },
    lg: { box: 'h-7 w-20', text: 'text-2xl' },
  };

  const current = sizes[size] || sizes.md;

  return (
    <div className={`inline-flex items-center gap-2.5 select-none ${className}`}>
      <div className={`${current.box} relative shrink-0 overflow-hidden`}>
        <img
          src="/wingstack-orbital-logo.png"
          alt="WingStack orbital logo"
          className="absolute inset-0 h-full w-full object-contain"
        />
      </div>

      <div className="flex flex-col leading-none">
        <span className={`${current.text} font-bold tracking-tight text-white`}>
          Wing<span className="text-gradient">Stack</span>
        </span>
        {showTagline && (
          <span className="mt-1 text-[10px] font-mono uppercase tracking-[0.2em] text-slate-400">
            Scout &amp; Protocol
          </span>
        )}
      </div>
    </div>
  );
}
