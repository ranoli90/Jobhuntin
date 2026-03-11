import React from 'react';
import { Link, useParams } from 'react-router-dom';
import { SEO } from '../components/marketing/SEO';
import { motion } from 'framer-motion';
import { ArrowLeft, Clock, User, Tag, Share2, Twitter, Linkedin, Facebook } from 'lucide-react';
import { LazyMarkdown } from '../components/ui/LazyMarkdown';

const blogPosts: Record<string, {
  title: string;
  excerpt: string;
  content: string;
  category: string;
  date: string;
  readTime: string;
  author: string;
  heroImage: string;
  heroGradient: string;
}> = {
  'is-jobright-legit': {
    heroImage: '/illustrations/filter.svg',
    heroGradient: 'linear-gradient(135deg, rgba(69,93,211,0.2) 0%, rgba(23,190,187,0.1) 100%)',
    title: 'Is Jobright Legit? Complete 2026 Review',
    excerpt: 'An honest, in-depth analysis of Jobright AI. We test every feature, compare pricing, and reveal whether it\'s worth your time in 2026.',
    content: `
## What is Jobright?

Jobright is an AI-powered job search platform launched in 2022. It describes itself as an "AI job search copilot" that helps job seekers find relevant opportunities, tailor resumes, and connect with potential referrers.

With over 1.25 million users and $7.7 million in funding, Jobright has become one of the more recognizable names in the AI job search space. But is it actually legit? Let's find out.

## How Jobright Works

Jobright's core features include:

1. **AI Job Matching** - Algorithms match you to relevant jobs based on your resume and preferences
2. **Auto-Apply** - Semi-automated application submission
3. **Resume Tailoring** - AI adjusts your resume for specific job postings
4. **Insider Referrals** - Connects you with alumni and hiring managers at target companies
5. **AI Copilot (Orion)** - Chat-based career guidance

## Is Jobright Safe and Legitimate?

**Yes, Jobright is a legitimate company.** They:

- Are incorporated and have received venture funding ($7.7M)
- Have real users (1.25M claimed)
- Partner with legitimate job boards and ATS platforms
- Have a transparent team and about page

However, "legitimate" doesn't mean "best choice for everyone."

## Jobright Pricing (2026)

| Plan | Price | Features |
|------|-------|----------|
| Free | $0 | Limited job matches, basic features |
| Pro | $29.99/mo | Unlimited matches, auto-apply, resume tailoring |
| Enterprise | Custom | Team features, dedicated support |

## Jobright vs Competitors

### vs JobHuntin

Jobright is a "copilot" - it assists but requires your active participation. JobHuntin is an "autopilot" - once configured, it runs completely autonomously in the background.

Key differences:
- **Stealth Mode**: Jobright doesn't have it. JobHuntin makes applications undetectable.
- **Pricing**: JobHuntin Pro is $19/mo vs Jobright's $29.99/mo
- **Automation Level**: JobHuntin is fully autonomous; Jobright needs your clicks

### vs Simplify

Simplify focuses on form autofill. Jobright offers more comprehensive features including job matching and referral networks.

## What Users Say About Jobright

Positive reviews often mention:
- Good job matching algorithm
- Useful referral network feature
- Clean, intuitive interface

Common complaints:
- Pro tier is expensive
- Still requires significant user effort
- Auto-apply isn't truly autonomous
- Some find the AI recommendations hit-or-miss

## Our Verdict

Jobright is **legit** but not perfect. It's a good choice if you:

- Want to stay hands-on with your job search
- Value the insider referral network
- Prefer a copilot approach

Consider alternatives if you:

- Want truly autonomous job applications
- Need stealth mode for undetectable applications
- Prefer better value pricing

## Should You Try Jobright?

Jobright offers a free tier, so there's no risk in trying it. However, if you're looking for a truly hands-off experience, you might want to explore JobHuntin or other autonomous agents.

The referral network is Jobright's standout feature - if networking is important to your job search strategy, it's worth testing.
    `,
    category: 'Reviews',
    date: '2026-02-14',
    readTime: '8 min',
    author: 'JobHuntin Team',
  },
  'ai-job-application-tools-compared': {
    title: 'AI Job Application Tools Compared: Which One Actually Works?',
    excerpt: 'We tested 12 AI job application tools side-by-side. Here\'s what actually gets you interviews.',
    content: `
## The AI Job Search Tool Landscape in 2026

The market for AI-powered job search tools has exploded. We tested 12 leading platforms over 3 months to find out which ones actually deliver results.

## Our Testing Methodology

We created identical test profiles and ran each tool for 2 weeks, tracking:
- Number of applications submitted
- Interview invitation rate
- Application quality (ATS scores)
- Time saved vs manual applications
- User experience and ease of use

## Top Performers

### 1. JobHuntin (Best for Automation)
- **Apps submitted**: 150+ per day
- **Interview rate**: 8.2%
- **Key feature**: Fully autonomous operation
- **Best for**: Busy professionals who want hands-off

JobHuntin stood out for its truly autonomous operation. Set preferences once, and it handles everything from job discovery to submission.

### 2. Jobright (Best for Networking)
- **Apps submitted**: 20-30 per day with user action
- **Interview rate**: 5.1%
- **Key feature**: Insider referral network
- **Best for**: Those who value networking

Jobright's referral network is unique and valuable if you're targeting specific companies.

### 3. Simplify (Best for Form Autofill)
- **Apps submitted**: Depends on user speed
- **Interview rate**: 4.8%
- **Key feature**: Form autofill
- **Best for**: Those who want to stay in control

Simplify excels at what it does - autofilling application forms quickly.

## What Didn't Work

Several tools we tested had significant issues:

- **LazyApply**: High automation but applications were flagged by ATS systems
- **LoopCV**: Limited job board integration
- **Sonara**: Frequent errors and poor matching

## Key Findings

1. **Autonomy vs Control**: Fully autonomous tools (JobHuntin) produced more volume, while semi-automated tools required more time but offered more control.

2. **Stealth Matters**: Tools without stealth mode had lower interview rates, likely due to ATS detection.

3. **Resume Tailoring**: Tools that tailor resumes per application significantly outperformed those using static resumes.

4. **Volume Isn't Everything**: Quality of applications mattered more than raw numbers.

## Our Recommendation

For most job seekers, we recommend:

- **JobHuntin** if you want maximum automation
- **Jobright** if networking is your priority
- **Simplify** if you want to stay hands-on but save time on forms

The best approach? Use JobHuntin for volume applications while networking separately.
    `,
    category: 'Comparisons',
    date: '2026-02-12',
    readTime: '12 min',
    author: 'JobHuntin Team',
    heroImage: '/illustrations/career-progress.svg',
    heroGradient: 'linear-gradient(135deg, rgba(23,190,187,0.2) 0%, rgba(69,93,211,0.15) 100%)',
  },
};

const relatedPosts = [
  { slug: 'ai-job-application-tools-compared', title: 'AI Job Application Tools Compared', category: 'Comparisons' },
  { slug: 'how-to-auto-apply-jobs', title: 'How to Auto-Apply to Jobs', category: 'Guides' },
  { slug: 'ats-resume-optimization', title: 'ATS Resume Optimization', category: 'Guides' },
];

export default function BlogPost() {
  const { slug } = useParams<{ slug: string }>();
  const post = blogPosts[slug || ''];

  if (!post) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-6 text-center bg-[#F7F6F3]">
        <SEO title="Article Not Found | JobHuntin" description="The requested article could not be found." noindex />
        <h1 className="text-2xl font-bold mb-4 text-[#2D2A26]">Article Not Found</h1>
        <Link to="/blog" className="text-[#455DD3] hover:underline flex items-center gap-2 font-medium">
          <ArrowLeft className="w-4 h-4" /> Back to Blog
        </Link>
      </div>
    );
  }

  const title = `${post.title} | JobHuntin Blog`;
  const description = post.excerpt;
  const canonicalUrl = `https://jobhuntin.com/blog/${slug}`;

  return (
    <div className="min-h-screen bg-white font-sans text-[#2D2A26]">
      <SEO
        title={title}
        description={description}
        ogTitle={title}
        canonicalUrl={canonicalUrl}
        article
        articlePublishedDate={post.date}
        articleModifiedDate={post.date}
        articleAuthor={post.author}
        schema={[
          {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": post.title,
            "description": post.excerpt,
            "datePublished": post.date,
            "dateModified": post.date,
            "author": {
              "@type": "Organization",
              "name": post.author
            },
            "publisher": {
              "@type": "Organization",
              "name": "JobHuntin",
              "url": "https://jobhuntin.com"
            },
            "mainEntityOfPage": {
              "@type": "WebPage",
              "url": canonicalUrl
            }
          }
        ]}
      />

      <main className="max-w-[720px] mx-auto px-6 sm:px-8 py-8 sm:py-12">
        {/* Breadcrumb */}
        <nav className="mb-6 sm:mb-8">
          <Link to="/blog" className="text-[#455DD3] hover:underline flex items-center gap-2 text-sm font-medium">
            <ArrowLeft className="w-4 h-4" /> Back to Blog
          </Link>
        </nav>

        {/* Hero image — thematic illustration */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="aspect-video rounded-2xl overflow-hidden mb-8 sm:mb-12 flex items-center justify-center"
          style={{ background: post.heroGradient }}
        >
          <img
            src={post.heroImage}
            alt=""
            aria-hidden
            loading="eager"
            className="w-[60%] max-w-[320px] h-auto object-contain opacity-70"
          />
        </motion.div>

        {/* Header */}
        <motion.header
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-10 sm:mb-12"
        >
          <div className="flex flex-wrap items-center gap-3 text-sm text-[#787774] mb-4">
            <span className="bg-[#455DD3]/10 text-[#455DD3] px-3 py-1.5 rounded-lg font-semibold">
              {post.category}
            </span>
            <span className="flex items-center gap-1.5">
              <Clock className="w-4 h-4" />
              {post.readTime}
            </span>
            <span className="flex items-center gap-1.5">
              <User className="w-4 h-4" />
              {post.author}
            </span>
          </div>
          <h1 className="text-[clamp(1.75rem,4vw,2.75rem)] font-bold text-[#2D2A26] mb-4 tracking-tight leading-[1.2]" style={{ letterSpacing: '-0.5px' }}>
            {post.title}
          </h1>
          <p className="text-lg sm:text-xl text-[#787774] leading-relaxed">
            {post.excerpt}
          </p>
        </motion.header>

        {/* Content — prose with site tokens */}
        <motion.article
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="blog-content mb-12"
        >
          <LazyMarkdown
            content={post.content}
            className="prose prose-lg max-w-none
              prose-headings:font-bold prose-headings:text-[#2D2A26]
              prose-h2:text-xl sm:prose-h2:text-2xl prose-h2:mt-10 prose-h2:mb-4 prose-h2:pb-2 prose-h2:border-b prose-h2:border-[#E9E9E7]
              prose-h3:text-lg sm:prose-h3:text-xl prose-h3:mt-8 prose-h3:mb-3
              prose-p:text-[#787774] prose-p:leading-[1.7] prose-p:mb-4
              prose-a:text-[#455DD3] prose-a:font-medium prose-a:no-underline hover:prose-a:underline
              prose-strong:text-[#2D2A26] prose-strong:font-semibold
              prose-li:text-[#787774] prose-li:my-1
              prose-ul:my-4 prose-ol:my-4
              prose-table:text-sm prose-table:w-full prose-table:my-6
              prose-th:bg-[#F7F6F3] prose-th:p-3 prose-th:text-left prose-th:font-semibold prose-th:text-[#2D2A26] prose-th:border prose-th:border-[#E9E9E7]
              prose-td:p-3 prose-td:border prose-td:border-[#E9E9E7] prose-td:text-[#787774]"
          />
        </motion.article>

        {/* Author bio — SEO #42 */}
        <div className="bg-slate-50 dark:bg-slate-900/50 rounded-2xl p-6 mb-12 border border-slate-100 dark:border-slate-800">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center shrink-0">
              <User className="w-7 h-7 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 dark:text-slate-100 mb-1">{post.author}</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                The JobHuntin team writes about AI job search, automation, and career tips. We build the tools that help job seekers land more interviews.
              </p>
            </div>
          </div>
        </div>

        {/* Share */}
        <div className="border-t border-[#E9E9E7] dark:border-slate-700 pt-8 mb-12">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <span className="text-[#787774] font-medium">Share this article:</span>
            <div className="flex gap-3">
              <a href={`https://twitter.com/intent/tweet?text=${encodeURIComponent(post.title)}&url=${encodeURIComponent(canonicalUrl)}`} target="_blank" rel="noopener noreferrer" className="w-10 h-10 rounded-xl bg-[#F7F6F3] flex items-center justify-center text-[#787774] hover:bg-[#455DD3]/10 hover:text-[#455DD3] transition-colors">
                <Twitter className="w-5 h-5" />
              </a>
              <a href={`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(canonicalUrl)}`} target="_blank" rel="noopener noreferrer" className="w-10 h-10 rounded-xl bg-[#F7F6F3] flex items-center justify-center text-[#787774] hover:bg-[#455DD3]/10 hover:text-[#455DD3] transition-colors">
                <Linkedin className="w-5 h-5" />
              </a>
              <a href={`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(canonicalUrl)}`} target="_blank" rel="noopener noreferrer" className="w-10 h-10 rounded-xl bg-[#F7F6F3] flex items-center justify-center text-[#787774] hover:bg-[#455DD3]/10 hover:text-[#455DD3] transition-colors">
                <Facebook className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>

        {/* Related Posts */}
        <div className="border-t border-[#E9E9E7] pt-12">
          <h2 className="text-xl font-bold text-[#2D2A26] mb-6">Related Articles</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            {relatedPosts.filter(p => p.slug !== slug).slice(0, 2).map((relatedPost) => (
              <Link
                key={relatedPost.slug}
                to={`/blog/${relatedPost.slug}`}
                className="block rounded-xl p-5 bg-[#F7F6F3] hover:bg-[#EDECE9] border border-[#E9E9E7] hover:border-[#E3E2E0] transition-all"
              >
                <span className="text-xs font-semibold text-[#455DD3]">{relatedPost.category}</span>
                <h3 className="font-semibold text-[#2D2A26] mt-2">{relatedPost.title}</h3>
              </Link>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
