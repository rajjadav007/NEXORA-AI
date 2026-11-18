import React from 'react';
import { PageHeader } from '../components/layout/PageHeader';
import { EmptyState } from '../components/layout/EmptyState';
import { Building2 } from 'lucide-react';

export function EmployerPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Employer Intelligence"
        description="Analyze hiring signals, company engineering cultures, and compensation bands."
        badge="Placeholder"
      />
      <EmptyState
        icon={Building2}
        title="Employer Intelligence Workspace Ready"
        description="Company profiles, hiring trends, and market intelligence will be available in future modules."
      />
    </div>
  );
}
