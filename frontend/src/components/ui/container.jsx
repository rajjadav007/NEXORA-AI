import React from 'react';
import { cn } from '../../utils/cn';

const maxWidths = {
  sm: 'max-w-3xl',
  md: 'max-w-5xl',
  lg: 'max-w-7xl',
  xl: 'max-w-screen-2xl',
  full: 'w-full',
};

export const Container = React.forwardRef(({
  className,
  size = 'lg',
  children,
  ...props
}, ref) => {
  return (
    <div
      ref={ref}
      className={cn(
        'w-full mx-auto px-4 sm:px-6 lg:px-8',
        maxWidths[size] || maxWidths.lg,
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
});

Container.displayName = 'Container';
