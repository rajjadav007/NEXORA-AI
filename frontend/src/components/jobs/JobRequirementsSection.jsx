import React from 'react';
import {
  AlertCircle,
  Award,
  Briefcase,
  Code2,
  Cpu,
  Database,
  Globe,
  GraduationCap,
  Layers,
  RefreshCw,
  Users,
  Wrench,
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

const TECH_GROUPS = [
  { key: 'Programming Language', label: 'Programming Languages', icon: Code2 },
  { key: 'AI & Machine Learning', label: 'AI & Machine Learning', icon: Cpu },
  { key: 'Framework & Library', label: 'Frameworks & Libraries', icon: Layers },
  { key: 'Tool & Platform', label: 'Tools & Platforms', icon: Wrench },
  { key: 'Database', label: 'Databases', icon: Database },
];

const IMPORTANCE_STYLES = {
  Mandatory: 'border-rose-200 bg-rose-50 text-rose-800',
  Preferred: 'border-sky-200 bg-sky-50 text-sky-800',
  Optional: 'border-slate-200 bg-slate-50 text-slate-700',
  Unspecified: 'border-amber-200 bg-amber-50 text-amber-800',
};

function RequirementChip({ item }) {
  const style = IMPORTANCE_STYLES[item.importance] || IMPORTANCE_STYLES.Unspecified;
  return (
    <div
      className={`rounded-lg border px-2.5 py-1.5 text-xs ${style}`}
      title={item.evidence || item.name}
    >
      <div className="flex items-center gap-1.5 font-semibold">
        <span>{item.name}</span>
        <span className="text-[10px] opacity-75">• {item.importance}</span>
      </div>
      {item.evidence && (
        <p className="text-[11px] opacity-80 mt-0.5 line-clamp-1">{item.evidence}</p>
      )}
    </div>
  );
}

function RequirementListGroup({ title, icon: Icon, items }) {
  if (!items || items.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-3.5">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 mb-1.5">
          {Icon && <Icon className="h-3.5 w-3.5 text-slate-400" />}
          <span>{title}</span>
        </div>
        <p className="text-xs italic text-slate-400">None specified</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-3.5 space-y-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700">
          {Icon && <Icon className="h-3.5 w-3.5 text-slate-500" />}
          <span>{title}</span>
        </div>
        <span className="text-[11px] text-slate-500">{items.length}</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {items.map((item, idx) => (
          <RequirementChip key={`${item.name}-${idx}`} item={item} />
        ))}
      </div>
    </div>
  );
}

export function JobRequirementsSection({
  selectedJob,
  requirements,
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
      : requirements?.analysis_status || selectedJob.analysis_status || 'PENDING';

  const techSkills = requirements?.technical_skills || [];
  const mandatoryTech = techSkills.filter((s) => s.importance === 'Mandatory');
  const preferredTech = techSkills.filter((s) => s.importance !== 'Mandatory');
  const knownGroupKeys = new Set(TECH_GROUPS.map((g) => g.key));
  const otherTech = techSkills.filter((s) => !knownGroupKeys.has(s.category));

  const edu = requirements?.education || {};
  const exp = requirements?.experience || {};
  const counts = requirements?.summary_counts || {};

  return (
    <Card>
      <CardHeader className="border-b border-slate-100 pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <CardTitle className="text-base">Job Requirements Analysis</CardTitle>
              <Badge variant="secondary" className="text-[11px]">
                {statusLabel}
              </Badge>
              {requirements?.cached && (
                <Badge variant="outline" className="text-[11px]">
                  Cached
                </Badge>
              )}
            </div>
            <p className="text-xs text-slate-500">
              {selectedJob.job_title} • {selectedJob.company_name}
            </p>
          </div>

          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => onAnalyze(selectedJob.id, Boolean(requirements))}
            disabled={isLoading}
          >
            <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>{requirements ? 'Re-analyze Requirements' : 'Analyze Requirements'}</span>
          </Button>
        </div>
      </CardHeader>

      <CardContent className="pt-5 space-y-6">
        {isLoading && (
          <div className="flex items-center justify-center py-8 gap-2.5 text-sm text-slate-600">
            <LoadingIndicator size="sm" />
            <span>Extracting technical skills, education, and experience requirements...</span>
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

        {!isLoading && !error && requirements && (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="rounded-xl border border-rose-200 bg-rose-50/70 p-3">
                <p className="text-[11px] font-medium text-rose-700">Mandatory</p>
                <p className="text-lg font-bold text-rose-900">{counts.mandatory_count ?? 0}</p>
              </div>
              <div className="rounded-xl border border-sky-200 bg-sky-50/70 p-3">
                <p className="text-[11px] font-medium text-sky-700">Preferred</p>
                <p className="text-lg font-bold text-sky-900">{counts.preferred_count ?? 0}</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <p className="text-[11px] font-medium text-slate-600">Optional / Unspecified</p>
                <p className="text-lg font-bold text-slate-900">
                  {(counts.optional_count ?? 0) + (counts.unspecified_count ?? 0)}
                </p>
              </div>
              <div className="rounded-xl border border-indigo-200 bg-indigo-50/70 p-3">
                <p className="text-[11px] font-medium text-indigo-700">Total Extracted</p>
                <p className="text-lg font-bold text-indigo-900">{counts.total_requirements ?? 0}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="rounded-xl border border-rose-200 bg-rose-50/30 p-4 space-y-2.5">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-rose-700">
                  Mandatory Technical Skills ({mandatoryTech.length})
                </h4>
                {mandatoryTech.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {mandatoryTech.map((item, idx) => (
                      <RequirementChip key={`m-${item.name}-${idx}`} item={item} />
                    ))}
                  </div>
                ) : (
                  <p className="text-xs italic text-slate-400">No mandatory technical skills stated.</p>
                )}
              </div>

              <div className="rounded-xl border border-sky-200 bg-sky-50/30 p-4 space-y-2.5">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-sky-700">
                  Preferred / Optional Technical Skills ({preferredTech.length})
                </h4>
                {preferredTech.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {preferredTech.map((item, idx) => (
                      <RequirementChip key={`p-${item.name}-${idx}`} item={item} />
                    ))}
                  </div>
                ) : (
                  <p className="text-xs italic text-slate-400">No preferred technical skills stated.</p>
                )}
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Technical Skills by Category
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {TECH_GROUPS.map((group) => (
                  <RequirementListGroup
                    key={group.key}
                    title={group.label}
                    icon={group.icon}
                    items={techSkills.filter((s) => s.category === group.key)}
                  />
                ))}
                {otherTech.length > 0 && (
                  <RequirementListGroup title="Other Technical Skills" icon={Code2} items={otherTech} />
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-4 space-y-2">
                <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-600">
                  <GraduationCap className="h-4 w-4 text-slate-500" />
                  <span>Educational Requirements & Certifications</span>
                </div>
                <div className="text-xs space-y-1 text-slate-700">
                  <p>
                    <span className="font-semibold">Minimum Level:</span>{' '}
                    {edu.minimum_level || <span className="italic text-slate-400">Not specified</span>}
                  </p>
                  <p>
                    <span className="font-semibold">Required Degree:</span>{' '}
                    {edu.required_degree || <span className="italic text-slate-400">Not specified</span>}
                  </p>
                  <p>
                    <span className="font-semibold">Preferred Degree:</span>{' '}
                    {edu.preferred_degree || <span className="italic text-slate-400">Not specified</span>}
                  </p>
                  <p>
                    <span className="font-semibold">Academic Fields:</span>{' '}
                    {edu.required_fields?.length ? (
                      edu.required_fields.join(', ')
                    ) : (
                      <span className="italic text-slate-400">Not specified</span>
                    )}
                  </p>
                  <div className="flex items-start gap-1.5 pt-1">
                    <Award className="h-3.5 w-3.5 text-slate-400 mt-0.5 shrink-0" />
                    <span>
                      <span className="font-semibold">Certifications:</span>{' '}
                      {[...(edu.required_certifications || []), ...(edu.preferred_certifications || [])].length
                        ? [...(edu.required_certifications || []), ...(edu.preferred_certifications || [])].join(', ')
                        : 'None specified'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-4 space-y-2">
                <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-600">
                  <Briefcase className="h-4 w-4 text-slate-500" />
                  <span>Experience Requirements</span>
                </div>
                <div className="text-xs space-y-1 text-slate-700">
                  <p>
                    <span className="font-semibold">Years:</span>{' '}
                    {exp.minimum_years !== null && exp.minimum_years !== undefined
                      ? `${exp.minimum_years}${
                          exp.maximum_years !== null && exp.maximum_years !== undefined
                            ? `–${exp.maximum_years}`
                            : '+'
                        } years`
                      : 'Not specified'}
                  </p>
                  <p>
                    <span className="font-semibold">Fresher Eligible:</span>{' '}
                    {exp.fresher_eligible === true
                      ? 'Yes'
                      : exp.fresher_eligible === false
                        ? 'No'
                        : 'Not specified'}
                  </p>
                  {exp.professional_experience && (
                    <p>
                      <span className="font-semibold">Professional:</span> {exp.professional_experience}
                    </p>
                  )}
                  {exp.internship_experience && (
                    <p>
                      <span className="font-semibold">Internship:</span> {exp.internship_experience}
                    </p>
                  )}
                  {exp.project_experience && (
                    <p>
                      <span className="font-semibold">Project:</span> {exp.project_experience}
                    </p>
                  )}
                  {exp.domain_experience && (
                    <p>
                      <span className="font-semibold">Domain:</span> {exp.domain_experience}
                    </p>
                  )}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <RequirementListGroup title="Soft Skills" icon={Users} items={requirements.soft_skills} />
              <RequirementListGroup title="Domain Knowledge" icon={Globe} items={requirements.domain_knowledge} />
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
