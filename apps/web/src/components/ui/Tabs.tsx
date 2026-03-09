import React from "react";

export const Tabs = ({ children, className = "", defaultValue, ...props }: { children: React.ReactNode; className?: string; defaultValue?: string; [key: string]: unknown }) => (
  <div className={`${className}`} data-default-value={defaultValue} {...props}>{children}</div>
);

export const TabsList = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
  <div className={`flex gap-1 border-b border-slate-200 mb-4 ${className}`}>{children}</div>
);

export const TabsTrigger = ({ children, value, className = "" }: { children: React.ReactNode; value: string; className?: string }) => (
  <button className={`px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 border-b-2 border-transparent hover:border-slate-300 transition-colors ${className}`} data-value={value}>{children}</button>
);

export const TabsContent = ({ children, value, className = "" }: { children: React.ReactNode; value: string; className?: string }) => (
  <div className={`${className}`} data-value={value}>{children}</div>
);
