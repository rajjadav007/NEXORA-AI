import React from 'react';
import { PageHeader } from '../components/layout/PageHeader';
import { Compass } from 'lucide-react';

export function CareerPage() {
  return (
    <div>
      <PageHeader
        title="Career Roadmaps & Skill Gaps"
        description="Measure career readiness and follow tailored milestone plans."
        badge="Placeholder"
      />
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="rounded-lg border-2 border-dashed border-slate-200 bg-white p-12 text-center">
          <Compass className="mx-auto h-12 w-12 text-slate-400 mb-4" />
          <h3 className="text-base font-semibold text-slate-900">Career Intelligence Workspace Ready</h3>
          <p className="mt-1 text-sm text-slate-500">
            Readiness scoring and automated roadmap generation will be enabled in upcoming modules.
          </p>
        </div>
      </div>
    </div>
  );
}
