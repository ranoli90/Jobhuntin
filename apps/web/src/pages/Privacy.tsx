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
              Welcome to JobHuntin ("we," "our," or "us"). We provide an AI-powered job search automation platform (the "Service"). 
              We are committed to protecting your personal information and your right to privacy. If you have any questions or concerns about our policy, 
              or our practices with regards to your personal information, please contact us at <a href="mailto:privacy@jobhuntin.com">privacy@jobhuntin.com</a>.
            </p>
            <p>
              This Privacy Policy applies to all information collected through our website (https://jobhuntin.com), and/or any related services, sales, marketing, or events.
            </p>
          </section>

          <section>
            <h2>2. Information We Collect</h2>
            <p>We collect personal information that you voluntarily provide to us when registering at the Service, expressing an interest in obtaining information about us or our products and services, when participating in activities on the Service, or otherwise contacting us.</p>
            
            <div className="grid md:grid-cols-2 gap-6 my-8 not-prose">
              <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100">
                <div className="flex items-center gap-3 mb-3">
                  <Database className="w-5 h-5 text-primary-500" />
                  <h4 className="font-bold text-slate-900 m-0">Personal Data</h4>
                </div>
                <ul className="text-sm text-slate-600 space-y-2 list-disc list-inside">
                  <li>Name and Contact Data (Email, Phone)</li>
                  <li>Credentials (Passwords, Security hints)</li>
                  <li>Payment Data (Processed securely by Stripe)</li>
                  <li>Resume/CV Data & Employment History</li>
                </ul>
              </div>
              <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100">
                <div className="flex items-center gap-3 mb-3">
                  <Globe className="w-5 h-5 text-blue-500" />
                  <h4 className="font-bold text-slate-900 m-0">Usage Data</h4>
                </div>
                <ul className="text-sm text-slate-600 space-y-2 list-disc list-inside">
                  <li>IP Address & Device Characteristics</li>
                  <li>Operating System & Browser Type</li>
                  <li>Clickstream Data & Navigation Paths</li>
                  <li>Cookies & Tracking Technologies</li>
                </ul>
              </div>
            </div>

            <h3>Information Automatically Collected</h3>
            <p>
              We automatically collect certain information when you visit, use, or navigate the Service. This information does not reveal your specific identity (like your name or contact information) but may include device and usage information, such as your IP address, browser and device characteristics, operating system, language preferences, referring URLs, device name, country, location, information about how and when you use our Service, and other technical information.
            </p>
          </section>

          <section>
            <h2>3. How We Use Your Information</h2>
            <p>We use personal information collected via our Service for a variety of business purposes described below. We process your personal information for these purposes in reliance on our legitimate business interests, in order to enter into or perform a contract with you, with your consent, and/or for compliance with our legal obligations.</p>
            <ul>
              <li><strong>To facilitate account creation and logon process:</strong> If you choose to link your account with us to a third-party account (such as your Google or LinkedIn account), we use the information you allowed us to collect from those third parties to facilitate account creation and logon processes.</li>
              <li><strong>To deliver services to the user:</strong> We use your information to provide the AI job application services, including tailoring resumes, generating cover letters, and submitting applications on your behalf.</li>
              <li><strong>To improve our AI models:</strong> We may use anonymized and aggregated data to train and improve the performance of our matchmaking and content generation algorithms.</li>
              <li><strong>To send administrative information to you:</strong> We may use your personal information to send you product, service and new feature information and/or information about changes to our terms, conditions, and policies.</li>
              <li><strong>To protect our Services:</strong> We may use your information as part of our efforts to keep our Service safe and secure (for example, for fraud monitoring and prevention).</li>
            </ul>
          </section>

          <section>
            <h2>4. Sharing Your Information</h2>
            <p>We only share information with your consent, to comply with laws, to provide you with services, to protect your rights, or to fulfill business obligations.</p>
            <ul>
              <li><strong>Business Transfers:</strong> We may share or transfer your information in connection with, or during negotiations of, any merger, sale of company assets, financing, or acquisition of all or a portion of our business to another company.</li>
              <li><strong>Vendors, Consultants and Other Third-Party Service Providers:</strong> We may share your data with third-party vendors, service providers, contractors, or agents who perform services for us or on our behalf and require access to such information to do that work (e.g., Stripe for payments, OpenAI for content generation, Supabase for database hosting).</li>
              <li><strong>Legal Requirements:</strong> We may disclose your information where we are legally required to do so in order to comply with applicable law, governmental requests, a judicial proceeding, court order, or legal process.</li>
            </ul>
          </section>

          <section>
            <h2>5. International Transfers</h2>
            <p>
              Our servers are located in the United States. If you are accessing our Service from outside, please be aware that your information may be transferred to, stored, and processed by us in our facilities and by those third parties with whom we may share your personal information.
            </p>
            <p>
              If you are a resident in the European Economic Area (EEA) or United Kingdom (UK), then these countries may not necessarily have data protection laws or other similar laws as comprehensive as those in your country. We will however take all necessary measures to protect your personal information in accordance with this privacy policy and applicable law.
            </p>
          </section>

          <section>
            <h2>6. Your Privacy Rights (GDPR & CCPA)</h2>
            <p>Depending on your location, you may have the following rights regarding your personal data:</p>
            <div className="space-y-4 mt-6">
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-bold">1</div>
                <div>
                  <h4 className="font-bold text-slate-900">Right to Access</h4>
                  <p className="text-sm text-slate-600 m-0">You have the right to request copies of your personal data.</p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-bold">2</div>
                <div>
                  <h4 className="font-bold text-slate-900">Right to Rectification</h4>
                  <p className="text-sm text-slate-600 m-0">You have the right to request that we correct any information you believe is inaccurate.</p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-bold">3</div>
                <div>
                  <h4 className="font-bold text-slate-900">Right to Erasure ("Right to be Forgotten")</h4>
                  <p className="text-sm text-slate-600 m-0">You have the right to request that we erase your personal data, under certain conditions.</p>
                </div>
              </div>
            </div>
            <p className="mt-6">
              To exercise any of these rights, please contact us at <a href="mailto:privacy@jobhuntin.com">privacy@jobhuntin.com</a>. We will respond to your request within 30 days.
            </p>
          </section>

          <section>
            <h2>7. Data Security</h2>
            <p>
              We have implemented appropriate technical and organizational security measures designed to protect the security of any personal information we process. 
              However, despite our safeguards and efforts to secure your information, no electronic transmission over the Internet or information storage technology can be guaranteed to be 100% secure, so we cannot promise or guarantee that hackers, cybercriminals, or other unauthorized third parties will not be able to defeat our security, and improperly collect, access, steal, or modify your information.
            </p>
          </section>

          <section>
            <h2>8. Contact Us</h2>
            <p>
              If you have questions or comments about this policy, you may email us at <a href="mailto:privacy@jobhuntin.com">privacy@jobhuntin.com</a> or by post to:
            </p>
            <address className="not-italic bg-slate-50 p-6 rounded-xl border border-slate-100">
              <strong>JobHuntin AI Inc.</strong><br />
              123 Innovation Drive<br />
              Suite 400<br />
              Denver, CO 80202<br />
              United States
            </address>
          </section>
        </div>
      </main>
    </div>
  );
}
