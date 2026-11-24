import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart3,
  TrendingUp,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Clock,
  Sparkles,
  RefreshCw,
  FileText,
  Layers,
  ArrowRight,
  ExternalLink,
  Zap,
  Target,
  Trophy,
  SlidersHorizontal,
  ChevronRight,
  Eye,
  Check,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { LoadingIndicator } from '../ui/loading-indicator';
import { Alert } from '../ui/alert';
import { getResumeAnalyticsDashboard } from '../../services/analyticsService';
import { useResume } from '../../context/ResumeContext';
import { formatFileSize } from '../../hooks/useResumeUpload';
import { cn } from '../../utils/cn';
import { SkillDistributionSection } from './SkillDistributionSection';
import { ResumeImprovementTracker } from './ResumeImprovementTracker';

/**
 * Helper to compute color classes based on 0-100 score value.
 */
function getScoreColorClass(score) {
  if (score === null || score === undefined) return 'text-slate-400 bg-slate-100 border-slate-200';
  if (score >= 85) return 'text-emerald-700 bg-emerald-50 border-emerald-200';
  if (score >= 70) return 'text-teal-700 bg-teal-50 border-teal-200';
  if (score >= 55) return 'text-amber-700 bg-amber-50 border-amber-200';
  return 'text-rose-700 bg-rose-50 border-rose-200';
}

function getScoreBarFillClass(score) {
  if (score === null || score === undefined) return 'bg-slate-300';
  if (score >= 85) return 'bg-emerald-600';
  if (score >= 70) return 'bg-teal-600';
  if (score >= 55) return 'bg-amber-500';
  return 'bg-rose-500';
}

function getPriorityBadgeClass(priority) {
  const p = (priority || '').toLowerCase();
  if (p === 'critical') return 'bg-rose-100 text-rose-800 border-rose-300 font-semibold';
  if (p === 'high') return 'bg-amber-100 text-amber-800 border-amber-300 font-semibold';
  if (p === 'medium') return 'bg-blue-100 text-blue-800 border-blue-300';
  return 'bg-slate-100 text-slate-700 border-slate-300';
}

/**
 * ResumeAnalyticsDashboard Component
 * Phase 5 | Feature #28: Resume Analytics Dashboard
 */
export function ResumeAnalyticsDashboard({
  resumeId: propResumeId,
  onRouteChangeResume,
  className,
}) {
  const navigate = useNavigate();
  const { activeResumeId, selectResume } = useResume();
  const activeId = propResumeId || activeResumeId;

  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [insightsTab, setInsightsTab] = useState('strengths'); // 'strengths' | 'weaknesses' | 'improvements'

  const fetchDashboard = useCallback(async (showRefreshing = false) => {
    if (!activeId) return;
    if (showRefreshing) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);

    try {
      const res = await getResumeAnalyticsDashboard(activeId);
      setData(res.data);
    } catch (err) {
      setError(err.message || 'Failed to load resume analytics dashboard.');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [activeId]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  // Handle resume switch from dropdown
  const handleSelectResume = (e) => {
    const nextId = e.target.value;
    if (!nextId || nextId === activeId) return;
    selectResume(nextId);
    if (onRouteChangeResume) {
      onRouteChangeResume(nextId);
    } else {
      navigate(`/resume/analytics?id=${nextId}`);
    }
  };

  // 1. LOADING SKELETON STATE
  if (isLoading) {
    return (
      <div className={cn('space-y-6', className)}>
        {/* Header Skeleton */}
        <div className="p-6 rounded-xl border border-slate-200 bg-white shadow-xs space-y-4 animate-pulse">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-slate-200" />
              <div className="space-y-2">
                <div className="h-4 w-48 bg-slate-200 rounded" />
                <div className="h-3 w-32 bg-slate-100 rounded" />
              </div>
            </div>
            <div className="h-9 w-36 bg-slate-200 rounded-lg" />
          </div>
        </div>

        {/* Cards Skeleton */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="p-5 rounded-xl border border-slate-200 bg-white space-y-3 animate-pulse">
              <div className="h-3 w-24 bg-slate-200 rounded" />
              <div className="h-8 w-16 bg-slate-300 rounded" />
              <div className="h-2 w-full bg-slate-100 rounded" />
            </div>
          ))}
        </div>

        {/* Visual Analytics Skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-64 rounded-xl border border-slate-200 bg-white p-6 space-y-4 animate-pulse">
            <div className="h-4 w-40 bg-slate-200 rounded" />
            <div className="space-y-3 pt-2">
              <div className="h-3 bg-slate-100 rounded w-full" />
              <div className="h-3 bg-slate-100 rounded w-5/6" />
              <div className="h-3 bg-slate-100 rounded w-4/6" />
            </div>
          </div>
          <div className="h-64 rounded-xl border border-slate-200 bg-white p-6 space-y-4 animate-pulse">
            <div className="h-4 w-40 bg-slate-200 rounded" />
            <div className="space-y-3 pt-2">
              <div className="h-3 bg-slate-100 rounded w-full" />
              <div className="h-3 bg-slate-100 rounded w-5/6" />
              <div className="h-3 bg-slate-100 rounded w-4/6" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 2. NO RESUME SELECTED STATE
  if (!activeId) {
    return (
      <Card className={cn('p-12 text-center border-slate-200 shadow-sm max-w-xl mx-auto space-y-4', className)}>
        <div className="w-14 h-14 rounded-2xl bg-teal-50 text-teal-600 flex items-center justify-center mx-auto border border-teal-100">
          <BarChart3 className="w-7 h-7" />
        </div>
        <div className="space-y-1">
          <h3 className="text-base font-bold text-slate-900">
            No Resume Selected for Analytics
          </h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
            Upload a resume or select an existing stored document to view your complete visual intelligence analytics dashboard.
          </p>
        </div>
        <div className="pt-2">
          <Button
            onClick={() => navigate('/resume')}
            className="text-xs h-9 bg-teal-600 hover:bg-teal-700 text-white font-semibold inline-flex items-center gap-2"
          >
            <Sparkles className="w-4 h-4" /> Go to Resume Intelligence
          </Button>
        </div>
      </Card>
    );
  }

  // 3. API ERROR STATE
  if (error && !data) {
    return (
      <Card className={cn('p-8 border-red-200 bg-red-50/30 text-center space-y-4 shadow-sm', className)}>
        <div className="w-12 h-12 rounded-full bg-red-100 text-red-600 flex items-center justify-center mx-auto">
          <AlertCircle className="w-6 h-6" />
        </div>
        <div className="space-y-1 max-w-md mx-auto">
          <h3 className="text-base font-bold text-red-950">
            Analytics Dashboard Unavailable
          </h3>
          <p className="text-xs text-red-700 leading-relaxed">
            {error}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => fetchDashboard(false)}
          className="text-xs h-8 border-red-300 text-red-800 hover:bg-red-50"
        >
          <RefreshCw className="w-3.5 h-3.5 mr-1.5" /> Try Again
        </Button>
      </Card>
    );
  }

  const {
    resume_header = {},
    summary_cards = {},
    visual_analytics = {},
    resume_insights = {},
    has_any_analysis = false,
  } = data || {};

  const isFullComplete = resume_header.analysis_status === 'COMPLETE';
  const isPartial = resume_header.analysis_status === 'PARTIAL';

  return (
    <div className={cn('space-y-6', className)}>
      {/* SECTION A: RESUME HEADER & RESUME SELECTION */}
      <Card className="border-slate-200 shadow-sm overflow-hidden bg-white">
        <CardHeader className="bg-gradient-to-r from-teal-50/70 via-slate-50 to-indigo-50/70 border-b border-slate-100 pb-4">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            {/* Left: Document info */}
            <div className="flex items-start gap-3.5 min-w-0">
              <div className="w-11 h-11 rounded-xl bg-teal-600 text-white flex items-center justify-center shadow-xs shrink-0 mt-0.5">
                <BarChart3 className="w-6 h-6" />
              </div>
              <div className="space-y-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-base sm:text-lg font-bold text-slate-900 truncate" title={resume_header.filename}>
                    {resume_header.filename}
                  </h2>
                  <Badge
                    variant="outline"
                    className="text-[10px] font-mono bg-white uppercase border-slate-300 text-slate-700"
                  >
                    {resume_header.file_type || 'PDF'}
                  </Badge>
                  {/* Status badge */}
                  <Badge
                    variant="outline"
                    className={cn(
                      'text-[10px] font-semibold border',
                      isFullComplete
                        ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                        : isPartial
                        ? 'bg-amber-50 text-amber-800 border-amber-300'
                        : 'bg-slate-100 text-slate-600 border-slate-300'
                    )}
                  >
                    {isFullComplete
                      ? 'Full Coverage (6/6 Analyses)'
                      : isPartial
                      ? `Partial Coverage (${resume_header.coverage_count}/6 Analyses)`
                      : 'Not Analyzed (0/6 Analyses)'}
                  </Badge>
                </div>

                <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
                  <span>{formatFileSize(resume_header.file_size)}</span>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    Last Analyzed:{' '}
                    {resume_header.last_analyzed_date
                      ? new Date(resume_header.last_analyzed_date).toLocaleDateString(undefined, {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })
                      : 'Never'}
                  </span>
                </div>
              </div>
            </div>

            {/* Right: Controls & Resume Switcher */}
            <div className="flex flex-wrap items-center gap-2 self-start lg:self-auto shrink-0">
              {/* Multi-Resume Selector */}
              {resume_header.available_resumes && resume_header.available_resumes.length > 1 && (
                <div className="relative min-w-[180px]">
                  <select
                    value={activeId}
                    onChange={handleSelectResume}
                    aria-label="Switch active resume"
                    className="h-8 w-full appearance-none rounded-lg border border-slate-200 bg-white px-3 pr-8 text-xs font-semibold text-slate-700 shadow-xs focus:outline-none focus:ring-1 focus:ring-teal-500 hover:border-slate-300"
                  >
                    {resume_header.available_resumes.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.filename}
                      </option>
                    ))}
                  </select>
                  <SlidersHorizontal className="pointer-events-none absolute right-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
                </div>
              )}

              {/* Refresh button */}
              <Button
                variant="outline"
                size="sm"
                onClick={() => fetchDashboard(true)}
                disabled={isRefreshing}
                className="text-xs h-8 border-slate-200 text-slate-700 hover:bg-slate-100 flex items-center gap-1.5"
                title="Refresh dashboard metrics"
              >
                <RefreshCw className={cn('w-3.5 h-3.5', isRefreshing && 'animate-spin')} />
                <span>Refresh</span>
              </Button>

              {/* Full Preview Link */}
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate(`/resume/preview?id=${activeId}`)}
                className="text-xs h-8 border-slate-200 text-slate-700 hover:text-slate-900 hover:bg-slate-100 flex items-center gap-1.5"
                title="Navigate to detailed feature breakdown and original document"
              >
                <Eye className="w-3.5 h-3.5" />
                <span>Full Preview</span>
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* EMPTY DASHBOARD NOTICE (when resume has zero analyses) */}
      {!has_any_analysis && (
        <Card className="border-amber-200 bg-amber-50/40 p-6 shadow-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h4 className="text-sm font-bold text-amber-950">
                  No Analysis Completed for this Resume Yet
                </h4>
                <p className="text-xs text-amber-800 leading-relaxed max-w-2xl">
                  Run Phase 4 Resume Quality evaluations (Quality Score, Strengths, Weaknesses, ATS Compatibility, Grammar, or Achievements) to unlock comprehensive visual charts, scoring distributions, and synthesized insights.
                </p>
              </div>
            </div>
            <Button
              size="sm"
              onClick={() => navigate(`/resume/preview?id=${activeId}`)}
              className="text-xs h-9 bg-teal-600 hover:bg-teal-700 text-white shrink-0 flex items-center gap-2 font-semibold"
            >
              <span>Run Quality Analysis</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Button>
          </div>
        </Card>
      )}

      {/* SECTION B: ANALYTICS SUMMARY CARDS (4 Core Genuine Metrics) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Overall Quality Score */}
        {(() => {
          const card = summary_cards.quality_score || {};
          const isAvail = card.available;
          const score = card.score;
          return (
            <Card className="p-5 border-slate-200 bg-white shadow-xs space-y-3 flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500">
                  {card.label || 'Overall Quality Score'}
                </span>
                <div className="w-7 h-7 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center">
                  <Sparkles className="w-4 h-4" />
                </div>
              </div>

              <div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                    {isAvail && score !== null ? score : '--'}
                  </span>
                  {isAvail && score !== null && (
                    <span className="text-xs font-semibold text-slate-400">/ 100</span>
                  )}
                </div>

                <div className="mt-1 flex items-center gap-1.5">
                  <Badge
                    variant="outline"
                    className={cn('text-[10px] font-semibold border', getScoreColorClass(score))}
                  >
                    {card.grade_or_rating || 'Not Evaluated'}
                  </Badge>
                </div>
              </div>

              <div className="space-y-1.5 pt-1">
                <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                  <div
                    className={cn('h-full rounded-full transition-all duration-500', getScoreBarFillClass(score))}
                    style={{ width: `${Math.min(100, Math.max(0, score || 0))}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-400 line-clamp-1">{card.description}</p>
              </div>
            </Card>
          );
        })()}

        {/* Card 2: ATS Compatibility Score */}
        {(() => {
          const card = summary_cards.ats_compatibility || {};
          const isAvail = card.available;
          const score = card.score;
          return (
            <Card className="p-5 border-slate-200 bg-white shadow-xs space-y-3 flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500">
                  {card.label || 'ATS Compatibility Score'}
                </span>
                <div className="w-7 h-7 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center">
                  <ShieldCheck className="w-4 h-4" />
                </div>
              </div>

              <div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                    {isAvail && score !== null ? score : '--'}
                  </span>
                  {isAvail && score !== null && (
                    <span className="text-xs font-semibold text-slate-400">/ 100</span>
                  )}
                </div>

                <div className="mt-1 flex items-center gap-1.5">
                  <Badge
                    variant="outline"
                    className={cn('text-[10px] font-semibold border', getScoreColorClass(score))}
                  >
                    {card.grade_or_rating || 'Not Evaluated'}
                  </Badge>
                </div>
              </div>

              <div className="space-y-1.5 pt-1">
                <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                  <div
                    className={cn('h-full rounded-full transition-all duration-500', getScoreBarFillClass(score))}
                    style={{ width: `${Math.min(100, Math.max(0, score || 0))}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-400 line-clamp-1">{card.description}</p>
              </div>
            </Card>
          );
        })()}

        {/* Card 3: Readability Score */}
        {(() => {
          const card = summary_cards.readability || {};
          const isAvail = card.available;
          const score = card.score;
          return (
            <Card className="p-5 border-slate-200 bg-white shadow-xs space-y-3 flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500">
                  {card.label || 'Readability Score'}
                </span>
                <div className="w-7 h-7 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
                  <FileText className="w-4 h-4" />
                </div>
              </div>

              <div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                    {isAvail && score !== null ? score : '--'}
                  </span>
                  {isAvail && score !== null && (
                    <span className="text-xs font-semibold text-slate-400">/ 100</span>
                  )}
                </div>

                <div className="mt-1 flex items-center gap-1.5">
                  <Badge
                    variant="outline"
                    className={cn('text-[10px] font-semibold border', getScoreColorClass(score))}
                  >
                    {card.grade_or_rating || 'Not Evaluated'}
                  </Badge>
                </div>
              </div>

              <div className="space-y-1.5 pt-1">
                <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                  <div
                    className={cn('h-full rounded-full transition-all duration-500', getScoreBarFillClass(score))}
                    style={{ width: `${Math.min(100, Math.max(0, score || 0))}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-400 line-clamp-1">{card.description}</p>
              </div>
            </Card>
          );
        })()}

        {/* Card 4: Content Completeness Score */}
        {(() => {
          const card = summary_cards.content_completeness || {};
          const isAvail = card.available;
          const score = card.score;
          return (
            <Card className="p-5 border-slate-200 bg-white shadow-xs space-y-3 flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500">
                  {card.label || 'Content Completeness'}
                </span>
                <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                  <CheckCircle2 className="w-4 h-4" />
                </div>
              </div>

              <div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                    {isAvail && score !== null ? score : '--'}
                  </span>
                  {isAvail && score !== null && (
                    <span className="text-xs font-semibold text-slate-400">/ 100</span>
                  )}
                </div>

                <div className="mt-1 flex items-center gap-1.5">
                  <Badge
                    variant="outline"
                    className={cn('text-[10px] font-semibold border', getScoreColorClass(score))}
                  >
                    {card.grade_or_rating || 'Not Evaluated'}
                  </Badge>
                </div>
              </div>

              <div className="space-y-1.5 pt-1">
                <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                  <div
                    className={cn('h-full rounded-full transition-all duration-500', getScoreBarFillClass(score))}
                    style={{ width: `${Math.min(100, Math.max(0, score || 0))}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-400 line-clamp-1">{card.description}</p>
              </div>
            </Card>
          );
        })()}
      </div>

      {/* SECTION C: VISUAL ANALYTICS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Visual 1: Resume Quality Overview / Category Breakdown */}
        <Card className="border-slate-200 shadow-sm bg-white">
          <CardHeader className="pb-3 border-b border-slate-100">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-teal-600" />
                  Resume Quality Overview
                </CardTitle>
                <CardDescription className="text-xs text-slate-500">
                  Granular performance across 8 evaluation dimensions (Feature #21)
                </CardDescription>
              </div>
              <Badge variant="outline" className="text-[10px] bg-slate-50 text-slate-600">
                Rubric v1.0
              </Badge>
            </div>
          </CardHeader>

          <CardContent className="p-5 space-y-4">
            {visual_analytics.quality_category_breakdown && visual_analytics.quality_category_breakdown.length > 0 ? (
              visual_analytics.quality_category_breakdown.map((cat) => (
                <div key={cat.category_key} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-700">{cat.category_name}</span>
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-slate-900">
                        {cat.score} / {cat.max_score}
                      </span>
                      <span className="text-[11px] text-slate-400">({cat.score_percentage}%)</span>
                      <Badge
                        variant="outline"
                        className={cn('text-[9px] px-1.5 py-0 border', getScoreColorClass(cat.score_percentage))}
                      >
                        {cat.rating}
                      </Badge>
                    </div>
                  </div>
                  <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div
                      className={cn('h-full rounded-full transition-all duration-500', getScoreBarFillClass(cat.score_percentage))}
                      style={{ width: `${Math.min(100, Math.max(0, cat.score_percentage))}%` }}
                    />
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200 space-y-2">
                <BarChart3 className="w-8 h-8 text-slate-300 mx-auto" />
                <p className="text-xs font-semibold text-slate-600">Quality score breakdown not yet available</p>
                <p className="text-[11px] text-slate-400 max-w-xs mx-auto">
                  Run Feature #21 Quality Score to populate the 8-category performance breakdown.
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Visual 2: Score Distribution Across Features */}
        <Card className="border-slate-200 shadow-sm bg-white">
          <CardHeader className="pb-3 border-b border-slate-100">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-teal-600" />
                  Score Distribution Across Analyses
                </CardTitle>
                <CardDescription className="text-xs text-slate-500">
                  Standardized 0-100 comparison across all completed Phase 4 modules
                </CardDescription>
              </div>
            </div>
          </CardHeader>

          <CardContent className="p-5 space-y-4">
            {visual_analytics.score_distribution && visual_analytics.score_distribution.length > 0 ? (
              visual_analytics.score_distribution.map((item) => (
                <div key={item.metric} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-1.5">
                      <span className="font-semibold text-slate-700">{item.metric}</span>
                      {!item.available && (
                        <span className="text-[10px] text-slate-400">(Unanalyzed)</span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-slate-900">
                        {item.available && item.score !== null ? `${item.score}%` : '--'}
                      </span>
                      <span className="text-[11px] text-slate-500 font-medium">{item.status}</span>
                    </div>
                  </div>
                  <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                    <div
                      className={cn(
                        'h-full rounded-full transition-all duration-500',
                        item.available ? getScoreBarFillClass(item.score) : 'bg-slate-200'
                      )}
                      style={{ width: `${item.available ? Math.min(100, Math.max(0, item.score || 0)) : 0}%` }}
                    />
                  </div>
                </div>
              ))
            ) : null}

            {/* Visual 3: Strengths vs Weaknesses Balance Bar */}
            <div className="pt-3 border-t border-slate-100 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-700 flex items-center gap-1.5">
                  <Target className="w-3.5 h-3.5 text-teal-600" /> Strengths vs Weaknesses Ratio
                </span>
                <span className="text-xs font-semibold text-slate-500">
                  {visual_analytics.strengths_vs_weaknesses?.strengths_count || 0} Strengths : {visual_analytics.strengths_vs_weaknesses?.weaknesses_count || 0} Weaknesses
                </span>
              </div>

              {(() => {
                const sCount = visual_analytics.strengths_vs_weaknesses?.strengths_count || 0;
                const wCount = visual_analytics.strengths_vs_weaknesses?.weaknesses_count || 0;
                const total = sCount + wCount;
                const sRatio = total > 0 ? Math.round((sCount / total) * 100) : 50;
                const wRatio = total > 0 ? 100 - sRatio : 50;

                return (
                  <div className="space-y-1">
                    <div className="w-full h-3 rounded-full overflow-hidden flex bg-slate-100">
                      <div
                        className="bg-emerald-500 h-full transition-all duration-500"
                        style={{ width: `${sRatio}%` }}
                        title={`${sCount} Strengths (${sRatio}%)`}
                      />
                      <div
                        className="bg-amber-500 h-full transition-all duration-500"
                        style={{ width: `${wRatio}%` }}
                        title={`${wCount} Weaknesses (${wRatio}%)`}
                      />
                    </div>
                    <div className="flex justify-between text-[10px] text-slate-400 font-medium">
                      <span className="text-emerald-700">● {sCount} Strengths ({sRatio}%)</span>
                      <span className="text-amber-700">● {wCount} Weaknesses ({wRatio}%)</span>
                    </div>
                  </div>
                );
              })()}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* SECTION: SKILL DISTRIBUTION ANALYTICS (Phase 5 | Feature #29) */}
      <SkillDistributionSection resumeId={activeId} />

      {/* SECTION: RESUME IMPROVEMENT TRACKER (Phase 5 | Feature #30) */}
      <ResumeImprovementTracker resumeId={activeId} />

      {/* SECTION D: RESUME INSIGHTS (Strengths, Weaknesses, Improvements, Feature Summaries) */}
      <Card className="border-slate-200 shadow-sm bg-white overflow-hidden">
        <CardHeader className="border-b border-slate-100 pb-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Zap className="w-4 h-4 text-teal-600" />
                Synthesized Resume Insights
              </CardTitle>
              <CardDescription className="text-xs text-slate-500">
                Actionable qualitative takeaways synthesized from completed analyses
              </CardDescription>
            </div>

            {/* Insight Tabs */}
            <div className="flex items-center bg-slate-100 p-0.5 rounded-lg self-start sm:self-auto text-xs">
              <button
                type="button"
                onClick={() => setInsightsTab('strengths')}
                className={cn(
                  'px-3 py-1 rounded-md font-semibold transition-colors flex items-center gap-1.5',
                  insightsTab === 'strengths'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                )}
              >
                <Trophy className="w-3.5 h-3.5 text-emerald-600" />
                <span>Key Strengths ({resume_insights.key_strengths?.length || 0})</span>
              </button>

              <button
                type="button"
                onClick={() => setInsightsTab('weaknesses')}
                className={cn(
                  'px-3 py-1 rounded-md font-semibold transition-colors flex items-center gap-1.5',
                  insightsTab === 'weaknesses'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                )}
              >
                <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                <span>Weaknesses ({resume_insights.important_weaknesses?.length || 0})</span>
              </button>

              <button
                type="button"
                onClick={() => setInsightsTab('improvements')}
                className={cn(
                  'px-3 py-1 rounded-md font-semibold transition-colors flex items-center gap-1.5',
                  insightsTab === 'improvements'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                )}
              >
                <Zap className="w-3.5 h-3.5 text-teal-600" />
                <span>Action Areas ({resume_insights.main_improvement_areas?.length || 0})</span>
              </button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-6">
          {/* TAB 1: KEY STRENGTHS */}
          {insightsTab === 'strengths' && (
            <div className="space-y-4">
              {resume_insights.key_strengths && resume_insights.key_strengths.length > 0 ? (
                resume_insights.key_strengths.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl border border-emerald-100 bg-emerald-50/20 space-y-2 hover:border-emerald-200 transition-colors"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <Check className="w-4 h-4 text-emerald-600 shrink-0" />
                        <h4 className="text-sm font-bold text-slate-900">{item.title}</h4>
                      </div>
                      <Badge variant="outline" className="text-[10px] bg-white text-emerald-800 border-emerald-200">
                        {item.category}
                      </Badge>
                    </div>

                    <p className="text-xs text-slate-600 leading-relaxed pl-6">
                      {item.explanation}
                    </p>

                    {item.evidence && (
                      <div className="ml-6 p-2.5 bg-white rounded-lg border border-emerald-100 text-[11px] font-mono text-emerald-950 italic">
                        "{item.evidence}"
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200 space-y-2">
                  <Trophy className="w-8 h-8 text-slate-300 mx-auto" />
                  <p className="text-xs font-semibold text-slate-600">No key strengths documented yet</p>
                  <p className="text-[11px] text-slate-400">
                    Run Feature #22 Strength Analysis to extract verified strengths and competitive career advantages.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: IMPORTANT WEAKNESSES */}
          {insightsTab === 'weaknesses' && (
            <div className="space-y-4">
              {resume_insights.important_weaknesses && resume_insights.important_weaknesses.length > 0 ? (
                resume_insights.important_weaknesses.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl border border-amber-200 bg-amber-50/20 space-y-2 hover:border-amber-300 transition-colors"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
                        <h4 className="text-sm font-bold text-slate-900">{item.title}</h4>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Badge
                          variant="outline"
                          className={cn('text-[10px] border', getPriorityBadgeClass(item.priority))}
                        >
                          {item.priority} Priority
                        </Badge>
                        <Badge variant="outline" className="text-[10px] bg-white text-slate-600 border-slate-200">
                          {item.category}
                        </Badge>
                      </div>
                    </div>

                    <p className="text-xs text-slate-600 leading-relaxed pl-6">
                      {item.explanation}
                    </p>

                    {item.suggested_improvement && (
                      <div className="ml-6 p-2.5 bg-white rounded-lg border border-amber-200 text-xs text-amber-950 font-medium">
                        <span className="font-bold text-amber-800">Recommendation: </span>
                        {item.suggested_improvement}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200 space-y-2">
                  <AlertCircle className="w-8 h-8 text-slate-300 mx-auto" />
                  <p className="text-xs font-semibold text-slate-600">No weaknesses flagged yet</p>
                  <p className="text-[11px] text-slate-400">
                    Run Feature #23 Weakness Analysis to detect content gaps, unquantified bullets, and missing sections.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: MAIN IMPROVEMENT AREAS */}
          {insightsTab === 'improvements' && (
            <div className="space-y-4">
              {resume_insights.main_improvement_areas && resume_insights.main_improvement_areas.length > 0 ? (
                resume_insights.main_improvement_areas.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl border border-teal-100 bg-teal-50/20 space-y-2 hover:border-teal-200 transition-colors"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <ArrowRight className="w-4 h-4 text-teal-600 shrink-0" />
                        <h4 className="text-sm font-bold text-slate-900">{item.title}</h4>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Badge
                          variant="outline"
                          className={cn('text-[10px] border', getPriorityBadgeClass(item.priority))}
                        >
                          {item.priority}
                        </Badge>
                        <Badge variant="outline" className="text-[10px] bg-white text-teal-800 border-teal-200">
                          {item.category}
                        </Badge>
                      </div>
                    </div>

                    <p className="text-xs text-slate-700 font-medium leading-relaxed pl-6">
                      {item.suggested_action}
                    </p>
                  </div>
                ))
              ) : (
                <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200 space-y-2">
                  <Zap className="w-8 h-8 text-slate-300 mx-auto" />
                  <p className="text-xs font-semibold text-slate-600">No improvement areas recorded yet</p>
                  <p className="text-[11px] text-slate-400">
                    Run Feature #27 Improvement Recommendations to generate prioritized actionable roadmap items.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Short Module Summaries Bar */}
          {resume_insights.feature_summaries && Object.keys(resume_insights.feature_summaries).length > 0 && (
            <div className="mt-6 pt-5 border-t border-slate-100 space-y-2">
              <div className="text-xs font-bold text-slate-700">Module Summaries:</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
                {resume_insights.feature_summaries.quality && (
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
                    <div className="text-[10px] uppercase font-bold text-slate-500">Quality Score</div>
                    <div className="text-sm font-extrabold text-slate-900">
                      {resume_insights.feature_summaries.quality.overall_score}%
                    </div>
                    <div className="text-[11px] text-teal-700 font-semibold">
                      {resume_insights.feature_summaries.quality.rating_level}
                    </div>
                  </div>
                )}
                {resume_insights.feature_summaries.ats && (
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
                    <div className="text-[10px] uppercase font-bold text-slate-500">ATS Audit</div>
                    <div className="text-sm font-extrabold text-slate-900">
                      {resume_insights.feature_summaries.ats.ats_score}%
                    </div>
                    <div className="text-[11px] text-sky-700 font-semibold">
                      {resume_insights.feature_summaries.ats.score_grade}
                    </div>
                  </div>
                )}
                {resume_insights.feature_summaries.grammar && (
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
                    <div className="text-[10px] uppercase font-bold text-slate-500">Grammar & Tone</div>
                    <div className="text-sm font-extrabold text-slate-900">
                      {resume_insights.feature_summaries.grammar.writing_score}%
                    </div>
                    <div className="text-[11px] text-purple-700 font-semibold">
                      {resume_insights.feature_summaries.grammar.writing_grade}
                    </div>
                  </div>
                )}
                {resume_insights.feature_summaries.achievement && (
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
                    <div className="text-[10px] uppercase font-bold text-slate-500">Achievements</div>
                    <div className="text-sm font-extrabold text-slate-900">
                      {resume_insights.feature_summaries.achievement.achievement_score}%
                    </div>
                    <div className="text-[11px] text-emerald-700 font-semibold">
                      {resume_insights.feature_summaries.achievement.quantification_rate}% Quantified
                    </div>
                  </div>
                )}
                {resume_insights.feature_summaries.recommendations && (
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
                    <div className="text-[10px] uppercase font-bold text-slate-500">Roadmap Progress</div>
                    <div className="text-sm font-extrabold text-slate-900">
                      {resume_insights.feature_summaries.recommendations.completion_percentage}%
                    </div>
                    <div className="text-[11px] text-teal-700 font-semibold">
                      {resume_insights.feature_summaries.recommendations.completed_count}/{resume_insights.feature_summaries.recommendations.total_count} Done
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default ResumeAnalyticsDashboard;
