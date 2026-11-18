import React from 'react';
import { PageHeader } from '../components/layout/PageHeader';
import { EmptyState } from '../components/layout/EmptyState';
import { Target } from 'lucide-react';

export function MatchingPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Job Matching"
        description="Automated alignment between candidate profiles and market position requirements."
        badge="Placeholder"
      />
      <EmptyState
        icon={Target}
        title="Job Matching Engine Ready"
        description="Semantic candidate-to-job matching pipelines will be integrated in upcoming releases."
      />
    </div>
  );
}
