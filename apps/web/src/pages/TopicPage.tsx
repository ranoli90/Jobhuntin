import React, { useState, useEffect, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronRight, Home, BookOpen, FileText, BarChart3, Menu, X } from 'lucide-react';
import topicsData from '../data/topics.json';
import guidesData from '../data/guides.json';
import competitorsData from '../data/competitors.json';
import { SEO } from '../components/marketing/SEO';
import { ConversionCTA } from '../components/seo/ConversionCTA';
import { XSSProtection } from '../lib/validation';
import { config } from '../config';

const topics = topicsData as Record<string, { title: string; description?: string; content: string }>;
const guides = guidesData as Record<string, { title: string; category: string; readTime: string }>;
const competitors = competitorsData as Array<{ slug: string; name: string }>;

/** Strip HTML and truncate for meta description */
function stripHtml(html: string, maxLen = 155): string {
  const text = html.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
  return text.length > maxLen ? text.slice(0, maxLen - 1) + '…' : text;
}

/** Add unique IDs to headings in HTML content */
function addHeadingIds(html: string): string {
  let index = 0;
  return html.replace(/<h([2-4])(\s[^>]*)?>/gi, (_, level: string, rest = '') => {
    const id = `heading-${index++}`;
    return `<h${level} id="${id}"${rest}>`;
  });
}

/** Extract headings from HTML for TOC */
function extractHeadings(html: string): Array< { id: string; text: string; level: number }> {
  if (typeof document === 'undefined') return [];
  const div = document.createElement('div');
  div.innerHTML = XSSProtection.sanitizeHTML(html);
  const elements = div.querySelectorAll('h2, h3, h4');
  return Array.from(elements).map((el, i) => ({
    id: el.id || `heading-${i}`,
    text: el.textContent || '',
    level: parseInt(el.tagName.charAt(1), 10),
  }));
}

const FEATURED_COMPETITORS = ['jobright', 'teal', 'simplify', 'sonara-ai'];

export default function TopicPage() {
  const { slug } = useParams<{ slug: string }>();
  const topic = slug ? topics[slug] : null;
  const [navOpen, setNavOpen] = useState(false);
  const [headings, setHeadings] = useState<Array<{ id: string; text: string; level: number }>>([]);

  const processedContent = useMemo(() => {
    if (!topic?.content) return '';
    const sanitized = XSSProtection.sanitizeHTML(topic.content);
    return addHeadingIds(sanitized);
  }, [topic?.content]);

  useEffect(() => {
    if (topic?.content) {
      setHeadings(extractHeadings(topic.content));
    } else {
      setHeadings([]);
    }
  }, [topic?.content]);

  const topicSlugs = useMemo(() => Object.keys(topics), []);
  const relatedTopics = useMemo(() => {
    if (!slug) return [];
    return topicSlugs.filter((s) => s !== slug).slice(0, 4);
  }, [slug, topicSlugs]);

  const relatedGuides = useMemo(() => {
    const slugs = Object.keys(guides);
    return slugs.slice(0, 4);
  }, []);

  const comparisonLinks = useMemo(() => {
    return FEATURED_COMPETITORS.filter((s) =>
      competitors.some((c) => c.slug === s)
    ).map((s) => competitors.find((c) => c.slug === s)!);
  }, []);

  // 404 state
  if (!topic) {
    return (
      <div className="min-h-screen bg-[#F7F6F3] flex flex-col items-center justify-center px-6">
        <div className="max-w-lg w-full text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-slate-200/80 mb-6">
            <FileText className="w-8 h-8 text-slate-600" />
          </div>
          <h1 className="text-3xl font-bold text-slate-900 mb-3">Topic not found</h1>
          <p className="text-slate-600 mb-8">
            The topic you're looking for doesn't exist or may have been moved.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              to="/"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-semibold bg-primary-600 text-white hover:bg-primary-700 transition-colors"
            >
              <Home className="w-4 h-4" /> Home
            </Link>
            <Link
              to="/blog"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-semibold border-2 border-slate-200 text-slate-900 hover:border-primary-500 hover:text-primary-600 transition-colors"
            >
              <FileText className="w-4 h-4" /> Blog
            </Link>
            <Link
              to="/guides"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-semibold border-2 border-slate-200 text-slate-900 hover:border-primary-500 hover:text-primary-600 transition-colors"
            >
              <BookOpen className="w-4 h-4" /> Guides
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const description = topic.description ?? stripHtml(topic.content);
  const canonicalUrl = `${config.urls.homepage}/topics/${slug}`;
  const breadcrumbs = [
    { name: 'Home', url: config.urls.homepage + '/' },
    { name: 'Topics', url: config.urls.homepage + '/blog' },
    { name: topic.title, url: canonicalUrl },
  ];

  const articleSchema = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: topic.title,
    description,
    url: canonicalUrl,
    publisher: { '@type': 'Organization', name: 'JobHuntin', url: config.urls.homepage },
    datePublished: '2026-02-01',
    dateModified: '2026-03-01',
  };

  return (
    <div className="min-h-screen bg-[#F7F6F3] font-sans text-slate-900 selection:bg-primary-500/20 selection:text-primary-700">
      <SEO
        title={`${topic.title} | JobHuntin`}
        description={description}
        ogTitle={`${topic.title} | JobHuntin`}
        ogDescription={description}
        canonicalUrl={canonicalUrl}
        ogType="article"
        article
        articlePublishedDate="2026-02-01"
        articleModifiedDate="2026-03-01"
        breadcrumbs={breadcrumbs}
        schema={articleSchema}
      />

      <main className="max-w-5xl mx-auto px-6 py-12 sm:py-16">
        {/* Breadcrumb */}
        <nav aria-label="Breadcrumb" className="mb-8">
          <ol className="flex flex-wrap items-center gap-2 text-sm text-slate-600">
            <li>
              <Link to="/" className="hover:text-primary-600 transition-colors flex items-center gap-1">
                <Home className="w-4 h-4" /> Home
              </Link>
            </li>
            <li>
              <ChevronRight className="w-4 h-4 text-slate-400" />
            </li>
            <li>
              <Link to="/blog" className="hover:text-primary-600 transition-colors">
                Topics
              </Link>
            </li>
            <li>
              <ChevronRight className="w-4 h-4 text-slate-400" />
            </li>
            <li className="font-semibold text-slate-900">{topic.title}</li>
          </ol>
        </nav>

        <div className="flex flex-col lg:flex-row gap-12">
          {/* Sidebar: Table of Contents */}
          {headings.length > 0 && (
            <aside className="hidden lg:block lg:w-64 shrink-0">
              <div className="lg:sticky lg:top-24">
                <div className="bg-white rounded-2xl border border-slate-100 p-4 shadow-sm">
                  <h2 className="text-sm font-bold text-slate-900 mb-3">On this page</h2>
                  <nav className="space-y-1.5">
                    {headings.map((h) => (
                      <a
                        key={h.id}
                        href={`#${h.id}`}
                        className={`block text-sm text-slate-600 hover:text-primary-600 transition-colors ${
                          h.level === 2 ? 'font-semibold' : h.level === 4 ? 'pl-3' : 'pl-1.5'
                        }`}
                      >
                        {h.text}
                      </a>
                    ))}
                  </nav>
                </div>
              </div>
            </aside>
          )}

          {/* Mobile TOC toggle */}
          {headings.length > 0 && (
            <div className="lg:hidden">
              <button
                onClick={() => setNavOpen(!navOpen)}
                className="w-full flex items-center justify-between gap-4 p-4 rounded-2xl bg-white border border-slate-100 shadow-sm hover:border-primary-200 transition-colors"
                aria-expanded={navOpen}
                aria-label={navOpen ? 'Close table of contents' : 'Open table of contents'}
              >
                <span className="text-sm font-semibold text-slate-900">Table of contents</span>
                {navOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
              </button>
              {navOpen && (
                <div className="mt-3 p-4 rounded-2xl bg-white border border-slate-100 shadow-sm">
                  <nav className="space-y-1.5">
                    {headings.map((h) => (
                      <a
                        key={h.id}
                        href={`#${h.id}`}
                        onClick={() => setNavOpen(false)}
                        className="block text-sm text-slate-600 hover:text-primary-600 py-1"
                      >
                        {h.text}
                      </a>
                    ))}
                  </nav>
                </div>
              )}
            </div>
          )}

          {/* Main content */}
          <article className="flex-1 min-w-0">
            {/* Hero */}
            <header className="mb-12">
              <span className="inline-block px-4 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider bg-primary-100 text-primary-700 mb-6">
                Topic
              </span>
              <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-slate-900 leading-tight mb-6">
                {topic.title}
              </h1>
              <p className="text-lg text-slate-600 max-w-2xl leading-relaxed">
                {stripHtml(topic.content, 300)}
              </p>
            </header>

            {/* Article content */}
            <div
              className="prose prose-lg max-w-none prose-headings:font-bold prose-headings:text-slate-900 prose-p:text-slate-600 prose-a:text-primary-600 prose-strong:text-slate-900 prose-ul:text-slate-600 prose-ol:text-slate-600"
              dangerouslySetInnerHTML={{ __html: processedContent }}
            />

            {/* Related Topics */}
            {relatedTopics.length > 0 && (
              <section className="mt-16">
                <h2 className="text-xl font-bold text-slate-900 mb-4">Related Topics</h2>
                <div className="grid sm:grid-cols-2 gap-4">
                  {relatedTopics.map((s) => {
                    const t = topics[s];
                    if (!t) return null;
                    return (
                      <Link
                        key={s}
                        to={`/topics/${s}`}
                        className="block p-5 rounded-2xl bg-white border border-slate-100 hover:border-primary-200 hover:shadow-md transition-all group"
                      >
                        <h3 className="font-bold text-slate-900 group-hover:text-primary-600 transition-colors">
                          {t.title}
                        </h3>
                        <p className="text-sm text-slate-600 mt-1 line-clamp-2">
                          {stripHtml(t.content, 100)}
                        </p>
                        <span className="inline-flex items-center gap-1 text-sm font-medium text-primary-600 mt-2">
                          Read more <ChevronRight className="w-4 h-4" />
                        </span>
                      </Link>
                    );
                  })}
                </div>
              </section>
            )}

            {/* Related Guides */}
            <section className="mt-16">
              <h2 className="text-xl font-bold text-slate-900 mb-4">Related Guides</h2>
              <div className="grid sm:grid-cols-2 gap-4">
                {relatedGuides.map((guideSlug) => {
                  const g = guides[guideSlug];
                  if (!g) return null;
                  return (
                    <Link
                      key={guideSlug}
                      to={`/guides/${guideSlug}`}
                      className="flex items-start gap-4 p-5 rounded-2xl bg-white border border-slate-100 hover:border-primary-200 hover:shadow-md transition-all group"
                    >
                      <div className="w-12 h-12 rounded-xl bg-primary-50 text-primary-600 flex items-center justify-center shrink-0 group-hover:bg-primary-100 transition-colors">
                        <BookOpen className="w-6 h-6" />
                      </div>
                      <div className="min-w-0">
                        <h3 className="font-bold text-slate-900 group-hover:text-primary-600 transition-colors">
                          {g.title}
                        </h3>
                        <p className="text-sm text-slate-500 mt-1">
                          {g.category} · {g.readTime}
                        </p>
                      </div>
                      <ChevronRight className="w-5 h-5 text-slate-400 shrink-0" />
                    </Link>
                  );
                })}
              </div>
            </section>

            {/* Comparison & Blog links */}
            <section className="mt-16">
              <h2 className="text-xl font-bold text-slate-900 mb-4">Explore More</h2>
              <div className="flex flex-wrap gap-4">
                <Link
                  to="/blog"
                  className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-white border border-slate-100 hover:border-primary-200 hover:shadow-sm transition-all font-medium text-slate-900"
                >
                  <FileText className="w-4 h-4" /> Blog
                </Link>
                {comparisonLinks.slice(0, 3).map((c) => (
                  <Link
                    key={c.slug}
                    to={`/vs/${c.slug}`}
                    className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-white border border-slate-100 hover:border-primary-200 hover:shadow-sm transition-all font-medium text-slate-900"
                  >
                    <BarChart3 className="w-4 h-4" /> {c.name} vs JobHuntin
                  </Link>
                ))}
              </div>
            </section>

            {/* Conversion CTA */}
            <div className="mt-20">
              <ConversionCTA />
            </div>
          </article>
        </div>
      </main>
    </div>
  );
}
