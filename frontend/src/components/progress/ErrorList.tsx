interface ErrorListProps {
  errors: string[];
}

export function ErrorList({ errors }: ErrorListProps) {
  if (!errors.length) return null;

  return (
    <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4">
      <h4 className="text-sm font-medium text-red-800 dark:text-red-400 mb-2">
        Warnings ({errors.length})
      </h4>
      <ul className="space-y-1">
        {errors.map((err, i) => (
          <li key={i} className="text-sm text-red-700 dark:text-red-300">
            {err}
          </li>
        ))}
      </ul>
    </div>
  );
}
