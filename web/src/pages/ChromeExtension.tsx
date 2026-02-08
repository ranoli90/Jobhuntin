import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Bot, ArrowLeft, Download, Linkedin, Briefcase, Plus, Check } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function ChromeExtension() {
  const [activeStep, setActiveStep] = useState(0);

  // Simulation Loop
  useEffect(() => {
    const timer = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % 4);
    }, 3000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="min-h-screen bg-[#FAF9F6] font-inter text-[#2D2D2D] selection:bg-[#FF6B35] selection:text-white">
      <nav className="px-6 py-4 bg-white/80 backdrop-blur-md sticky top-0 z-50 border-b border-gray-100">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="bg-[#FF6B35] p-2 rounded-xl rotate-3 shadow-lg shadow-orange-500/20">
              <Bot className="text-white w-6 h-6" />
            </div>
            <span className="text-xl font-bold font-poppins">JobHuntin</span>
          </Link>
          <Link to="/" className="text-sm font-medium hover:text-[#FF6B35] flex items-center gap-2 group transition-colors">
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" /> Back to Home
          </Link>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-20">
        <div className="flex flex-col lg:flex-row items-center gap-20">
          <div className="flex-1">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="inline-block bg-blue-50 text-[#4A90E2] px-4 py-1 rounded-full text-sm font-bold mb-6"
            >
              v2.0 Now Available
            </motion.div>
            
            <motion.h1 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="text-5xl md:text-7xl font-extrabold font-poppins mb-8 leading-tight tracking-tight"
            >
              The "Add to Cart" <br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FF6B35] to-[#4A90E2]">for your career.</span>
            </motion.h1>
            
            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="text-xl text-gray-600 mb-10 leading-relaxed max-w-lg"
            >
              Browse LinkedIn, Indeed, or Glassdoor. See a job you like? 
              Click one button. Our AI handles the resume tailoring, cover letter, and submission.
            </motion.p>
            
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="flex flex-wrap gap-4"
            >
              <button className="bg-[#2D2D2D] text-white px-8 py-4 rounded-xl font-bold hover:bg-[#FF6B35] transition-colors flex items-center gap-3 shadow-xl hover:shadow-orange-500/20 transform hover:-translate-y-1">
                <Download className="w-5 h-5" />
                Add to Chrome
                <span className="text-gray-400 font-normal text-sm ml-2">It's free</span>
              </button>
              <button className="bg-white border-2 border-gray-200 text-gray-700 px-8 py-4 rounded-xl font-bold hover:border-[#4A90E2] hover:text-[#4A90E2] transition-colors">
                Watch Demo
              </button>
            </motion.div>
          </div>

          {/* Fake Browser Interaction */}
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4 }}
            className="flex-1 w-full max-w-2xl relative"
          >
            {/* Browser Window */}
            <div className="bg-white rounded-2xl shadow-2xl border border-gray-200 overflow-hidden relative z-10">
              {/* Browser Bar */}
              <div className="bg-gray-100 px-4 py-3 border-b border-gray-200 flex items-center gap-4">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-400" />
                  <div className="w-3 h-3 rounded-full bg-yellow-400" />
                  <div className="w-3 h-3 rounded-full bg-green-400" />
                </div>
                <div className="bg-white rounded-md flex-1 px-3 py-1 text-xs text-gray-400 font-mono flex items-center">
                  <span className="text-gray-300 mr-2">🔒</span> linkedin.com/jobs/view/382910...
                </div>
              </div>

              {/* Web Content */}
              <div className="p-6 h-[400px] bg-gray-50 relative">
                 {/* Job Header */}
                 <div className="flex justify-between items-start mb-6">
                    <div className="flex gap-4">
                      <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-xl">L</div>
                      <div>
                        <div className="h-4 w-48 bg-gray-800 rounded mb-2"></div>
                        <div className="h-3 w-24 bg-gray-400 rounded"></div>
                      </div>
                    </div>
                    {/* The Magic Button */}
                    <motion.button 
                      animate={{ 
                        scale: activeStep === 1 ? [1, 0.9, 1] : 1,
                        backgroundColor: activeStep >= 2 ? "#10B981" : "#2D2D2D"
                      }}
                      className="bg-[#2D2D2D] text-white px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 shadow-lg relative z-50"
                    >
                      {activeStep >= 2 ? (
                        <><Check className="w-4 h-4" /> Added to Queue</>
                      ) : (
                        <><Plus className="w-4 h-4" /> Auto-Apply</>
                      )}
                    </motion.button>
                 </div>

                 {/* Job Body */}
                 <div className="space-y-3 opacity-30">
                   <div className="h-3 w-full bg-gray-300 rounded"></div>
                   <div className="h-3 w-full bg-gray-300 rounded"></div>
                   <div className="h-3 w-3/4 bg-gray-300 rounded"></div>
                   <div className="h-3 w-full bg-gray-300 rounded"></div>
                 </div>

                 {/* Extension Overlay */}
                 <AnimatePresence>
                   {activeStep >= 1 && (
                     <motion.div 
                       initial={{ x: 300, opacity: 0 }}
                       animate={{ x: 0, opacity: 1 }}
                       exit={{ x: 300, opacity: 0 }}
                       className="absolute top-4 right-4 w-72 bg-white rounded-xl shadow-2xl border border-gray-100 p-4 z-40"
                     >
                       <div className="flex items-center gap-2 mb-4 border-b border-gray-100 pb-2">
                         <div className="bg-[#FF6B35] p-1 rounded-lg">
                           <Bot className="w-4 h-4 text-white" />
                         </div>
                         <span className="font-bold text-sm">JobHuntin Agent</span>
                       </div>

                       {activeStep === 1 && (
                         <div className="flex items-center gap-3 text-sm text-gray-600">
                           <div className="w-4 h-4 border-2 border-[#FF6B35] border-t-transparent rounded-full animate-spin" />
                           Parsing job details...
                         </div>
                       )}

                       {activeStep === 2 && (
                         <div className="space-y-3">
                           <div className="flex items-center gap-2 text-sm text-green-600 font-medium">
                             <Check className="w-4 h-4" /> Match Score: 94%
                           </div>
                           <div className="bg-gray-50 p-2 rounded text-xs text-gray-500 font-mono">
                             > Tailoring resume...<br/>
                             > Drafting cover letter...<br/>
                             > Added to priority queue.
                           </div>
                         </div>
                       )}
                       
                       {activeStep === 3 && (
                          <div className="text-center py-4">
                            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-2 text-green-600">
                              <Check className="w-6 h-6" />
                            </div>
                            <h4 className="font-bold text-gray-900">Ready to Apply!</h4>
                            <p className="text-xs text-gray-500">Agent will submit in ~2 mins</p>
                          </div>
                       )}
                     </motion.div>
                   )}
                 </AnimatePresence>
                 
                 {/* Mouse Cursor */}
                 <motion.div 
                   animate={{ 
                     x: activeStep === 0 ? 380 : 400,
                     y: activeStep === 0 ? 40 : 50,
                     scale: activeStep === 1 ? 0.9 : 1
                   }}
                   transition={{ duration: 1 }}
                   className="absolute top-0 left-0 w-6 h-6 pointer-events-none z-50"
                 >
                   <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                     <path d="M3 3L10.07 19.97L12.58 12.58L19.97 10.07L3 3Z" fill="black" stroke="white" strokeWidth="2"/>
                   </svg>
                 </motion.div>
              </div>
            </div>
            
            {/* Background Blob */}
            <div className="absolute -inset-10 bg-gradient-to-tr from-[#FF6B35] to-[#4A90E2] rounded-full blur-[80px] opacity-20 -z-10" />
          </motion.div>
        </div>

        {/* Feature Grid */}
        <div className="mt-32 grid md:grid-cols-3 gap-8">
           {[
             { icon: Linkedin, title: "LinkedIn Integration", desc: "Works on standard posts & Easy Apply." },
             { icon: Briefcase, title: "One-Click Add", desc: "No copy-pasting. Just click and go." },
             { icon: Bot, title: "Smart Matching", desc: "Instant match score overlay on every job." }
           ].map((f, i) => (
             <motion.div 
               key={i}
               initial={{ opacity: 0, y: 20 }}
               whileInView={{ opacity: 1, y: 0 }}
               transition={{ delay: i * 0.1 }}
               viewport={{ once: true }}
               className="bg-white p-8 rounded-3xl border border-gray-100 hover:shadow-xl transition-all hover:-translate-y-1 group"
             >
               <div className="w-14 h-14 bg-gray-50 rounded-2xl flex items-center justify-center mb-6 group-hover:bg-[#FF6B35] group-hover:text-white transition-colors text-[#2D2D2D]">
                 <f.icon className="w-7 h-7" />
               </div>
               <h3 className="text-xl font-bold mb-3 font-poppins">{f.title}</h3>
               <p className="text-gray-600 leading-relaxed">{f.desc}</p>
             </motion.div>
           ))}
        </div>
      </main>

      <footer className="bg-white border-t border-gray-200 py-12">
        <div className="max-w-7xl mx-auto px-6 text-center text-gray-400 text-sm">
          &copy; {new Date().getFullYear()} JobHuntin AI. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
