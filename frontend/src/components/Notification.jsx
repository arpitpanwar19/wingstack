import React from 'react';
import { AlertTriangle, CheckCircle2, Info, X, XCircle } from 'lucide-react';

const styles = {
  info: {
    container: 'border-honey-300/25 bg-honey-300/[0.06] text-honey-100',
    icon: Info,
    iconColor: 'text-honey-200',
  },
  success: {
    container: 'border-emerald-400/25 bg-emerald-500/10 text-emerald-100',
    icon: CheckCircle2,
    iconColor: 'text-emerald-400',
  },
  warning: {
    container: 'border-amber-400/25 bg-amber-500/10 text-amber-100',
    icon: AlertTriangle,
    iconColor: 'text-amber-400',
  },
  error: {
    container: 'border-rose-400/30 bg-rose-500/10 text-rose-100',
    icon: XCircle,
    iconColor: 'text-rose-400',
  },
};

export default function Notification({
  type = 'info',
  title,
  message,
  onClose,
  action,
  className = '',
}) {
  if (!message && !title) return null;

  const variant = styles[type] || styles.info;
  const Icon = variant.icon;

  return (
    <div
      role="alert"
      className={`relative flex items-start gap-3 rounded-2xl border backdrop-blur-xl px-4 py-3.5 shadow-glass transition-all duration-300 ${variant.container} ${className}`}
    >
      <Icon className={`h-5 w-5 shrink-0 mt-0.5 ${variant.iconColor}`} />

      <div className="flex-1 min-w-0 text-sm">
        {title && <p className="font-semibold text-white">{title}</p>}
        {message && <p className="text-slate-200/90 text-xs sm:text-sm leading-relaxed mt-0.5">{message}</p>}
        {action && <div className="mt-2.5">{action}</div>}
      </div>

      {onClose && (
        <button
          type="button"
          onClick={onClose}
          aria-label="Dismiss notification"
          className="rounded-lg p-1 text-slate-300/80 hover:bg-white/10 hover:text-white transition-colors shrink-0"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
