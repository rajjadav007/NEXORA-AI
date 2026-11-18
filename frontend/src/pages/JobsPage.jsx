import React from 'react';
import { PageHeader } from '../components/layout/PageHeader';
import { EmptyState } from '../components/layout/EmptyState';
import { Briefcase } from 'lucide-react';

export function JobsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Jobs Discovery & Matching"
        description="Explore targeted opportunities and role-specific requirements."
        badge="Placeholder"
      />
      <EmptyState
        icon={Briefcase}
        title="Job Matching Workspace Ready"
        description="Job description analysis and candidate alignment will be enabled in upcoming modules."
      />
    </div>
  );
}
