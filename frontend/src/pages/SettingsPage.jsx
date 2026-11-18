import React from 'react';
import { PageHeader } from '../components/layout/PageHeader';
import { Settings } from 'lucide-react';

export function SettingsPage() {
  return (
    <div>
      <PageHeader
        title="Settings"
        description="Configure account preferences, platform notifications, and integrations."
        badge="Placeholder"
      />
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="rounded-lg border-2 border-dashed border-slate-200 bg-white p-12 text-center">
          <Settings className="mx-auto h-12 w-12 text-slate-400 mb-4" />
          <h3 className="text-base font-semibold text-slate-900">Settings Workspace Ready</h3>
          <p className="mt-1 text-sm text-slate-500">
            User settings and platform preferences will be configured in future features.
          </p>
        </div>
      </div>
    </div>
  );
}
