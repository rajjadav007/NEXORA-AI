import React from 'react';
import { PageHeader } from '../components/layout/PageHeader';
import { EmptyState } from '../components/layout/EmptyState';
import { Compass } from 'lucide-react';

export function CareerPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Career Roadmaps & Skill Gaps"
        description="Measure career readiness and follow tailored milestone plans."
        badge="Placeholder"
      />
      <EmptyState
        icon={Compass}
        title="Career Intelligence Workspace Ready"
        description="Readiness scoring and automated roadmap generation will be enabled in upcoming modules."
      />
    </div>
  );
}
