import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Lightbulb,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  RefreshCw,
  Search,
  CheckSquare,
  Clock,
  Layers,
  Code,
  FileText,
  Briefcase,
  Trophy,
  ShieldCheck,
  Sparkles,
  Zap,
  ArrowRight,
  Filter,
  Check,
  SlidersHorizontal,
  ChevronDown,
  ChevronUp,
  Percent,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { LoadingIndicator } from '../ui/loading-indicator';
import { Alert } from '../ui/alert';
import {
  getResumeRecommendations,
  generateResumeRecommendations,
  updateRecommendationStatus,
} from '../../services/recommendationService';
import { cn } from '../../utils/cn';

// Category metadata and display icons
const CATEGORY_META = {
  technical_skills: {
    label: 'Technical Skills',
    icon: Code,
    badgeClass: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  },
  professional_summary: {
    label: 'Professional Summary',
    icon: FileText,
    badgeClass: 'bg-sky-50 text-sky-700 border-sky-200',
  },
  project_descriptions: {
    label: 'Project Descriptions',
    icon: Layers,
    badgeClass: 'bg-purple-50 text-purple-700 border-purple-200',
  },
  work_experience: {
    label: 'Work Experience',
    icon: Briefcase,
    badgeClass: 'bg-blue-50 text-blue-700 border-blue-200',
  },
  achievements_impact: {
    label: 'Achievements & Impact',
    icon: Trophy,
    badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  },
  ats_compatibility: {
    label: 'ATS Compatibility',
    icon: ShieldCheck,
    badgeClass: 'bg-amber-50 text-amber-700 border-amber-200',
  },
  grammar_clarity: {
    label: 'Grammar & Clarity',
    icon: Sparkles,
    badgeClass: 'bg-teal-50 text-teal-700 border-teal-200',
  },
  resume_completeness: {
    label: 'Resume Completeness',
    icon: CheckSquare,
    badgeClass: 'bg-slate-50 text-slate-700 border-slate-200',
  },
};

function getPriorityBadgeClass(priority) {
  const p = (priority || '').toLowerCase();
  if (p === 'critical') return 'bg-rose-100 text-rose-800 border-rose-300 font-semibold';
  if (p === 'high') return 'bg-amber-100 text-amber-800 border-amber-300 font-semibold';
  if (p === 'medium') return 'bg-blue-100 text-blue-800 border-blue-300';
  return 'bg-slate-100 text-slate-700 border-slate-300';
}

function getEffortBadgeClass(effort) {
  const e = (effort || '').toLowerCase();
  if (e === 'easy') return 'bg-emerald-50 text-emerald-700 border-emerald-200';
  if (e === 'medium') return 'bg-amber-50 text-amber-700 border-amber-200';
  return 'bg-purple-50 text-purple-700 border-purple-200';
}

/**
 * ResumeRecommendationDashboard Component
 * Phase 4 | Feature #27: Resume Improvement Recommendations
 */
export function ResumeRecommendationDashboard({ resumeId, className }) {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);

  // Filters state
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedPriority, setSelectedPriority] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all'); // 'all' | 'pending' | 'completed'
  const [searchQuery, setSearchQuery] = useState('');

  // Toggling state tracker per item
  const [togglingIds, setTogglingIds] = useState(new Set());

  // Load recommendations
  const fetchRecommendations = useCallback(async () => {
    if (!resumeId) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await getResumeRecommendations(resumeId);
      setData(res.data);
    } catch (err) {
      if (err.status === 404) {
        // Not generated yet, let user trigger or auto-generate
        setData(null);
      } else {
        setError(err.message || 'Failed to load recommendations.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [resumeId]);

  useEffect(() => {
    fetchRecommendations();
  }, [fetchRecommendations]);

  // Generate / Regenerate recommendations
  const handleGenerate = async (forceRecalculate = false) => {
    if (!resumeId || isGenerating) return;
    setIsGenerating(true);
    setError(null);
    try {
      const res = await generateResumeRecommendations(resumeId, { forceRecalculate });
      setData(res.data);
    } catch (err) {
      setError(err.message || 'Failed to generate improvement recommendations.');
    } finally {
      setIsGenerating(false);
    }
  };

  // Toggle completion status
  const handleToggleStatus = async (item) => {
    if (!item?.id || togglingIds.has(item.id)) return;

    const nextCompleted = !item.is_completed;
    setTogglingIds((prev) => new Set(prev).add(item.id));

    // Optimistic UI update
    setData((prev) => {
      if (!prev) return prev;
      const updatedRecs = (prev.recommendations || []).map((r) => {
        if (r.id === item.id) {
          return {
            ...r,
            is_completed: nextCompleted,
            completed_at: nextCompleted ? new Date().toISOString() : null,
          };
        }
        return r;
      });

      const total = updatedRecs.length;
      const completed = updatedRecs.filter((r) => r.is_completed).length;
      const pending = total - completed;
      const percentage = total > 0 ? Math.round((completed / total) * 1000) / 10 : 0;

      return {
        ...prev,
        recommendations: updatedRecs,
        completed_count: completed,
        pending_count: pending,
        completion_percentage: percentage,
      };
    });

    try {
      await updateRecommendationStatus(resumeId, item.id, nextCompleted);
    } catch (err) {
      // Revert on error
      setError(`Failed to update status for ${item.id}: ${err.message}`);
      fetchRecommendations();
    } finally {
      setTogglingIds((prev) => {
        const next = new Set(prev);
        next.delete(item.id);
        return next;
      });
    }
  };

  // Filter recommendations based on category, priority, status, and search query
  const filteredRecommendations = useMemo(() => {
    if (!data?.recommendations) return [];

    return data.recommendations.filter((item) => {
      // Category filter
      if (selectedCategory !== 'all' && item.category !== selectedCategory) {
        return false;
      }
      // Priority filter
      if (selectedPriority !== 'all' && item.priority.toLowerCase() !== selectedPriority.toLowerCase()) {
        return false;
      }
      // Status filter
      if (selectedStatus === 'pending' && item.is_completed) {
        return false;
      }
      if (selectedStatus === 'completed' && !item.is_completed) {
        return false;
      }
      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const titleMatch = item.title?.toLowerCase().includes(q);
        const explanationMatch = item.explanation?.toLowerCase().includes(q);
        const actionMatch = item.suggested_action?.toLowerCase().includes(q);
        const idMatch = item.id?.toLowerCase().includes(q);
        if (!titleMatch && !explanationMatch && !actionMatch && !idMatch) {
          return false;
        }
      }
      return true;
    });
  }, [data, selectedCategory, selectedPriority, selectedStatus, searchQuery]);

  // Loading Initial State
  if (isLoading) {
    return (
      <Card className={cn('p-8 border-slate-200 text-center space-y-4 shadow-sm', className)}>
        <LoadingIndicator size="lg" className="text-teal-600 mx-auto" />
        <p className="text-sm font-semibold text-slate-800">
          Loading Resume Improvement Recommendations...
        </p>
      </Card>
    );
  }

  // Not generated state
  if (!data && !isGenerating) {
    return (
      <Card className={cn('border-slate-200 shadow-sm overflow-hidden', className)}>
        <CardHeader className="bg-gradient-to-r from-teal-50/60 via-slate-50 to-indigo-50/60 border-b border-slate-100 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-600 text-white flex items-center justify-center shadow-sm">
              <Lightbulb className="w-5 h-5" />
            </div>
            <div>
              <CardTitle className="text-base font-bold text-slate-900">
                Resume Improvement Recommendations
              </CardTitle>
              <CardDescription className="text-xs text-slate-500">
                Phase 4 | Feature #27: Multi-analysis synthesis & actionable roadmap
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-8 text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-teal-50 text-teal-600 flex items-center justify-center mx-auto">
            <Sparkles className="w-6 h-6" />
          </div>
          <div className="max-w-md mx-auto space-y-1">
            <h4 className="text-sm font-bold text-slate-800">
              No Recommendations Generated Yet
            </h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              Combine findings from Quality Score, Strengths, Weaknesses, ATS Compatibility, Grammar, and Achievements into a personalized, prioritized improvement roadmap.
            </p>
          </div>
          <Button
            onClick={() => handleGenerate(false)}
            className="text-xs h-9 bg-teal-600 hover:bg-teal-700 text-white font-semibold inline-flex items-center gap-2"
          >
            <Zap className="w-4 h-4" />
            Generate Recommendations
          </Button>
        </CardContent>
      </Card>
    );
  }

  // Active generating state
  if (isGenerating) {
    return (
      <Card className={cn('p-12 border-teal-200 bg-teal-50/20 text-center space-y-4 shadow-sm', className)}>
        <LoadingIndicator size="lg" className="text-teal-600 mx-auto" />
        <div className="space-y-1">
          <h4 className="text-sm font-bold text-slate-800">
            Synthesizing Resume Intelligence...
          </h4>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Executing 7-stage LangGraph workflow across Quality, Strengths, Weaknesses, ATS Compatibility, Grammar, and Accomplishments to generate prioritized recommendations.
          </p>
        </div>
      </Card>
    );
  }

  const {
    overall_summary,
    total_recommendations_count,
    completed_count,
    pending_count,
    completion_percentage,
    priority_breakdown = {},
    coverage_summary = {},
    recommendations = [],
  } = data || {};

  const isFullCoverage = coverage_summary?.is_full_coverage;

  return (
    <Card className={cn('border-slate-200 shadow-sm overflow-hidden', className)}>
      {/* Header */}
      <CardHeader className="bg-gradient-to-r from-teal-50/70 via-slate-50 to-indigo-50/70 border-b border-slate-100 pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-600 text-white flex items-center justify-center shadow-sm">
              <Lightbulb className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <CardTitle className="text-base font-bold text-slate-900">
                  Resume Improvement Recommendations
                </CardTitle>
                <Badge
                  variant="outline"
                  className={cn(
                    'text-[10px] font-semibold border',
                    isFullCoverage
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : 'bg-amber-50 text-amber-700 border-amber-200'
                  )}
                >
                  {isFullCoverage
                    ? 'Full 6/6 Analysis Coverage'
                    : `${coverage_summary?.available_features?.length || 0}/6 Analyses Covered`}
                </Badge>
              </div>
              <CardDescription className="text-xs text-slate-500">
                Actionable step-by-step roadmap synthesizing previous resume evaluations
              </CardDescription>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleGenerate(true)}
              disabled={isGenerating}
              className="text-xs h-8 border-slate-200 text-slate-700 hover:bg-slate-100 flex items-center gap-1.5"
              title="Re-run recommendation engine with latest resume data"
            >
              <RefreshCw className={cn('w-3.5 h-3.5', isGenerating && 'animate-spin')} />
              <span>Re-evaluate</span>
            </Button>
          </div>
        </div>

        {error && (
          <Alert variant="destructive" className="mt-3">
            <p className="text-xs">{error}</p>
          </Alert>
        )}
      </CardHeader>

      <CardContent className="p-6 space-y-6">
        {/* Coverage Note Banner (if partial) */}
        {!isFullCoverage && coverage_summary?.coverage_notes && (
          <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-lg flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <div className="text-xs text-amber-800 leading-relaxed">
              <span className="font-semibold">Partial Coverage Note: </span>
              {coverage_summary.coverage_notes}
            </div>
          </div>
        )}

        {/* Executive Summary */}
        {overall_summary && (
          <div className="p-4 bg-slate-50/80 border border-slate-100 rounded-xl space-y-1.5">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-700 uppercase tracking-wider">
              <Zap className="w-3.5 h-3.5 text-teal-600" />
              Strategic Overview
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              {overall_summary}
            </p>
          </div>
        )}

        {/* Progress & Stat Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          {/* Completion Percentage Progress */}
          <div className="p-4 rounded-xl border border-slate-200 bg-white shadow-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500">Progress</span>
              <span className="text-xs font-bold text-teal-600">{completion_percentage}%</span>
            </div>
            <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
              <div
                className="bg-teal-600 h-full rounded-full transition-all duration-500 ease-out"
                style={{ width: `${Math.min(100, Math.max(0, completion_percentage))}%` }}
              />
            </div>
            <div className="text-[11px] text-slate-400">
              {completed_count} of {total_recommendations_count} completed
            </div>
          </div>

          {/* Total Recommendations */}
          <div className="p-4 rounded-xl border border-slate-200 bg-white shadow-xs flex items-center justify-between">
            <div className="space-y-0.5">
              <span className="text-xs font-semibold text-slate-500">Total Items</span>
              <div className="text-xl font-extrabold text-slate-900">{total_recommendations_count}</div>
              <span className="text-[10px] text-slate-400">Roadmap recommendations</span>
            </div>
            <div className="w-10 h-10 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center">
              <CheckSquare className="w-5 h-5" />
            </div>
          </div>

          {/* Pending Items */}
          <div className="p-4 rounded-xl border border-amber-200 bg-amber-50/30 shadow-xs flex items-center justify-between">
            <div className="space-y-0.5">
              <span className="text-xs font-semibold text-amber-700">Pending</span>
              <div className="text-xl font-extrabold text-amber-900">{pending_count}</div>
              <span className="text-[10px] text-amber-600">Action items to address</span>
            </div>
            <div className="w-10 h-10 rounded-lg bg-amber-100 text-amber-700 flex items-center justify-center">
              <Clock className="w-5 h-5" />
            </div>
          </div>

          {/* Completed Items */}
          <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/30 shadow-xs flex items-center justify-between">
            <div className="space-y-0.5">
              <span className="text-xs font-semibold text-emerald-700">Completed</span>
              <div className="text-xl font-extrabold text-emerald-900">{completed_count}</div>
              <span className="text-[10px] text-emerald-600">Successfully improved</span>
            </div>
            <div className="w-10 h-10 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>
        </div>

        {/* Priority Filter Breakdown */}
        <div className="space-y-2">
          <div className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
            <SlidersHorizontal className="w-3.5 h-3.5 text-slate-400" />
            <span>Filter by Priority</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { key: 'Critical', label: 'Critical', color: 'border-rose-300 bg-rose-50/50 text-rose-800 hover:bg-rose-100/50' },
              { key: 'High', label: 'High Priority', color: 'border-amber-300 bg-amber-50/50 text-amber-800 hover:bg-amber-100/50' },
              { key: 'Medium', label: 'Medium Priority', color: 'border-blue-300 bg-blue-50/50 text-blue-800 hover:bg-blue-100/50' },
              { key: 'Low', label: 'Low / Polish', color: 'border-slate-300 bg-slate-50 text-slate-800 hover:bg-slate-100' },
            ].map(({ key, label, color }) => {
              const count = priority_breakdown[key] || 0;
              const isSelected = selectedPriority === key;
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => setSelectedPriority(isSelected ? 'all' : key)}
                  className={cn(
                    'p-3 rounded-lg border text-left transition-all flex items-center justify-between',
                    color,
                    isSelected ? 'ring-2 ring-teal-600 shadow-xs' : 'opacity-85'
                  )}
                >
                  <div>
                    <div className="text-[11px] font-semibold">{label}</div>
                    <div className="text-base font-extrabold mt-0.5">{count}</div>
                  </div>
                  {isSelected && <Check className="w-4 h-4 text-teal-700 shrink-0" />}
                </button>
              );
            })}
          </div>
        </div>

        {/* Category Tabs & Toolbar */}
        <div className="space-y-3 pt-2 border-t border-slate-100">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
            {/* Category selection */}
            <div className="text-xs font-bold text-slate-700">
              Categories ({recommendations.length} total)
            </div>

            {/* Search and Status Filters */}
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative min-w-[200px]">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search recommendations..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full h-8 pl-8 pr-3 text-xs rounded-md border border-slate-200 focus:outline-none focus:ring-1 focus:ring-teal-500 bg-white"
                />
              </div>

              {/* Status Filter */}
              <div className="flex items-center bg-slate-100 p-0.5 rounded-md text-xs">
                {['all', 'pending', 'completed'].map((statusKey) => (
                  <button
                    key={statusKey}
                    type="button"
                    onClick={() => setSelectedStatus(statusKey)}
                    className={cn(
                      'px-2.5 py-1 rounded capitalize font-medium transition-colors',
                      selectedStatus === statusKey
                        ? 'bg-white text-slate-900 shadow-xs'
                        : 'text-slate-600 hover:text-slate-900'
                    )}
                  >
                    {statusKey}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Horizontal Category Pill Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-none">
            <button
              type="button"
              onClick={() => setSelectedCategory('all')}
              className={cn(
                'px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-colors border',
                selectedCategory === 'all'
                  ? 'bg-teal-600 text-white border-teal-600'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              )}
            >
              All Categories ({recommendations.length})
            </button>

            {Object.entries(CATEGORY_META).map(([key, meta]) => {
              const count = recommendations.filter((r) => r.category === key).length;
              const isSelected = selectedCategory === key;
              const Icon = meta.icon;
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => setSelectedCategory(key)}
                  className={cn(
                    'px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors flex items-center gap-1.5 border',
                    isSelected
                      ? 'bg-teal-600 text-white border-teal-600 font-semibold'
                      : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                  )}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{meta.label}</span>
                  <span className={cn('text-[10px] px-1.5 py-0.2 rounded-full', isSelected ? 'bg-teal-700 text-teal-100' : 'bg-slate-100 text-slate-500')}>
                    {count}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Filtered Recommendations List */}
        <div className="space-y-4">
          {filteredRecommendations.length === 0 ? (
            <div className="p-8 text-center bg-slate-50/50 rounded-xl border border-dashed border-slate-200 space-y-2">
              <CheckCircle2 className="w-8 h-8 text-slate-300 mx-auto" />
              <div className="text-xs font-semibold text-slate-600">
                No recommendations match your active filters.
              </div>
              <p className="text-[11px] text-slate-400">
                Try clearing category, priority, or search filters.
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSelectedCategory('all');
                  setSelectedPriority('all');
                  setSelectedStatus('all');
                  setSearchQuery('');
                }}
                className="text-xs h-7 mt-1 border-slate-200"
              >
                Reset Filters
              </Button>
            </div>
          ) : (
            filteredRecommendations.map((item) => {
              const isCompleted = item.is_completed;
              const isToggling = togglingIds.has(item.id);
              const catMeta = CATEGORY_META[item.category] || CATEGORY_META.resume_completeness;
              const CatIcon = catMeta.icon;

              return (
                <div
                  key={item.id}
                  className={cn(
                    'p-5 rounded-xl border transition-all duration-200 bg-white space-y-4',
                    isCompleted
                      ? 'border-emerald-200 bg-emerald-50/20 opacity-80'
                      : 'border-slate-200 hover:border-slate-300 shadow-xs'
                  )}
                >
                  {/* Top Bar: Checkbox + Title + Badges */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3 min-w-0">
                      {/* Completion Checkbox */}
                      <button
                        type="button"
                        onClick={() => handleToggleStatus(item)}
                        disabled={isToggling}
                        aria-label={isCompleted ? 'Mark as incomplete' : 'Mark as completed'}
                        className={cn(
                          'w-5 h-5 rounded mt-0.5 flex items-center justify-center transition-colors border shrink-0',
                          isCompleted
                            ? 'bg-emerald-600 border-emerald-600 text-white shadow-xs'
                            : 'border-slate-300 hover:border-teal-500 bg-white text-transparent',
                          isToggling && 'opacity-50 cursor-wait'
                        )}
                      >
                        <Check className="w-3.5 h-3.5 stroke-[3]" />
                      </button>

                      {/* Title and ID */}
                      <div className="space-y-1 min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-[10px] font-mono text-slate-400 shrink-0">
                            {item.id}
                          </span>
                          <h4
                            className={cn(
                              'text-sm font-bold text-slate-900 leading-snug',
                              isCompleted && 'line-through text-slate-500'
                            )}
                          >
                            {item.title}
                          </h4>
                        </div>

                        {/* Badges row */}
                        <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                          {/* Priority */}
                          <Badge
                            variant="outline"
                            className={cn('text-[10px] px-2 py-0.5 border', getPriorityBadgeClass(item.priority))}
                          >
                            {item.priority} Priority
                          </Badge>

                          {/* Effort */}
                          <Badge
                            variant="outline"
                            className={cn('text-[10px] px-2 py-0.5 border', getEffortBadgeClass(item.estimated_effort))}
                          >
                            Effort: {item.estimated_effort}
                          </Badge>

                          {/* Category */}
                          <Badge
                            variant="outline"
                            className={cn('text-[10px] px-2 py-0.5 border flex items-center gap-1', catMeta.badgeClass)}
                          >
                            <CatIcon className="w-3 h-3" />
                            <span>{item.category_name || catMeta.label}</span>
                          </Badge>

                          {/* Related Feature */}
                          <span className="text-[10px] text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full border border-slate-200">
                            {item.related_feature}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Completed At Timestamp */}
                    {isCompleted && item.completed_at && (
                      <div className="text-[10px] text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-md shrink-0">
                        Completed
                      </div>
                    )}
                  </div>

                  {/* Detailed Explanation */}
                  <div className="text-xs text-slate-600 leading-relaxed pl-8">
                    {item.explanation}
                  </div>

                  {/* Why it Matters (Reason) */}
                  {item.reason && (
                    <div className="ml-8 p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
                      <div className="text-[11px] font-bold text-slate-700 flex items-center gap-1.5">
                        <Zap className="w-3 h-3 text-amber-500" />
                        <span>Why this recommendation matters:</span>
                      </div>
                      <p className="text-xs text-slate-600 leading-relaxed">
                        {item.reason}
                      </p>
                    </div>
                  )}

                  {/* Supporting Evidence */}
                  {item.evidence && (
                    <div className="ml-8 p-3 bg-amber-50/40 rounded-lg border border-amber-100 space-y-1">
                      <div className="text-[11px] font-bold text-amber-900 flex items-center gap-1.5">
                        <FileText className="w-3 h-3 text-amber-600" />
                        <span>Supporting Resume Evidence:</span>
                      </div>
                      <blockquote className="text-xs font-mono text-amber-950 italic border-l-2 border-amber-400 pl-2 leading-relaxed">
                        "{item.evidence}"
                      </blockquote>
                    </div>
                  )}

                  {/* Suggested Action Box */}
                  {item.suggested_action && (
                    <div className="ml-8 p-3.5 bg-gradient-to-r from-teal-50/70 to-emerald-50/50 rounded-xl border border-teal-200/80 space-y-1.5">
                      <div className="text-xs font-bold text-teal-900 flex items-center gap-1.5">
                        <ArrowRight className="w-3.5 h-3.5 text-teal-600" />
                        <span>Suggested Action & Implementation Steps:</span>
                      </div>
                      <p className="text-xs text-teal-950 font-medium leading-relaxed">
                        {item.suggested_action}
                      </p>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default ResumeRecommendationDashboard;
