import React, { useState } from 'react';
import { PageHeader } from '../components/layout/PageHeader';
import { ResumeUpload } from '../components/resume/ResumeUpload';
import { SavedResumesList } from '../components/resume/SavedResumesList';
import { ResumeAnalyticsDashboard } from '../components/resume/ResumeAnalyticsDashboard';
import { Upload, FolderOpen, BarChart3 } from 'lucide-react';
import { cn } from '../utils/cn';

export function ResumePage() {
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' | 'saved' | 'analytics'

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <PageHeader
          title="Resume Intelligence"
          description="Upload, validate, clean, analyze, and track performance metrics for your career documents."
          badge="Phase 5 • Feature 28"
        />

        {/* Tab switch */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-xl self-start sm:self-auto border border-slate-200">
          <button
            type="button"
            onClick={() => setActiveTab('upload')}
            className={cn(
              'flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-colors',
              activeTab === 'upload'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            )}
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Upload & Process</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('saved')}
            className={cn(
              'flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-colors',
              activeTab === 'saved'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            )}
          >
            <FolderOpen className="w-3.5 h-3.5" />
            <span>Saved Resumes</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('analytics')}
            className={cn(
              'flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-colors',
              activeTab === 'analytics'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            )}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Analytics Dashboard</span>
          </button>
        </div>
      </div>

      {activeTab === 'upload' ? (
        <ResumeUpload />
      ) : activeTab === 'saved' ? (
        <SavedResumesList onUploadNew={() => setActiveTab('upload')} />
      ) : (
        <ResumeAnalyticsDashboard />
      )}
    </div>
  );
}
