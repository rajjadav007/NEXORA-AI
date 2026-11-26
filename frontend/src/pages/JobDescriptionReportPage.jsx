import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  AlertCircle,
  ArrowLeft,
  Award,
  Brain,
  Briefcase,
  Building2,
  CheckCircle2,
  Clock,
  Code2,
  Cpu,
  Database,
  FileBarChart2,
  Globe,
  GraduationCap,
  Layers,
  MapPin,
  RefreshCw,
  ShieldAlert,
  Sparkles,
  Users,
  Wrench,
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
} from '../components/ui';
import {
  generateJobDescriptionReport,
  getJobDescriptionReport,
  listJobDescriptions,
} from '../services/jobDescriptionService';

const TECH_BUCKETS = [
  { key: 'programming_languages', label: 'Programming Languages', icon: Code2 },
  { key: 'ai_and_machine_learning', label: 'AI & Machine Learning', icon: Cpu },
  { key: 'frameworks_and_libraries', label: 'Frameworks & Libraries', icon: Layers },
  { key: 'tools_and_platforms', label: 'Tools & Platforms', icon: Wrench },
  { key: 'databases', label: 'Databases', icon: Database },
  { key: 'cloud_technologies', label: 'Cloud Technologies', icon: Globe },
  { key: 'other_technical_skills', label: 'Other Technical Skills', icon: Briefcase },
];

const SKILL_TIERS = [
  { key: 'mandatory', title: 'Mandatory Skills', badge: 'border-rose-200 bg-rose-50 text-rose-800', icon: ShieldAlert },
  { key: 'preferred', title: 'Preferred Skills', badge: 'border-sky-200 bg-sky-50 text-sky-800', icon: CheckCircle2 },
  { key: 'optional', title: 'Optional Skills', badge: 'border-slate-200 bg-slate-100 text-slate-700', icon: Layers },
  { key: 'unspecified', title: 'Unspecified Skills', badge: 'border-amber-200 bg-amber-50 text-amber-800', icon: AlertCircle },
];

const COMPLEXITY_BADGE = {
  Beginner: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  Intermediate: 'bg-sky-50 text-sky-800 border-sky-200',
  Advanced: 'bg-amber-50 text-amber-800 border-amber-200',
  Expert: 'bg-rose-50 text-rose-800 border-rose-200',
};

function MetaField({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-100 bg-slate-50/70 p-2.5">
      <span className="block text-[11px] font-medium text-slate-500">{label}</span>
      <span className="text-sm font-semibold text-slate-900">{value || 'Unknown'}</span>
    </div>
  );
}

export function JobDescriptionReportPage() {
  const { jobId: routeJobId } = useParams();
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState(routeJobId || '');
  const [report, setReport] = useState(null);
  const [isLoadingJobs, setIsLoadingJobs] = useState(true);
  const [isLoadingReport, setIsLoadingReport] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (routeJobId) {
      setSelectedJobId(routeJobId);
    }
  }, [routeJobId]);

  useEffect(() => {
    let active = true;
    async function loadJobs() {
      setIsLoadingJobs(true);
      try {
        const res = await listJobDescriptions();
        const items = res?.data || [];
        if (active) {
          setJobs(items);
          if (!routeJobId && items.length > 0) {
            setSelectedJobId(items[0].id);
          }
        }
      } catch (err) {
        if (active) {
          setError(err.message || 'Unable to load saved job descriptions.');
        }
      } finally {
        if (active) {
          setIsLoadingJobs(false);
        }
      }
    }
    loadJobs();
    return () => {
      active = false;
    };
  }, [routeJobId]);

  useEffect(() => {
    if (!selectedJobId) {
      setReport(null);
      return;
    }
    let active = true;
    async function loadSavedReport() {
      setIsLoadingReport(true);
      setError('');
      try {
        const res = await getJobDescriptionReport(selectedJobId);
        if (active) {
          setReport(res?.data || null);
        }
      } catch (err) {
        if (active) {
          // 404 simply means report not generated yet
          setReport(null);
          if (err.status && err.status !== 404) {
            setError(err.message || 'Failed to load saved report.');
          }
        }
      } finally {
        if (active) {
          setIsLoadingReport(false);
        }
      }
    }
    loadSavedReport();
    return () => {
      active = false;
    };
  }, [selectedJobId]);

  const handleGenerate = async (regenerate = false) => {
    if (!selectedJobId) return;
    setIsGenerating(true);
    setError('');
    try {
      const res = await generateJobDescriptionReport(selectedJobId, { regenerate });
      if (res?.data) {
        setReport(res.data);
      }
    } catch (err) {
      setError(err.message || 'Failed to generate job description report.');
    } finally {
      setIsGenerating(false);
    }
  };

  const overview = report?.overview || {};
  const role = report?.role_analysis || {};
  const tech = report?.technical_requirements || {};
  const skillClass = report?.skill_classification || {};
  const edu = report?.education || {};
  const exp = report?.experience || {};
  const complexity = report?.complexity_analysis || {};
  const eligibility = report?.eligibility_criteria || {};

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <PageHeader
          title="Job Description Report"
          description="Comprehensive career intelligence report combining role metadata, technical requirements, skill priorities, and AI insights."
          badge="Phase 6 • Feature 38"
        />

        <div className="flex flex-wrap items-center gap-2">
          <Link to="/jobs">
            <Button type="button" variant="outline" size="sm">
              <ArrowLeft className="h-3.5 w-3.5 mr-1.5" />
              <span>Back to Jobs</span>
            </Button>
          </Link>

          {selectedJobId && (
            <Button
              type="button"
              size="sm"
              onClick={() => handleGenerate(Boolean(report))}
              disabled={isGenerating || isLoadingReport}
            >
              {report ? (
                <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
              ) : (
                <Sparkles className="h-3.5 w-3.5 mr-1.5" />
              )}
              <span>{report ? 'Regenerate Report' : 'Generate Report'}</span>
            </Button>
          )}
        </div>
      </div>

      {!isLoadingJobs && jobs.length > 0 && (
        <Card>
          <CardContent className="pt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-xs font-medium text-slate-600">
              <Briefcase className="h-4 w-4 text-slate-400" />
              <span>Selected Job Posting:</span>
            </div>
            <select
              value={selectedJobId}
              onChange={(e) => {
                const nextId = e.target.value;
                setSelectedJobId(nextId);
                navigate(`/jobs/${nextId}/report`);
              }}
              className="w-full sm:w-96 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-900"
            >
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.job_title} — {job.company_name}
                </option>
              ))}
            </select>
          </CardContent>
        </Card>
      )}

      {error && (
        <Alert variant="error">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex flex-wrap items-center justify-between gap-2 w-full">
            <span>{error}</span>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => handleGenerate(Boolean(report))}
              disabled={isGenerating}
            >
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {isLoadingJobs || isLoadingReport || isGenerating ? (
        <Card>
          <CardContent className="py-12 flex items-center justify-center gap-2 text-sm text-slate-500">
            <LoadingIndicator size="sm" />
            <span>
              {isGenerating
                ? 'Generating comprehensive Job Description Report...'
                : 'Loading Job Description Report...'}
            </span>
          </CardContent>
        </Card>
      ) : jobs.length === 0 ? (
        <EmptyState
          icon={FileBarChart2}
          title="No Saved Job Descriptions"
          description="Save and analyze a job description first, then return here to generate a complete report."
        />
      ) : !report ? (
        <Card>
          <CardContent className="py-10 text-center space-y-3">
            <FileBarChart2 className="h-10 w-10 text-slate-300 mx-auto" />
            <h3 className="text-base font-semibold text-slate-900">Report Not Generated Yet</h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              Ensure Role Analysis (#35), Requirement Extraction (#36), and Skill Classification (#37) are completed for this job, then click <strong>Generate Report</strong>.
            </p>
            <Button type="button" size="sm" onClick={() => handleGenerate(false)}>
              <Sparkles className="h-3.5 w-3.5 mr-1.5" />
              <span>Generate Report</span>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {/* Report Metadata Bar */}
          <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-xs text-slate-600">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="secondary">v{report.report_version}</Badge>
              {report.cached && <Badge variant="outline">CACHED</Badge>}
              {report.model_used && <span>Model: {report.model_used}</span>}
            </div>
            <span className="inline-flex items-center gap-1">
              <Clock className="h-3.5 w-3.5" />
              Generated: {new Date(report.generated_at).toLocaleString()}
            </span>
          </div>

          {/* 1. Job Overview */}
          <Card>
            <CardHeader className="border-b border-slate-100 pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Building2 className="h-4 w-4 text-slate-600" />
                <span>1. Job Overview</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <MetaField label="Job Title" value={overview.job_title} />
                <MetaField label="Company" value={overview.company_name} />
                <MetaField label="Location" value={overview.location} />
                <MetaField label="Employment Type" value={overview.employment_type} />
                <MetaField label="Work Arrangement" value={overview.work_arrangement} />
                <MetaField label="Seniority Level" value={overview.seniority_level} />
                <MetaField label="Experience" value={overview.experience_requirements} />
                <MetaField label="Industry" value={overview.industry} />
              </div>
              {overview.job_description_summary && (
                <p className="text-xs text-slate-600 bg-slate-50 rounded-lg p-3 border border-slate-100">
                  {overview.job_description_summary}
                </p>
              )}
            </CardContent>
          </Card>

          {/* 2. Role Analysis & 11. Job Complexity */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader className="border-b border-slate-100 pb-3">
                <CardTitle className="text-base">2. Role Analysis</CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <MetaField label="Standardized Role" value={role.standardized_role} />
                  <MetaField label="Department" value={role.department} />
                  <MetaField label="Category" value={role.category} />
                  <MetaField label="Industry" value={role.industry} />
                </div>
                {role.role_summary && (
                  <p className="text-xs text-slate-600">{role.role_summary}</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="border-b border-slate-100 pb-3">
                <CardTitle className="text-base flex items-center justify-between gap-2">
                  <span>11. Job Complexity</span>
                  <span
                    className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${
                      COMPLEXITY_BADGE[complexity.level] || COMPLEXITY_BADGE.Intermediate
                    }`}
                  >
                    {complexity.level || 'Intermediate'}
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-2">
                <p className="text-sm text-slate-700">{complexity.explanation || 'No explanation provided.'}</p>
                <p className="text-[11px] italic text-slate-500">{complexity.disclaimer}</p>
              </CardContent>
            </Card>
          </div>

          {/* 3. Technical Requirements */}
          <Card>
            <CardHeader className="border-b border-slate-100 pb-3">
              <CardTitle className="text-base">3. Technical Requirements</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
              {TECH_BUCKETS.map((bucket) => {
                const Icon = bucket.icon;
                const items = tech[bucket.key] || [];
                return (
                  <div key={bucket.key} className="rounded-xl border border-slate-200 bg-slate-50/60 p-3 space-y-2">
                    <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
                      <span className="inline-flex items-center gap-1.5">
                        <Icon className="h-3.5 w-3.5 text-slate-500" />
                        {bucket.label}
                      </span>
                      <span className="text-slate-500">{items.length}</span>
                    </div>
                    {items.length === 0 ? (
                      <p className="text-xs italic text-slate-400">None specified</p>
                    ) : (
                      <div className="flex flex-wrap gap-1.5">
                        {items.map((item, idx) => (
                          <Badge key={`${item.name}-${idx}`} variant="outline" className="text-[11px] bg-white">
                            {item.name} ({item.importance})
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </CardContent>
          </Card>

          {/* 4-6. Skill Classification */}
          <Card>
            <CardHeader className="border-b border-slate-100 pb-3">
              <CardTitle className="text-base">4–6. Skill Classification Breakdown</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              {SKILL_TIERS.map((tier) => {
                const Icon = tier.icon;
                const items = skillClass[tier.key] || [];
                return (
                  <div key={tier.key} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-semibold text-slate-800 inline-flex items-center gap-1.5">
                        <Icon className="h-4 w-4 text-slate-600" />
                        {tier.title}
                      </h4>
                      <Badge variant="secondary" className="text-[11px]">{items.length}</Badge>
                    </div>
                    {items.length === 0 ? (
                      <p className="text-xs italic text-slate-400">None classified in this tier.</p>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                        {items.map((skill, idx) => (
                          <div key={`${skill.name}-${idx}`} className="rounded-lg border border-slate-200 bg-white p-3 text-xs space-y-1">
                            <div className="flex items-center justify-between gap-2">
                              <span className="font-semibold text-slate-900">{skill.name}</span>
                              <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${tier.badge}`}>
                                {skill.priority_score !== null && skill.priority_score !== undefined
                                  ? `${skill.priority_score}/100 • ${skill.priority_level}`
                                  : skill.priority_level}
                              </span>
                            </div>
                            <p className="text-slate-500">
                              {skill.category} • Proficiency: {skill.expected_proficiency || 'Unspecified'}
                            </p>
                            {skill.evidence && <p className="text-slate-600 italic">"{skill.evidence}"</p>}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </CardContent>
          </Card>

          {/* 7. Education & 8. Experience */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader className="border-b border-slate-100 pb-3">
                <CardTitle className="text-base inline-flex items-center gap-2">
                  <GraduationCap className="h-4 w-4 text-slate-600" />
                  <span>7. Education Requirements</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 grid grid-cols-2 gap-3">
                <MetaField label="Required Degree" value={edu.required_degree || edu.minimum_level} />
                <MetaField label="Preferred Degree" value={edu.preferred_degree} />
                <MetaField
                  label="Academic Fields"
                  value={edu.required_fields?.length ? edu.required_fields.join(', ') : null}
                />
                <MetaField
                  label="Required Certifications"
                  value={edu.required_certifications?.length ? edu.required_certifications.join(', ') : null}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="border-b border-slate-100 pb-3">
                <CardTitle className="text-base inline-flex items-center gap-2">
                  <Award className="h-4 w-4 text-slate-600" />
                  <span>8. Experience Requirements</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 grid grid-cols-2 gap-3">
                <MetaField
                  label="Minimum Years"
                  value={exp.minimum_years !== null && exp.minimum_years !== undefined ? `${exp.minimum_years} yrs` : null}
                />
                <MetaField
                  label="Maximum Years"
                  value={exp.maximum_years !== null && exp.maximum_years !== undefined ? `${exp.maximum_years} yrs` : null}
                />
                <MetaField
                  label="Fresher Eligible"
                  value={
                    exp.fresher_eligible === true
                      ? 'Yes'
                      : exp.fresher_eligible === false
                        ? 'No'
                        : 'Unknown'
                  }
                />
                <MetaField label="Internship / Project" value={exp.internship_experience || exp.project_experience} />
              </CardContent>
            </Card>
          </div>

          {/* 9. Soft Skills & 10. Responsibilities */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader className="border-b border-slate-100 pb-3">
                <CardTitle className="text-base inline-flex items-center gap-2">
                  <Users className="h-4 w-4 text-slate-600" />
                  <span>9. Soft Skills</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4">
                {report.soft_skills?.length ? (
                  <div className="flex flex-wrap gap-2">
                    {report.soft_skills.map((s, idx) => (
                      <Badge key={`${s.name}-${idx}`} variant="outline" className="text-xs">
                        {s.name} ({s.importance})
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs italic text-slate-400">No explicit soft skills extracted.</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="border-b border-slate-100 pb-3">
                <CardTitle className="text-base">10. Job Responsibilities</CardTitle>
              </CardHeader>
              <CardContent className="pt-4">
                {report.responsibilities?.length ? (
                  <ul className="list-disc pl-5 space-y-1 text-xs text-slate-700">
                    {report.responsibilities.map((resp, idx) => (
                      <li key={idx}>{resp}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs italic text-slate-400">No responsibilities listed.</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* 12. Eligibility Criteria & 13. AI Job Insights */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader className="border-b border-slate-100 pb-3">
                <CardTitle className="text-base">12. Candidate Eligibility Criteria</CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-3 text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <MetaField label="Required Education" value={eligibility.required_education} />
                  <MetaField label="Required Experience" value={eligibility.required_experience} />
                </div>
                {eligibility.important_technical_requirements?.length > 0 && (
                  <div>
                    <span className="font-semibold text-slate-700 block mb-1">Mandatory Technical Skills:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {eligibility.important_technical_requirements.map((item, idx) => (
                        <Badge key={idx} variant="secondary" className="text-[11px]">{item}</Badge>
                      ))}
                    </div>
                  </div>
                )}
                <p className="text-[11px] italic text-slate-500">{eligibility.disclaimer}</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="border-b border-slate-100 pb-3">
                <CardTitle className="text-base inline-flex items-center gap-2">
                  <Brain className="h-4 w-4 text-slate-600" />
                  <span>13. AI Job Insights</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-2.5">
                {report.ai_insights?.length ? (
                  report.ai_insights.map((insight, idx) => (
                    <div key={idx} className="rounded-lg border border-slate-100 bg-slate-50 p-3 text-xs space-y-1">
                      <h5 className="font-semibold text-slate-900">{insight.title}</h5>
                      <p className="text-slate-600">{insight.detail}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-xs italic text-slate-400">No AI insights generated.</p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
