import React from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '../../utils/cn';

export const Select = React.forwardRef(({
  className,
  error = false,
  disabled = false,
  children,
  ...props
}, ref) => {
  return (
    <div className="relative w-full">
      <select
        ref={ref}
        disabled={disabled}
        aria-invalid={error ? 'true' : undefined}
        className={cn(
          'flex h-10 w-full appearance-none rounded-md border bg-white px-3 py-2 pr-9 text-sm text-slate-900',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
          'disabled:cursor-not-allowed disabled:bg-slate-50 disabled:opacity-60',
          error ? 'border-red-500 focus-visible:ring-red-500' : 'border-slate-300 hover:border-slate-400',
          className
        )}
        {...props}
      >
        {children}
      </select>
      <ChevronDown
        className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
        aria-hidden="true"
      />
    </div>
  );
});

Select.displayName = 'Select';
