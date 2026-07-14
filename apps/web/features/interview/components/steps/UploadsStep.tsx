"use client";

import { memo, useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useFormContext } from "react-hook-form";
import {
  UploadCloud,
  File as FileIcon,
  X,
  RotateCcw,
  CheckCircle2,
  FileText,
  Loader2,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  useUploadResume,
  useUploadJobDescription,
} from "@/features/interview/hooks/use-interview-setup";
import type { InterviewSetupFormValues } from "@/features/interview/lib/wizard-schema";

interface UploadsStepProps {
  className?: string;
}

const MAX_FILE_SIZE = 5 * 1024 * 1024;
const MAX_JD_TEXT_LENGTH = 10000;

const MAGIC_NUMBERS: Record<string, number[]> = {
  "application/pdf": [0x25, 0x50, 0x44, 0x46],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
    0x50, 0x4b, 0x03, 0x04,
  ],
};

type UploadState = "idle" | "uploading" | "success" | "error";

interface ResumeFile {
  file: File;
  hash: string;
  progress: number;
  state: UploadState;
  resumeId?: string;
  error?: string;
}

export const UploadsStep = memo(function UploadsStep({ className }: UploadsStepProps) {
  const { register, setValue, watch } = useFormContext<InterviewSetupFormValues>();
  const uploadResumeMutation = useUploadResume();
  const uploadJdMutation = useUploadJobDescription();

  const [resumeFile, setResumeFile] = useState<ResumeFile | null>(null);
  const [jdMode, setJdMode] = useState<"text" | "file">("text");
  const [jdText, setJdText] = useState("");
  const [jdFile, setJdFile] = useState<{
    file: File;
    state: UploadState;
    error?: string;
    jdId?: string;
  } | null>(null);
  const [jdTextError, setJdTextError] = useState<string | null>(null);
  const [jdTextSaving, setJdTextSaving] = useState(false);
  const [jdTextSaved, setJdTextSaved] = useState(false);

  const onDrop = useCallback(
    async (accepted: File[]) => {
      const file = accepted[0];
      if (!file) return;

      if (file.size > MAX_FILE_SIZE) {
        setResumeFile({
          file,
          hash: "",
          progress: 0,
          state: "error",
          error: "File exceeds 5MB limit",
        });
        return;
      }

      const isValidType = await checkMagicNumber(file, file.type);
      if (!isValidType) {
        setResumeFile({
          file,
          hash: "",
          progress: 0,
          state: "error",
          error: "File content doesn't match its extension",
        });
        return;
      }

      try {
        const hash = await hashFile(file);
        setResumeFile({ file, hash, progress: 0, state: "uploading" });

        const result = await uploadResumeMutation.mutateAsync({
          original_filename: sanitizeFilename(file.name),
          mime_type: file.type,
          file_size: file.size,
          file_hash: hash,
        });

        setResumeFile({ file, hash, progress: 100, state: "success", resumeId: result.id });
        setValue("resume_id", result.id, { shouldDirty: true });
      } catch (err) {
        setResumeFile((prev) => ({
          file: prev?.file ?? file,
          hash: prev?.hash ?? "",
          progress: 0,
          state: "error",
          error: err instanceof Error ? err.message : "Upload failed",
        }));
      }
    },
    [uploadResumeMutation, setValue],
  );

  const dropzone = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
    maxFiles: 1,
    maxSize: MAX_FILE_SIZE,
    disabled: resumeFile?.state === "uploading",
  });

  const isDragActive = dropzone.isDragActive;
  const fileRejections = dropzone.fileRejections;

  const removeResume = () => {
    setResumeFile(null);
    setValue("resume_id", null, { shouldDirty: true });
  };

  const retryResume = async () => {
    if (!resumeFile) return;
    setResumeFile({ ...resumeFile, state: "uploading", progress: 0, error: undefined });
    try {
      const result = await uploadResumeMutation.mutateAsync({
        original_filename: sanitizeFilename(resumeFile.file.name),
        mime_type: resumeFile.file.type,
        file_size: resumeFile.file.size,
        file_hash: resumeFile.hash,
      });
      setResumeFile({ ...resumeFile, progress: 100, state: "success", resumeId: result.id });
      setValue("resume_id", result.id, { shouldDirty: true });
    } catch (err) {
      setResumeFile({
        ...resumeFile,
        state: "error",
        error: err instanceof Error ? err.message : "Retry failed",
      });
    }
  };

  const handleJdTextSubmit = async () => {
    if (jdText.trim().length < 10) {
      setJdTextError("Please enter at least 10 characters");
      return;
    }
    if (jdText.length > MAX_JD_TEXT_LENGTH) {
      setJdTextError(`Job description must be ${MAX_JD_TEXT_LENGTH} characters or less`);
      return;
    }
    setJdTextSaving(true);
    setJdTextError(null);
    try {
      const result = await uploadJdMutation.mutateAsync({
        source: "text",
        raw_text: sanitizeText(jdText),
      });
      setValue("job_description_id", result.id, { shouldDirty: true });
      setJdTextSaved(true);
    } catch (err) {
      setJdTextError(err instanceof Error ? err.message : "Failed to save job description");
    } finally {
      setJdTextSaving(false);
    }
  };

  const handleJdFileDrop = async (accepted: File[]) => {
    const file = accepted[0];
    if (!file) return;
    if (file.size > MAX_FILE_SIZE) {
      setJdFile({ file, state: "error", error: "File exceeds 5MB limit" });
      return;
    }
    const isValidType = file.type === "text/plain" ? true : await checkMagicNumber(file, file.type);
    if (!isValidType) {
      setJdFile({ file, state: "error", error: "File content doesn't match its extension" });
      return;
    }
    try {
      const hash = await hashFile(file);
      setJdFile({ file, state: "uploading" });
      const result = await uploadJdMutation.mutateAsync({
        source: "file",
        original_filename: sanitizeFilename(file.name),
        mime_type: file.type,
        file_size: file.size,
        file_hash: hash,
      });
      setJdFile({ file, state: "success", jdId: result.id });
      setValue("job_description_id", result.id, { shouldDirty: true });
    } catch (err) {
      setJdFile({
        file,
        state: "error",
        error: err instanceof Error ? err.message : "Upload failed",
      });
    }
  };

  const jdDropzone = useDropzone({
    onDrop: handleJdFileDrop,
    accept: {
      "application/pdf": [".pdf"],
      "text/plain": [".txt"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
    maxFiles: 1,
    maxSize: MAX_FILE_SIZE,
    disabled: jdFile?.state === "uploading",
  });

  const customInstructions = watch("custom_instructions");

  return (
    <div className={cn("space-y-8", className)}>
      {/* Resume Upload */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label htmlFor="resume-upload">Resume (optional)</Label>
          {resumeFile?.state === "success" && (
            <Badge variant="success" className="gap-1">
              <CheckCircle2 className="h-3 w-3" /> Uploaded
            </Badge>
          )}
        </div>

        {!resumeFile || resumeFile.state === "idle" ? (
          <div
            {...dropzone.getRootProps()}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                dropzone.open();
              }
            }}
            className={cn(
              "flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-8 text-center transition-all cursor-pointer",
              isDragActive
                ? "border-primary bg-primary/5 ring-4 ring-primary/10"
                : "border-border hover:border-primary/50 hover:bg-accent/30",
            )}
            role="button"
            tabIndex={0}
            aria-label="Upload resume"
          >
            <input
              {...dropzone.getInputProps()}
              id="resume-upload"
              aria-describedby="resume-help"
            />
            <UploadCloud className="h-10 w-10 text-muted-foreground" aria-hidden="true" />
            <div>
              <p className="text-sm font-medium">
                {isDragActive ? "Drop your resume here" : "Drag & drop or click to upload"}
              </p>
              <p id="resume-help" className="mt-1 text-xs text-muted-foreground">
                PDF or DOCX, max 5MB
              </p>
            </div>
          </div>
        ) : (
          <AnimatePresence mode="wait">
            <motion.div
              key={resumeFile.state}
              initial={{ opacity: 0, scale: 0.97 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.97 }}
              className={cn(
                "flex items-center gap-3 rounded-lg border-2 p-4",
                resumeFile.state === "success" && "border-success-border bg-success-bg",
                resumeFile.state === "uploading" && "border-info-border bg-info-bg",
                resumeFile.state === "error" && "border-destructive/30 bg-destructive/5",
              )}
            >
              <FileIcon
                className={cn(
                  "h-8 w-8 shrink-0",
                  resumeFile.state === "success" ? "text-success" : "text-muted-foreground",
                )}
              />

              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{resumeFile.file.name}</p>
                <p className="text-xs text-muted-foreground">
                  {formatFileSize(resumeFile.file.size)}
                </p>
                {resumeFile.state === "uploading" && (
                  <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                    <motion.div
                      className="h-full rounded-full bg-primary"
                      initial={{ width: "0%" }}
                      animate={{ width: `${resumeFile.progress}%` }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                )}
                {resumeFile.state === "error" && (
                  <p className="mt-1 text-xs text-destructive">{resumeFile.error}</p>
                )}
              </div>

              <div className="flex shrink-0 items-center gap-1">
                {resumeFile.state === "uploading" && (
                  <Loader2 className="h-4 w-4 animate-spin text-info" aria-label="Uploading" />
                )}
                {resumeFile.state === "success" && (
                  <CheckCircle2 className="h-4 w-4 text-success" aria-label="Upload complete" />
                )}
                {resumeFile.state === "error" && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={retryResume}
                    aria-label="Retry upload"
                  >
                    <RotateCcw className="h-4 w-4" />
                  </Button>
                )}
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={removeResume}
                  aria-label="Remove resume"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </motion.div>
          </AnimatePresence>
        )}

        {fileRejections.length > 0 &&
          fileRejections[0]?.errors.map((err, i) => (
            <p key={i} className="text-sm text-destructive" role="alert">
              {err.code === "file-too-large"
                ? "File is too large. Max 5MB."
                : err.code === "file-invalid-type"
                  ? "Invalid file type. Please upload a PDF or DOCX."
                  : err.message}
            </p>
          ))}

        {dropzone.isDragReject && (
          <p className="text-sm text-destructive" role="alert">
            Invalid file type.
          </p>
        )}
      </div>

      {/* Job Description */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label htmlFor="jd-input">Job Description (optional)</Label>
          <div
            className="flex gap-1 rounded-md border border-input p-0.5"
            role="tablist"
            aria-label="Job description input mode"
          >
            <button
              type="button"
              role="tab"
              aria-selected={jdMode === "text"}
              onClick={() => setJdMode("text")}
              className={cn(
                "rounded px-2 py-1 text-xs font-medium transition-colors",
                jdMode === "text"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              Text
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={jdMode === "file"}
              onClick={() => setJdMode("file")}
              className={cn(
                "rounded px-2 py-1 text-xs font-medium transition-colors",
                jdMode === "file"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              File
            </button>
          </div>
        </div>

        {jdMode === "text" ? (
          <div className="space-y-2">
            <Textarea
              id="jd-input"
              placeholder="Paste the job description here..."
              rows={5}
              value={jdText}
              onChange={(e) => {
                setJdText(e.target.value);
                setJdTextSaved(false);
              }}
              aria-invalid={!!jdTextError}
              aria-describedby={jdTextError ? "jd-text-error" : undefined}
            />
            {jdTextError && (
              <p id="jd-text-error" className="text-sm text-destructive" role="alert">
                {jdTextError}
              </p>
            )}
            {jdTextSaved && (
              <p className="flex items-center gap-1 text-sm text-success">
                <CheckCircle2 className="h-3 w-3" /> Saved
              </p>
            )}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleJdTextSubmit}
              disabled={jdTextSaving || jdText.trim().length < 10}
            >
              {jdTextSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              {jdTextSaving ? "Saving..." : "Save Job Description"}
            </Button>
          </div>
        ) : (
          <>
            {!jdFile || jdFile.state === "idle" ? (
              <div
                {...jdDropzone.getRootProps()}
                className={cn(
                  "flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-6 text-center transition-all cursor-pointer",
                  jdDropzone.isDragActive
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-primary/50 hover:bg-accent/30",
                )}
              >
                <input {...jdDropzone.getInputProps()} aria-label="Upload job description" />
                <FileText className="h-8 w-8 text-muted-foreground" aria-hidden="true" />
                <p className="text-sm font-medium">
                  {jdDropzone.isDragActive
                    ? "Drop the file here"
                    : "Drag & drop JD (PDF, TXT, DOCX)"}
                </p>
              </div>
            ) : (
              <motion.div
                initial={{ opacity: 0, scale: 0.97 }}
                animate={{ opacity: 1, scale: 1 }}
                className={cn(
                  "flex items-center gap-3 rounded-lg border-2 p-4",
                  jdFile.state === "success" && "border-success-border bg-success-bg",
                  jdFile.state === "uploading" && "border-info-border bg-info-bg",
                  jdFile.state === "error" && "border-destructive/30 bg-destructive/5",
                )}
              >
                <FileIcon className="h-6 w-6 shrink-0 text-muted-foreground" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{jdFile.file.name}</p>
                  {jdFile.state === "error" && (
                    <p className="text-xs text-destructive">{jdFile.error}</p>
                  )}
                </div>
                {jdFile.state === "success" && <CheckCircle2 className="h-4 w-4 text-success" />}
                {jdFile.state === "uploading" && (
                  <Loader2 className="h-4 w-4 animate-spin text-info" />
                )}
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setJdFile(null);
                    setValue("job_description_id", null, { shouldDirty: true });
                  }}
                  aria-label="Remove job description"
                >
                  <X className="h-4 w-4" />
                </Button>
              </motion.div>
            )}
          </>
        )}
      </div>

      {/* Custom Instructions */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="custom_instructions">Custom Instructions (optional)</Label>
          <span className="text-xs text-muted-foreground">
            {customInstructions?.length ?? 0}/2000
          </span>
        </div>
        <Textarea
          id="custom_instructions"
          placeholder="Any specific topics, areas to focus on, or instructions for the AI interviewer..."
          rows={4}
          maxLength={2000}
          {...register("custom_instructions")}
        />
      </div>
    </div>
  );
});

// ── Helpers ────────────────────────────────────────────────────────────────

async function hashFile(file: File): Promise<string> {
  const buffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

async function checkMagicNumber(file: File, expectedMime: string): Promise<boolean> {
  const sig = MAGIC_NUMBERS[expectedMime];
  if (!sig) return true;
  if (file.size < sig.length) return false;
  const slice = await file.slice(0, sig.length).arrayBuffer();
  const bytes = new Uint8Array(slice);
  return sig.every((byte, i) => bytes[i] === byte);
}

function sanitizeFilename(name: string): string {
  return name
    .replace(/[/\\]/g, "_")
    .replace(/[\0-\x1f]/g, "")
    .slice(0, 255);
}

function sanitizeText(text: string): string {
  return text.replace(/\0/g, "").trim();
}
