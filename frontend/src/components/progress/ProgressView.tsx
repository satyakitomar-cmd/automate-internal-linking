import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { ProgressBar } from "./ProgressBar";
import { ErrorList } from "./ErrorList";
import type { JobInfo, ParsedProgress } from "@/types/api";
import { cn } from "@/lib/cn";

interface ProgressViewProps {
  jobInfo: JobInfo | null;
}

const STAGES = [
  { id: "fetch", label: "Fetching Pages" },
  { id: "profile", label: "Profiling Documents" },
  { id: "candidates", label: "Building Graph" },
  { id: "analyze", label: "Analyzing Links" },
  { id: "done", label: "Complete" },
];

function parseProgress(raw: string): ParsedProgress {
  const match = raw.match(/^(\w+):\s*(\d+)%\s*[-–]\s*(.*)$/);
  if (!match) return { stage: "unknown", percentage: 0, detail: raw };
  return { stage: match[1], percentage: parseInt(match[2], 10), detail: match[3] };
}

function getStageIndex(stage: string): number {
  return STAGES.findIndex((s) => s.id === stage);
}

export function ProgressView({ jobInfo }: ProgressViewProps) {
  if (!jobInfo) {
    return (
      <Card className="flex flex-col items-center justify-center py-16 gap-4">
        <Spinner size="lg" />
        <p className="text-gray-500 dark:text-gray-400">Waiting for job to start...</p>
      </Card>
    );
  }

  if (jobInfo.status === "failed") {
    return (
      <Card className="space-y-4">
        <div className="text-center py-8">
          <div className="text-red-500 text-4xl mb-3">!</div>
          <h3 className="text-lg font-semibold text-red-700 dark:text-red-400">Analysis Failed</h3>
        </div>
        <ErrorList errors={jobInfo.errors} />
      </Card>
    );
  }

  const parsed = parseProgress(jobInfo.progress || "");
  const activeIdx = getStageIndex(parsed.stage);
  const stageLabel = STAGES[activeIdx]?.label || "Processing";

  return (
    <Card className="space-y-6">
      {/* Stepper */}
      <div className="flex items-center justify-between">
        {STAGES.map((stage, idx) => {
          const isActive = idx === activeIdx;
          const isDone = idx < activeIdx || jobInfo.status === "completed";
          return (
            <div key={stage.id} className="flex items-center flex-1 last:flex-none">
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    "h-8 w-8 rounded-full flex items-center justify-center text-xs font-bold transition-colors",
                    isDone
                      ? "bg-green-500 text-white"
                      : isActive
                        ? "bg-blue-600 text-white ring-4 ring-blue-100 dark:ring-blue-900"
                        : "bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400"
                  )}
                >
                  {isDone ? (
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    idx + 1
                  )}
                </div>
                <span className={cn(
                  "text-xs mt-1 hidden sm:block",
                  isActive ? "text-blue-600 dark:text-blue-400 font-medium" : "text-gray-400 dark:text-gray-500"
                )}>
                  {stage.label}
                </span>
              </div>
              {idx < STAGES.length - 1 && (
                <div className={cn(
                  "flex-1 h-0.5 mx-2",
                  isDone ? "bg-green-500" : "bg-gray-200 dark:bg-gray-700"
                )} />
              )}
            </div>
          );
        })}
      </div>

      {/* Progress Bar */}
      {jobInfo.status !== "completed" && (
        <ProgressBar percentage={parsed.percentage} stage={parsed.stage} label={stageLabel} />
      )}

      {/* Detail */}
      {parsed.detail && jobInfo.status !== "completed" && (
        <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
          {parsed.detail}
        </p>
      )}

      {/* Completed */}
      {jobInfo.status === "completed" && (
        <div className="text-center py-4">
          <p className="text-lg font-semibold text-green-600 dark:text-green-400">
            Analysis Complete
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {jobInfo.stats.total_suggestions} suggestions found across {jobInfo.stats.sources_with_suggestions} pages
            {" "}in {jobInfo.stats.elapsed_seconds?.toFixed(1)}s
          </p>
        </div>
      )}

      {/* Errors */}
      {jobInfo.errors.length > 0 && <ErrorList errors={jobInfo.errors} />}
    </Card>
  );
}
