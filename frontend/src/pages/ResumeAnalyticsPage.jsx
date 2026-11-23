import React, { useEffect } from 'react';
import { useSearchParams, useParams, useNavigate } from 'react-router-dom';
import { PageHeader } from '../components/layout/PageHeader';
import { ResumeAnalyticsDashboard } from '../components/resume/ResumeAnalyticsDashboard';
import { Button } from '../components/ui/button';
import { ArrowLeft, Eye, Upload } from 'lucide-react';
import { useResume } from '../context/ResumeContext';

/**
 * ResumeAnalyticsPage Component
 * Phase 5 | Feature #28: Resume Analytics Dashboard
 */
export function ResumeAnalyticsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const routeParams = useParams();
  const navigate = useNavigate();
  const { activeResumeId, selectResume } = useResume();

  const urlResumeId = searchParams.get('id') || routeParams.resumeId;
  const resumeId = urlResumeId || activeResumeId;

  useEffect(() => {
    if (urlResumeId && urlResumeId !== activeResumeId) {
      selectResume(urlResumeId);
    } else if (!urlResumeId && activeResumeId) {
      setSearchParams({ id: activeResumeId }, { replace: true });
    }
  }, [urlResumeId, activeResumeId, selectResume, setSearchParams]);

  const handleSwitchResume = (nextId) => {
    selectResume(nextId);
    setSearchParams({ id: nextId }, { replace: true });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <PageHeader
          title="Resume Analytics Dashboard"
          description="Visual insights, scoring distributions, and synthesized findings from completed Phase 4 resume evaluations."
          badge="Phase 5 • Feature 28"
        />

        <div className="flex items-center gap-2 self-start sm:self-auto shrink-0">
          {resumeId && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/resume/preview?id=${resumeId}`)}
              className="flex items-center gap-1.5 text-xs text-slate-700 border-slate-300 hover:bg-slate-50"
            >
              <Eye className="w-3.5 h-3.5" /> Resume Details
            </Button>
          )}

          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/resume')}
            className="flex items-center gap-1.5 text-xs text-slate-700 border-slate-300 hover:bg-slate-50"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Resumes
          </Button>
        </div>
      </div>

      <ResumeAnalyticsDashboard
        resumeId={resumeId}
        onRouteChangeResume={handleSwitchResume}
      />
    </div>
  );
}

export default ResumeAnalyticsPage;
