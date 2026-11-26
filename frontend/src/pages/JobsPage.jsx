import React, { useEffect, useState } from 'react';
import { Briefcase, Building2, Clock, FileText, Globe, MapPin, Sparkles, Trash2 } from 'lucide-react';
import { PageHeader } from '../components/layout/PageHeader';
import { EmptyState } from '../components/layout/EmptyState';
import { JobDescriptionInputForm } from '../components/jobs/JobDescriptionInputForm';
import { JobDescriptionUrlImport } from '../components/jobs/JobDescriptionUrlImport';
import { JobRoleAnalysisSection } from '../components/jobs/JobRoleAnalysisSection';
import { cn } from '../utils/cn';
import {
  Alert,
  AlertDescription,
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  LoadingIndicator,
} from '../components/ui';
import {
  deleteJobDescription,
  extractJobRoleAnalysis,
  listJobDescriptions,
} from '../services/jobDescriptionService';

export function JobsPage() {
  const [activeTab, setActiveTab] = useState('manual'); // 'manual' | 'url'
  const [savedJobs, setSavedJobs] = useState([]);
  const [isLoadingList, setIsLoadingList] = useState(true);
  const [listError, setListError] = useState('');
  const [deletingId, setDeletingId] = useState(null);
  const [selectedJobId, setSelectedJobId] = useState(null);
  const [roleAnalyses, setRoleAnalyses] = useState({});
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState('');

  useEffect(() => {
    let active = true;
    async function loadJobs() {
      setIsLoadingList(true);
      setListError('');
      try {
        const res = await listJobDescriptions();
        if (active) {
          setSavedJobs(res?.data || []);
        }
      } catch (err) {
        if (active) {
          setListError(err.message || 'Unable to load saved job descriptions.');
        }
      } finally {
        if (active) {
          setIsLoadingList(false);
        }
      }
    }
    loadJobs();
    return () => {
      active = false;
    };
  }, []);

  const handleSaved = (newRecord) => {
    setSavedJobs((prev) => [newRecord, ...prev.filter((item) => item.id !== newRecord.id)]);
  };

  const handleDelete = async (id) => {
    if (deletingId) return;
    setDeletingId(id);
    setListError('');
    try {
      await deleteJobDescription(id);
      setSavedJobs((prev) => prev.filter((item) => item.id !== id));
      if (selectedJobId === id) {
        setSelectedJobId(null);
        setAnalysisError('');
      }
    } catch (err) {
      setListError(err.message || 'Failed to delete job description.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleAnalyzeJob = async (jobId, forceRecalculate = false) => {
    setSelectedJobId(jobId);
    setIsAnalyzing(true);
    setAnalysisError('');
    try {
      const res = await extractJobRoleAnalysis(jobId, { forceRecalculate });
      if (res?.data) {
        setRoleAnalyses((prev) => ({ ...prev, [jobId]: res.data }));
        setSavedJobs((prev) =>
          prev.map((item) =>
            item.id === jobId ? { ...item, analysis_status: res.data.analysis_status || 'COMPLETED' } : item
          )
        );
      }
    } catch (err) {
      setAnalysisError(err.message || 'Failed to extract job role metadata.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const selectedJob = savedJobs.find((item) => item.id === selectedJobId) || null;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <PageHeader
          title="Job Description Analyzer"
          description="Enter manually or import from a job posting URL, then extract structured role intelligence."
          badge="Phase 6 • Features 33–35"
        />

        <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-xl self-start sm:self-auto border border-slate-200">
          <button
            type="button"
            onClick={() => setActiveTab('manual')}
            className={cn(
              'flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-colors',
              activeTab === 'manual'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            )}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Manual Input</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('url')}
            className={cn(
              'flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-colors',
              activeTab === 'url'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            )}
          >
            <Globe className="w-3.5 h-3.5" />
            <span>Import from URL</span>
          </button>
        </div>
      </div>

      {activeTab === 'manual' ? (
        <JobDescriptionInputForm onSaved={handleSaved} />
      ) : (
        <JobDescriptionUrlImport
          onSaved={handleSaved}
          onFallbackToManual={() => setActiveTab('manual')}
        />
      )}

      <Card>
        <CardHeader className="border-b border-slate-100 pb-4">
          <div className="flex items-center justify-between gap-2">
            <CardTitle className="text-base">Saved Job Descriptions ({savedJobs.length})</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="pt-4">
          {listError && (
            <Alert variant="error" className="mb-4" onClose={() => setListError('')}>
              <AlertDescription>{listError}</AlertDescription>
            </Alert>
          )}

          {isLoadingList ? (
            <div className="flex items-center justify-center py-8 text-sm text-slate-500 gap-2">
              <LoadingIndicator size="sm" />
              <span>Loading saved job descriptions...</span>
            </div>
          ) : savedJobs.length === 0 ? (
            <EmptyState
              icon={Briefcase}
              title="No Saved Job Descriptions Yet"
              description="Submit a job description above to store it and prepare it for upcoming AI analysis."
            />
          ) : (
            <div className="divide-y divide-slate-100">
              {savedJobs.map((job) => (
                <div
                  key={job.id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 py-3.5 first:pt-0 last:pb-0"
                >
                  <div className="space-y-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <h4 className="font-semibold text-slate-900 truncate">{job.job_title}</h4>
                      <Badge variant="secondary" className="text-[11px]">
                        {job.analysis_status}
                      </Badge>
                    </div>
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
                      <span className="inline-flex items-center gap-1">
                        <Building2 className="h-3.5 w-3.5" />
                        {job.company_name}
                      </span>
                      {job.location && (
                        <span className="inline-flex items-center gap-1">
                          <MapPin className="h-3.5 w-3.5" />
                          {job.location}
                        </span>
                      )}
                      {job.employment_type && (
                        <span className="inline-flex items-center gap-1">
                          <Clock className="h-3.5 w-3.5" />
                          {job.employment_type}
                        </span>
                      )}
                      <span>{job.character_count?.toLocaleString() || job.description?.length || 0} chars</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-start sm:self-center shrink-0">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => handleAnalyzeJob(job.id, false)}
                      disabled={isAnalyzing && selectedJobId === job.id}
                    >
                      <Sparkles className="h-3.5 w-3.5 mr-1.5" />
                      <span>{job.analysis_status === 'COMPLETED' ? 'View Role' : 'Analyze Job'}</span>
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(job.id)}
                      disabled={deletingId === job.id}
                      aria-label={`Delete ${job.job_title}`}
                      className="text-slate-500 hover:text-red-600"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <JobRoleAnalysisSection
        selectedJob={selectedJob}
        analysis={selectedJob ? roleAnalyses[selectedJob.id] : null}
        isLoading={isAnalyzing}
        error={analysisError}
        onAnalyze={handleAnalyzeJob}
        onRetry={() => selectedJob && handleAnalyzeJob(selectedJob.id, true)}
      />
    </div>
  );
}
