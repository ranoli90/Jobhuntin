import React, { useState } from 'react';
import { Search, Loader2, ExternalLink } from 'lucide-react';
import { Button } from './Button';
import { Input } from './Input';
import { motion, AnimatePresence } from 'framer-motion';

interface SearchResult {
  title: string;
  link: string;
  snippet: string;
}

export function GoogleSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const apiKey = import.meta.env.VITE_GOOGLE_API_KEY;
  const searchEngineId = import.meta.env.VITE_GOOGLE_SEARCH_CX; // Needs to be configured

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    if (!apiKey || !searchEngineId) {
      // Fallback to external Google search if API/CX not configured
      window.open(`https://www.google.com/search?q=site:jobhuntin.com+${encodeURIComponent(query)}`, '_blank');
      return;
    }

    setIsLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      const response = await fetch(
        `https://www.googleapis.com/customsearch/v1?key=${apiKey}&cx=${searchEngineId}&q=${encodeURIComponent(query)}`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch search results');
      }

      const data = await response.json();
      setResults(data.items || []);
    } catch (err) {
      setError('Failed to perform search. Please try again.');
      console.error('Google Search Error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-4">
      <form onSubmit={handleSearch} className="relative flex gap-2">
        <div className="relative flex-1">
          <Input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search site content..."
            className="pl-10 pr-4 py-3 w-full rounded-xl border-slate-200 focus:border-primary-500 focus:ring-primary-500/20 transition-all shadow-sm"
          />
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
        </div>
        <Button 
          type="submit" 
          disabled={isLoading || !query.trim()}
          className="rounded-xl px-6 shadow-lg shadow-primary-500/10"
        >
          {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Search'}
        </Button>
      </form>

      <AnimatePresence>
        {(!apiKey || !searchEngineId) && query && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-2 text-xs text-slate-500 flex items-center gap-1 ml-1"
          >
            <ExternalLink className="w-3 h-3" />
            Redirects to Google Search (API configuration missing)
          </motion.div>
        )}

        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-4 p-4 bg-red-50 text-red-600 rounded-xl text-sm font-medium border border-red-100"
          >
            {error}
          </motion.div>
        )}

        {hasSearched && !isLoading && !error && results.length === 0 && (apiKey && searchEngineId) && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-8 text-center text-slate-500"
          >
            No results found for "{query}"
          </motion.div>
        )}

        {results.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-6 space-y-4"
          >
            {results.map((result, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="p-4 bg-white rounded-xl border border-slate-100 hover:border-primary-200 hover:shadow-md transition-all group"
              >
                <a href={result.link} target="_blank" rel="noopener noreferrer" className="block">
                  <h3 className="text-lg font-bold text-slate-900 group-hover:text-primary-600 transition-colors mb-1">
                    {result.title}
                  </h3>
                  <p className="text-xs text-green-600 mb-2 truncate">{result.link}</p>
                  <p className="text-sm text-slate-600 leading-relaxed">
                    {result.snippet}
                  </p>
                </a>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}