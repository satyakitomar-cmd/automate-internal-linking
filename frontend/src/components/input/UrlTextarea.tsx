import { Badge } from "@/components/ui/Badge";

interface UrlTextareaProps {
  value: string;
  onChange: (raw: string) => void;
  urlCount: number;
}

export function UrlTextarea({ value, onChange, urlCount }: UrlTextareaProps) {
  return (
    <div className="relative">
      <div className="absolute top-3 right-3 z-10">
        <Badge variant={urlCount >= 2 ? "info" : "default"}>
          {urlCount} URL{urlCount !== 1 ? "s" : ""}
        </Badge>
      </div>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={"Paste URLs here, one per line...\n\nhttps://example.com/page-1\nhttps://example.com/page-2\nhttps://example.com/page-3"}
        className="w-full h-52 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 pr-20 text-sm font-mono text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-y"
      />
    </div>
  );
}
