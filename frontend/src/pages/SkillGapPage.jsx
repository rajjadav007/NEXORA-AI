import React from 'react';
import { PageHeader } from '../components/layout/PageHeader';
import { EmptyState } from '../components/layout/EmptyState';
import { TrendingUp } from 'lucide-react';

export function SkillGapPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Skill Gap Analysis"
        description="Pinpoint technical and contextual gaps between current skills and target career profiles."
        badge="Placeholder"
      />
      <EmptyState
        icon={TrendingUp}
        title="Skill Gap Diagnostics Ready"
        description="Gap evaluation matrices and prescriptive study plans will be connected soon."
      />
    </div>
  );
}
