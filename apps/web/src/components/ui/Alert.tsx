import React from "react";
export const Alert = ({
  children,
  className = "",
  variant,
}: {
  children: React.ReactNode;
  className?: string;
  variant?: string;
}) => (
  <div
    className={`p-4 rounded-lg border ${variant === "destructive" ? "bg-red-50 border-red-200 text-red-800" : "bg-slate-50 border-slate-200"} ${className}`}
  >
    {children}
  </div>
);
export const AlertDescription = ({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) => <p className={`text-sm ${className}`}>{children}</p>;
