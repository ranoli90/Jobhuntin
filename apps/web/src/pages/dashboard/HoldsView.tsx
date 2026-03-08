import { motion, useReducedMotion } from "framer-motion";
import { CheckCircle, Clock, Quote, Send } from "lucide-react";
import { useState } from "react";
import { useApplications } from "../../hooks/useApplications";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { sharedLocale, sharedRtl } from "./shared";

export default function HoldsView() {
  const { holdApplications, answerHold, snoozeApplication, isLoading, isSubmitting } = useApplications();
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const shouldReduceMotion = useReducedMotion();
  const locale = sharedLocale;
  const rtl = sharedRtl;

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 pb-6 px-4 lg:px-0" aria-busy="true" aria-label="Loading items needing your input">
        <div className="space-y-2">
          <div className="h-8 w-56 bg-slate-200 rounded animate-pulse" />
          <div className="h-4 w-72 bg-slate-100 rounded animate-pulse" />
        </div>
        <div className="space-y-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="p-0 overflow-hidden border border-slate-200 rounded-2xl animate-pulse">
              <div className="bg-slate-50 border-b border-slate-200 p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-lg bg-slate-200" />
                  <div className="space-y-2">
                    <div className="h-4 w-24 bg-slate-200 rounded" />
                    <div className="h-3 w-32 bg-slate-100 rounded" />
                  </div>
                </div>
                <div className="h-6 w-24 bg-amber-100 rounded" />
              </div>
              <div className="p-6 space-y-4">
                <div className="h-16 bg-amber-50 rounded-2xl" />
                <div className="h-24 bg-slate-100 rounded-xl" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (holdApplications.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 px-6">
        <div className="w-12 h-12 rounded-full border-2 border-slate-200 flex items-center justify-center mb-6">
          <CheckCircle className="w-5 h-5 text-slate-400" />
        </div>
        <h2 className="text-lg font-semibold text-slate-900 mb-1">Nothing needs your attention</h2>
        <p className="text-sm text-slate-500 max-w-xs mx-auto text-center mb-4">
          All your applications are progressing. When the agent needs input from you, it will appear here.
        </p>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-50 border border-slate-200">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs text-slate-500">Agent active</span>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-6 px-4 lg:px-0">
      <div>
        <h2 className="text-2xl font-black text-slate-900 tracking-tight">Items Needing Your Input</h2>
        <p className="text-slate-500 font-medium">Your AI agent needs clarification on these {holdApplications.length} threads.</p>
      </div>

      <div className="space-y-6">
        {holdApplications.map((app, idx) => (
          <motion.div
            key={app.id}
            initial={shouldReduceMotion ? undefined : { opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={shouldReduceMotion ? undefined : { delay: idx * 0.05, duration: 0.25 }}
          >
            <Card className="p-0 overflow-hidden border-slate-200" shadow="lift">
              <div className="bg-slate-50 border-b border-slate-200 p-3 sm:p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center text-white font-bold text-xs">
                    {app.company.charAt(0)}
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900 text-sm">{app.company}</h3>
                    <p className="text-[10px] text-slate-500 font-medium uppercase tracking-wider">{app.job_title}</p>
                  </div>
                </div>
                <Badge variant="warning" className="rounded-md font-bold text-[10px]">RESPONSE REQUIRED</Badge>
              </div>

              <div className="p-4 sm:p-6 space-y-6">
                <div id={`hold-question-${app.id}`} className="bg-amber-50 rounded-2xl p-4 sm:p-6 border border-amber-100 relative">
                  <Quote className="absolute top-4 left-4 w-12 h-12 text-amber-200/50 -z-0" />
                  <p className="text-amber-900 font-medium leading-relaxed relative z-10">
                    "I've encountered a specific question on the portal: <span className="font-black italic">'{app.hold_question}'</span>. How should I proceed?"
                  </p>
                </div>

                <div className="space-y-4">
                  <label htmlFor={`hold-answer-${app.id}`} className="sr-only">
                    Your response for {app.company} — {app.job_title}
                  </label>
                  <textarea
                    id={`hold-answer-${app.id}`}
                    className="w-full p-4 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 transition-all bg-white dark:bg-slate-900 dark:border-slate-700 dark:text-slate-100 font-medium min-h-[100px]"
                    maxLength={5000}
                    placeholder="Type your response here... (e.g. Yes, I have 5 years experience with Kubernetes)"
                    value={answers[app.id] || ""}
                    onChange={(e) => setAnswers(prev => ({ ...prev, [app.id]: e.target.value }))}
                    aria-describedby={`hold-question-${app.id}`}
                  />
                  <div className="flex items-center justify-between">
                    <p className="text-[10px] text-slate-400">
                      {(answers[app.id] || '').length}/5000 characters
                    </p>
                    {(answers[app.id] || '').length > 4500 && (
                      <p className="text-[10px] text-amber-500 font-medium">
                        {5000 - (answers[app.id] || '').length} characters remaining
                      </p>
                    )}
                  </div>
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-4 sticky bottom-0 bg-white/90 backdrop-blur p-2 rounded-xl border border-slate-100">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-slate-500 hover:text-slate-600 font-bold text-xs uppercase"
                      disabled={isSubmitting(`snooze-${app.id}`)}
                      onClick={() => snoozeApplication(app.id)}
                    >
                      {isSubmitting(`snooze-${app.id}`) ? <LoadingSpinner className="w-4 h-4 mr-2" /> : <Clock className="w-4 h-4 mr-2" />} Snooze 24h
                    </Button>
                    <Button
                      disabled={!answers[app.id] || isSubmitting(app.id)}
                      onClick={() => answerHold(app.id, answers[app.id])}
                      className="bg-primary-600 hover:bg-primary-500 text-white font-bold rounded-xl px-6 sm:px-8 shadow-lg shadow-primary-500/20"
                    >
                      {isSubmitting(app.id)
                        ? <><LoadingSpinner className="mr-2 w-4 h-4" />Sending...</>
                        : <><Send className="mr-2 w-4 h-4" />Send Instructions</>}
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
}