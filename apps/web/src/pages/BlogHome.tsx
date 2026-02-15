import React from 'react';
import { Link } from 'react-router-dom';
import { SEO } from '../components/marketing/SEO';
import { motion } from 'framer-motion';
import { ArrowRight, Clock, User, Tag, Search } from 'lucide-react';

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
  },
];

const categories = ['All', 'Reviews', 'Comparisons', 'Guides', 'Data', 'Success Stories'];

export default function BlogHome() {
  const title = 'JobHuntin Blog | AI Job Search Tips, Reviews & Guides';
  const description = 'Expert insights on AI-powered job search. Tool reviews, application strategies, interview tips, and real success stories from job seekers who landed their dream jobs.';

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900">
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
                "@type": "Organization",
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
          className="text-center mb-16"
        >
          <h1 className="text-4xl md:text-5xl font-black text-slate-900 mb-6 tracking-tight">
            Job Search Intelligence
          </h1>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto">
            In-depth guides, honest reviews, and data-driven insights to help you land your dream job faster.
          </p>
        </motion.div>

        {/* Search */}
        <div className="max-w-xl mx-auto mb-12">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              placeholder="Search articles..."
              className="w-full pl-12 pr-4 py-4 rounded-2xl border border-slate-200 focus:border-primary-500 focus:ring-2 focus:ring-primary-100 outline-none transition-all"
            />
          </div>
        </div>

        {/* Categories */}
        <div className="flex flex-wrap justify-center gap-3 mb-12">
          {categories.map((cat) => (
            <button
              key={cat}
              className={`px-5 py-2 rounded-full text-sm font-semibold transition-all ${
                cat === 'All'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-slate-600 hover:bg-primary-50 hover:text-primary-700 border border-slate-200'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Featured Posts */}
        <div className="mb-16">
          <h2 className="text-2xl font-bold mb-8">Featured Articles</h2>
          <div className="grid md:grid-cols-2 gap-6">
            {blogPosts.filter(p => p.featured).slice(0, 2).map((post, index) => (
              <motion.div
                key={post.slug}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Link
                  to={`/blog/${post.slug}`}
                  className="block bg-white rounded-2xl overflow-hidden shadow-sm border border-slate-100 hover:shadow-lg transition-all group"
                >
                  <div className="aspect-video bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center">
                    <span className="text-6xl opacity-50">📝</span>
                  </div>
                  <div className="p-6">
                    <div className="flex items-center gap-3 text-sm text-slate-500 mb-3">
                      <span className="bg-primary-100 text-primary-700 px-3 py-1 rounded-full font-medium">
                        {post.category}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {post.readTime}
                      </span>
                    </div>
                    <h3 className="text-xl font-bold text-slate-900 group-hover:text-primary-600 transition-colors mb-3">
                      {post.title}
                    </h3>
                    <p className="text-slate-600 leading-relaxed">
                      {post.excerpt}
                    </p>
                    <div className="mt-4 flex items-center justify-between">
                      <span className="text-sm text-slate-500">{post.date}</span>
                      <span className="text-primary-600 font-semibold text-sm flex items-center gap-1 group-hover:gap-2 transition-all">
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
          <h2 className="text-2xl font-bold mb-8">All Articles</h2>
          <div className="space-y-4">
            {blogPosts.map((post, index) => (
              <motion.div
                key={post.slug}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Link
                  to={`/blog/${post.slug}`}
                  className="block bg-white rounded-xl p-6 shadow-sm border border-slate-100 hover:shadow-md hover:border-primary-100 transition-all group"
                >
                  <div className="flex items-start gap-6">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 text-sm text-slate-500 mb-2">
                        <Tag className="w-4 h-4" />
                        {post.category}
                        <span>•</span>
                        <Clock className="w-4 h-4" />
                        {post.readTime}
                      </div>
                      <h3 className="text-lg font-bold text-slate-900 group-hover:text-primary-600 transition-colors mb-2">
                        {post.title}
                      </h3>
                      <p className="text-slate-600 text-sm line-clamp-2">
                        {post.excerpt}
                      </p>
                    </div>
                    <div className="hidden md:flex items-center text-primary-600 font-semibold text-sm whitespace-nowrap">
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
