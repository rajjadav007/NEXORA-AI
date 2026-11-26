import React, { useRef, useState } from 'react';
import { Globe, Link2, Save, XCircle, ArrowRight } from 'lucide-react';
import {
  Alert,
  AlertDescription,
  AlertTitle,
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Label,
  LoadingIndicator,
  Select,
  Textarea,
} from '../ui';
import {
  EMPLOYMENT_TYPES,
  JD_MAX_LENGTH,
  JD_MIN_LENGTH,
  createJobDescription,
  importJobDescriptionFromUrl,
  validateJobDescriptionInput,
  validateJobUrl,
} from '../../services/jobDescriptionService';
import { cn } from '../../utils/cn';

function parseSkillsInput(text) {
  return String(text || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
}

export function JobDescriptionUrlImport({ onSaved, onFallbackToManual }) {
  const [url, setUrl] = useState('');
  const [urlError, setUrlError] = useState('');
  const [isImporting, setIsImporting] = useState(false);
  const [progressMessage, setProgressMessage] = useState('');
  const [importError, setImportError] = useState('');

  const [preview, setPreview] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [successRecord, setSuccessRecord] = useState(null);
  const saveLockRef = useRef(false);

  const handleImport = async (event) => {
    event.preventDefault();
    if (isImporting) return;

    const check = validateJobUrl(url);
    if (!check.isValid) {
      setUrlError(check.error);
      return;
    }

    setUrlError('');
    setImportError('');
    setSaveError('');
    setSuccessRecord(null);
    setPreview(null);
    setIsImporting(true);
    setProgressMessage('Validating URL and fetching public job posting...');

    try {
      const response = await importJobDescriptionFromUrl(check.url);
      const data = response?.data;
      if (!data) {
        throw new Error('No job information returned from import.');
      }
      setProgressMessage('Extraction complete. Review and edit fields below before saving.');
      setPreview({
        source_url: data.source_url,
        source_platform: data.source_platform,
        extraction_method: data.extraction_method,
        job_title: data.job_title || '',
        company_name: data.company_name || '',
        location: data.location || '',
        employment_type: data.employment_type || '',
        experience_required: data.experience_required || '',
        salary_info: data.salary_info || '',
        description: data.description || '',
        required_skills_text: (data.required_skills || []).join(', '),
        preferred_skills_text: (data.preferred_skills || []).join(', '),
      });
      setFieldErrors({});
    } catch (err) {
      setProgressMessage('');
      setImportError(err.message || 'Failed to import job description from URL.');
    } finally {
      setIsImporting(false);
    }
  };

  const handlePreviewChange = (field) => (event) => {
    const value = event.target.value;
    setPreview((prev) => (prev ? { ...prev, [field]: value } : prev));
    if (fieldErrors[field]) {
      setFieldErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
    if (saveError) setSaveError('');
  };

  const handleCancelPreview = () => {
    setPreview(null);
    setFieldErrors({});
    setSaveError('');
    setProgressMessage('');
  };

  const handleSave = async (event) => {
    event.preventDefault();
    if (!preview || saveLockRef.current || isSaving) return;

    const payload = {
      job_title: preview.job_title,
      company_name: preview.company_name,
      location: preview.location,
      employment_type: preview.employment_type,
      experience_required: preview.experience_required,
      salary_info: preview.salary_info,
      description: preview.description,
      source_url: preview.source_url,
      source_type: 'url',
      mandatory_skills: parseSkillsInput(preview.required_skills_text),
      preferred_skills: parseSkillsInput(preview.preferred_skills_text),
    };

    const { isValid, errors, normalized } = validateJobDescriptionInput(payload);
    if (!isValid) {
      setFieldErrors(errors);
      setSaveError('Please fix the highlighted fields before saving.');
      return;
    }

    saveLockRef.current = true;
    setIsSaving(true);
    setSaveError('');

    try {
      const response = await createJobDescription(normalized);
      const saved = response?.data || null;
      setSuccessRecord(saved);
      setPreview(null);
      setUrl('');
      setProgressMessage('');
      if (onSaved && saved) {
        onSaved(saved);
      }
    } catch (err) {
      setSaveError(err.message || 'Failed to save imported job description.');
    } finally {
      setIsSaving(false);
      saveLockRef.current = false;
    }
  };

  const descLen = preview?.description?.length || 0;
  const trimmedLen = preview?.description?.trim().length || 0;

  return (
    <Card>
      <CardHeader className="border-b border-slate-100 pb-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-teal-50 text-teal-700">
              <Globe className="h-5 w-5" />
            </div>
            <div>
              <CardTitle>Import Job Description from URL</CardTitle>
              <CardDescription>
                Supports public postings from LinkedIn, Indeed, Wellfound, Naukri, and company career pages.
              </CardDescription>
            </div>
          </div>
          <Badge variant="outline" className="text-xs">
            Phase 6 • Feature 34
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="pt-6 space-y-6">
        <form onSubmit={handleImport} noValidate className="space-y-3">
          <Label htmlFor="jd-import-url" required>
            Job Posting URL
          </Label>
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Link2 className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input
                id="jd-import-url"
                type="url"
                placeholder="https://careers.example.com/jobs/backend-engineer"
                value={url}
                onChange={(e) => {
                  setUrl(e.target.value);
                  if (urlError) setUrlError('');
                  if (importError) setImportError('');
                }}
                error={Boolean(urlError)}
                disabled={isImporting || isSaving}
                className="pl-9"
              />
            </div>
            <Button type="submit" disabled={isImporting || isSaving} className="shrink-0 gap-2">
              {isImporting ? (
                <>
                  <LoadingIndicator size="sm" />
                  Importing...
                </>
              ) : (
                'Import Job Description'
              )}
            </Button>
          </div>
          {urlError && <p className="text-xs text-red-600">{urlError}</p>}
        </form>

        {isImporting && progressMessage && (
          <Alert variant="info">
            <AlertTitle>Extracting Job Details</AlertTitle>
            <AlertDescription className="flex items-center gap-2">
              <LoadingIndicator size="sm" />
              <span>{progressMessage}</span>
            </AlertDescription>
          </Alert>
        )}

        {importError && (
          <Alert variant="error" onClose={() => setImportError('')}>
            <AlertTitle>Import Failed</AlertTitle>
            <AlertDescription className="space-y-3">
              <p>{importError}</p>
              {onFallbackToManual && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={onFallbackToManual}
                  className="gap-1.5 bg-white"
                >
                  Use Manual Input Instead
                  <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              )}
            </AlertDescription>
          </Alert>
        )}

        {successRecord && (
          <Alert variant="success" onClose={() => setSuccessRecord(null)}>
            <AlertTitle>Imported Job Description Saved</AlertTitle>
            <AlertDescription>
              <strong>{successRecord.job_title}</strong> at <strong>{successRecord.company_name}</strong> has been
              saved from URL and queued for AI analysis.
            </AlertDescription>
          </Alert>
        )}

        {preview && (
          <form onSubmit={handleSave} noValidate className="space-y-5 rounded-xl border border-slate-200 bg-slate-50/60 p-5">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Extracted Job Preview (Editable)</h3>
                <p className="text-xs text-slate-500">
                  Source: {preview.source_platform} ({preview.extraction_method})
                </p>
              </div>
              <Badge variant="secondary" className="text-xs">
                Review before saving
              </Badge>
            </div>

            {saveError && (
              <Alert variant="error" onClose={() => setSaveError('')}>
                <AlertTitle>Save Error</AlertTitle>
                <AlertDescription>{saveError}</AlertDescription>
              </Alert>
            )}

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="preview-job-title" required>
                  Job Title
                </Label>
                <Input
                  id="preview-job-title"
                  value={preview.job_title}
                  onChange={handlePreviewChange('job_title')}
                  error={Boolean(fieldErrors.job_title)}
                  disabled={isSaving}
                />
                {fieldErrors.job_title && (
                  <p className="mt-1 text-xs text-red-600">{fieldErrors.job_title}</p>
                )}
              </div>

              <div>
                <Label htmlFor="preview-company-name" required>
                  Company Name
                </Label>
                <Input
                  id="preview-company-name"
                  value={preview.company_name}
                  onChange={handlePreviewChange('company_name')}
                  error={Boolean(fieldErrors.company_name)}
                  disabled={isSaving}
                />
                {fieldErrors.company_name && (
                  <p className="mt-1 text-xs text-red-600">{fieldErrors.company_name}</p>
                )}
              </div>

              <div>
                <Label htmlFor="preview-location">Job Location (Optional)</Label>
                <Input
                  id="preview-location"
                  value={preview.location}
                  onChange={handlePreviewChange('location')}
                  disabled={isSaving}
                />
              </div>

              <div>
                <Label htmlFor="preview-employment-type">Employment Type (Optional)</Label>
                <Select
                  id="preview-employment-type"
                  value={preview.employment_type}
                  onChange={handlePreviewChange('employment_type')}
                  disabled={isSaving}
                >
                  <option value="">Select employment type (optional)</option>
                  {EMPLOYMENT_TYPES.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </Select>
              </div>

              <div>
                <Label htmlFor="preview-experience">Experience Requirements (Optional)</Label>
                <Input
                  id="preview-experience"
                  placeholder="e.g., 3+ years"
                  value={preview.experience_required}
                  onChange={handlePreviewChange('experience_required')}
                  disabled={isSaving}
                />
              </div>

              <div>
                <Label htmlFor="preview-salary">Salary Information (Optional)</Label>
                <Input
                  id="preview-salary"
                  placeholder="e.g., USD 120,000 - 150,000 / year"
                  value={preview.salary_info}
                  onChange={handlePreviewChange('salary_info')}
                  disabled={isSaving}
                />
              </div>

              <div>
                <Label htmlFor="preview-required-skills">Required Skills (Comma-separated)</Label>
                <Input
                  id="preview-required-skills"
                  placeholder="Python, FastAPI, PostgreSQL"
                  value={preview.required_skills_text}
                  onChange={handlePreviewChange('required_skills_text')}
                  disabled={isSaving}
                />
              </div>

              <div>
                <Label htmlFor="preview-preferred-skills">Preferred Skills (Comma-separated)</Label>
                <Input
                  id="preview-preferred-skills"
                  placeholder="Docker, Kubernetes, AWS"
                  value={preview.preferred_skills_text}
                  onChange={handlePreviewChange('preferred_skills_text')}
                  disabled={isSaving}
                />
              </div>
            </div>

            <div>
              <div className="mb-1.5 flex items-center justify-between gap-2">
                <Label htmlFor="preview-description" required className="mb-0">
                  Job Description
                </Label>
                <span
                  className={cn(
                    'text-xs font-medium tabular-nums',
                    trimmedLen > JD_MAX_LENGTH
                      ? 'text-red-600'
                      : trimmedLen < JD_MIN_LENGTH
                        ? 'text-amber-600'
                        : 'text-teal-700'
                  )}
                >
                  {descLen.toLocaleString()} / {JD_MAX_LENGTH.toLocaleString()} characters
                </span>
              </div>
              <Textarea
                id="preview-description"
                rows={9}
                className="min-h-[200px] bg-white"
                value={preview.description}
                onChange={handlePreviewChange('description')}
                error={Boolean(fieldErrors.description)}
                disabled={isSaving}
              />
              {fieldErrors.description && (
                <p className="mt-1 text-xs text-red-600">{fieldErrors.description}</p>
              )}
            </div>

            <div className="flex flex-wrap items-center justify-end gap-3 border-t border-slate-200 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={handleCancelPreview}
                disabled={isSaving}
                className="gap-1.5 bg-white"
              >
                <XCircle className="h-4 w-4" />
                Cancel
              </Button>
              <Button type="submit" disabled={isSaving} className="gap-1.5">
                {isSaving ? (
                  <>
                    <LoadingIndicator size="sm" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4" />
                    Save Job Description
                  </>
                )}
              </Button>
            </div>
          </form>
        )}
      </CardContent>
    </Card>
  );
}
