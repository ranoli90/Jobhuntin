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
    <div className="min-h-screen bg-[#FAF9F6] font-inter text-[#2D2D2D]">
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

      <main className="max-w-5xl mx-auto px-6 py-16">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center gap-2 bg-orange-50 text-[#FF6B35] px-4 py-1 rounded-full text-sm font-bold mb-6">
            <Sparkles className="w-4 h-4" />
            AI-Powered Job Search in {formattedCity}
          </div>
          <h1 className="text-4xl md:text-6xl font-extrabold font-poppins mb-6">
            {formattedRole} Jobs in <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FF6B35] to-[#4A90E2]">{formattedCity}</span>
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Stop manually applying to {formattedRole} roles. Let our AI agent handle the grind in {formattedCity} while you focus on the interview.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-8 mb-20">
          <div className="bg-white p-8 rounded-3xl border border-gray-100 shadow-sm">
            <div className="w-12 h-12 bg-blue-50 rounded-2xl flex items-center justify-center mb-6 text-[#4A90E2]">
              <MapPin className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-lg mb-2">Localized Hunts</h3>
            <p className="text-gray-500 text-sm">Deep scanning of local {formattedCity} job boards and company career pages.</p>
          </div>
          <div className="bg-white p-8 rounded-3xl border border-gray-100 shadow-sm">
            <div className="w-12 h-12 bg-orange-50 rounded-2xl flex items-center justify-center mb-6 text-[#FF6B35]">
              <Briefcase className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-lg mb-2">Role Specific</h3>
            <p className="text-gray-500 text-sm">Optimized for {formattedRole} skills and industry-specific keywords.</p>
          </div>
          <div className="bg-white p-8 rounded-3xl border border-gray-100 shadow-sm">
            <div className="w-12 h-12 bg-green-50 rounded-2xl flex items-center justify-center mb-6 text-green-500">
              <Zap className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-lg mb-2">Instant Apply</h3>
            <p className="text-gray-500 text-sm">Automated tailoring and submission for every {formattedRole} opening found.</p>
          </div>
        </div>

        <div className="bg-gray-900 rounded-[3rem] p-12 text-white text-center relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-[#FF6B35]/10 rounded-full blur-3xl" />
          <h2 className="text-3xl font-bold mb-6 relative z-10">Ready to start your {formattedCity} hunt?</h2>
          <p className="text-gray-400 mb-10 relative z-10 max-w-lg mx-auto">
            Join thousands of {formattedRole}s who have skipped the application line using JobHuntin.
          </p>
          <Link 
            to="/login" 
            className="inline-block bg-[#FF6B35] text-white px-10 py-4 rounded-2xl font-bold text-lg hover:scale-105 transition-transform shadow-xl shadow-orange-500/20"
          >
            Start My {formattedCity} Run
          </Link>
        </div>
      </main>

      <footer className="bg-white border-t border-gray-200 py-12 mt-20">
        <div className="max-w-7xl mx-auto px-6 text-center text-gray-400 text-sm">
          &copy; {new Date().getFullYear()} JobHuntin AI. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
