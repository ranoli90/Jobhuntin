import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { Bot, ArrowLeft, MapPin, Sparkles, Briefcase, Zap } from 'lucide-react';
import { SEO } from '../components/marketing/SEO';
import { motion } from 'framer-motion';

export default function JobNiche() {
  const { role, city } = useParams<{ role: string; city: string }>();
  
  const formattedRole = role?.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ') || "Professional";
  const formattedCity = city?.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ') || "Remote";

  const title = `AI ${formattedRole} Jobs in ${formattedCity} | Auto-Apply with JobHuntin`;
  const description = `Find and auto-apply to the best ${formattedRole} roles in ${formattedCity}. JobHuntin's AI agent hunts for ${formattedRole} opportunities, tailors your resume, and applies while you sleep.`;
  const canonicalUrl = `https://jobhuntin.com/jobs/${role ?? ''}/${city ?? ''}`;
  const ogImage = `https://sorce-web.onrender.com/api/og?job=${encodeURIComponent(formattedRole)}&company=${encodeURIComponent(formattedCity)}&score=100&location=${encodeURIComponent(formattedCity)}`;

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-primary-500/20 selection:text-primary-700">
      <SEO 
        title={title}
        description={description}
        ogTitle={title}
        ogImage={ogImage}
        canonicalUrl={canonicalUrl}
        schema={{
          "@context": "https://schema.org",
          "@type": "CollectionPage",
          "name": title,
          "description": description,
          "url": canonicalUrl,
          "about": formattedRole,
          "hasPart": {
            "@type": "ItemList",
            "name": `${formattedRole} roles in ${formattedCity}`
          }
        }}
      />
      
      <nav className="px-6 py-4 bg-white/80 backdrop-blur-md sticky top-0 z-50 border-b border-gray-100">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="bg-gradient-to-tr from-primary-500 to-primary-600 p-2 rounded-xl rotate-3 shadow-lg shadow-primary-500/20">
              <Bot className="text-white w-6 h-6" />
            </div>
            <span className="text-xl font-bold font-display text-slate-900">JobHuntin</span>
          </Link>
          <Link to="/" className="text-sm font-medium text-slate-600 hover:text-primary-600 flex items-center gap-2 group transition-colors">
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" /> Back to Home
          </Link>
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-6 py-16">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center gap-2 bg-orange-50 text-primary-600 px-4 py-1 rounded-full text-sm font-bold mb-6 border border-orange-100">
            <Sparkles className="w-4 h-4" />
            AI-Powered Job Search in {formattedCity}
          </div>
          <h1 className="text-4xl md:text-6xl font-black font-display mb-6 text-slate-900">
            {formattedRole} Jobs in <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-500 to-amber-500">{formattedCity}</span>
          </h1>
          <p className="text-xl text-slate-500 max-w-2xl mx-auto font-medium">
            Stop manually applying to {formattedRole} roles. Let our AI agent handle the grind in {formattedCity} while you focus on the interview.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-8 mb-20">
          <div className="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm hover:shadow-lg transition-all">
            <div className="w-12 h-12 bg-blue-50 rounded-2xl flex items-center justify-center mb-6 text-blue-500">
              <MapPin className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-lg mb-2 text-slate-900">Localized Hunts</h3>
            <p className="text-slate-500 text-sm font-medium">Deep scanning of local {formattedCity} job boards and company career pages.</p>
          </div>
          <div className="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm hover:shadow-lg transition-all">
            <div className="w-12 h-12 bg-orange-50 rounded-2xl flex items-center justify-center mb-6 text-primary-500">
              <Briefcase className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-lg mb-2 text-slate-900">Role Specific</h3>
            <p className="text-slate-500 text-sm font-medium">Optimized for {formattedRole} skills and industry-specific keywords.</p>
          </div>
          <div className="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm hover:shadow-lg transition-all">
            <div className="w-12 h-12 bg-green-50 rounded-2xl flex items-center justify-center mb-6 text-emerald-500">
              <Zap className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-lg mb-2 text-slate-900">Instant Apply</h3>
            <p className="text-slate-500 text-sm font-medium">Automated tailoring and submission for every {formattedRole} opening found.</p>
          </div>
        </div>

        <div className="bg-slate-900 rounded-[3rem] p-12 text-white text-center relative overflow-hidden shadow-2xl">
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary-500/20 rounded-full blur-3xl" />
          <h2 className="text-3xl font-bold mb-6 relative z-10 font-display">Ready to start your {formattedCity} hunt?</h2>
          <p className="text-slate-400 mb-10 relative z-10 max-w-lg mx-auto text-lg font-medium">
            Join thousands of {formattedRole}s who have skipped the application line using JobHuntin.
          </p>
          <Link 
            to="/login" 
            className="inline-block bg-primary-600 hover:bg-primary-700 text-white px-10 py-4 rounded-2xl font-bold text-lg hover:scale-105 transition-transform shadow-xl shadow-primary-500/20"
          >
            Start My {formattedCity} Run
          </Link>
        </div>
      </main>

      <footer className="bg-white border-t border-slate-200 py-12 mt-20">
        <div className="max-w-7xl mx-auto px-6 text-center text-slate-400 text-sm font-medium">
          &copy; {new Date().getFullYear()} JobHuntin AI. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
