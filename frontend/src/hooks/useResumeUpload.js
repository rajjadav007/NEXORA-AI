import { useState, useRef, useCallback } from 'react';
import { uploadResume } from '../services/resumeService.js';

export const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB
export const MIN_FILE_SIZE_BYTES = 64; // 64 bytes
export const ALLOWED_EXTENSIONS = ['.pdf', '.docx'];

/**
 * Format bytes into readable string (e.g., "1.45 MB", "520 KB")
 */
export function formatFileSize(bytes) {
  if (typeof bytes !== 'number' || isNaN(bytes) || bytes < 0) return '0 B';
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(i > 1 ? 2 : 1)} ${units[i]}`;
}

/**
 * Returns actionable user suggestions based on backend validation error code.
 */
export function getErrorSuggestion(code) {
  switch (code) {
    case 'PASSWORD_PROTECTED_FILE':
      return 'Please remove password encryption in your PDF viewer and re-upload the unlocked document.';
    case 'INVALID_DOCUMENT_STRUCTURE':
      return 'This file is a standard ZIP archive or corrupted package. Please save as a standard Microsoft Word (.docx) document.';
    case 'INVALID_FILE_SIGNATURE':
      return 'The file header does not match genuine PDF/DOCX signatures. Renamed files are rejected.';
    case 'MIME_TYPE_MISMATCH':
      return 'The file content does not match its extension. Please verify you are uploading a genuine document.';
    case 'CORRUPTED_FILE':
      return 'The document appears damaged or unreadable. Please re-export a fresh copy.';
    case 'FILE_TOO_LARGE':
      return 'Maximum file size is 10 MB. Consider compressing embedded images.';
    case 'UNSUPPORTED_FILE_TYPE':
      return 'Only modern PDF (.pdf) and Word (.docx) documents are supported. Legacy .doc files are not accepted.';
    case 'EMPTY_FILE':
    case 'FILE_TOO_SMALL':
      return 'The file contains insufficient document data. Please check your file.';
    default:
      return 'Please verify your document format and try again.';
  }
}

/**
 * Custom hook managing the resume upload and validation flow.
 */
export function useResumeUpload() {
  const [file, setFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null); // { message, code, category, suggestion } | null
  const [uploadResult, setUploadResult] = useState(null);
  const [status, setStatus] = useState('idle'); // 'idle' | 'selected' | 'uploading' | 'success' | 'error'

  const activeUploadRef = useRef(null);

  const validateClientFile = useCallback((candidateFile) => {
    if (!candidateFile) {
      return {
        message: 'Please choose a file to upload.',
        code: 'EMPTY_FILE',
      };
    }

    const name = candidateFile.name.toLowerCase();
    const hasValidExt = ALLOWED_EXTENSIONS.some((ext) => name.endsWith(ext));
    if (!hasValidExt) {
      return {
        message: 'Unsupported file format. Please upload a PDF (.pdf) or Word document (.docx).',
        code: 'UNSUPPORTED_FILE_TYPE',
      };
    }

    if (candidateFile.size === 0) {
      return {
        message: 'The selected file is empty (0 bytes).',
        code: 'EMPTY_FILE',
      };
    }

    if (candidateFile.size < MIN_FILE_SIZE_BYTES) {
      return {
        message: 'The selected file is too small to be a valid document.',
        code: 'FILE_TOO_SMALL',
      };
    }

    if (candidateFile.size > MAX_FILE_SIZE_BYTES) {
      return {
        message: `File size (${formatFileSize(candidateFile.size)}) exceeds the maximum allowed limit of 10 MB.`,
        code: 'FILE_TOO_LARGE',
      };
    }

    return null;
  }, []);

  const selectFile = useCallback(
    (newFile) => {
      if (activeUploadRef.current) {
        activeUploadRef.current.abort();
        activeUploadRef.current = null;
      }

      setError(null);
      setUploadResult(null);
      setUploadProgress(0);

      const clientErr = validateClientFile(newFile);
      if (clientErr) {
        setFile(null);
        setError({
          message: clientErr.message,
          code: clientErr.code,
          suggestion: getErrorSuggestion(clientErr.code),
        });
        setStatus('error');
        return false;
      }

      setFile(newFile);
      setStatus('selected');
      return true;
    },
    [validateClientFile]
  );

  const removeFile = useCallback(() => {
    if (activeUploadRef.current) {
      activeUploadRef.current.abort();
      activeUploadRef.current = null;
    }
    setFile(null);
    setUploadProgress(0);
    setIsUploading(false);
    setError(null);
    setUploadResult(null);
    setStatus('idle');
  }, []);

  const startUpload = useCallback(async () => {
    if (isUploading) {
      return;
    }

    if (!file) {
      setError({
        message: 'No file selected for upload.',
        code: 'EMPTY_FILE',
        suggestion: 'Please select a PDF or DOCX file to begin.',
      });
      setStatus('error');
      return;
    }

    const clientErr = validateClientFile(file);
    if (clientErr) {
      setError({
        message: clientErr.message,
        code: clientErr.code,
        suggestion: getErrorSuggestion(clientErr.code),
      });
      setStatus('error');
      return;
    }

    setIsUploading(true);
    setError(null);
    setUploadProgress(0);
    setStatus('uploading');

    try {
      const uploadHandle = uploadResume(file, (percent) => {
        setUploadProgress(percent);
      });
      activeUploadRef.current = uploadHandle;

      const response = await uploadHandle.promise;

      setUploadProgress(100);
      setUploadResult(response.data || response);
      setStatus('success');
      activeUploadRef.current = null;
    } catch (err) {
      const errCode = err.code || 'FILE_VALIDATION_FAILED';
      setError({
        message: err.message || 'An error occurred during resume upload and validation.',
        code: errCode,
        category: err.category || 'validation',
        suggestion: getErrorSuggestion(errCode),
      });
      setStatus('error');
    } finally {
      setIsUploading(false);
    }
  }, [file, isUploading, validateClientFile]);

  const reset = useCallback(() => {
    removeFile();
  }, [removeFile]);

  return {
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
  };
}
