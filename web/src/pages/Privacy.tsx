import React from 'react';
import { Link } from 'react-router-dom';
import { Bot, ArrowLeft } from 'lucide-react';

export default function Privacy() {
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
        <h1 className="text-4xl font-bold font-poppins mb-8">Privacy Policy</h1>
        <div className="prose prose-lg max-w-none prose-headings:font-poppins prose-headings:text-[#2D2D2D] prose-p:text-gray-600 prose-a:text-[#4A90E2]">
          <p className="text-gray-500 mb-8">Last updated: {new Date().toLocaleDateString()}</p>
          
          <h3>1. Introduction</h3>
          <p>
            Welcome to JobHuntin. We respect your privacy and are committed to protecting your personal data. 
            This privacy policy will inform you as to how we look after your personal data when you visit our website 
            and tell you about your privacy rights and how the law protects you.
          </p>

          <h3>2. Data We Collect</h3>
          <p>
            We may collect, use, store and transfer different kinds of personal data about you which we have grouped together follows:
          </p>
          <ul>
            <li><strong>Identity Data:</strong> includes first name, last name, username or similar identifier.</li>
            <li><strong>Contact Data:</strong> includes email address and telephone number.</li>
            <li><strong>Technical Data:</strong> includes internet protocol (IP) address, your login data, browser type and version.</li>
            <li><strong>Profile Data:</strong> includes your username and password, purchases or orders made by you, your interests, preferences, feedback and survey responses.</li>
            <li><strong>Usage Data:</strong> includes information about how you use our website, products and services.</li>
          </ul>

          <h3>3. How We Use Your Data</h3>
          <p>
            We will only use your personal data when the law allows us to. Most commonly, we will use your personal data in the following circumstances:
          </p>
          <ul>
            <li>Where we need to perform the contract we are about to enter into or have entered into with you.</li>
            <li>Where it is necessary for our legitimate interests (or those of a third party) and your interests and fundamental rights do not override those interests.</li>
            <li>Where we need to comply with a legal or regulatory obligation.</li>
          </ul>

          <h3>4. Data Security</h3>
          <p>
            We have put in place appropriate security measures to prevent your personal data from being accidentally lost, used or accessed in an unauthorized way, altered or disclosed.
          </p>

          <h3>5. Contact Us</h3>
          <p>
            If you have any questions about this privacy policy or our privacy practices, please contact us at: <a href="mailto:privacy@jobhuntin.com">privacy@jobhuntin.com</a>.
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
