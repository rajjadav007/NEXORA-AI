import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  PenTool,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  RefreshCw,
  Sparkles,
  BookOpen,
  ArrowRight,
  Copy,
  Check,
  SpellCheck,
  FileText,
  HelpCircle,
  Layers,
  Quote,
  SlidersHorizontal,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert } from '../ui/alert';
import { LoadingIndicator } from '../ui/loading-indicator';
import { getResumeGrammar, analyzeResumeGrammar } from '../../services/grammarService';
import { cn } from '../../utils/cn';

function getScoreBadgeClass(grade) {
  const g = (grade || '').toLowerCase();
  if (g.includes('excellent')) return 'bg-emerald-100 text-emerald-800 border-emerald-300';
  if (g.includes('professional')) return 'bg-blue-100 text-blue-800 border-blue-300';
  if (g.includes('polish')) return 'bg-amber-100 text-amber-800 border-amber-300';
  return 'bg-rose-100 text-rose-800 border-rose-300';
}

function getSeverityBadgeClass(severity) {
  const s = (severity || '').toLowerCase();
  if (s === 'high') return 'bg-rose-100 text-rose-800 border-rose-300 font-bold';
  if (s === 'medium') return 'bg-amber-100 text-amber-800 border-amber-300 font-semibold';
  return 'bg-slate-100 text-slate-700 border-slate-300';
}

function getCategoryBadgeClass(category) {
  switch (category) {
    case 'grammar':
    case 'spelling':
      return 'bg-rose-50 text-rose-700 border-rose-200';
    case 'clarity':
    case 'structure':
      return 'bg-blue-50 text-blue-700 border-blue-200';
    case 'tone':
      return 'bg-purple-50 text-purple-700 border-purple-200';
    case 'wordiness':
    case 'repetition':
      return 'bg-amber-50 text-amber-700 border-amber-200';
    default:
      return 'bg-slate-50 text-slate-700 border-slate-200';
  }
}

const DASHBOARD_TABS = [
  { key: 'all', label: 'All Issues', icon: Layers },
  { key: 'grammar_spelling', label: 'Grammar & Spelling', icon: SpellCheck },
  { key: 'clarity_structure', label: 'Clarity & Structure', icon: SlidersHorizontal },
  { key: 'tone', label: 'Professional Tone', icon: PenTool },
  { key: 'wordiness', label: 'Wordiness & Repetition', icon: FileText },
  { key: 'comparisons', label: 'Sentence Comparisons', icon: ArrowRight },
];

/**
 * ResumeGrammarDashboard Component
 * Phase 4 | Feature #25: Grammar & Clarity Analysis
 */
export function ResumeGrammarDashboard({ resumeId, className }) {
  const [grammarData, setGrammarData] = useState(null);
  const [activeTab, setActiveTab] = useState('all');
  const [copiedId, setCopiedId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null);

  const fetchGrammar = useCallback(async () => {
    if (!resumeId) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await getResumeGrammar(resumeId);
      if (response && response.data) {
        setGrammarData(response.data);
      }
    } catch (err) {
      if (err.status !== 404) {
        setError(err.message || 'Failed to load grammar and clarity analysis.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [resumeId]);

  useEffect(() => {
    fetchGrammar();
  }, [fetchGrammar]);

  const handleAnalyze = async (force = false) => {
    if (!resumeId || isAnalyzing) return;
    setIsAnalyzing(true);
    setError(null);
    try {
      const response = await analyzeResumeGrammar(resumeId, { forceRecalculate: force });
      if (response && response.data) {
        setGrammarData(response.data);
      }
    } catch (err) {
      setError(err.message || 'Resume grammar audit failed.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleCopy = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredIssues = useMemo(() => {
    if (!grammarData || !grammarData.issues) return [];
    if (activeTab === 'all') return grammarData.issues;
    if (activeTab === 'grammar_spelling') {
      return grammarData.issues.filter((i) => i.category === 'grammar' || i.category === 'spelling');
    }
    if (activeTab === 'clarity_structure') {
      return grammarData.issues.filter((i) => i.category === 'clarity' || i.category === 'structure');
    }
    if (activeTab === 'tone') {
      return grammarData.issues.filter((i) => i.category === 'tone');
    }
    if (activeTab === 'wordiness') {
      return grammarData.issues.filter((i) => i.category === 'wordiness' || i.category === 'repetition');
    }
    return grammarData.issues;
  }, [grammarData, activeTab]);

  // 1. LOADING STATE
  if (isLoading) {
    return (
      <Card className={cn('p-8 text-center space-y-4 border-slate-200 shadow-sm', className)}>
        <LoadingIndicator size="lg" className="text-purple-600 mx-auto" />
        <div className="space-y-1">
          <h3 className="text-base font-bold text-slate-800">
            Analyzing Grammar, Clarity & Tone...
          </h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Checking subject-verb agreement, passive diction, wordiness, first-person pronouns, and sentence clarity.
          </p>
        </div>
      </Card>
    );
  }

  // 2. ERROR STATE (when not 404)
  if (error && !grammarData) {
    return (
      <Card className={cn('p-6 border-red-200 bg-red-50/40 shadow-sm space-y-4', className)}>
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="text-sm font-bold text-red-900">Grammar Analysis Failed</h4>
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
              'Retry Grammar Audit'
            )}
          </Button>
        </div>
      </Card>
    );
  }

  // 3. EMPTY STATE (Never analyzed)
  if (!grammarData) {
    return (
      <Card className={cn('p-8 border-dashed border-2 border-slate-200 text-center space-y-4 shadow-sm', className)}>
        <div className="w-12 h-12 bg-purple-50 rounded-full flex items-center justify-center mx-auto text-purple-600 border border-purple-100">
          <PenTool className="w-6 h-6" />
        </div>
        <div className="space-y-1.5 max-w-md mx-auto">
          <h3 className="text-base font-bold text-slate-900">
            Grammar & Clarity Analysis
          </h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            Audit your resume for spelling mistakes, passive verbs, colloquial pronouns, awkward structures, and wordiness with before-and-after sentence comparisons.
          </p>
        </div>
        <Button
          onClick={() => handleAnalyze(false)}
          disabled={isAnalyzing}
          className="bg-purple-600 hover:bg-purple-700 text-white text-xs h-9 px-4 font-semibold shadow-sm"
        >
          {isAnalyzing ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin mr-2" />
              Running Grammar Audit...
            </>
          ) : (
            <>
              <PenTool className="w-3.5 h-3.5 mr-2" />
              Run Grammar & Clarity Audit
            </>
          )}
        </Button>
      </Card>
    );
  }

  const {
    writing_score = 85,
    writing_grade = 'Professional',
    overall_assessment = '',
    readability_metrics = { readability_score: 65, grade_level: 'Professional', avg_words_per_sentence: 15, total_words: 0, complexity_assessment: '' },
    category_counts = {},
    issues = [],
    sentence_comparisons = [],
  } = grammarData;

  return (
    <Card className={cn('border-slate-200 shadow-sm overflow-hidden', className)}>
      {/* Header */}
      <CardHeader className="bg-slate-50/50 border-b border-slate-100 pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-purple-100 text-purple-800 border border-purple-200">
                <PenTool className="w-4 h-4" />
              </div>
              <CardTitle className="text-base sm:text-lg font-bold text-slate-900">
                Grammar & Clarity Analysis
              </CardTitle>
            </div>
            <CardDescription className="text-xs text-slate-500">
              Evaluates grammar, spelling, clarity, professional tone, and sentence readability without modifying original resume text.
            </CardDescription>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleAnalyze(true)}
              disabled={isAnalyzing}
              className="text-xs h-8 gap-1.5 border-slate-200 text-slate-700 hover:bg-white hover:text-slate-900"
              title="Re-run AI grammar and clarity evaluation"
            >
              <RefreshCw className={cn('w-3.5 h-3.5', isAnalyzing && 'animate-spin')} />
              <span>{isAnalyzing ? 'Analyzing...' : 'Re-audit Grammar'}</span>
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
        {/* Top Writing Quality Banner */}
        <div className="p-5 rounded-xl border bg-slate-50/70 border-slate-200/80 flex flex-col md:flex-row items-start md:items-center justify-between gap-5">
          <div className="flex items-center gap-4">
            <div className="w-20 h-20 rounded-2xl border border-purple-200 bg-purple-50 text-purple-800 flex flex-col items-center justify-center font-bold shrink-0 shadow-xs">
              <span className="text-2xl font-extrabold tracking-tight">{writing_score}</span>
              <span className="text-[10px] uppercase font-semibold text-slate-500 tracking-wider">/ 100</span>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className={cn('text-xs uppercase font-extrabold', getScoreBadgeClass(writing_grade))}>
                  {writing_grade}
                </Badge>
                <span className="text-xs text-slate-500 font-medium">Writing Assessment</span>
              </div>
              <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-medium">
                {overall_assessment}
              </p>
            </div>
          </div>

          {/* Readability Metrics Card */}
          <div className="flex items-center gap-3 w-full md:w-auto shrink-0 border-t md:border-t-0 md:border-l border-slate-200 pt-3 md:pt-0 md:pl-5">
            <div className="text-center px-3 py-1.5 bg-white border border-slate-200 rounded-lg">
              <span className="text-[10px] font-bold text-slate-400 block uppercase">Reading Level</span>
              <span className="text-xs font-bold text-slate-800">{readability_metrics.grade_level.split(' ')[0]}</span>
            </div>
            <div className="text-center px-3 py-1.5 bg-white border border-slate-200 rounded-lg">
              <span className="text-[10px] font-bold text-slate-400 block uppercase">Avg Sentence</span>
              <span className="text-xs font-bold text-slate-800">{readability_metrics.avg_words_per_sentence} words</span>
            </div>
            <div className="text-center px-3 py-1.5 bg-white border border-slate-200 rounded-lg">
              <span className="text-[10px] font-bold text-slate-400 block uppercase">Issues Found</span>
              <span className={cn('text-xs font-bold', issues.length > 0 ? 'text-amber-700' : 'text-emerald-700')}>
                {issues.length}
              </span>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-slate-200 pb-1 flex items-center gap-1.5 overflow-x-auto scrollbar-none">
          {DASHBOARD_TABS.map((tab) => {
            const Icon = tab.icon;
            const isSelected = activeTab === tab.key;
            let count = null;
            if (tab.key === 'all') count = issues.length;
            else if (tab.key === 'grammar_spelling') count = (category_counts.grammar || 0) + (category_counts.spelling || 0);
            else if (tab.key === 'clarity_structure') count = (category_counts.clarity || 0) + (category_counts.structure || 0);
            else if (tab.key === 'tone') count = category_counts.tone || 0;
            else if (tab.key === 'wordiness') count = (category_counts.wordiness || 0) + (category_counts.repetition || 0);
            else if (tab.key === 'comparisons') count = sentence_comparisons.length;

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

        {/* TAB: SENTENCE COMPARISONS (Before & After) */}
        {activeTab === 'comparisons' ? (
          <div className="space-y-4">
            <div className="p-3.5 bg-purple-50/60 border border-purple-200 rounded-xl space-y-1 text-xs text-slate-700">
              <span className="font-bold text-purple-900 block uppercase tracking-wider">
                Before-and-After Sentence Comparisons
              </span>
              <p>Review suggested phrasing upgrades below. You can copy any improved sentence directly to use in your resume editor.</p>
            </div>

            {sentence_comparisons.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500 border border-dashed rounded-xl">
                <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                No sentence rewrites needed. All bullet points exhibit high professional clarity.
              </div>
            ) : (
              sentence_comparisons.map((comp, idx) => (
                <div
                  key={idx}
                  className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs space-y-3"
                >
                  <div className="flex items-center justify-between gap-2">
                    <Badge variant="outline" className="text-[10px] bg-slate-50 text-slate-600">
                      {comp.section || 'General'}
                    </Badge>
                    <span className="text-[11px] text-slate-400 font-medium">{comp.reason}</span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    {/* Before */}
                    <div className="p-3 rounded-lg bg-rose-50/50 border border-rose-200/80 space-y-1.5">
                      <span className="text-[10px] font-bold text-rose-800 uppercase tracking-wider block">
                        Original Statement
                      </span>
                      <p className="text-slate-700 leading-relaxed font-mono text-[11px]">
                        "{comp.original_sentence}"
                      </p>
                    </div>

                    {/* After */}
                    <div className="p-3 rounded-lg bg-emerald-50/50 border border-emerald-200/80 space-y-1.5 flex flex-col justify-between">
                      <div className="space-y-1">
                        <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider block">
                          Improved Professional Phrasing
                        </span>
                        <p className="text-slate-900 font-medium leading-relaxed">
                          "{comp.improved_sentence}"
                        </p>
                      </div>

                      <div className="pt-2 flex justify-end">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleCopy(comp.improved_sentence, `comp_${idx}`)}
                          className="h-7 text-[11px] px-2 text-emerald-800 hover:bg-emerald-100 flex items-center gap-1"
                          title="Copy improved sentence to clipboard"
                        >
                          {copiedId === `comp_${idx}` ? (
                            <>
                              <Check className="w-3 h-3 text-emerald-600" /> Copied
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3" /> Copy Phrasing
                            </>
                          )}
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        ) : (
          /* ISSUES LIST */
          <div className="space-y-4">
            {filteredIssues.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500 border border-dashed rounded-xl space-y-2">
                <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
                <p className="font-semibold text-slate-700">No issues found in this category.</p>
                <p className="text-slate-400">Your phrasing adheres to standard professional writing conventions.</p>
              </div>
            ) : (
              filteredIssues.map((issue) => (
                <div
                  key={issue.id}
                  className="p-4 sm:p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-3 hover:border-slate-300 transition-colors"
                >
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <Badge variant="outline" className={cn('text-[10px] uppercase', getSeverityBadgeClass(issue.severity))}>
                        {issue.severity} Severity
                      </Badge>
                      <Badge variant="outline" className={cn('text-[10px]', getCategoryBadgeClass(issue.category))}>
                        {issue.category_name}
                      </Badge>
                      <Badge variant="outline" className="text-[10px] bg-slate-50 text-slate-600">
                        {issue.section || 'General'}
                      </Badge>
                    </div>
                  </div>

                  <p className="text-xs text-slate-600 leading-relaxed">{issue.explanation}</p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    {/* Problematic text */}
                    <div className="p-3 rounded-lg bg-rose-50/50 border border-rose-200/80 space-y-1">
                      <span className="text-[10px] font-bold text-rose-800 uppercase tracking-wider block">
                        Original Excerpt
                      </span>
                      <p className="text-slate-700 font-mono text-[11px] leading-relaxed break-words">
                        "{issue.original_text}"
                      </p>
                    </div>

                    {/* Suggested correction */}
                    <div className="p-3 rounded-lg bg-emerald-50/50 border border-emerald-200/80 space-y-1 flex flex-col justify-between">
                      <div className="space-y-1">
                        <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider block">
                          Suggested Professional Correction
                        </span>
                        <p className="text-slate-900 font-medium leading-relaxed break-words">
                          "{issue.suggested_text}"
                        </p>
                      </div>

                      <div className="pt-2 flex justify-end">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleCopy(issue.suggested_text, issue.id)}
                          className="h-7 text-[11px] px-2 text-emerald-800 hover:bg-emerald-100 flex items-center gap-1"
                          title="Copy correction"
                        >
                          {copiedId === issue.id ? (
                            <>
                              <Check className="w-3 h-3 text-emerald-600" /> Copied
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3" /> Copy
                            </>
                          )}
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
