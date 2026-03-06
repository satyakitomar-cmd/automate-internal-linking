import { cn } from "@/lib/cn";

interface ProgressBarProps {
  percentage: number;
  stage: string;
  label: string;
}

const stageColors: Record<string, string> = {
  fetch: "bg-blue-500",
  profile: "bg-indigo-500",
  candidates: "bg-purple-500",
  analyze: "bg-emerald-500",
  done: "bg-green-500",
};

export function ProgressBar({ percentage, stage, label }: ProgressBarProps) {
  const color = stageColors[stage] || "bg-blue-500";

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="font-medium text-gray-700 dark:text-gray-300">{label}</span>
        <span className="font-mono text-gray-500 dark:text-gray-400">{percentage}%</span>
      </div>
      <div className="h-3 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-500 ease-out", color)}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  );
}
