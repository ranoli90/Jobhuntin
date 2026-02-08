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
            <h2>1. Agreement to Terms</h2>
            <p>
              By accessing our website at <a href="https://jobhuntin.com">https://jobhuntin.com</a> and using our services, you agree to be bound by these Terms of Service and to comply with all applicable laws and regulations. If you do not agree with any of these terms, you are prohibited from using or accessing this site.
            </p>
          </section>

          <section>
            <h2>2. Use License & Restrictions</h2>
            <p>
              Permission is granted to temporarily download one copy of the materials (information or software) on JobHuntin's website for personal, non-commercial transitory viewing only. This is the grant of a license, not a transfer of title, and under this license you may not:
            </p>
            <ul>
              <li>Modify or copy the materials;</li>
              <li>Use the materials for any commercial purpose, or for any public display (commercial or non-commercial);</li>
              <li>Attempt to decompile or reverse engineer any software contained on JobHuntin's website;</li>
              <li>Remove any copyright or other proprietary notations from the materials; or</li>
              <li>Transfer the materials to another person or "mirror" the materials on any other server.</li>
            </ul>
            <p>
              This license shall automatically terminate if you violate any of these restrictions and may be terminated by JobHuntin at any time. Upon terminating your viewing of these materials or upon the termination of this license, you must destroy any downloaded materials in your possession whether in electronic or printed format.
            </p>
          </section>

          <section>
            <h2>3. Service Description & Disclaimers</h2>
            <div className="bg-amber-50 p-6 rounded-2xl border border-amber-100 my-6 not-prose">
               <div className="flex items-start gap-3">
                 <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0 mt-1" />
                 <div>
                   <h4 className="font-bold text-amber-900 text-lg mb-2">No Guarantee of Employment</h4>
                   <p className="text-amber-800 text-sm leading-relaxed">
                     JobHuntin is a tool to assist in the job application process. We do not guarantee interviews, job offers, or employment. 
                     The outcome of any job application depends on numerous factors beyond our control, including your qualifications and the employer's requirements.
                   </p>
                 </div>
               </div>
            </div>
            <p>
              The materials on JobHuntin's website are provided on an 'as is' basis. JobHuntin makes no warranties, expressed or implied, and hereby disclaims and negates all other warranties including, without limitation, implied warranties or conditions of merchantability, fitness for a particular purpose, or non-infringement of intellectual property or other violation of rights.
            </p>
            <p>
              Further, JobHuntin does not warrant or make any representations concerning the accuracy, likely results, or reliability of the use of the materials on its website or otherwise relating to such materials or on any sites linked to this site.
            </p>
          </section>

          <section>
            <h2>4. User Accounts & Security</h2>
            <p>
              When you create an account with us, you must provide us information that is accurate, complete, and current at all times. Failure to do so constitutes a breach of the Terms, which may result in immediate termination of your account on our Service.
            </p>
            <p>
              You are responsible for safeguarding the password that you use to access the Service and for any activities or actions under your password, whether your password is with our Service or a third-party service. You agree not to disclose your password to any third party. You must notify us immediately upon becoming aware of any breach of security or unauthorized use of your account.
            </p>
          </section>

          <section>
            <h2>5. Subscription & Payments</h2>
            <p>
              Some parts of the Service are billed on a subscription basis ("Subscription(s)"). You will be billed in advance on a recurring and periodic basis ("Billing Cycle"). Billing cycles are set either on a monthly or annual basis, depending on the type of subscription plan you select when purchasing a Subscription.
            </p>
            <ul>
              <li><strong>Cancellation:</strong> You may cancel your Subscription renewal either through your online account management page or by contacting our customer support team.</li>
              <li><strong>Refunds:</strong> Certain refund requests for Subscriptions may be considered by JobHuntin on a case-by-case basis and granted at the sole discretion of JobHuntin.</li>
              <li><strong>Fee Changes:</strong> JobHuntin, in its sole discretion and at any time, may modify the Subscription fees. Any Subscription fee change will become effective at the end of the then-current Billing Cycle.</li>
            </ul>
          </section>

          <section>
            <h2>6. Limitation of Liability</h2>
            <p>
              In no event shall JobHuntin or its suppliers be liable for any damages (including, without limitation, damages for loss of data or profit, or due to business interruption) arising out of the use or inability to use the materials on JobHuntin's website, even if JobHuntin or a JobHuntin authorized representative has been notified orally or in writing of the possibility of such damage. Because some jurisdictions do not allow limitations on implied warranties, or limitations of liability for consequential or incidental damages, these limitations may not apply to you.
            </p>
          </section>

          <section>
            <h2>7. Governing Law</h2>
            <p>
              These terms and conditions are governed by and construed in accordance with the laws of Colorado, United States and you irrevocably submit to the exclusive jurisdiction of the courts in that State or location.
            </p>
          </section>

          <section>
            <h2>8. Changes to Terms</h2>
            <p>
              We reserve the right, at our sole discretion, to modify or replace these Terms at any time. If a revision is material we will try to provide at least 30 days notice prior to any new terms taking effect. What constitutes a material change will be determined at our sole discretion.
            </p>
            <p>
              By continuing to access or use our Service after those revisions become effective, you agree to be bound by the revised terms. If you do not agree to the new terms, please stop using the Service.
            </p>
          </section>

          <section>
            <h2>9. Contact Us</h2>
            <p>
              If you have any questions about these Terms, please contact us at <a href="mailto:legal@jobhuntin.com">legal@jobhuntin.com</a>.
            </p>
          </section>

        </div>
      </main>
    </div>
  );
}
