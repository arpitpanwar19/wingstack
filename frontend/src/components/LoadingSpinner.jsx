import React from 'react';

const sizeClasses = {
  sm: 'h-5 w-5 border-2',
  md: 'h-9 w-9 border-[3px]',
  lg: 'h-14 w-14 border-[3px]',
};

export default function LoadingSpinner({
  size = 'md',
  label,
  fullScreen = false,
  className = '',
}) {
  const spinner = (
    <div className={`inline-flex flex-col items-center justify-center gap-3 ${className}`}>
      <div className="relative flex items-center justify-center">
        <div
          className={`${
            sizeClasses[size] || sizeClasses.md
          } rounded-full border-honey-100/10 border-t-honey-300 border-r-plum-300 animate-spin`}
        />
        <div className="absolute inset-1 rounded-full bg-honey-400/10 blur-sm pointer-events-none" />
      </div>
      {label && (
        <p className="text-xs font-medium tracking-wide text-slate-300 animate-pulse">{label}</p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-void-950/70 backdrop-blur-md">
        <div className="glass-panel px-8 py-6">{spinner}</div>
      </div>
    );
  }

  return spinner;
}
