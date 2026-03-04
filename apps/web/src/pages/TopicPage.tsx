import React from 'react';
import { useParams } from 'react-router-dom';
import topics from '../data/topics.json';
import { XSSProtection } from '../lib/validation';

export default function TopicPage() {
  const { slug } = useParams<{ slug: string }>();
  const topic = slug ? (topics as Record<string, any>)[slug] : null;

  if (!topic) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-slate-900 mb-4">Topic not found</h1>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-4xl mx-auto px-6 py-16 sm:py-20">
        <h1 className="text-4xl font-bold mb-6">{topic.title}</h1>
        <div
          className="prose prose-lg max-w-none prose-headings:font-display prose-headings:font-bold prose-headings:text-slate-900 prose-p:text-slate-600 prose-a:text-primary-600 prose-strong:text-slate-900"
          dangerouslySetInnerHTML={{ __html: XSSProtection.sanitizeHTML(topic.content) }}
        />
      </div>
    </div>
  );
}
