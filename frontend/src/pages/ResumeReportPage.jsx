import React, { useEffect } from 'react';
import { useSearchParams, useParams, useNavigate } from 'react-router-dom';
import { PageHeader } from '../components/layout/PageHeader';
import { ResumeReportView } from '../components/resume/ResumeReportView';
import { Button } from '../components/ui/button';
import { ArrowLeft, Eye, BarChart3, TrendingUp } from 'lucide-react';
import { useResume } from '../context/ResumeContext';

/**
 * ResumeReportPage Component
 * Phase 5 | Feature #31: AI Resume Report
 */
export function ResumeReportPage() {
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

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <PageHeader
          title="AI Resume Report"
          description="Comprehensive 11-section personalized evaluation synthesized by local AI models."
          badge="Phase 5 • Feature 31"
        />

        <div className="flex items-center gap-2 self-start sm:self-auto shrink-0 flex-wrap">
          {resumeId && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate(`/resume/analytics?id=${resumeId}`)}
                className="flex items-center gap-1.5 text-xs text-slate-700 border-slate-300 hover:bg-slate-50"
              >
                <BarChart3 className="w-3.5 h-3.5" /> Analytics Dashboard
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate(`/resume/improvements?id=${resumeId}`)}
                className="flex items-center gap-1.5 text-xs text-slate-700 border-slate-300 hover:bg-slate-50"
              >
                <TrendingUp className="w-3.5 h-3.5" /> Improvement Tracker
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate(`/resume/preview?id=${resumeId}`)}
                className="flex items-center gap-1.5 text-xs text-slate-700 border-slate-300 hover:bg-slate-50"
              >
                <Eye className="w-3.5 h-3.5" /> Resume Details
              </Button>
            </>
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

      <ResumeReportView resumeId={resumeId} />
    </div>
  );
}

export default ResumeReportPage;
