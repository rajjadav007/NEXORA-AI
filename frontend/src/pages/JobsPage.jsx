import React, { useEffect, useState } from 'react';
import { Briefcase, Building2, Clock, MapPin, Trash2 } from 'lucide-react';
import { PageHeader } from '../components/layout/PageHeader';
import { EmptyState } from '../components/layout/EmptyState';
import { JobDescriptionInputForm } from '../components/jobs/JobDescriptionInputForm';
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
  listJobDescriptions,
} from '../services/jobDescriptionService';

export function JobsPage() {
  const [savedJobs, setSavedJobs] = useState([]);
  const [isLoadingList, setIsLoadingList] = useState(true);
  const [listError, setListError] = useState('');
  const [deletingId, setDeletingId] = useState(null);

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
    } catch (err) {
      setListError(err.message || 'Failed to delete job description.');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Job Description Analyzer"
        description="Enter or paste target job descriptions to store and prepare them for AI role and skill extraction."
        badge="Phase 6 • Feature 33"
      />

      <JobDescriptionInputForm onSaved={handleSaved} />

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

                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(job.id)}
                    disabled={deletingId === job.id}
                    aria-label={`Delete ${job.job_title}`}
                    className="text-slate-500 hover:text-red-600 self-start sm:self-center shrink-0"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
