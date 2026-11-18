import React, { useEffect, useState, useCallback } from 'react';
import { useSearchParams, useParams, useNavigate } from 'react-router-dom';
import { PageHeader } from '../components/layout/PageHeader';
import { ResumePreview } from '../components/resume/ResumePreview';
import { getResumePreview } from '../services/resumeService';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Upload, ArrowLeft } from 'lucide-react';

/**
 * ResumePreviewPage
 * Phase 2 | Feature 5: Task 1 (Resume Preview Page)
 */
export function ResumePreviewPage() {
  const [searchParams] = useSearchParams();
  const routeParams = useParams();
  const navigate = useNavigate();

  // Support both query param `?id=uuid` and path param `/resume/:resumeId/preview`
  const resumeId = searchParams.get('id') || routeParams.resumeId;

  const [previewData, setPreviewData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchPreview = useCallback(async () => {
    if (!resumeId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await getResumePreview(resumeId);
      if (response && response.data) {
        setPreviewData(response.data);
      } else {
        throw new Error('Received invalid preview response from server.');
      }
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, [resumeId]);

  useEffect(() => {
    if (resumeId) {
      fetchPreview();
    }
  }, [resumeId, fetchPreview]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <PageHeader
          title="Resume Preview"
          description="Review cleaned resume text, structural sections, and verify your original document."
          badge="Phase 2 • Feature 5"
        />

        <div className="flex items-center gap-2 self-start sm:self-auto shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/resume')}
            className="flex items-center gap-1.5 text-xs text-slate-700 border-slate-300 hover:bg-slate-50"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Upload
          </Button>
        </div>
      </div>

      {!resumeId ? (
        <Card className="p-12 text-center space-y-4 border-slate-200 shadow-sm max-w-xl mx-auto">
          <div className="w-14 h-14 rounded-2xl bg-teal-50 text-teal-600 flex items-center justify-center mx-auto border border-teal-100">
            <Upload className="w-7 h-7" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-slate-900">
              No Resume Selected for Preview
            </h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
              To preview your resume, please upload and validate a PDF or DOCX file first.
            </p>
          </div>
          <div className="pt-2">
            <Button
              onClick={() => navigate('/resume')}
              className="flex items-center gap-2 mx-auto px-6"
            >
              <Upload className="w-4 h-4" /> Go to Resume Upload
            </Button>
          </div>
        </Card>
      ) : (
        <ResumePreview
          previewData={previewData}
          isLoading={isLoading}
          error={error}
          onRetry={fetchPreview}
          onNewUpload={() => navigate('/resume')}
        />
      )}
    </div>
  );
}
