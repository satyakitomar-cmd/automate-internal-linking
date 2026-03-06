import { useState, useCallback } from "react";
import { ThemeProvider } from "@/context/ThemeContext";
import { Header } from "@/components/layout/Header";
import { TabNav, type Tab } from "@/components/layout/TabNav";
import { Footer } from "@/components/layout/Footer";
import { UrlInputPanel } from "@/components/input/UrlInputPanel";
import { ProgressView } from "@/components/progress/ProgressView";
import { ResultsDashboard } from "@/components/results/ResultsDashboard";
import { useJobPoller } from "@/hooks/useJobPoller";
import { apiClient } from "@/api/client";
import type { PipelineConfig, SiteRules, JobInfo } from "@/types/api";

function parseUrls(raw: string): string[] {
  return raw
    .split(/[\r\n]+/)
    .map((l) => l.trim())
    .filter((l) => l && /^https?:\/\//i.test(l))
    .filter((l, i, arr) => arr.indexOf(l) === i); // dedupe
}

function AppInner() {
  const [activeTab, setActiveTab] = useState<Tab>("input");
  const [rawUrls, setRawUrls] = useState("");
  const [config, setConfig] = useState<PipelineConfig>({});
  const [siteRules, setSiteRules] = useState<SiteRules>({});
  const [jobId, setJobId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const urls = parseUrls(rawUrls);

  const handleCompleted = useCallback((job: JobInfo) => {
    setActiveTab("results");
  }, []);

  const { jobInfo } = useJobPoller(jobId, {
    onCompleted: handleCompleted,
  });

  const handleAnalyze = async () => {
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const body: { urls: string[]; config?: PipelineConfig; site_rules?: SiteRules } = { urls };
      if (Object.keys(config).length) body.config = config;
      if (Object.keys(siteRules).length) body.site_rules = siteRules;

      const result = await apiClient.analyze(body);
      setJobId(result.job_id);
      setActiveTab("progress");
    } catch (err) {
      setSubmitError(String(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <TabNav
        activeTab={activeTab}
        onTabChange={setActiveTab}
        jobId={jobId}
        jobStatus={jobInfo?.status ?? null}
      />

      <main className="flex-1 mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === "input" && (
          <div>
            <UrlInputPanel
              rawUrls={rawUrls}
              onRawUrlsChange={setRawUrls}
              urls={urls}
              config={config}
              onConfigChange={setConfig}
              siteRules={siteRules}
              onSiteRulesChange={setSiteRules}
              onAnalyze={handleAnalyze}
              isSubmitting={isSubmitting}
            />
            {submitError && (
              <div className="mt-4 p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-300">
                {submitError}
              </div>
            )}
          </div>
        )}

        {activeTab === "progress" && (
          <ProgressView jobInfo={jobInfo} />
        )}

        {activeTab === "results" && jobInfo?.status === "completed" && (
          <ResultsDashboard jobInfo={jobInfo} />
        )}
      </main>

      <Footer />
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AppInner />
    </ThemeProvider>
  );
}
