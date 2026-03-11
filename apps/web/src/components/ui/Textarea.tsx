import React from "react";
export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement> & { className?: string }
>(({ className = "", ...properties }, reference) => (
  <textarea
    ref={reference}
    className={`w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 ${className}`}
    {...properties}
  />
));
Textarea.displayName = "Textarea";
