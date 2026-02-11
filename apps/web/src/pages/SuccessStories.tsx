import React, { useRef } from 'react';
import { Link } from 'react-router-dom';
import { Star, Quote, Play } from 'lucide-react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { SEO } from '../components/marketing/SEO';
import { Button } from '../components/ui/Button';

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
    <div className="font-sans text-slate-900 overflow-x-hidden">
      <SEO 
        title="Success Stories | JobHuntin AI — They Got Hired. You're Next."
        description="Real people who stopped scrolling and started interviewing. See how JobHuntin users landed offers in days, not months."
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

      <main className="pt-32 pb-20">
        <div className="text-center mb-24 px-6">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="text-5xl md:text-8xl font-black font-display mb-8 tracking-tighter leading-tight text-slate-900">
              THEY <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-500 to-amber-500">WON.</span><br/>
              YOU'RE NEXT.
            </h1>
          </motion.div>
          <p className="text-xl text-slate-500 max-w-2xl mx-auto font-medium">
            Real people. Real offers. No BS.
          </p>
        </div>

        {/* Responsive Layout: Stack on Mobile, Scroll on Desktop */}
        <div className="lg:hidden px-6 space-y-12">
          {stories.map((story, i) => (
            <div 
              key={i} 
              className="w-full bg-white p-8 rounded-3xl border border-slate-100 shadow-xl relative"
            >
              {/* Hired Stamp */}
              <div className="absolute -top-4 -right-4 border-2 border-emerald-500 text-emerald-600 font-black text-sm px-3 py-1 rounded-md uppercase tracking-widest bg-emerald-50 transform rotate-12 shadow-sm">
                HIRED
              </div>

              <div className="flex items-center gap-4 mb-6">
                <img src={story.image} alt={story.name} className="w-16 h-16 rounded-full object-cover border-2 border-white shadow-md" />
                <div>
                  <h3 className="font-bold text-lg text-slate-900">{story.name}</h3>
                  <p className="text-slate-500 text-sm">{story.role}</p>
                </div>
              </div>

              <p className="text-lg font-medium leading-relaxed text-slate-700 mb-6 relative z-10">
                "{story.quote}"
              </p>

              <div className="flex items-center justify-between border-t border-slate-100 pt-4">
                <div className="flex gap-0.5 text-amber-400">
                  {[1,2,3,4,5].map(s => <Star key={s} className="w-3 h-3 fill-current" />)}
                </div>
                <div className="font-mono text-xs text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full font-bold">
                  {story.stat}
                </div>
              </div>
            </div>
          ))}
          
           {/* CTA Card Mobile */}
           <div className="w-full bg-gradient-to-br from-primary-500 to-primary-600 p-8 rounded-3xl text-center relative overflow-hidden shadow-xl">
             <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10"></div>
             <h3 className="text-3xl font-black mb-4 relative z-10 text-white">YOUR TURN.</h3>
             <Button asChild className="w-full bg-white text-primary-600 hover:bg-slate-50 border-none shadow-lg text-lg font-bold">
               <Link to="/login">
                 Start Free Trial
               </Link>
             </Button>
           </div>
        </div>

        {/* Horizontal Scroll Section - Desktop Only */}
        <div ref={scrollRef} className="hidden lg:block h-[300vh] relative">
          <div className="sticky top-40 overflow-hidden">
            <motion.div style={{ x }} className="flex gap-12 pl-12 pr-12 w-max">
              {stories.map((story, i) => (
                <div 
                  key={i} 
                  className="w-[500px] bg-white p-10 rounded-[3rem] border border-slate-100 shadow-2xl shadow-slate-200/50 relative flex-shrink-0 group hover:border-primary-200 transition-colors"
                >
                  {/* Dynamic Hired Stamp */}
                  <motion.div 
                    initial={{ scale: 2, opacity: 0, rotate: -20 }}
                    whileInView={{ scale: 1, opacity: 1, rotate: -12 }}
                    viewport={{ once: true }}
                    className="absolute -top-6 -right-6 border-4 border-emerald-500 text-emerald-600 font-black text-2xl px-4 py-2 rounded-lg uppercase tracking-widest bg-emerald-50/90 backdrop-blur transform rotate-12 shadow-lg"
                  >
                    HIRED
                  </motion.div>

                  <div className="flex items-center gap-6 mb-8">
                    <div className="relative">
                      <img src={story.image} alt={`${story.name} - ${story.role} Success Story`} className="w-20 h-20 rounded-full object-cover border-4 border-white shadow-lg" />
                      <div className="absolute -bottom-2 -right-2 bg-primary-500 rounded-full p-1.5 cursor-pointer hover:scale-110 transition-transform shadow-md">
                        <Play className="w-3 h-3 text-white fill-current" />
                      </div>
                    </div>
                    <div>
                      <h3 className="font-bold text-2xl text-slate-900">{story.name}</h3>
                      <p className="text-slate-500">{story.role}</p>
                      <p className="text-primary-600 text-sm font-bold">@{story.company}</p>
                    </div>
                  </div>

                  <div className="mb-8 relative">
                    <Quote className="w-10 h-10 text-slate-100 absolute -top-4 -left-4 -z-10" />
                    <p className="text-xl font-medium leading-relaxed text-slate-700 relative z-10">
                      "{story.quote}"
                    </p>
                  </div>

                  <div className="flex items-center justify-between border-t border-slate-100 pt-6">
                    <div className="flex gap-1 text-amber-400">
                      {[1,2,3,4,5].map(s => <Star key={s} className="w-4 h-4 fill-current" />)}
                    </div>
                    <div className="font-mono text-sm text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full font-bold">
                      {story.stat}
                    </div>
                  </div>
                </div>
              ))}
              
              {/* CTA Card at the end */}
              <div className="w-[500px] bg-gradient-to-br from-primary-500 to-primary-600 p-10 rounded-[3rem] flex flex-col justify-center items-center text-center relative overflow-hidden shadow-2xl shadow-primary-500/30">
                <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10"></div>
                <h3 className="text-4xl font-black mb-6 relative z-10 text-white">YOUR TURN.</h3>
                <p className="text-white/90 mb-8 relative z-10 text-lg font-medium">Every hour you wait, someone else gets the interview you wanted.</p>
                <Button asChild className="bg-white text-primary-600 hover:bg-slate-50 hover:scale-105 transition-transform relative z-10 shadow-xl hover:shadow-2xl h-16 px-8 text-xl font-bold rounded-2xl border-none">
                  <Link to="/login">
                    Start Free Trial
                  </Link>
                </Button>
              </div>
            </motion.div>
          </div>
        </div>
      </main>
    </div>
  );
}
