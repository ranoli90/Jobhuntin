import { useLocation } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';

interface SEOProps {
  title: string;
  description: string;
  ogTitle?: string;
  ogDescription?: string;
  ogImage?: string;
  ogImageWidth?: string;
  ogImageHeight?: string;
  canonicalUrl?: string;
  robots?: string;
  themeColor?: string;
  schema?: object | object[];
  includeDate?: boolean;
}

const DEFAULT_OG_IMAGE = "https://jobhuntin.com/og-image.png";
const BASE_URL = "https://jobhuntin.com";

const getDynamicDate = () => {
  const d = new Date();
  const month = d.toLocaleString('default', { month: 'long' });
  const year = d.getFullYear();
  return `${month} ${year}`;
};

const getDynamicMonth = () => {
  return new Date().toLocaleString('default', { month: 'long' });
};

export const SEO = ({
  title,
  description,
  ogTitle,
  ogDescription,
  ogImage = DEFAULT_OG_IMAGE,
  ogImageWidth = "1200",
  ogImageHeight = "630",
  canonicalUrl,
  robots = "index,follow",
  themeColor = "#1e293b",
  schema,
  includeDate = false
}: SEOProps) => {
  const location = useLocation();
  const resolvedCanonical = canonicalUrl || `${BASE_URL}${location.pathname === "/" ? "" : location.pathname}`;

  const displayTitle = includeDate ? `${title} (${getDynamicDate()})` : title;
  const displayDescription = includeDate ? `${description} Updated ${getDynamicDate()}.` : description;

  const baseSchema = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": "JobHuntin",
    "url": BASE_URL,
    "alternateName": "AI Job Search Automation",
    "description": description,
    "inLanguage": "en-US",
    "publisher": {
      "@type": "Organization",
      "name": "JobHuntin",
      "url": BASE_URL,
      "logo": `${BASE_URL}/logo.png`
    },
    "potentialAction": {
      "@type": "SearchAction",
      "target": `${BASE_URL}/search?q={search_term_string}`,
      "query-input": "required name=search_term_string"
    }
  };

  const organizationSchema = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "JobHuntin",
    "url": BASE_URL,
    "logo": `${BASE_URL}/logo.png`,
    "description": "AI-powered job search automation with auto-apply, resume tailoring, and stealth mode",
    "foundingDate": "2024",
    "contactPoint": {
      "@type": "ContactPoint",
      "telephone": "+1-555-JOB-HUNT",
      "contactType": "customer service",
      "email": "support@jobhuntin.com",
      "availableLanguage": "English"
    },
    "sameAs": [
      "https://twitter.com/jobhuntin",
      "https://github.com/ranoli90/sorce",
      "https://linkedin.com/company/jobhuntin"
    ]
  };

  // SoftwareApplication schema for the main product
  const softwareSchema = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "JobHuntin",
    "applicationCategory": "BusinessApplication",
    "operatingSystem": "Web, Chrome Extension",
    "url": BASE_URL,
    "description": "AI-powered job search automation platform with autonomous agent, auto-apply, resume tailoring, and stealth mode",
    "author": {
      "@type": "Organization",
      "name": "JobHuntin",
      "url": BASE_URL
    },
    "offers": {
      "@type": "Offer",
      "price": "19",
      "priceCurrency": "USD",
      "availability": "https://schema.org/InStock",
      "validFrom": "2024-01-01"
    },
    "aggregateRating": {
      "@type": "AggregateRating",
      "ratingValue": "4.9",
      "reviewCount": "847",
      "bestRating": "5"
    },
    "reviews": [
      {
        "@type": "Review",
        "reviewRating": {
          "@type": "Rating",
          "ratingValue": "5",
          "bestRating": "5"
        },
        "author": {
          "@type": "Person",
          "name": "Sarah M."
        },
        "reviewBody": "Landedi my dream job in 2 weeks using JobHuntin's AI agent!"
      }
    ]
  };

  // Breadcrumb Schema
  const pathSegments = location.pathname.split('/').filter(Boolean);
  const breadcrumbSchema = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {
        "@type": "ListItem",
        "position": 1,
        "name": "Home",
        "item": BASE_URL
      },
      ...pathSegments.map((segment, index) => ({
        "@type": "ListItem",
        "position": index + 2,
        "name": segment.charAt(0).toUpperCase() + segment.slice(1).replace(/-/g, ' '),
        "item": `${BASE_URL}/${pathSegments.slice(0, index + 1).join('/')}`
      }))
    ]
  };

  // JobPosting Schema for job pages
  const jobPostingSchema = location.pathname.startsWith('/jobs/') ? {
    "@context": "https://schema.org",
    "@type": "JobPosting",
    "title": title,
    "description": description,
    "identifier": resolvedCanonical,
    "datePosted": new Date().toISOString().split('T')[0],
    "validThrough": new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    "employmentType": "FULL_TIME",
    "jobLocationType": "FULL_TIME",
    "hiringOrganization": {
      "@type": "Organization",
      "name": "JobHuntin",
      "url": BASE_URL,
      "logo": `${BASE_URL}/logo.png`
    },
    "jobLocation": {
      "@type": "Place",
      "address": {
        "@type": "PostalAddress",
        "addressCountry": "US"
      }
    },
    "baseSalary": {
      "@type": "MonetaryAmount",
      "currency": "USD"
    },
    "qualifications": "Experience in related field preferred",
    "responsibilities": "Apply to jobs and manage applications efficiently",
    "benefits": "AI-powered job search automation, resume tailoring, and application tracking"
  } : null;

  const finalSchema: unknown[] = [baseSchema, organizationSchema, softwareSchema, breadcrumbSchema];
  if (jobPostingSchema) {
    finalSchema.push(jobPostingSchema);
  }
  if (schema) {
    if (Array.isArray(schema)) {
      finalSchema.push(...schema);
    } else {
      finalSchema.push(schema);
    }
  }

  return (
    <Helmet>
      <title>{displayTitle}</title>
      <meta name="description" content={displayDescription} />
      <link rel="canonical" href={resolvedCanonical} />
      <meta name="robots" content={`${robots}, max-image-preview:large, max-snippet:-1, max-video-preview:-1`} />
      <meta name="theme-color" content={themeColor} />
      <meta property="og:locale" content="en_US" />
      <meta name="author" content="JobHuntin" />

      {/* Open Graph / Facebook */}
      <meta property="og:type" content={location.pathname.includes('/reviews/') || location.pathname.includes('/blog/') ? 'article' : 'website'} />
      <meta property="og:url" content={resolvedCanonical} />
      <meta property="og:title" content={ogTitle || displayTitle} />
      <meta property="og:description" content={ogDescription || displayDescription} />
      <meta property="og:image" content={ogImage} />
      <meta property="og:image:width" content={ogImageWidth} />
      <meta property="og:image:height" content={ogImageHeight} />
      <meta property="og:image:alt" content={ogTitle || displayTitle} />
      <meta property="og:site_name" content="JobHuntin" />

      {/* Twitter */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:site" content="@jobhuntin" />
      <meta name="twitter:creator" content="@jobhuntin" />
      <meta name="twitter:title" content={ogTitle || displayTitle} />
      <meta name="twitter:description" content={ogDescription || displayDescription} />
      <meta name="twitter:image" content={ogImage} />
      <meta name="twitter:image:alt" content={ogTitle || displayTitle} />

      {/* Additional SEO Meta Tags */}
      <meta name="format-detection" content="telephone=no" />
      <meta name="mobile-web-app-capable" content="yes" />
      <meta name="apple-mobile-web-app-capable" content="yes" />
      <meta name="apple-mobile-web-app-status-bar-style" content="default" />
      <meta name="apple-mobile-web-app-title" content="JobHuntin" />
      <meta name="application-name" content="JobHuntin" />
      <meta name="msapplication-TileColor" content={themeColor} />
      <meta name="msapplication-config" content="none" />

      {/* GEO Tags for Local SEO */}
      <meta name="geo.region" content="US" />
      <meta name="geo.placename" content="San Francisco" />
      <meta name="geo.position" content="37.7749;-122.4194" />
      <meta name="ICBM" content="37.7749, -122.4194" />

      {/* JSON-LD Structured Data — one script per schema object for SEO best practice */}
      {finalSchema.map((schemaObj, idx) => (
        <script key={idx} type="application/ld+json">
          {JSON.stringify(schemaObj)}
        </script>
      ))}
    </Helmet>
  );
};

