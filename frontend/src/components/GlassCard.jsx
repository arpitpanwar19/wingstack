import React from 'react';

const glowClasses = {
  none: '',
  blue: 'shadow-glow-blue border-honey-300/15',
  purple: 'shadow-glow-purple border-plum-300/20',
  cyan: 'shadow-glow-cyan border-honey-200/15',
};

export default function GlassCard({
  children,
  className = '',
  hover = false,
  glow = 'none',
  padding = 'p-6',
  as: Component = 'div',
  ...props
}) {
  return (
    <Component
      className={`${hover ? 'glass-panel-hover' : 'glass-panel'} ${
        glowClasses[glow] || ''
      } ${padding} ${className}`}
      {...props}
    >
      {children}
    </Component>
  );
}
