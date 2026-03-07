
import React from 'react';
import { Helmet } from 'react-helmet-async';

interface SEOProps {
  title: string;
  description: string;
  ogTitle?: string;
  canonicalUrl?: string;
  schema?: any;
}

export const SEO: React.FC<SEOProps> = ({ title, description, ogTitle, canonicalUrl, schema }) => {
  return (
    <Helmet>
      <title>{title}</title>
      <meta name="description" content={description} />
      {ogTitle && <meta property="og:title" content={ogTitle} />}
      {canonicalUrl && <link rel="canonical" href={canonicalUrl} />}
      {schema && <script type="application/ld+json">{JSON.stringify(schema)}</script>}
    </Helmet>
  );
};
