import React from 'react';
import { AlertCircle, CheckCircle2, AlertTriangle, Info, X } from 'lucide-react';
import { cn } from '../../utils/cn';

const alertVariants = {
  info: {
    container: 'bg-blue-50 border-blue-200 text-blue-900',
    icon: Info,
    iconColor: 'text-blue-600',
  },
  success: {
    container: 'bg-green-50 border-green-200 text-green-900',
    icon: CheckCircle2,
    iconColor: 'text-green-600',
  },
  warning: {
    container: 'bg-amber-50 border-amber-200 text-amber-900',
    icon: AlertTriangle,
    iconColor: 'text-amber-600',
  },
  destructive: {
    container: 'bg-red-50 border-red-200 text-red-900',
    icon: AlertCircle,
    iconColor: 'text-red-600',
  },
  error: {
    container: 'bg-red-50 border-red-200 text-red-900',
    icon: AlertCircle,
    iconColor: 'text-red-600',
  },
};

export function Alert({
  className,
  variant = 'info',
  onClose,
  children,
  ...props
}) {
  const config = alertVariants[variant] || alertVariants.info;
  const IconComponent = config.icon;

  return (
    <div
      role="alert"
      className={cn(
        'relative flex w-full gap-3 rounded-lg border p-4 text-sm',
        config.container,
        className
      )}
      {...props}
    >
      <IconComponent className={cn('h-5 w-5 shrink-0 mt-0.5', config.iconColor)} aria-hidden="true" />
      <div className="flex-1">{children}</div>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          className="shrink-0 rounded-md p-1 opacity-70 hover:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          aria-label="Dismiss alert"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}

export function AlertTitle({ className, children, ...props }) {
  return (
    <h5
      className={cn('font-semibold leading-none tracking-tight mb-1', className)}
      {...props}
    >
      {children}
    </h5>
  );
}

export function AlertDescription({ className, children, ...props }) {
  return (
    <div className={cn('text-sm opacity-90 leading-relaxed', className)} {...props}>
      {children}
    </div>
  );
}
