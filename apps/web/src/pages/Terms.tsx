import React from 'react';
import { Link } from 'react-router-dom';
import { Bot, FileText, CheckCircle, AlertTriangle, HelpCircle } from 'lucide-react';
import { SEO } from '../components/marketing/SEO';

export default function Terms() {
  const lastUpdated = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-primary-500/20 selection:text-primary-700">
      <SEO 
        title="Terms of Service | JobHuntin AI"
        description="Read the terms and conditions for using JobHuntin's AI job hunting services. Understanding your rights and responsibilities."
        ogTitle="Terms of Service | JobHuntin AI"
        canonicalUrl="https://jobhuntin.com/terms"
      />
      
      <main className="max-w-4xl mx-auto px-6 py-20">
        <div className="mb-12 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-50 rounded-2xl mb-6">
            <FileText className="w-8 h-8 text-primary-600" />
          </div>
          <h1 className="text-4xl md:text-5xl font-black font-display text-slate-900 mb-6 tracking-tight">Terms of Service</h1>
          <p className="text-lg text-slate-500 max-w-2xl mx-auto">
            Please read these terms carefully before using our service. They govern your relationship with JobHuntin AI.
          </p>
          <p className="text-sm text-slate-400 mt-4 font-mono">Last Updated: {lastUpdated}</p>
        </div>

        <div className="bg-white rounded-3xl shadow-xl shadow-slate-200/50 p-8 md:p-12 border border-slate-100 prose prose-slate prose-lg max-w-none prose-headings:font-display prose-headings:font-bold prose-headings:text-slate-900 prose-a:text-primary-600 prose-a:no-underline hover:prose-a:underline prose-li:marker:text-primary-500">
          
          <section>
            <h2>1. Description of Service</h2>
            <p>
              <strong>Sorce</strong> (the "Service") is an Autonomous Job Application Platform that uses Artificial Intelligence to:
            </p>
            <ol>
              <li>Parse and normalize your resume (<code>/webhook/resume_parse</code>).</li>
              <li>Search and score job listings (<code>/match-job</code>).</li>
              <li>Autonomously fill and submit applications (<code>/claim_next</code>).</li>
            </ol>
          </section>

          <section>
            <h2>2. Agency & "Human-in-the-Loop"</h2>
            <h3>2.1 Limited Power of Attorney</h3>
            <p>
              By enabling the "Auto-Apply" feature, you grant <strong>JobHuntin AI</strong> a specific, limited power of attorney to act as your digital agent: to access job boards, complete forms, and electronically sign applications in your name.
            </p>

            <h3>2.2 Your Responsibility (The "Review Queue")</h3>
            <p>
              You acknowledge that AI is probabilistic and prone to "hallucinations" (errors).
            </p>
            <ul>
              <li><strong>You must review</strong> your "Canonical Profile" after the initial Resume Parse to ensure accuracy.</li>
              <li><strong>You assume full liability</strong> for any misrepresentation (e.g., incorrect dates, phantom degrees) submitted by the Agent if you failed to correct the data in your <code>public.profiles</code> record or the <code>Pending Review</code> queue.</li>
            </ul>
          </section>

          <section>
            <h2>3. Acceptable Use</h2>
            <p>You agree NOT to use the Service/API to:</p>
            <ul>
              <li><strong>DDoS Job Boards:</strong> Use the <code>match-jobs-batch</code> endpoint to flood third-party sites with excessive requests.</li>
              <li><strong>Prompt Injection:</strong> Attempt to manipulate our LLM (e.g., "ignore previous instructions") via the <code>custom_instructions</code> or profile fields. <em>We employ strict sanitization logic (<code>sanitize_input</code>) and will ban accounts attempting injection attacks.</em></li>
            </ul>
          </section>

          <section>
            <h2>4. Payment & Credits</h2>
            <ul>
              <li><strong>Pay-Per-Application:</strong> Some plans may charge based on the number of <code>SUBMITTED</code> events recorded in our <code>application_events</code> log.</li>
              <li><strong>No Refunds for Rejections:</strong> We do not guarantee employment. You pay for the <em>agent's labor</em>, not the <em>outcome</em>.</li>
            </ul>
          </section>

          <section>
            <h2>5. Third-Party Intelligence (OpenRouter & Nvidia)</h2>
            <p>Our Service uses models provided by <strong>OpenRouter</strong> and <strong>Nvidia</strong>.</p>
            <ul>
              <li><strong>Service Availability:</strong> We are not liable for outages caused by OpenRouter's API failure or valid <code>CircuitBreakerOpen</code> exceptions thrown by our internal reliability systems.</li>
              <li><strong>Data Accuracy:</strong> We disclaim all warranties regarding the accuracy of AI-generated text (e.g., Cover Letters generated via <code>/generate-cover-letter</code>).</li>
            </ul>
          </section>

          <section>
            <h2>6. Intellectual Property</h2>
            <ul>
              <li><strong>Your Data:</strong> You retain ownership of your Resume and <code>profile_data</code>.</li>
              <li><strong>Generated Content:</strong> You own the rights to any Cover Letters or inputs generated by the Agent on your behalf, subject to the license terms of the underlying LLM providers.</li>
            </ul>
          </section>

          <section>
            <h2>7. Disclaimer of Warranties</h2>
            <p>
              THE SERVICE IS PROVIDED "AS IS." WE DO NOT WARRANT THAT THE "MATCH SCORE" ACCURATELY PREDICTS HIRING SUCCESS OR THAT THE "SMART PRE-FILL" MEMORY WILL WORK ON ALL THIRD-PARTY FORMS.
            </p>
          </section>

          <section>
            <h2>8. Limitation of Liability</h2>
            <p>
              TO THE MAXIMUM EXTENT PERMITTED BY LAW, OUR LIABILITY FOR ANY CLAIM RELATED TO AN INCORRECT JOB APPLICATION SUBMISSION IS LIMITED TO THE AMOUNT YOU PAID FOR THE SERVICE IN THE PAST 12 MONTHS. WE ARE NOT LIABLE FOR CONSEQUENTIAL DAMAGES (E.G., LOST WAGES FROM A MISSED JOB OPPORTUNITY).
            </p>
          </section>

          <section>
            <h2>9. Arbitration & Class Action Waiver</h2>
            <p>
              All disputes shall be resolved by binding arbitration. <strong>You waive your right to participate in a class-action lawsuit</strong>, including claims related to Algorithmic Bias or Automated Decision-Making laws.
            </p>
          </section>

          <section>
            <h2>10. Governing Law</h2>
            <p>
              Delaware Law governs these Terms.
            </p>
          </section>

        </div>
      </main>
    </div>
  );
}
