import React, { useRef } from 'react';
import { Link } from 'react-router-dom';
import { Bot, ArrowLeft, Star, Quote, Play, Pause, Stamp } from 'lucide-react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { SEO } from '../components/marketing/SEO';

export default function SuccessStories() {
  const scrollRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: scrollRef });
  const x = useTransform(scrollYProgress, [0, 1], ["1%", "-50%"]);

  const stories = [
    {
      name: "Sarah Jenkins",
      role: "Marketing Director",
      company: "TechFlow",
      image: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?ixlib=rb-1.2.1&auto=format&fit=crop&w=256&q=80",
      quote: "I was spending 3 hours a day applying. JobHuntin did it while I slept. I got 5 interviews in the first week.",
      stat: "Hired in 14 days",
      audio: "sarah_clip.mp3"
    },
    {
      name: "Michael Chen",
      role: "Senior Developer",
      company: "CloudScale",
      image: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-1.2.1&auto=format&fit=crop&w=256&q=80",
      quote: "The cover letters it generates are actually better than what I write myself. It picked up nuances in my resume I forgot about.",
      stat: "3 Offers Received",
      audio: "michael_clip.mp3"
    },
    {
      name: "Jessica Alverez",
      role: "Sales Executive",
      company: "Global Sales",
      image: "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?ixlib=rb-1.2.1&auto=format&fit=crop&w=256&q=80",
      quote: "Being in sales, I know it's a numbers game. JobHuntin maximized my volume without sacrificing quality.",
      stat: "$20k Salary Bump",
      audio: "jessica_clip.mp3"
    },
    {
      name: "David Ross",
      role: "Product Manager",
      company: "InnovateLabs",
      image: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?ixlib=rb-1.2.1&auto=format&fit=crop&w=256&q=80",
      quote: "I didn't believe it at first. Then I woke up to an inbox full of 'Let's chat' emails. Game changer.",
      stat: "Remote Role Landed",
      audio: "david_clip.mp3"
    },
    {
      name: "Emily Zhang",
      role: "UX Designer",
      company: "Creative Co",
      image: "https://images.unsplash.com/photo-1580489944761-15a19d654956?ixlib=rb-1.2.1&auto=format&fit=crop&w=256&q=80",
      quote: "My portfolio got more views in 3 days with JobHuntin than in 3 months of manual applying.",
      stat: "Dream Job Secured",
      audio: "emily_clip.mp3"
    }
  ];

  return (
    <div className="min-h-screen bg-[#111] font-inter text-white overflow-x-hidden selection:bg-[#FF6B35] selection:text-white">
      <SEO 
        title="Success Stories | JobHuntin AI - Real People, Real Offers"
        description="See how Sarah, Michael, and others landed their dream jobs in record time using JobHuntin's AI automation. 98% match rates and massive salary bumps."
        ogTitle="Success Stories | JobHuntin AI"
        ogImage="https://jobhuntin.com/og/success-stories.png"
        canonicalUrl="https://jobhuntin.com/success-stories"
        schema={stories.map(story => ({
          "@context": "https://schema.org",
          "@type": "Review",
          "author": {
            "@type": "Person",
            "name": story.name
          },
          "reviewBody": story.quote,
          "reviewRating": {
            "@type": "Rating",
            "ratingValue": "5",
            "bestRating": "5"
          },
          "itemReviewed": {
            "@type": "SoftwareApplication",
            "name": "JobHuntin",
            "applicationCategory": "CareerAutomation"
          }
        }))}
      />
      <nav className="px-6 py-4 fixed top-0 left-0 right-0 z-50 bg-[#111]/80 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="bg-[#FF6B35] p-2 rounded-xl rotate-3 shadow-[0_0_15px_rgba(255,107,53,0.5)]">
              <Bot className="text-white w-6 h-6" />
            </div>
            <span className="text-xl font-bold font-poppins tracking-tight">JobHuntin</span>
          </Link>
          <Link to="/" className="text-sm font-medium text-gray-400 hover:text-white flex items-center gap-2 transition-colors">
            <ArrowLeft className="w-4 h-4" /> Back to Home
          </Link>
        </div>
      </nav>

      <main className="pt-32 pb-20">
        <div className="text-center mb-24 px-6">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="text-5xl md:text-8xl font-extrabold font-poppins mb-8 tracking-tighter leading-tight">
              THEY <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FF6B35] to-[#FF9F43]">WON.</span><br/>
              YOU'RE NEXT.
            </h1>
          </motion.div>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Real people. Real offers. No BS.
          </p>
        </div>

        {/* Horizontal Scroll Section */}
        <div ref={scrollRef} className="h-[300vh] relative">
          <div className="sticky top-40 overflow-hidden">
            <motion.div style={{ x }} className="flex gap-12 pl-12 pr-12 w-max">
              {stories.map((story, i) => (
                <div 
                  key={i} 
                  className="w-[400px] md:w-[500px] bg-[#1a1a1a] p-10 rounded-[3rem] border border-white/5 relative flex-shrink-0 group hover:border-[#FF6B35]/30 transition-colors"
                >
                  {/* Dynamic Hired Stamp */}
                  <motion.div 
                    initial={{ scale: 2, opacity: 0, rotate: -20 }}
                    whileInView={{ scale: 1, opacity: 1, rotate: -12 }}
                    viewport={{ once: true }}
                    className="absolute -top-6 -right-6 border-4 border-green-500 text-green-500 font-black text-2xl px-4 py-2 rounded-lg uppercase tracking-widest opacity-80 mix-blend-screen transform rotate-12"
                  >
                    HIRED
                  </motion.div>

                  <div className="flex items-center gap-6 mb-8">
                    <div className="relative">
                      <img src={story.image} alt={`${story.name} - ${story.role} Success Story`} className="w-20 h-20 rounded-full object-cover border-2 border-white/10" />
                      <div className="absolute -bottom-2 -right-2 bg-[#FF6B35] rounded-full p-1.5 cursor-pointer hover:scale-110 transition-transform">
                        <Play className="w-3 h-3 text-white fill-current" />
                      </div>
                    </div>
                    <div>
                      <h3 className="font-bold text-2xl">{story.name}</h3>
                      <p className="text-gray-400">{story.role}</p>
                      <p className="text-[#FF6B35] text-sm font-bold">@{story.company}</p>
                    </div>
                  </div>

                  <div className="mb-8">
                    <Quote className="w-10 h-10 text-white/10 mb-4" />
                    <p className="text-xl font-light leading-relaxed text-gray-200">
                      "{story.quote}"
                    </p>
                  </div>

                  <div className="flex items-center justify-between border-t border-white/5 pt-6">
                    <div className="flex gap-1 text-[#FF6B35]">
                      {[1,2,3,4,5].map(s => <Star key={s} className="w-4 h-4 fill-current" />)}
                    </div>
                    <div className="font-mono text-sm text-green-400 bg-green-500/10 px-3 py-1 rounded-full">
                      {story.stat}
                    </div>
                  </div>
                </div>
              ))}
              
              {/* CTA Card at the end */}
              <div className="w-[400px] md:w-[500px] bg-[#FF6B35] p-10 rounded-[3rem] flex flex-col justify-center items-center text-center relative overflow-hidden">
                <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10"></div>
                <h3 className="text-4xl font-black mb-6 relative z-10">YOUR TURN.</h3>
                <p className="text-white/80 mb-8 relative z-10 text-lg">Don't let another dream job slip away.</p>
                <Link to="/login" className="bg-white text-[#FF6B35] px-8 py-4 rounded-2xl font-bold text-xl hover:scale-105 transition-transform relative z-10 shadow-xl">
                  Start Free Trial
                </Link>
              </div>
            </motion.div>
          </div>
        </div>
      </main>

      <footer className="bg-[#0a0a0a] border-t border-white/5 py-12">
        <div className="max-w-7xl mx-auto px-6 text-center text-gray-500 text-sm">
          &copy; {new Date().getFullYear()} JobHuntin AI. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
