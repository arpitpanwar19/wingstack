import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';

export default function GlassInput({
  label,
  icon: Icon,
  error,
  hint,
  type = 'text',
  as = 'input',
  rightElement,
  className = '',
  containerClassName = '',
  id,
  children,
  ...props
}) {
  const [showPassword, setShowPassword] = useState(false);
  const isPassword = type === 'password';
  const resolvedType = isPassword ? (showPassword ? 'text' : 'password') : type;
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  const baseFieldClasses = `w-full rounded-xl bg-black/35 backdrop-blur-md border text-sm text-slate-100 placeholder:text-slate-500 transition-all duration-200 focus:outline-none focus:bg-plum-950/60 focus:ring-2 ${
    error
      ? 'border-rose-400/50 focus:border-rose-400 focus:ring-rose-500/20'
      : 'border-honey-100/15 focus:border-honey-300/60 focus:ring-honey-400/15'
  } ${Icon ? 'pl-11' : 'pl-4'} ${isPassword || rightElement ? 'pr-11' : 'pr-4'} ${
    as === 'textarea' ? 'py-3 min-h-[100px] resize-y' : 'py-3'
  } ${className}`;

  return (
    <div className={`space-y-1.5 ${containerClassName}`}>
      {label && (
        <label
          htmlFor={inputId}
          className="block text-xs font-semibold uppercase tracking-wider text-slate-300/90"
        >
          {label}
        </label>
      )}

      <div className="relative">
        {Icon && (
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400">
            <Icon className="h-4 w-4" />
          </div>
        )}

        {as === 'textarea' ? (
          <textarea id={inputId} className={baseFieldClasses} {...props} />
        ) : as === 'select' ? (
          <select id={inputId} className={baseFieldClasses} {...props}>
            {children}
          </select>
        ) : (
          <input id={inputId} type={resolvedType} className={baseFieldClasses} {...props} />
        )}

        {isPassword && (
          <button
            type="button"
            onClick={() => setShowPassword((prev) => !prev)}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            className="absolute inset-y-0 right-0 flex items-center pr-3.5 text-slate-400 hover:text-white transition-colors"
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        )}

        {!isPassword && rightElement && (
          <div className="absolute inset-y-0 right-0 flex items-center pr-3">{rightElement}</div>
        )}
      </div>

      {error ? (
        <p className="text-xs text-rose-300">{error}</p>
      ) : hint ? (
        <p className="text-xs text-slate-400">{hint}</p>
      ) : null}
    </div>
  );
}
