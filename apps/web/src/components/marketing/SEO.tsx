import React from 'react';
import { Helmet } from 'react-helmet-async';

const BASE_URL = 'https://jobhuntin.com';
const SITE_NAME = 'JobHuntin';
const DEFAULT_OG_IMAGE = 'https://jobhuntin.com/og-image.png';
const TWITTER_SITE = '@jobhuntin';
const DEFAULT_LOCALE = 'en_US';

export interface BreadcrumbItem {
  name: string;
  url: string;
}

export interface SEOProps {
  title: string;
  description: string;
  /** Override for og:title (defaults to title) */
  ogTitle?: string;
  /** Override for og:description (defaults to description) */
  ogDescription?: string;
  /** Canonical URL */
  canonicalUrl?: string;
  /** OG image URL (defaults to DEFAULT_OG_IMAGE) */
  ogImage?: string;
  /** og:type - website, article, etc. */
  ogType?: 'website' | 'article';
  /** Schema.org JSON-LD (single object or array) */
  schema?: object | object[];
  /** Breadcrumbs for BreadcrumbList schema */
  breadcrumbs?: BreadcrumbItem[];
  /** @deprecated Meta keywords ignored by Google; kept for backwards compatibility but not rendered */
  keywords?: string | string[];
  /** Set noindex, nofollow */
  noindex?: boolean;
  /** Article meta: published_time, modified_time, author */
  article?: boolean;
  /** Include article date meta (uses articlePublishedDate when set) */
  includeDate?: boolean;
  /** ISO date for article:published_time */
  articlePublishedDate?: string;
  /** ISO date for article:modified_time */
  articleModifiedDate?: string;
  /** Author for article:author */
  articleAuthor?: string;
}

function resolveOgImage(ogImage?: string): string {
  if (ogImage && ogImage.startsWith('http')) return ogImage;
  if (ogImage) return `${BASE_URL}${ogImage.startsWith('/') ? '' : '/'}${ogImage}`;
  return DEFAULT_OG_IMAGE;
}

function resolveCanonicalUrl(canonicalUrl?: string): string {
  if (!canonicalUrl) return BASE_URL;
  return canonicalUrl.startsWith('http') ? canonicalUrl : `${BASE_URL}${canonicalUrl.startsWith('/') ? '' : '/'}${canonicalUrl}`;
}

function buildBreadcrumbSchema(breadcrumbs: BreadcrumbItem[]): object {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: breadcrumbs.map((item, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: item.name,
      item: item.url.startsWith('http') ? item.url : `${BASE_URL}${item.url.startsWith('/') ? '' : '/'}${item.url}`,
    })),
  };
}

function normalizeSchema(schema: object | object[] | undefined): object[] {
  if (!schema) return [];
  return Array.isArray(schema) ? schema : [schema];
}

export const SEO: React.FC<SEOProps> = ({
  title,
  description,
  ogTitle,
  ogDescription,
  canonicalUrl,
  ogImage,
  ogType = 'website',
  schema,
  breadcrumbs,
  keywords,
  noindex,
  article,
  includeDate,
  articlePublishedDate,
  articleModifiedDate,
  articleAuthor,
}) => {
  const resolvedOgImage = resolveOgImage(ogImage);
  const resolvedCanonical = resolveCanonicalUrl(canonicalUrl);
  const displayOgTitle = ogTitle ?? title;
  const displayOgDescription = ogDescription ?? description;

  const showArticleMeta = article || includeDate;
  const hasPublishedDate = !!articlePublishedDate;
  const hasModifiedDate = !!articleModifiedDate;

  const allSchemas = [
    ...normalizeSchema(schema),
    ...(breadcrumbs && breadcrumbs.length > 0 ? [buildBreadcrumbSchema(breadcrumbs)] : []),
  ];

  return (
    <Helmet>
      <title>{title}</title>
      <meta name="description" content={description} />
      {noindex && <meta name="robots" content="noindex, nofollow" />}

      {/* Canonical */}
      <link rel="canonical" href={resolvedCanonical} />

      {/* hreflang - English + French (SEO #50: i18n support) */}
      <link rel="alternate" hrefLang="en" href={resolvedCanonical} />
      <link rel="alternate" hrefLang="fr" href={`${resolvedCanonical}${resolvedCanonical.includes('?') ? '&' : '?'}lang=fr`} />

      {/* Open Graph */}
      <meta property="og:title" content={displayOgTitle} />
      <meta property="og:description" content={displayOgDescription} />
      <meta property="og:url" content={resolvedCanonical} />
      <meta property="og:image" content={resolvedOgImage} />
      <meta property="og:image:width" content="1200" />
      <meta property="og:image:height" content="630" />
      <meta property="og:image:alt" content={displayOgTitle} />
      <meta property="og:type" content={article ? 'article' : ogType} />
      <meta property="og:site_name" content={SITE_NAME} />
      <meta property="og:locale" content={DEFAULT_LOCALE} />

      {/* Twitter Card */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:site" content={TWITTER_SITE} />
      <meta name="twitter:title" content={displayOgTitle} />
      <meta name="twitter:description" content={displayOgDescription} />
      <meta name="twitter:image" content={resolvedOgImage} />

      {/* Article meta (when article=true or includeDate with dates) */}
      {showArticleMeta && hasPublishedDate && (
        <meta property="article:published_time" content={articlePublishedDate} />
      )}
      {showArticleMeta && hasModifiedDate && (
        <meta property="article:modified_time" content={articleModifiedDate} />
      )}
      {showArticleMeta && articleAuthor && (
        <meta property="article:author" content={articleAuthor} />
      )}

      {/* JSON-LD Schema */}
      {allSchemas.map((s, i) => (
        <script key={i} type="application/ld+json">
          {JSON.stringify(s)}
        </script>
      ))}
    </Helmet>
  );
};
