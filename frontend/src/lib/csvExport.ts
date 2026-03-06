import type { Suggestion } from "@/types/api";

function escapeCSV(value: string): string {
  if (value.includes(",") || value.includes('"') || value.includes("\n")) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

export function suggestionsToCSV(results: Record<string, Suggestion[]>): string {
  const headers = [
    "source_url", "target_url", "anchor_text", "confidence_score",
    "match_reason", "risk_flags", "lexical", "semantic", "context",
    "quality", "context_snippet", "dom_path",
  ];

  const rows: string[] = [headers.join(",")];

  for (const suggestions of Object.values(results)) {
    for (const s of suggestions) {
      rows.push([
        escapeCSV(s.source_url),
        escapeCSV(s.target_url),
        escapeCSV(s.anchor_text),
        String(s.confidence_score),
        escapeCSV(s.match_reason),
        escapeCSV(s.risk_flags.join("; ")),
        String(s.scores.lexical),
        String(s.scores.semantic),
        String(s.scores.context),
        String(s.scores.quality),
        escapeCSV(s.context_snippet),
        escapeCSV(s.insertion_hint?.dom_path ?? ""),
      ].join(","));
    }
  }

  return rows.join("\n");
}

export function downloadFile(content: string, filename: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
