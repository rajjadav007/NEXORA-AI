import React from 'react';
import { PageHeader } from '../components/layout/PageHeader';
import { FileText } from 'lucide-react';

export function ResumePage() {
  return (
    <div>
      <PageHeader
        title="Resume Intelligence"
        description="Extract, analyze, and optimize your resume credentials."
        badge="Placeholder"
      />
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="rounded-lg border-2 border-dashed border-slate-200 bg-white p-12 text-center">
          <FileText className="mx-auto h-12 w-12 text-slate-400 mb-4" />
          <h3 className="text-base font-semibold text-slate-900">Resume Workspace Ready</h3>
          <p className="mt-1 text-sm text-slate-500">
            Resume parsing and intelligence features will be enabled in upcoming modules.
          </p>
        </div>
      </div>
    </div>
  );
}
