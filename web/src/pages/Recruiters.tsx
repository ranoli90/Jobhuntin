import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Bot, ArrowLeft, Terminal, User, Code, CheckCircle, Search, Filter } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Recruiters() {
  const [view, setView] = useState<'human' | 'terminal'>('human');

  return (
    <div className={`min-h-screen font-inter transition-colors duration-500 ${view === 'terminal' ? 'bg-[#0d1117] text-gray-300' : 'bg-[#FAF9F6] text-[#2D2D2D]'}`}>
      <nav className={`px-6 py-4 sticky top-0 z-50 border-b transition-colors duration-500 ${view === 'terminal' ? 'bg-[#0d1117]/80 border-gray-800' : 'bg-white/80 border-gray-100'} backdrop-blur-md`}>
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className={`p-2 rounded-xl rotate-3 transition-colors ${view === 'terminal' ? 'bg-green-500' : 'bg-[#FF6B35]'}`}>
              <Bot className="text-white w-6 h-6" />
            </div>
            <span className={`text-xl font-bold font-poppins ${view === 'terminal' ? 'text-white' : 'text-[#2D2D2D]'}`}>JobHuntin</span>
          </Link>
          
          <div className="flex items-center gap-4">
             <div className="bg-gray-200 dark:bg-gray-800 p-1 rounded-full flex gap-1 relative">
                <motion.div 
                   layoutId="activeTab"
                   className={`absolute inset-1 w-1/2 bg-white dark:bg-gray-700 rounded-full shadow-sm`}
                   animate={{ x: view === 'human' ? 0 : '100%' }}
                />
                <button 
                  onClick={() => setView('human')}
                  className={`px-4 py-1.5 rounded-full text-sm font-bold relative z-10 transition-colors ${view === 'human' ? 'text-gray-900' : 'text-gray-500'}`}
                >
                  <User className="w-4 h-4 inline mr-2" />
                  Human
                </button>
                <button 
                  onClick={() => setView('terminal')}
                  className={`px-4 py-1.5 rounded-full text-sm font-bold relative z-10 transition-colors ${view === 'terminal' ? 'text-white' : 'text-gray-500'}`}
                >
                  <Terminal className="w-4 h-4 inline mr-2" />
                  Terminal
                </button>
             </div>
             <Link to="/" className={`text-sm font-medium flex items-center gap-2 ${view === 'terminal' ? 'hover:text-green-400' : 'hover:text-[#FF6B35]'}`}>
               <ArrowLeft className="w-4 h-4" /> Back
             </Link>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-20 relative">
        <AnimatePresence mode="wait">
          {view === 'human' ? (
            <motion.div 
               key="human"
               initial={{ opacity: 0, x: -20 }}
               animate={{ opacity: 1, x: 0 }}
               exit={{ opacity: 0, x: 20 }}
               className="space-y-20"
            >
               <div className="text-center">
                  <h1 className="text-5xl md:text-7xl font-bold font-poppins mb-6 leading-tight">
                    Hire talent, <br/>
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FF6B35] to-[#4A90E2]">not keyword stuffers.</span>
                  </h1>
                  <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-8">
                    Our AI pre-interviews every candidate before they reach your inbox. You get structured data, not PDF chaos.
                  </p>
                  <button className="bg-[#2D2D2D] text-white px-8 py-4 rounded-xl font-bold hover:bg-[#FF6B35] transition-colors shadow-lg">
                    Request API Access
                  </button>
               </div>

               <div className="grid md:grid-cols-2 gap-12 items-center">
                  <div className="relative">
                    <div className="absolute -inset-4 bg-gradient-to-r from-[#FF6B35] to-[#4A90E2] rounded-[2rem] opacity-20 blur-xl" />
                    <div className="bg-white p-8 rounded-3xl shadow-xl relative border border-gray-100">
                       <div className="flex items-center gap-4 mb-6 border-b border-gray-100 pb-4">
                         <img src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-1.2.1&auto=format&fit=crop&w=64&q=80" className="w-12 h-12 rounded-full" />
                         <div>
                           <h3 className="font-bold">Michael Chen</h3>
                           <p className="text-sm text-gray-500">Senior React Developer</p>
                         </div>
                         <div className="ml-auto bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs font-bold">
                           98% Match
                         </div>
                       </div>
                       <div className="space-y-4">
                         <div className="bg-gray-50 p-4 rounded-xl">
                           <p className="text-xs font-bold text-gray-400 uppercase mb-1">Q: Experience with High Scale?</p>
                           <p className="text-sm text-gray-800">"Yes, at CloudScale I optimized a dashboard handling 50k WS connections..."</p>
                         </div>
                         <div className="bg-gray-50 p-4 rounded-xl">
                           <p className="text-xs font-bold text-gray-400 uppercase mb-1">Q: Salary Expectations?</p>
                           <p className="text-sm text-gray-800">$160k - $180k (Remote)</p>
                         </div>
                       </div>
                    </div>
                  </div>
                  <div>
                    <h3 className="text-3xl font-bold font-poppins mb-6">Structured Candidate Cards</h3>
                    <p className="text-gray-600 text-lg leading-relaxed mb-6">
                      Stop parsing PDFs. We deliver JSON-ready profiles with verified answers to your screening questions.
                    </p>
                    <ul className="space-y-4">
                      <li className="flex items-center gap-3"><CheckCircle className="w-5 h-5 text-green-500" /> Auto-screened for skills</li>
                      <li className="flex items-center gap-3"><CheckCircle className="w-5 h-5 text-green-500" /> Salary expectations verified</li>
                      <li className="flex items-center gap-3"><CheckCircle className="w-5 h-5 text-green-500" /> "Human-verified" badge</li>
                    </ul>
                  </div>
               </div>
            </motion.div>
          ) : (
            <motion.div 
               key="terminal"
               initial={{ opacity: 0, x: 20 }}
               animate={{ opacity: 1, x: 0 }}
               exit={{ opacity: 0, x: -20 }}
               className="font-mono"
            >
               <div className="text-center mb-16">
                  <h1 className="text-5xl md:text-7xl font-bold mb-6 text-green-400">
                    $ curl api.jobhuntin.io/v1/candidates
                  </h1>
                  <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-8">
                    Direct pipe to the top 1% of the market. Webhooks, JSON streams, and zero UI friction.
                  </p>
                  <button className="border border-green-500 text-green-500 px-8 py-4 rounded-xl font-bold hover:bg-green-500/10 transition-colors">
                    Generate API Key
                  </button>
               </div>

               <div className="max-w-4xl mx-auto bg-[#0d1117] border border-gray-800 rounded-lg overflow-hidden shadow-2xl">
                 <div className="bg-[#161b22] px-4 py-2 border-b border-gray-800 flex items-center gap-2">
                   <div className="w-3 h-3 rounded-full bg-red-500" />
                   <div className="w-3 h-3 rounded-full bg-yellow-500" />
                   <div className="w-3 h-3 rounded-full bg-green-500" />
                   <span className="ml-2 text-xs text-gray-500">bash — 80x24</span>
                 </div>
                 <div className="p-6 text-sm text-gray-300 overflow-x-auto">
                   <p className="mb-2"><span className="text-green-400">➜</span> <span className="text-blue-400">~</span> curl -X POST https://api.jobhuntin.io/webhook \</p>
                   <p className="mb-2 pl-4">-H "Authorization: Bearer sk_live_..." \</p>
                   <p className="mb-4 pl-4">-d '{"{"}"criteria": ["react", "node", "5+ years"]{"}"}'</p>
                   
                   <p className="mb-2 text-gray-500"># Response stream initiating...</p>
                   <p className="mb-2 text-green-400">{"{"}</p>
                   <p className="mb-1 pl-4">"id": "cand_892301",</p>
                   <p className="mb-1 pl-4">"match_score": 0.98,</p>
                   <p className="mb-1 pl-4">"github_activity": "high",</p>
                   <p className="mb-1 pl-4">"screening": {"{"}</p>
                   <p className="mb-1 pl-8">"q1_scale": "Architected k8s cluster for...",</p>
                   <p className="mb-1 pl-8">"q2_salary": "160000"</p>
                   <p className="mb-1 pl-4">{"}"}</p>
                   <p className="text-green-400">{"}"}</p>
                   <motion.div 
                     animate={{ opacity: [0, 1, 0] }}
                     transition={{ repeat: Infinity, duration: 0.8 }}
                     className="inline-block w-2 h-4 bg-green-400 ml-1 align-middle"
                   />
                 </div>
               </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <footer className={`border-t py-12 transition-colors duration-500 ${view === 'terminal' ? 'bg-[#0d1117] border-gray-800' : 'bg-white border-gray-200'}`}>
        <div className={`max-w-7xl mx-auto px-6 text-center text-sm ${view === 'terminal' ? 'text-gray-600' : 'text-gray-400'}`}>
          &copy; {new Date().getFullYear()} JobHuntin AI. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
