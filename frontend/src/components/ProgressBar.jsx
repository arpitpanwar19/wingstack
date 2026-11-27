import React from 'react';

const barVariants = {
  gradient: 'from-honey-500 via-honey-300 to-honey-100 shadow-[0_0_14px_rgba(240,201,134,0.25)]',
  blue: 'from-honey-400 to-honey-200 shadow-[0_0_14px_rgba(240,201,134,0.25)]',
  purple: 'from-plum-500 to-plum-200 shadow-[0_0_14px_rgba(142,77,127,0.35)]',
  emerald: 'from-honey-400 to-honey-200 shadow-[0_0_14px_rgba(240,201,134,0.25)]',
  amber: 'from-honey-400 to-honey-200 shadow-[0_0_14px_rgba(240,201,134,0.25)]',
};

const sizeMap = {
  sm: 'h-1.5',
  md: 'h-2.5',
  lg: 'h-3.5',
};

export default function ProgressBar({
  value = 0,
  max = 100,
  label,
  sublabel,
  showValue = true,
  variant = 'gradient',
  size = 'md',
  className = '',
}) {
  const safeMax = max > 0 ? max : 100;
  const pct = Math.max(0, Math.min(100, Math.round((value / safeMax) * 100)));

  return (
    <div className={`w-full space-y-2 ${className}`}>
      {(label || showValue) && (
        <div className="flex items-center justify-between gap-2 text-xs">
          <div className="flex items-center gap-2 min-w-0">
            {label && <span className="font-medium text-slate-200 truncate">{label}</span>}
            {sublabel && <span className="text-slate-400 truncate">{sublabel}</span>}
          </div>
          {showValue && (
            <span className="font-mono font-semibold text-honey-200 shrink-0">{pct}%</span>
          )}
        </div>
      )}

      <div
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        className={`w-full rounded-full bg-white/[0.06] border border-white/10 overflow-hidden backdrop-blur-sm ${
          sizeMap[size] || sizeMap.md
        }`}
      >
        <div
          className={`h-full rounded-full bg-gradient-to-r transition-all duration-700 ease-out ${
            barVariants[variant] || barVariants.gradient
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
