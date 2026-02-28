import React from 'react';
import { Wrench, Mail } from 'lucide-react';
import { SEO } from '../components/marketing/SEO';

export default function Maintenance() {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col items-center justify-center px-6">
      <SEO
        title="Maintenance | JobHuntin"
        description="JobHuntin is temporarily unavailable for maintenance. We'll be back shortly."
      />
      <div className="max-w-md text-center">
        <div className="w-20 h-20 rounded-2xl bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center mx-auto mb-6">
          <Wrench className="w-10 h-10 text-amber-600 dark:text-amber-400" aria-hidden />
        </div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">
          We&apos;re making things better
        </h1>
        <p className="text-slate-600 dark:text-slate-400 mb-6">
          JobHuntin is temporarily unavailable for scheduled maintenance. We&apos;ll be back shortly.
        </p>
        <a
          href="mailto:support@jobhuntin.com"
          className="inline-flex items-center gap-2 text-sm font-medium text-primary-600 dark:text-primary-400 hover:underline"
        >
          <Mail className="w-4 h-4" aria-hidden />
          Contact support
        </a>
      </div>
    </div>
  );
}
