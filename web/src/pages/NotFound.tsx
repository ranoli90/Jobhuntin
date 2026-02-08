import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Bot, ArrowLeft, HelpCircle, FileQuestion, MessageCircle } from 'lucide-react';
import { SEO } from '../components/marketing/SEO';
import { Button } from '../components/ui/Button';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-primary-500/20 selection:text-primary-700">
      <SEO 
        title="404 - Page Not Found | JobHuntin"
        description="The page you are looking for doesn't exist. Let's get you back to hunting."
      />
      
      <main className="flex flex-col items-center justify-center min-h-screen px-6 text-center relative overflow-hidden">
        {/* Background Elements */}
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
           <div className="absolute top-[20%] left-[20%] w-64 h-64 bg-primary-500/10 rounded-full blur-3xl animate-pulse" />
           <div className="absolute bottom-[20%] right-[20%] w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        </div>

        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="relative z-10 max-w-2xl"
        >
          <div className="w-24 h-24 bg-slate-100 rounded-3xl flex items-center justify-center mx-auto mb-8 shadow-inner rotate-12">
            <Bot className="w-12 h-12 text-slate-400" />
          </div>
          
          <h1 className="text-8xl font-black font-display text-slate-900 mb-6 tracking-tighter">
            404
          </h1>
          <h2 className="text-3xl font-bold mb-6 text-slate-800">
            Lost in the Application Void?
          </h2>
          <p className="text-xl text-slate-500 mb-10 leading-relaxed max-w-lg mx-auto">
            The page you're looking for seems to have been rejected by the server. 
            Don't worry, unlike most applications, this one has a happy ending.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/">
              <Button size="lg" className="rounded-xl px-8 shadow-xl shadow-primary-500/20">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to HQ
              </Button>
            </Link>
            <Link to="/login">
               <Button variant="outline" size="lg" className="rounded-xl px-8 bg-white hover:bg-slate-50">
                 Login to Dashboard
               </Button>
            </Link>
          </div>

          <div className="mt-16 grid grid-cols-1 sm:grid-cols-3 gap-6 text-left">
            <Link to="/guides" className="p-4 bg-white rounded-2xl border border-slate-100 hover:border-primary-200 hover:shadow-lg transition-all group">
              <div className="w-10 h-10 bg-orange-50 rounded-lg flex items-center justify-center mb-3 text-primary-500 group-hover:bg-primary-500 group-hover:text-white transition-colors">
                <FileQuestion className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-slate-900 mb-1">Read Guides</h3>
              <p className="text-xs text-slate-500">Master the art of AI job hunting.</p>
            </Link>
            <Link to="/pricing" className="p-4 bg-white rounded-2xl border border-slate-100 hover:border-primary-200 hover:shadow-lg transition-all group">
              <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center mb-3 text-blue-500 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                <HelpCircle className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-slate-900 mb-1">View Pricing</h3>
              <p className="text-xs text-slate-500">Simple plans for serious hunters.</p>
            </Link>
            <a href="mailto:support@jobhuntin.com" className="p-4 bg-white rounded-2xl border border-slate-100 hover:border-primary-200 hover:shadow-lg transition-all group">
              <div className="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center mb-3 text-green-500 group-hover:bg-green-500 group-hover:text-white transition-colors">
                <MessageCircle className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-slate-900 mb-1">Contact Support</h3>
              <p className="text-xs text-slate-500">We're here to help you win.</p>
            </a>
          </div>
        </motion.div>
      </main>
    </div>
  );
}
