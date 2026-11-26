import React from 'react';
import {
  AlertCircle,
  CheckCircle2,
  HelpCircle,
  Layers,
  RefreshCw,
  ShieldAlert,
  Sparkles,
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

const CLASSIFICATION_SECTIONS = [
  {
    key: 'Mandatory',
    title: 'Mandatory Skills',
    subtitle: 'Must-have requirements explicitly demanded by the employer',
    icon: ShieldAlert,
    badgeClass: 'border-rose-200 bg-rose-50 text-rose-800',
    cardClass: 'border-rose-200/80 bg-rose-50/40',
  },
  {
    key: 'Preferred',
    title: 'Preferred Skills',
    subtitle: 'Good-to-have skills that strengthen a candidate profile',
    icon: CheckCircle2,
    badgeClass: 'border-sky-200 bg-sky-50 text-sky-800',
    cardClass: 'border-sky-200/80 bg-sky-50/40',
  },
  {
    key: 'Optional',
    title: 'Optional Skills',
    subtitle: 'Explicitly additional or bonus skills',
    icon: Layers,
    badgeClass: 'border-slate-200 bg-slate-100 text-slate-700',
    cardClass: 'border-slate-200 bg-slate-50/60',
  },
  {
    key: 'Unspecified',
    title: 'Unspecified Skills',
    subtitle: 'Mentioned without clear priority or with ambiguous context',
    icon: HelpCircle,
    badgeClass: 'border-amber-200 bg-amber-50 text-amber-800',
    cardClass: 'border-amber-200/80 bg-amber-50/40',
  },
];

const PRIORITY_BADGE = {
  High: 'bg-rose-100 text-rose-800 border-rose-200',
  Medium: 'bg-sky-100 text-sky-800 border-sky-200',
  Low: 'bg-slate-100 text-slate-700 border-slate-200',
};

function SkillCard({ skill, badgeClass }) {
  const confidencePct = Math.round((Number(skill.confidence_score ?? 0) || 0) * 100);
  const priorityBadge = PRIORITY_BADGE[skill.priority_level] || PRIORITY_BADGE.Low;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-2xs space-y-2">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="space-y-0.5">
          <div className="flex flex-wrap items-center gap-2">
            <h5 className="text-sm font-semibold text-slate-900">{skill.name}</h5>
            {skill.original_name && (
              <span className="text-[11px] text-slate-400">({skill.original_name})</span>
            )}
          </div>
          <p className="text-xs text-slate-500">{skill.category || 'Other'}</p>
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium ${badgeClass}`}>
            {skill.classification}
          </span>
          <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium ${priorityBadge}`}>
            {skill.priority_level} Priority
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs pt-1 border-t border-slate-100">
        <div>
          <span className="text-slate-400 block text-[11px]">Priority Score</span>
          <span className="font-semibold text-slate-800">
            {skill.priority_score !== null && skill.priority_score !== undefined
              ? `${skill.priority_score}/100`
              : 'N/A'}
          </span>
        </div>
        <div>
          <span className="text-slate-400 block text-[11px]">Proficiency</span>
          <span className="font-medium text-slate-800">{skill.expected_proficiency || 'Unspecified'}</span>
        </div>
        <div>
          <span className="text-slate-400 block text-[11px]">Confidence</span>
          <span className="font-medium text-slate-800">{confidencePct}%</span>
        </div>
        <div>
          <span className="text-slate-400 block text-[11px]">Source</span>
          <span className="font-medium capitalize text-slate-800">{skill.source_type || 'explicit'}</span>
        </div>
      </div>

      {skill.evidence && (
        <p className="text-xs text-slate-600 bg-slate-50 rounded-lg px-2.5 py-1.5 border border-slate-100">
          <span className="font-medium text-slate-700">Evidence:</span> {skill.evidence}
        </p>
      )}
    </div>
  );
}

export function SkillClassificationSection({
  selectedJob,
  classification,
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
      : classification?.analysis_status || selectedJob.analysis_status || 'PENDING';

  const summary = classification?.classification_summary || {};
  const skills = classification?.skills || [];

  return (
    <Card>
      <CardHeader className="border-b border-slate-100 pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <CardTitle className="text-base">
                Skill Classification — {selectedJob.job_title}
              </CardTitle>
              <Badge variant="secondary" className="text-[11px]">
                {statusLabel}
              </Badge>
              {classification?.cached && (
                <Badge variant="outline" className="text-[11px]">
                  CACHED
                </Badge>
              )}
              {classification?.model_used && (
                <span className="text-[11px] text-slate-500">Model: {classification.model_used}</span>
              )}
            </div>
            <p className="text-xs text-slate-500">
              Evidence-based Mandatory, Preferred, Optional, and Unspecified skill classification with priority scoring.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-center">
            <Button
              type="button"
              size="sm"
              onClick={() => onAnalyze(selectedJob.id, Boolean(classification))}
              disabled={isLoading}
            >
              {classification ? (
                <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
              ) : (
                <Sparkles className="h-3.5 w-3.5 mr-1.5" />
              )}
              <span>{classification ? 'Re-analyze Skills' : 'Analyze Skills'}</span>
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-4 space-y-5">
        {error && (
          <Alert variant="error">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="flex flex-wrap items-center justify-between gap-2 w-full">
              <span>{error}</span>
              <Button type="button" size="sm" variant="outline" onClick={onRetry} disabled={isLoading}>
                Retry
              </Button>
            </AlertDescription>
          </Alert>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center py-8 text-sm text-slate-500 gap-2">
            <LoadingIndicator size="sm" />
            <span>Classifying skills and computing priority scores...</span>
          </div>
        ) : !classification ? (
          <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50/50 p-6 text-center space-y-2">
            <p className="text-sm font-medium text-slate-700">No skill classification generated yet</p>
            <p className="text-xs text-slate-500">
              Click <strong>Analyze Skills</strong> to classify extracted requirements into Mandatory, Preferred, Optional, and Unspecified tiers.
            </p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              <div className="rounded-xl border border-rose-200 bg-rose-50/60 p-3">
                <span className="text-[11px] font-medium text-rose-700">Mandatory</span>
                <p className="text-xl font-bold text-rose-900">{summary.mandatory_count ?? 0}</p>
              </div>
              <div className="rounded-xl border border-sky-200 bg-sky-50/60 p-3">
                <span className="text-[11px] font-medium text-sky-700">Preferred</span>
                <p className="text-xl font-bold text-sky-900">{summary.preferred_count ?? 0}</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <span className="text-[11px] font-medium text-slate-600">Optional</span>
                <p className="text-xl font-bold text-slate-900">{summary.optional_count ?? 0}</p>
              </div>
              <div className="rounded-xl border border-amber-200 bg-amber-50/60 p-3">
                <span className="text-[11px] font-medium text-amber-700">Unspecified</span>
                <p className="text-xl font-bold text-amber-900">{summary.unspecified_count ?? 0}</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-3">
                <span className="text-[11px] font-medium text-slate-500">Total Skills</span>
                <p className="text-xl font-bold text-slate-900">{summary.total_skills ?? skills.length}</p>
              </div>
            </div>

            <div className="space-y-4">
              {CLASSIFICATION_SECTIONS.map((section) => {
                const Icon = section.icon;
                const groupSkills = skills.filter((s) => s.classification === section.key);
                return (
                  <div
                    key={section.key}
                    className={`rounded-xl border p-4 space-y-3 ${section.cardClass}`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <Icon className="h-4 w-4 text-slate-700" />
                        <div>
                          <h4 className="text-sm font-semibold text-slate-900">{section.title}</h4>
                          <p className="text-[11px] text-slate-500">{section.subtitle}</p>
                        </div>
                      </div>
                      <Badge variant="secondary" className="text-[11px]">
                        {groupSkills.length}
                      </Badge>
                    </div>

                    {groupSkills.length === 0 ? (
                      <p className="text-xs italic text-slate-500">No skills classified in this tier.</p>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {groupSkills.map((skill, idx) => (
                          <SkillCard
                            key={`${skill.name}-${idx}`}
                            skill={skill}
                            badgeClass={section.badgeClass}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
