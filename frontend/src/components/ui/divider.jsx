import React from 'react';
import { cn } from '../../utils/cn';

export function Divider({
  className,
  orientation = 'horizontal',
  label,
  ...props
}) {
  if (orientation === 'vertical') {
    return (
      <div
        role="separator"
        aria-orientation="vertical"
        className={cn('inline-block h-full min-h-[1em] w-[1px] bg-slate-200 self-stretch', className)}
        {...props}
      />
    );
  }

  if (label) {
    return (
      <div className={cn('relative flex py-2 items-center w-full', className)} {...props}>
        <div className="flex-grow border-t border-slate-200" />
        <span className="flex-shrink mx-4 text-xs font-medium text-slate-500 uppercase tracking-wider">
          {label}
        </span>
        <div className="flex-grow border-t border-slate-200" />
      </div>
    );
  }

  return (
    <hr
      role="separator"
      className={cn('border-0 border-t border-slate-200 my-4 w-full', className)}
      {...props}
    />
  );
}
