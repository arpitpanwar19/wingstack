import React, { useRef, useState } from 'react';
import { FileText, Sparkles, Trash2, UploadCloud } from 'lucide-react';
import GlassCard from './GlassCard';
import GlassButton from './GlassButton';
import ProgressBar from './ProgressBar';

export default function ResumeUploader({
  onFileSelect,
  selectedFile,
  isUploading = false,
  uploadProgress = 0,
  error,
  onClear,
  onAnalyze,
}) {
  const inputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [localError, setLocalError] = useState('');

  const validateAndSelect = (file) => {
    if (!file) return;
    const isPdf =
      file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
    if (!isPdf) {
      setLocalError('Please upload a valid PDF resume (.pdf).');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setLocalError('PDF file must be 10 MB or smaller.');
      return;
    }
    setLocalError('');
    onFileSelect?.(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const file = e.dataTransfer?.files?.[0];
    validateAndSelect(file);
  };

  const displayError = error || localError;
  const formattedSize = selectedFile
    ? `${(selectedFile.size / 1024).toFixed(1)} KB`
    : '';

  return (
    <GlassCard glow={isDragging ? 'cyan' : 'none'} className="space-y-4">
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          setIsDragging(false);
        }}
        onDrop={handleDrop}
        className={`relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-10 text-center transition-all duration-300 cursor-pointer ${
          isDragging
            ? 'border-honey-300 bg-honey-300/10 shadow-glow-cyan'
            : 'border-honey-100/15 bg-black/20 hover:border-honey-300/40 hover:bg-plum-950/35'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          className="hidden"
          onChange={(e) => {
            validateAndSelect(e.target.files?.[0]);
            e.target.value = '';
          }}
        />

        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-honey-200/20 bg-gradient-to-br from-honey-300/10 to-plum-700/40 text-honey-200 shadow-glow-blue">
          <UploadCloud className="h-7 w-7" />
        </div>

        <h3 className="text-base sm:text-lg font-bold text-white">
          {isDragging ? 'Drop your PDF resume here' : 'Drag & drop your PDF resume'}
        </h3>
        <p className="mt-1.5 text-xs sm:text-sm text-slate-400 max-w-md">
          A PDF is optional (max 10 MB) and will be sent with your profile analysis.
        </p>

        <div className="mt-5">
          <GlassButton
            variant="secondary"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              inputRef.current?.click();
            }}
          >
            Browse PDF File
          </GlassButton>
        </div>
      </div>

      {displayError && (
        <p className="text-xs font-medium text-rose-300 px-1">{displayError}</p>
      )}

      {selectedFile && (
        <div className="rounded-xl border border-white/12 bg-white/[0.05] p-4 space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-plum-900/50 border border-honey-200/15 text-honey-200">
                <FileText className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-white truncate">
                  {selectedFile.name}
                </p>
                <p className="text-xs font-mono text-slate-400">PDF • {formattedSize}</p>
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              {onClear && !isUploading && (
                <GlassButton
                  variant="ghost"
                  size="sm"
                  icon={Trash2}
                  onClick={onClear}
                  aria-label="Remove selected file"
                >
                  Remove
                </GlassButton>
              )}
              {onAnalyze && (
                <GlassButton
                  variant="primary"
                  size="sm"
                  icon={Sparkles}
                  loading={isUploading}
                  onClick={onAnalyze}
                >
                  {isUploading ? 'Uploading...' : 'Upload and Analyze'}
                </GlassButton>
              )}
            </div>
          </div>

          {isUploading && selectedFile && (
            <ProgressBar
              value={uploadProgress}
              label="Sending profile data"
              size="sm"
            />
          )}
        </div>
      )}
    </GlassCard>
  );
}
