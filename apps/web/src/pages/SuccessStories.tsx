import React, { useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Star, Quote, Volume2, VolumeX } from 'lucide-react';
import { motion, useScroll, useTransform, useReducedMotion } from 'framer-motion';
import { SEO } from '../components/marketing/SEO';
import { Button } from '../components/ui/Button';
import { t, getLocale } from '../lib/i18n';

export default function SuccessStories() {
  const locale = getLocale();
  const scrollRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: scrollRef });
  const x = useTransform(scrollYProgress, [0, 1], ["1%", "-50%"]);
  const shouldReduceMotion = useReducedMotion();
  const [playingAudio, setPlayingAudio] = useState<string | null>(null);

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
      name: "Jessica Alvarez",
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
    <div className="font-sans text-slate-900 dark:text-slate-100 overflow-x-hidden bg-white dark:bg-slate-950">
      <SEO
        title="Success Stories | Real Users Share How They Got Hired with JobHuntin"
        description="Real JobHuntin success stories: Users landed jobs in 14 days, got salary bumps, and received multiple offers using our AI auto-apply platform. Read their testimonials."
        ogTitle="Success Stories | JobHuntin Users Got Hired"
        ogImage="https://jobhuntin.com/og/success-stories.png"
        canonicalUrl="https://jobhuntin.com/success-stories"
        includeDate={true}
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
            <h1 className="text-5xl md:text-8xl font-black font-display mb-8 tracking-tighter leading-tight text-slate-900 dark:text-slate-100">
              {t("successStories.headingWon", locale)} <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-500 to-amber-500">{t("successStories.headingNext", locale)}</span><br />
              {t("successStories.headingYou", locale)}
            </h1>
          </motion.div>
          <p className="text-xl text-slate-500 dark:text-slate-400 max-w-2xl mx-auto font-medium">
            {t("successStories.subtitle", locale)}
          </p>
        </div>

        {/* Responsive Layout: Stack on Mobile, Scroll on Desktop */}
        <div className="lg:hidden px-6 space-y-12">
          {stories.map((story, i) => (
            <StoryCard key={i} story={story} index={i} isMobile={true} playingAudio={playingAudio} setPlayingAudio={setPlayingAudio} locale={locale} />
          ))}

          {/* CTA Card Mobile */}
          <div className="w-full bg-gradient-to-br from-primary-500 to-primary-600 p-8 rounded-3xl text-center relative overflow-hidden shadow-xl">
            <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10"></div>
            <h3 className="text-3xl font-black mb-4 relative z-10 text-white">{t("successStories.ctaTitle", locale)}</h3>
            <p className="text-white/90 mb-6 relative z-10 font-medium">{t("successStories.ctaDescription", locale)}</p>
            <Button asChild className="w-full bg-white text-primary-600 hover:bg-slate-50 border-none shadow-lg text-lg font-bold">
              <Link to="/login">
                {t("successStories.startFreeTrial", locale)}
              </Link>
            </Button>
          </div>
        </div>

        {/* Horizontal Scroll Section - Desktop Only */}
        <div ref={scrollRef} className="hidden lg:block relative" style={{ height: shouldReduceMotion ? 'auto' : '300vh' }}>
          <div className={`sticky ${shouldReduceMotion ? 'relative top-0' : 'top-40'} overflow-hidden`}>
            <motion.div
              style={{
                x: shouldReduceMotion ? 0 : x,
                display: shouldReduceMotion ? 'grid' : 'flex',
                gridTemplateColumns: shouldReduceMotion ? 'repeat(auto-fit, minmax(500px, 1fr))' : 'none',
                gap: shouldReduceMotion ? '2rem' : '3rem',
                padding: shouldReduceMotion ? '0 3rem' : '0 3rem',
                width: shouldReduceMotion ? '100%' : 'max-content'
              }}
              className="w-max"
            >
              {stories.map((story, i) => (
                <StoryCard key={i} story={story} index={i} isMobile={false} playingAudio={playingAudio} setPlayingAudio={setPlayingAudio} locale={locale} />
              ))}

              {/* CTA Card at the end */}
              <div className="w-[500px] bg-gradient-to-br from-primary-500 to-primary-600 p-10 rounded-[3rem] flex flex-col justify-center items-center text-center relative overflow-hidden shadow-2xl shadow-primary-500/30">
                <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10"></div>
                <h3 className="text-4xl font-black mb-6 relative z-10 text-white">{t("successStories.ctaTitle", locale)}</h3>
                <p className="text-white/90 mb-8 relative z-10 text-lg font-medium">{t("successStories.ctaDescription", locale)}</p>
                <Button asChild className="bg-white text-primary-600 hover:bg-slate-50 hover:scale-105 transition-transform relative z-10 shadow-xl hover:shadow-2xl h-16 px-8 text-xl font-bold rounded-2xl border-none">
                  <Link to="/login">
                    {t("successStories.startFreeTrial", locale)}
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

// Story Card Component
const StoryCard = ({
  story,
  index,
  isMobile,
  playingAudio,
  setPlayingAudio,
  locale
}: {
  story: any;
  index: number;
  isMobile: boolean;
  playingAudio: string | null;
  setPlayingAudio: (audio: string | null) => void;
  locale: string;
}) => {
  const shouldReduceMotion = useReducedMotion();
  const isCurrentlyPlaying = playingAudio === story.audio;

  const handlePlayAudio = () => {
    if (isCurrentlyPlaying) {
      setPlayingAudio(null);
    } else {
      setPlayingAudio(story.audio);
    }
  };

  return (
    <div
      className={`${isMobile ? 'w-full' : 'w-[500px]'} bg-white dark:bg-slate-900 ${isMobile ? 'p-8' : 'p-10'} rounded-3xl border border-slate-100 dark:border-slate-700 shadow-xl relative flex-shrink-0 group hover:border-primary-200 dark:hover:border-primary-600 transition-colors overflow-hidden`}
    >
      {/* Hired Stamp */}
      {/* Hired Ribbon */}
      <div className="absolute top-6 -right-12 bg-emerald-500 text-white py-1 px-12 rotate-45 transform shadow-md text-xs font-black tracking-widest uppercase z-10">
        {t("successStories.hired", locale)}
      </div>

      <div className="flex items-center gap-4 mb-6">
        <div className="relative">
          <img
            src={story.image}
            alt={`${story.name} - ${story.role} Success Story`}
            className={`${isMobile ? 'w-16 h-16' : 'w-20 h-20'} rounded-full object-cover border-4 border-white shadow-lg`}
            loading="lazy"
          />
          <div className="absolute inset-0 bg-black/20 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <button
              onClick={handlePlayAudio}
              className="bg-white/90 rounded-full p-2 cursor-pointer hover:scale-110 transition-transform shadow-lg backdrop-blur-sm"
              aria-label={isCurrentlyPlaying ? 'Pause audio' : 'Play audio testimonial'}
              aria-pressed={isCurrentlyPlaying}
            >
              {isCurrentlyPlaying ? (
                <VolumeX className="w-4 h-4 text-slate-900" />
              ) : (
                <Volume2 className="w-4 h-4 text-slate-900" />
              )}
            </button>
          </div>
        </div>
        <div>
          <h3 className={`font-bold ${isMobile ? 'text-lg' : 'text-2xl'} text-slate-900 dark:text-slate-100`}>{story.name}</h3>
          <p className="text-slate-500 dark:text-slate-400">{story.role}</p>
          {!isMobile && <p className="text-primary-600 text-sm font-bold">@{story.company}</p>}
        </div>
      </div>

      <div className={`mb-${isMobile ? '6' : '8'} relative`}>
        <Quote className={`w-${isMobile ? '8' : '10'} h-${isMobile ? '8' : '10'} text-slate-100 absolute -top-4 -left-4 -z-10`} />
        <p className={`${isMobile ? 'text-lg' : 'text-xl'} font-medium leading-relaxed text-slate-700 dark:text-slate-300 relative z-10`}>
          "{story.quote}"
        </p>
      </div>

      <div className="flex items-center justify-between border-t border-slate-100 dark:border-slate-700 pt-4">
        <div className="flex gap-0.5 text-amber-400">
          {[1, 2, 3, 4, 5].map(s => <Star key={s} className={`w-${isMobile ? '3' : '4'} h-${isMobile ? '3' : '4'} fill-current`} />)}
        </div>
        <div className={`font-mono ${isMobile ? 'text-xs' : 'text-sm'} text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/30 px-${isMobile ? '2' : '3'} py-1 rounded-full font-bold`}>
          {story.stat}
        </div>
      </div>
    </div>
  );
};
