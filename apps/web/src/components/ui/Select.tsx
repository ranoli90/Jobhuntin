import React from "react";
export const Select = ({ children, value, onValueChange, ...props }: { children: React.ReactNode; value?: string; onValueChange?: (value: string) => void; [key: string]: unknown }) => (
  <div {...props}>{children}</div>
);
export const SelectTrigger = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
  <div className={`flex items-center justify-between px-3 py-2 border border-slate-200 rounded-lg cursor-pointer hover:border-slate-300 ${className}`}>{children}</div>
);
export const SelectValue = ({ placeholder }: { placeholder?: string }) => <span className="text-sm text-slate-500">{placeholder}</span>;
export const SelectContent = ({ children }: { children: React.ReactNode }) => <div className="mt-1 border border-slate-200 rounded-lg bg-white shadow-lg">{children}</div>;
export const SelectItem = ({ children, value }: { children: React.ReactNode; value: string }) => (
  <div className="px-3 py-2 text-sm hover:bg-slate-50 cursor-pointer" data-value={value}>{children}</div>
);
