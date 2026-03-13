/**
 * Unauthorized Access Page
 * Displayed when user tries to access a page they don't have permission for
 */

import React from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  Shield,
  ArrowLeft,
  Home,
  Mail,
  Lock,
} from "lucide-react";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { SEO } from "../SEO";

export default function Unauthorized() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const locale = localStorage.getItem("language") || "en";

  const handleGoBack = () => {
    navigate(-1);
  };

  const handleGoHome = () => {
    navigate("/");
  };

  const handleGoToDashboard = () => {
    navigate("/app/dashboard");
  };

  const handleContactSupport = () => {
    window.location.href = "mailto:support@jobhuntin.com";
  };

  return (
    <>
      <SEO
        title="403 | Access Denied | JobHuntin"
        description="You don't have permission to access this page. Return to JobHuntin to continue."
      />

      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-red-500/10 rounded-full blur-3xl" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-amber-500/10 rounded-full blur-3xl" />
        </div>

        <Card className="max-w-lg w-full p-8 relative z-10 text-center border-2 border-red-100 shadow-xl">
          {/* Icon */}
          <div className="mx-auto mb-6 w-20 h-20 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center">
            <Shield className="w-10 h-10 text-red-600 dark:text-red-400" />
          </div>

          {/* Error Code */}
          <div className="text-sm font-bold text-red-600 dark:text-red-400 uppercase tracking-wider mb-2">
            {t("unauthorized.errorCode", locale) || "Error 403"}
          </div>

          {/* Heading */}
          <h1 className="text-4xl sm:text-5xl font-black text-slate-900 dark:text-slate-100 mb-4 tracking-tight">
            {t("unauthorized.heading", locale) || "Access Denied"}
          </h1>

          {/* Description */}
          <p className="text-lg text-slate-600 dark:text-slate-400 mb-8 leading-relaxed">
            {t(
              "unauthorized.description",
              locale,
            ) ||
              "You don't have permission to access this page. If you believe this is an error, please contact support."}
          </p>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mb-8">
            <Button
              onClick={handleGoBack}
              variant="outline"
              className="w-full sm:w-auto"
              aria-label={t("unauthorized.goBack", locale) || "Go Back"}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              {t("unauthorized.goBack", locale) || "Go Back"}
            </Button>
            <Button
              onClick={handleGoToDashboard}
              className="w-full sm:w-auto"
              aria-label={t("unauthorized.dashboard", locale) || "Go to Dashboard"}
            >
              <Home className="w-4 h-4 mr-2" />
              {t("unauthorized.dashboard", locale) || "Dashboard"}
            </Button>
          </div>

          {/* Help Section */}
          <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-6">
            <div className="flex items-start gap-3">
              <Lock className="w-5 h-5 text-slate-600 dark:text-slate-400 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-slate-600 dark:text-slate-400 text-left">
                <p className="font-medium text-slate-900 dark:text-slate-200 mb-2">
                  {t("unauthorized.needHelp", locale) || "Need help?"}
                </p>
                <p className="mb-3">
                  {t(
                    "unauthorized.contactDescription",
                    locale,
                  ) ||
                    "If you believe you should have access to this page, please contact our support team."}
                </p>
                <button
                  onClick={handleContactSupport}
                  className="inline-flex items-center gap-2 text-primary-600 dark:text-primary-400 hover:underline font-medium"
                >
                  <Mail className="w-4 h-4" />
                  {t("unauthorized.contactSupport", locale) ||
                    "Contact Support"}
                </button>
              </div>
            </div>
          </div>

          {/* Debug Info (development only) */}
          {import.meta.env.DEV && (
            <details className="mt-6 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
              <summary className="cursor-pointer font-medium text-yellow-800 dark:text-yellow-200 text-sm">
                Debug Information (Development)
              </summary>
              <div className="mt-3 text-xs text-yellow-700 dark:text-yellow-300 text-left space-y-2">
                <div>
                  <span className="font-medium">Current Path:</span>{" "}
                  <code className="bg-yellow-100 dark:bg-yellow-900/50 px-1 rounded">
                    {window.location.pathname}
                  </code>
                </div>
                <div>
                  <span className="font-medium">User Auth Status:</span> Check
                  console for details
                </div>
              </div>
            </details>
          )}
        </Card>
      </div>
    </>
  );
}
