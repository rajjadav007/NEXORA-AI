import React from 'react';
import { cn } from '../../utils/cn';

export function DashboardCard({
  icon: Icon,
  title,
  description,
  badge,
  action,
  children,
  className,
  onClick,
}) {
  return (
    <div
      onClick={onClick}
      className={cn(
        'group flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition-all duration-150 hover:border-teal-500 hover:shadow-md',
        onClick && 'cursor-pointer',
        className
      )}
    >
      <div>
        <div className="flex items-start justify-between gap-3">
          {Icon && (
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-teal-50 text-teal-600 transition-colors group-hover:bg-teal-600 group-hover:text-white">
              <Icon className="h-5 w-5" aria-hidden="true" />
            </div>
          )}
          {badge && (
            <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-700">
              {badge}
            </span>
          )}
        </div>
        <h3 className="mt-4 text-base font-semibold text-slate-900 group-hover:text-teal-700">
          {title}
        </h3>
        {description && (
          <p className="mt-1 text-sm text-slate-500 leading-relaxed">
            {description}
          </p>
        )}
      </div>

      {children && <div className="mt-4">{children}</div>}

      {action && (
        <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between text-xs font-medium text-teal-600 group-hover:text-teal-700">
          {action}
        </div>
      )}
    </div>
  );
}
