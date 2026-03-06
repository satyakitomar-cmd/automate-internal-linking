import { useState } from "react";
import { Slider } from "@/components/ui/Slider";
import type { PipelineConfig, SiteRules } from "@/types/api";

interface ConfigPanelProps {
  config: PipelineConfig;
  onConfigChange: (config: PipelineConfig) => void;
  siteRules: SiteRules;
  onSiteRulesChange: (rules: SiteRules) => void;
}

export function ConfigPanel({ config, onConfigChange, siteRules, onSiteRulesChange }: ConfigPanelProps) {
  const [open, setOpen] = useState(false);

  const updateConfig = (patch: Partial<PipelineConfig>) =>
    onConfigChange({ ...config, ...patch });
  const updateRules = (patch: Partial<SiteRules>) =>
    onSiteRulesChange({ ...siteRules, ...patch });

  const wl = config.weight_lexical ?? 0.35;
  const ws = config.weight_semantic ?? 0.35;
  const wc = config.weight_context ?? 0.15;
  const wq = config.weight_quality ?? 0.15;
  const weightSum = wl + ws + wc + wq;

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
      >
        <span>Advanced Settings</span>
        <svg
          className={`h-5 w-5 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-6 border-t border-gray-200 dark:border-gray-700 pt-4">
          {/* Pipeline Config */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Pipeline Config</h3>

            <Slider label="Score Threshold" value={config.score_threshold ?? 0.62} onChange={(v) => updateConfig({ score_threshold: v })} />
            <Slider label="MMR Lambda" value={config.mmr_lambda ?? 0.75} onChange={(v) => updateConfig({ mmr_lambda: v })} />

            <div className="flex items-center gap-3">
              <label className="text-sm text-gray-600 dark:text-gray-400">Max Suggestions / Source</label>
              <input
                type="number"
                min={1} max={20}
                value={config.max_suggestions_per_source ?? 5}
                onChange={(e) => updateConfig({ max_suggestions_per_source: parseInt(e.target.value) || 5 })}
                className="w-20 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2 py-1 text-sm"
              />
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Score Weights</span>
                <span className={`text-xs font-mono ${Math.abs(weightSum - 1) < 0.05 ? "text-green-600" : Math.abs(weightSum - 1) < 0.2 ? "text-yellow-600" : "text-red-600"}`}>
                  Sum: {weightSum.toFixed(2)}
                </span>
              </div>
              <Slider label="Lexical" value={wl} onChange={(v) => updateConfig({ weight_lexical: v })} />
              <Slider label="Semantic" value={ws} onChange={(v) => updateConfig({ weight_semantic: v })} />
              <Slider label="Context" value={wc} onChange={(v) => updateConfig({ weight_context: v })} />
              <Slider label="Quality" value={wq} onChange={(v) => updateConfig({ weight_quality: v })} />
            </div>
          </div>

          {/* Site Rules */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Site Rules</h3>

            <div className="flex items-center gap-3">
              <label className="text-sm text-gray-600 dark:text-gray-400">Max Links / Source Page</label>
              <input
                type="number" min={1} max={50}
                value={siteRules.max_links_per_source_page ?? 5}
                onChange={(e) => updateRules({ max_links_per_source_page: parseInt(e.target.value) || 5 })}
                className="w-20 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2 py-1 text-sm"
              />
            </div>

            <div className="flex items-center gap-3">
              <label className="text-sm text-gray-600 dark:text-gray-400 whitespace-nowrap">Anchor Length</label>
              <input
                type="number" min={1} max={10}
                value={siteRules.anchor_length_min_words ?? 2}
                onChange={(e) => updateRules({ anchor_length_min_words: parseInt(e.target.value) || 2 })}
                className="w-16 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2 py-1 text-sm"
              />
              <span className="text-gray-400">to</span>
              <input
                type="number" min={1} max={10}
                value={siteRules.anchor_length_max_words ?? 6}
                onChange={(e) => updateRules({ anchor_length_max_words: parseInt(e.target.value) || 6 })}
                className="w-16 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2 py-1 text-sm"
              />
              <span className="text-sm text-gray-500">words</span>
            </div>

            <div>
              <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">Avoid Sections</label>
              <input
                type="text"
                value={(siteRules.avoid_sections ?? ["Related Posts", "nav", "footer", "sidebar", "author bio", "comments"]).join(", ")}
                onChange={(e) => updateRules({ avoid_sections: e.target.value.split(",").map(s => s.trim()).filter(Boolean) })}
                className="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-1.5 text-sm"
              />
            </div>

            <div className="flex items-center gap-3">
              <label className="text-sm text-gray-600 dark:text-gray-400">Link Policy</label>
              <select
                value={siteRules.existing_link_policy ?? "skip"}
                onChange={(e) => updateRules({ existing_link_policy: e.target.value as "skip" | "allow_different_anchor" })}
                className="rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2 py-1 text-sm"
              >
                <option value="skip">Skip if already linked</option>
                <option value="allow_different_anchor">Allow different anchor</option>
              </select>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
