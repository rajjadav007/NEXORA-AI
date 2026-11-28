import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  Briefcase,
  CheckCircle2,
  FolderGit2,
  GraduationCap,
  HelpCircle,
  Layers,
  RefreshCw,
  ShieldAlert,
  Sparkles,
  Target,
  TrendingUp,
} from 'lucide-react';
import { PageHeader } from '../components/layout/PageHeader';
import { EmptyState } from '../components/layout/EmptyState';
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
  Select,
} from '../components/ui';
import { getSavedResumes } from '../services/resumeService';
import { listJobDescriptions } from '../services/jobDescriptionService';
import { compareResumeAndJob, getJobMatchById, listJobMatches } from '../services/jobMatchService';

const STATUS_BADGE = {
  Matched: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  'Partially Matched': 'border-amber-200 bg-amber-50 text-amber-800',
  Missing: 'border-rose-200 bg-rose-50 text-rose-800',
  'Not Verifiable': 'border-slate-200 bg-slate-100 text-slate-700',
};

function scoreColorClass(score) {
  if (score >= 75) return 'text-emerald-600';
  if (score >= 50) return 'text-amber-600';
  return 'text-rose-600';
}

function SkillMatchCard({ title, icon: Icon, items, badgeClass, emptyText }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <Icon className="h-4 w-4 text-slate-600" />
            {title}
          </span>
          <Badge variant="outline" className={badgeClass}>
            {items.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-slate-500">{emptyText}</p>
        ) : (
          <ul className="space-y-2.5">
            {items.map((item, idx) => (
              <li
                key={`${item.requirement}-${idx}`}
                className="rounded-lg border border-slate-100 bg-slate-50/70 p-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-sm font-semibold text-slate-900">{item.requirement}</span>
                  <div className="flex items-center gap-1.5">
                    {item.importance && item.importance !== 'Unspecified' && (
                      <Badge variant="outline" className="text-[11px]">
                        {item.importance}
                      </Badge>
                    )}
                    <Badge variant="outline" className={badgeClass}>
                      {item.status}
                    </Badge>
                  </div>
                </div>
                {item.matched_with && (
                  <p className="mt-1 text-xs text-slate-600">
                    Matched with: <span className="font-medium text-slate-800">{item.matched_with}</span>
                  </p>
                )}
                {item.reason && <p className="mt-1 text-xs text-slate-500">{item.reason}</p>}
                {Array.isArray(item.evidence) && item.evidence.length > 0 && (
                  <p className="mt-1 text-xs text-teal-700">Evidence: {item.evidence[0]}</p>
                )}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

export function MatchingPage() {
  const [resumes, setResumes] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [savedMatches, setSavedMatches] = useState([]);
  const [selectedResumeId, setSelectedResumeId] = useState('');
  const [selectedJobId, setSelectedJobId] = useState('');
  const [matchResult, setMatchResult] = useState(null);

  const [isLoadingOptions, setIsLoadingOptions] = useState(true);
  const [isComparing, setIsComparing] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    async function loadInitialData() {
      setIsLoadingOptions(true);
      setError('');
      try {
        const [resumesRes, jobsRes, matchesRes] = await Promise.all([
          getSavedResumes().catch(() => ({ data: [] })),
          listJobDescriptions().catch(() => ({ data: [] })),
          listJobMatches().catch(() => ({ data: [] })),
        ]);
        if (!active) return;
        const resumeList = resumesRes?.data || [];
        const jobList = jobsRes?.data || [];
        const matchList = matchesRes?.data || [];
        setResumes(resumeList);
        setJobs(jobList);
        setSavedMatches(matchList);
        if (resumeList.length > 0) setSelectedResumeId(resumeList[0].id);
        if (jobList.length > 0) setSelectedJobId(jobList[0].id);
      } catch (err) {
        if (active) setError(err.message || 'Failed to load resumes and job descriptions.');
      } finally {
        if (active) setIsLoadingOptions(false);
      }
    }
    loadInitialData();
    return () => {
      active = false;
    };
  }, []);

  async function handleCompare(regenerate = false) {
    if (!selectedResumeId || !selectedJobId) {
      setError('Please select both a resume and a job description to compare.');
      return;
    }
    setIsComparing(true);
    setError('');
    try {
      const response = await compareResumeAndJob({
        resumeId: selectedResumeId,
        jobDescriptionId: selectedJobId,
        regenerate,
      });
      setMatchResult(response.data);
      const matchesRes = await listJobMatches().catch(() => null);
      if (matchesRes?.data) setSavedMatches(matchesRes.data);
    } catch (err) {
      setError(err.message || 'Failed to compare resume and job description.');
    } finally {
      setIsComparing(false);
    }
  }

  async function handleLoadSavedMatch(matchId) {
    setIsComparing(true);
    setError('');
    try {
      const response = await getJobMatchById(matchId);
      setMatchResult(response.data);
      setSelectedResumeId(response.data.resume_id);
      setSelectedJobId(response.data.job_description_id);
    } catch (err) {
      setError(err.message || 'Failed to load saved match.');
    } finally {
      setIsComparing(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Resume-to-Job Matching"
        description="Evidence-backed comparison between your analyzed resume and target job requirements."
        badge="Feature #39"
      />

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Selection Controls */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Select Candidate Resume &amp; Target Job</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoadingOptions ? (
            <LoadingIndicator label="Loading analyzed resumes and job descriptions..." />
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-12 md:items-end">
              <div className="space-y-1.5 md:col-span-5">
                <label htmlFor="resume-selector" className="text-xs font-medium text-slate-600">
                  Analyzed Resume
                </label>
                <Select
                  id="resume-selector"
                  value={selectedResumeId}
                  onChange={(e) => setSelectedResumeId(e.target.value)}
                  disabled={resumes.length === 0 || isComparing}
                >
                  {resumes.length === 0 ? (
                    <option value="">No saved resumes found</option>
                  ) : (
                    resumes.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.original_filename}
                      </option>
                    ))
                  )}
                </Select>
              </div>

              <div className="space-y-1.5 md:col-span-5">
                <label htmlFor="job-selector" className="text-xs font-medium text-slate-600">
                  Job Description
                </label>
                <Select
                  id="job-selector"
                  value={selectedJobId}
                  onChange={(e) => setSelectedJobId(e.target.value)}
                  disabled={jobs.length === 0 || isComparing}
                >
                  {jobs.length === 0 ? (
                    <option value="">No job descriptions found</option>
                  ) : (
                    jobs.map((j) => (
                      <option key={j.id} value={j.id}>
                        {j.job_title} — {j.company_name}
                      </option>
                    ))
                  )}
                </Select>
              </div>

              <div className="flex gap-2 md:col-span-2">
                <Button
                  type="button"
                  onClick={() => handleCompare(false)}
                  disabled={!selectedResumeId || !selectedJobId || isComparing}
                  className="w-full"
                >
                  {isComparing ? 'Matching...' : 'Compare'}
                </Button>
                {matchResult && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => handleCompare(true)}
                    disabled={isComparing}
                    title="Recalculate match"
                  >
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {isComparing && (
        <Card>
          <CardContent className="py-10">
            <LoadingIndicator label="Evaluating skills, experience, education, and projects..." />
          </CardContent>
        </Card>
      )}

      {!isComparing && !matchResult && (
        <EmptyState
          icon={Target}
          title="Ready to Compare"
          description="Select an analyzed resume and a job description above, then click Compare to calculate a weighted match score."
        />
      )}

      {!isComparing && matchResult && (
        <div className="space-y-6">
          {/* Overall Score & Breakdown */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <Card className="lg:col-span-1">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center justify-between text-base">
                  <span>Overall Match Score</span>
                  <Badge variant="outline">v{matchResult.version_number}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-baseline gap-2">
                  <span className={`text-5xl font-bold ${scoreColorClass(matchResult.overall_match_score)}`}>
                    {Math.round(matchResult.overall_match_score)}%
                  </span>
                  <span className="text-xs text-slate-500">
                    ({matchResult.overall_match_score.toFixed(1)} / 100)
                  </span>
                </div>
                <p className="text-xs text-slate-600">
                  {matchResult.resume_filename} vs {matchResult.job_title} ({matchResult.company_name})
                </p>
                <div className="grid grid-cols-2 gap-2 pt-1 text-xs">
                  <div className="rounded-md bg-emerald-50 p-2 text-emerald-800">
                    <span className="font-semibold">{matchResult.summary_counts.matched_count}</span> Matched
                  </div>
                  <div className="rounded-md bg-amber-50 p-2 text-amber-800">
                    <span className="font-semibold">{matchResult.summary_counts.partially_matched_count}</span> Partial
                  </div>
                  <div className="rounded-md bg-rose-50 p-2 text-rose-800">
                    <span className="font-semibold">{matchResult.summary_counts.missing_count}</span> Missing
                  </div>
                  <div className="rounded-md bg-slate-100 p-2 text-slate-700">
                    <span className="font-semibold">{matchResult.summary_counts.not_verifiable_count}</span> Unverifiable
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Layers className="h-4 w-4 text-slate-600" />
                  Weighted Score Breakdown
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {Object.values(matchResult.score_breakdown?.categories || {}).map((cat) => (
                  <div key={cat.category} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-slate-800">
                        {cat.label}{' '}
                        <span className="text-slate-400">
                          (Weight {Math.round(cat.configured_weight * 100)}%
                          {cat.available && cat.applied_weight !== cat.configured_weight
                            ? ` -> Normalized ${Math.round(cat.applied_weight * 100)}%`
                            : ''}
                          )
                        </span>
                      </span>
                      <span className="font-semibold text-slate-900">
                        {cat.available ? `${cat.raw_score?.toFixed(1)}%` : 'Not Verifiable'}
                      </span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                      <div
                        className={`h-full rounded-full ${cat.available ? 'bg-teal-600' : 'bg-slate-300'}`}
                        style={{ width: `${cat.available ? cat.raw_score || 0 : 0}%` }}
                      />
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Skills Sections */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <SkillMatchCard
              title="Matching Skills"
              icon={CheckCircle2}
              items={matchResult.matching_skills || []}
              badgeClass={STATUS_BADGE.Matched}
              emptyText="No directly matched technical skills found."
            />
            <SkillMatchCard
              title="Partially Matching Skills"
              icon={AlertCircle}
              items={matchResult.partially_matching_skills || []}
              badgeClass={STATUS_BADGE['Partially Matched']}
              emptyText="No partially matched technical skills."
            />
            <SkillMatchCard
              title="Missing Skills"
              icon={ShieldAlert}
              items={matchResult.missing_skills || []}
              badgeClass={STATUS_BADGE.Missing}
              emptyText="No missing technical skills identified."
            />
          </div>

          {/* Experience & Education Comparison */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center justify-between text-base">
                  <span className="flex items-center gap-2">
                    <Briefcase className="h-4 w-4 text-slate-600" />
                    Experience Comparison
                  </span>
                  <Badge variant="outline" className={STATUS_BADGE[matchResult.experience_match?.status]}>
                    {matchResult.experience_match?.status}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-slate-700">
                <p>{matchResult.experience_match?.summary}</p>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="rounded-md border border-slate-100 bg-slate-50 p-2.5">
                    <span className="block text-slate-500">Candidate Experience</span>
                    <span className="font-semibold text-slate-900">
                      {matchResult.experience_match?.candidate_total_years != null
                        ? `${matchResult.experience_match.candidate_total_years} years`
                        : 'Unavailable'}
                    </span>
                  </div>
                  <div className="rounded-md border border-slate-100 bg-slate-50 p-2.5">
                    <span className="block text-slate-500">Required Minimum</span>
                    <span className="font-semibold text-slate-900">
                      {matchResult.experience_match?.required_min_years != null
                        ? `${matchResult.experience_match.required_min_years}+ years`
                        : 'Not specified'}
                    </span>
                  </div>
                </div>
                {matchResult.experience_match?.relevant_roles?.length > 0 && (
                  <div className="space-y-1.5">
                    <p className="text-xs font-semibold text-slate-600">Relevant Roles</p>
                    {matchResult.experience_match.relevant_roles.map((role, idx) => (
                      <div key={idx} className="rounded-md border border-slate-100 p-2 text-xs">
                        <span className="font-medium text-slate-900">{role.job_title || 'Role'}</span>
                        {role.company ? ` at ${role.company}` : ''}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center justify-between text-base">
                  <span className="flex items-center gap-2">
                    <GraduationCap className="h-4 w-4 text-slate-600" />
                    Education Comparison
                  </span>
                  <Badge variant="outline" className={STATUS_BADGE[matchResult.education_match?.status]}>
                    {matchResult.education_match?.status}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-slate-700">
                <p>{matchResult.education_match?.summary}</p>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="rounded-md border border-slate-100 bg-slate-50 p-2.5">
                    <span className="block text-slate-500">Required Education</span>
                    <span className="font-semibold text-slate-900">
                      {matchResult.education_match?.required_degree || 'Not specified'}
                    </span>
                  </div>
                  <div className="rounded-md border border-slate-100 bg-slate-50 p-2.5">
                    <span className="block text-slate-500">Candidate Degree(s)</span>
                    <span className="font-semibold text-slate-900">
                      {matchResult.education_match?.candidate_degrees?.length > 0
                        ? matchResult.education_match.candidate_degrees
                            .map((d) => d.degree)
                            .filter(Boolean)
                            .join(', ')
                        : 'Unavailable'}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Relevant Projects & Not Verifiable */}
          {matchResult.relevant_projects?.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <FolderGit2 className="h-4 w-4 text-slate-600" />
                  Relevant Projects
                </CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-1 gap-3 md:grid-cols-2">
                {matchResult.relevant_projects.map((proj) => (
                  <div key={proj.project_id} className="rounded-lg border border-slate-100 bg-slate-50/70 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-semibold text-slate-900">{proj.project_title}</span>
                      <Badge variant="outline">{Math.round(proj.relevance_score)}% relevant</Badge>
                    </div>
                    {proj.matched_skills?.length > 0 && (
                      <p className="mt-1 text-xs text-teal-700">
                        Matched skills: {proj.matched_skills.join(', ')}
                      </p>
                    )}
                    {proj.evidence?.length > 0 && (
                      <p className="mt-1 text-xs text-slate-500">{proj.evidence[0]}</p>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Strengths & Improvement Areas */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Sparkles className="h-4 w-4 text-emerald-600" />
                  Strengths for This Role
                </CardTitle>
              </CardHeader>
              <CardContent>
                {matchResult.strengths?.length > 0 ? (
                  <ul className="list-disc space-y-1.5 pl-4 text-sm text-slate-700">
                    {matchResult.strengths.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-slate-500">No major strengths highlighted yet.</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <TrendingUp className="h-4 w-4 text-amber-600" />
                  Areas Needing Improvement
                </CardTitle>
              </CardHeader>
              <CardContent>
                {matchResult.improvement_areas?.length > 0 ? (
                  <ul className="list-disc space-y-1.5 pl-4 text-sm text-slate-700">
                    {matchResult.improvement_areas.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-slate-500">No improvement gaps detected.</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Not Verifiable Requirements */}
          {matchResult.not_verifiable_requirements?.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <HelpCircle className="h-4 w-4 text-slate-500" />
                  Not Verifiable Requirements ({matchResult.not_verifiable_requirements.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {matchResult.not_verifiable_requirements.map((item, idx) => (
                  <div key={idx} className="rounded-md border border-slate-100 bg-slate-50 p-2.5 text-xs">
                    <span className="font-semibold text-slate-800">{item.requirement}</span>
                    {item.reason && <span className="ml-2 text-slate-500">— {item.reason}</span>}
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Saved Match History */}
      {savedMatches.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Recent Saved Matches</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {savedMatches.slice(0, 5).map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => handleLoadSavedMatch(m.id)}
                className="flex w-full items-center justify-between rounded-lg border border-slate-200 bg-white px-3 py-2 text-left text-sm hover:bg-slate-50"
              >
                <div>
                  <span className="font-medium text-slate-900">
                    {m.job_title || 'Job'} {m.company_name ? `(${m.company_name})` : ''}
                  </span>
                  <span className="ml-2 text-xs text-slate-500">{m.resume_filename}</span>
                </div>
                <Badge variant="outline">{Math.round(m.overall_match_score)}%</Badge>
              </button>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
