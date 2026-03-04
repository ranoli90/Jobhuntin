import { Link, useLocation } from "react-router-dom";
import { ChevronRight, Home } from "lucide-react";
import { cn } from "../lib/utils";

interface BreadcrumbItem {
  label: string;
  path?: string;
}

interface BreadcrumbsProps {
  items?: BreadcrumbItem[];
  className?: string;
  homeLabel?: string;
}

const pathLabels: Record<string, string> = {
  "about": "About",
  "pricing": "Pricing",
  "blog": "Blog",
  "guides": "Guides",
  "contact": "Contact",
  "terms": "Terms",
  "privacy": "Privacy",
  "success-stories": "Success Stories",
  "chrome-extension": "Chrome Extension",
  "recruiters": "For Recruiters",
  "app": "Dashboard",
  "jobs": "Jobs",
  "applications": "Applications",
  "billing": "Billing",
  "settings": "Settings",
  "profile": "Profile",
  "onboarding": "Getting Started"
};

export function Breadcrumbs({ items, className, homeLabel = "Home" }: BreadcrumbsProps) {
  const location = useLocation();
  
  // Generate breadcrumbs from path if not provided
  const breadcrumbItems = items || (() => {
    const paths = location.pathname.split("/").filter(Boolean);
    const generated: BreadcrumbItem[] = [{ label: homeLabel, path: "/" }];
    
    let currentPath = "";
    paths.forEach((segment) => {
      currentPath += `/${segment}`;
      generated.push({
        label: pathLabels[segment] || segment.charAt(0).toUpperCase() + segment.slice(1).replace(/-/g, " "),
        path: currentPath
      });
    });
    
    return generated;
  })();

  // Don't show on home page
  if (breadcrumbItems.length <= 1) return null;

  return (
    <nav 
      aria-label="Breadcrumb" 
      className={cn("py-4 px-6", className)}
    >
      <ol className="flex items-center flex-wrap gap-2 text-sm">
        {breadcrumbItems.map((item, index) => {
          const isLast = index === breadcrumbItems.length - 1;
          const isFirst = index === 0;
          
          return (
            <li key={index} className="flex items-center">
              {index > 0 && (
                <ChevronRight className="w-4 h-4 mx-2 text-slate-400" aria-hidden="true" />
              )}
              
              {isLast || !item.path ? (
                <span 
                  className="font-medium text-slate-900 dark:text-slate-100"
                  aria-current="page"
                >
                  {isFirst && <Home className="w-4 h-4 inline mr-1" />}
                  {item.label}
                </span>
              ) : (
                <Link
                  to={item.path}
                  className={cn(
                    "font-medium text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 transition-colors",
                    isFirst && "flex items-center"
                  )}
                >
                  {isFirst && <Home className="w-4 h-4 inline mr-1" />}
                  {item.label}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

// Simplified version for pages
export function PageBreadcrumb({ 
  title, 
  parent,
  className 
}: { 
  title: string; 
  parent?: { label: string; path: string };
  className?: string;
}) {
  return (
    <Breadcrumbs
      items={[
        { label: "Home", path: "/" },
        ...(parent ? [parent] : []),
        { label: title }
      ]}
      className={className}
    />
  );
}

export default Breadcrumbs;
