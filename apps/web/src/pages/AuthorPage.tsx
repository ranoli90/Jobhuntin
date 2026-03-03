import React from 'react';
import { useParams, Link } from 'react-router-dom';
import authors from '../data/authors.json';
import guides from '../data/guides.json';

export default function AuthorPage() {
  const { authorId } = useParams<{ authorId: string }>();
  const author = authors.find(a => a.id === authorId);
  const guides = Object.entries(guides as Record<string, any>).filter(([slug, guide]) => guide.authorId === authorId);

  if (!author) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-slate-900 mb-4">Author not found</h1>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
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
          {guides.map(([slug, guide]) => (
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
