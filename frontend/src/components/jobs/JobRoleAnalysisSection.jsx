import React from 'react';
import {
  AlertCircle,
  Briefcase,
  Building2,
  CheckCircle2,
  Clock,
  Layers,
  MapPin,
  RefreshCw,
  Sparkles,
  Tag,
} from 'lucide-react';
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
} from '../ui';

function formatUnavailable(value, fallback = 'Not specified') {
  if (value === null || value === undefined || value === '' || value === 'Unknown') {
    return { text: value === 'Unknown' ? 'Unknown' : fallback, unavailable: true };
  }
  return { text: String(value), unavailable: false };
}

function formatExperience(experienceLevel) {
  if (!experienceLevel) {
    return { text: 'Not specified', unavailable: true };
  }
  if (experienceLevel.description) {
    return { text: experienceLevel.description, unavailable: false };
  }
  const min = experienceLevel.minimum_years;
  const max = experienceLevel.maximum_years;
  if (min !== null && min !== undefined && max !== null && max !== undefined) {
    return { text: `${min}–${max} years`, unavailable: false };
  }
  if (min !== null && min !== undefined) {
    return { text: `${min}+ years`, unavailable: false };
  }
  if (max !== null && max !== undefined) {
    return { text: `Up to ${max} years`, unavailable: false };
  }
  return { text: 'Not specified', unavailable: true };
}

function DetailTile({ icon: Icon, label, value, unavailable }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3.5">
      <div className="flex items-center gap-1.5 text-xs font-medium text-slate-500 mb-1">
        {Icon && <Icon className="h-3.5 w-3.5 text-slate-400" />}
        <span>{label}</span>
      </div>
      <p className={unavailable ? 'text-sm italic text-slate-400' : 'text-sm font-semibold text-slate-900'}>
        {value}
      </p>
    </div>
  );
}

export function JobRoleAnalysisSection({
  selectedJob,
  analysis,
  isLoading,
  error,
  onAnalyze,
  onRetry,
}) {
  if (!selectedJob) {
    return null;
  }

  const statusLabel = isLoading
    ? 'ANALYZING'
    : error
      ? 'FAILED'
      : analysis?.analysis_status || selectedJob.analysis_status || 'PENDING';

  const confidencePercent =
    typeof analysis?.confidence_score === 'number'
      ? Math.round(analysis.confidence_score * 100)
      : null;

  const titleField = formatUnavailable(analysis?.job_title);
  const roleField = formatUnavailable(analysis?.standardized_role);
  const deptField = formatUnavailable(analysis?.department);
  const categoryField = formatUnavailable(analysis?.category);
  const seniorityField = formatUnavailable(analysis?.seniority, 'Unknown');
  const expField = formatExperience(analysis?.experience_level);
  const employmentField = formatUnavailable(analysis?.employment_type);
  const workField = formatUnavailable(analysis?.work_arrangement, 'Unknown');
  const industryField = formatUnavailable(analysis?.industry);

  return (
    <Card>
      <CardHeader className="border-b border-slate-100 pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <CardTitle className="text-base">Job Role Analysis</CardTitle>
              <Badge variant="secondary" className="text-[11px]">
                {statusLabel}
              </Badge>
              {analysis?.cached && (
                <Badge variant="outline" className="text-[11px]">
                  Cached
                </Badge>
              )}
            </div>
            <p className="text-xs text-slate-500">
              {selectedJob.job_title} • {selectedJob.company_name}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => onAnalyze(selectedJob.id, Boolean(analysis))}
              disabled={isLoading}
            >
              <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${isLoading ? 'animate-spin' : ''}`} />
              <span>{analysis ? 'Re-analyze' : 'Analyze Job'}</span>
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-5 space-y-5">
        {isLoading && (
          <div className="flex items-center justify-center py-8 gap-2.5 text-sm text-slate-600">
            <LoadingIndicator size="sm" />
            <span>Extracting structured job role intelligence...</span>
          </div>
        )}

        {!isLoading && error && (
          <Alert variant="error">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <span>{error}</span>
              <Button type="button" size="sm" variant="outline" onClick={onRetry}>
                Retry
              </Button>
            </AlertDescription>
          </Alert>
        )}

        {!isLoading && !error && analysis && (
          <>
            <div className="rounded-xl border border-indigo-100 bg-indigo-50/50 p-4 space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-indigo-700">
                  Role Summary
                </span>
                {confidencePercent !== null && (
                  <span className="text-xs font-semibold text-indigo-700">
                    Confidence Score: {confidencePercent}%
                  </span>
                )}
              </div>
              <p className={analysis.role_summary ? 'text-sm text-slate-800' : 'text-sm italic text-slate-400'}>
                {analysis.role_summary || 'No summary could be derived from the posting.'}
              </p>
              {confidencePercent !== null && (
                <div className="w-full bg-indigo-100 h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-indigo-600 h-full transition-all"
                    style={{ width: `${Math.min(100, Math.max(0, confidencePercent))}%` }}
                  />
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              <DetailTile icon={Briefcase} label="Job Title" value={titleField.text} unavailable={titleField.unavailable} />
              <DetailTile icon={Sparkles} label="Standardized Role" value={roleField.text} unavailable={roleField.unavailable} />
              <DetailTile icon={Building2} label="Department" value={deptField.text} unavailable={deptField.unavailable} />
              <DetailTile icon={Tag} label="Category" value={categoryField.text} unavailable={categoryField.unavailable} />
              <DetailTile icon={Layers} label="Seniority" value={seniorityField.text} unavailable={seniorityField.unavailable} />
              <DetailTile icon={Clock} label="Experience Level" value={expField.text} unavailable={expField.unavailable} />
              <DetailTile icon={Clock} label="Employment Type" value={employmentField.text} unavailable={employmentField.unavailable} />
              <DetailTile icon={MapPin} label="Work Arrangement" value={workField.text} unavailable={workField.unavailable} />
              <DetailTile icon={Building2} label="Industry / Domain" value={industryField.text} unavailable={industryField.unavailable} />
            </div>

            <div className="space-y-2">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Key Responsibilities
              </h4>
              {Array.isArray(analysis.responsibilities) && analysis.responsibilities.length > 0 ? (
                <ul className="space-y-1.5">
                  {analysis.responsibilities.map((item, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-slate-700">
                      <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm italic text-slate-400">
                  No responsibilities explicitly stated in the job description.
                </p>
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
