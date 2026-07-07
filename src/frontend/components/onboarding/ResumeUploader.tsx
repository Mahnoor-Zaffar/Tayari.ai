'use client';

import { useCallback, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';

export function ResumeUploader() {
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const uploadFile = useCallback(async (file: File) => {
    if (file.type !== 'application/pdf') {
      setError('Only PDF files are supported');
      return;
    }

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('resume', file);

    try {
      const res = await fetch('/api/resume/upload', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.error ?? `Upload failed (${res.status})`);
      }

      setSuccess(true);
      setTimeout(() => router.push('/dashboard'), 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  }, [router]);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) uploadFile(file);
    },
    [uploadFile],
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) uploadFile(file);
    },
    [uploadFile],
  );

  return (
    <div className="flex flex-col items-center gap-6">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`
          flex w-full max-w-md cursor-pointer flex-col items-center gap-4
          rounded-xl border-2 border-dashed p-12 transition-colors
          ${dragOver
            ? 'border-emerald-500 bg-emerald-950/20'
            : success
              ? 'border-emerald-600 bg-emerald-950/10'
              : 'border-zinc-700 bg-zinc-900 hover:border-zinc-500'
          }
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          className="hidden"
          onChange={handleChange}
        />

        {uploading ? (
          <div className="flex flex-col items-center gap-3">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-zinc-600 border-t-emerald-400" />
            <span className="text-sm text-zinc-400">Uploading and processing...</span>
          </div>
        ) : success ? (
          <div className="flex flex-col items-center gap-2">
            <svg className="h-10 w-10 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span className="text-sm text-emerald-400">Resume uploaded! Redirecting...</span>
          </div>
        ) : (
          <>
            <svg className="h-10 w-10 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <div className="text-center">
              <p className="text-sm font-medium text-zinc-300">
                Drop your resume here, or click to browse
              </p>
              <p className="mt-1 text-xs text-zinc-600">PDF format only</p>
            </div>
          </>
        )}
      </div>

      {error && (
        <p className="text-sm text-red-500">{error}</p>
      )}
    </div>
  );
}
