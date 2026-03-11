import React from 'react';
import { useParams, Link } from 'react-router-dom';
import authors from '../data/authors.json';
import guides from '../data/guides.json';
import { SEO } from '../components/marketing/SEO';

export default function AuthorPage() {
  const { authorId } = useParams<{ authorId: string }>();
  const author = authors.find(a => a.id === authorId);
  const authorGuides = Object.entries(guides as Record<string, any>).filter(([slug, guide]: [string, any]) => guide.authorId === authorId);

  if (!author) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <SEO title="Author Not Found | JobHuntin" description="The requested author could not be found." noindex />
        <div className="text-center">
          <h1 className="text-4xl font-bold text-slate-900 mb-4">Author not found</h1>
        </div>
      </div>
    );
  }

  const title = `${author.name} | JobHuntin Blog Author`;
  const description = `${author.bio} Explore guides and articles by ${author.name}.`;

  return (
    <div className="min-h-screen bg-slate-50">
      <SEO
        title={title}
        description={description}
        ogTitle={title}
        canonicalUrl={`https://jobhuntin.com/authors/${authorId}`}
        schema={[
          {
            "@context": "https://schema.org",
            "@type": "Person",
            "name": author.name,
            "description": author.bio,
            "url": `https://jobhuntin.com/authors/${authorId}`,
            "image": author.image.startsWith("http") ? author.image : `https://jobhuntin.com${author.image.startsWith("/") ? "" : "/"}${author.image}`
          },
          {
            "@context": "https://schema.org",
            "@type": "ProfilePage",
            "name": title,
            "mainEntity": { "@type": "Person", "name": author.name }
          }
        ]}
      />
      <div className="max-w-4xl mx-auto px-6 py-16 sm:py-20">
        <div className="flex items-center mb-12">
          <img src={author.image} alt={author.name} className="w-32 h-32 rounded-full mr-8" />
          <div>
            <h1 className="text-4xl font-bold mb-2">{author.name}</h1>
            <p className="text-slate-600 mb-2">{author.title}</p>
            <p className="text-slate-600 mb-4">{author.bio}</p>
            <div className="flex gap-4">
              <a href={author.social.twitter} target="_blank" rel="noreferrer" className="text-slate-600 hover:text-slate-900">Twitter</a>
              <a href={author.social.linkedin} target="_blank" rel="noreferrer" className="text-slate-600 hover:text-slate-900">LinkedIn</a>
            </div>
          </div>
        </div>

        <h2 className="text-2xl font-bold mb-6">Guides by {author.name}</h2>
        <div className="grid gap-8">
          {authorGuides.map(([slug, guide]: [string, any]) => (
            <Link to={`/guides/${slug}`} key={slug} className="bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow">
              <h3 className="text-xl font-bold mb-2">{guide.title}</h3>
              <p className="text-slate-600">{guide.readTime}</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
