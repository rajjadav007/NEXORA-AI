import React, { useRef, useState } from 'react';
import { Briefcase, Eraser, Send, Sparkles } from 'lucide-react';
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
  validateJobDescriptionInput,
} from '../../services/jobDescriptionService';
import { cn } from '../../utils/cn';

const INITIAL_FORM = {
  job_title: '',
  company_name: '',
  location: '',
  employment_type: '',
  description: '',
};

export function JobDescriptionInputForm({ onSaved }) {
  const [form, setForm] = useState(INITIAL_FORM);
  const [fieldErrors, setFieldErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [successRecord, setSuccessRecord] = useState(null);
  const [lastSubmittedSignature, setLastSubmittedSignature] = useState('');
  const submitLockRef = useRef(false);

  const trimmedDescriptionLength = form.description.trim().length;
  const rawDescriptionLength = form.description.length;
  const isOverLimit = trimmedDescriptionLength > JD_MAX_LENGTH;
  const isUnderMinimum = trimmedDescriptionLength > 0 && trimmedDescriptionLength < JD_MIN_LENGTH;

  const currentSignature = `${form.job_title.trim().toLowerCase()}|${form.company_name
    .trim()
    .toLowerCase()}|${form.description.trim()}`;

  const handleFieldChange = (field) => (event) => {
    const value = event.target.value;
    setForm((prev) => ({ ...prev, [field]: value }));
    if (fieldErrors[field]) {
      setFieldErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
    if (submitError) setSubmitError('');
    if (successRecord) setSuccessRecord(null);
  };

  const handleClear = () => {
    setForm(INITIAL_FORM);
    setFieldErrors({});
    setSubmitError('');
    setSuccessRecord(null);
    setLastSubmittedSignature('');
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (submitLockRef.current || isSubmitting) return;

    const { isValid, errors, normalized } = validateJobDescriptionInput(form);
    if (!isValid) {
      setFieldErrors(errors);
      setSubmitError('Please fix the highlighted fields before submitting.');
      return;
    }

    if (lastSubmittedSignature && currentSignature === lastSubmittedSignature) {
      setSubmitError('This job description was just submitted. Modify it or click Clear to enter a new one.');
      return;
    }

    submitLockRef.current = true;
    setIsSubmitting(true);
    setSubmitError('');
    setSuccessRecord(null);

    try {
      const response = await createJobDescription(normalized);
      const saved = response?.data || null;
      setSuccessRecord(saved);
      setLastSubmittedSignature(currentSignature);
      setFieldErrors({});
      if (onSaved && saved) {
        onSaved(saved);
      }
    } catch (err) {
      setSubmitError(err.message || 'Failed to save job description. Please try again.');
    } finally {
      setIsSubmitting(false);
      submitLockRef.current = false;
    }
  };

  return (
    <Card>
      <CardHeader className="border-b border-slate-100 pb-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-teal-50 text-teal-700">
              <Briefcase className="h-5 w-5" />
            </div>
            <div>
              <CardTitle>Job Description Input</CardTitle>
              <CardDescription>
                Paste or enter a job description to save it for AI role, requirement, and skill analysis.
              </CardDescription>
            </div>
          </div>
          <Badge variant="outline" className="gap-1 text-xs">
            <Sparkles className="h-3 w-3 text-teal-600" />
            Ready for AI Analysis
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="pt-6">
        <form onSubmit={handleSubmit} noValidate className="space-y-5">
          {submitError && (
            <Alert variant="error" onClose={() => setSubmitError('')}>
              <AlertTitle>Submission Error</AlertTitle>
              <AlertDescription>{submitError}</AlertDescription>
            </Alert>
          )}

          {successRecord && (
            <Alert variant="success" onClose={() => setSuccessRecord(null)}>
              <AlertTitle>Job Description Saved</AlertTitle>
              <AlertDescription>
                <strong>{successRecord.job_title}</strong> at <strong>{successRecord.company_name}</strong>{' '}
                ({successRecord.character_count.toLocaleString()} characters) has been saved and queued for analysis.
              </AlertDescription>
            </Alert>
          )}

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor="jd-job-title" required>
                Job Title
              </Label>
              <Input
                id="jd-job-title"
                name="job_title"
                placeholder="e.g., Senior Backend Engineer"
                value={form.job_title}
                onChange={handleFieldChange('job_title')}
                error={Boolean(fieldErrors.job_title)}
                disabled={isSubmitting}
                maxLength={255}
              />
              {fieldErrors.job_title && (
                <p className="mt-1 text-xs text-red-600">{fieldErrors.job_title}</p>
              )}
            </div>

            <div>
              <Label htmlFor="jd-company-name" required>
                Company Name
              </Label>
              <Input
                id="jd-company-name"
                name="company_name"
                placeholder="e.g., Nexora Labs"
                value={form.company_name}
                onChange={handleFieldChange('company_name')}
                error={Boolean(fieldErrors.company_name)}
                disabled={isSubmitting}
                maxLength={255}
              />
              {fieldErrors.company_name && (
                <p className="mt-1 text-xs text-red-600">{fieldErrors.company_name}</p>
              )}
            </div>

            <div>
              <Label htmlFor="jd-location">Location (Optional)</Label>
              <Input
                id="jd-location"
                name="location"
                placeholder="e.g., Remote, New York, NY"
                value={form.location}
                onChange={handleFieldChange('location')}
                error={Boolean(fieldErrors.location)}
                disabled={isSubmitting}
                maxLength={255}
              />
              {fieldErrors.location && (
                <p className="mt-1 text-xs text-red-600">{fieldErrors.location}</p>
              )}
            </div>

            <div>
              <Label htmlFor="jd-employment-type">Employment Type (Optional)</Label>
              <Select
                id="jd-employment-type"
                name="employment_type"
                value={form.employment_type}
                onChange={handleFieldChange('employment_type')}
                error={Boolean(fieldErrors.employment_type)}
                disabled={isSubmitting}
              >
                <option value="">Select employment type (optional)</option>
                {EMPLOYMENT_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </Select>
              {fieldErrors.employment_type && (
                <p className="mt-1 text-xs text-red-600">{fieldErrors.employment_type}</p>
              )}
            </div>
          </div>

          <div>
            <div className="mb-1.5 flex items-center justify-between gap-2">
              <Label htmlFor="jd-description" required className="mb-0">
                Job Description
              </Label>
              <span
                className={cn(
                  'text-xs font-medium tabular-nums',
                  isOverLimit
                    ? 'text-red-600'
                    : isUnderMinimum
                      ? 'text-amber-600'
                      : trimmedDescriptionLength >= JD_MIN_LENGTH
                        ? 'text-teal-700'
                        : 'text-slate-500'
                )}
                aria-live="polite"
              >
                {rawDescriptionLength.toLocaleString()} / {JD_MAX_LENGTH.toLocaleString()} characters
                {trimmedDescriptionLength < JD_MIN_LENGTH && ` (min ${JD_MIN_LENGTH})`}
              </span>
            </div>

            <Textarea
              id="jd-description"
              name="description"
              rows={10}
              className="min-h-[220px] resize-y leading-relaxed"
              placeholder="Paste the full job description here, including responsibilities, required qualifications, and preferred skills..."
              value={form.description}
              onChange={handleFieldChange('description')}
              error={Boolean(fieldErrors.description) || isOverLimit}
              disabled={isSubmitting}
            />
            {fieldErrors.description && (
              <p className="mt-1 text-xs text-red-600">{fieldErrors.description}</p>
            )}
          </div>

          <div className="flex flex-wrap items-center justify-end gap-3 border-t border-slate-100 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={handleClear}
              disabled={isSubmitting}
              className="gap-1.5"
            >
              <Eraser className="h-4 w-4" />
              Clear
            </Button>
            <Button type="submit" disabled={isSubmitting} className="gap-1.5">
              {isSubmitting ? (
                <>
                  <LoadingIndicator size="sm" />
                  Saving...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4" />
                  Save Job Description
                </>
              )}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
