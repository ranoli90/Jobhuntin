import React from 'react';
import { Link } from 'react-router-dom';
import { Bot, ArrowLeft, Shield, Lock, Eye, FileText, Database, Globe } from 'lucide-react';
import { SEO } from '../components/marketing/SEO';

export default function Privacy() {
  const lastUpdated = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-primary-500/20 selection:text-primary-700">
      <SEO 
        title="Privacy Policy | JobHuntin AI"
        description="Comprehensive details on how JobHuntin collects, uses, and protects your personal data. Compliant with GDPR, CCPA, and global privacy standards."
        ogTitle="Privacy Policy | JobHuntin AI"
        canonicalUrl="https://jobhuntin.com/privacy"
      />
      
      {/* Header handled by Layout, but keeping independent nav if accessed directly or for print styles */}
      
      <main className="max-w-4xl mx-auto px-6 py-20">
        <div className="mb-12 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-50 rounded-2xl mb-6">
            <Shield className="w-8 h-8 text-primary-600" />
          </div>
          <h1 className="text-4xl md:text-5xl font-black font-display text-slate-900 mb-6 tracking-tight">Privacy Policy</h1>
          <p className="text-lg text-slate-500 max-w-2xl mx-auto">
            Your trust is our foundation. We are transparent about every byte of data we collect and how we use it to land your dream job.
          </p>
          <p className="text-sm text-slate-400 mt-4 font-mono">Last Updated: {lastUpdated}</p>
        </div>

        <div className="bg-white rounded-3xl shadow-xl shadow-slate-200/50 p-8 md:p-12 border border-slate-100 prose prose-slate prose-lg max-w-none prose-headings:font-display prose-headings:font-bold prose-headings:text-slate-900 prose-a:text-primary-600 prose-a:no-underline hover:prose-a:underline prose-li:marker:text-primary-500">
          
          <section>
            <h2>1. Introduction</h2>
            <p>
              This Privacy Policy explains how <strong>JobHuntin AI</strong> ("we") collects, uses, and protects your data while operating the <strong>Sorce</strong> platform. This policy is strictly aligned with our technical architecture to ensure essentially "Zero-Defect" compliance with strict 2026 regulations (CCPA, Colorado AI Act, GDPR).
            </p>
          </section>

          <section>
            <h2>2. The Data We Collect & Where It Lives</h2>
            <p>We collect data to power our <strong>Autonomous Job Application Agent</strong>.</p>
            
            <div className="space-y-6 my-8 not-prose">
              <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100">
                <div className="flex items-center gap-3 mb-3">
                  <Database className="w-5 h-5 text-primary-500" />
                  <h4 className="font-bold text-slate-900 m-0">Core Profile Data (<code>public.profiles</code>)</h4>
                </div>
                <ul className="text-sm text-slate-600 space-y-2 list-disc list-inside">
                  <li><strong>Collected:</strong> Full Name, Resume (PDF), Experience, Education, Skills.</li>
                  <li><strong>Storage:</strong> Securely stored in <strong>Supabase (PostgreSQL)</strong>.</li>
                  <li><strong>Purpose:</strong> To generate a "Canonical Profile" used for filling job applications.</li>
                  <li><strong>Retention:</strong> Retained while your account is active.</li>
                </ul>
              </div>

              <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100">
                <div className="flex items-center gap-3 mb-3">
                  <Bot className="w-5 h-5 text-indigo-500" />
                  <h4 className="font-bold text-slate-900 m-0">"Smart Pre-Fill" Memory (<code>public.answer_memory</code>)</h4>
                </div>
                <ul className="text-sm text-slate-600 space-y-2 list-disc list-inside">
                  <li><strong>Collected:</strong> Answers you provide to specific job application questions (e.g., "Do you require sponsorship?", "Years of Python experience").</li>
                  <li><strong>Function:</strong> We store these <code>(Field, Value)</code> pairs to auto-fill future applications.</li>
                  <li><strong>Control:</strong> You may clear this memory via the <code>/me/answer-memory</code> endpoint in your dashboard settings.</li>
                </ul>
              </div>

              <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100">
                <div className="flex items-center gap-3 mb-3">
                  <FileText className="w-5 h-5 text-emerald-500" />
                  <h4 className="font-bold text-slate-900 m-0">Application History (<code>public.applications</code>)</h4>
                </div>
                <ul className="text-sm text-slate-600 space-y-2 list-disc list-inside">
                  <li><strong>Collected:</strong> Job descriptions, application status, and timestamps.</li>
                  <li><strong>Purpose:</strong> To track the Agent's performance and provide an "Audit Log" of where we applied on your behalf.</li>
                </ul>
              </div>
            </div>
          </section>

          <section>
            <h2>3. How We Use Artificial Intelligence (AI)</h2>
            <p>We use "High-Risk" AI systems (Generative AI & LLMs) to analyze your profile and write content.</p>
            
            <h3>3.1 Sub-Processors & Vendors</h3>
            <p>We transmit data to the following third-party AI providers:</p>
            <ul>
              <li><strong>OpenRouter.ai:</strong> Our primary gateway for LLM inference.</li>
              <li><strong>Google (Gemini) & OpenAI:</strong> The underlying models used for reasoning and content generation.</li>
              <li><strong>Render:</strong> Provides database hosting and application infrastructure.</li>
            </ul>

            <div className="bg-blue-50 p-6 rounded-2xl border border-blue-100 my-6 not-prose">
               <div className="flex items-start gap-3">
                 <Lock className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
                 <div>
                   <h4 className="font-bold text-blue-900 text-lg mb-2">Privacy-by-Design: PII Stripping</h4>
                   <p className="text-blue-800 text-sm leading-relaxed">
                     Before sending your data to any AI provider (e.g., for <code>suggest-roles</code> or <code>generate-cover-letter</code>), our system <strong>automatically strips</strong> the following Personally Identifiable Information (PII) to protect your anonymity:
                   </p>
                   <ul className="grid grid-cols-2 gap-2 mt-4 text-sm text-blue-800 font-medium">
                     <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>Email Address</li>
                     <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>Phone Number</li>
                     <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>Physical Address</li>
                     <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>Social URLs</li>
                   </ul>
                   <p className="text-xs text-blue-600 mt-4 italic">
                     *Codebase Verification: This is enforced by our <code>strip_pii_for_llm</code> middleware function.
                   </p>
                 </div>
               </div>
            </div>
          </section>

          <section>
            <h2>4. Automated Decision-Making Technology (ADMT)</h2>
            
            <h3>4.1 Scoring & Ranking (<code>match-job</code>)</h3>
            <ul>
              <li><strong>Usage:</strong> We use an algorithm to assign a "Match Score" (0-100) to job postings.</li>
              <li><strong>Logic:</strong> The score is based on keyword overlap between your <code>public.profiles</code> data and the job description.</li>
              <li><strong>Your Right:</strong> You have the right to request the specific logic used for any score.</li>
            </ul>

            <h3>4.2 Auto-Apply (<code>/claim_next</code>)</h3>
            <ul>
              <li><strong>Usage:</strong> Our "Worker Agent" autonomously claims jobs from your queue and submits applications.</li>
              <li><strong>Opt-Out:</strong> You can disable "Auto-Apply" at any time, reverting the system to "Manual Approval Mode."</li>
            </ul>
          </section>

          <section>
            <h2>5. Security & Data Integrity</h2>
            <ul>
              <li><strong>Encryption:</strong> All data in transit is encrypted via TLS. Database connections use SSL.</li>
              <li><strong>Access Control:</strong> We use Row Level Security (RLS) and distinct Tenant Contexts to ensure your data is never accessible by other users.</li>
              <li><strong>Audit Logging:</strong> We maintain an immutable <code>application_events</code> log (<code>id</code>, <code>event_type</code>, <code>payload</code>) to record every action the Agent takes.</li>
            </ul>
          </section>

          <section>
            <h2>6. Your Rights (CCPA/CPRA & GDPR)</h2>
            <div className="space-y-4 mt-6">
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-bold">1</div>
                <div>
                  <h4 className="font-bold text-slate-900">Right to Know</h4>
                  <p className="text-sm text-slate-600 m-0">You may request a dump of your <code>public.profiles</code> and <code>public.application_inputs</code> data.</p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-bold">2</div>
                <div>
                  <h4 className="font-bold text-slate-900">Right to Delete</h4>
                  <p className="text-sm text-slate-600 m-0">You may request deletion of your account. We will purge your data from Supabase and our Redis cache.</p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-bold">3</div>
                <div>
                  <h4 className="font-bold text-slate-900">Global Privacy Control (GPC)</h4>
                  <p className="text-sm text-slate-600 m-0">We respect GPC signals from your browser to automatically limit third-party data sharing.</p>
                </div>
              </div>
            </div>
          </section>

          <section>
            <h2>7. Contact</h2>
            <p>
              For privacy requests or "Bias Audit" results, email us at <a href="mailto:privacy@jobhuntin.com">privacy@jobhuntin.com</a>.
            </p>
          </section>
        </div>
      </main>
    </div>
  );
}
