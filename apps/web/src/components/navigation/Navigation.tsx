import React, { useState, useEffect } from "react";
import { cn } from "@/lib/utils";

interface NavigationProperties {
  className?: string;
  variant?: "header" | "sidebar" | "footer";
  orientation?: "horizontal" | "vertical";
}

interface NavItemProperties {
  href?: string;
  onClick?: () => void;
  children: React.ReactNode;
  icon?: React.ReactNode;
  badge?: string;
  isActive?: boolean;
  disabled?: boolean;
}

interface NavSectionProperties {
  title?: string;
  children: React.ReactNode;
  className?: string;
}

const NavItem: React.FC<NavItemProperties> = ({
  href,
  onClick,
  children,
  icon,
  badge,
  isActive = false,
  disabled = false,
}) => {
  const Component = href ? "a" : "button";

  return (
    <Component
      href={href}
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors",
        "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2",
        isActive
          ? "bg-blue-100 text-blue-700"
          : disabled
            ? "text-gray-400 cursor-not-allowed"
            : "text-gray-600 hover:text-gray-900 hover:bg-gray-50",
      )}
    >
      {icon && <span className="mr-3 text-gray-500">{icon}</span>}
      <span className="flex-1">{children}</span>
      {badge && (
        <span className="ml-2 bg-blue-600 text-white text-xs px-2 py-1 rounded-full">
          {badge}
        </span>
      )}
    </Component>
  );
};

const NavSection: React.FC<NavSectionProperties> = ({
  title,
  children,
  className,
}) => {
  return (
    <div className={cn("space-y-1", className)}>
      {title && (
        <h3 className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">
          {title}
        </h3>
      )}
      {children}
    </div>
  );
};

const Navigation: React.FC<NavigationProperties> = ({
  className,
  variant = "header",
  orientation = "horizontal",
}) => {
  const [activeItem, setActiveItem] = useState<string>("dashboard");
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    if (variant === "header") {
      const handleScroll = () => {
        setIsScrolled(window.scrollY > 10);
      };
      window.addEventListener("scroll", handleScroll);
      return () => window.removeEventListener("scroll", handleScroll);
    }
  }, [variant]);

  const handleItemClick = (item: string, onClick?: () => void) => {
    setActiveItem(item);
    onClick?.();
  };

  if (variant === "header") {
    return (
      <nav
        className={cn(
          "sticky top-0 z-50 bg-white border-b border-gray-200 transition-all duration-200",
          isScrolled && "shadow-sm",
          className,
        )}
      >
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center mr-3">
                <span className="text-white font-bold text-sm">JH</span>
              </div>
              <span className="text-xl font-bold text-gray-900">JobHuntin</span>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-1">
              <NavItem
                href="/app/dashboard"
                onClick={() => handleItemClick("dashboard")}
                isActive={activeItem === "dashboard"}
                icon={
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
                    />
                  </svg>
                }
              >
                Dashboard
              </NavItem>

              <NavItem
                href="/app/jobs"
                onClick={() => handleItemClick("jobs")}
                isActive={activeItem === "jobs"}
                badge="New"
                icon={
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M21 13.255A9.957 9.957 0 0112 21a9.957 9.957 0 01-9-7.745M21 13.255V16a2 2 0 01-2 2H5a2 2 0 01-2-2v-2.745M21 13.255A9.957 9.957 0 0012 21a9.957 9.957 0 00-9-7.745M21 13.255A9.957 9.957 0 0012 21a9.957 9.957 0 00-9-7.745"
                    />
                  </svg>
                }
              >
                Jobs
              </NavItem>

              <NavItem
                href="/app/applications"
                onClick={() => handleItemClick("applications")}
                isActive={activeItem === "applications"}
                badge="3"
                icon={
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                }
              >
                Applications
              </NavItem>

              <NavItem
                href="/app/settings"
                onClick={() => handleItemClick("resume")}
                isActive={activeItem === "resume"}
                icon={
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                }
              >
                Resume
              </NavItem>

              <NavItem
                href="/app/dashboard"
                onClick={() => handleItemClick("interviews")}
                isActive={activeItem === "interviews"}
                icon={
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                    />
                  </svg>
                }
              >
                Interviews
              </NavItem>
            </div>

            {/* User Menu */}
            <div className="hidden md:flex items-center space-x-3">
              <button className="p-2 rounded-lg hover:bg-gray-100 transition-colors">
                <svg
                  className="w-5 h-5 text-gray-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  />
                </svg>
              </button>

              <div className="flex items-center">
                <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                  <svg
                    className="w-4 h-4 text-gray-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                    />
                  </svg>
                </div>
              </div>
            </div>

            {/* Mobile Menu Button */}
            <div className="md:hidden">
              <button className="p-2 rounded-lg hover:bg-gray-100 transition-colors">
                <svg
                  className="w-6 h-6 text-gray-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </nav>
    );
  }

  if (variant === "sidebar") {
    return (
      <nav
        className={cn(
          "w-64 bg-white border-r border-gray-200 h-full overflow-y-auto",
          className,
        )}
      >
        <div className="p-6">
          <div className="flex items-center mb-8">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center mr-3">
              <span className="text-white font-bold text-sm">JH</span>
            </div>
            <span className="text-xl font-bold text-gray-900">JobHuntin</span>
          </div>

          <div className="space-y-6">
            <NavSection>
              <NavItem
                href="/app/dashboard"
                onClick={() => handleItemClick("dashboard")}
                isActive={activeItem === "dashboard"}
                icon={
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
                    />
                  </svg>
                }
              >
                Dashboard
              </NavItem>

              <NavItem
                href="/app/jobs"
                onClick={() => handleItemClick("jobs")}
                isActive={activeItem === "jobs"}
                badge="New"
                icon={
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M21 13.255A9.957 9.957 0 0112 21a9.957 9.957 0 01-9-7.745M21 13.255V16a2 2 0 01-2 2H5a2 2 0 01-2-2v-2.745M21 13.255A9.957 9.957 0 0012 21a9.957 9.957 0 00-9-7.745M21 13.255A9.957 9.957 0 0012 21a9.957 9.957 0 00-9-7.745"
                    />
                  </svg>
                }
              >
                Job Search
              </NavItem>

              <NavItem
                href="/app/applications"
                onClick={() => handleItemClick("applications")}
                isActive={activeItem === "applications"}
                badge="3"
                icon={
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                }
              >
                Applications
              </NavItem>

              <NavItem
                href="/app/settings"
                onClick={() => handleItemClick("resume")}
                isActive={activeItem === "resume"}
                icon={
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                }
              >
                Resume Builder
              </NavItem>

              <NavItem
                href="/app/dashboard"
                onClick={() => handleItemClick("interviews")}
                isActive={activeItem === "interviews"}
                icon={
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                    />
                  </svg>
                }
              >
                Interview Prep
              </NavItem>
            </NavSection>

            <NavSection title="Tools">
              <NavItem
                href="/app/tailor"
                onClick={() => handleItemClick("ai-coach")}
                isActive={activeItem === "ai-coach"}
                badge="Pro"
                icon={
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                    />
                  </svg>
                }
              >
                AI Career Coach
              </NavItem>

              <NavItem
                href="/app/dashboard"
                onClick={() => handleItemClick("analytics")}
                isActive={activeItem === "analytics"}
                icon={
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                    />
                  </svg>
                }
              >
                Analytics
              </NavItem>
            </NavSection>

            <NavSection title="Settings">
              <NavItem
                href="/app/settings"
                onClick={() => handleItemClick("settings")}
                isActive={activeItem === "settings"}
                icon={
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                }
              >
                Settings
              </NavItem>

              <NavItem
                href="/app/settings"
                onClick={() => handleItemClick("help")}
                isActive={activeItem === "help"}
                icon={
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                }
              >
                Help & Support
              </NavItem>
            </NavSection>
          </div>
        </div>
      </nav>
    );
  }

  if (variant === "footer") {
    return (
      <nav className={cn("border-t border-gray-200 bg-white", className)}>
        <div className="container mx-auto px-4 py-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-4">
                Product
              </h3>
              <ul className="space-y-2">
                <li>
                  <a
                    href="/features"
                    className="text-sm text-gray-600 hover:text-gray-900"
                  >
                    Features
                  </a>
                </li>
                <li>
                  <a
                    href="/pricing"
                    className="text-sm text-gray-600 hover:text-gray-900"
                  >
                    Pricing
                  </a>
                </li>
                <li>
                  <a
                    href="/integrations"
                    className="text-sm text-gray-600 hover:text-gray-900"
                  >
                    Integrations
                  </a>
                </li>
              </ul>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-4">
                Resources
              </h3>
              <ul className="space-y-2">
                <li>
                  <a
                    href="/blog"
                    className="text-sm text-gray-600 hover:text-gray-900"
                  >
                    Blog
                  </a>
                </li>
                <li>
                  <a
                    href="/guides"
                    className="text-sm text-gray-600 hover:text-gray-900"
                  >
                    Guides
                  </a>
                </li>
                <li>
                  <a
                    href="/api"
                    className="text-sm text-gray-600 hover:text-gray-900"
                  >
                    API Docs
                  </a>
                </li>
              </ul>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-4">
                Company
              </h3>
              <ul className="space-y-2">
                <li>
                  <a
                    href="/about"
                    className="text-sm text-gray-600 hover:text-gray-900"
                  >
                    About
                  </a>
                </li>
                <li>
                  <a
                    href="/careers"
                    className="text-sm text-gray-600 hover:text-gray-900"
                  >
                    Careers
                  </a>
                </li>
                <li>
                  <a
                    href="/contact"
                    className="text-sm text-gray-600 hover:text-gray-900"
                  >
                    Contact
                  </a>
                </li>
              </ul>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-4">
                Legal
              </h3>
              <ul className="space-y-2">
                <li>
                  <a
                    href="/privacy"
                    className="text-sm text-gray-600 hover:text-gray-900"
                  >
                    Privacy Policy
                  </a>
                </li>
                <li>
                  <a
                    href="/terms"
                    className="text-sm text-gray-600 hover:text-gray-900"
                  >
                    Terms of Service
                  </a>
                </li>
                <li>
                  <a
                    href="/security"
                    className="text-sm text-gray-600 hover:text-gray-900"
                  >
                    Security
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </nav>
    );
  }

  return null;
};

export { Navigation, NavItem, NavSection };
export default Navigation;
