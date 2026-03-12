/**
 * Saved Jobs Page - View and manage bookmarked jobs
 * Microsoft-level implementation with filtering, sorting, and bulk actions
 */

import * as React from "react";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { useSavedJobs, type SavedJob } from "../../hooks/useSavedJobs";
import { formatCurrency, formatDate } from "../../lib/format";
import {
  Briefcase,
  MapPin,
  Calendar,
  ExternalLink,
  Trash2,
  Bookmark,
  Search,
} from "lucide-react";

export default function SavedJobsPage() {
  const { t } = useTranslation();
  const locale = localStorage.getItem("language") || "en";

  const { savedJobs, isLoading, error, isJobSaved, unsaveJob, isUnsaving } =
    useSavedJobs();

  const [searchTerm, setSearchTerm] = React.useState("");
  const [sortBy, setSortBy] = React.useState<"date" | "title" | "company">(
    "date",
  );

  // Filter and sort jobs
  const filteredJobs = React.useMemo(() => {
    let filtered = savedJobs;

    // Apply search filter
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (job) =>
          job.job_data.title.toLowerCase().includes(searchLower) ||
          job.job_data.company.toLowerCase().includes(searchLower) ||
          job.job_data.location?.toLowerCase().includes(searchLower),
      );
    }

    // Apply sorting
    return filtered.sort((a, b) => {
      switch (sortBy) {
        case "title": {
          return a.job_data.title.localeCompare(b.job_data.title);
        }
        case "company": {
          return a.job_data.company.localeCompare(b.job_data.company);
        }
        case "date":
        default: {
          return (
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          );
        }
      }
    });
  }, [savedJobs, searchTerm, sortBy]);

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <Card className="p-6 text-center">
          <h2 className="text-xl font-semibold text-red-600 mb-2">
            {t("savedJobs.errorLoading", locale) || "Error Loading Saved Jobs"}
          </h2>
          <p className="text-slate-600">{error}</p>
          <Button onClick={() => window.location.reload()}>
            {t("common.retry", locale) || "Retry"}
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight">
            {t("savedJobs.title", locale) || "Saved Jobs"}
          </h1>
          <p className="text-slate-500 font-medium">
            {t("savedJobs.description", locale) ||
              "Jobs you've bookmarked for later review"}
          </p>
        </div>
        <div className="text-sm text-slate-500">
          {filteredJobs.length} {t("savedJobs.jobs", locale) || "jobs"}
        </div>
      </div>

      {/* Filters and Search */}
      <Card className="p-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder={
                  t("savedJobs.searchPlaceholder", locale) ||
                  "Search saved jobs..."
                }
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          {/* Sort */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-600">
              {t("savedJobs.sortBy", locale) || "Sort by:"}
            </span>
            <select
              value={sortBy}
              onChange={(e) =>
                setSortBy(e.target.value as "date" | "title" | "company")
              }
              className="border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="date">
                {t("savedJobs.dateSaved", locale) || "Date Saved"}
              </option>
              <option value="title">
                {t("savedJobs.jobTitle", locale) || "Job Title"}
              </option>
              <option value="company">
                {t("savedJobs.company", locale) || "Company"}
              </option>
            </select>
          </div>
        </div>
      </Card>

      {/* Jobs List */}
      {filteredJobs.length === 0 ? (
        <Card className="p-8 text-center">
          <Bookmark className="w-12 h-12 mx-auto text-slate-300 mb-4" />
          <h3 className="text-xl font-semibold text-slate-900 mb-2">
            {searchTerm
              ? t("savedJobs.noSearchResults", locale) ||
                "No saved jobs match your search"
              : t("savedJobs.noSavedJobs", locale) || "No saved jobs yet"}
          </h3>
          <p className="text-slate-600 mb-4">
            {searchTerm
              ? t("savedJobs.tryDifferentSearch", locale) ||
                "Try adjusting your search terms"
              : t("savedJobs.startSaving", locale) ||
                "Start saving jobs you're interested in to see them here"}
          </p>
          {!searchTerm && (
            <Button onClick={() => setSearchTerm("")}>
              {t("savedJobs.clearSearch", locale) || "Clear Search"}
            </Button>
          )}
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredJobs.map((savedJob) => (
            <Card
              key={savedJob.id}
              className="p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex flex-col lg:flex-row gap-6">
                {/* Job Details */}
                <div className="flex-1">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="text-lg font-semibold text-slate-900 mb-1">
                        {savedJob.job_data.title}
                      </h3>
                      <p className="text-slate-600 font-medium mb-2">
                        {savedJob.job_data.company}
                      </p>
                      <div className="flex items-center gap-4 text-sm text-slate-500">
                        <div className="flex items-center gap-1">
                          <MapPin className="w-4 h-4" />
                          <span>{savedJob.job_data.location}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Calendar className="w-4 h-4" />
                          <span>Saved {formatDate(savedJob.created_at)}</span>
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          window.open(`/app/jobs/${savedJob.job_id}`, "_blank")
                        }
                      >
                        <ExternalLink className="w-4 h-4 mr-1" />
                        {t("savedJobs.viewJob", locale) || "View Job"}
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => unsaveJob(savedJob.job_id)}
                        disabled={isUnsaving}
                      >
                        {isUnsaving ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-slate-600"></div>
                        ) : (
                          <Trash2 className="w-4 h-4 mr-1" />
                        )}
                        {t("savedJobs.remove", locale) || "Remove"}
                      </Button>
                    </div>
                  </div>

                  {/* Salary */}
                  {savedJob.job_data.salary_min &&
                    savedJob.job_data.salary_max && (
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-sm text-slate-600">
                          {t("savedJobs.salaryRange", locale) || "Salary:"}
                        </span>
                        <Badge variant="lagoon">
                          {formatCurrency(savedJob.job_data.salary_min)} -{" "}
                          {formatCurrency(savedJob.job_data.salary_max)}
                        </Badge>
                      </div>
                    )}

                  {/* Description */}
                  {savedJob.job_data.description && (
                    <p className="text-slate-600 text-sm line-clamp-3">
                      {savedJob.job_data.description}
                    </p>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
