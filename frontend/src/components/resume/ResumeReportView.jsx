import React, { useState, useEffect, useCallback } from 'react';
import {
  FileText,
  Sparkles,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Award,
  Layers,
  TrendingUp,
  Cpu,
  Calendar,
  Clock,
  Briefcase,
  GraduationCap,
  FolderGit2,
  ShieldCheck,
  Zap,
  ListOrdered,
  ArrowRight,
  History,
  AlertCircle,
  Check,
  Download,
  FileDown,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { LoadingIndicator } from '../ui/loading-indicator';
import { Alert } from '../ui/alert';
import {
  generateResumeReport,
  getResumeReportHistory,
  getLatestResumeReport,
  getResumeReportById,
  exportResumeReportPdf,
} from '../../services/reportService';
import { cn } from '../../utils/cn';

function formatTimestamp(isoStr) {
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

function getPriorityBadgeClass(priority) {
  const p = (priority || '').toLowerCase();
  if (p === 'high' || p === 'critical') return 'bg-rose-50 text-rose-700 border-rose-200 font-semibold';
  if (p === 'medium') return 'bg-amber-50 text-amber-700 border-amber-200 font-medium';
  return 'bg-slate-100 text-slate-700 border-slate-200';
}

function getScoreColorClass(score) {
  if (score === null || score === undefined) return 'text-slate-400 bg-slate-50 border-slate-200';
  if (score >= 85) return 'text-emerald-700 bg-emerald-50 border-emerald-200';
  if (score >= 70) return 'text-teal-700 bg-teal-50 border-teal-200';
  if (score >= 55) return 'text-amber-700 bg-amber-50 border-amber-200';
  return 'text-rose-700 bg-rose-50 border-rose-200';
}

/**
 * ResumeReportView Component
 * Phase 5 | Feature #31: AI Resume Report
 */
export function ResumeReportView({ resumeId, className }) {
  const [report, setReport] = useState(null);
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isExportingPdf, setIsExportingPdf] = useState(false);
  const [downloadFeedback, setDownloadFeedback] = useState(null);
  const [error, setError] = useState(null);
  const [selectedReportId, setSelectedReportId] = useState('');

  // Initial load: fetch history and latest report
  const loadInitialData = useCallback(async () => {
    if (!resumeId) return;
    setIsLoading(true);
    setError(null);

    try {
      // 1. Fetch history
      const histRes = await getResumeReportHistory(resumeId).catch(() => ({ data: [] }));
      const items = histRes.data || [];
      setHistory(items);

      // 2. Fetch latest if history exists
      if (items.length > 0) {
        const latestRes = await getLatestResumeReport(resumeId);
        setReport(latestRes.data);
        setSelectedReportId(latestRes.data.report_id);
      } else {
        setReport(null);
      }
    } catch (err) {
      // 404 is normal when no report generated yet
      if (err.status !== 404) {
        setError(err.message || 'Failed to load report data.');
      } else {
        setReport(null);
      }
    } finally {
      setIsLoading(false);
    }
  }, [resumeId]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Handle switching between past reports
  const handleSelectReport = async (reportId) => {
    if (!reportId || reportId === selectedReportId) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await getResumeReportById(resumeId, reportId);
      setReport(res.data);
      setSelectedReportId(reportId);
    } catch (err) {
      setError(err.message || 'Failed to retrieve selected report.');
    } finally {
      setIsLoading(false);
    }
  };

  // Trigger report generation (calls local Ollama with fallback if offline)
  const handleGenerate = async (force = false) => {
    if (!resumeId) return;
    setIsGenerating(true);
    setError(null);

    try {
      // Try local Ollama first; if unavailable, allow fallback to deterministic analysis
      let res;
      try {
        res = await generateResumeReport(resumeId, { forceRecalculate: force, fallbackToDeterministic: false });
      } catch (ollamaErr) {
        if (ollamaErr.status === 503) {
          // Ollama offline, inform user and allow fallback synthesis
          const fallback = window.confirm(
            'Local Ollama service is currently offline or unreachable.\n\nWould you like to synthesize the AI Report from your existing Phase 3, 4, and 5 analysis records?'
          );
          if (fallback) {
            res = await generateResumeReport(resumeId, { forceRecalculate: force, fallbackToDeterministic: true });
          } else {
            throw ollamaErr;
          }
        } else {
          throw ollamaErr;
        }
      }

      setReport(res.data);
      setSelectedReportId(res.data.report_id);

      // Refresh history list
      const histRes = await getResumeReportHistory(resumeId).catch(() => ({ data: [] }));
      setHistory(histRes.data || []);
    } catch (err) {
      setError(err.message || 'Failed to generate AI Resume Report.');
    } finally {
      setIsGenerating(false);
    }
  };

  // Trigger PDF Report Export (Feature #32)
  const handleDownloadPdf = async () => {
    if (!resumeId || !report?.report_id) return;
    setIsExportingPdf(true);
    setError(null);
    setDownloadFeedback(null);

    try {
      const { blob, filename } = await exportResumeReportPdf(resumeId, report.report_id);

      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);

      setDownloadFeedback(`PDF successfully downloaded: ${filename}`);
      setTimeout(() => setDownloadFeedback(null), 6000);
    } catch (err) {
      setError(err.message || 'Failed to download report PDF. Please try again.');
    } finally {
      setIsExportingPdf(false);
    }
  };

  if (isLoading) {
    return (
      <Card className="border-slate-200 shadow-sm bg-white p-8">
        <div className="flex flex-col items-center justify-center space-y-4 text-center">
          <LoadingIndicator size="lg" text="Loading AI Resume Report..." />
          <p className="text-xs text-slate-500 max-w-sm">
            Retrieving structured evaluations, executive findings, and model assessments...
          </p>
        </div>
      </Card>
    );
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* REPORT CONTROLS & HEADER BANNER */}
      <Card className="border-slate-200 shadow-sm bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white overflow-hidden">
        <div className="p-6 sm:p-7">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold tracking-wide uppercase bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  <Sparkles className="w-3.5 h-3.5" /> Feature #31 • AI Resume Report
                </span>
                {report && (
                  <span className="text-xs text-slate-400 flex items-center gap-1">
                    <Cpu className="w-3.5 h-3.5 text-teal-400" /> {report.model}
                  </span>
                )}
              </div>
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                Comprehensive AI Resume Evaluation Report
              </h2>
              <p className="text-sm text-slate-300 max-w-2xl leading-relaxed">
                Detailed 11-section personalized assessment synthesizing Phase 3, Phase 4, and Phase 5 intelligence.
              </p>
            </div>

            <div className="flex items-center gap-2.5 self-start sm:self-auto shrink-0 flex-wrap">
              {/* Previous report history picker */}
              {history.length > 1 && (
                <div className="flex items-center gap-1.5 bg-white/10 px-2.5 py-1.5 rounded-lg border border-white/20 text-xs">
                  <History className="w-3.5 h-3.5 text-slate-300" />
                  <select
                    value={selectedReportId}
                    onChange={(e) => handleSelectReport(e.target.value)}
                    className="bg-transparent text-white text-xs focus:outline-none cursor-pointer"
                  >
                    {history.map((h, idx) => (
                      <option key={h.report_id} value={h.report_id} className="text-slate-900">
                        Report #{history.length - idx} ({formatTimestamp(h.generated_at)})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Download PDF Export Button (Feature #32) */}
              {report && (
                <Button
                  size="sm"
                  onClick={handleDownloadPdf}
                  disabled={isExportingPdf || isGenerating}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs flex items-center gap-1.5 shadow-sm"
                  title="Download complete multi-page assessment report as PDF"
                >
                  <Download className={cn('w-3.5 h-3.5', isExportingPdf && 'animate-bounce')} />
                  {isExportingPdf ? 'Generating PDF...' : 'Download PDF'}
                </Button>
              )}

              {/* Generate or Regenerate Button */}
              <Button
                size="sm"
                onClick={() => handleGenerate(report ? true : false)}
                disabled={isGenerating || isExportingPdf}
                className="bg-teal-500 hover:bg-teal-600 text-slate-950 font-semibold text-xs flex items-center gap-1.5 shadow-sm"
              >
                <RefreshCw className={cn('w-3.5 h-3.5', isGenerating && 'animate-spin')} />
                {isGenerating
                  ? 'Generating Report with Ollama...'
                  : report
                  ? 'Regenerate Report'
                  : 'Generate AI Report'}
              </Button>
            </div>
          </div>

          {report && (
            <div className="mt-4 pt-3 border-t border-white/10 flex flex-wrap items-center justify-between text-xs text-slate-400 gap-2">
              <span className="flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-teal-400" /> Generated: {formatTimestamp(report.generated_at)}
              </span>
              <span className="flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-slate-400" /> Duration: {report.generation_duration_seconds ? `${report.generation_duration_seconds}s` : 'Instant'}
              </span>
            </div>
          )}
        </div>
      </Card>

      {/* DOWNLOAD SUCCESS FEEDBACK */}
      {downloadFeedback && (
        <Alert variant="success" title="PDF Export Complete">
          <div className="flex items-center justify-between">
            <p className="text-sm text-emerald-800">{downloadFeedback}</p>
            <Button
              size="sm"
              variant="outline"
              onClick={handleDownloadPdf}
              className="text-xs ml-4 border-emerald-300 text-emerald-900 hover:bg-emerald-100"
            >
              <RefreshCw className="w-3 h-3 mr-1" /> Download Again
            </Button>
          </div>
        </Alert>
      )}

      {/* ERROR ALERT */}
      {error && (
        <Alert variant="error" title="Report Generation Error">
          <div className="space-y-2">
            <p>{error}</p>
            <div className="pt-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleGenerate(true)}
                className="text-xs flex items-center gap-1.5"
              >
                <RefreshCw className="w-3.5 h-3.5" /> Try Again
              </Button>
            </div>
          </div>
        </Alert>
      )}

      {/* EMPTY STATE */}
      {!report && !isGenerating && !error && (
        <Card className="border-slate-200 shadow-sm bg-white p-12 text-center">
          <div className="max-w-md mx-auto space-y-4">
            <div className="w-14 h-14 bg-indigo-50 border border-indigo-200 text-indigo-600 rounded-2xl flex items-center justify-center mx-auto shadow-xs">
              <FileText className="w-7 h-7" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">No AI Report Generated Yet</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Generate a personalized, comprehensive evaluation report covering executive assessment, scores, skills, experience, projects, ATS compliance, and strategic next steps.
            </p>
            <div className="pt-2">
              <Button
                onClick={() => handleGenerate(false)}
                className="bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold px-4 py-2 flex items-center gap-2 mx-auto"
              >
                <Sparkles className="w-4 h-4" /> Generate AI Resume Report
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* GENERATING SKELETON */}
      {isGenerating && (
        <Card className="border-slate-200 shadow-sm bg-white p-10 text-center">
          <div className="max-w-sm mx-auto space-y-4">
            <LoadingIndicator size="lg" text="Generating comprehensive AI report with local model..." />
            <p className="text-xs text-slate-500">
              Evaluating 11 distinct dimensions, synthesizing evidence, and structuring recommendations...
            </p>
          </div>
        </Card>
      )}

      {/* REPORT CONTENT VIEW */}
      {report && !isGenerating && (
        <div className="space-y-6">
          {/* SECTION A: EXECUTIVE SUMMARY */}
          <Card className="border-slate-200 shadow-sm bg-white overflow-hidden">
            <CardHeader className="bg-slate-50 border-b border-slate-100 pb-3">
              <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                <FileText className="w-4 h-4 text-teal-600" /> A. Executive Summary
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-5">
              <p className="text-sm text-slate-700 leading-relaxed font-normal">
                {report.sections.executive_summary.overall_assessment}
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
                {/* Main Strengths */}
                <div className="p-4 rounded-xl border border-emerald-100 bg-emerald-50/40 space-y-2">
                  <span className="text-xs font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Key Strengths
                  </span>
                  <ul className="text-xs text-slate-700 space-y-1.5 list-disc pl-4">
                    {report.sections.executive_summary.main_strengths?.map((s, idx) => (
                      <li key={idx}>{s}</li>
                    ))}
                  </ul>
                </div>

                {/* Key Weaknesses */}
                <div className="p-4 rounded-xl border border-rose-100 bg-rose-50/40 space-y-2">
                  <span className="text-xs font-bold text-rose-800 uppercase tracking-wider flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5" /> Critical Improvement Areas
                  </span>
                  <ul className="text-xs text-slate-700 space-y-1.5 list-disc pl-4">
                    {report.sections.executive_summary.key_weaknesses?.map((w, idx) => (
                      <li key={idx}>{w}</li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 text-xs text-slate-700">
                <span className="font-semibold text-slate-900 block mb-1">Strategic Enhancement Direction</span>
                <p>{report.sections.executive_summary.general_direction}</p>
              </div>
            </CardContent>
          </Card>

          {/* SECTION B: QUALITY ASSESSMENT & SCORE CARDS */}
          <Card className="border-slate-200 shadow-sm bg-white overflow-hidden">
            <CardHeader className="bg-slate-50 border-b border-slate-100 pb-3">
              <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-teal-600" /> B. Resume Quality Assessment
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-6">
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
                {/* Overall Score */}
                <div className="p-4 rounded-xl border bg-white shadow-xs space-y-1">
                  <span className="text-xs text-slate-500 font-medium">Overall Quality</span>
                  <div className="text-2xl font-bold text-slate-900">
                    {report.sections.quality_assessment.overall_score !== null && report.sections.quality_assessment.overall_score !== undefined
                      ? `${report.sections.quality_assessment.overall_score.toFixed(1)}/100`
                      : 'Not Evaluated'}
                  </div>
                  <p className="text-[11px] text-slate-500">8-dimension composite</p>
                </div>

                {/* ATS Compatibility */}
                <div className="p-4 rounded-xl border bg-white shadow-xs space-y-1">
                  <span className="text-xs text-slate-500 font-medium">ATS Compatibility</span>
                  <div className="text-2xl font-bold text-slate-900">
                    {report.sections.quality_assessment.ats_compatibility_score !== null && report.sections.quality_assessment.ats_compatibility_score !== undefined
                      ? `${report.sections.quality_assessment.ats_compatibility_score.toFixed(1)}/100`
                      : 'Not Evaluated'}
                  </div>
                  <p className="text-[11px] text-slate-500">Parser hygiene & layout</p>
                </div>

                {/* Readability */}
                <div className="p-4 rounded-xl border bg-white shadow-xs space-y-1">
                  <span className="text-xs text-slate-500 font-medium">Readability Score</span>
                  <div className="text-2xl font-bold text-slate-900">
                    {report.sections.quality_assessment.readability_score !== null && report.sections.quality_assessment.readability_score !== undefined
                      ? `${report.sections.quality_assessment.readability_score.toFixed(1)}/100`
                      : 'Not Evaluated'}
                  </div>
                  <p className="text-[11px] text-slate-500">Sentence clarity & tone</p>
                </div>

                {/* Content Completeness */}
                <div className="p-4 rounded-xl border bg-white shadow-xs space-y-1">
                  <span className="text-xs text-slate-500 font-medium">Content Completeness</span>
                  <div className="text-2xl font-bold text-slate-900">
                    {report.sections.quality_assessment.content_completeness_score !== null && report.sections.quality_assessment.content_completeness_score !== undefined
                      ? `${report.sections.quality_assessment.content_completeness_score.toFixed(1)}/100`
                      : 'Not Evaluated'}
                  </div>
                  <p className="text-[11px] text-slate-500">Core section coverage</p>
                </div>
              </div>

              <div className="text-xs text-slate-700 bg-slate-50 p-4 rounded-xl border border-slate-200">
                <span className="font-semibold text-slate-900 block mb-1">Score Explanation & Interpretation</span>
                <p className="leading-relaxed">{report.sections.quality_assessment.assessment_summary}</p>
              </div>
            </CardContent>
          </Card>

          {/* SECTION C: SKILLS ASSESSMENT */}
          <Card className="border-slate-200 shadow-sm bg-white overflow-hidden">
            <CardHeader className="bg-slate-50 border-b border-slate-100 pb-3">
              <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Cpu className="w-4 h-4 text-teal-600" /> C. Skills Assessment
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-4">
              <p className="text-xs text-slate-600 leading-relaxed">
                {report.sections.skills_assessment.distribution_observations}
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Programming Languages */}
                {report.sections.skills_assessment.programming_languages?.length > 0 && (
                  <div className="p-3.5 rounded-lg border border-slate-100 bg-slate-50 space-y-1.5">
                    <span className="text-xs font-semibold text-slate-800">Programming Languages</span>
                    <div className="flex flex-wrap gap-1.5">
                      {report.sections.skills_assessment.programming_languages.map((s, idx) => (
                        <span key={idx} className="px-2 py-0.5 rounded text-[11px] bg-white border border-slate-200 font-medium text-slate-800">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* AI / ML Skills */}
                {report.sections.skills_assessment.ai_ml_skills?.length > 0 && (
                  <div className="p-3.5 rounded-lg border border-slate-100 bg-slate-50 space-y-1.5">
                    <span className="text-xs font-semibold text-slate-800">AI & Machine Learning</span>
                    <div className="flex flex-wrap gap-1.5">
                      {report.sections.skills_assessment.ai_ml_skills.map((s, idx) => (
                        <span key={idx} className="px-2 py-0.5 rounded text-[11px] bg-white border border-slate-200 font-medium text-slate-800">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Frameworks & Tools */}
                {report.sections.skills_assessment.frameworks_and_tools?.length > 0 && (
                  <div className="sm:col-span-2 p-3.5 rounded-lg border border-slate-100 bg-slate-50 space-y-1.5">
                    <span className="text-xs font-semibold text-slate-800">Frameworks, Libraries & DevOps</span>
                    <div className="flex flex-wrap gap-1.5">
                      {report.sections.skills_assessment.frameworks_and_tools.map((s, idx) => (
                        <span key={idx} className="px-2 py-0.5 rounded text-[11px] bg-white border border-slate-200 font-medium text-slate-800">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* SECTION D & F: EXPERIENCE & PROJECTS */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Experience Assessment */}
            <Card className="border-slate-200 shadow-sm bg-white overflow-hidden">
              <CardHeader className="bg-slate-50 border-b border-slate-100 pb-3">
                <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Briefcase className="w-4 h-4 text-teal-600" /> D. Experience Assessment
                </CardTitle>
              </CardHeader>
              <CardContent className="p-5 space-y-3 text-xs text-slate-700">
                <p><strong>Responsibilities & Scope:</strong> {report.sections.experience_assessment.responsibilities_review}</p>
                <p><strong>Measurable Impact:</strong> {report.sections.experience_assessment.measurable_results_usage}</p>
                <p><strong>Presentation Quality:</strong> {report.sections.experience_assessment.professional_presentation}</p>
              </CardContent>
            </Card>

            {/* Projects Assessment */}
            <Card className="border-slate-200 shadow-sm bg-white overflow-hidden">
              <CardHeader className="bg-slate-50 border-b border-slate-100 pb-3">
                <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <FolderGit2 className="w-4 h-4 text-teal-600" /> F. Projects Assessment
                </CardTitle>
              </CardHeader>
              <CardContent className="p-5 space-y-3 text-xs text-slate-700">
                <p><strong>Problem Statements:</strong> {report.sections.project_assessment.problem_statements_clarity}</p>
                <p><strong>Implementation Rigor:</strong> {report.sections.project_assessment.implementation_details}</p>
                <p><strong>Outcomes & Traction:</strong> {report.sections.project_assessment.outcomes_and_measurable_results}</p>
              </CardContent>
            </Card>
          </div>

          {/* SECTION E: EDUCATION & CERTIFICATIONS */}
          <Card className="border-slate-200 shadow-sm bg-white overflow-hidden">
            <CardHeader className="bg-slate-50 border-b border-slate-100 pb-3">
              <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                <GraduationCap className="w-4 h-4 text-teal-600" /> E. Education Assessment
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5 space-y-3 text-xs text-slate-700">
              <p><strong>Academic Credentials:</strong> {report.sections.education_assessment.academic_presentation}</p>
              {report.sections.education_assessment.degrees_reviewed?.length > 0 && (
                <div>
                  <span className="font-semibold text-slate-800 block mb-1">Degrees Identified:</span>
                  <ul className="list-disc pl-4 space-y-0.5">
                    {report.sections.education_assessment.degrees_reviewed.map((d, idx) => (
                      <li key={idx}>{d}</li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>

          {/* SECTION G & H: STRENGTHS & WEAKNESSES */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Strengths */}
            <Card className="border-slate-200 shadow-sm bg-white overflow-hidden">
              <CardHeader className="bg-slate-50 border-b border-slate-100 pb-3">
                <CardTitle className="text-base font-bold text-emerald-800 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" /> G. Genuine Resume Strengths
                </CardTitle>
              </CardHeader>
              <CardContent className="p-5 space-y-3">
                {report.sections.strengths?.length === 0 ? (
                  <p className="text-xs text-slate-500">No specific strengths documented.</p>
                ) : (
                  report.sections.strengths.map((s, idx) => (
                    <div key={idx} className="p-3 rounded-lg border border-slate-100 bg-slate-50/60 space-y-1 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-900">{s.title}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-white text-slate-600 border border-slate-200">
                          {s.section}
                        </span>
                      </div>
                      <p className="text-slate-600 italic">"{s.evidence}"</p>
                      <p className="text-slate-700 font-medium">{s.impact}</p>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            {/* Weaknesses */}
            <Card className="border-slate-200 shadow-sm bg-white overflow-hidden">
              <CardHeader className="bg-slate-50 border-b border-slate-100 pb-3">
                <CardTitle className="text-base font-bold text-rose-800 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-600" /> H. Weakness & Gap Analysis
                </CardTitle>
              </CardHeader>
              <CardContent className="p-5 space-y-3">
                {report.sections.weaknesses?.length === 0 ? (
                  <p className="text-xs text-slate-500">No major weaknesses detected.</p>
                ) : (
                  report.sections.weaknesses.map((w, idx) => (
                    <div key={idx} className="p-3 rounded-lg border border-slate-100 bg-slate-50/60 space-y-1 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-900">{w.issue}</span>
                        <span className={cn('text-[10px] px-2 py-0.5 rounded border', getPriorityBadgeClass(w.severity))}>
                          {w.severity} Severity
                        </span>
                      </div>
                      <p className="text-slate-600">{w.recommendation}</p>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          {/* SECTION I: ATS ASSESSMENT */}
          <Card className="border-slate-200 shadow-sm bg-white overflow-hidden">
            <CardHeader className="bg-slate-50 border-b border-slate-100 pb-3">
              <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-teal-600" /> I. Applicant Tracking System (ATS) Assessment
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5 space-y-3 text-xs text-slate-700">
              <p className="leading-relaxed">{report.sections.ats_assessment.keyword_coverage_summary}</p>
              {report.sections.ats_assessment.actionable_improvements?.length > 0 && (
                <div>
                  <span className="font-semibold text-slate-900 block mb-1">Parser Hygiene Best Practices:</span>
                  <ul className="list-disc pl-4 space-y-0.5">
                    {report.sections.ats_assessment.actionable_improvements.map((imp, idx) => (
                      <li key={idx}>{imp}</li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>

          {/* SECTION J: IMPROVEMENT RECOMMENDATIONS */}
          <Card className="border-slate-200 shadow-sm bg-white overflow-hidden">
            <CardHeader className="bg-slate-50 border-b border-slate-100 pb-3">
              <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Zap className="w-4 h-4 text-teal-600" /> J. Prioritized Improvement Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5 space-y-3">
              {report.sections.recommendations?.length === 0 ? (
                <p className="text-xs text-slate-500">No pending recommendations.</p>
              ) : (
                report.sections.recommendations.map((rec, idx) => (
                  <div key={idx} className="p-3.5 rounded-lg border border-slate-200 bg-white space-y-1.5 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900">{rec.title}</span>
                      <span className={cn('text-[10px] px-2 py-0.5 rounded border', getPriorityBadgeClass(rec.priority))}>
                        {rec.priority} Priority
                      </span>
                    </div>
                    <p className="text-slate-600 leading-relaxed">{rec.description}</p>
                    <div className="p-2.5 rounded bg-slate-50 border border-slate-100 text-teal-900 font-medium">
                      Action: {rec.suggested_action}
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          {/* SECTION K: FINAL ASSESSMENT */}
          <Card className="border-teal-200 shadow-sm bg-gradient-to-br from-teal-50/50 via-white to-indigo-50/40 overflow-hidden">
            <CardHeader className="border-b border-teal-100 pb-3">
              <CardTitle className="text-base font-bold text-teal-950 flex items-center gap-2">
                <Award className="w-4 h-4 text-teal-600" /> K. Final Strategic Assessment & Next Steps
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-4">
              <p className="text-sm text-slate-800 leading-relaxed font-medium">
                {report.sections.final_assessment.overall_conclusion}
              </p>

              <div className="p-4 rounded-xl border border-teal-200 bg-white space-y-2">
                <span className="text-xs font-bold text-teal-900 uppercase tracking-wider flex items-center gap-1.5">
                  <ListOrdered className="w-3.5 h-3.5" /> Top 5 Recommended Immediate Actions
                </span>
                <ol className="text-xs text-slate-700 space-y-1.5 list-decimal pl-4">
                  {report.sections.final_assessment.top_five_actions?.map((act, idx) => (
                    <li key={idx} className="leading-relaxed">{act}</li>
                  ))}
                </ol>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

export default ResumeReportView;
