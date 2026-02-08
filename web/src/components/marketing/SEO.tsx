import { useEffect } from 'react';

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
  useEffect(() => {
    document.title = title;

    const updateMeta = (name: string, content: string, attr: string = 'name') => {
      let el = document.querySelector(`meta[${attr}="${name}"]`);
      if (!el) {
        el = document.createElement('meta');
        el.setAttribute(attr, name);
        document.head.appendChild(el);
      }
      el.setAttribute('content', content);
    };

    const resolvedCanonical = canonicalUrl || (typeof window !== 'undefined' ? window.location.href : "https://jobhuntin.com");

    updateMeta("description", description);
    updateMeta("og:title", ogTitle || title, 'property');
    updateMeta("og:description", ogDescription || description, 'property');
    updateMeta("og:type", "website", 'property');
    updateMeta("og:url", resolvedCanonical, 'property');
    
    // OG Image tags for iMessage/Social optimization
    updateMeta("og:image", ogImage, 'property');
    updateMeta("og:image:width", ogImageWidth, 'property');
    updateMeta("og:image:height", ogImageHeight, 'property');
    updateMeta("og:image:alt", ogTitle || title, 'property');

    updateMeta("og:site_name", "JobHuntin", 'property');
    updateMeta("theme-color", themeColor);
    updateMeta("robots", robots);
    
    // Twitter Card tags
    updateMeta("twitter:card", "summary_large_image");
    updateMeta("twitter:site", "@jobhuntin");
    updateMeta("twitter:title", ogTitle || title);
    updateMeta("twitter:description", ogDescription || description);
    updateMeta("twitter:image", ogImage);
    updateMeta("twitter:image:alt", ogTitle || title);

    // Canonical
    let canonical = document.querySelector('link[rel="canonical"]');
    if (!canonical) {
      canonical = document.createElement('link');
      canonical.setAttribute('rel', 'canonical');
      document.head.appendChild(canonical);
    }
    canonical.setAttribute('href', resolvedCanonical);

    // Schema.org JSON-LD
    const scriptId = 'seo-schema-jsonld';
    let script = document.getElementById(scriptId) as HTMLScriptElement;
    if (!script) {
      script = document.createElement('script');
      script.id = scriptId;
      script.type = "application/ld+json";
      document.head.appendChild(script);
    }

    const baseSchema = {
      "@context": "https://schema.org",
      "@type": "WebSite",
      "name": "JobHuntin",
      "url": resolvedCanonical,
      "description": description,
      "potentialAction": {
        "@type": "SearchAction",
        "target": `${resolvedCanonical}/search?q={search_term_string}`,
        "query-input": "required name=search_term_string"
      }
    };

    const organizationSchema = {
      "@context": "https://schema.org",
      "@type": "Organization",
      "name": "JobHuntin",
      "url": "https://jobhuntin.com",
      "logo": "https://jobhuntin.com/logo.png",
      "sameAs": [
        "https://twitter.com/jobhuntin",
        "https://github.com/jobhuntin"
      ]
    };

    // Breadcrumb Schema
    const pathSegments = window.location.pathname.split('/').filter(Boolean);
    const breadcrumbSchema = {
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      "itemListElement": [
        {
          "@type": "ListItem",
          "position": 1,
          "name": "Home",
          "item": "https://jobhuntin.com"
        },
        ...pathSegments.map((segment, index) => ({
          "@type": "ListItem",
          "position": index + 2,
          "name": segment.charAt(0).toUpperCase() + segment.slice(1).replace(/-/g, ' '),
          "item": `https://jobhuntin.com/${pathSegments.slice(0, index + 1).join('/')}`
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

    script.text = JSON.stringify(finalSchema);

    return () => {
      // Cleanup if needed
    };
  }, [title, description, ogTitle, ogDescription, ogImage, ogImageWidth, ogImageHeight, canonicalUrl, robots, themeColor, schema]);

  return null;
};
