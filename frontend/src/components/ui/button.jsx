import React from 'react';
import { cn } from '../../utils/cn';

export const buttonVariants = {
  variant: {
    primary: 'bg-primary text-primary-foreground hover:bg-teal-700 shadow-sm active:bg-teal-800',
    secondary: 'bg-slate-100 text-slate-800 hover:bg-slate-200 active:bg-slate-300',
    outline: 'border border-border bg-white text-slate-700 hover:bg-slate-50 hover:text-slate-900 active:bg-slate-100',
    ghost: 'text-slate-700 hover:bg-slate-100 hover:text-slate-900 active:bg-slate-200',
    destructive: 'bg-red-600 text-white hover:bg-red-700 active:bg-red-800 shadow-sm',
    link: 'text-primary underline-offset-4 hover:underline p-0 h-auto',
  },
  size: {
    sm: 'h-8 px-3 text-xs rounded-md',
    md: 'h-10 px-4 text-sm rounded-md',
    lg: 'h-11 px-6 text-base rounded-md',
    icon: 'h-10 w-10 p-0 rounded-md shrink-0',
  },
};

export const Button = React.forwardRef(({
  className,
  variant = 'primary',
  size = 'md',
  type = 'button',
  disabled = false,
  children,
  ...props
}, ref) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none select-none';

  return (
    <button
      ref={ref}
      type={type}
      disabled={disabled}
      className={cn(
        baseStyles,
        buttonVariants.variant[variant] || buttonVariants.variant.primary,
        buttonVariants.size[size] || buttonVariants.size.md,
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
});

Button.displayName = 'Button';

export const PrimaryButton = React.forwardRef((props, ref) => (
  <Button ref={ref} variant="primary" {...props} />
));
PrimaryButton.displayName = 'PrimaryButton';

export const SecondaryButton = React.forwardRef((props, ref) => (
  <Button ref={ref} variant="secondary" {...props} />
));
SecondaryButton.displayName = 'SecondaryButton';

export const OutlineButton = React.forwardRef((props, ref) => (
  <Button ref={ref} variant="outline" {...props} />
));
OutlineButton.displayName = 'OutlineButton';

export const IconButton = React.forwardRef(({ label, 'aria-label': ariaLabel, children, ...props }, ref) => (
  <Button
    ref={ref}
    size="icon"
    variant="ghost"
    aria-label={label || ariaLabel}
    {...props}
  >
    {children}
  </Button>
));
IconButton.displayName = 'IconButton';
