import React from 'react';
import { PageHeader } from '../components/layout/PageHeader';
import { EmptyState } from '../components/layout/EmptyState';
import { Settings } from 'lucide-react';

export function SettingsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        description="Configure account preferences, platform notifications, and integrations."
        badge="Placeholder"
      />
      <EmptyState
        icon={Settings}
        title="Settings Workspace Ready"
        description="User settings and platform preferences will be configured in future features."
      />
    </div>
  );
}
