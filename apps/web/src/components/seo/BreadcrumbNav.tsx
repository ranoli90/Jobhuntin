import React from "react";
import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import type { BreadcrumbItem } from "../marketing/SEO";

interface BreadcrumbNavProperties {
  items: BreadcrumbItem[];
  className?: string;
}

/** Renders visual breadcrumb navigation from SEO breadcrumb items. SEO #55 */
export function BreadcrumbNav({
  items,
  className = "",
}: BreadcrumbNavProperties) {
  if (!items || items.length <= 1) return null;

  return (
    <nav
      aria-label="Breadcrumb"
      className={`mb-6 text-sm text-slate-500 dark:text-slate-400 ${className}`}
    >
      <ol className="flex flex-wrap items-center gap-2">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          const href = item.url.startsWith("http")
            ? item.url
            : `https://jobhuntin.com${item.url.startsWith("/") ? "" : "/"}${item.url}`;
          const path = href.startsWith("http")
            ? new URL(href).pathname || "/"
            : (item.url.startsWith("/")
              ? item.url
              : `/${item.url}`);

          return (
            <li key={index} className="flex items-center gap-2">
              {index > 0 && (
                <ChevronRight
                  className="w-4 h-4 text-slate-400 shrink-0"
                  aria-hidden
                />
              )}
              {isLast ? (
                <span
                  className="font-medium text-slate-700 dark:text-slate-300"
                  aria-current="page"
                >
                  {item.name}
                </span>
              ) : (
                <Link
                  to={path}
                  className="hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
                >
                  {item.name}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
