import { cn } from "@/lib/cn";
import type { JobStatus } from "@/types/api";

export type Tab = "input" | "progress" | "results";

interface TabNavProps {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
  jobId: string | null;
  jobStatus: JobStatus | null;
}

const tabs: { id: Tab; label: string }[] = [
  { id: "input", label: "Input" },
  { id: "progress", label: "Progress" },
  { id: "results", label: "Results" },
];

export function TabNav({ activeTab, onTabChange, jobId, jobStatus }: TabNavProps) {
  const isEnabled = (tab: Tab) => {
    if (tab === "input") return true;
    if (tab === "progress") return jobId !== null;
    if (tab === "results") return jobStatus === "completed";
    return false;
  };

  return (
    <div className="border-b border-gray-200 dark:border-gray-800">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <nav className="flex gap-1" aria-label="Tabs">
          {tabs.map((tab) => {
            const enabled = isEnabled(tab.id);
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => enabled && onTabChange(tab.id)}
                disabled={!enabled}
                className={cn(
                  "px-4 py-3 text-sm font-medium border-b-2 transition-colors",
                  active
                    ? "border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400"
                    : "border-transparent text-gray-500 dark:text-gray-400",
                  enabled && !active && "hover:text-gray-700 hover:border-gray-300 dark:hover:text-gray-300",
                  !enabled && "opacity-40 cursor-not-allowed"
                )}
              >
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
