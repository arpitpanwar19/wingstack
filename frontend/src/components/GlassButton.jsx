import React from 'react';
import { Loader2 } from 'lucide-react';

const variants = {
  primary:
    'bg-gradient-to-r from-honey-500 via-honey-300 to-honey-200 border border-honey-100/50 text-void-950 shadow-[0_8px_28px_rgba(240,201,134,0.2)] hover:shadow-[0_12px_36px_rgba(240,201,134,0.32)] hover:brightness-105',
  secondary:
    'bg-plum-900/55 backdrop-blur-md border border-honey-300/20 text-honey-100 hover:bg-plum-800/70 hover:border-honey-300/40',
  ghost:
    'bg-transparent border border-transparent text-slate-300 hover:bg-plum-900/60 hover:text-honey-100 hover:border-honey-300/15',
  success:
    'bg-emerald-500/15 backdrop-blur-md border border-emerald-400/30 text-emerald-200 hover:bg-emerald-500/25 hover:border-emerald-300/45',
  danger:
    'bg-rose-500/15 backdrop-blur-md border border-rose-400/30 text-rose-200 hover:bg-rose-500/25 hover:border-rose-300/45',
};

const sizes = {
  sm: 'px-3.5 py-2 text-xs rounded-xl gap-1.5',
  md: 'px-5 py-2.5 text-sm rounded-xl gap-2',
  lg: 'px-6 py-3.5 text-base rounded-2xl gap-2.5',
};

export default function GlassButton({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  icon: Icon,
  iconRight: IconRight,
  className = '',
  type = 'button',
  ...props
}) {
  const isDisabled = disabled || loading;

  return (
    <button
      type={type}
      disabled={isDisabled}
      className={`inline-flex items-center justify-center font-semibold tracking-tight transition-all duration-200 active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none select-none ${
        variants[variant] || variants.primary
      } ${sizes[size] || sizes.md} ${className}`}
      {...props}
    >
      {loading ? (
        <Loader2 className="h-4 w-4 animate-spin shrink-0" />
      ) : Icon ? (
        <Icon className="h-4 w-4 shrink-0" />
      ) : null}
      {children && <span>{children}</span>}
      {!loading && IconRight && <IconRight className="h-4 w-4 shrink-0" />}
    </button>
  );
}
