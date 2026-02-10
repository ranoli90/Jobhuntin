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
}

const DEFAULT_OG_IMAGE = "https://sorce-api.onrender.com/api/og?job=AI%20Job%20Hunter&company=JobHuntin&score=100&location=Global";
const BASE_URL = "https://jobhuntin.com";

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
  themeColor = "#FF6B35",
  schema
}: SEOProps) => {
  const location = useLocation();
  const resolvedCanonical = canonicalUrl || `${BASE_URL}${location.pathname === "/" ? "" : location.pathname}`;

  const baseSchema = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": "JobHuntin",
    "url": BASE_URL,
    "description": description,
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
    "sameAs": [
      "https://twitter.com/jobhuntin",
      "https://github.com/jobhuntin"
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

  const finalSchema: any[] = [baseSchema, organizationSchema, breadcrumbSchema];
  if (schema) {
    if (Array.isArray(schema)) {
      finalSchema.push(...schema);
    } else {
      finalSchema.push(schema);
    }
  }

  return (
    <Helmet>
      <title>{title}</title>
      <meta name="description" content={description} />
      <link rel="canonical" href={resolvedCanonical} />
      <meta name="robots" content={robots} />
      <meta name="theme-color" content={themeColor} />

      {/* Open Graph / Facebook */}
      <meta property="og:type" content="website" />
      <meta property="og:url" content={resolvedCanonical} />
      <meta property="og:title" content={ogTitle || title} />
      <meta property="og:description" content={ogDescription || description} />
      <meta property="og:image" content={ogImage} />
      <meta property="og:image:width" content={ogImageWidth} />
      <meta property="og:image:height" content={ogImageHeight} />
      <meta property="og:image:alt" content={ogTitle || title} />
      <meta property="og:site_name" content="JobHuntin" />

      {/* Twitter */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:site" content="@jobhuntin" />
      <meta name="twitter:title" content={ogTitle || title} />
      <meta name="twitter:description" content={ogDescription || description} />
      <meta name="twitter:image" content={ogImage} />
      <meta name="twitter:image:alt" content={ogTitle || title} />

      {/* JSON-LD Structured Data */}
      <script type="application/ld+json">
        {JSON.stringify(finalSchema)}
      </script>
    </Helmet>
  );
};

