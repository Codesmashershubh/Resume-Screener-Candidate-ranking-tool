import { useCallback, useRef, useState } from "react";
import { Upload, X, FileText } from "lucide-react";

interface ResumeDropzoneProps {
  files: File[];
  onChange: (files: File[]) => void;
  maxFiles: number;
  maxSizeBytes: number;
}

const ACCEPTED_EXTENSIONS = [".pdf", ".docx", ".txt"];

export function ResumeDropzone({ files, onChange, maxFiles, maxSizeBytes }: ResumeDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [rejectionNote, setRejectionNote] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = useCallback(
    (incoming: FileList | File[]) => {
      const incomingArr = Array.from(incoming);
      const accepted: File[] = [];
      const rejected: string[] = [];

      for (const file of incomingArr) {
        const ext = "." + (file.name.split(".").pop() || "").toLowerCase();
        if (!ACCEPTED_EXTENSIONS.includes(ext)) {
          rejected.push(`${file.name} (unsupported type)`);
          continue;
        }
        if (file.size > maxSizeBytes) {
          rejected.push(`${file.name} (over ${(maxSizeBytes / 1_048_576).toFixed(0)} MB)`);
          continue;
        }
        accepted.push(file);
      }

      const combined = [...files, ...accepted];
      const overflow = combined.length - maxFiles;
      const finalFiles = overflow > 0 ? combined.slice(0, maxFiles) : combined;

      const notes: string[] = [];
      if (rejected.length) notes.push(`Skipped: ${rejected.join(", ")}`);
      if (overflow > 0) notes.push(`Only the first ${maxFiles} files were kept (batch limit).`);
      setRejectionNote(notes.length ? notes.join(" ") : null);

      onChange(finalFiles);
    },
    [files, onChange, maxFiles, maxSizeBytes],
  );

  function removeFile(index: number) {
    onChange(files.filter((_, i) => i !== index));
  }

  return (
    <div>
      <h3 className="font-display text-lg font-medium text-ink mb-3">Resumes</h3>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          if (e.dataTransfer.files.length) addFiles(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
        className={`rounded-3xl border-2 border-dashed p-8 text-center cursor-pointer transition-colors ${
          isDragging ? "border-ink bg-slate-50" : "border-slate-200 bg-white hover:border-slate-300"
        }`}
      >
        <Upload size={22} className="mx-auto text-slate-300 mb-3" />
        <p className="text-[13px] text-ink font-medium">Drop resumes here, or click to browse</p>
        <p className="text-[12px] text-muted mt-1">
          PDF, DOCX or TXT &middot; up to {maxFiles} files &middot; {(maxSizeBytes / 1_048_576).toFixed(0)} MB each
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPTED_EXTENSIONS.join(",")}
          onChange={(e) => e.target.files && addFiles(e.target.files)}
          className="hidden"
        />
      </div>

      {rejectionNote && <p className="text-[12px] text-amber-700 mt-2">{rejectionNote}</p>}

      {files.length > 0 && (
        <ul className="mt-4 space-y-2">
          {files.map((file, i) => (
            <li
              key={`${file.name}-${i}`}
              className="flex items-center justify-between gap-3 bg-white border border-slate-200/70 rounded-2xl px-4 py-2.5"
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <FileText size={15} className="text-slate-400 shrink-0" />
                <span className="text-[13px] text-ink truncate">{file.name}</span>
                <span className="text-[11px] text-slate-400 shrink-0 font-mono">
                  {(file.size / 1024).toFixed(0)} KB
                </span>
              </div>
              <button
                type="button"
                onClick={() => removeFile(i)}
                aria-label={`Remove ${file.name}`}
                className="text-slate-300 hover:text-ink transition-colors shrink-0"
              >
                <X size={15} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
