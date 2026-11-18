import React from 'react';
import { PageHeader } from '../components/layout/PageHeader';
import { EmptyState } from '../components/layout/EmptyState';
import { FileText } from 'lucide-react';

export function ResumePage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Resume Intelligence"
        description="Extract, analyze, and optimize your resume credentials."
        badge="Placeholder"
      />
      <EmptyState
        icon={FileText}
        title="Resume Workspace Ready"
        description="Resume parsing and intelligence features will be enabled in upcoming modules."
      />
    </div>
  );
}
