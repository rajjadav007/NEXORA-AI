import React, { useRef, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useResume } from '../../context/ResumeContext';
import {
  FileText,
  Upload,
  CheckCircle2,
  X,
  RefreshCw,
  ShieldCheck,
  RotateCcw,
  Sparkles,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  BookOpen,
  Eye,
} from 'lucide-react';
import { useResumeUpload, formatFileSize } from '../../hooks/useResumeUpload';
import { extractResumeText, cleanResumeText } from '../../services/resumeService.js';
import { UploadDropzone } from './UploadDropzone';
import { Card, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Alert } from '../ui/alert';
import { Badge } from '../ui/badge';
import { cn } from '../../utils/cn';

export function ResumeUpload() {
  const navigate = useNavigate();
  const { selectResume } = useResume();
  const {
    file,
    uploadProgress,
    isUploading,
    error,
    uploadResult,
    status,
    selectFile,
    removeFile,
    startUpload,
    reset,
  } = useResumeUpload();

  useEffect(() => {
    if (status === 'success' && uploadResult?.upload_id) {
      selectResume(uploadResult.upload_id, uploadResult);
    }
  }, [status, uploadResult, selectResume]);

  const [extractionData, setExtractionData] = useState(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractionError, setExtractionError] = useState(null);
  const [showExtractedText, setShowExtractedText] = useState(false);

  const [cleaningData, setCleaningData] = useState(null);
  const [isCleaning, setIsCleaning] = useState(false);
  const [cleaningError, setCleaningError] = useState(null);
  const [activeTextView, setActiveTextView] = useState('cleaned');

  const replaceInputRef = useRef(null);

  const isPdf = file?.name?.toLowerCase().endsWith('.pdf');
  const isDocx = file?.name?.toLowerCase().endsWith('.docx');

  const handleExtractText = async () => {
    if (!uploadResult?.upload_id || isExtracting) return;

    setIsExtracting(true);
    setExtractionError(null);

    try {
      const response = await extractResumeText(uploadResult.upload_id);
      setExtractionData(response.data);
      setShowExtractedText(true);
    } catch (err) {
      setExtractionError(err.message || 'Failed to extract text from resume.');
    } finally {
      setIsExtracting(false);
    }
  };

  const handleCleanText = async () => {
    if (!uploadResult?.upload_id || isCleaning) return;

    setIsCleaning(true);
    setCleaningError(null);

    try {
      const response = await cleanResumeText(
        uploadResult.upload_id,
        extractionData?.raw_text || null
      );
      setCleaningData(response.data);
      setActiveTextView('cleaned');
      setShowExtractedText(true);
    } catch (err) {
      setCleaningError(err.message || 'Failed to clean resume text.');
    } finally {
      setIsCleaning(false);
    }
  };

  const handleReset = () => {
    setExtractionData(null);
    setExtractionError(null);
    setCleaningData(null);
    setCleaningError(null);
    setShowExtractedText(false);
    reset();
  };

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      {/* Upload Card */}
      <Card className="border-slate-200 shadow-sm overflow-hidden">
        <CardHeader className="border-b border-slate-100 bg-slate-50/50 pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl font-bold text-slate-900">
                Upload & Process Resume
              </CardTitle>
              <CardDescription className="mt-1 text-slate-500">
                Select your PDF or DOCX resume to validate integrity and extract readable text.
              </CardDescription>
            </div>
            <Badge variant="outline" className="border-teal-200 bg-teal-50 text-teal-800 font-medium">
              Phase 2 • Feature 4
            </Badge>
          </div>
        </CardHeader>

        <div className="p-6 space-y-6">
          {/* Validation & Upload Error Banner */}
          {error && (
            <Alert variant="destructive" className="animate-in fade-in duration-200">
              <div className="flex-1 space-y-1">
                <div className="flex items-center gap-2">
                  <p className="font-semibold text-sm">
                    {error.code ? `Validation Error (${error.code})` : 'Upload Issue'}
                  </p>
                </div>
                <p className="text-xs text-red-800 font-medium">
                  {typeof error === 'string' ? error : error.message}
                </p>
                {error.suggestion && (
                  <p className="text-xs text-red-700 bg-red-100/60 p-2 rounded-md mt-1.5 border border-red-200/50">
                    <span className="font-semibold">Recommendation: </span>
                    {error.suggestion}
                  </p>
                )}
              </div>
            </Alert>
          )}

          {/* Success State */}
          {status === 'success' && uploadResult ? (
            <div className="space-y-5 animate-in fade-in zoom-in-95 duration-300">
              <div className="p-6 rounded-2xl bg-teal-50/70 border border-teal-200 text-center space-y-4">
                <div className="w-14 h-14 bg-teal-600 text-white rounded-full flex items-center justify-center mx-auto shadow-md">
                  <CheckCircle2 className="w-8 h-8" />
                </div>

                <div className="space-y-1">
                  <h4 className="text-lg font-bold text-teal-950">
                    Resume Validated & Staged!
                  </h4>
                  <p className="text-sm text-teal-800 max-w-md mx-auto">
                    Your document passed all integrity checks and is ready for text extraction.
                  </p>
                </div>

                {/* Upload Metadata Preview */}
                <div className="bg-white p-4 rounded-xl border border-teal-100 max-w-md mx-auto text-left space-y-2 text-xs text-slate-600 shadow-xs">
                  <div className="flex justify-between items-center py-1 border-b border-slate-100">
                    <span className="font-medium text-slate-500">Document:</span>
                    <span className="font-semibold text-slate-900 truncate max-w-[220px]">
                      {uploadResult.original_filename}
                    </span>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-slate-100">
                    <span className="font-medium text-slate-500">File Size:</span>
                    <span className="font-semibold text-slate-900">
                      {formatFileSize(uploadResult.file_size)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-slate-100">
                    <span className="font-medium text-slate-500">Format:</span>
                    <span className="font-semibold text-slate-900 uppercase">
                      {uploadResult.file_type || (isPdf ? 'PDF' : 'DOCX')}
                    </span>
                  </div>
                  <div className="flex justify-between items-center py-1">
                    <span className="font-medium text-slate-500">Status:</span>
                    <span className="inline-flex items-center gap-1 font-semibold text-teal-700 capitalize">
                      <ShieldCheck className="w-3.5 h-3.5" /> Validated & Staged
                    </span>
                  </div>
                </div>

                {/* Extraction Action */}
                {!extractionData ? (
                  <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
                    <Button
                      onClick={handleExtractText}
                      disabled={isExtracting}
                      className="inline-flex items-center gap-2 shadow-sm px-6"
                    >
                      {isExtracting ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin" /> Extracting Text...
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4" /> Extract Resume Text
                        </>
                      )}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={handleReset}
                      className="inline-flex items-center gap-2 border-slate-300 text-slate-700"
                    >
                      <RotateCcw className="w-4 h-4" /> New Upload
                    </Button>
                  </div>
                ) : null}

                {extractionError && (
                  <Alert variant="destructive" className="text-left mt-3">
                    <p className="text-xs">{extractionError}</p>
                  </Alert>
                )}
              </div>

              {/* Extraction Results View */}
              {extractionData && (
                <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                    <div className="flex items-center gap-2">
                      <BookOpen className="w-5 h-5 text-teal-600" />
                      <h4 className="text-base font-bold text-slate-900">
                        Extracted Content Summary
                      </h4>
                    </div>
                    <Badge
                      className={cn(
                        'text-xs font-semibold uppercase',
                        extractionData.extraction_status === 'SUCCESS'
                          ? 'bg-green-100 text-green-800 border-green-200'
                          : 'bg-amber-100 text-amber-800 border-amber-200'
                      )}
                    >
                      {extractionData.extraction_status}
                    </Badge>
                  </div>

                  {extractionData.extraction_status === 'NO_SELECTABLE_TEXT' ? (
                    <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900 space-y-1">
                      <p className="font-bold flex items-center gap-1.5">
                        <AlertTriangle className="w-4 h-4 text-amber-600" /> Scanned Document Detected
                      </p>
                      <p>
                        This PDF appears to be a scanned image without selectable digital text.
                        Optical Character Recognition (OCR) will be required in a future update.
                      </p>
                    </div>
                  ) : null}

                  {/* Extraction Metrics */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                      <p className="text-xs text-slate-500 font-medium">Words</p>
                      <p className="text-lg font-bold text-slate-900 font-mono">
                        {extractionData.word_count.toLocaleString()}
                      </p>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                      <p className="text-xs text-slate-500 font-medium">Characters</p>
                      <p className="text-lg font-bold text-slate-900 font-mono">
                        {extractionData.character_count.toLocaleString()}
                      </p>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                      <p className="text-xs text-slate-500 font-medium">Pages</p>
                      <p className="text-lg font-bold text-slate-900 font-mono">
                        {extractionData.page_count ?? '1'}
                      </p>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                      <p className="text-xs text-slate-500 font-medium">Method</p>
                      <p className="text-xs font-semibold text-slate-800 uppercase mt-1">
                        {extractionData.extraction_method}
                      </p>
                    </div>
                  </div>

                  {/* Text Cleaning Action */}
                  {extractionData.raw_text && !cleaningData && (
                    <div className="pt-2 flex justify-center">
                      <Button
                        onClick={handleCleanText}
                        disabled={isCleaning}
                        className="inline-flex items-center gap-2 shadow-sm bg-indigo-600 hover:bg-indigo-700 text-white px-5"
                      >
                        {isCleaning ? (
                          <>
                            <RefreshCw className="w-4 h-4 animate-spin" /> Cleaning & Normalizing...
                          </>
                        ) : (
                          <>
                            <Sparkles className="w-4 h-4" /> Clean & Normalize Text
                          </>
                        )}
                      </Button>
                    </div>
                  )}

                  {cleaningError && (
                    <Alert variant="destructive" className="text-left mt-2">
                      <p className="text-xs">{cleaningError}</p>
                    </Alert>
                  )}

                  {/* Cleaned Results Section */}
                  {cleaningData && (
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3 mt-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Sparkles className="w-4 h-4 text-indigo-600" />
                          <span className="text-sm font-bold text-slate-800">Normalized Text Profile</span>
                        </div>
                        <Badge variant="outline" className="text-xs font-semibold uppercase bg-indigo-50 text-indigo-800 border-indigo-200">
                          {cleaningData.cleaning_status}
                        </Badge>
                      </div>

                      {/* Before / After Stats */}
                      <div className="grid grid-cols-3 gap-2 text-center text-xs">
                        <div className="p-2 bg-white rounded-lg border border-slate-100">
                          <span className="text-slate-400 block text-[10px] uppercase font-semibold">Cleaned Chars</span>
                          <span className="font-bold text-slate-900 font-mono text-sm">{cleaningData.cleaned_character_count.toLocaleString()}</span>
                        </div>
                        <div className="p-2 bg-white rounded-lg border border-slate-100">
                          <span className="text-slate-400 block text-[10px] uppercase font-semibold">Reduced</span>
                          <span className="font-bold text-teal-600 font-mono text-sm">
                            {Math.max(0, cleaningData.original_character_count - cleaningData.cleaned_character_count)} chars
                          </span>
                        </div>
                        <div className="p-2 bg-white rounded-lg border border-slate-100">
                          <span className="text-slate-400 block text-[10px] uppercase font-semibold">Words</span>
                          <span className="font-bold text-slate-900 font-mono text-sm">{cleaningData.cleaned_word_count.toLocaleString()}</span>
                        </div>
                      </div>

                      {/* Operations Applied */}
                      {cleaningData.cleaning_actions?.length > 0 && (
                        <div className="space-y-1">
                          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                            Applied Operations:
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {cleaningData.cleaning_actions.map((act) => (
                              <span
                                key={act}
                                className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-indigo-100 text-indigo-800"
                              >
                                {act.replace(/_/g, ' ')}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* View Switcher: Cleaned vs Raw */}
                      <div className="flex items-center justify-between pt-1">
                        <div className="flex gap-2">
                          <button
                            type="button"
                            onClick={() => setActiveTextView('cleaned')}
                            className={cn(
                              'text-xs px-2.5 py-1 rounded-md font-medium transition-colors',
                              activeTextView === 'cleaned'
                                ? 'bg-indigo-600 text-white'
                                : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
                            )}
                          >
                            Cleaned Text
                          </button>
                          <button
                            type="button"
                            onClick={() => setActiveTextView('raw')}
                            className={cn(
                              'text-xs px-2.5 py-1 rounded-md font-medium transition-colors',
                              activeTextView === 'raw'
                                ? 'bg-indigo-600 text-white'
                                : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
                            )}
                          >
                            Raw Extracted
                          </button>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setShowExtractedText(!showExtractedText)}
                          className="text-xs text-slate-500 h-7"
                        >
                          {showExtractedText ? 'Hide' : 'Expand'}
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* Text Display */}
                  {extractionData.raw_text && showExtractedText && (
                    <div className="p-4 rounded-xl bg-slate-900 text-slate-100 max-h-72 overflow-y-auto font-mono text-xs whitespace-pre-wrap leading-relaxed shadow-inner">
                      {cleaningData && activeTextView === 'cleaned'
                        ? cleaningData.cleaned_text
                        : extractionData.raw_text}
                    </div>
                  )}

                  <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
                    <Button
                      onClick={() => navigate(`/resume/preview?id=${uploadResult.upload_id}`)}
                      className="inline-flex items-center gap-2 shadow-sm px-6 bg-teal-600 hover:bg-teal-700 text-white"
                    >
                      <Eye className="w-4 h-4" /> Open Full Resume Preview
                    </Button>
                    <Button
                      variant="outline"
                      onClick={handleReset}
                      className="inline-flex items-center gap-2 border-slate-300 text-slate-700"
                    >
                      <RotateCcw className="w-4 h-4" /> Upload Another Resume
                    </Button>
                  </div>
                </div>
              )}
            </div>
          ) : !file ? (
            /* Dropzone when no file selected */
            <UploadDropzone
              onFileSelect={selectFile}
              disabled={isUploading}
            />
          ) : (
            /* Selected File Card */
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 rounded-xl border border-slate-200 bg-slate-50/80">
                <div className="flex items-center gap-3 min-w-0">
                  <div
                    className={cn(
                      'w-11 h-11 rounded-lg flex items-center justify-center shrink-0 font-bold text-xs',
                      isPdf ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'
                    )}
                  >
                    {isPdf ? 'PDF' : isDocx ? 'DOCX' : <FileText className="w-6 h-6" />}
                  </div>

                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-slate-900 truncate">
                      {file.name}
                    </p>
                    <p className="text-xs text-slate-500">
                      {formatFileSize(file.size)}
                    </p>
                  </div>
                </div>

                {/* Actions: Replace / Remove */}
                <div className="flex items-center gap-2 shrink-0">
                  <input
                    ref={replaceInputRef}
                    type="file"
                    accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    className="hidden"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        selectFile(e.target.files[0]);
                        e.target.value = '';
                      }
                    }}
                    disabled={isUploading}
                  />

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => replaceInputRef.current?.click()}
                    disabled={isUploading}
                    className="text-xs text-slate-600 hover:text-slate-900"
                  >
                    <RefreshCw className="w-3.5 h-3.5 mr-1" /> Replace
                  </Button>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={removeFile}
                    disabled={isUploading}
                    className="text-xs text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <X className="w-3.5 h-3.5 mr-1" /> Remove
                  </Button>
                </div>
              </div>

              {/* Progress Bar (Visible while uploading or finishing) */}
              {isUploading && (
                <div className="space-y-1.5 p-3 rounded-lg bg-teal-50/50 border border-teal-100">
                  <div className="flex justify-between items-center text-xs font-medium text-slate-700">
                    <span className="flex items-center gap-1.5 text-teal-800">
                      <Upload className="w-3.5 h-3.5 animate-bounce" /> Uploading and validating resume...
                    </span>
                    <span className="text-teal-900 font-mono font-bold">{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-primary h-2 rounded-full transition-all duration-200 ease-out"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Upload Trigger Button */}
              <div className="pt-2">
                <Button
                  onClick={startUpload}
                  disabled={isUploading}
                  className="w-full flex items-center justify-center gap-2 h-11 text-base shadow-sm"
                >
                  {isUploading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" /> Processing Upload...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4" /> Start Resume Upload
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Security & Processing Notice */}
      <div className="p-4 rounded-xl border border-slate-200 bg-white/60 text-xs text-slate-500 space-y-1">
        <p className="font-semibold text-slate-700 flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-teal-600" /> Private Document Intelligence
        </p>
        <p>
          Uploaded documents are safely validated, staged in private temporary storage, and processed page-by-page.
          Original resume formatting and reading order are preserved for downstream intelligence matching.
        </p>
      </div>
    </div>
  );
}
