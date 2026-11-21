import React, { useState, useEffect, useCallback } from 'react';
import {
  Cpu,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  RefreshCw,
  Layout,
  FileText,
  Search,
  Sparkles,
  Info,
  Check,
  X,
  Shield,
  Layers,
  Lightbulb,
  Tag,
  HelpCircle,
  ExternalLink,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert } from '../ui/alert';
import { LoadingIndicator } from '../ui/loading-indicator';
import { getResumeATS, analyzeResumeATS } from '../../services/atsService';
import { cn } from '../../utils/cn';

function getScoreColorClass(score) {
  if (score >= 85) return 'text-emerald-700 bg-emerald-50 border-emerald-200';
  if (score >= 70) return 'text-blue-700 bg-blue-50 border-blue-200';
  if (score >= 50) return 'text-amber-700 bg-amber-50 border-amber-200';
  return 'text-rose-700 bg-rose-50 border-rose-200';
}

function getGradeBadgeClass(grade) {
  const g = (grade || '').toLowerCase();
  if (g.includes('excellent')) return 'bg-emerald-100 text-emerald-800 border-emerald-300';
  if (g.includes('good')) return 'bg-blue-100 text-blue-800 border-blue-300';
  if (g.includes('need') || g.includes('fair')) return 'bg-amber-100 text-amber-800 border-amber-300';
  return 'bg-rose-100 text-rose-800 border-rose-300';
}

function getSeverityBadgeClass(severity) {
  const s = (severity || '').toLowerCase();
  if (s === 'critical') return 'bg-rose-100 text-rose-800 border-rose-300 font-bold';
  if (s === 'warning') return 'bg-amber-100 text-amber-800 border-amber-300 font-semibold';
  return 'bg-slate-100 text-slate-700 border-slate-300';
}

const DASHBOARD_TABS = [
  { key: 'overview', label: 'Score Breakdown', icon: Layers },
  { key: 'issues', label: 'Issues & Layout Risks', icon: AlertTriangle },
  { key: 'sections', label: 'Section Headings', icon: Layout },
  { key: 'keywords', label: 'Keywords & Verbs', icon: Tag },
  { key: 'recommendations', label: 'AI Optimization', icon: Sparkles },
];

/**
 * ResumeATSDashboard Component
 * Phase 4 | Feature #24: ATS Compatibility Analysis
 */
export function ResumeATSDashboard({ resumeId, className }) {
  const [atsData, setAtsData] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null);

  const fetchATS = useCallback(async () => {
    if (!resumeId) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await getResumeATS(resumeId);
      if (response && response.data) {
        setAtsData(response.data);
      }
    } catch (err) {
      if (err.status !== 404) {
        setError(err.message || 'Failed to load ATS compatibility analysis.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [resumeId]);

  useEffect(() => {
    fetchATS();
  }, [fetchATS]);

  const handleAnalyze = async (force = false) => {
    if (!resumeId || isAnalyzing) return;
    setIsAnalyzing(true);
    setError(null);
    try {
      const response = await analyzeResumeATS(resumeId, { forceRecalculate: force });
      if (response && response.data) {
        setAtsData(response.data);
      }
    } catch (err) {
      setError(err.message || 'Resume ATS evaluation failed.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // 1. LOADING STATE
  if (isLoading) {
    return (
      <Card className={cn('p-8 text-center space-y-4 border-slate-200 shadow-sm', className)}>
        <LoadingIndicator size="lg" className="text-teal-600 mx-auto" />
        <div className="space-y-1">
          <h3 className="text-base font-bold text-slate-800">
            Evaluating ATS Compatibility...
          </h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Testing layout tables, column overlap, standard section headers, contact completeness, and keyword indexability.
          </p>
        </div>
      </Card>
    );
  }

  // 2. ERROR STATE (when not 404)
  if (error && !atsData) {
    return (
      <Card className={cn('p-6 border-red-200 bg-red-50/40 shadow-sm space-y-4', className)}>
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="text-sm font-bold text-red-900">ATS Evaluation Failed</h4>
            <p className="text-xs text-red-700">{error}</p>
          </div>
        </div>
        <div className="flex justify-end">
          <Button
            size="sm"
            variant="outline"
            className="text-xs border-red-300 text-red-800 hover:bg-red-100"
            onClick={() => handleAnalyze(false)}
            disabled={isAnalyzing}
          >
            {isAnalyzing ? (
              <>
                <RefreshCw className="w-3 h-3 animate-spin mr-1.5" /> Retrying...
              </>
            ) : (
              'Retry ATS Audit'
            )}
          </Button>
        </div>
      </Card>
    );
  }

  // 3. EMPTY STATE (Never analyzed)
  if (!atsData) {
    return (
      <Card className={cn('p-8 border-dashed border-2 border-slate-200 text-center space-y-4 shadow-sm', className)}>
        <div className="w-12 h-12 bg-teal-50 rounded-full flex items-center justify-center mx-auto text-teal-600 border border-teal-100">
          <Cpu className="w-6 h-6" />
        </div>
        <div className="space-y-1.5 max-w-md mx-auto">
          <h3 className="text-base font-bold text-slate-900">
            ATS Compatibility Analysis
          </h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            Run a deterministic ATS audit to verify column structures, check standard headings, inspect table layout risks, and verify keyword extractability before submitting job applications.
          </p>
        </div>
        <Button
          onClick={() => handleAnalyze(false)}
          disabled={isAnalyzing}
          className="bg-teal-600 hover:bg-teal-700 text-white text-xs h-9 px-4 font-semibold shadow-sm"
        >
          {isAnalyzing ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin mr-2" />
              Running ATS Audit...
            </>
          ) : (
            <>
              <Cpu className="w-3.5 h-3.5 mr-2" />
              Run ATS Compatibility Audit
            </>
          )}
        </Button>
      </Card>
    );
  }

  const {
    ats_score = 0,
    score_grade = 'Good',
    score_interpretation = '',
    category_scores = {},
    verified_issues = [],
    formatting_risks = [],
    detected_sections = [],
    missing_sections = [],
    keyword_findings = { total_detected_keywords: 0, top_technical_keywords: [], top_action_verbs: [], recommended_keywords: [], keyword_density_note: '' },
    ai_feedback = { executive_summary: '', tailored_recommendations: [], keyword_optimization_advice: '' },
    disclaimer = '',
  } = atsData;

  const totalIssuesCount = verified_issues.length + formatting_risks.length;

  return (
    <Card className={cn('border-slate-200 shadow-sm overflow-hidden', className)}>
      {/* Header */}
      <CardHeader className="bg-slate-50/50 border-b border-slate-100 pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-teal-100 text-teal-800 border border-teal-200">
                <Cpu className="w-4 h-4" />
              </div>
              <CardTitle className="text-base sm:text-lg font-bold text-slate-900">
                ATS Compatibility Analysis
              </CardTitle>
            </div>
            <CardDescription className="text-xs text-slate-500">
              Evaluates formatting, structure, readability, contact information, and keyword indexability.
            </CardDescription>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleAnalyze(true)}
              disabled={isAnalyzing}
              className="text-xs h-8 gap-1.5 border-slate-200 text-slate-700 hover:bg-white hover:text-slate-900"
              title="Re-run deterministic ATS scoring"
            >
              <RefreshCw className={cn('w-3.5 h-3.5', isAnalyzing && 'animate-spin')} />
              <span>{isAnalyzing ? 'Evaluating...' : 'Re-audit ATS'}</span>
            </Button>
          </div>
        </div>

        {error && (
          <Alert variant="destructive" className="mt-3 text-xs">
            {error}
          </Alert>
        )}
      </CardHeader>

      <CardContent className="p-6 space-y-6">
        {/* Top Score Banner */}
        <div className="p-5 rounded-xl border bg-slate-50/70 border-slate-200/80 flex flex-col md:flex-row items-start md:items-center justify-between gap-5">
          <div className="flex items-center gap-4">
            {/* Score Ring / Pill */}
            <div
              className={cn(
                'w-20 h-20 rounded-2xl border flex flex-col items-center justify-center font-bold shrink-0 shadow-xs',
                getScoreColorClass(ats_score)
              )}
            >
              <span className="text-2xl font-extrabold tracking-tight">{ats_score}</span>
              <span className="text-[10px] uppercase font-semibold text-slate-500 tracking-wider">/ 100</span>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className={cn('text-xs uppercase font-extrabold', getGradeBadgeClass(score_grade))}>
                  {score_grade}
                </Badge>
                <span className="text-xs text-slate-500 font-medium">Deterministic Rubric</span>
              </div>
              <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-medium">
                {score_interpretation}
              </p>
            </div>
          </div>

          {/* Quick Metrics */}
          <div className="flex items-center gap-3 w-full md:w-auto shrink-0 border-t md:border-t-0 md:border-l border-slate-200 pt-3 md:pt-0 md:pl-5">
            <div className="text-center px-3 py-1.5 bg-white border border-slate-200 rounded-lg">
              <span className="text-[10px] font-bold text-slate-400 block uppercase">Verified Issues</span>
              <span className={cn('text-sm font-bold', verified_issues.length > 0 ? 'text-rose-700' : 'text-slate-800')}>
                {verified_issues.length}
              </span>
            </div>
            <div className="text-center px-3 py-1.5 bg-white border border-slate-200 rounded-lg">
              <span className="text-[10px] font-bold text-slate-400 block uppercase">Layout Risks</span>
              <span className={cn('text-sm font-bold', formatting_risks.length > 0 ? 'text-amber-700' : 'text-slate-800')}>
                {formatting_risks.length}
              </span>
            </div>
            <div className="text-center px-3 py-1.5 bg-white border border-slate-200 rounded-lg">
              <span className="text-[10px] font-bold text-slate-400 block uppercase">Keywords</span>
              <span className="text-sm font-bold text-teal-700">
                {keyword_findings.total_detected_keywords}
              </span>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-slate-200 pb-1 flex items-center gap-1.5 overflow-x-auto scrollbar-none">
          {DASHBOARD_TABS.map((tab) => {
            const Icon = tab.icon;
            const isSelected = activeTab === tab.key;
            const count =
              tab.key === 'issues'
                ? totalIssuesCount
                : tab.key === 'sections'
                ? missing_sections.length
                : tab.key === 'keywords'
                ? keyword_findings.total_detected_keywords
                : null;

            return (
              <button
                key={tab.key}
                type="button"
                onClick={() => setActiveTab(tab.key)}
                className={cn(
                  'px-3 py-2 text-xs font-semibold rounded-lg flex items-center gap-1.5 whitespace-nowrap transition-colors',
                  isSelected
                    ? 'bg-slate-900 text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                )}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
                {count !== null && (
                  <span
                    className={cn(
                      'text-[10px] px-1.5 py-0.2 rounded-full font-mono',
                      isSelected ? 'bg-slate-800 text-slate-200' : 'bg-slate-200/70 text-slate-700'
                    )}
                  >
                    {count}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* TAB 1: OVERVIEW & CATEGORY BREAKDOWN */}
        {activeTab === 'overview' && (
          <div className="space-y-4">
            {ai_feedback.executive_summary && (
              <div className="p-4 rounded-xl bg-teal-50/50 border border-teal-200/80 space-y-1.5">
                <div className="flex items-center gap-2 text-teal-900 font-semibold text-xs tracking-wide uppercase">
                  <Sparkles className="w-4 h-4 text-teal-700" />
                  Executive ATS Readiness Summary
                </div>
                <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-medium">
                  {ai_feedback.executive_summary}
                </p>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {Object.values(category_scores).map((cat) => {
                const pct = Math.round((cat.score / cat.max_score) * 100);
                return (
                  <div
                    key={cat.key}
                    className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs space-y-2.5"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-0.5">
                        <h5 className="text-xs font-bold text-slate-900">{cat.name}</h5>
                        <p className="text-[11px] text-slate-500">{cat.feedback}</p>
                      </div>
                      <Badge
                        variant="outline"
                        className={cn(
                          'text-[10px] uppercase font-bold shrink-0',
                          cat.status === 'Pass'
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : cat.status === 'Warning'
                            ? 'bg-amber-50 text-amber-700 border-amber-200'
                            : 'bg-rose-50 text-rose-700 border-rose-200'
                        )}
                      >
                        {cat.status}
                      </Badge>
                    </div>

                    {/* Progress Bar */}
                    <div className="space-y-1">
                      <div className="flex justify-between text-[11px] font-mono text-slate-500">
                        <span>{pct}%</span>
                        <span>{cat.score.toFixed(1)} / {cat.max_score.toFixed(1)} pts</span>
                      </div>
                      <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className={cn(
                            'h-full rounded-full transition-all',
                            pct >= 80 ? 'bg-emerald-500' : pct >= 50 ? 'bg-blue-500' : 'bg-rose-500'
                          )}
                          style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* TAB 2: ISSUES & RISKS (Distinguished Verified Issues vs Formatting Risks) */}
        {activeTab === 'issues' && (
          <div className="space-y-6">
            {/* Verified Issues Section */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-rose-600" />
                  <h4 className="text-xs sm:text-sm font-bold text-slate-900">
                    Verified Content & Structural Issues ({verified_issues.length})
                  </h4>
                </div>
                <span className="text-[11px] text-slate-500">Confirmed missing or broken data fields</span>
              </div>

              {verified_issues.length === 0 ? (
                <div className="p-4 bg-emerald-50/50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>No verified structural gaps detected. Key resume fields are present.</span>
                </div>
              ) : (
                verified_issues.map((issue) => (
                  <div
                    key={issue.id}
                    className="p-4 bg-white border border-rose-200 rounded-xl shadow-xs space-y-2.5"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-1.5">
                          <Badge variant="outline" className={cn('text-[10px] uppercase', getSeverityBadgeClass(issue.severity))}>
                            {issue.severity}
                          </Badge>
                          <Badge variant="outline" className="text-[10px] bg-slate-50 text-slate-600">
                            {issue.category_name}
                          </Badge>
                        </div>
                        <h5 className="text-xs sm:text-sm font-bold text-slate-900">{issue.title}</h5>
                      </div>
                    </div>
                    <p className="text-xs text-slate-700 leading-relaxed">{issue.explanation}</p>
                    {issue.evidence && issue.evidence.length > 0 && (
                      <div className="text-[11px] font-mono text-slate-600 bg-slate-50 p-2 rounded-lg border border-slate-100">
                        Evidence: {issue.evidence.join('; ')}
                      </div>
                    )}
                    <div className="p-2.5 bg-emerald-50/60 border border-emerald-200 rounded-lg flex items-start gap-2">
                      <Lightbulb className="w-3.5 h-3.5 text-emerald-700 shrink-0 mt-0.5" />
                      <p className="text-xs text-slate-800 font-medium">{issue.suggested_fix}</p>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Formatting & Parsing Risks Section */}
            <div className="space-y-3 pt-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Layout className="w-4 h-4 text-amber-600" />
                  <h4 className="text-xs sm:text-sm font-bold text-slate-900">
                    Formatting & Layout Risks ({formatting_risks.length})
                  </h4>
                </div>
                <span className="text-[11px] text-slate-500">Columns, tables, textboxes & parsing hazards</span>
              </div>

              {formatting_risks.length === 0 ? (
                <div className="p-4 bg-emerald-50/50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>No layout or document hazards detected. Clean single-column formatting.</span>
                </div>
              ) : (
                formatting_risks.map((risk) => (
                  <div
                    key={risk.id}
                    className="p-4 bg-white border border-amber-200 rounded-xl shadow-xs space-y-2.5"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-1.5">
                          <Badge variant="outline" className={cn('text-[10px] uppercase', getSeverityBadgeClass(risk.severity))}>
                            {risk.severity}
                          </Badge>
                          <Badge variant="outline" className="text-[10px] bg-slate-50 text-slate-600">
                            {risk.category_name}
                          </Badge>
                        </div>
                        <h5 className="text-xs sm:text-sm font-bold text-slate-900">{risk.title}</h5>
                      </div>
                    </div>
                    <p className="text-xs text-slate-700 leading-relaxed">{risk.explanation}</p>
                    {risk.evidence && risk.evidence.length > 0 && (
                      <div className="text-[11px] font-mono text-slate-600 bg-slate-50 p-2 rounded-lg border border-slate-100">
                        Evidence: {risk.evidence.join('; ')}
                      </div>
                    )}
                    <div className="p-2.5 bg-amber-50/60 border border-amber-200 rounded-lg flex items-start gap-2">
                      <Lightbulb className="w-3.5 h-3.5 text-amber-700 shrink-0 mt-0.5" />
                      <p className="text-xs text-slate-800 font-medium">{risk.suggested_fix}</p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* TAB 3: SECTIONS & HEADINGS */}
        {activeTab === 'sections' && (
          <div className="space-y-4">
            <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-600">
              ATS parsers scan for conventional section titles. Avoid creative or informal headings (e.g. 'Where I've Been' instead of 'Experience') to ensure all content is indexed into the recruiter database.
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {detected_sections.map((sec) => (
                <div
                  key={sec.section_key}
                  className={cn(
                    'p-3.5 rounded-xl border flex items-center justify-between gap-3',
                    sec.detected
                      ? 'bg-white border-slate-200'
                      : 'bg-rose-50/40 border-rose-200'
                  )}
                >
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-slate-900 block">{sec.section_name}</span>
                    <span className="text-[11px] text-slate-500 font-mono">
                      {sec.heading_text ? `Heading: "${sec.heading_text}"` : 'Not detected in document'}
                    </span>
                  </div>
                  <Badge
                    variant="outline"
                    className={cn(
                      'text-[10px] shrink-0 font-bold',
                      sec.status === 'Standard'
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : sec.status === 'Unusual'
                        ? 'bg-amber-50 text-amber-700 border-amber-200'
                        : 'bg-rose-50 text-rose-700 border-rose-200'
                    )}
                  >
                    {sec.status}
                  </Badge>
                </div>
              ))}
            </div>

            {missing_sections.length > 0 && (
              <div className="p-4 bg-amber-50/60 border border-amber-200 rounded-xl space-y-1.5">
                <span className="text-xs font-bold text-amber-900 uppercase tracking-wider block">
                  Missing Standard Sections
                </span>
                <p className="text-xs text-slate-700">
                  The following sections were not found in your resume: <strong className="text-slate-900">{missing_sections.join(', ')}</strong>. Adding these sections will improve recruiter search visibility.
                </p>
              </div>
            )}
          </div>
        )}

        {/* TAB 4: KEYWORDS & ACTION VERBS */}
        {activeTab === 'keywords' && (
          <div className="space-y-4">
            <div className="p-3.5 bg-teal-50/60 border border-teal-200 rounded-xl space-y-1 text-xs text-slate-700">
              <span className="font-bold text-teal-900 block uppercase tracking-wider">
                Keyword Density Note
              </span>
              <p>{keyword_findings.keyword_density_note}</p>
            </div>

            {/* Technical Keywords */}
            <div className="space-y-2">
              <h5 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Detected Technical Keywords ({keyword_findings.top_technical_keywords?.length || 0})
              </h5>
              <div className="flex flex-wrap gap-1.5">
                {keyword_findings.top_technical_keywords?.map((kw, i) => (
                  <Badge key={i} variant="outline" className="text-xs bg-slate-50 text-slate-800 border-slate-200">
                    {kw}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Action Verbs */}
            <div className="space-y-2 pt-2">
              <h5 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                High-Impact Action Verbs Found ({keyword_findings.top_action_verbs?.length || 0})
              </h5>
              <div className="flex flex-wrap gap-1.5">
                {keyword_findings.top_action_verbs?.map((verb, i) => (
                  <Badge key={i} variant="outline" className="text-xs bg-emerald-50 text-emerald-800 border-emerald-200">
                    ✓ {verb}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Recommended Verbs */}
            {keyword_findings.recommended_keywords?.length > 0 && (
              <div className="space-y-2 pt-2">
                <h5 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Recommended Power Verbs to Consider
                </h5>
                <div className="flex flex-wrap gap-1.5">
                  {keyword_findings.recommended_keywords.map((kw, i) => (
                    <Badge key={i} variant="outline" className="text-xs bg-amber-50 text-amber-800 border-amber-200">
                      + {kw}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 5: AI RECOMMENDATIONS (Before & After) */}
        {activeTab === 'recommendations' && (
          <div className="space-y-4">
            {ai_feedback.keyword_optimization_advice && (
              <div className="p-3.5 bg-blue-50/50 border border-blue-200 rounded-xl space-y-1 text-xs text-slate-700">
                <span className="font-bold text-blue-900 block uppercase tracking-wider">
                  Keyword Optimization Guidance
                </span>
                <p>{ai_feedback.keyword_optimization_advice}</p>
              </div>
            )}

            <div className="space-y-3">
              {ai_feedback.tailored_recommendations?.length === 0 ? (
                <div className="p-6 text-center text-xs text-slate-500 border border-dashed rounded-xl">
                  No tailored recommendations needed. Formatting aligns with ATS best practices.
                </div>
              ) : (
                ai_feedback.tailored_recommendations.map((rec, idx) => (
                  <div
                    key={idx}
                    className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs space-y-3"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <h5 className="text-xs sm:text-sm font-bold text-slate-900">{rec.title}</h5>
                      <div className="flex items-center gap-1.5">
                        <Badge variant="outline" className="text-[10px] bg-slate-50 text-slate-600">
                          {rec.category}
                        </Badge>
                        <Badge variant="outline" className={cn('text-[10px]', getSeverityBadgeClass(rec.priority))}>
                          {rec.priority}
                        </Badge>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      {/* Current State */}
                      <div className="p-3 rounded-lg bg-rose-50/50 border border-rose-200/80 space-y-1">
                        <span className="text-[10px] font-bold text-rose-800 uppercase tracking-wider block">
                          Current State
                        </span>
                        <p className="text-slate-700 font-mono text-[11px] leading-relaxed">
                          {rec.current_state}
                        </p>
                      </div>

                      {/* Recommended Rewrite */}
                      <div className="p-3 rounded-lg bg-emerald-50/50 border border-emerald-200/80 space-y-1">
                        <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider block">
                          Recommended ATS Rewrite
                        </span>
                        <p className="text-slate-800 font-medium leading-relaxed">
                          {rec.recommended_rewrite}
                        </p>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Disclaimer Footer */}
        {disclaimer && (
          <div className="pt-2 border-t border-slate-100 flex items-start gap-2 text-[11px] text-slate-400">
            <Info className="w-3.5 h-3.5 shrink-0 mt-0.5 text-slate-400" />
            <p>{disclaimer}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
