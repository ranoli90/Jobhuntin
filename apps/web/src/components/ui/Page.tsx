import * as React from "react";
import { Helmet } from "react-helmet-async";

interface PageProperties {
  title?: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}

export function Page({
  title,
  description,
  children,
  className,
}: PageProperties) {
  return (
    <>
      {title && (
        <Helmet>
          <title>{title}</title>
          {description && <meta name="description" content={description} />}
        </Helmet>
      )}
      <div className={className}>{children}</div>
    </>
  );
}
