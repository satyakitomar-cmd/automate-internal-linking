import { useCallback, useState } from "react";

interface FileUploadProps {
  onUrlsLoaded: (urls: string[]) => void;
}

export function FileUpload({ onUrlsLoaded }: FileUploadProps) {
  const [dragging, setDragging] = useState(false);

  const handleFile = useCallback(
    (file: File) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const text = e.target?.result as string;
        const urls = text
          .split(/[\r\n]+/)
          .map((l) => l.trim())
          .filter((l) => l && l.startsWith("http"));
        if (urls.length) onUrlsLoaded(urls);
      };
      reader.readAsText(file);
    },
    [onUrlsLoaded]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={`rounded-lg border-2 border-dashed p-4 text-center text-sm transition-colors cursor-pointer ${
        dragging
          ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
          : "border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-600"
      }`}
    >
      <input
        type="file"
        accept=".txt,.csv"
        className="hidden"
        id="url-file-upload"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />
      <label htmlFor="url-file-upload" className="cursor-pointer">
        <span className="text-gray-500 dark:text-gray-400">
          Drop a <strong>.txt</strong> or <strong>.csv</strong> file here, or{" "}
          <span className="text-blue-600 dark:text-blue-400 underline">browse</span>
        </span>
      </label>
    </div>
  );
}
