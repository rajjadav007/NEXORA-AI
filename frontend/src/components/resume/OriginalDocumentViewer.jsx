import React from 'react';
import {
  FileText,
  Download,
  ExternalLink,
  ShieldCheck,
  FileCheck,
  Info,
} from 'lucide-react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { formatFileSize } from '../../hooks/useResumeUpload';
import { cn } from '../../utils/cn';

/**
 * OriginalDocumentViewer component
 * Phase 2 | Feature 5: Task 4 (Original Resume Access)
 */
export function OriginalDocumentViewer({
  resumeId,
  originalFilename,
  fileType,
  fileSize,
  fileDownloadUrl,
  fileViewUrl,
  className,
}) {
  const isPdf = fileType?.toLowerCase() === 'pdf' || originalFilename?.toLowerCase().endsWith('.pdf');
  const isDocx = fileType?.toLowerCase() === 'docx' || originalFilename?.toLowerCase().endsWith('.docx');

  return (
    <div className={cn('space-y-4', className)}>
      {/* File Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 bg-slate-50 border border-slate-200 rounded-xl">
        <div className="flex items-center gap-2.5 min-w-0">
          <div
            className={cn(
              'w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs shrink-0',
              isPdf ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'
            )}
          >
            {isPdf ? 'PDF' : isDocx ? 'DOCX' : 'DOC'}
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-slate-800 truncate" title={originalFilename}>
              {originalFilename || 'original_resume'}
            </p>
            <p className="text-xs text-slate-500">
              {formatFileSize(fileSize)} • Staged securely
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isPdf && fileViewUrl && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.open(fileViewUrl, '_blank', 'noopener,noreferrer')}
              className="text-xs flex items-center gap-1.5 h-8 border-slate-300 text-slate-700 hover:text-slate-900"
              title="Open PDF in a new browser tab"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Open in Tab</span>
            </Button>
          )}

          {fileDownloadUrl && (
            <a
              href={fileDownloadUrl}
              download={originalFilename || 'resume'}
              className="inline-flex"
            >
              <Button
                variant="outline"
                size="sm"
                className="text-xs flex items-center gap-1.5 h-8 bg-white border-slate-300 text-slate-800 hover:bg-slate-100"
                title={`Download ${originalFilename || 'document'}`}
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download Original</span>
              </Button>
            </a>
          )}
        </div>
      </div>

      {/* Document Presentation Container */}
      {isPdf ? (
        <div className="rounded-xl border border-slate-200 overflow-hidden bg-slate-100 shadow-inner flex flex-col h-[650px]">
          <object
            data={fileViewUrl}
            type="application/pdf"
            className="w-full h-full flex-1"
            title={`Preview of ${originalFilename}`}
          >
            {/* Fallback when native PDF object cannot be rendered inline */}
            <div className="p-8 text-center flex flex-col items-center justify-center h-full space-y-4 bg-white">
              <div className="w-16 h-16 rounded-full bg-red-50 text-red-600 flex items-center justify-center">
                <FileText className="w-8 h-8" />
              </div>
              <div className="space-y-1 max-w-sm">
                <h4 className="text-base font-bold text-slate-900">
                  PDF Preview Unavailable in this Browser
                </h4>
                <p className="text-xs text-slate-500">
                  Your browser does not support inline PDF embedding. You can view or download the original file safely below.
                </p>
              </div>
              <div className="flex items-center gap-2 pt-2">
                <Button
                  size="sm"
                  onClick={() => window.open(fileViewUrl, '_blank', 'noopener,noreferrer')}
                  className="flex items-center gap-1.5"
                >
                  <ExternalLink className="w-4 h-4" /> Open in New Tab
                </Button>
                <a href={fileDownloadUrl} download={originalFilename}>
                  <Button variant="outline" size="sm" className="flex items-center gap-1.5">
                    <Download className="w-4 h-4" /> Download PDF
                  </Button>
                </a>
              </div>
            </div>
          </object>
        </div>
      ) : isDocx ? (
        /* DOCX Presentation Card */
        <Card className="p-8 border-slate-200 bg-white text-center space-y-5 shadow-xs">
          <div className="w-16 h-16 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto border border-blue-100">
            <FileCheck className="w-8 h-8" />
          </div>

          <div className="space-y-2 max-w-md mx-auto">
            <h4 className="text-lg font-bold text-slate-900">
              Word Document Ready
            </h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              Microsoft Word (.docx) files use proprietary OpenXML layout. The extracted and cleaned content is fully formatted in the <span className="font-semibold text-slate-700">Cleaned Resume</span> tab, and you can download your original untouched file below.
            </p>
          </div>

          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200/80 max-w-sm mx-auto text-left text-xs space-y-2 text-slate-600">
            <div className="flex justify-between">
              <span className="font-medium text-slate-500">Filename:</span>
              <span className="font-semibold text-slate-900 truncate max-w-[200px]">{originalFilename}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium text-slate-500">Document Format:</span>
              <span className="font-semibold text-blue-700 uppercase">Microsoft Word (DOCX)</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium text-slate-500">File Size:</span>
              <span className="font-semibold text-slate-900">{formatFileSize(fileSize)}</span>
            </div>
          </div>

          <div className="pt-2 flex justify-center">
            <a href={fileDownloadUrl} download={originalFilename}>
              <Button className="flex items-center gap-2 px-6 shadow-sm">
                <Download className="w-4 h-4" /> Download Original Document
              </Button>
            </a>
          </div>
        </Card>
      ) : (
        <Card className="p-6 text-center text-xs text-slate-500">
          Document format is not previewable inline.
        </Card>
      )}

      {/* Security notice */}
      <div className="flex items-center gap-1.5 text-[11px] text-slate-500 px-1">
        <ShieldCheck className="w-3.5 h-3.5 text-teal-600 shrink-0" />
        <span>Document served through secure temporary streaming. Internal storage paths are never exposed.</span>
      </div>
    </div>
  );
}
