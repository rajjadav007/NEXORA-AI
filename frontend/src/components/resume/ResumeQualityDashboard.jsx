import React, { useState, useEffect, useCallback } from 'react';
import {
  Award,
  Sparkles,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  FileCheck2,
  BookOpen,
  Briefcase,
  Code2,
  FolderGit2,
  GraduationCap,
  Trophy,
  Type,
  Lightbulb,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert } from '../ui/alert';
import { LoadingIndicator } from '../ui/loading-indicator';
import { getResumeQualityScore, analyzeResumeQualityScore } from '../../services/qualityScoreService';
import { cn } from '../../utils/cn';

// Icon mapping per rubric category
const CATEGORY_ICONS = {
  completeness: FileCheck2,
  professional_summary: BookOpen,
  technical_skills: Code2,
  work_experience: Briefcase,
  project_descriptions: FolderGit2,
  education: GraduationCap,
  achievements: Trophy,
  content_clarity: Type,
};

function getScoreColorClass(score) {
  if (score >= 90) return { bg: 'bg-emerald-500', text: 'text-emerald-700', border: 'border-emerald-200', lightBg: 'bg-emerald-50' };
  if (score >= 80) return { bg: 'bg-teal-500', text: 'text-teal-700', border: 'border-teal-200', lightBg: 'bg-teal-50' };
  if (score >= 70) return { bg: 'bg-blue-500', text: 'text-blue-700', border: 'border-blue-200', lightBg: 'bg-blue-50' };
  if (score >= 50) return { bg: 'bg-amber-500', text: 'text-amber-700', border: 'border-amber-200', lightBg: 'bg-amber-50' };
  return { bg: 'bg-rose-500', text: 'text-rose-700', border: 'border-rose-200', lightBg: 'bg-rose-50' };
}

function getRatingBadgeVariant(rating) {
  switch (rating) {
    case 'Exceptional':
      return 'bg-emerald-100 text-emerald-800 border-emerald-300';
    case 'Strong':
      return 'bg-teal-100 text-teal-800 border-teal-300';
    case 'Good':
      return 'bg-blue-100 text-blue-800 border-blue-300';
    case 'Needs Improvement':
      return 'bg-amber-100 text-amber-800 border-amber-300';
    default:
      return 'bg-rose-100 text-rose-800 border-rose-300';
  }
}

/**
 * ResumeQualityDashboard Component
 * Phase 4 | Feature #21: Resume Quality Score Engine
 */
export function ResumeQualityDashboard({ resumeId, className }) {
  const [qualityData, setQualityData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const [expandedCategory, setExpandedCategory] = useState(null);

  const fetchScore = useCallback(async () => {
    if (!resumeId) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await getResumeQualityScore(resumeId);
      if (response && response.data) {
        setQualityData(response.data);
      }
    } catch (err) {
      // 404 indicates score has not been calculated yet; not a terminal error
      if (err.status !== 404) {
        setError(err.message || 'Failed to load resume quality score.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [resumeId]);

  useEffect(() => {
    fetchScore();
  }, [fetchScore]);

  const handleAnalyze = async (force = false) => {
    if (!resumeId || isAnalyzing) return;
    setIsAnalyzing(true);
    setError(null);
    try {
      const response = await analyzeResumeQualityScore(resumeId, { forceRecalculate: force });
      if (response && response.data) {
        setQualityData(response.data);
      }
    } catch (err) {
      setError(err.message || 'Resume quality score evaluation failed.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const toggleCategory = (key) => {
    setExpandedCategory((prev) => (prev === key ? null : key));
  };

  // 1. INITIAL LOADING STATE
  if (isLoading && !qualityData) {
    return (
      <Card className={cn('p-8 border-slate-200 shadow-sm text-center space-y-3', className)}>
        <LoadingIndicator size="md" className="text-teal-600 mx-auto" />
        <p className="text-xs text-slate-500 font-medium">Loading Resume Quality Score...</p>
      </Card>
    );
  }

  // 2. NOT YET ANALYZED STATE
  if (!qualityData && !isLoading) {
    return (
      <Card className={cn('border-teal-100 bg-gradient-to-br from-teal-50/50 via-white to-slate-50 shadow-sm overflow-hidden', className)}>
        <CardHeader className="pb-4 border-b border-teal-100/60">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-teal-600 text-white flex items-center justify-center shadow-xs">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                  Resume Quality Score
                  <Badge variant="outline" className="text-[10px] bg-teal-50 border-teal-200 text-teal-800">
                    Phase 4 • Feature 21
                  </Badge>
                </CardTitle>
                <CardDescription className="text-xs text-slate-500">
                  Evaluate completeness, clarity, impact metrics, and technical depth across 8 dimensions.
                </CardDescription>
              </div>
            </div>

            <Button
              onClick={() => handleAnalyze(false)}
              disabled={isAnalyzing}
              className="bg-teal-600 hover:bg-teal-700 text-white text-xs h-9 font-semibold gap-1.5 shadow-sm shrink-0"
            >
              {isAnalyzing ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Evaluating Resume...
                </>
              ) : (
                <>
                  <Award className="w-3.5 h-3.5" /> Analyze Quality Score
                </>
              )}
            </Button>
          </div>
        </CardHeader>

        {error && (
          <div className="p-4 bg-red-50/70 border-b border-red-100">
            <Alert variant="destructive" className="border-red-200 text-xs">
              <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
              <div className="space-y-1">
                <p className="font-semibold text-red-900">Analysis Error</p>
                <p className="text-red-700">{error}</p>
              </div>
            </Alert>
          </div>
        )}

        <CardContent className="pt-4 pb-5">
          <p className="text-xs text-slate-600 leading-relaxed max-w-2xl">
            Click <strong>Analyze Quality Score</strong> to benchmark your resume against our transparent 100-point rubric powered by local AI. Uncover missing sections, weak bullets, and high-impact improvement recommendations.
          </p>
        </CardContent>
      </Card>
    );
  }

  // 3. FULL QUALITY DASHBOARD STATE
  const overall = qualityData.overall_score || 0;
  const ratingLevel = qualityData.rating_level || 'Good';
  const color = getScoreColorClass(overall);
  const categories = Object.values(qualityData.category_scores || {});

  return (
    <Card className={cn('border-slate-200 shadow-sm overflow-hidden bg-white', className)}>
      {/* Top Header Card with Overall Score */}
      <CardHeader className="bg-slate-50/70 border-b border-slate-200/80 pb-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-teal-600 text-white flex items-center justify-center shadow-sm">
              <Award className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <CardTitle className="text-base font-bold text-slate-900">
                  Resume Quality Score
                </CardTitle>
                <Badge variant="outline" className={cn('text-[11px] font-bold border', getRatingBadgeVariant(ratingLevel))}>
                  {ratingLevel}
                </Badge>
              </div>
              <CardDescription className="text-xs text-slate-500">
                100-point transparent quality rubric evaluated via local AI reasoning & structural metrics.
              </CardDescription>
            </div>
          </div>

          <div className="flex items-center gap-3 self-end sm:self-auto">
            {/* Overall Score Meter */}
            <div className={cn('px-4 py-1.5 rounded-xl border flex items-center gap-2.5', color.lightBg, color.border)}>
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Score</span>
              <div className="flex items-baseline gap-0.5">
                <span className={cn('text-2xl font-black font-mono', color.text)}>
                  {overall}
                </span>
                <span className="text-xs font-bold text-slate-400">/100</span>
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => handleAnalyze(true)}
              disabled={isAnalyzing}
              className="text-xs h-9 border-slate-300 text-slate-700 hover:bg-slate-100 flex items-center gap-1.5 shrink-0"
              title="Re-run quality score evaluation"
            >
              <RefreshCw className={cn('w-3.5 h-3.5', isAnalyzing && 'animate-spin')} />
              <span>{isAnalyzing ? 'Re-evaluating...' : 'Re-calculate'}</span>
            </Button>
          </div>
        </div>

        {error && (
          <Alert variant="destructive" className="mt-3 border-red-200 text-xs">
            <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
            <div className="space-y-0.5">
              <p className="font-semibold text-red-900">Evaluation Warning</p>
              <p className="text-red-700">{error}</p>
            </div>
          </Alert>
        )}
      </CardHeader>

      <CardContent className="p-6 space-y-6">
        {/* Category Breakdown Grid */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
              <TrendingUp className="w-4 h-4 text-teal-600" />
              <span>Category Score Breakdown (8 Dimensions)</span>
            </h4>
            <span className="text-[11px] text-slate-400">Weights strictly sum to 100%</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {categories.map((cat) => {
              const IconComponent = CATEGORY_ICONS[cat.category_key] || Award;
              const isExpanded = expandedCategory === cat.category_key;
              const catColor = getScoreColorClass(cat.score_percentage);

              return (
                <div
                  key={cat.category_key}
                  className={cn(
                    'p-3.5 rounded-xl border transition-all text-xs space-y-2 bg-white',
                    isExpanded ? 'border-teal-300 shadow-xs' : 'border-slate-200 hover:border-slate-300'
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <div className="w-7 h-7 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center shrink-0">
                        <IconComponent className="w-3.5 h-3.5" />
                      </div>
                      <div className="min-w-0">
                        <span className="font-bold text-slate-900 truncate block">
                          {cat.category_name}
                        </span>
                        <span className="text-[10px] text-slate-400 block">
                          Weight: {cat.weight_percentage}%
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <Badge variant="outline" className={cn('text-[10px] font-semibold px-2 py-0.5', getRatingBadgeVariant(cat.rating))}>
                        {cat.rating}
                      </Badge>
                      <span className="font-mono font-bold text-slate-800 text-xs">
                        {cat.score} <span className="text-slate-400 font-normal">/ {cat.max_score}</span>
                      </span>
                      <button
                        type="button"
                        onClick={() => toggleCategory(cat.category_key)}
                        className="p-1 text-slate-400 hover:text-slate-700 rounded-md"
                        title={isExpanded ? 'Collapse' : 'Expand feedback'}
                      >
                        {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>

                  {/* Visual Progress Bar */}
                  <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                    <div
                      className={cn('h-full rounded-full transition-all duration-500', catColor.bg)}
                      style={{ width: `${Math.min(100, Math.max(0, cat.score_percentage))}%` }}
                    />
                  </div>

                  {/* Expandable Explanation & Recommendations */}
                  {isExpanded && (
                    <div className="pt-2 border-t border-slate-100 space-y-2 text-xs">
                      <p className="text-slate-600 leading-relaxed italic">
                        "{cat.explanation}"
                      </p>

                      {cat.strengths && cat.strengths.length > 0 && (
                        <div className="space-y-1">
                          <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-wide block">
                            Key Strengths:
                          </span>
                          <ul className="space-y-0.5 pl-3 list-disc text-slate-600 text-[11px]">
                            {cat.strengths.map((s, idx) => (
                              <li key={idx}>{s}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {cat.improvements && cat.improvements.length > 0 && (
                        <div className="space-y-1">
                          <span className="text-[10px] font-bold text-amber-700 uppercase tracking-wide block">
                            Targeted Improvements:
                          </span>
                          <ul className="space-y-0.5 pl-3 list-disc text-slate-600 text-[11px]">
                            {cat.improvements.map((imp, idx) => (
                              <li key={idx}>{imp}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Missing Information Callout */}
        {qualityData.missing_information && qualityData.missing_information.length > 0 && (
          <div className="p-4 rounded-xl border border-amber-200 bg-amber-50/50 space-y-2">
            <div className="flex items-center gap-2 text-amber-900 font-bold text-xs uppercase tracking-wider">
              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
              <span>Missing Information & Structural Gaps</span>
            </div>
            <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-amber-950 pl-2">
              {qualityData.missing_information.map((item, idx) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Two-Column Insights: Top Strengths & Priority Improvements */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Top Strengths */}
          <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/40 space-y-2.5">
            <div className="flex items-center gap-2 text-emerald-900 font-bold text-xs uppercase tracking-wider">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>Standout Strengths</span>
            </div>
            {qualityData.strengths && qualityData.strengths.length > 0 ? (
              <ul className="space-y-2 text-xs text-emerald-950">
                {qualityData.strengths.map((str, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 mt-0.5 shrink-0" />
                    <span className="leading-relaxed">{str}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-slate-500 italic">No specific strengths captured.</p>
            )}
          </div>

          {/* Priority Improvements */}
          <div className="p-4 rounded-xl border border-teal-200 bg-teal-50/40 space-y-2.5">
            <div className="flex items-center gap-2 text-teal-900 font-bold text-xs uppercase tracking-wider">
              <Lightbulb className="w-4 h-4 text-teal-600 shrink-0" />
              <span>Actionable Improvement Suggestions</span>
            </div>
            {qualityData.improvement_suggestions && qualityData.improvement_suggestions.length > 0 ? (
              <ul className="space-y-2 text-xs text-slate-800">
                {qualityData.improvement_suggestions.map((sug, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <div className="w-4 h-4 rounded-full bg-teal-200 text-teal-800 flex items-center justify-center font-mono font-bold text-[10px] shrink-0 mt-0.5">
                      {idx + 1}
                    </div>
                    <span className="leading-relaxed">{sug}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-slate-500 italic">No critical improvement suggestions required.</p>
            )}
          </div>
        </div>

        {/* Analysis Metadata Footer */}
        {qualityData.analysis_metadata && (
          <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-[11px] text-slate-400">
            <div className="flex items-center gap-3">
              <span>Model: <strong className="font-mono text-slate-600">{qualityData.analysis_metadata.model || 'local-ai'}</strong></span>
              {qualityData.analysis_metadata.duration_ms && (
                <span>Duration: <strong className="font-mono text-slate-600">{qualityData.analysis_metadata.duration_ms}ms</strong></span>
              )}
              <span>Rubric: <strong className="font-mono text-slate-600">v{qualityData.rubric_version}</strong></span>
            </div>
            {qualityData.updated_at && (
              <span>Last Evaluated: {new Date(qualityData.updated_at).toLocaleString()}</span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
