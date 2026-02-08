import React from 'react';
import { Link } from 'react-router-dom';
import { Bot, ArrowLeft } from 'lucide-react';

export default function Terms() {
  return (
    <div className="min-h-screen bg-[#FAF9F6] font-inter text-[#2D2D2D]">
      <nav className="px-6 py-4 bg-white/80 backdrop-blur-md sticky top-0 z-50 border-b border-gray-100">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="bg-[#FF6B35] p-2 rounded-xl rotate-3">
              <Bot className="text-white w-6 h-6" />
            </div>
            <span className="text-xl font-bold font-poppins">JobHuntin</span>
          </Link>
          <Link to="/" className="text-sm font-medium hover:text-[#FF6B35] flex items-center gap-2">
            <ArrowLeft className="w-4 h-4" /> Back to Home
          </Link>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="text-4xl font-bold font-poppins mb-8">Terms of Service</h1>
        <div className="prose prose-lg max-w-none prose-headings:font-poppins prose-headings:text-[#2D2D2D] prose-p:text-gray-600 prose-a:text-[#4A90E2]">
          <p className="text-gray-500 mb-8">Last updated: {new Date().toLocaleDateString()}</p>
          
          <h3>1. Acceptance of Terms</h3>
          <p>
            By accessing and using this website, you accept and agree to be bound by the terms and provision of this agreement. 
            In addition, when using these particular services, you shall be subject to any posted guidelines or rules applicable to such services.
          </p>

          <h3>2. Description of Service</h3>
          <p>
            JobHuntin provides an AI-powered job application service. You understand and agree that the Service is provided "AS-IS" and 
            that JobHuntin assumes no responsibility for the timeliness, deletion, mis-delivery or failure to store any user communications or personalization settings.
          </p>

          <h3>3. User Conduct</h3>
          <p>
            You agree to use the Service only for purposes that are legal, proper and in accordance with these Terms and any applicable policies or guidelines.
          </p>

          <h3>4. Intellectual Property</h3>
          <p>
            All content included on this site, such as text, graphics, logos, button icons, images, audio clips, digital downloads, data compilations, and software, is the property of JobHuntin or its content suppliers and protected by international copyright laws.
          </p>

          <h3>5. Termination</h3>
          <p>
            We may terminate or suspend access to our Service immediately, without prior notice or liability, for any reason whatsoever, including without limitation if you breach the Terms.
          </p>

          <h3>6. Contact Us</h3>
          <p>
            If you have any questions about these Terms, please contact us at: <a href="mailto:legal@jobhuntin.com">legal@jobhuntin.com</a>.
          </p>
        </div>
      </main>
      
      <footer className="bg-white border-t border-gray-200 py-12 mt-12">
        <div className="max-w-4xl mx-auto px-6 text-center text-gray-400 text-sm">
          &copy; {new Date().getFullYear()} JobHuntin AI. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
