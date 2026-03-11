import React, { useEffect, useState } from "react";
import DOMPurify from "dompurify";

interface LazyMarkdownProps {
  content: string;
  className?: string;
}

/**
 * Renders markdown content by dynamically importing `marked` only when needed.
 * Keeps the marked library out of the main bundle.
 */
export function LazyMarkdown({ content, className }: LazyMarkdownProps) {
  const [html, setHtml] = useState<string | null>(null);

  useEffect(() => {
    import("marked").then(({ marked }) => {
      marked.setOptions({ gfm: true });
      const parsed = marked.parse(content, { async: false }) as string;
      setHtml(DOMPurify.sanitize(parsed));
    });
  }, [content]);

  if (html === null) {
    return (
      <div className={className} aria-busy="true">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-3/4" />
          <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-full" />
          <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-5/6" />
        </div>
      </div>
    );
  }

  return (
    <div
      className={className}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
