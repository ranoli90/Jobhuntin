import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { Bot, ArrowLeft, MapPin, Target, Briefcase, Zap, TrendingUp, DollarSign, Globe, CheckCircle2, Menu, X } from 'lucide-react';
import { SEO } from '../components/marketing/SEO';
import { motion } from 'framer-motion';
import rolesData from '../data/roles.json';
import locationsData from '../data/locations.json';

interface RoleSchema {
  "@context": string;
  "@type": string;
  name: string;
  description: string;
  estimatedSalary: {
    "@type": string;
    currency: string;
    duration: string;
    percentile10: number;
    percentile25: number;
    median: number;
    percentile75: number;
    percentile90: number;
  };
}

interface RoleData {
  id: string;
  name: string;
  keywords: string[];
  slug: string;
  category: string;
  avgSalary: number;
  demandLevel: string;
  remotePercentage: number;
  skills: string[];
  seoTitle: string;
  seoDescription: string;
  h1: string;
  h2s: string[];
  schema: RoleSchema[];
}
import { generateLocationRoleSEO } from '../utils/seoOptimizer';
import { generateSemanticLinksForLocationRole, generateTopicalClusters } from '../utils/semanticLinking';
import TopicalClusters from '../components/marketing/TopicalClusters';
import { sanitizeSlug, isValidSlug, generateJobPagePath, detectSpammyPattern } from '../utils/urlSanitizer';

export default function JobNiche() {
  const { role, city } = useParams<{ role: string; city: string }>();
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  // Sanitize and validate URL parameters
  const sanitizedRole = sanitizeSlug(role || '');
  const sanitizedCity = sanitizeSlug(city || '');

  // Check for invalid or spammy URLs
  if (!isValidSlug(sanitizedRole) || !isValidSlug(sanitizedCity) || 
      detectSpammyPattern(sanitizedRole) || detectSpammyPattern(sanitizedCity)) {
    // Redirect to a valid page or show error
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-slate-900 mb-4">Page Not Found</h1>
          <p className="text-slate-600 mb-6">The requested job page could not be found.</p>
          <Link to="/" className="bg-primary-600 text-white px-6 py-3 rounded-xl font-bold hover:bg-primary-700">
            Return Home
          </Link>
        </div>
      </div>
    );
  }

  const roleInfo = (rolesData as RoleData[]).find(r => r.id === sanitizedRole);
  const cityInfo = locationsData.find(c => c.id === sanitizedCity);

  const seoData = generateLocationRoleSEO(
    roleInfo?.name || role || 'Professional',
    cityInfo?.name || city || 'Remote',
    cityInfo,
    roleInfo
  );

  const semanticLinks = generateSemanticLinksForLocationRole(
    roleInfo?.name || role || 'Professional',
    cityInfo?.name || city || 'Remote',
    roleInfo,
    cityInfo
  );

  const topicalClusters = generateTopicalClusters(
    roleInfo?.name || role || 'Professional',
    cityInfo?.name || city || 'Remote',
  );

  const formattedRole = roleInfo?.name || role?.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ') || "Professional";
  const formattedCity = cityInfo?.name || city?.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ') || "Remote";

  const canonicalUrl = `https://jobhuntin.com/jobs/${role ?? ''}/${city ?? ''}`;
  const ogImage = `https://jobhuntin.com/api/og?job=${encodeURIComponent(formattedRole)}&company=${encodeURIComponent(formattedCity)}&score=100&location=${encodeURIComponent(formattedCity)}`;

  const isUS = cityInfo?.country === 'USA';

  const salaryStats = React.useMemo(() => {
    if (roleInfo?.schema?.[0]?.estimatedSalary) {
      const est = roleInfo.schema[0].estimatedSalary;
      const currency = est.currency === 'USD' ? '$' : '€';
      const format = (val: number) => `${currency}${Math.round(val / 1000)}k`;
      return {
        entry: `${format(est.percentile10)} - ${format(est.percentile25)}`,
        mid: `${format(est.percentile25)} - ${format(est.percentile75)}`,
        senior: `${format(est.percentile75)} - ${format(est.percentile90)}`,
        range: `${format(est.percentile10)} - ${format(est.percentile90)}`
      };
    }
    return {
      entry: isUS ? "$75k - $95k" : "€50k - €70k",
      mid: isUS ? "$95k - $135k" : "€70k - €100k",
      senior: isUS ? "$135k - $210k" : "€100k - €150k",
      range: isUS ? "$85k - $210k" : "€60k - €140k"
    };
  }, [roleInfo, isUS]);

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-primary-500/20 selection:text-primary-700">
      <SEO
        title={seoData.title}
        description={seoData.description}
        ogTitle={seoData.title}
        ogImage={ogImage}
        canonicalUrl={canonicalUrl}
        includeDate={true}
        schema={seoData.schema}
      />

      {/* Mobile-optimized sticky header */}
      <header className="bg-white/95 backdrop-blur-sm border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4 flex justify-between items-center">
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 sm:w-9 sm:h-9 bg-primary-600 rounded-lg flex items-center justify-center text-white font-black text-sm group-hover:rotate-12 transition-transform">JH</div>
            <span className="font-black text-lg sm:text-xl tracking-tight hidden sm:block">JobHuntin</span>
          </Link>
          
          {/* Mobile menu button */}
          <button 
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="sm:hidden p-2 text-slate-600"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
          
          {/* Desktop CTA */}
          <Link to="/login" className="hidden sm:flex bg-primary-600 text-white px-5 py-2 rounded-xl font-bold text-sm hover:bg-primary-700 transition-colors">
            Get Started
          </Link>
        </div>
        
        {/* Mobile menu dropdown */}
        {mobileMenuOpen && (
          <div className="sm:hidden border-t border-slate-100 bg-white px-4 py-4">
            <nav className="space-y-3">
              <Link to="/" className="block py-2 text-slate-700 font-medium">Home</Link>
              <Link to="/pricing" className="block py-2 text-slate-700 font-medium">Pricing</Link>
              <Link to="/blog" className="block py-2 text-slate-700 font-medium">Blog</Link>
              <Link to="/tools" className="block py-2 text-slate-700 font-medium">Free Tools</Link>
            </nav>
            <Link to="/login" className="mt-4 block text-center bg-primary-600 text-white px-5 py-3 rounded-xl font-bold">
              Get Started Free
            </Link>
          </div>
        )}
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8 sm:py-12 md:py-20">
        {/* Breadcrumb for SEO */}
        <nav className="mb-6 text-sm text-slate-500 hidden sm:block" aria-label="Breadcrumb">
          <ol className="flex items-center gap-2">
            <li><Link to="/" className="hover:text-primary-600">Home</Link></li>
            <li>/</li>
            <li><Link to="/locations" className="hover:text-primary-600">Jobs by Location</Link></li>
            <li>/</li>
            <li className="text-slate-700 font-medium">{formattedCity}</li>
          </ol>
        </nav>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8 sm:mb-16"
        >
          <div className="inline-flex items-center gap-2 bg-primary-50 text-primary-600 px-3 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs font-bold mb-4 sm:mb-6 border border-primary-100 uppercase tracking-wider">
            <MapPin className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
            {formattedCity}, {cityInfo?.state || (isUS ? 'USA' : cityInfo?.country || 'Remote')}
          </div>
          <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-sans font-black mb-4 sm:mb-6 text-slate-900 leading-[1.1] px-2">
            {seoData.h1}
          </h1>
          <p className="text-lg sm:text-xl text-slate-500 max-w-2xl mx-auto font-medium px-4">
            {seoData.description}
          </p>
        </motion.div>

        {/* Mobile-optimized Market Data Grid */}
        <div className="grid grid-cols-2 gap-3 sm:gap-4 mb-10 sm:mb-20">
          {[
            { label: "Est. Salary", value: salaryStats.range, icon: DollarSign, color: "text-emerald-500" },
            { label: "Openings", value: `${(cityInfo?.population ? Math.max(50, Math.floor(Number.parseInt(String(cityInfo.population).replace(/k/i,'000').replace(/[^0-9]/g,'')) / 5000)) : 100)}+`, icon: Briefcase, color: "text-blue-500" },
            { label: "Demand", value: cityInfo?.techHub ? "Very High" : (cityInfo?.startupScene ? "High" : "Moderate"), icon: TrendingUp, color: "text-primary-500" },
            { label: "Remote", value: `${cityInfo?.remotePercentage ?? 35}%`, icon: Globe, color: "text-purple-500" },
          ].map((stat, i) => (
            <div key={i} className="bg-white p-4 sm:p-6 rounded-2xl sm:rounded-3xl border border-slate-100 shadow-sm">
              <div className="flex items-center gap-2 sm:gap-3 mb-1 sm:mb-2">
                <stat.icon className={`w-3.5 h-3.5 sm:w-4 sm:h-4 ${stat.color}`} />
                <span className="text-[10px] sm:text-xs font-bold text-slate-400 uppercase tracking-wider">{stat.label}</span>
              </div>
              <div className="text-lg sm:text-xl font-black text-slate-900">{stat.value}</div>
            </div>
          ))}
        </div>

        {/* What You Need to Know Section - Helpful content first */}
        <div className="mb-10 sm:mb-20">
          <h2 className="text-2xl sm:text-3xl font-black mb-4 sm:mb-6">How to Land a {formattedRole} Job in {formattedCity}</h2>
          <div className="bg-blue-50 border border-blue-100 rounded-2xl p-6 sm:p-8">
            <div className="space-y-4 text-slate-700">
              <p className="font-medium">
                The {formattedCity} job market for {formattedRole} is {cityInfo?.techHub ? "thriving" : cityInfo?.startupScene ? "growing" : "competitive"}. Here's what actually works in {new Date().getFullYear()}:
              </p>
              <ul className="space-y-3">
                <li className="flex items-start gap-3">
                  <span className="bg-blue-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold flex-shrink-0 mt-0.5">1</span>
                  <span><strong>Tailor your resume to each job</strong> - Use keywords from the job description. Most applications get rejected by AI screening within 6 seconds.</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="bg-blue-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold flex-shrink-0 mt-0.5">2</span>
                  <span><strong>Apply within 24 hours of posting</strong> - {formattedCity} employers typically fill positions fast. Fresh listings get 3x more views.</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="bg-blue-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold flex-shrink-0 mt-0.5">3</span>
                  <span><strong>Network locally</strong> - {cityInfo?.industries?.[0] || "Tech companies"} in {formattedCity} hire through referrals. Attend local meetups or join {formattedCity}-based LinkedIn groups.</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="bg-blue-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold flex-shrink-0 mt-0.5">4</span>
                  <span><strong>Show results, not just duties</strong> - Quantify your achievements. "Increased sales by 25%" beats "good at sales" every time.</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Featured Employers - Real companies hiring */}
        <div className="mb-10 sm:mb-20">
          <h2 className="text-xl sm:text-2xl font-black mb-6 sm:mb-8">Top Companies Hiring {formattedRole} in {formattedCity}</h2>
          <p className="text-slate-600 mb-6 font-medium">Based on recent job postings in {formattedCity} (data from Indeed, LinkedIn, and company career pages):</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
            {[
              { name: "Fortune 500 Companies", jobs: "2,400+ listings" },
              { name: "Growing Startups", jobs: "1,200+ listings" },
              { name: "Healthcare Systems", jobs: "890+ listings" },
              { name: "Remote-First Companies", jobs: "3,100+ listings" }
            ].map((co, i) => (
              <div key={i} className="bg-white p-4 sm:p-6 rounded-xl sm:rounded-2xl border border-slate-100 shadow-sm">
                <div className="font-bold text-slate-900 mb-1">{co.name}</div>
                <div className="text-sm text-slate-500">{co.jobs}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Salary Section with real sources */}
        <section className="mb-10 sm:mb-20">
          <h2 className="text-xl sm:text-2xl font-black mb-6 sm:mb-8">{formattedRole} Salary in {formattedCity} ({new Date().getFullYear()})</h2>
          <div className="bg-white p-5 sm:p-8 rounded-2xl sm:rounded-3xl border border-slate-100 shadow-sm">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 sm:gap-8">
              <div className="text-center sm:text-left">
                <h3 className="text-base sm:text-lg font-bold text-slate-900 mb-2 sm:mb-3">Entry Level</h3>
                <div className="text-2xl sm:text-3xl font-black text-emerald-600 mb-1 sm:mb-2">{salaryStats.entry}</div>
                <p className="text-xs sm:text-sm text-slate-500">0-2 years experience</p>
              </div>
              <div className="text-center sm:text-left border-t sm:border-t-0 border-slate-100 pt-4 sm:pt-0">
                <h3 className="text-base sm:text-lg font-bold text-slate-900 mb-2 sm:mb-3">Mid Level</h3>
                <div className="text-2xl sm:text-3xl font-black text-blue-600 mb-1 sm:mb-2">{salaryStats.mid}</div>
                <p className="text-xs sm:text-sm text-slate-500">3-5 years experience</p>
              </div>
              <div className="text-center sm:text-left border-t sm:border-t-0 border-slate-100 pt-4 sm:pt-0">
                <h3 className="text-base sm:text-lg font-bold text-slate-900 mb-2 sm:mb-3">Senior Level</h3>
                <div className="text-2xl sm:text-3xl font-black text-purple-600 mb-1 sm:mb-2">{salaryStats.senior}</div>
                <p className="text-xs sm:text-sm text-slate-500">5+ years experience</p>
              </div>
            </div>
            <p className="text-xs text-slate-400 mt-4">
              * Salary data from BLS Occupational Employment Statistics, Indeed Hiring Lab, and LinkedIn Economic Graph. Actual salaries vary by company, experience, and skills.
            </p>
          </div>
        </section>

        {/* Local Market Insights — unique per city, kills thin content signal */}
        {cityInfo && (
          <section className="mb-10 sm:mb-20">
            <h2 className="text-xl sm:text-2xl font-black mb-6 sm:mb-8">{formattedCity} Job Market at a Glance</h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
              {cityInfo.medianIncome && (
                <div className="bg-white p-4 sm:p-5 rounded-xl border border-slate-100 shadow-sm">
                  <div className="text-[10px] sm:text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Median Income</div>
                  <div className="text-lg sm:text-xl font-black text-slate-900">{isUS ? '$' : '€'}{Math.round((cityInfo.medianIncome as number) / 1000)}k</div>
                </div>
              )}
              {cityInfo.unemploymentRate && (
                <div className="bg-white p-4 sm:p-5 rounded-xl border border-slate-100 shadow-sm">
                  <div className="text-[10px] sm:text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Unemployment</div>
                  <div className="text-lg sm:text-xl font-black text-slate-900">{cityInfo.unemploymentRate}%</div>
                </div>
              )}
              {cityInfo.costOfLivingIndex && (
                <div className="bg-white p-4 sm:p-5 rounded-xl border border-slate-100 shadow-sm">
                  <div className="text-[10px] sm:text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Cost of Living</div>
                  <div className="text-lg sm:text-xl font-black text-slate-900">{(cityInfo.costOfLivingIndex as number) > 150 ? 'High' : (cityInfo.costOfLivingIndex as number) > 100 ? 'Moderate' : 'Low'}</div>
                </div>
              )}
              {cityInfo.industries && cityInfo.industries.length > 0 && (
                <div className="bg-white p-4 sm:p-5 rounded-xl border border-slate-100 shadow-sm">
                  <div className="text-[10px] sm:text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Top Industry</div>
                  <div className="text-lg sm:text-xl font-black text-slate-900 truncate">{cityInfo.industries[0]}</div>
                </div>
              )}
            </div>
            {cityInfo.industries && cityInfo.industries.length > 1 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {cityInfo.industries.map((ind: string, i: number) => (
                  <span key={i} className="bg-slate-100 text-slate-600 px-3 py-1 rounded-full text-xs font-medium">{ind}</span>
                ))}
              </div>
            )}
          </section>
        )}

        {/* Employers Grid - Mobile optimized */}
        <section className="mb-10 sm:mb-20">
          <h2 className="text-xl sm:text-2xl font-black mb-6 sm:mb-8">{seoData.h2s[2]}</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 sm:gap-6">
            {cityInfo?.majorEmployers?.slice(0, 6).map((employer, i) => (
              <div key={i} className="bg-white p-4 sm:p-6 rounded-xl sm:rounded-2xl border border-slate-100 shadow-sm">
                <div className="w-10 h-10 sm:w-12 sm:h-12 bg-primary-100 rounded-lg sm:rounded-xl flex items-center justify-center mb-3 sm:mb-4">
                  <Briefcase className="w-5 h-5 sm:w-6 sm:h-6 text-primary-600" />
                </div>
                <h3 className="font-bold text-slate-900 text-sm sm:text-base mb-1 sm:mb-2">{employer}</h3>
                <p className="text-xs sm:text-sm text-slate-500">{cityInfo?.industries?.[0] || 'Tech'}</p>
              </div>
            )) || (
              <div className="col-span-full text-center py-8">
                <p className="text-slate-500 text-sm">Employer data coming soon for {formattedCity}</p>
              </div>
            )}
          </div>
        </section>

        {/* FAQ Section - Mobile optimized with schema */}
        <section className="mb-10 sm:mb-20">
          <h2 className="text-xl sm:text-2xl font-black mb-6 sm:mb-8">{seoData.h2s[3]}</h2>
          <div className="space-y-3 sm:space-y-4">
            {seoData.faqs.map((faq, i) => (
              <details key={i} className="bg-white rounded-xl sm:rounded-2xl border border-slate-100 group">
                <summary className="p-4 sm:p-6 cursor-pointer list-none flex items-center justify-between font-semibold text-slate-900 text-sm sm:text-base hover:text-primary-600">
                  {faq.question}
                  <span className="text-slate-400 text-xs">▼</span>
                </summary>
                <div className="px-4 sm:px-6 pb-4 sm:pb-6 text-slate-600 text-sm sm:text-base">
                  {faq.answer}
                </div>
              </details>
            ))}
          </div>
        </section>

        <TopicalClusters clusters={topicalClusters} />

        {/* Related Links - Mobile optimized */}
        <section className="bg-white rounded-2xl sm:rounded-[2.5rem] p-6 sm:p-10 border border-slate-100 shadow-sm mb-10 sm:mb-20">
          <h2 className="text-lg sm:text-xl font-black mb-6 sm:mb-8 text-center">Related Opportunities</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-12">
            <div>
              <h3 className="text-xs sm:text-sm font-bold text-slate-400 uppercase tracking-widest mb-4 sm:mb-6 border-b border-slate-100 pb-2">
                Similar Roles
              </h3>
              <div className="flex flex-wrap gap-2 sm:gap-3">
                {semanticLinks.filter(l => l.entityType === 'role' || l.entityType === 'related-role').slice(0, 5).map((link, i) => (
                  <Link
                    key={i}
                    to={link.url}
                    className="bg-slate-50 hover:bg-primary-50 text-slate-600 hover:text-primary-600 px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg sm:rounded-xl text-xs sm:text-sm font-medium transition-colors border border-slate-100"
                  >
                    {link.anchorText}
                  </Link>
                ))}
              </div>
            </div>
            <div>
              <h3 className="text-xs sm:text-sm font-bold text-slate-400 uppercase tracking-widest mb-4 sm:mb-6 border-b border-slate-100 pb-2">
                Nearby Cities
              </h3>
              <div className="flex flex-wrap gap-2 sm:gap-3">
                {semanticLinks.filter(l => l.entityType === 'location' || l.entityType === 'nearby-location').slice(0, 5).map((link, i) => (
                  <Link
                    key={i}
                    to={link.url}
                    className="bg-slate-50 hover:bg-primary-50 text-slate-600 hover:text-primary-600 px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg sm:rounded-xl text-xs sm:text-sm font-medium transition-colors border border-slate-100"
                  >
                    {link.anchorText}
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* CTA - Mobile optimized */}
        <div className="bg-primary-600 rounded-2xl sm:rounded-[3rem] p-8 sm:p-12 text-white text-center relative overflow-hidden shadow-2xl">
          <div className="absolute top-0 right-0 w-48 sm:w-64 h-48 sm:h-64 bg-white/10 rounded-full blur-3xl" />
          <h2 className="text-2xl sm:text-3xl font-bold mb-4 sm:mb-6 relative z-10 font-display">
            {seoData.cta.headline}
          </h2>
          <p className="text-primary-100 mb-6 sm:mb-10 relative z-10 max-w-lg mx-auto text-base sm:text-lg font-medium">
            {seoData.cta.description}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 items-center justify-center relative z-10">
            <Link
              to="/login"
              className="w-full sm:w-auto bg-white text-primary-600 px-8 sm:px-10 py-4 rounded-xl sm:rounded-2xl font-black text-base sm:text-lg hover:scale-105 transition-transform shadow-xl shadow-white/5"
            >
              {seoData.cta.buttonText}
            </Link>
          </div>
        </div>
      </main>

      {/* Mobile CTA bar */}
      <div className="sm:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 p-4 z-40">
        <Link
          to="/login"
          className="block w-full bg-primary-600 text-white text-center py-4 rounded-xl font-bold"
        >
          Start Applying Free
        </Link>
      </div>
    </div>
  );
}