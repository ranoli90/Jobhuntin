import React from 'react';
import { Link } from 'react-router-dom';
import { SEO } from '../components/marketing/SEO';
import { motion } from 'framer-motion';
import { ArrowRight, Clock, User, Tag, Search } from 'lucide-react';

/** When adding posts, also add slug to src/data/blog-slugs.json for sitemap (SEO #49) */
const blogPosts = [
  {
    slug: 'is-jobright-legit',
    title: 'Is Jobright Legit? Complete 2026 Review',
    excerpt: 'An honest, in-depth analysis of Jobright AI. We test every feature, compare pricing, and reveal whether it\'s worth your time in 2026.',
    category: 'Reviews',
    date: '2026-02-14',
    readTime: '8 min',
    author: 'JobHuntin Team',
    featured: true,
    heroImage: '/illustrations/filter.svg',
    heroGradient: 'linear-gradient(135deg, rgba(69,93,211,0.2) 0%, rgba(23,190,187,0.1) 100%)',
  },
  {
    slug: 'ai-job-application-tools-compared',
    title: 'AI Job Application Tools Compared: Which One Actually Works?',
    excerpt: 'We tested 12 AI job application tools side-by-side. Here\'s what actually gets you interviews.',
    category: 'Comparisons',
    date: '2026-02-12',
    readTime: '12 min',
    author: 'JobHuntin Team',
    featured: true,
    heroImage: '/illustrations/career-progress.svg',
    heroGradient: 'linear-gradient(135deg, rgba(23,190,187,0.2) 0%, rgba(69,93,211,0.15) 100%)',
  },
  {
    slug: 'how-to-auto-apply-jobs',
    title: 'How to Auto-Apply to Jobs: Complete Guide for 2026',
    excerpt: 'Everything you need to know about automated job applications. Setup, best practices, and how to avoid common pitfalls.',
    category: 'Guides',
    date: '2026-02-10',
    readTime: '10 min',
    author: 'JobHuntin Team',
    featured: false,
    heroImage: '/illustrations/application.svg',
    heroGradient: 'linear-gradient(135deg, rgba(234,88,12,0.15) 0%, rgba(69,93,211,0.1) 100%)',
  },
  {
    slug: 'ats-resume-optimization',
    title: 'ATS Resume Optimization: How to Beat the Bots in 2026',
    excerpt: 'Learn exactly how Applicant Tracking Systems work and how to format your resume to pass every time.',
    category: 'Guides',
    date: '2026-02-08',
    readTime: '7 min',
    author: 'JobHuntin Team',
    featured: false,
    heroImage: '/illustrations/files-uploading.svg',
    heroGradient: 'linear-gradient(135deg, rgba(22,163,74,0.15) 0%, rgba(69,93,211,0.1) 100%)',
  },
  {
    slug: 'job-search-statistics-2026',
    title: 'Job Search Statistics 2026: Data-Driven Insights',
    excerpt: 'The latest data on job market trends, application success rates, and what\'s working for job seekers right now.',
    category: 'Data',
    date: '2026-02-06',
    readTime: '6 min',
    author: 'JobHuntin Team',
    featured: false,
    heroImage: '/illustrations/dashboard.svg',
    heroGradient: 'linear-gradient(135deg, rgba(69,93,211,0.15) 0%, rgba(23,190,187,0.1) 100%)',
  },
  {
    slug: 'interview-success-stories',
    title: 'Interview Success Stories: Real Users Share Their Experience',
    excerpt: 'How 5 job seekers landed their dream jobs using AI-powered tools. Their exact strategies revealed.',
    category: 'Success Stories',
    date: '2026-02-04',
    readTime: '9 min',
    author: 'JobHuntin Team',
    featured: true,
    heroImage: '/illustrations/celebration.svg',
    heroGradient: 'linear-gradient(135deg, rgba(234,88,12,0.15) 0%, rgba(23,190,187,0.12) 100%)',
  },
];

const categories = ['All', 'Reviews', 'Comparisons', 'Guides', 'Data', 'Success Stories'];

export default function BlogHome() {
  const title = 'JobHuntin Blog | AI Job Search Tips, Reviews & Guides';
  const description = 'Expert insights on AI-powered job search. Tool reviews, application strategies, interview tips, and real success stories from job seekers who landed their dream jobs.';

  return (
    <div className="min-h-screen bg-[#F7F6F3] font-sans text-[#2D2A26]">
      <SEO
        title={title}
        description={description}
        ogTitle={title}
        canonicalUrl="https://jobhuntin.com/blog"
        includeDate={true}
        schema={[
          {
            "@context": "https://schema.org",
            "@type": "Blog",
            "name": "JobHuntin Blog",
            "description": description,
            "url": "https://jobhuntin.com/blog",
            "publisher": {
              "@type": "Organization",
              "name": "JobHuntin",
              "url": "https://jobhuntin.com"
            },
            "blogPost": blogPosts.slice(0, 5).map(post => ({
              "@type": "BlogPosting",
              "headline": post.title,
              "description": post.excerpt,
              "datePublished": post.date,
              "author": {
                "@type": "Person",
                "name": post.author
              },
              "url": `https://jobhuntin.com/blog/${post.slug}`
            }))
          }
        ]}
      />

      <main className="max-w-6xl mx-auto px-6 py-16">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12 sm:mb-16"
        >
          <h1 className="text-[clamp(2rem,4vw,3rem)] font-bold text-[#2D2A26] mb-4 tracking-tight" style={{ letterSpacing: '-0.5px' }}>
            Job Search Intelligence
          </h1>
          <p className="text-lg sm:text-xl text-[#787774] max-w-2xl mx-auto leading-relaxed">
            In-depth guides, honest reviews, and data-driven insights to help you land your dream job faster.
          </p>
        </motion.div>

        {/* Search */}
        <div className="max-w-xl mx-auto mb-10">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#9B9A97]" />
            <input
              type="text"
              placeholder="Search articles..."
              className="w-full pl-12 pr-4 py-3.5 sm:py-4 rounded-xl border-2 border-[#E9E9E7] bg-white focus:border-[#455DD3] focus:ring-2 focus:ring-[#455DD3]/10 outline-none transition-all text-[#2D2A26] placeholder:text-[#9B9A97]"
            />
          </div>
        </div>

        {/* Categories */}
        <div className="flex flex-wrap justify-center gap-2 sm:gap-3 mb-10 sm:mb-12">
          {categories.map((cat) => (
            <button
              key={cat}
              className={`px-4 sm:px-5 py-2 rounded-xl text-sm font-semibold transition-all ${
                cat === 'All'
                  ? 'bg-[#455DD3] text-white'
                  : 'bg-white text-[#787774] hover:bg-[#455DD3]/10 hover:text-[#455DD3] border border-[#E9E9E7]'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Featured Posts */}
        <div className="mb-12 sm:mb-16">
          <h2 className="text-xl sm:text-2xl font-bold text-[#2D2A26] mb-6 sm:mb-8">Featured Articles</h2>
          <div className="grid sm:grid-cols-2 gap-6">
            {blogPosts.filter(p => p.featured).slice(0, 2).map((post, index) => (
              <motion.div
                key={post.slug}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Link
                  to={`/blog/${post.slug}`}
                  className="block bg-white rounded-2xl overflow-hidden border border-[#E9E9E7] hover:border-[#E3E2E0] hover:shadow-lg transition-all duration-300 group"
                >
                  <div
                    className="aspect-video flex items-center justify-center"
                    style={{ background: post.heroGradient }}
                  >
                    <img
                      src={post.heroImage}
                      alt=""
                      aria-hidden
                      loading="lazy"
                      className="w-[50%] max-w-[200px] h-auto object-contain opacity-60 group-hover:opacity-80 transition-opacity"
                    />
                  </div>
                  <div className="p-5 sm:p-6">
                    <div className="flex flex-wrap items-center gap-3 text-sm text-[#787774] mb-3">
                      <span className="bg-[#455DD3]/10 text-[#455DD3] px-3 py-1 rounded-lg font-semibold">
                        {post.category}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {post.readTime}
                      </span>
                    </div>
                    <h3 className="text-lg sm:text-xl font-bold text-[#2D2A26] group-hover:text-[#455DD3] transition-colors mb-2">
                      {post.title}
                    </h3>
                    <p className="text-[#787774] text-sm sm:text-base leading-relaxed line-clamp-2">
                      {post.excerpt}
                    </p>
                    <div className="mt-4 flex items-center justify-between">
                      <span className="text-sm text-[#9B9A97]">{post.date}</span>
                      <span className="text-[#455DD3] font-semibold text-sm flex items-center gap-1 group-hover:gap-2 transition-all">
                        Read More <ArrowRight className="w-4 h-4" />
                      </span>
                    </div>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>

        {/* All Posts */}
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-[#2D2A26] mb-6 sm:mb-8">All Articles</h2>
          <div className="space-y-3 sm:space-y-4">
            {blogPosts.map((post, index) => (
              <motion.div
                key={post.slug}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Link
                  to={`/blog/${post.slug}`}
                  className="block bg-white rounded-xl p-5 sm:p-6 border border-[#E9E9E7] hover:border-[#E3E2E0] hover:shadow-md transition-all duration-300 group"
                >
                  <div className="flex items-start gap-4 sm:gap-6">
                    <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-xl flex-shrink-0 flex items-center justify-center overflow-hidden" style={{ background: post.heroGradient }}>
                      <img src={post.heroImage} alt="" aria-hidden loading="lazy" className="w-[70%] h-[70%] object-contain opacity-60" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-sm text-[#787774] mb-1.5">
                        <Tag className="w-4 h-4 shrink-0" />
                        {post.category}
                        <span className="text-[#E9E9E7]">•</span>
                        <Clock className="w-4 h-4" />
                        {post.readTime}
                      </div>
                      <h3 className="text-base sm:text-lg font-bold text-[#2D2A26] group-hover:text-[#455DD3] transition-colors mb-1.5">
                        {post.title}
                      </h3>
                      <p className="text-[#787774] text-sm line-clamp-2">
                        {post.excerpt}
                      </p>
                    </div>
                    <div className="hidden sm:flex items-center text-[#455DD3] font-semibold text-sm whitespace-nowrap shrink-0">
                      Read <ArrowRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
                    </div>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
