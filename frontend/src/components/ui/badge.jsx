import React from 'react';
import { cn } from '../../utils/cn';

export const badgeVariants = {
  primary: 'bg-teal-50 text-teal-800 border-teal-200',
  secondary: 'bg-slate-100 text-slate-700 border-slate-200',
  outline: 'bg-white text-slate-700 border-slate-300',
  success: 'bg-green-50 text-green-700 border-green-200',
  warning: 'bg-amber-50 text-amber-800 border-amber-200',
  error: 'bg-red-50 text-red-700 border-red-200',
  destructive: 'bg-red-50 text-red-700 border-red-200',
  info: 'bg-blue-50 text-blue-700 border-blue-200',
};

export function Badge({
  className,
  variant = 'primary',
  children,
  ...props
}) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border transition-colors',
        badgeVariants[variant] || badgeVariants.primary,
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
