import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Download,
  Eye,
  Trash2,
  RefreshCw,
  FolderOpen,
  Calendar,
  Layers,
  ShieldCheck,
  Upload,
  CheckCircle,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { LoadingIndicator } from '../ui/loading-indicator';
import { Alert } from '../ui/alert';
import {
  getSavedResumes,
  deleteStoredResume,
  getResumeFileUrl,
} from '../../services/resumeService';
import { formatFileSize } from '../../hooks/useResumeUpload';
import { cn } from '../../utils/cn';
import { useResume } from '../../context/ResumeContext';

export function SavedResumesList({ onUploadNew, className }) {
  const navigate = useNavigate();
  const { activeResumeId, selectResume, clearActiveResume } = useResume();
  const [resumes, setResumes] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  const fetchResumes = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await getSavedResumes();
      setResumes(res.data || []);
    } catch (err) {
      setError(err.message || 'Failed to load saved resumes.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchResumes();
  }, []);

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Are you sure you want to delete "${name}" and all historical versions?`)) {
      return;
    }

    setDeletingId(id);
    try {
      await deleteStoredResume(id);
      setResumes((prev) => prev.filter((r) => r.id !== id));
      if (id === activeResumeId) {
        clearActiveResume();
      }
    } catch (err) {
      alert(`Failed to delete resume: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  if (isLoading) {
    return (
      <Card className={cn('p-12 text-center border-slate-200', className)}>
        <LoadingIndicator size="lg" className="text-teal-600 mx-auto mb-3" />
        <p className="text-xs text-slate-500 font-medium">Loading stored resumes...</p>
      </Card>
    );
  }

  return (
    <div className={cn('space-y-4 max-w-4xl mx-auto', className)}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-bold text-slate-900">Stored Resumes</h3>
          <p className="text-xs text-slate-500">
            Manage your permanently stored resumes, version history, and document access.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchResumes}
            disabled={isLoading}
            className="text-xs h-8 flex items-center gap-1.5 border-slate-300"
          >
            <RefreshCw className={cn('w-3.5 h-3.5', isLoading && 'animate-spin')} /> Refresh
          </Button>
          {onUploadNew && (
            <Button
              size="sm"
              onClick={onUploadNew}
              className="text-xs h-8 flex items-center gap-1.5 shadow-sm"
            >
              <Upload className="w-3.5 h-3.5" /> Upload New
            </Button>
          )}
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <p className="text-xs">{error}</p>
        </Alert>
      )}

      {resumes.length === 0 ? (
        <Card className="p-10 text-center space-y-4 border-slate-200 shadow-sm">
          <div className="w-14 h-14 rounded-2xl bg-slate-50 text-slate-400 flex items-center justify-center mx-auto border border-slate-100">
            <FolderOpen className="w-7 h-7" />
          </div>
          <div className="space-y-1">
            <h4 className="text-sm font-bold text-slate-800">No Stored Resumes Yet</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Upload a resume and click &quot;Save Resume&quot; from the preview page to store it permanently.
            </p>
          </div>
          {onUploadNew && (
            <div className="pt-2">
              <Button size="sm" onClick={onUploadNew} className="text-xs">
                Upload Your First Resume
              </Button>
            </div>
          )}
        </Card>
      ) : (
        <div className="space-y-3">
          {resumes.map((resume) => {
            const isPdf = resume.file_type?.toLowerCase() === 'pdf';
            const isDocx = resume.file_type?.toLowerCase() === 'docx';
            const dateStr = resume.created_at
              ? new Date(resume.created_at).toLocaleDateString(undefined, {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                })
              : 'Recent';

            return (
              <Card
                key={resume.id}
                className="p-4 border-slate-200 hover:border-teal-200 transition-colors shadow-xs"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <div
                      className={cn(
                        'w-10 h-10 rounded-lg flex items-center justify-center font-bold text-xs shrink-0',
                        isPdf ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'
                      )}
                    >
                      {isPdf ? 'PDF' : isDocx ? 'DOCX' : 'DOC'}
                    </div>

                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-semibold text-slate-900 truncate" title={resume.original_filename}>
                          {resume.original_filename}
                        </p>
                        {resume.id === activeResumeId && (
                          <Badge className="text-[10px] bg-teal-100 text-teal-800 border-teal-300 font-medium">
                            Active
                          </Badge>
                        )}
                        <Badge variant="outline" className="text-[10px] bg-slate-50 text-slate-700 font-mono">
                          v{resume.current_version || 1}
                        </Badge>
                      </div>

                      <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 mt-0.5">
                        <span>{formatFileSize(resume.file_size)}</span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3 text-slate-400" /> {dateStr}
                        </span>
                        <span>•</span>
                        <span className="inline-flex items-center gap-1 text-teal-700 font-medium">
                          <ShieldCheck className="w-3 h-3" /> Stored
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 self-end sm:self-auto">
                    {resume.id !== activeResumeId && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => selectResume(resume.id, resume)}
                        className="text-xs h-8 text-teal-700 hover:text-teal-800 hover:bg-teal-50"
                      >
                        Set Active
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        selectResume(resume.id, resume);
                        navigate(`/resume/preview?id=${resume.id}`);
                      }}
                      className="text-xs h-8 flex items-center gap-1 border-slate-200 text-slate-700 hover:text-slate-900"
                    >
                      <Eye className="w-3.5 h-3.5" /> Preview
                    </Button>

                    <a href={getResumeFileUrl(resume.id, true)} download={resume.original_filename}>
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-xs h-8 flex items-center gap-1 border-slate-200 text-slate-700 hover:text-slate-900"
                      >
                        <Download className="w-3.5 h-3.5" /> Download
                      </Button>
                    </a>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(resume.id, resume.original_filename)}
                      disabled={deletingId === resume.id}
                      className="text-xs h-8 text-red-600 hover:text-red-700 hover:bg-red-50 p-2"
                      title="Delete resume"
                    >
                      {deletingId === resume.id ? (
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Trash2 className="w-3.5 h-3.5" />
                      )}
                    </Button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
