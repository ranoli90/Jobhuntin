import { Helmet } from 'react-helmet-async';

export default function Maintenance() {
  return (
    <>
      <Helmet>
        <title>JobHuntin — Maintenance</title>
        <meta name="robots" content="noindex" />
      </Helmet>
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 px-4 text-center">
        <div className="w-16 h-16 rounded-2xl bg-brand-accent/10 flex items-center justify-center mb-6">
          <svg className="w-8 h-8 text-brand-accent" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M11.42 15.17l-5.82-3.36a1.5 1.5 0 010-2.58l5.82-3.36a1.5 1.5 0 011.16 0l5.82 3.36a1.5 1.5 0 010 2.58l-5.82 3.36a1.5 1.5 0 01-1.16 0z" />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-brand-ink mb-3">We'll be right back</h1>
        <p className="text-slate-500 max-w-md mb-8">
          JobHuntin is currently undergoing scheduled maintenance. We're making things better and will be back shortly.
        </p>
        <p className="text-sm text-slate-400">
          Questions? Email us at{' '}
          <a href="mailto:support@jobhuntin.com" className="text-brand-accent hover:underline">
            support@jobhuntin.com
          </a>
        </p>
      </div>
    </>
  );
}
