import React from 'react';

export default function GlassChartTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;

  return (
    <div className="rounded-xl border border-white/15 bg-void-900/90 backdrop-blur-xl px-3.5 py-2.5 shadow-glass text-xs">
      {label && (
        <p className="mb-1.5 font-semibold text-white border-b border-white/10 pb-1">
          {label}
        </p>
      )}
      <div className="space-y-1">
        {payload.map((entry) => (
          <div key={entry.name} className="flex items-center justify-between gap-4">
            <span className="flex items-center gap-1.5 text-slate-300">
              <span
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: entry.color || '#f0c986' }}
              />
              {entry.name}
            </span>
            <span className="font-mono font-bold text-white">{entry.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
