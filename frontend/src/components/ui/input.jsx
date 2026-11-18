import React from 'react';
import { cn } from '../../utils/cn';

export const Input = React.forwardRef(({
  className,
  type = 'text',
  error = false,
  disabled = false,
  ...props
}, ref) => {
  return (
    <input
      type={type}
      ref={ref}
      disabled={disabled}
      aria-invalid={error ? 'true' : undefined}
      className={cn(
        'flex h-10 w-full rounded-md border bg-white px-3 py-2 text-sm text-slate-900',
        'file:border-0 file:bg-transparent file:text-sm file:font-medium',
        'placeholder:text-slate-400',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
        'disabled:cursor-not-allowed disabled:bg-slate-50 disabled:opacity-60',
        error ? 'border-red-500 focus-visible:ring-red-500' : 'border-slate-300 hover:border-slate-400',
        className
      )}
      {...props}
    />
  );
});

Input.displayName = 'Input';
