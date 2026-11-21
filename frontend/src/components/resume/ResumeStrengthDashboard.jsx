import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Zap,
  Sparkles,
  CheckCircle2,
  Compass,
  AlertTriangle,
  RefreshCw,
  Code2,
  FolderGit2,
  Briefcase,
  GraduationCap,
  Trophy,
  Users2,
  MessageSquare,
  ShieldCheck,
  TrendingUp,
  Quote,
  Lightbulb,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert } from '../ui/alert';
import { LoadingIndicator } from '../ui/loading-indicator';
import { getResumeStrengths, analyzeResumeStrengths } from '../../services/strengthService';
import { cn } from '../../utils/cn';

const CATEGORY_TABS = [
  { key: 'all', label: 'All Strengths', icon: Zap },
  { key: 'technical_skills', label: 'Technical Skills', icon: Code2 },
  { key: 'projects', label: 'Projects', icon: FolderGit2 },
  { key: 'experience', label: 'Experience', icon: Briefcase },
  { key: 'education', label: 'Education', icon: GraduationCap },
  { key: 'achievements', label: 'Achievements', icon: Trophy },
  { key: 'leadership', label: 'Leadership & Teamwork', icon: Users2 },
  { key: 'communication', label: 'Communication & Problem-Solving', icon: MessageSquare },
];

function getCategoryIcon(catKey) {
  const match = CATEGORY_TABS.find((t) => t.key === catKey);
  return match ? match.icon : Zap;
}

function getConfidenceBadgeClass(confidence) {
  const c = (confidence || '').toLowerCase();
  if (c === 'high') {
    return 'bg-emerald-100 text-emerald-800 border-emerald-300';
  }
  if (c === 'medium') {
    return 'bg-blue-100 text-blue-800 border-blue-300';
  }
  return 'bg-slate-100 text-slate-700 border-slate-300';
}

/**
 * ResumeStrengthDashboard Component
 * Phase 4 | Feature #22: Resume Strength Analysis
 */
export function ResumeStrengthDashboard({ resumeId, className }) {
  const [strengthData, setStrengthData] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null);

  const fetchStrengths = useCallback(async () => {
    if (!resumeId) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await getResumeStrengths(resumeId);
      if (response && response.data) {
        setStrengthData(response.data);
      }
    } catch (err) {
      if (err.status !== 404) {
        setError(err.message || 'Failed to load strength analysis.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [resumeId]);

  useEffect(() => {
    fetchStrengths();
  }, [fetchStrengths]);

  const handleAnalyze = async (force = false) => {
    if (!resumeId || isAnalyzing) return;
    setIsAnalyzing(true);
    setError(null);
    try {
      const response = await analyzeResumeStrengths(resumeId, { forceRecalculate: force });
      if (response && response.data) {
        setStrengthData(response.data);
      }
    } catch (err) {
      setError(err.message || 'Resume strength evaluation failed.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const filteredStrengths = useMemo(() => {
    if (!strengthData || !strengthData.strengths) return [];
    if (selectedCategory === 'all') return strengthData.strengths;
    return strengthData.strengths.filter((s) => s.category === selectedCategory);
  }, [strengthData, selectedCategory]);

  // 1. INITIAL LOADING STATE
  if (isLoading && !strengthData) {
    return (
      <Card className={cn('p-8 border-slate-200 shadow-sm text-center space-y-3', className)}>
        <LoadingIndicator size="md" className="text-teal-600 mx-auto" />
        <p className="text-xs text-slate-500 font-medium">Loading Candidate Strengths...</p>
      </Card>
    );
  }

  // 2. NOT YET ANALYZED STATE
  if (!strengthData && !isLoading) {
    return (
      <Card className={cn('border-teal-100 bg-gradient-to-br from-teal-50/40 via-white to-slate-50 shadow-sm overflow-hidden', className)}>
        <CardHeader className="pb-4 border-b border-teal-100/60">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-teal-600 text-white flex items-center justify-center shadow-xs">
                <Zap className="w-5 h-5" />
              </div>
              <div>
                <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                  Resume Strength Analysis
                  <Badge variant="outline" className="text-[10px] bg-teal-50 border-teal-200 text-teal-800">
                    Phase 4 • Feature 22
                  </Badge>
                </CardTitle>
                <CardDescription className="text-xs text-slate-500">
                  Discover verified demonstrated and potential strengths grounded in your structured resume data.
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
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Evaluating Strengths...
                </>
              ) : (
                <>
                  <Zap className="w-3.5 h-3.5" /> Analyze Strengths
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
            Click <strong>Analyze Strengths</strong> to extract your strongest skills, quantified outcomes, projects, leadership evidence, and professional market differentiators without any fabricated claims.
          </p>
        </CardContent>
      </Card>
    );
  }

  // 3. FULL STRENGTH DASHBOARD STATE
  const totalCount = strengthData.total_strengths_count || 0;
  const demonstratedCount = strengthData.demonstrated_count || 0;
  const potentialCount = strengthData.potential_count || 0;

  return (
    <Card className={cn('border-slate-200 shadow-sm overflow-hidden bg-white', className)}>
      {/* Header with Metrics and Actions */}
      <CardHeader className="bg-slate-50/70 border-b border-slate-200/80 pb-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-teal-600 text-white flex items-center justify-center shadow-sm">
              <Zap className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <CardTitle className="text-base font-bold text-slate-900">
                  Candidate Strength Intelligence
                </CardTitle>
                <Badge variant="outline" className="text-[11px] font-bold bg-teal-50 text-teal-800 border-teal-200">
                  Feature 22
                </Badge>
              </div>
              <CardDescription className="text-xs text-slate-500">
                Evidence-backed strengths categorized, ranked by relevance, and evaluated for hiring value.
              </CardDescription>
            </div>
          </div>

          <div className="flex items-center gap-2.5 self-end sm:self-auto flex-wrap">
            <div className="flex items-center gap-1.5 px-3 py-1 bg-white border border-slate-200 rounded-lg text-center shadow-xs">
              <span className="text-[10px] font-bold text-slate-400 uppercase">Total</span>
              <span className="text-xs font-black text-slate-800 font-mono">{totalCount}</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1 bg-emerald-50 border border-emerald-200 rounded-lg text-center shadow-xs text-emerald-800">
              <CheckCircle2 className="w-3 h-3 text-emerald-600 shrink-0" />
              <span className="text-[10px] font-bold uppercase">Demonstrated</span>
              <span className="text-xs font-black font-mono">{demonstratedCount}</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1 bg-purple-50 border border-purple-200 rounded-lg text-center shadow-xs text-purple-800">
              <Compass className="w-3 h-3 text-purple-600 shrink-0" />
              <span className="text-[10px] font-bold uppercase">Potential</span>
              <span className="text-xs font-black font-mono">{potentialCount}</span>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => handleAnalyze(true)}
              disabled={isAnalyzing}
              className="text-xs h-8 border-slate-300 text-slate-700 hover:bg-slate-100 flex items-center gap-1.5 shrink-0"
              title="Re-run strength analysis"
            >
              <RefreshCw className={cn('w-3 h-3', isAnalyzing && 'animate-spin')} />
              <span>{isAnalyzing ? 'Analyzing...' : 'Re-analyze'}</span>
            </Button>
          </div>
        </div>

        {error && (
          <Alert variant="destructive" className="mt-3 border-red-200 text-xs">
            <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
            <div className="space-y-0.5">
              <p className="font-semibold text-red-900">Analysis Error</p>
              <p className="text-red-700">{error}</p>
            </div>
          </Alert>
        )}
      </CardHeader>

      <CardContent className="p-6 space-y-6">
        {/* Executive Summary */}
        {strengthData.top_strengths_summary && (
          <div className="p-4 rounded-xl border border-teal-200 bg-teal-50/50 space-y-1.5">
            <div className="flex items-center gap-1.5 text-teal-900 font-bold text-xs uppercase tracking-wider">
              <Sparkles className="w-4 h-4 text-teal-600" />
              <span>Executive Strength Profile</span>
            </div>
            <p className="text-xs text-slate-700 leading-relaxed">
              {strengthData.top_strengths_summary}
            </p>
          </div>
        )}

        {/* Insufficient Evidence Alert Banner */}
        {!strengthData.is_sufficient_evidence && (
          <div className="p-4 rounded-xl border border-amber-200 bg-amber-50/60 space-y-2">
            <div className="flex items-center gap-2 text-amber-900 font-bold text-xs uppercase tracking-wider">
              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
              <span>Insufficient Evidence Notice</span>
            </div>
            <p className="text-xs text-amber-950 leading-relaxed">
              {strengthData.insufficient_evidence_reason ||
                'This resume does not currently provide enough descriptive work achievements, project outcomes, or quantified metrics to extract verified professional strengths.'}
            </p>
          </div>
        )}

        {/* Category Filter Pills */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Filter by Strength Category
            </span>
            <span className="text-[11px] text-slate-400">
              Showing {filteredStrengths.length} of {totalCount} strengths
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-1.5 pb-1">
            {CATEGORY_TABS.map((tab) => {
              const TabIcon = tab.icon;
              const isActive = selectedCategory === tab.key;
              const catSummary = strengthData.category_summaries?.[tab.key];
              const badgeCount =
                tab.key === 'all' ? totalCount : catSummary?.total_strengths || 0;

              return (
                <button
                  key={tab.key}
                  type="button"
                  onClick={() => setSelectedCategory(tab.key)}
                  className={cn(
                    'px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all border',
                    isActive
                      ? 'bg-teal-600 text-white border-teal-600 shadow-xs'
                      : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300 hover:text-slate-900'
                  )}
                >
                  <TabIcon className="w-3.5 h-3.5 shrink-0" />
                  <span>{tab.label}</span>
                  <span
                    className={cn(
                      'text-[10px] px-1.5 py-0.2 rounded-full font-mono font-bold',
                      isActive ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-500'
                    )}
                  >
                    {badgeCount}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Strengths Cards List */}
        {filteredStrengths.length === 0 ? (
          <div className="py-8 text-center border border-dashed border-slate-200 rounded-xl space-y-2">
            <p className="text-xs text-slate-500 font-medium">
              No strengths identified in this specific category.
            </p>
            <p className="text-[11px] text-slate-400">
              Switch to "All Strengths" to review the candidate's complete profile.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredStrengths.map((item) => {
              const IconComp = getCategoryIcon(item.category);
              const isDemonstrated = item.strength_type === 'demonstrated';

              return (
                <div
                  key={`${item.category}-${item.relevance_rank}-${item.title}`}
                  className="p-4 rounded-xl border border-slate-200 bg-white hover:border-slate-300 transition-all shadow-xs space-y-3"
                >
                  {/* Card Header */}
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2.5">
                    <div className="flex items-start gap-2.5 min-w-0">
                      <div className="w-8 h-8 rounded-lg bg-teal-50 text-teal-700 border border-teal-100 flex items-center justify-center shrink-0 mt-0.5">
                        <IconComp className="w-4 h-4" />
                      </div>
                      <div className="space-y-0.5 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-mono text-[11px] font-bold text-teal-700 bg-teal-50 px-1.5 py-0.5 rounded border border-teal-100">
                            #{item.relevance_rank}
                          </span>
                          <h4 className="text-sm font-bold text-slate-900 leading-snug">
                            {item.title}
                          </h4>
                        </div>
                        <span className="text-[11px] text-slate-400 block font-medium">
                          {item.category_name}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5 shrink-0 self-start">
                      {/* Demonstrated vs Potential Badge */}
                      <Badge
                        variant="outline"
                        className={cn(
                          'text-[10px] font-semibold gap-1 px-2 py-0.5 border',
                          isDemonstrated
                            ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                            : 'bg-purple-50 text-purple-800 border-purple-200'
                        )}
                      >
                        {isDemonstrated ? (
                          <>
                            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                            <span>Demonstrated</span>
                          </>
                        ) : (
                          <>
                            <Compass className="w-3 h-3 text-purple-600" />
                            <span>Potential</span>
                          </>
                        )}
                      </Badge>

                      {/* Confidence Badge */}
                      <Badge
                        variant="outline"
                        className={cn(
                          'text-[10px] font-semibold px-2 py-0.5 border',
                          getConfidenceBadgeClass(item.confidence_level)
                        )}
                        title={`Confidence: ${item.confidence_level}`}
                      >
                        {item.confidence_level} Confidence
                      </Badge>
                    </div>
                  </div>

                  {/* Explanation */}
                  <p className="text-xs text-slate-700 leading-relaxed">
                    {item.explanation}
                  </p>

                  {/* Supporting Evidence Callout */}
                  {item.evidence && item.evidence.length > 0 && (
                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 space-y-1.5">
                      <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                        <Quote className="w-3 h-3 text-slate-400" />
                        <span>Supporting Resume Evidence:</span>
                      </div>
                      <ul className="space-y-1 text-xs text-slate-800 pl-2">
                        {item.evidence.map((ev, evIdx) => (
                          <li key={evIdx} className="flex items-start gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-teal-500 mt-1.5 shrink-0" />
                            <span className="leading-relaxed font-mono text-[11px] text-slate-800">{ev}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Why this matters professionally */}
                  {item.professional_value && (
                    <div className="p-2.5 rounded-lg bg-emerald-50/40 border border-emerald-100/80 flex items-start gap-2 text-xs text-emerald-950">
                      <Lightbulb className="w-3.5 h-3.5 text-emerald-600 mt-0.5 shrink-0" />
                      <div className="space-y-0.5 leading-relaxed">
                        <span className="font-bold text-[10px] text-emerald-800 uppercase tracking-wider block">
                          Why This Matters Professionally:
                        </span>
                        <span>{item.professional_value}</span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Metadata Footer */}
        {strengthData.analysis_metadata && (
          <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-[11px] text-slate-400">
            <div className="flex items-center gap-3">
              <span>
                Model:{' '}
                <strong className="font-mono text-slate-600">
                  {strengthData.analysis_metadata.model || 'local-ai'}
                </strong>
              </span>
              {strengthData.analysis_metadata.duration_ms && (
                <span>
                  Duration:{' '}
                  <strong className="font-mono text-slate-600">
                    {strengthData.analysis_metadata.duration_ms}ms
                  </strong>
                </span>
              )}
            </div>
            {strengthData.updated_at && (
              <span>Last Analyzed: {new Date(strengthData.updated_at).toLocaleString()}</span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
