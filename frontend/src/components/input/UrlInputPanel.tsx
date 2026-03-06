import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { UrlTextarea } from "./UrlTextarea";
import { FileUpload } from "./FileUpload";
import { ConfigPanel } from "./ConfigPanel";
import type { PipelineConfig, SiteRules } from "@/types/api";

interface UrlInputPanelProps {
  rawUrls: string;
  onRawUrlsChange: (raw: string) => void;
  urls: string[];
  config: PipelineConfig;
  onConfigChange: (config: PipelineConfig) => void;
  siteRules: SiteRules;
  onSiteRulesChange: (rules: SiteRules) => void;
  onAnalyze: () => void;
  isSubmitting: boolean;
}

export function UrlInputPanel({
  rawUrls,
  onRawUrlsChange,
  urls,
  config,
  onConfigChange,
  siteRules,
  onSiteRulesChange,
  onAnalyze,
  isSubmitting,
}: UrlInputPanelProps) {
  const handleFileUrls = (fileUrls: string[]) => {
    const existing = rawUrls.trim();
    const newText = existing ? existing + "\n" + fileUrls.join("\n") : fileUrls.join("\n");
    onRawUrlsChange(newText);
  };

  return (
    <div className="space-y-6">
      <Card>
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
              Analyze URLs for Internal Linking
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Enter at least 2 URLs from the same site to discover internal linking opportunities.
            </p>
          </div>

          <UrlTextarea value={rawUrls} onChange={onRawUrlsChange} urlCount={urls.length} />
          <FileUpload onUrlsLoaded={handleFileUrls} />

          <div className="flex items-center justify-between pt-2">
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {urls.length < 2 ? "Need at least 2 valid URLs" : `${urls.length} URLs ready`}
            </span>
            <Button
              onClick={onAnalyze}
              disabled={urls.length < 2}
              loading={isSubmitting}
              size="lg"
            >
              Analyze Links
            </Button>
          </div>
        </div>
      </Card>

      <ConfigPanel
        config={config}
        onConfigChange={onConfigChange}
        siteRules={siteRules}
        onSiteRulesChange={onSiteRulesChange}
      />
    </div>
  );
}
