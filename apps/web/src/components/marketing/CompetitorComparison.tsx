import React from 'react';
import { motion } from 'framer-motion';
import { Bot, X, Zap, CheckCircle, Shield, Target } from 'lucide-react';

interface CompetitorData {
  name: string;
  weakness: string;
  strength: string;
}

export const CompetitorComparison = ({ competitor }: { competitor: CompetitorData }) => {
  return (
    <div className="bg-white rounded-[2rem] p-8 md:p-12 border border-slate-100 shadow-xl overflow-hidden relative">
      <div className="absolute top-0 right-0 w-64 h-64 bg-primary-50 rounded-full blur-3xl -mr-32 -mt-32 opacity-50" />
      
      <div className="grid md:grid-cols-2 gap-12 relative z-10">
        <div>
          <h2 className="text-3xl font-bold font-display mb-6 text-slate-900">
            JobHuntin vs <span className="text-primary-500">{competitor.name}</span>
          </h2>
          <p className="text-slate-600 mb-8 leading-relaxed font-medium">
            While {competitor.name} focuses on {competitor.strength.toLowerCase()}, JobHuntin is engineered for autonomous results. 
            We don't just help you apply; we hunt for you.
          </p>
          
          <div className="space-y-6">
            <div className="flex gap-4">
              <div className="w-12 h-12 bg-red-50 rounded-xl flex items-center justify-center flex-shrink-0 text-red-500">
                <X className="w-6 h-6" />
              </div>
              <div>
                <h4 className="font-bold text-slate-900">{competitor.name} Gap</h4>
                <p className="text-sm text-slate-500 font-medium">{competitor.weakness}</p>
              </div>
            </div>
            
            <div className="flex gap-4">
              <div className="w-12 h-12 bg-green-50 rounded-xl flex items-center justify-center flex-shrink-0 text-green-500">
                <Zap className="w-6 h-6" />
              </div>
              <div>
                <h4 className="font-bold text-slate-900">JobHuntin Edge</h4>
                <p className="text-sm text-slate-500 font-medium">Fully autonomous AI agent with human-like browsing patterns.</p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-slate-50 rounded-3xl p-6 border border-slate-100">
          <div className="space-y-4">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Feature Simulation</h4>
            {[
              { label: "AI Tailoring", jh: true, comp: true },
              { label: "Auto-Submission", jh: true, comp: false },
              { label: "Bot Protection Bypass", jh: true, comp: false },
              { label: "Custom Cover Letters", jh: true, comp: true },
              { label: "Recruiter Pre-Screening", jh: true, comp: false }
            ].map((feature, i) => (
              <div key={i} className="flex items-center justify-between py-2 border-b border-slate-200 last:border-0">
                <span className="text-sm font-medium text-slate-700">{feature.label}</span>
                <div className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <span className="text-[10px] text-slate-400 mb-1">JH</span>
                    {feature.jh ? <CheckCircle className="w-4 h-4 text-green-500" /> : <X className="w-4 h-4 text-slate-300" />}
                  </div>
                  <div className="flex flex-col items-center">
                    <span className="text-[10px] text-slate-400 mb-1">{competitor.name.slice(0, 3).toUpperCase()}</span>
                    {feature.comp ? <CheckCircle className="w-4 h-4 text-green-500" /> : <X className="w-4 h-4 text-slate-300" />}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
