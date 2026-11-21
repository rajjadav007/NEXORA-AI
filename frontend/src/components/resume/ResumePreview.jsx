import React, { useState } from 'react';
import {
  FileText,
  FileCheck,
  RefreshCw,
  RotateCcw,
  Sparkles,
  AlertCircle,
  ShieldCheck,
  Layers,
  File,
  Eye,
  Bookmark,
  Check,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert } from '../ui/alert';
import { LoadingIndicator } from '../ui/loading-indicator';
import { ResumeStructuredView } from './ResumeStructuredView';
import { OriginalDocumentViewer } from './OriginalDocumentViewer';
import { PersonalInfoCard } from './PersonalInfoCard';
import { EducationSection } from './EducationSection';
import { ExperienceSection } from './ExperienceSection';
import { ProjectsSection } from './ProjectsSection';
import { CertificationsAchievementsSection } from './CertificationsAchievementsSection';
import { SkillsSection } from './SkillsSection';
import { ResumeQualityDashboard } from './ResumeQualityDashboard';
import { ResumeStrengthDashboard } from './ResumeStrengthDashboard';
import { ResumeWeaknessDashboard } from './ResumeWeaknessDashboard';
import { ResumeATSDashboard } from './ResumeATSDashboard';
import { formatFileSize } from '../../hooks/useResumeUpload';
import { saveResume } from '../../services/resumeService';
import { cn } from '../../utils/cn';

/**
 * ResumePreview component
 * Phase 2 | Feature 5 (Preview) & Feature 6 (Storage)
 */
export function ResumePreview({
  previewData,
  isLoading,
  error,
  onRetry,
  onNewUpload,
  className,
}) {
  const [activeTab, setActiveTab] = useState('cleaned'); // 'cleaned' | 'original'
  const [isSaving, setIsSaving] = useState(false);
  const [savedVersion, setSavedVersion] = useState(null);
  const [saveError, setSaveError] = useState(null);

  const handleSaveResume = async () => {
    if (!previewData?.resume_id || isSaving) return;
    setIsSaving(true);
    setSaveError(null);
    try {
      const res = await saveResume(previewData.resume_id);
      setSavedVersion(res.data?.current_version || 1);
    } catch (err) {
      setSaveError(err.message || 'Failed to save resume.');
    } finally {
      setIsSaving(false);
    }
  };

  // 1. LOADING STATE
  if (isLoading) {
    return (
      <Card className={cn('p-12 text-center space-y-4 border-slate-200 shadow-sm', className)}>
        <LoadingIndicator size="lg" className="text-teal-600 mx-auto" />
        <div className="space-y-1">
          <h3 className="text-base font-bold text-slate-800">
            Loading Resume Preview...
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Retrieving cleaned resume text, structural blocks, and document preview.
          </p>
        </div>
      </Card>
    );
  }

  // 2. ERROR STATE
  if (error) {
    return (
      <Card className={cn('p-8 border-red-200 bg-red-50/40 text-center space-y-4 shadow-sm', className)}>
        <div className="w-12 h-12 rounded-full bg-red-100 text-red-600 flex items-center justify-center mx-auto">
          <AlertCircle className="w-6 h-6" />
        </div>
        <div className="space-y-1 max-w-md mx-auto">
          <h3 className="text-base font-bold text-red-950">
            Unable to Load Resume Preview
          </h3>
          <p className="text-xs text-red-800 leading-relaxed">
            {typeof error === 'string' ? error : error?.message || 'An error occurred while loading the preview.'}
          </p>
        </div>
        <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
          {onRetry && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRetry}
              className="flex items-center gap-1.5 border-red-300 text-red-700 bg-white hover:bg-red-50"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Try Again
            </Button>
          )}
          {onNewUpload && (
            <Button
              size="sm"
              onClick={onNewUpload}
              className="flex items-center gap-1.5 shadow-sm"
            >
              <RotateCcw className="w-3.5 h-3.5" /> Upload New Resume
            </Button>
          )}
        </div>
      </Card>
    );
  }

  // 3. PROCESSING STATE
  if (previewData?.preview_status === 'PROCESSING') {
    return (
      <Card className={cn('p-8 border-amber-200 bg-amber-50/40 text-center space-y-4 shadow-sm', className)}>
        <div className="w-12 h-12 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center mx-auto">
          <RefreshCw className="w-6 h-6 animate-spin" />
        </div>
        <div className="space-y-1 max-w-md mx-auto">
          <h3 className="text-base font-bold text-amber-950">
            Resume Processing In Progress
          </h3>
          <p className="text-xs text-amber-800 leading-relaxed">
            Your uploaded document is currently undergoing text extraction and normalization.
          </p>
        </div>
        {onRetry && (
          <div className="pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onRetry}
              className="flex items-center gap-1.5 mx-auto border-amber-300 text-amber-800 bg-white hover:bg-amber-50"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Check Status
            </Button>
          </div>
        )}
      </Card>
    );
  }

  // 4. EMPTY STATE
  if (!previewData || previewData?.preview_status === 'EMPTY' || !previewData?.cleaned_text?.trim()) {
    return (
      <Card className={cn('p-10 border-slate-200 text-center space-y-4 shadow-sm', className)}>
        <div className="w-14 h-14 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center mx-auto">
          <FileText className="w-7 h-7" />
        </div>
        <div className="space-y-1.5 max-w-md mx-auto">
          <h3 className="text-base font-bold text-slate-800">
            No Cleaned Content Found
          </h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            The document was processed, but no selectable digital text could be extracted or normalized.
            This typically occurs with scanned resumes or image-only documents.
          </p>
        </div>
        {onNewUpload && (
          <div className="pt-2">
            <Button
              size="sm"
              onClick={onNewUpload}
              className="flex items-center gap-1.5 shadow-sm mx-auto"
            >
              <RotateCcw className="w-3.5 h-3.5" /> Upload Another Resume
            </Button>
          </div>
        )}
      </Card>
    );
  }

  // 5. READY STATE
  const {
    resume_id,
    original_filename,
    file_type,
    file_size,
    cleaned_text,
    blocks,
    character_count,
    word_count,
    page_count,
    cleaning_actions,
    file_download_url,
    file_view_url,
  } = previewData;

  const isPdf = file_type?.toLowerCase() === 'pdf' || original_filename?.toLowerCase().endsWith('.pdf');

  return (
    <div className={cn('space-y-6', className)}>
      {/* Resume Quality Score Engine (Phase 4 Feature #21) */}
      <ResumeQualityDashboard resumeId={resume_id} />

      {/* Resume Strength Analysis (Phase 4 Feature #22) */}
      <ResumeStrengthDashboard resumeId={resume_id} />

      {/* Resume Weakness Analysis (Phase 4 Feature #23) */}
      <ResumeWeaknessDashboard resumeId={resume_id} />

      {/* Resume ATS Compatibility Analysis (Phase 4 Feature #24) */}
      <ResumeATSDashboard resumeId={resume_id} />

      {/* Extracted Personal Information (Phase 3 Feature #13) */}
      <PersonalInfoCard resumeId={resume_id} />

      {/* Extracted Professional Experience (Phase 3 Feature #15) */}
      <ExperienceSection resumeId={resume_id} />

      {/* Extracted Education Information (Phase 3 Feature #14) */}
      <EducationSection resumeId={resume_id} />

      {/* Extracted Project Intelligence (Phase 3 Feature #18) */}
      <ProjectsSection resumeId={resume_id} />

      {/* Extracted Certifications & Achievements (Phase 3 Feature #19) */}
      <CertificationsAchievementsSection resumeId={resume_id} />

      {/* Normalized Skills Profile (Phase 3 Feature #17) */}
      <SkillsSection resumeId={resume_id} />

      {/* Top Metadata Card */}
      <Card className="border-slate-200 shadow-sm overflow-hidden">
        <CardHeader className="border-b border-slate-100 bg-slate-50/50 pb-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="space-y-1 min-w-0">
              <div className="flex items-center gap-2">
                <CardTitle className="text-lg font-bold text-slate-900 truncate" title={original_filename}>
                  {original_filename}
                </CardTitle>
                <Badge
                  variant="outline"
                  className={cn(
                    'text-[10px] uppercase font-bold shrink-0',
                    isPdf ? 'border-red-200 bg-red-50 text-red-700' : 'border-blue-200 bg-blue-50 text-blue-700'
                  )}
                >
                  {isPdf ? 'PDF' : 'DOCX'}
                </Badge>
              </div>
              <CardDescription className="text-xs text-slate-500">
                {formatFileSize(file_size)} • {isPdf && page_count ? `${page_count} page${page_count > 1 ? 's' : ''} • ` : ''}Cleaned and verified
              </CardDescription>
            </div>

            {/* Quick Metrics */}
            <div className="flex items-center gap-2 shrink-0">
              <div className="px-2.5 py-1 bg-white border border-slate-200 rounded-lg text-center">
                <span className="text-[10px] font-semibold text-slate-400 block uppercase">Words</span>
                <span className="text-xs font-bold text-slate-800 font-mono">{word_count?.toLocaleString()}</span>
              </div>
              <div className="px-2.5 py-1 bg-white border border-slate-200 rounded-lg text-center">
                <span className="text-[10px] font-semibold text-slate-400 block uppercase">Characters</span>
                <span className="text-xs font-bold text-slate-800 font-mono">{character_count?.toLocaleString()}</span>
              </div>
              <Button
                variant={savedVersion ? 'outline' : 'default'}
                size="sm"
                onClick={handleSaveResume}
                disabled={isSaving}
                className={cn(
                  'text-xs h-9 flex items-center gap-1.5 shadow-sm font-semibold',
                  savedVersion
                    ? 'border-green-300 text-green-800 bg-green-50 hover:bg-green-100'
                    : 'bg-primary text-white hover:bg-primary/90'
                )}
                title="Store this resume permanently in your account"
              >
                {isSaving ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Saving...
                  </>
                ) : savedVersion ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-green-600" /> Saved (v{savedVersion})
                  </>
                ) : (
                  <>
                    <Bookmark className="w-3.5 h-3.5" /> Save Resume
                  </>
                )}
              </Button>

              {onNewUpload && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onNewUpload}
                  className="text-xs h-9 flex items-center gap-1.5 border-slate-200 text-slate-700 hover:text-slate-900 hover:bg-slate-50"
                  title="Upload a different resume"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span className="hidden md:inline">Upload New</span>
                </Button>
              )}
            </div>
          </div>

          {saveError && (
            <Alert variant="destructive" className="mt-3 text-left">
              <p className="text-xs">{saveError}</p>
            </Alert>
          )}
        </CardHeader>

        {/* Tab Navigation */}
        <div className="px-6 pt-4 border-b border-slate-100 flex items-center gap-4">
          <button
            type="button"
            onClick={() => setActiveTab('cleaned')}
            className={cn(
              'pb-3 text-xs sm:text-sm font-semibold border-b-2 flex items-center gap-2 transition-colors',
              activeTab === 'cleaned'
                ? 'border-primary text-primary'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            )}
          >
            <Sparkles className="w-4 h-4" />
            <span>Cleaned Resume ({word_count?.toLocaleString()} words)</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('original')}
            className={cn(
              'pb-3 text-xs sm:text-sm font-semibold border-b-2 flex items-center gap-2 transition-colors',
              activeTab === 'original'
                ? 'border-primary text-primary'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            )}
          >
            <Eye className="w-4 h-4" />
            <span>Original Document</span>
          </button>
        </div>

        {/* Tab Content Panes */}
        <div className="p-6">
          {activeTab === 'cleaned' ? (
            <ResumeStructuredView
              blocks={blocks}
              cleanedText={cleaned_text}
              cleaningActions={cleaning_actions}
            />
          ) : (
            <OriginalDocumentViewer
              resumeId={resume_id}
              originalFilename={original_filename}
              fileType={file_type}
              fileSize={file_size}
              fileDownloadUrl={file_download_url}
              fileViewUrl={file_view_url}
            />
          )}
        </div>
      </Card>
    </div>
  );
}
