import React, { useRef, useState, useCallback } from 'react';
import { UploadCloud, FileText, CheckCircle2 } from 'lucide-react';
import { cn } from '../../utils/cn';

/**
 * Drag and Drop upload zone component for resumes.
 */
export function UploadDropzone({ onFileSelect, disabled = false, className }) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = useCallback(
    (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (!disabled) {
        setIsDragging(true);
      }
    },
    [disabled]
  );

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      if (disabled) return;

      if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
        const droppedFile = e.dataTransfer.files[0];
        onFileSelect(droppedFile);
      }
    },
    [disabled, onFileSelect]
  );

  const handleFileInputChange = useCallback(
    (e) => {
      if (e.target.files && e.target.files.length > 0) {
        const selectedFile = e.target.files[0];
        onFileSelect(selectedFile);
        // Reset input value so re-selecting same file triggers change
        e.target.value = '';
      }
    },
    [onFileSelect]
  );

  const handleClick = useCallback(() => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  }, [disabled]);

  const handleKeyDown = useCallback(
    (e) => {
      if ((e.key === 'Enter' || e.key === ' ') && !disabled) {
        e.preventDefault();
        handleClick();
      }
    },
    [disabled, handleClick]
  );

  return (
    <div
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-disabled={disabled}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={cn(
        'relative flex flex-col items-center justify-center p-8 md:p-12 text-center rounded-2xl border-2 border-dashed transition-all cursor-pointer select-none group',
        isDragging
          ? 'border-primary bg-primary/5 shadow-inner scale-[0.99]'
          : 'border-slate-300 hover:border-primary/70 bg-slate-50/50 hover:bg-slate-50',
        disabled && 'opacity-60 cursor-not-allowed pointer-events-none',
        className
      )}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        onChange={handleFileInputChange}
        disabled={disabled}
        className="hidden"
        aria-label="Upload resume file"
      />

      <div
        className={cn(
          'w-16 h-16 mb-4 rounded-2xl flex items-center justify-center transition-colors',
          isDragging
            ? 'bg-primary text-white shadow-md'
            : 'bg-primary/10 text-primary group-hover:bg-primary group-hover:text-white'
        )}
      >
        <UploadCloud className="w-8 h-8 transition-transform group-hover:scale-110" />
      </div>

      <div className="space-y-1 max-w-md">
        <p className="text-base font-semibold text-slate-800">
          <span className="text-primary hover:underline">Click to upload</span> or drag and drop
        </p>
        <p className="text-xs md:text-sm text-slate-500">
          Supported formats: <span className="font-medium text-slate-700">PDF (.pdf)</span> or{' '}
          <span className="font-medium text-slate-700">Word (.docx)</span>
        </p>
        <p className="text-xs text-slate-400 mt-2">Maximum file size: 10 MB</p>
      </div>

      <div className="mt-6 flex items-center gap-4 text-xs text-slate-500">
        <span className="inline-flex items-center gap-1">
          <CheckCircle2 className="w-3.5 h-3.5 text-teal-600" /> Safe & Private
        </span>
        <span className="inline-flex items-center gap-1">
          <FileText className="w-3.5 h-3.5 text-teal-600" /> Preserves Formatting
        </span>
      </div>
    </div>
  );
}
