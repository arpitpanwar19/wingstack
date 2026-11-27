import React from 'react';
import { Minus, TrendingDown, TrendingUp } from 'lucide-react';
import GlassCard from './GlassCard';

const accentStyles = {
  blue: 'from-honey-300/15 to-plum-900/35 text-honey-100 border-honey-300/20',
  purple: 'from-plum-700/35 to-black/20 text-plum-100 border-plum-300/25',
  emerald: 'from-honey-300/10 to-black/20 text-honey-100 border-honey-200/15',
  amber: 'from-honey-300/15 to-plum-950/35 text-honey-100 border-honey-300/20',
};

export default function DashboardCard({
  title,
  value,
  subtitle,
  trend,
  trendDirection = 'up',
  icon: Icon,
  accent = 'blue',
  children,
  footer,
  className = '',
}) {
  const TrendIcon =
    trendDirection === 'down' ? TrendingDown : trendDirection === 'neutral' ? Minus : TrendingUp;
  const trendColor =
    trendDirection === 'down'
      ? 'text-rose-300 bg-rose-500/10 border-rose-400/20'
      : trendDirection === 'neutral'
      ? 'text-slate-300 bg-white/5 border-white/10'
      : 'text-emerald-300 bg-emerald-500/10 border-emerald-400/20';

  return (
    <GlassCard hover className={`flex flex-col justify-between ${className}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1 min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{title}</p>
          {value !== undefined && (
            <p className="text-2xl sm:text-3xl font-bold tracking-tight text-white font-mono">
              {value}
            </p>
          )}
          {subtitle && <p className="text-xs text-slate-400 leading-relaxed">{subtitle}</p>}
        </div>

        {Icon && (
          <div
            className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border bg-gradient-to-br ${
              accentStyles[accent] || accentStyles.blue
            }`}
          >
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>

      {children && <div className="mt-4">{children}</div>}

      {(trend || footer) && (
        <div className="mt-4 pt-3 border-t border-white/[0.08] flex items-center justify-between gap-2">
          {trend ? (
            <span
              className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${trendColor}`}
            >
              <TrendIcon className="h-3 w-3" />
              {trend}
            </span>
          ) : (
            <span />
          )}
          {footer && <div className="text-xs text-slate-400">{footer}</div>}
        </div>
      )}
    </GlassCard>
  );
}
