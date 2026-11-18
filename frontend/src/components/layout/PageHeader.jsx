import React from 'react';
import { Badge } from '../ui/badge';
import { Container } from '../ui/container';
import { cn } from '../../utils/cn';

export function PageHeader({ title, description, badge, action, className }) {
  return (
    <div className={cn('border-b border-border bg-white py-6 sm:py-8', className)}>
      <Container>
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="space-y-1.5">
            {badge && (
              <div className="mb-2">
                <Badge variant="primary">{badge}</Badge>
              </div>
            )}
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
              {title}
            </h1>
            {description && (
              <p className="text-sm text-slate-500 max-w-3xl leading-relaxed">
                {description}
              </p>
            )}
          </div>
          {action && <div className="flex-shrink-0 flex items-center gap-2">{action}</div>}
        </div>
      </Container>
    </div>
  );
}
