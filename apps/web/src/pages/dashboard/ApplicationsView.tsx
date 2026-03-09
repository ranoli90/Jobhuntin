import { Briefcase as BriefcaseIcon, CheckCircle, Clock, Zap, Rocket, Radar, MoreVertical, Eye, Pause, Trash2, X } from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { useApplications } from "../../hooks/useApplications";
import { useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { getApiBase, getAuthHeaders } from "../../lib/api";
import { pushToast } from "../../lib/toast";
import { formatDate } from "../../lib/format";
import { t, formatT, getLocale } from "../../lib/i18n";
import { statusVariant } from "./shared";

const APPLICATIONS_PAGE_SIZE = 20;

import type { ApplicationRecord } from "../../hooks/useApplications";

function ActionsMenu({ app, onAction }: { app: ApplicationRecord; onAction: (action: string, appId: string) => void }) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleAction = (action: string) => {
    onAction(action, app.id);
    setIsOpen(false);
  };

  return (
    <div className="relative" ref={menuRef} onClick={(e) => e.stopPropagation()}>
      <Button
        variant="ghost"
        size="sm"
        className="h-8 w-8 p-0 hover:bg-slate-100"
        onClick={(e: React.MouseEvent<HTMLButtonElement>) => { e.stopPropagation(); setIsOpen(!isOpen); }}
        aria-label="Actions menu"
        aria-expanded={isOpen}
      >
        <MoreVertical className="w-4 h-4" />
      </Button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 top-full mt-1 w-48 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg z-50"
          >
            <div className="py-1">
              <button
                onClick={() => handleAction('view')}
                className="w-full px-3 py-2 text-left text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center gap-2"
              >
                <Eye className="w-4 h-4" />
                View Details
              </button>
              <button
                onClick={() => handleAction('reviewed')}
                className="w-full px-3 py-2 text-left text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center gap-2"
              >
                <CheckCircle className="w-4 h-4" />
                Mark as Reviewed
              </button>
              {app.status === 'HOLD' && (
                <button
                  onClick={() => handleAction('snooze')}
                  className="w-full px-3 py-2 text-left text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center gap-2"
                >
                  <Pause className="w-4 h-4" />
                  Snooze 24h
                </button>
              )}
              <button
                onClick={() => handleAction('withdraw')}
                className="w-full px-3 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                Withdraw
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function ApplicationsView() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { applications, isLoading, answerHold, snoozeApplication, isSubmitting } = useApplications();
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const locale = getLocale();
  const [displayedCount, setDisplayedCount] = useState(APPLICATIONS_PAGE_SIZE);

  const STATUS_FILTERS = [
    { label: 'All', value: null },
    { label: 'Applying', value: 'APPLYING' },
    { label: 'Applied', value: 'APPLIED' },
    { label: 'Hold', value: 'HOLD' },
    { label: 'Failed', value: 'FAILED' },
    { label: 'Rejected', value: 'REJECTED' },
  ] as const;

  const filteredApps = useMemo(
    () => applications.filter(app => {
      const matchesSearch = !searchTerm ||
        app.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
        app.job_title.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = !statusFilter || app.status === statusFilter;
      return matchesSearch && matchesStatus;
    }),
    [applications, searchTerm, statusFilter]
  );

  const loadMoreApps = filteredApps.slice(0, displayedCount);
  const hasMoreToLoad = displayedCount < filteredApps.length;

  useEffect(() => { setDisplayedCount(APPLICATIONS_PAGE_SIZE); }, [searchTerm, statusFilter]);

  const handleApplicationAction = useCallback(async (action: string, appId: string) => {
    try {
      switch (action) {
        case 'view':
          navigate(`/app/applications/${appId}`);
          break;
        case 'reviewed':
          await fetch(`${getApiBase()}/me/applications/${appId}/review`, {
            method: 'POST',
            headers: await getAuthHeaders(),
          });
          await queryClient.invalidateQueries({ queryKey: ["applications"] });
          pushToast({ title: "Marked as reviewed", description: "Application has been marked as reviewed.", tone: "success" });
          break;
        case 'snooze':
          await snoozeApplication(appId, 24);
          break;
        case 'withdraw':
          await fetch(`${getApiBase()}/me/applications/${appId}/withdraw`, {
            method: 'POST',
            headers: await getAuthHeaders(),
          });
          await queryClient.invalidateQueries({ queryKey: ["applications"] });
          pushToast({ title: "Application withdrawn", description: "The application has been withdrawn.", tone: "info" });
          break;
        default:
          if (import.meta.env.DEV) console.warn('Unknown action:', action);
      }
    } catch (error) {
      if (import.meta.env.DEV) console.error('Action failed:', error);
    }
  }, [navigate, snoozeApplication, queryClient]);

  if (isLoading) {
    return (
      <div className="space-y-6 max-w-6xl mx-auto pb-4" aria-busy="true" aria-label="Loading applications">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 md:gap-6">
          <div className="space-y-2">
            <div className="h-8 w-48 bg-slate-200 rounded animate-pulse" />
            <div className="h-4 w-64 bg-slate-100 rounded animate-pulse" />
          </div>
          <div className="h-12 w-full md:w-72 bg-slate-100 rounded-2xl animate-pulse" />
        </div>
        <div className="grid gap-3 md:hidden">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="p-4 rounded-2xl border border-slate-200 bg-white animate-pulse">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-slate-200" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-24 bg-slate-200 rounded" />
                  <div className="h-3 w-16 bg-slate-100 rounded" />
                </div>
                <div className="h-6 w-16 bg-slate-100 rounded" />
              </div>
              <div className="mt-3 h-4 w-20 bg-slate-100 rounded" />
            </div>
          ))}
        </div>
        <div className="hidden md:block p-0 overflow-hidden border border-slate-200 rounded-2xl">
          <div className="bg-slate-50 border-b border-slate-200 px-6 py-4">
            <div className="h-4 w-32 bg-slate-200 rounded" />
          </div>
          <div className="divide-y divide-slate-100">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="px-6 py-4 flex items-center gap-4">
                <div className="h-10 w-10 rounded-lg bg-slate-200 animate-pulse" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-32 bg-slate-200 rounded" />
                  <div className="h-3 w-24 bg-slate-100 rounded" />
                </div>
                <div className="h-6 w-20 bg-slate-100 rounded" />
                <div className="h-4 w-16 bg-slate-100 rounded" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-4">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 md:gap-6">
        <div>
          <h2 className="text-2xl md:text-3xl font-black text-slate-900 tracking-tight">Active Applications</h2>
          <p id="applications-search-hint" className="text-slate-500 font-medium">Tracking {applications.length} automated application threads.</p>
        </div>
        <div className="relative w-full md:w-72">
          <input
            type="text"
            placeholder="Search company or title..."
            aria-label="Search applications by company or title"
            aria-describedby="applications-search-hint"
            className="w-full px-10 py-3 rounded-2xl border border-brand-border text-sm focus:ring-2 focus:ring-brand-primary/20 focus:border-brand-primary transition-all bg-white dark:bg-slate-900 dark:border-slate-700 dark:text-slate-100 font-medium shadow-sm pr-8"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <BriefcaseIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
              aria-label="Clear search"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Status filter tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1 no-scrollbar">
        {STATUS_FILTERS.map(({ label, value }) => (
          <button
            key={label}
            onClick={() => setStatusFilter(value)}
            className={`px-3 py-1.5 rounded-full text-xs font-bold whitespace-nowrap transition-all border ${statusFilter === value
              ? 'bg-slate-900 text-white border-slate-900'
              : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300 hover:bg-slate-50'
              }`}
          >
            {label}
            {value !== null && (
              <span className="ml-1.5 text-[10px] opacity-60">
                ({applications.filter(a => a.status === value).length})
              </span>
            )}
          </button>
        ))}
      </div>

      <div className="grid gap-3 md:hidden">
        {loadMoreApps.length === 0 ? (
          <Card className="flex flex-col items-center justify-center p-8 text-center" shadow="sm">
            <div className="w-16 h-16 rounded-full bg-slate-50 flex items-center justify-center mb-4">
              <Radar className="w-8 h-8 text-slate-500 animate-pulse" />
            </div>
            <h3 className="text-lg font-black text-slate-900 mb-2">{t("applications.noResults", locale)}</h3>
            <p className="text-slate-500 font-medium mb-6 max-w-xs">
              {searchTerm ? t("applications.searchNoResults", locale) : t("applications.emptyDescription", locale)}
            </p>
            {!searchTerm && (
              <Button onClick={() => navigate('/app/jobs')} className="font-bold text-xs uppercase rounded-xl">
                {t("applications.startSearching", locale)} <Rocket className="ml-2 w-4 h-4" />
              </Button>
            )}
          </Card>
        ) : (
          loadMoreApps.map((app) => (
            <Card key={app.id} className="p-4 border-slate-200" shadow="sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-slate-900 flex items-center justify-center text-white font-bold text-sm shadow-sm">
                  {app.company.charAt(0)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-slate-900">{app.company}</p>
                  <p className="text-xs text-slate-500 font-medium truncate">{app.job_title}</p>
                </div>
                <Badge
                  variant={statusVariant(app.status)}
                  className="rounded-lg px-3 py-1 font-bold text-[10px] tracking-wider uppercase border-none"
                >
                  {app.status === 'APPLYING' && <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse mr-2" />}
                  {app.status}
                </Badge>
              </div>
              <div className="mt-3 flex items-center justify-between text-sm text-slate-600">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-slate-500" />
                  {app.last_activity ? formatDate(app.last_activity, locale) : 'Just now'}
                </div>
                <ActionsMenu app={app} onAction={handleApplicationAction} />
              </div>
            </Card>
          ))
        )}
      </div>

      <Card className="p-0 overflow-hidden border-slate-200 hidden md:block" shadow="sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <caption className="sr-only">Your job applications</caption>
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th scope="col" className="px-6 py-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">Company & Role</th>
                <th scope="col" className="px-6 py-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">Status</th>
                <th scope="col" className="px-6 py-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">Last Activity</th>
                <th scope="col" className="px-6 py-4 text-[10px] font-black text-slate-500 uppercase tracking-widest text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {loadMoreApps.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-24 text-center">
                    <div className="flex flex-col items-center justify-center">
                      <div className="w-12 h-12 rounded-full border-2 border-slate-200 flex items-center justify-center mb-6">
                        <BriefcaseIcon className="w-5 h-5 text-slate-400" />
                      </div>
                      <h3 className="text-lg font-semibold text-slate-900 mb-1">
                        {t("applications.noActiveApplications", locale)}
                      </h3>
                      <p className="text-sm text-slate-500 mb-6 max-w-xs text-center">
                        {searchTerm ? t("applications.searchNoResultsDesktop", locale) : t("applications.emptyDesktopDescription", locale)}
                      </p>
                      {!searchTerm && (
                        <Button onClick={() => navigate('/app/jobs')} className="text-sm font-medium bg-slate-900 hover:bg-slate-800 text-white rounded-lg px-5 py-2.5 transition-colors">
                          Browse jobs
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ) : (
                loadMoreApps.map((app) => (
                  <tr
                    key={app.id}
                    className="group hover:bg-slate-50/50 transition-colors cursor-pointer"
                    tabIndex={0}
                    role="button"
                    aria-label={`View details for ${app.company} - ${app.job_title}`}
                    onClick={() => navigate(`/app/applications/${app.id}`)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        navigate(`/app/applications/${app.id}`);
                      }
                    }}
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-lg bg-slate-900 flex items-center justify-center text-white font-bold text-sm shadow-sm">
                          {app.company.charAt(0)}
                        </div>
                        <div>
                          <p className="font-bold text-brand-text group-hover:text-brand-primary transition-colors">{app.company}</p>
                          <p className="text-xs text-slate-500 font-medium">{app.job_title}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <Badge
                        variant={statusVariant(app.status)}
                        className="rounded-lg px-3 py-1 font-bold text-[10px] tracking-wider uppercase border-none"
                      >
                        {app.status === 'APPLYING' && <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse mr-2" />}
                        {app.status}
                      </Badge>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2 text-sm text-slate-600 font-medium">
                        <Clock className="w-4 h-4 text-slate-500" />
                        {app.last_activity ? formatDate(app.last_activity, locale) : 'Just now'}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <ActionsMenu app={app} onAction={handleApplicationAction} />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {filteredApps.length > 0 && (
        <div className="flex items-center justify-between flex-wrap gap-3">
          <p className="text-xs text-slate-500 font-medium" aria-live="polite">
            {formatT("dashboard.showingApplications", { count: loadMoreApps.length, total: filteredApps.length }, locale)}
          </p>
          {hasMoreToLoad ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setDisplayedCount(c => Math.min(c + APPLICATIONS_PAGE_SIZE, filteredApps.length))}
              className="text-xs font-bold"
            >
              {t("applications.loadMore", locale)}
            </Button>
          ) : null}
        </div>
      )}

      <div className="p-4 bg-brand-primary/10 rounded-2xl border border-brand-primary/20 flex items-center gap-4">
        <div className="h-10 w-10 rounded-full bg-white flex items-center justify-center text-brand-primary shadow-sm flex-shrink-0">
          <Zap className="h-5 w-5" />
        </div>
        <p className="text-sm text-primary-900 font-medium font-display leading-tight">
          {t("dashboard.aiAgentMonitoring", locale)} <span className="font-black">{t("dashboard.aiAgentMonitoringNewListings", locale)}</span> {t("dashboard.aiAgentMonitoringSource", locale)}
        </p>
      </div>
    </div>
  );
}
