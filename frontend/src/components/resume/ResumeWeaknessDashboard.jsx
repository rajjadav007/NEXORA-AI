import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  AlertTriangle,
  Sparkles,
  RefreshCw,
  Code2,
  FolderGit2,
  Briefcase,
  GraduationCap,
  Trophy,
  FileText,
  CheckCircle2,
  HelpCircle,
  Lightbulb,
  Quote,
  ShieldAlert,
  Search,
  Filter,
  ArrowUpRight,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert } from '../ui/alert';
import { LoadingIndicator } from '../ui/loading-indicator';
import { getResumeWeaknesses, analyzeResumeWeaknesses } from '../../services/weaknessService';
import { cn } from '../../utils/cn';

const CATEGORY_TABS = [
  { key: 'all', label: 'All Weaknesses', icon: ShieldAlert },
  { key: 'technical_skills', label: 'Skills', icon: Code2 },
  { key: 'projects', label: 'Projects', icon: FolderGit2 },
  { key: 'experience', label: 'Experience', icon: Briefcase },
  { key: 'education', label: 'Education', icon: GraduationCap },
  { key: 'achievements', label: 'Achievements', icon: Trophy },
  { key: 'summary', label: 'Summary', icon: FileText },
  { key: 'clarity_relevance', label: 'Clarity & Flow', icon: Sparkles },
  { key: 'missing_info', label: 'Missing Info', icon: HelpCircle },
];

function getPriorityBadgeClass(priority) {
  const p = (priority || '').toLowerCase();
  switch (p) {
    case 'critical':
      return 'bg-rose-100 text-rose-800 border-rose-300 font-semibold';
    case 'high':
      return 'bg-amber-100 text-amber-800 border-amber-300 font-semibold';
    case 'medium':
      return 'bg-blue-100 text-blue-800 border-blue-300 font-medium';
    case 'low':
      return 'bg-slate-100 text-slate-700 border-slate-300 font-normal';
    default:
      return 'bg-slate-100 text-slate-700 border-slate-300';
  }
}

function getWeaknessTypeBadge(type) {
  switch (type) {
    case 'lacks_measurable_impact':
      return { label: 'Lacks Metrics', bg: 'bg-orange-50 text-orange-700 border-orange-200' };
    case 'vague_description':
      return { label: 'Vague Phrasing', bg: 'bg-purple-50 text-purple-700 border-purple-200' };
    case 'content_gap':
      return { label: 'Content Gap', bg: 'bg-blue-50 text-blue-700 border-blue-200' };
    case 'formatting_structure':
      return { label: 'Structure', bg: 'bg-gray-50 text-gray-700 border-gray-200' };
    case 'clarity_issue':
      return { label: 'Clarity & Buzzword', bg: 'bg-amber-50 text-amber-700 border-amber-200' };
    default:
      return { label: 'Improvement Area', bg: 'bg-slate-50 text-slate-700 border-slate-200' };
  }
}

/**
 * ResumeWeaknessDashboard Component
 * Phase 4 | Feature #23: Resume Weakness Analysis
 */
export function ResumeWeaknessDashboard({ resumeId, className }) {
  const [weaknessData, setWeaknessData] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedPriority, setSelectedPriority] = useState('all');
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null);

  const fetchWeaknesses = useCallback(async () => {
    if (!resumeId) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await getResumeWeaknesses(resumeId);
      if (response && response.data) {
        setWeaknessData(response.data);
      }
    } catch (err) {
      if (err.status !== 404) {
        setError(err.message || 'Failed to load weakness analysis.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [resumeId]);

  useEffect(() => {
    fetchWeaknesses();
  }, [fetchWeaknesses]);

  const handleAnalyze = async (force = false) => {
    if (!resumeId || isAnalyzing) return;
    setIsAnalyzing(true);
    setError(null);
    try {
      const response = await analyzeResumeWeaknesses(resumeId, { forceRecalculate: force });
      if (response && response.data) {
        setWeaknessData(response.data);
      }
    } catch (err) {
      setError(err.message || 'Resume weakness evaluation failed.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const filteredWeaknesses = useMemo(() => {
    if (!weaknessData || !weaknessData.weaknesses) return [];
    return weaknessData.weaknesses.filter((w) => {
      const matchesCategory =
        selectedCategory === 'all' || selectedCategory === 'missing_info' || w.category === selectedCategory;
      const matchesPriority =
        selectedPriority === 'all' || w.priority.toLowerCase() === selectedPriority.toLowerCase();
      return matchesCategory && matchesPriority;
    });
  }, [weaknessData, selectedCategory, selectedPriority]);

  // 1. LOADING STATE
  if (isLoading) {
    return (
      <Card className={cn('p-8 text-center space-y-4 border-slate-200 shadow-sm', className)}>
        <LoadingIndicator size="lg" className="text-amber-600 mx-auto" />
        <div className="space-y-1">
          <h3 className="text-base font-bold text-slate-800">
            Evaluating Resume Weaknesses & Gaps...
          </h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Scanning for vague descriptions, missing metrics, buzzwords, and actionable areas of improvement.
          </p>
        </div>
      </Card>
    );
  }

  // 2. ERROR STATE (only when not 404)
  if (error && !weaknessData) {
    return (
      <Card className={cn('p-6 border-red-200 bg-red-50/40 shadow-sm space-y-4', className)}>
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="text-sm font-bold text-red-900">Weakness Analysis Unavailable</h4>
            <p className="text-xs text-red-700">{error}</p>
          </div>
        </div>
        <div className="flex justify-end gap-2">
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
              'Retry Analysis'
            )}
          </Button>
        </div>
      </Card>
    );
  }

  // 3. EMPTY STATE (Never analyzed)
  if (!weaknessData) {
    return (
      <Card className={cn('p-8 border-dashed border-2 border-slate-200 text-center space-y-4 shadow-sm', className)}>
        <div className="w-12 h-12 bg-amber-50 rounded-full flex items-center justify-center mx-auto text-amber-600 border border-amber-100">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <div className="space-y-1.5 max-w-md mx-auto">
          <h3 className="text-base font-bold text-slate-900">
            Resume Weakness & Gap Analysis
          </h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            Run an AI audit to detect vague statements, missing quantitative metrics, unoptimized skill lists, and missing information before recruiters see your resume.
          </p>
        </div>
        <Button
          onClick={() => handleAnalyze(false)}
          disabled={isAnalyzing}
          className="bg-amber-600 hover:bg-amber-700 text-white text-xs h-9 px-4 font-semibold shadow-sm"
        >
          {isAnalyzing ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin mr-2" />
              Analyzing Weaknesses...
            </>
          ) : (
            <>
              <AlertTriangle className="w-3.5 h-3.5 mr-2" />
              Analyze Resume Weaknesses
            </>
          )}
        </Button>
      </Card>
    );
  }

  const {
    total_weaknesses_count = 0,
    priority_breakdown = { critical: 0, high: 0, medium: 0, low: 0 },
    overall_summary = '',
    weaknesses = [],
    missing_information = [],
    category_summaries = {},
  } = weaknessData;

  const activeCategorySummary =
    selectedCategory !== 'all' && selectedCategory !== 'missing_info'
      ? category_summaries[selectedCategory]
      : null;

  return (
    <Card className={cn('border-slate-200 shadow-sm overflow-hidden', className)}>
      {/* Header */}
      <CardHeader className="bg-slate-50/50 border-b border-slate-100 pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-amber-100 text-amber-800 border border-amber-200">
                <AlertTriangle className="w-4 h-4" />
              </div>
              <CardTitle className="text-base sm:text-lg font-bold text-slate-900">
                Resume Weakness & Gap Analysis
              </CardTitle>
            </div>
            <CardDescription className="text-xs text-slate-500">
              Pinpoints vague claims, missing metrics, and prioritized improvements across 7 dimensions.
            </CardDescription>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleAnalyze(true)}
              disabled={isAnalyzing}
              className="text-xs h-8 gap-1.5 border-slate-200 text-slate-700 hover:bg-white hover:text-slate-900"
              title="Force AI re-evaluation of weaknesses"
            >
              <RefreshCw className={cn('w-3.5 h-3.5', isAnalyzing && 'animate-spin')} />
              <span>{isAnalyzing ? 'Re-evaluating...' : 'Re-analyze'}</span>
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
        {/* Executive Overview Banner */}
        {overall_summary && (
          <div className="p-4 rounded-xl bg-amber-50/60 border border-amber-200/80 space-y-2">
            <div className="flex items-center gap-2 text-amber-900 font-semibold text-xs tracking-wide uppercase">
              <Lightbulb className="w-4 h-4 text-amber-700" />
              Executive Audit Summary
            </div>
            <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-medium">
              {overall_summary}
            </p>
          </div>
        )}

        {/* Priority-Wise Metrics Breakdown */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <div className="p-3 bg-white border border-slate-200 rounded-xl space-y-1">
            <span className="text-[10px] font-bold text-slate-400 block uppercase tracking-wider">
              Total Weaknesses
            </span>
            <div className="flex items-baseline gap-1.5">
              <span className="text-xl font-extrabold text-slate-900">{total_weaknesses_count}</span>
              <span className="text-[11px] text-slate-500">identified</span>
            </div>
          </div>

          <div
            onClick={() => setSelectedPriority((prev) => (prev === 'critical' ? 'all' : 'critical'))}
            className={cn(
              'p-3 rounded-xl border cursor-pointer transition-all space-y-1',
              selectedPriority === 'critical'
                ? 'bg-rose-100 border-rose-400 shadow-sm ring-1 ring-rose-400'
                : 'bg-rose-50/50 border-rose-200 hover:bg-rose-50'
            )}
            title="Filter by Critical Priority"
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-rose-700 uppercase tracking-wider">Critical</span>
              <span className="w-2 h-2 rounded-full bg-rose-500" />
            </div>
            <span className="text-xl font-extrabold text-rose-900">{priority_breakdown.critical}</span>
          </div>

          <div
            onClick={() => setSelectedPriority((prev) => (prev === 'high' ? 'all' : 'high'))}
            className={cn(
              'p-3 rounded-xl border cursor-pointer transition-all space-y-1',
              selectedPriority === 'high'
                ? 'bg-amber-100 border-amber-400 shadow-sm ring-1 ring-amber-400'
                : 'bg-amber-50/50 border-amber-200 hover:bg-amber-50'
            )}
            title="Filter by High Priority"
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-amber-700 uppercase tracking-wider">High</span>
              <span className="w-2 h-2 rounded-full bg-amber-500" />
            </div>
            <span className="text-xl font-extrabold text-amber-900">{priority_breakdown.high}</span>
          </div>

          <div
            onClick={() => setSelectedPriority((prev) => (prev === 'medium' ? 'all' : 'medium'))}
            className={cn(
              'p-3 rounded-xl border cursor-pointer transition-all space-y-1',
              selectedPriority === 'medium'
                ? 'bg-blue-100 border-blue-400 shadow-sm ring-1 ring-blue-400'
                : 'bg-blue-50/50 border-blue-200 hover:bg-blue-50'
            )}
            title="Filter by Medium Priority"
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-blue-700 uppercase tracking-wider">Medium</span>
              <span className="w-2 h-2 rounded-full bg-blue-500" />
            </div>
            <span className="text-xl font-extrabold text-blue-900">{priority_breakdown.medium}</span>
          </div>

          <div
            onClick={() => setSelectedPriority((prev) => (prev === 'low' ? 'all' : 'low'))}
            className={cn(
              'p-3 rounded-xl border cursor-pointer transition-all space-y-1',
              selectedPriority === 'low'
                ? 'bg-slate-200 border-slate-400 shadow-sm ring-1 ring-slate-400'
                : 'bg-slate-50 border-slate-200 hover:bg-slate-100'
            )}
            title="Filter by Low Priority"
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-slate-600 uppercase tracking-wider">Low</span>
              <span className="w-2 h-2 rounded-full bg-slate-400" />
            </div>
            <span className="text-xl font-extrabold text-slate-800">{priority_breakdown.low}</span>
          </div>
        </div>

        {/* Category Tabs */}
        <div className="border-b border-slate-200 pb-1 flex items-center gap-1.5 overflow-x-auto scrollbar-none">
          {CATEGORY_TABS.map((tab) => {
            const Icon = tab.icon;
            const isSelected = selectedCategory === tab.key;
            const count =
              tab.key === 'all'
                ? total_weaknesses_count
                : tab.key === 'missing_info'
                ? missing_information.length
                : (category_summaries[tab.key]?.total_weaknesses || 0);

            return (
              <button
                key={tab.key}
                type="button"
                onClick={() => setSelectedCategory(tab.key)}
                className={cn(
                  'px-3 py-2 text-xs font-semibold rounded-lg flex items-center gap-1.5 whitespace-nowrap transition-colors',
                  isSelected
                    ? 'bg-slate-900 text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                )}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
                <span
                  className={cn(
                    'text-[10px] px-1.5 py-0.2 rounded-full font-mono',
                    isSelected ? 'bg-slate-800 text-slate-200' : 'bg-slate-200/70 text-slate-700'
                  )}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Category Specific Recommendation */}
        {activeCategorySummary && (
          <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg flex items-start gap-2.5">
            <Lightbulb className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
            <div className="space-y-0.5">
              <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider">
                {activeCategorySummary.category_name} Recommendation
              </span>
              <p className="text-xs text-slate-600">{activeCategorySummary.key_recommendation}</p>
            </div>
          </div>
        )}

        {/* Missing Information Panel (Separate from weaknesses) */}
        {selectedCategory === 'missing_info' ? (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-blue-50/60 border border-blue-200 space-y-1">
              <div className="flex items-center gap-2 text-blue-900 font-semibold text-xs tracking-wide uppercase">
                <HelpCircle className="w-4 h-4 text-blue-700" />
                Missing Resume Details
              </div>
              <p className="text-xs text-slate-600">
                Missing sections are identified separately from content flaws. Note that some details (such as certifications or GPA) may be optional depending on your experience level and industry.
              </p>
            </div>

            {missing_information.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500 border border-dashed rounded-xl">
                No missing sections detected. Your resume structure covers standard expected sections.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {missing_information.map((m, idx) => (
                  <div
                    key={idx}
                    className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs space-y-2.5"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-0.5">
                        <Badge variant="outline" className="text-[10px] bg-slate-50 text-slate-700">
                          {m.section}
                        </Badge>
                        <h5 className="text-xs font-bold text-slate-900">{m.item}</h5>
                      </div>
                      <Badge
                        variant="outline"
                        className={cn(
                          'text-[10px] shrink-0',
                          m.is_optional
                            ? 'bg-slate-100 text-slate-600 border-slate-200'
                            : 'bg-rose-50 text-rose-700 border-rose-200 font-bold'
                        )}
                      >
                        {m.is_optional ? 'Optional' : 'Recommended'}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-600 leading-relaxed">{m.relevance}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          /* List of Weaknesses */
          <div className="space-y-4">
            {filteredWeaknesses.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500 border border-dashed rounded-xl space-y-2">
                <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
                <p className="font-semibold text-slate-700">No weaknesses found in this filter.</p>
                <p className="text-slate-400">
                  {selectedPriority !== 'all'
                    ? `No weaknesses with ${selectedPriority} priority.`
                    : 'This section meets key quality standards.'}
                </p>
              </div>
            ) : (
              filteredWeaknesses.map((item, idx) => {
                const typeInfo = getWeaknessTypeBadge(item.weakness_type);
                return (
                  <div
                    key={idx}
                    className="p-4 sm:p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-3.5 hover:border-slate-300 transition-colors"
                  >
                    {/* Weakness Header */}
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
                      <div className="space-y-1">
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span className="text-[11px] font-mono font-bold text-slate-400">
                            #{item.relevance_rank}
                          </span>
                          <Badge
                            variant="outline"
                            className={cn('text-[10px] uppercase font-bold', getPriorityBadgeClass(item.priority))}
                          >
                            {item.priority}
                          </Badge>
                          <Badge
                            variant="outline"
                            className={cn('text-[10px] border', typeInfo.bg)}
                          >
                            {typeInfo.label}
                          </Badge>
                          <Badge variant="outline" className="text-[10px] text-slate-600 bg-slate-50">
                            {item.category_name}
                          </Badge>
                        </div>
                        <h4 className="text-sm sm:text-base font-bold text-slate-900">
                          {item.title}
                        </h4>
                      </div>
                    </div>

                    {/* Detailed Explanation */}
                    <p className="text-xs sm:text-sm text-slate-700 leading-relaxed">
                      {item.explanation}
                    </p>

                    {/* Supporting Evidence */}
                    {item.evidence && item.evidence.length > 0 && (
                      <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 space-y-1.5">
                        <div className="flex items-center gap-1.5 text-slate-500 font-semibold text-[11px]">
                          <Quote className="w-3.5 h-3.5" />
                          <span>Supporting Evidence from Resume:</span>
                        </div>
                        <ul className="list-disc list-inside space-y-1 text-xs text-slate-700 font-mono">
                          {item.evidence.map((ev, eIdx) => (
                            <li key={eIdx} className="break-words">
                              <span className="text-slate-800 bg-slate-200/60 px-1 py-0.5 rounded">
                                {ev}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Why it Matters & Suggested Improvement Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                      {/* Why it matters */}
                      <div className="p-3 rounded-lg bg-amber-50/40 border border-amber-200/60 space-y-1">
                        <span className="text-[10px] font-bold text-amber-800 uppercase tracking-wider block">
                          Why It Matters
                        </span>
                        <p className="text-xs text-slate-700 leading-relaxed">
                          {item.why_it_matters}
                        </p>
                      </div>

                      {/* Suggested improvement */}
                      <div className="p-3 rounded-lg bg-emerald-50/40 border border-emerald-200/60 space-y-1">
                        <div className="flex items-center gap-1 text-[10px] font-bold text-emerald-800 uppercase tracking-wider">
                          <Lightbulb className="w-3 h-3 text-emerald-600" />
                          <span>Suggested Improvement</span>
                        </div>
                        <p className="text-xs text-slate-700 leading-relaxed font-medium">
                          {item.suggested_improvement}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
