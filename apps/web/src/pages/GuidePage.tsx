import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Bot, ArrowLeft, BookOpen, Clock, Calendar, Share2, ChevronRight, Zap, Shield, Target, Menu, X } from 'lucide-react';
import { SEO } from '../components/marketing/SEO';
import { ConversionCTA } from '../components/seo/ConversionCTA';
import { BreadcrumbNav } from '../components/seo/BreadcrumbNav';
import { motion, useReducedMotion } from 'framer-motion';
import { config } from '../config';
import { XSSProtection } from '../lib/validation';
import authors from '../data/authors.json';
import Author from '../components/marketing/Author';
import RelatedGuides from '../components/marketing/RelatedGuides';
import { useDynamicData } from '../hooks/useDynamicData';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';

export default function GuidePage() {
  const { guideSlug } = useParams<{ guideSlug: string }>();
  const { data: guidesData, loading } = useDynamicData(() => import('../data/guides.json'));
  const guides = guidesData as Record<string, { title: string; category: string; readTime: string; content: string; authorId?: string }> | null;
  const guide = guideSlug && guides ? guides[guideSlug] : null;
  const author = guide ? authors.find(a => a.id === guide.authorId) : null;
  const [navOpen, setNavOpen] = useState(false);
  const [headings, setHeadings] = useState<Array<{id: string, text: string, level: number}>>([]);
  const shouldReduceMotion = useReducedMotion();

  // Extract headings for navigation (sanitize to prevent XSS from CMS content)
  useEffect(() => {
    if (guide) {
      const tempDiv = document.createElement("div");
      // nosemgrep: javascript.browser.security.insecure-document-method - content sanitized via XSSProtection
      tempDiv.innerHTML = XSSProtection.sanitizeHTML(guide.content);
      const headingElements = tempDiv.querySelectorAll('h3, h4');
      const extractedHeadings = Array.from(headingElements).map((heading, index) => ({
        id: `heading-${index}`,
        text: heading.textContent || '',
        level: Number.parseInt(heading.tagName.charAt(1))
      }));
      setHeadings(extractedHeadings);
    }
  }, [guide]);

  // Generate HowTo schema based on guide content
  const generateHowToSchema = () => {
    if (!guide) return null;
    
    const steps = headings.map((heading, index) => ({
      "@type": "HowToStep",
      "name": heading.text,
      "position": index + 1,
      "text": `Learn about ${heading.text.toLowerCase()} in our comprehensive guide.`
    }));

    return {
      "@context": "https://schema.org",
      "@type": "HowTo",
      "name": guide.title,
      "description": `Step-by-step guide: ${guide.title.toLowerCase()}`,
      "totalTime": `PT${guide.readTime.replace(' min', '')}M`,
      "estimatedCost": {
        "@type": "MonetaryAmount",
        "currency": "USD",
        "value": "0"
      },
      "step": steps.length > 0 ? steps : [
        {
          "@type": "HowToStep",
          "name": "Read the guide",
          "position": 1,
          "text": "Follow our comprehensive guide to master this topic."
        }
      ],
      "tool": [
        {
          "@type": "HowToTool",
          "name": "JobHuntin Agent"
        }
      ]
    };
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <LoadingSpinner label="Loading..." />
      </div>
    );
  }

  if (!guide) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-6 text-center bg-slate-50">
        <BookOpen className="w-16 h-16 text-primary-500 mb-4 animate-pulse" />
        <h2 className="text-2xl font-bold mb-4 text-slate-900">Guide Not Found</h2>
        <Link to="/guides" className="text-primary-600 hover:underline flex items-center gap-2 font-medium">
          <ArrowLeft className="w-4 h-4" /> Back to Playbook
        </Link>
      </div>
    );
  }

  const howToSchema = generateHowToSchema();

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-primary-500/20 selection:text-primary-700">
      <SEO
        title={`${guide.title} | JobHuntin Playbook`}
        description={`Deep dive into ${guide.title.toLowerCase()}. Part of the JobHuntin automation playbook.`}
        ogTitle={`${guide.title} | JobHuntin Playbook`}
        ogImage={`${config.urls.og}/api/og?job=${encodeURIComponent(guide.title)}&company=JobHuntin&score=100&location=Global`}
        canonicalUrl={`${config.urls.homepage}/guides/${guideSlug}`}
        schema={[
          {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": guide.title,
            "description": `Deep dive into ${guide.title.toLowerCase()}. Part of the JobHuntin automation playbook.`,
            "url": `https://jobhuntin.com/guides/${guideSlug}`,
            "about": guide.category,
            "author": author ? {
              "@type": "Person",
              "name": author.name,
              "url": `/authors/${author.id}`
            } : {
              "@type": "Organization",
              "name": "JobHuntin"
            },
            "datePublished": "2026-02-08",
            "dateModified": "2026-02-15",
            "speakable": {
              "@type": "SpeakableSpecification",
              "cssSelector": ["#guide-content"]
            }
          },
          howToSchema
        ]}
      />


      <main className="max-w-4xl mx-auto px-6 py-16 sm:py-20">
        <BreadcrumbNav items={[
          { name: 'Home', url: 'https://jobhuntin.com' },
          { name: 'Guides', url: 'https://jobhuntin.com/guides' },
          { name: guide.title, url: `https://jobhuntin.com/guides/${guideSlug}` },
        ]} />
        {/* Sticky Navigation for Desktop */}
        {!shouldReduceMotion && headings.length > 0 && (
          <div className="hidden lg:block fixed top-24 left-8 w-64 z-40">
            <div className="bg-white border border-slate-100 rounded-xl p-4 shadow-sm">
              <h4 className="text-sm font-bold text-slate-900 mb-3">Table of Contents</h4>
              <nav className="space-y-2">
                {headings.map((heading, index) => (
                  <a
                    key={heading.id}
                    href={`#${heading.id}`}
                    className={`block text-xs sm:text-sm ${heading.level === 3 ? 'font-semibold' : 'font-normal'} text-slate-600 hover:text-primary-600 transition-colors py-1`}
                    style={{ paddingLeft: `${(heading.level - 3) * 12}px` }}
                  >
                    {heading.text}
                  </a>
                ))}
              </nav>
            </div>
          </div>
        )}

        {/* Mobile Navigation Toggle */}
        {headings.length > 0 && (
          <div className="lg:hidden mb-6">
            <button
              onClick={() => setNavOpen(!navOpen)}
              className="bg-white border border-slate-200 rounded-xl p-3 flex items-center justify-between gap-4 hover:border-primary-500 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 w-full"
              aria-label={navOpen ? 'Close table of contents' : 'Open table of contents'}
              aria-expanded={navOpen}
            >
              <div className="flex items-center gap-3 text-slate-600">
                <Menu className="w-4 h-4" />
                <span className="text-sm font-medium">Table of Contents</span>
              </div>
              {navOpen ? <X className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            </button>
            
            {navOpen && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-4 bg-white border border-slate-100 rounded-xl p-4 shadow-sm"
              >
                <nav className="space-y-2">
                  {headings.map((heading, index) => (
                    <a
                      key={heading.id}
                      href={`#${heading.id}`}
                      className={`block text-sm ${heading.level === 3 ? 'font-semibold' : 'font-normal'} text-slate-600 hover:text-primary-600 transition-colors py-1`}
                      style={{ paddingLeft: `${(heading.level - 3) * 12}px` }}
                      onClick={() => setNavOpen(false)}
                    >
                      {heading.text}
                    </a>
                  ))}
                </nav>
              </motion.div>
            )}
          </div>
        )}

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12"
        >
          <div className="flex flex-col sm:flex-row sm:items-center gap-4 text-sm text-slate-400 font-bold uppercase tracking-widest mb-6">
            <span className="text-primary-500">{guide.category}</span>
            <span className="hidden sm:block w-1 h-1 bg-slate-300 rounded-full" />
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4" /> {guide.readTime}
            </div>
          </div>
          <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-sans font-black mb-6 sm:mb-8 leading-tight text-slate-900 text-balance">
            {guide.title}
          </h1>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-y border-slate-200 py-6">
            <div className="flex items-center gap-3">
              {author && <img src={author.image} alt={author.name} className="w-10 h-10 rounded-full" />}
              <div>
                <p className="text-sm font-bold text-slate-900">{author ? author.name : "JobHuntin Research Team"}</p>
                <p className="text-xs text-slate-500">Updated Feb 8, 2026</p>
              </div>
            </div>
            <button 
              className="p-2 hover:bg-slate-100 rounded-full transition-colors text-slate-400 hover:text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
              aria-label="Share this guide"
            >
              <Share2 className="w-5 h-5" />
            </button>
          </div>
        </motion.div>

        <article
          id="guide-content"
          className="prose prose-lg max-w-none prose-headings:font-display prose-headings:font-bold prose-headings:text-slate-900 prose-p:text-slate-600 prose-a:text-primary-600 mb-20 prose-strong:text-slate-900"
          dangerouslySetInnerHTML={{
            __html: XSSProtection.sanitizeHTML(guide.content.replace(/<h3>/g, '<h3 id="heading-0">').replace(/<h4>/g, '<h4 id="heading-1">')),
          }}
        />

        {author && <Author author={author} />}

        {guideSlug && <RelatedGuides currentGuideSlug={guideSlug} />}

        <div className="bg-white rounded-[2rem] sm:rounded-[2.5rem] p-6 sm:p-8 lg:p-10 border border-slate-100 shadow-sm mb-20">
          <h3 className="text-xl sm:text-2xl font-bold mb-6 font-display text-slate-900">Related Tools</h3>
          <div className="grid sm:grid-cols-2 gap-4">
            <Link to="/chrome-extension" className="flex items-center gap-4 p-4 rounded-2xl hover:bg-slate-50 transition-colors border border-transparent hover:border-slate-100 group focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2">
              <div className="w-12 h-12 bg-primary-50 text-primary-500 rounded-xl flex items-center justify-center flex-shrink-0 group-hover:bg-primary-500 group-hover:text-white transition-colors">
                <Zap className="w-6 h-6" />
              </div>
              <div>
                <p className="font-bold text-sm text-slate-900">Chrome Extension</p>
                <p className="text-xs text-slate-400">Auto-apply while browsing</p>
              </div>
            </Link>
            <Link to="/pricing" className="flex items-center gap-4 p-4 rounded-2xl hover:bg-slate-50 transition-colors border border-transparent hover:border-slate-100 group focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2">
              <div className="w-12 h-12 bg-blue-50 text-blue-500 rounded-xl flex items-center justify-center flex-shrink-0 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                <Target className="w-6 h-6" />
              </div>
              <div>
                <p className="font-bold text-sm text-slate-900">Pro Hunter Plan</p>
                <p className="text-xs text-slate-400">Scale your hunt 10x</p>
              </div>
            </Link>
          </div>
        </div>

        <ConversionCTA variant="guide" guideName={guide.title} />
      </main>


    </div>
  );
}
