import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  CheckCircle2,
  Circle,
  Clock,
  ArrowRight,
  ArrowUpRight,
  ArrowDownRight,
  Sparkles,
  RefreshCw,
  FileText,
  Layers,
  Filter,
  Check,
  RotateCcw,
  History,
  GitCompare,
  AlertTriangle,
  Calendar,
  ChevronDown,
  ListTodo,
  Milestone,
  CheckSquare,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { LoadingIndicator } from '../ui/loading-indicator';
import { Alert } from '../ui/alert';
import {
  getResumeImprovements,
  updateResumeImprovementTask,
  compareResumeVersions,
} from '../../services/improvementService';
import { cn } from '../../utils/cn';

/**
 * Helper to style score deltas: improved (green), declined (red), unchanged (slate)
 */
function renderScoreDeltaBadge(metric) {
  if (!metric || metric.status === 'no_previous_data' || metric.delta === null) {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full font-medium">
        <Minus className="w-3 h-3" /> Baseline
      </span>
    );
  }

  if (metric.status === 'improved') {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full font-semibold">
        <ArrowUpRight className="w-3.5 h-3.5" /> +{metric.delta.toFixed(1)}
      </span>
    );
  }

  if (metric.status === 'declined') {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-rose-700 bg-rose-50 border border-rose-200 px-2 py-0.5 rounded-full font-semibold">
        <ArrowDownRight className="w-3.5 h-3.5" /> {metric.delta.toFixed(1)}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 text-xs text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full font-medium">
      <Minus className="w-3 h-3" /> No Change
    </span>
  );
}

function getPriorityBadgeClass(priority) {
  const p = (priority || '').toLowerCase();
  if (p === 'high' || p === 'critical') return 'bg-rose-50 text-rose-700 border-rose-200 font-semibold';
  if (p === 'medium') return 'bg-amber-50 text-amber-700 border-amber-200 font-medium';
  return 'bg-slate-100 text-slate-700 border-slate-200';
}

function getStatusBadgeClass(status) {
  const s = (status || '').toLowerCase();
  if (s === 'completed') return 'bg-emerald-50 text-emerald-700 border-emerald-200';
  if (s === 'in progress' || s === 'inprogress') return 'bg-blue-50 text-blue-700 border-blue-200';
  return 'bg-amber-50 text-amber-700 border-amber-200';
}

function formatEventTimestamp(isoStr) {
  if (!isoStr) return '';
  try {
    const d = new Date(isoStr);
    return d.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return isoStr;
  }
}

/**
 * ResumeImprovementTracker Component
 * Phase 5 | Feature #30: Resume Improvement Tracker
 */
export function ResumeImprovementTracker({ resumeId, className }) {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState(null);

  // Active view tab: 'overview' | 'tasks' | 'timeline' | 'compare'
  const [activeTab, setActiveTab] = useState('overview');

  // Filters for tasks
  const [statusFilter, setStatusFilter] = useState('All');
  const [priorityFilter, setPriorityFilter] = useState('All');
  const [updatingTaskId, setUpdatingTaskId] = useState(null);

  // Version comparison state
  const [v1Select, setV1Select] = useState('');
  const [v2Select, setV2Select] = useState('');
  const [comparisonData, setComparisonData] = useState(null);
  const [isComparing, setIsComparing] = useState(false);
  const [comparisonError, setComparisonError] = useState(null);

  const fetchTrackerData = useCallback(async (isRefresh = false) => {
    if (!resumeId) return;
    if (isRefresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);

    try {
      const res = await getResumeImprovements(resumeId);
      setData(res.data);

      // Pre-populate version selection if available
      if (res.data?.available_versions && res.data.available_versions.length >= 2) {
        setV1Select(String(res.data.available_versions[1].version_number));
        setV2Select(String(res.data.available_versions[0].version_number));
      } else if (res.data?.available_versions && res.data.available_versions.length === 1) {
        setV1Select(String(res.data.available_versions[0].version_number));
        setV2Select(String(res.data.available_versions[0].version_number));
      }
    } catch (err) {
      setError(err.message || 'Failed to load resume improvement tracking data.');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [resumeId]);

  useEffect(() => {
    fetchTrackerData();
  }, [fetchTrackerData]);

  const handleUpdateStatus = async (taskId, newStatus) => {
    if (!resumeId || !taskId) return;
    setUpdatingTaskId(taskId);
    try {
      await updateResumeImprovementTask(resumeId, taskId, { status: newStatus });
      // Refresh tracker to re-compute percentages and timeline
      await fetchTrackerData(true);
    } catch (err) {
      alert(`Error updating task status: ${err.message}`);
    } finally {
      setUpdatingTaskId(null);
    }
  };

  const handleRunComparison = async () => {
    if (!resumeId) return;
    setIsComparing(true);
    setComparisonError(null);
    try {
      const v1Num = v1Select ? parseInt(v1Select, 10) : undefined;
      const v2Num = v2Select ? parseInt(v2Select, 10) : undefined;
      const res = await compareResumeVersions(resumeId, v1Num, v2Num);
      setComparisonData(res.data);
    } catch (err) {
      setComparisonError(err.message || 'Failed to compare resume versions.');
    } finally {
      setIsComparing(false);
    }
  };

  // Filtered tasks
  const filteredTasks = useMemo(() => {
    if (!data?.tasks) return [];
    return data.tasks.filter((t) => {
      const matchStatus =
        statusFilter === 'All' || t.status.toLowerCase() === statusFilter.toLowerCase();
      const matchPriority =
        priorityFilter === 'All' || t.priority.toLowerCase() === priorityFilter.toLowerCase();
      return matchStatus && matchPriority;
    });
  }, [data?.tasks, statusFilter, priorityFilter]);

  if (isLoading) {
    return (
      <Card className="border-slate-200 shadow-sm bg-white p-8">
        <div className="flex flex-col items-center justify-center space-y-4 text-center">
          <LoadingIndicator size="lg" text="Loading improvement tracker..." />
          <p className="text-xs text-slate-500 max-w-sm">
            Retrieving historical snapshots, score changes, actionable tasks, and version timeline...
          </p>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-slate-200 shadow-sm bg-white p-6">
        <Alert variant="error" title="Unable to Load Improvement Tracker">
          {error}
        </Alert>
        <div className="mt-4 flex justify-end">
          <Button
            size="sm"
            onClick={() => fetchTrackerData()}
            className="flex items-center gap-1.5"
          >
            <RefreshCw className="w-4 h-4" /> Try Again
          </Button>
        </div>
      </Card>
    );
  }

  if (!data) return null;

  const { score_comparison, progress_overview, tasks, timeline, history, available_versions } = data;

  return (
    <div className={cn('space-y-6', className)}>
      {/* HEADER CARD */}
      <Card className="border-slate-200 shadow-sm bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 text-white overflow-hidden">
        <div className="p-6 sm:p-7">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold tracking-wide uppercase bg-teal-500/20 text-teal-300 border border-teal-500/30">
                  <Sparkles className="w-3.5 h-3.5" /> Feature #30 • Improvement Tracker
                </span>
                <span className="text-xs text-slate-400">
                  {available_versions?.length || 1} Version{available_versions?.length !== 1 ? 's' : ''}
                </span>
              </div>
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                Resume Quality & Improvement Tracker
              </h2>
              <p className="text-sm text-slate-300 max-w-2xl leading-relaxed">
                Monitor version-over-version quality changes, track completed recommendations, and measure actionable progress over time.
              </p>
            </div>

            <div className="flex items-center gap-2 self-start sm:self-auto shrink-0">
              <Button
                variant="outline"
                size="sm"
                onClick={() => fetchTrackerData(true)}
                disabled={isRefreshing}
                className="bg-white/10 hover:bg-white/20 text-white border-white/20 text-xs flex items-center gap-1.5 backdrop-blur-sm"
              >
                <RefreshCw className={cn('w-3.5 h-3.5', isRefreshing && 'animate-spin')} />
                {isRefreshing ? 'Refreshing...' : 'Refresh'}
              </Button>
            </div>
          </div>

          {/* TAB NAVIGATION PILLS */}
          <div className="mt-6 flex flex-wrap items-center gap-2 border-t border-white/10 pt-4">
            <button
              type="button"
              onClick={() => setActiveTab('overview')}
              className={cn(
                'flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all',
                activeTab === 'overview'
                  ? 'bg-teal-500 text-slate-950 shadow-sm'
                  : 'bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white'
              )}
            >
              <TrendingUp className="w-3.5 h-3.5" /> Score Comparison & Progress
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('tasks')}
              className={cn(
                'flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all',
                activeTab === 'tasks'
                  ? 'bg-teal-500 text-slate-950 shadow-sm'
                  : 'bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white'
              )}
            >
              <ListTodo className="w-3.5 h-3.5" /> Actionable Tasks ({tasks?.length || 0})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('timeline')}
              className={cn(
                'flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all',
                activeTab === 'timeline'
                  ? 'bg-teal-500 text-slate-950 shadow-sm'
                  : 'bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white'
              )}
            >
              <Milestone className="w-3.5 h-3.5" /> Improvement Timeline ({timeline?.length || 0})
            </button>
            <button
              type="button"
              onClick={() => {
                setActiveTab('compare');
                if (!comparisonData) handleRunComparison();
              }}
              className={cn(
                'flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all',
                activeTab === 'compare'
                  ? 'bg-teal-500 text-slate-950 shadow-sm'
                  : 'bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white'
              )}
            >
              <GitCompare className="w-3.5 h-3.5" /> Version Comparison
            </button>
          </div>
        </div>
      </Card>

      {/* PROGRESS SUMMARY CARDS */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3.5">
        {/* Total Tasks */}
        <Card className="border-slate-200 shadow-sm bg-white p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Tasks</span>
            <ListTodo className="w-4 h-4 text-slate-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">{progress_overview.total_tasks}</div>
          <p className="mt-1 text-[11px] text-slate-500">Action items identified</p>
        </Card>

        {/* Completed Tasks */}
        <Card className="border-slate-200 shadow-sm bg-white p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Completed</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-700">{progress_overview.completed_tasks}</div>
          <p className="mt-1 text-[11px] text-emerald-600/80">Tasks resolved</p>
        </Card>

        {/* In Progress */}
        <Card className="border-slate-200 shadow-sm bg-white p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">In Progress</span>
            <Clock className="w-4 h-4 text-blue-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-blue-700">{progress_overview.in_progress_tasks}</div>
          <p className="mt-1 text-[11px] text-blue-600/80">Currently being addressed</p>
        </Card>

        {/* Pending */}
        <Card className="border-slate-200 shadow-sm bg-white p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Pending</span>
            <AlertTriangle className="w-4 h-4 text-amber-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-amber-700">{progress_overview.pending_tasks}</div>
          <p className="mt-1 text-[11px] text-amber-600/80">Awaiting action</p>
        </Card>

        {/* Completion % */}
        <Card className="col-span-2 sm:col-span-1 border-slate-200 shadow-sm bg-white p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Task Progress</span>
            <CheckSquare className="w-4 h-4 text-teal-600" />
          </div>
          <div className="mt-2 flex items-baseline gap-1.5">
            <span className="text-2xl font-bold text-teal-700">{progress_overview.completion_percentage}%</span>
            <span className="text-[11px] text-slate-500">done</span>
          </div>
          <div className="mt-2 w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-teal-600 h-1.5 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, Math.max(0, progress_overview.completion_percentage))}%` }}
            />
          </div>
        </Card>
      </div>

      {/* TAB 1: OVERVIEW & SCORE COMPARISON */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* SCORE COMPARISON CARDS */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Overall Score Comparison */}
            <Card className="border-slate-200 shadow-sm bg-white">
              <CardHeader className="pb-3 border-b border-slate-100">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-semibold text-slate-800">Overall Quality Score</CardTitle>
                  {renderScoreDeltaBadge(score_comparison?.overall_score)}
                </div>
              </CardHeader>
              <CardContent className="pt-4">
                <div className="flex items-baseline justify-between">
                  <div>
                    <span className="text-xs text-slate-400">Previous</span>
                    <div className="text-lg font-medium text-slate-500">
                      {score_comparison?.overall_score?.previous_score !== null && score_comparison?.overall_score?.previous_score !== undefined
                        ? `${score_comparison.overall_score.previous_score.toFixed(1)}/100`
                        : '—'}
                    </div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-300" />
                  <div className="text-right">
                    <span className="text-xs text-slate-400">Latest</span>
                    <div className="text-2xl font-bold text-slate-900">
                      {score_comparison?.overall_score?.latest_score !== null && score_comparison?.overall_score?.latest_score !== undefined
                        ? `${score_comparison.overall_score.latest_score.toFixed(1)}/100`
                        : 'Not Evaluated'}
                    </div>
                  </div>
                </div>
                <p className="mt-3 text-[11px] text-slate-500">
                  Comprehensive 8-category evaluation based on actual stored snapshots.
                </p>
              </CardContent>
            </Card>

            {/* ATS Score Comparison */}
            <Card className="border-slate-200 shadow-sm bg-white">
              <CardHeader className="pb-3 border-b border-slate-100">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-semibold text-slate-800">ATS Compatibility</CardTitle>
                  {renderScoreDeltaBadge(score_comparison?.ats_compatibility)}
                </div>
              </CardHeader>
              <CardContent className="pt-4">
                <div className="flex items-baseline justify-between">
                  <div>
                    <span className="text-xs text-slate-400">Previous</span>
                    <div className="text-lg font-medium text-slate-500">
                      {score_comparison?.ats_compatibility?.previous_score !== null && score_comparison?.ats_compatibility?.previous_score !== undefined
                        ? `${score_comparison.ats_compatibility.previous_score.toFixed(1)}/100`
                        : '—'}
                    </div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-300" />
                  <div className="text-right">
                    <span className="text-xs text-slate-400">Latest</span>
                    <div className="text-2xl font-bold text-slate-900">
                      {score_comparison?.ats_compatibility?.latest_score !== null && score_comparison?.ats_compatibility?.latest_score !== undefined
                        ? `${score_comparison.ats_compatibility.latest_score.toFixed(1)}/100`
                        : 'Not Evaluated'}
                    </div>
                  </div>
                </div>
                <p className="mt-3 text-[11px] text-slate-500">
                  Parsing hygiene, standard headings, and applicant system readability.
                </p>
              </CardContent>
            </Card>

            {/* Readability Score Comparison */}
            <Card className="border-slate-200 shadow-sm bg-white">
              <CardHeader className="pb-3 border-b border-slate-100">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-semibold text-slate-800">Readability Score</CardTitle>
                  {renderScoreDeltaBadge(score_comparison?.readability)}
                </div>
              </CardHeader>
              <CardContent className="pt-4">
                <div className="flex items-baseline justify-between">
                  <div>
                    <span className="text-xs text-slate-400">Previous</span>
                    <div className="text-lg font-medium text-slate-500">
                      {score_comparison?.readability?.previous_score !== null && score_comparison?.readability?.previous_score !== undefined
                        ? `${score_comparison.readability.previous_score.toFixed(1)}/100`
                        : '—'}
                    </div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-300" />
                  <div className="text-right">
                    <span className="text-xs text-slate-400">Latest</span>
                    <div className="text-2xl font-bold text-slate-900">
                      {score_comparison?.readability?.latest_score !== null && score_comparison?.readability?.latest_score !== undefined
                        ? `${score_comparison.readability.latest_score.toFixed(1)}/100`
                        : 'Not Evaluated'}
                    </div>
                  </div>
                </div>
                <p className="mt-3 text-[11px] text-slate-500">
                  Sentence length, grammatical clarity, active voice, and professional tone.
                </p>
              </CardContent>
            </Card>
          </div>

          {/* HISTORICAL SNAPSHOTS TABLE */}
          <Card className="border-slate-200 shadow-sm bg-white">
            <CardHeader className="border-b border-slate-100 pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base font-semibold text-slate-900 flex items-center gap-2">
                    <History className="w-4 h-4 text-teal-600" /> Historical Analysis Snapshots
                  </CardTitle>
                  <CardDescription className="text-xs text-slate-500 mt-0.5">
                    Chronological audit log of evaluation runs. Older snapshots are preserved permanently.
                  </CardDescription>
                </div>
                <Badge variant="outline" className="text-xs text-slate-600">
                  {history?.length || 0} Snapshot{history?.length !== 1 ? 's' : ''}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {(!history || history.length === 0) ? (
                <div className="p-8 text-center text-slate-400 text-sm">
                  No historical analysis snapshots recorded yet. Analyze a resume version to generate baseline snapshots.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm text-slate-600">
                    <thead className="bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500 font-semibold border-b border-slate-200">
                      <tr>
                        <th className="py-3 px-4">Version</th>
                        <th className="py-3 px-4">Analysis Date</th>
                        <th className="py-3 px-4">Quality Score</th>
                        <th className="py-3 px-4">ATS Compatibility</th>
                        <th className="py-3 px-4">Readability</th>
                        <th className="py-3 px-4">Strengths</th>
                        <th className="py-3 px-4">Weaknesses</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {history.map((s, idx) => (
                        <tr key={s.id || idx} className="hover:bg-slate-50/80 transition-colors">
                          <td className="py-3 px-4 font-semibold text-slate-900">
                            {s.version_name || `Version ${s.version_number}`}
                          </td>
                          <td className="py-3 px-4 text-xs text-slate-500">
                            {formatEventTimestamp(s.created_at)}
                          </td>
                          <td className="py-3 px-4 font-bold text-slate-900">
                            {s.overall_score !== null && s.overall_score !== undefined ? `${s.overall_score.toFixed(1)}/100` : '—'}
                          </td>
                          <td className="py-3 px-4">
                            {s.ats_score !== null && s.ats_score !== undefined ? `${s.ats_score.toFixed(1)}/100` : '—'}
                          </td>
                          <td className="py-3 px-4">
                            {s.readability_score !== null && s.readability_score !== undefined ? `${s.readability_score.toFixed(1)}/100` : '—'}
                          </td>
                          <td className="py-3 px-4 text-emerald-700 font-medium">
                            {s.strengths_count}
                          </td>
                          <td className="py-3 px-4 text-rose-700 font-medium">
                            {s.weaknesses_count}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB 2: ACTIONABLE IMPROVEMENT TASKS */}
      {activeTab === 'tasks' && (
        <Card className="border-slate-200 shadow-sm bg-white">
          <CardHeader className="border-b border-slate-100 pb-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <CardTitle className="text-base font-semibold text-slate-900 flex items-center gap-2">
                  <ListTodo className="w-4 h-4 text-teal-600" /> Actionable Improvement Tasks
                </CardTitle>
                <CardDescription className="text-xs text-slate-500 mt-0.5">
                  Action items derived directly from resume evaluations. Update task status to track your revision progress.
                </CardDescription>
              </div>

              {/* FILTER CONTROLS */}
              <div className="flex items-center gap-2 flex-wrap">
                <div className="flex items-center gap-1 text-xs text-slate-500">
                  <Filter className="w-3.5 h-3.5" />
                  <span>Status:</span>
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="border border-slate-300 rounded px-2 py-1 text-xs bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-teal-500"
                  >
                    <option value="All">All Statuses</option>
                    <option value="Pending">Pending</option>
                    <option value="In Progress">In Progress</option>
                    <option value="Completed">Completed</option>
                  </select>
                </div>

                <div className="flex items-center gap-1 text-xs text-slate-500">
                  <span>Priority:</span>
                  <select
                    value={priorityFilter}
                    onChange={(e) => setPriorityFilter(e.target.value)}
                    className="border border-slate-300 rounded px-2 py-1 text-xs bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-teal-500"
                  >
                    <option value="All">All Priorities</option>
                    <option value="High">High</option>
                    <option value="Medium">Medium</option>
                    <option value="Low">Low</option>
                  </select>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {(!filteredTasks || filteredTasks.length === 0) ? (
              <div className="p-8 text-center text-slate-400 text-sm">
                No improvement tasks match the selected filters.
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {filteredTasks.map((task) => {
                  const isUpdating = updatingTaskId === task.id;
                  const isDone = task.status === 'Completed';

                  return (
                    <div
                      key={task.id}
                      className={cn(
                        'p-4 sm:p-5 flex flex-col sm:flex-row sm:items-start justify-between gap-4 transition-colors',
                        isDone ? 'bg-slate-50/60' : 'hover:bg-slate-50/40'
                      )}
                    >
                      <div className="flex items-start gap-3 flex-1 min-w-0">
                        {/* Quick complete checkbox */}
                        <button
                          type="button"
                          disabled={isUpdating}
                          onClick={() => handleUpdateStatus(task.id, isDone ? 'Pending' : 'Completed')}
                          className={cn(
                            'mt-0.5 flex-shrink-0 w-5 h-5 rounded border flex items-center justify-center transition-colors',
                            isDone
                              ? 'bg-emerald-600 border-emerald-600 text-white'
                              : 'border-slate-300 hover:border-teal-600 bg-white'
                          )}
                          title={isDone ? 'Click to reopen task' : 'Click to mark as completed'}
                        >
                          {isDone && <Check className="w-3.5 h-3.5 stroke-[2.5]" />}
                        </button>

                        <div className="space-y-1 min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <span
                              className={cn(
                                'text-sm font-semibold',
                                isDone ? 'text-slate-500 line-through' : 'text-slate-900'
                              )}
                            >
                              {task.title}
                            </span>
                            <span className={cn('text-[10px] px-2 py-0.5 rounded-full border', getPriorityBadgeClass(task.priority))}>
                              {task.priority} Priority
                            </span>
                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
                              {task.section}
                            </span>
                          </div>

                          <p className="text-xs text-slate-600 leading-relaxed max-w-2xl">
                            {task.description}
                          </p>

                          <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400 pt-1">
                            <span>Created: {formatEventTimestamp(task.created_at)}</span>
                            {task.completed_at && (
                              <span className="text-emerald-600 font-medium">
                                Completed: {formatEventTimestamp(task.completed_at)}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Status selector */}
                      <div className="flex items-center gap-2 self-end sm:self-start shrink-0">
                        <select
                          disabled={isUpdating}
                          value={task.status}
                          onChange={(e) => handleUpdateStatus(task.id, e.target.value)}
                          className={cn(
                            'text-xs font-semibold px-2.5 py-1.5 rounded-lg border focus:outline-none transition-colors',
                            getStatusBadgeClass(task.status)
                          )}
                        >
                          <option value="Pending">Pending</option>
                          <option value="In Progress">In Progress</option>
                          <option value="Completed">Completed</option>
                        </select>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* TAB 3: CHRONOLOGICAL TIMELINE */}
      {activeTab === 'timeline' && (
        <Card className="border-slate-200 shadow-sm bg-white">
          <CardHeader className="border-b border-slate-100 pb-3">
            <CardTitle className="text-base font-semibold text-slate-900 flex items-center gap-2">
              <Milestone className="w-4 h-4 text-teal-600" /> Improvement & Revision Timeline
            </CardTitle>
            <CardDescription className="text-xs text-slate-500 mt-0.5">
              Chronological log of document uploads, automated evaluations, task milestones, and revisions with real event timestamps.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6">
            {(!timeline || timeline.length === 0) ? (
              <div className="p-8 text-center text-slate-400 text-sm">
                No timeline events recorded yet.
              </div>
            ) : (
              <div className="relative border-l-2 border-slate-200 ml-4 space-y-6 py-2">
                {timeline.map((evt) => {
                  let icon = <FileText className="w-4 h-4 text-slate-600" />;
                  let dotBg = 'bg-slate-100 border-slate-300';

                  if (evt.event_type === 'RESUME_UPLOADED' || evt.event_type === 'VERSION_UPLOADED') {
                    icon = <Layers className="w-4 h-4 text-indigo-600" />;
                    dotBg = 'bg-indigo-50 border-indigo-300';
                  } else if (evt.event_type === 'RESUME_ANALYZED' || evt.event_type === 'VERSION_ANALYZED') {
                    icon = <Sparkles className="w-4 h-4 text-teal-600" />;
                    dotBg = 'bg-teal-50 border-teal-300';
                  } else if (evt.event_type === 'TASK_COMPLETED') {
                    icon = <CheckCircle2 className="w-4 h-4 text-emerald-600" />;
                    dotBg = 'bg-emerald-50 border-emerald-300';
                  } else if (evt.event_type === 'TASK_REOPENED') {
                    icon = <RotateCcw className="w-4 h-4 text-amber-600" />;
                    dotBg = 'bg-amber-50 border-amber-300';
                  }

                  return (
                    <div key={evt.id} className="relative pl-6">
                      <div
                        className={cn(
                          'absolute -left-[17px] top-0.5 w-8 h-8 rounded-full border flex items-center justify-center bg-white shadow-xs',
                          dotBg
                        )}
                      >
                        {icon}
                      </div>

                      <div className="space-y-1">
                        <div className="flex flex-wrap items-baseline gap-2">
                          <span className="text-sm font-semibold text-slate-900">{evt.title}</span>
                          <span className="text-[11px] text-slate-400">
                            {formatEventTimestamp(evt.created_at)}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600">{evt.description}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* TAB 4: VERSION COMPARISON INTERFACE */}
      {activeTab === 'compare' && (
        <div className="space-y-6">
          <Card className="border-slate-200 shadow-sm bg-white">
            <CardHeader className="border-b border-slate-100 pb-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <CardTitle className="text-base font-semibold text-slate-900 flex items-center gap-2">
                    <GitCompare className="w-4 h-4 text-teal-600" /> Resume Version Comparison
                  </CardTitle>
                  <CardDescription className="text-xs text-slate-500 mt-0.5">
                    Compare two resume versions side-by-side to inspect objective content differences and score changes.
                  </CardDescription>
                </div>

                {/* VERSION PICKERS */}
                <div className="flex items-center gap-2 flex-wrap">
                  <div className="flex items-center gap-1.5 text-xs text-slate-600">
                    <span>Base Version:</span>
                    <select
                      value={v1Select}
                      onChange={(e) => setV1Select(e.target.value)}
                      className="border border-slate-300 rounded px-2 py-1 text-xs bg-white text-slate-700 focus:outline-none"
                    >
                      {available_versions?.map((v) => (
                        <option key={v.version_number} value={v.version_number}>
                          {v.version_name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <span className="text-slate-400 font-bold text-xs">vs</span>

                  <div className="flex items-center gap-1.5 text-xs text-slate-600">
                    <span>Comparison Version:</span>
                    <select
                      value={v2Select}
                      onChange={(e) => setV2Select(e.target.value)}
                      className="border border-slate-300 rounded px-2 py-1 text-xs bg-white text-slate-700 focus:outline-none"
                    >
                      {available_versions?.map((v) => (
                        <option key={v.version_number} value={v.version_number}>
                          {v.version_name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <Button
                    size="sm"
                    disabled={isComparing}
                    onClick={handleRunComparison}
                    className="text-xs flex items-center gap-1 bg-teal-600 hover:bg-teal-700 text-white"
                  >
                    <GitCompare className="w-3.5 h-3.5" />
                    {isComparing ? 'Comparing...' : 'Compare'}
                  </Button>
                </div>
              </div>
            </CardHeader>

            <CardContent className="p-6">
              {comparisonError && (
                <Alert variant="error" className="mb-4">
                  {comparisonError}
                </Alert>
              )}

              {isComparing && (
                <div className="py-8 text-center">
                  <LoadingIndicator size="md" text="Comparing versions..." />
                </div>
              )}

              {comparisonData && !isComparing && (
                <div className="space-y-6">
                  {/* METADATA COMPARISON CARDS */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Version 1 */}
                    <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/60 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-bold text-slate-900">
                          {comparisonData.version_1.version_name} (Base)
                        </span>
                        <Badge variant="outline" className="text-[11px] bg-white">
                          {comparisonData.version_1.word_count} words
                        </Badge>
                      </div>
                      <div className="text-xs text-slate-500 space-y-0.5">
                        <p>Uploaded: {formatEventTimestamp(comparisonData.version_1.upload_date)}</p>
                        <p>
                          Analyzed:{' '}
                          {comparisonData.version_1.analysis_date
                            ? formatEventTimestamp(comparisonData.version_1.analysis_date)
                            : 'Not Evaluated'}
                        </p>
                      </div>
                    </div>

                    {/* Version 2 */}
                    <div className="p-4 rounded-xl border border-teal-200 bg-teal-50/30 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-bold text-teal-900">
                          {comparisonData.version_2.version_name} (Revision)
                        </span>
                        <Badge variant="outline" className="text-[11px] bg-white border-teal-300 text-teal-800">
                          {comparisonData.version_2.word_count} words
                        </Badge>
                      </div>
                      <div className="text-xs text-slate-500 space-y-0.5">
                        <p>Uploaded: {formatEventTimestamp(comparisonData.version_2.upload_date)}</p>
                        <p>
                          Analyzed:{' '}
                          {comparisonData.version_2.analysis_date
                            ? formatEventTimestamp(comparisonData.version_2.analysis_date)
                            : 'Not Evaluated'}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* SCORE COMPARISON ACROSS VERSIONS */}
                  <div className="p-4 rounded-xl border border-slate-200 bg-white">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
                      Score Deltas Across Versions
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <div className="p-3 rounded-lg border border-slate-100 bg-slate-50">
                        <span className="text-xs text-slate-500">Overall Quality</span>
                        <div className="mt-1 flex items-center justify-between">
                          <span className="text-base font-bold text-slate-900">
                            {comparisonData.score_comparison?.overall_score?.latest_score !== null
                              ? `${comparisonData.score_comparison.overall_score.latest_score.toFixed(1)}/100`
                              : '—'}
                          </span>
                          {renderScoreDeltaBadge(comparisonData.score_comparison?.overall_score)}
                        </div>
                      </div>

                      <div className="p-3 rounded-lg border border-slate-100 bg-slate-50">
                        <span className="text-xs text-slate-500">ATS Compatibility</span>
                        <div className="mt-1 flex items-center justify-between">
                          <span className="text-base font-bold text-slate-900">
                            {comparisonData.score_comparison?.ats_compatibility?.latest_score !== null
                              ? `${comparisonData.score_comparison.ats_compatibility.latest_score.toFixed(1)}/100`
                              : '—'}
                          </span>
                          {renderScoreDeltaBadge(comparisonData.score_comparison?.ats_compatibility)}
                        </div>
                      </div>

                      <div className="p-3 rounded-lg border border-slate-100 bg-slate-50">
                        <span className="text-xs text-slate-500">Readability</span>
                        <div className="mt-1 flex items-center justify-between">
                          <span className="text-base font-bold text-slate-900">
                            {comparisonData.score_comparison?.readability?.latest_score !== null
                              ? `${comparisonData.score_comparison.readability.latest_score.toFixed(1)}/100`
                              : '—'}
                          </span>
                          {renderScoreDeltaBadge(comparisonData.score_comparison?.readability)}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* SKILLS COMPARISON */}
                  <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-4">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                      Skills Detected Across Versions
                    </h4>

                    {/* Added skills */}
                    {comparisonData.skills_comparison?.added_skills?.length > 0 && (
                      <div>
                        <span className="text-xs font-semibold text-emerald-700 flex items-center gap-1 mb-1.5">
                          <ArrowUpRight className="w-3.5 h-3.5" /> Added Skills ({comparisonData.skills_comparison.added_skills.length})
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {comparisonData.skills_comparison.added_skills.map((s, idx) => (
                            <span
                              key={idx}
                              className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-800 border border-emerald-200"
                            >
                              + {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Removed skills */}
                    {comparisonData.skills_comparison?.removed_skills?.length > 0 && (
                      <div>
                        <span className="text-xs font-semibold text-rose-700 flex items-center gap-1 mb-1.5">
                          <ArrowDownRight className="w-3.5 h-3.5" /> Removed Skills ({comparisonData.skills_comparison.removed_skills.length})
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {comparisonData.skills_comparison.removed_skills.map((s, idx) => (
                            <span
                              key={idx}
                              className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-50 text-rose-800 border border-rose-200"
                            >
                              - {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Retained skills */}
                    {comparisonData.skills_comparison?.retained_skills?.length > 0 && (
                      <div>
                        <span className="text-xs font-semibold text-slate-600 mb-1.5 block">
                          Retained Skills ({comparisonData.skills_comparison.retained_skills.length})
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {comparisonData.skills_comparison.retained_skills.map((s, idx) => (
                            <span
                              key={idx}
                              className="px-2.5 py-0.5 rounded-full text-xs bg-slate-100 text-slate-700 border border-slate-200"
                            >
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* CONTENT CHANGE SUMMARY */}
                  <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 text-xs text-slate-700 space-y-1">
                    <span className="font-semibold text-slate-900 block">Objective Content Summary</span>
                    <p>{comparisonData.content_changes?.summary}</p>
                    {comparisonData.notes?.map((n, idx) => (
                      <p key={idx} className="text-slate-500 italic pt-1">
                        Note: {n}
                      </p>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

export default ResumeImprovementTracker;
