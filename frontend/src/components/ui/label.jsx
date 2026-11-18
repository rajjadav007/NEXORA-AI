import React from 'react';
import { cn } from '../../utils/cn';

export const Label = React.forwardRef(({
  className,
  htmlFor,
  required = false,
  children,
  ...props
}, ref) => {
  return (
    <label
      ref={ref}
      htmlFor={htmlFor}
      className={cn(
        'text-sm font-medium text-slate-700 select-none block mb-1',
        className
      )}
      {...props}
    >
      {children}
      {required && (
        <span className="text-red-500 ml-1" aria-hidden="true">*</span>
      )}
    </label>
  );
});

Label.displayName = 'Label';
