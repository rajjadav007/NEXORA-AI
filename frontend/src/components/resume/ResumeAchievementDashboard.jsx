import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Trophy,
  Award,
  TrendingUp,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  RefreshCw,
  Copy,
  Check,
  Target,
  BarChart2,
  Briefcase,
  Code,
  Flag,
  Star,
  GraduationCap,
  Users,
  Sparkles,
  Percent,
  Clock,
  Zap,
  HelpCircle,
  Quote,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { LoadingIndicator } from '../ui/loading-indicator';
import { getResumeAchievements, analyzeResumeAchievements } from '../../services/achievementService';
import { cn } from '../../utils/cn';

function getScoreGradeBadgeClass(grade) {
  const g = (grade || '').toLowerCase();
  if (g.includes('exceptional')) return 'bg-emerald-100 text-emerald-800 border-emerald-300';
  if (g.includes('strong')) return 'bg-blue-100 text-blue-800 border-blue-300';
  if (g.includes('moderate')) return 'bg-amber-100 text-amber-800 border-amber-300';
  return 'bg-rose-100 text-rose-800 border-rose-300';
}

function getImpactBadgeClass(impact) {
  const imp = (impact || '').toLowerCase();
  if (imp === 'high') return 'bg-emerald-100 text-emerald-800 border-emerald-300 font-semibold';
  if (imp === 'medium') return 'bg-blue-100 text-blue-800 border-blue-300';
  return 'bg-slate-100 text-slate-700 border-slate-300';
}

function getQualityBadgeClass(quality) {
  const q = (quality || '').toLowerCase();
  if (q === 'strong') return 'bg-emerald-50 text-emerald-700 border-emerald-300';
  if (q === 'moderate') return 'bg-amber-50 text-amber-700 border-amber-300';
  return 'bg-rose-50 text-rose-700 border-rose-300';
}

function getCategoryIcon(catKey) {
  switch (catKey) {
    case 'experience':
      return Briefcase;
    case 'academic_projects':
    case 'projects':
      return Code;
    case 'competitions':
      return Flag;
    case 'awards':
      return Trophy;
    case 'certifications':
      return Award;
    case 'leadership':
      return Users;
    default:
      return Star;
  }
}

const DASHBOARD_TABS = [
  { key: 'all', label: 'All Achievements' },
  { key: 'quantified', label: 'Quantified' },
  { key: 'unquantified', label: 'Lacking Metrics' },
  { key: 'experience', label: 'Experience' },
  { key: 'projects', label: 'Projects' },
  { key: 'awards_competitions', label: 'Awards & Contests' },
  { key: 'rubric', label: 'Scoring Rubric' },
];

/**
 * ResumeAchievementDashboard Component
 * Phase 4 | Feature #26: Achievement Analysis
 */
export function ResumeAchievementDashboard({ resumeId, className }) {
  const [data, setData] = useState(null);
  const [activeTab, setActiveTab] = useState('all');
  const [copiedId, setCopiedId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null);

  const fetchAchievements = useCallback(async () => {
    if (!resumeId) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await getResumeAchievements(resumeId);
      if (response && response.data) {
        setData(response.data);
      }
    } catch (err) {
      if (err.status !== 404) {
        setError(err.message || 'Failed to load achievement analysis.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [resumeId]);

  useEffect(() => {
    fetchAchievements();
  }, [fetchAchievements]);

  const handleAnalyze = async (force = false) => {
    if (!resumeId || isAnalyzing) return;
    setIsAnalyzing(true);
    setError(null);
    try {
      const response = await analyzeResumeAchievements(resumeId, { forceRecalculate: force });
      if (response && response.data) {
        setData(response.data);
      }
    } catch (err) {
      setError(err.message || 'Achievement evaluation failed.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleCopy = (text, id) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredAchievements = useMemo(() => {
    if (!data || !data.achievements) return [];
    if (activeTab === 'all') return data.achievements;
    if (activeTab === 'quantified') return data.achievements.filter((a) => a.is_quantified);
    if (activeTab === 'unquantified') return data.achievements.filter((a) => !a.is_quantified);
    if (activeTab === 'experience') return data.achievements.filter((a) => a.category === 'experience');
    if (activeTab === 'projects') {
      return data.achievements.filter((a) => a.category === 'projects' || a.category === 'academic_projects');
    }
    if (activeTab === 'awards_competitions') {
      return data.achievements.filter((a) => a.category === 'awards' || a.category === 'competitions');
    }
    return data.achievements;
  }, [data, activeTab]);

  // 1. LOADING STATE
  if (isLoading) {
    return (
      <Card className={cn('p-8 text-center space-y-4 border-slate-200 shadow-sm', className)}>
        <LoadingIndicator size="lg" className="text-amber-600 mx-auto" />
        <div className="space-y-1">
          <h3 className="text-base font-bold text-slate-800">
            Analyzing Accomplishments & Measurable Impact...
          </h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Extracting achievements across work experience, open-source projects, competitions, and awards; calculating metric quantification rate and Google X-Y-Z statements.
          </p>
        </div>
      </Card>
    );
  }

  // 2. ERROR STATE (when not 404)
  if (error && !data) {
    return (
      <Card className={cn('p-6 border-red-200 bg-red-50/40 shadow-sm space-y-4', className)}>
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="text-sm font-bold text-red-900">Achievement Analysis Failed</h4>
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
              'Retry Achievement Analysis'
            )}
          </Button>
        </div>
      </Card>
    );
  }

  // 3. EMPTY STATE (Never analyzed)
  if (!data) {
    return (
      <Card className={cn('p-8 border-dashed border-2 border-slate-200 text-center space-y-4 shadow-sm', className)}>
        <div className="w-12 h-12 bg-amber-50 rounded-full flex items-center justify-center mx-auto text-amber-600 border border-amber-100">
          <Trophy className="w-6 h-6" />
        </div>
        <div className="space-y-1.5 max-w-md mx-auto">
          <h3 className="text-base font-bold text-slate-800">No Achievement Analysis Yet</h3>
          <p className="text-xs text-slate-500">
            Audit your resume accomplishments, extract measurable metrics (percentages, numbers, scale), identify achievements lacking metrics, and receive Google X-Y-Z improved statements.
          </p>
        </div>
        <div className="pt-2">
          <Button
            size="sm"
            onClick={() => handleAnalyze(true)}
            disabled={isAnalyzing}
            className="bg-amber-600 hover:bg-amber-700 text-white shadow-sm"
          >
            {isAnalyzing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                Auditing Accomplishments...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                Analyze Accomplishments & Metrics
              </>
            )}
          </Button>
        </div>
      </Card>
    );
  }

  // 4. MAIN DASHBOARD
  const {
    achievement_score,
    score_grade,
    executive_summary,
    total_achievements_count,
    quantified_count,
    unquantified_count,
    quantification_rate,
    category_breakdown,
    rubric_breakdown,
  } = data;

  return (
    <Card className={cn('border-slate-200 shadow-sm space-y-6', className)}>
      {/* HEADER SECTION */}
      <CardHeader className="pb-4 border-b border-slate-100">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-xl bg-amber-50 border border-amber-100 text-amber-600 shrink-0">
              <Trophy className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <CardTitle className="text-lg font-bold text-slate-900">
                  Achievement & Impact Intelligence
                </CardTitle>
                <Badge variant="outline" className={cn('text-xs font-semibold px-2 py-0.5', getScoreGradeBadgeClass(score_grade))}>
                  {score_grade} ({achievement_score}/100)
                </Badge>
              </div>
              <CardDescription className="text-xs text-slate-500 mt-1">
                Phase 4 | Feature #26: Accomplishment extraction, metric quantification rates, and Google X-Y-Z improved statements.
              </CardDescription>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-center">
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleAnalyze(true)}
              disabled={isAnalyzing}
              className="text-xs border-slate-200 text-slate-700 hover:bg-slate-50"
            >
              {isAnalyzing ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin mr-1.5" />
                  Re-evaluating...
                </>
              ) : (
                <>
                  <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
                  Recalculate
                </>
              )}
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6 pt-0">
        {/* EXECUTIVE SUMMARY */}
        {executive_summary && (
          <div className="p-3.5 bg-gradient-to-r from-amber-50/70 via-slate-50 to-amber-50/40 border border-amber-100/80 rounded-lg flex items-start gap-3">
            <Sparkles className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <p className="text-xs text-slate-700 leading-relaxed font-medium">
              {executive_summary}
            </p>
          </div>
        )}

        {/* METRICS SUMMARY GRID */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {/* 1. QUALITY SCORE */}
          <div className="p-3.5 bg-slate-50 border border-slate-100 rounded-lg space-y-1">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>Achievement Score</span>
              <Target className="w-3.5 h-3.5 text-amber-600" />
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-black text-slate-900">{achievement_score}</span>
              <span className="text-xs text-slate-400">/100</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-1.5 mt-2">
              <div
                className={cn(
                  'h-1.5 rounded-full',
                  achievement_score >= 80 ? 'bg-emerald-500' : achievement_score >= 60 ? 'bg-blue-500' : 'bg-amber-500'
                )}
                style={{ width: `${achievement_score}%` }}
              />
            </div>
          </div>

          {/* 2. TOTAL ACCOMPLISHMENTS */}
          <div className="p-3.5 bg-slate-50 border border-slate-100 rounded-lg space-y-1">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>Identified</span>
              <Award className="w-3.5 h-3.5 text-blue-600" />
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-black text-slate-900">{total_achievements_count}</span>
              <span className="text-xs text-slate-400">items</span>
            </div>
            <p className="text-[11px] text-slate-500">Across 7 career areas</p>
          </div>

          {/* 3. QUANTIFIED ACHIEVEMENTS */}
          <div className="p-3.5 bg-slate-50 border border-slate-100 rounded-lg space-y-1">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>Quantified Rate</span>
              <Percent className="w-3.5 h-3.5 text-emerald-600" />
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-black text-emerald-700">{quantification_rate}%</span>
              <span className="text-xs text-slate-500">({quantified_count}/{total_achievements_count})</span>
            </div>
            <p className="text-[11px] text-emerald-600 font-medium">Contains verified metrics</p>
          </div>

          {/* 4. LACKING METRICS */}
          <div className="p-3.5 bg-slate-50 border border-slate-100 rounded-lg space-y-1">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>Lacking Metrics</span>
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-black text-amber-700">{unquantified_count}</span>
              <span className="text-xs text-slate-400">statements</span>
            </div>
            <p className="text-[11px] text-amber-600">Needs measurable numbers</p>
          </div>
        </div>

        {/* CATEGORY BREAKDOWN PILLS */}
        {category_breakdown && Object.keys(category_breakdown).length > 0 && (
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-slate-600 uppercase tracking-wider">
              Category Distribution & Quantification
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
              {Object.entries(category_breakdown).map(([key, cat]) => {
                const IconComponent = getCategoryIcon(key);
                const hasItems = cat.total_count > 0;
                return (
                  <div
                    key={key}
                    className={cn(
                      'p-2.5 rounded-lg border text-xs flex items-start gap-2.5 transition-all',
                      hasItems ? 'bg-white border-slate-200' : 'bg-slate-50/50 border-slate-100 opacity-60'
                    )}
                  >
                    <div className="p-1 rounded bg-slate-100 text-slate-600 shrink-0 mt-0.5">
                      <IconComponent className="w-3.5 h-3.5" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="font-semibold text-slate-800 truncate">{cat.category_name}</div>
                      <div className="text-[11px] text-slate-500 mt-0.5">
                        <span className="font-bold text-slate-700">{cat.total_count}</span> total ·{' '}
                        <span className="text-emerald-700 font-semibold">{cat.quantified_count}</span> quantified
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* TABS NAVIGATION */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 border-b border-slate-100 text-xs">
          {DASHBOARD_TABS.map((tab) => {
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                type="button"
                onClick={() => setActiveTab(tab.key)}
                className={cn(
                  'px-3 py-1.5 rounded-md font-medium whitespace-nowrap transition-colors flex items-center gap-1.5',
                  isActive
                    ? 'bg-amber-100/80 text-amber-900 border border-amber-200/80 font-bold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                )}
              >
                <span>{tab.label}</span>
                {tab.key === 'all' && (
                  <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-slate-200/70 text-slate-700">
                    {total_achievements_count}
                  </span>
                )}
                {tab.key === 'quantified' && (
                  <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-emerald-100 text-emerald-800 font-semibold">
                    {quantified_count}
                  </span>
                )}
                {tab.key === 'unquantified' && unquantified_count > 0 && (
                  <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-amber-100 text-amber-800 font-semibold">
                    {unquantified_count}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* TAB CONTENT: RUBRIC BREAKDOWN */}
        {activeTab === 'rubric' && rubric_breakdown && (
          <div className="space-y-4 p-4 bg-slate-50/60 rounded-xl border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div>
                <h4 className="text-sm font-bold text-slate-800">Scoring Rubric Breakdown</h4>
                <p className="text-xs text-slate-500">Transparent mathematical score out of 100 points.</p>
              </div>
              <Badge className="bg-amber-600 text-white font-bold text-xs px-2.5 py-1">
                {rubric_breakdown.total_score} / 100 Points
              </Badge>
            </div>

            <div className="space-y-3.5">
              {/* Metric 1 */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-semibold text-slate-700">1. Quantification Rate Score</span>
                  <span className="font-bold text-slate-900">
                    {rubric_breakdown.quantification_rate_score} / 35 pts
                  </span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2">
                  <div
                    className="bg-emerald-500 h-2 rounded-full"
                    style={{ width: `${(rubric_breakdown.quantification_rate_score / 35) * 100}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-500">Evaluates the proportion of accomplishment bullets with numbers, scale, or metrics.</p>
              </div>

              {/* Metric 2 */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-semibold text-slate-700">2. Impact Magnitude Score</span>
                  <span className="font-bold text-slate-900">
                    {rubric_breakdown.impact_magnitude_score} / 25 pts
                  </span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full"
                    style={{ width: `${(rubric_breakdown.impact_magnitude_score / 25) * 100}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-500">Rewards high-impact system, business, and latency outcomes.</p>
              </div>

              {/* Metric 3 */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-semibold text-slate-700">3. Cross-Category Diversity Score</span>
                  <span className="font-bold text-slate-900">
                    {rubric_breakdown.cross_category_diversity_score} / 15 pts
                  </span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2">
                  <div
                    className="bg-purple-500 h-2 rounded-full"
                    style={{ width: `${(rubric_breakdown.cross_category_diversity_score / 15) * 100}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-500">Rewards accomplishments demonstrated across multiple categories (experience, open source, hackathons).</p>
              </div>

              {/* Metric 4 */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-semibold text-slate-700">4. Action-Verb & Framing Clarity</span>
                  <span className="font-bold text-slate-900">
                    {rubric_breakdown.action_clarity_score} / 15 pts
                  </span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2">
                  <div
                    className="bg-amber-500 h-2 rounded-full"
                    style={{ width: `${(rubric_breakdown.action_clarity_score / 15) * 100}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-500">Scores authoritative action verbs versus passive duty descriptions.</p>
              </div>

              {/* Metric 5 */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-semibold text-slate-700">5. Metric Verification Fidelity</span>
                  <span className="font-bold text-slate-900">
                    {rubric_breakdown.metric_verification_fidelity_score} / 10 pts
                  </span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2">
                  <div
                    className="bg-teal-500 h-2 rounded-full"
                    style={{ width: `${(rubric_breakdown.metric_verification_fidelity_score / 10) * 100}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-500">Direct factual grounding with verified quotes from candidate's resume.</p>
              </div>
            </div>
          </div>
        )}

        {/* TAB CONTENT: ACHIEVEMENTS LIST */}
        {activeTab !== 'rubric' && (
          <div className="space-y-4">
            {filteredAchievements.length === 0 ? (
              <div className="text-center py-8 text-slate-400 space-y-2 border border-dashed rounded-lg">
                <Award className="w-6 h-6 mx-auto text-slate-300" />
                <p className="text-xs">No accomplishments found for the selected tab filter.</p>
              </div>
            ) : (
              filteredAchievements.map((item) => {
                const CategoryIcon = getCategoryIcon(item.category);
                const hasMetrics =
                  item.is_quantified &&
                  item.measurable_metrics &&
                  (item.measurable_metrics.percentages?.length > 0 ||
                    item.measurable_metrics.numbers?.length > 0 ||
                    item.measurable_metrics.time_saved?.length > 0 ||
                    item.measurable_metrics.performance_gain?.length > 0 ||
                    item.measurable_metrics.users_impacted?.length > 0);

                return (
                  <div
                    key={item.id}
                    className="border border-slate-200/90 rounded-xl p-4 bg-white shadow-xs space-y-3.5 hover:border-slate-300 transition-colors"
                  >
                    {/* Top Card Bar */}
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <div className="p-1 rounded bg-amber-50 text-amber-700 shrink-0">
                          <CategoryIcon className="w-3.5 h-3.5" />
                        </div>
                        <h4 className="text-sm font-bold text-slate-900">{item.title}</h4>
                        <Badge variant="outline" className="text-[10px] px-1.5 py-0 bg-slate-50 text-slate-600">
                          {item.category_name}
                        </Badge>
                      </div>

                      <div className="flex items-center gap-1.5 flex-wrap">
                        <Badge variant="outline" className={cn('text-[10px] px-2 py-0.5', getImpactBadgeClass(item.impact_level))}>
                          {item.impact_level} Impact
                        </Badge>
                        <Badge variant="outline" className={cn('text-[10px] px-2 py-0.5', getQualityBadgeClass(item.quality_rating))}>
                          {item.quality_rating}
                        </Badge>
                        {item.is_quantified ? (
                          <Badge variant="outline" className="text-[10px] px-2 py-0.5 bg-emerald-50 text-emerald-800 border-emerald-300 font-semibold flex items-center gap-1">
                            <CheckCircle2 className="w-2.5 h-2.5" /> Quantified
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-[10px] px-2 py-0.5 bg-amber-50 text-amber-800 border-amber-300 font-medium flex items-center gap-1">
                            <AlertTriangle className="w-2.5 h-2.5" /> Needs Metrics
                          </Badge>
                        )}
                      </div>
                    </div>

                    {/* Detected Metrics Chips */}
                    {hasMetrics && (
                      <div className="flex items-center gap-1.5 flex-wrap pt-0.5">
                        <span className="text-[11px] font-semibold text-slate-500 mr-1">Detected Metrics:</span>
                        {item.measurable_metrics.percentages?.map((p, i) => (
                          <span key={`p_${i}`} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-50 border border-emerald-200 text-emerald-800 text-[11px] font-semibold">
                            <Percent className="w-3 h-3" /> {p}
                          </span>
                        ))}
                        {item.measurable_metrics.numbers?.map((n, i) => (
                          <span key={`n_${i}`} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-blue-50 border border-blue-200 text-blue-800 text-[11px] font-medium">
                            <TrendingUp className="w-3 h-3" /> {n}
                          </span>
                        ))}
                        {item.measurable_metrics.time_saved?.map((t, i) => (
                          <span key={`t_${i}`} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-teal-50 border border-teal-200 text-teal-800 text-[11px] font-medium">
                            <Clock className="w-3 h-3" /> {t}
                          </span>
                        ))}
                        {item.measurable_metrics.performance_gain?.map((pg, i) => (
                          <span key={`pg_${i}`} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-purple-50 border border-purple-200 text-purple-800 text-[11px] font-medium">
                            <Zap className="w-3 h-3" /> {pg}
                          </span>
                        ))}
                        {item.measurable_metrics.users_impacted?.map((u, i) => (
                          <span key={`u_${i}`} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-100 border border-slate-200 text-slate-800 text-[11px] font-medium">
                            <Users className="w-3 h-3" /> {u}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Original Resume Statement */}
                    <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/80 space-y-1">
                      <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                        <Quote className="w-3 h-3 text-slate-400" />
                        <span>Original Resume Statement</span>
                      </div>
                      <p className="text-xs text-slate-800 leading-relaxed font-mono">
                        "{item.original_statement}"
                      </p>
                    </div>

                    {/* Missing Metrics Note (If unquantified) */}
                    {!item.is_quantified && item.missing_metrics_note && (
                      <div className="p-2.5 bg-amber-50/70 border border-amber-200/80 rounded-lg flex items-start gap-2">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
                        <div className="space-y-0.5">
                          <span className="text-[11px] font-bold text-amber-900">How to Quantify:</span>
                          <p className="text-xs text-amber-800 leading-relaxed">
                            {item.missing_metrics_note}
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Google X-Y-Z Improved Statement */}
                    <div className="p-3 bg-emerald-50/60 rounded-lg border border-emerald-200 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5 text-[11px] font-bold text-emerald-900 uppercase tracking-wider">
                          <Sparkles className="w-3 h-3 text-emerald-600" />
                          <span>Google X-Y-Z Improved Statement</span>
                        </div>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleCopy(item.suggested_statement, item.id)}
                          className="h-6 px-2 text-[11px] text-emerald-700 hover:text-emerald-900 hover:bg-emerald-100/70"
                        >
                          {copiedId === item.id ? (
                            <>
                              <Check className="w-3 h-3 mr-1 text-emerald-600" /> Copied
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3 mr-1" /> Copy Statement
                            </>
                          )}
                        </Button>
                      </div>
                      <p className="text-xs text-emerald-950 font-medium leading-relaxed">
                        {item.suggested_statement}
                      </p>
                    </div>

                    {/* Recruiter Explanation & Supporting Resume Evidence */}
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pt-1 text-[11px] text-slate-500">
                      <div className="leading-relaxed">
                        <span className="font-semibold text-slate-700">Recruiter Impact: </span>
                        {item.explanation}
                      </div>

                      {item.evidence && item.evidence.length > 0 && (
                        <div className="flex items-center gap-1 shrink-0">
                          <span className="font-semibold text-slate-600">Evidence:</span>
                          <span className="italic text-slate-600">
                            "{item.evidence[0].slice(0, 45)}..."
                          </span>
                        </div>
                      )}
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

export default ResumeAchievementDashboard;
