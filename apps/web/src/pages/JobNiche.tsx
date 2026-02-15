import React from 'react';
import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { Bot, ArrowLeft, MapPin, Sparkles, Briefcase, Zap, TrendingUp, DollarSign, Globe, CheckCircle2 } from 'lucide-react';
import { SEO } from '../components/marketing/SEO';
import { motion } from 'framer-motion';
import rolesData from '../data/roles.json';
import locationsData from '../data/locations.json';
import { generateLocationRoleSEO } from '../utils/seoOptimizer';
import { generateSemanticLinksForLocationRole } from '../utils/semanticLinking';

export default function JobNiche() {
  const { role, city } = useParams<{ role: string; city: string }>();

  const roleInfo = rolesData.find(r => r.id === role);
  const cityInfo = locationsData.find(c => c.id === city);

  // Generate aggressive SEO content using our optimizer
  const seoData = generateLocationRoleSEO(
    roleInfo?.name || role || 'Professional',
    cityInfo?.name || city || 'Remote',
    cityInfo,
    roleInfo
  );

  // Generate semantic internal links
  const semanticLinks = generateSemanticLinksForLocationRole(
    roleInfo?.name || role || 'Professional',
    cityInfo?.name || city || 'Remote',
    roleInfo,
    cityInfo
  );

  const formattedRole = roleInfo?.name || role?.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ') || "Professional";
  const formattedCity = cityInfo?.name || city?.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ') || "Remote";

  const canonicalUrl = `https://jobhuntin.com/jobs/${role ?? ''}/${city ?? ''}`;
  const ogImage = `https://jobhuntin.com/api/og?job=${encodeURIComponent(formattedRole)}&company=${encodeURIComponent(formattedCity)}&score=100&location=${encodeURIComponent(formattedCity)}`;

  // Programmatic City-Specific Stats (Sample logic)
  const isUS = cityInfo?.country === 'USA';

  const salaryStats = React.useMemo(() => {
    // Check if role has comprehensive schema data
    if ((roleInfo as any)?.schema?.[0]?.estimatedSalary) {
      const est = (roleInfo as any).schema[0].estimatedSalary;
      const currency = est.currency === 'USD' ? '$' : '€';
      const format = (val: number) => `${currency}${Math.round(val / 1000)}k`;

      return {
        entry: `${format(est.percentile10)} - ${format(est.percentile25)}`,
        mid: `${format(est.percentile25)} - ${format(est.percentile75)}`,
        senior: `${format(est.percentile75)} - ${format(est.percentile90)}`,
        range: `${format(est.percentile10)} - ${format(est.percentile90)}`
      };
    }

    // Fallback defaults
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

      <header className="bg-white border-b border-slate-200 sticky top-0 z-50 py-4">
        <div className="max-w-7xl mx-auto px-6 flex justify-between items-center">
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center text-white font-black group-hover:rotate-12 transition-transform">JH</div>
            <span className="font-black text-xl tracking-tight">JobHuntin</span>
          </Link>
          <Link to="/login" className="bg-primary-600 text-white px-5 py-2 rounded-xl font-bold text-sm hover:bg-primary-700 transition-colors">
            Get Started
          </Link>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center gap-2 bg-primary-50 text-primary-600 px-4 py-1 rounded-full text-xs font-bold mb-6 border border-primary-100 uppercase tracking-wider">
            <Sparkles className="w-4 h-4" />
            Localized AI Job Hunt
          </div>
          {/* H1 - Primary heading with semantic keywords */}
          <h1 className="text-4xl md:text-6xl font-black font-display mb-6 text-slate-900 leading-[1.1]">
            {seoData.h1}
          </h1>
          <p className="text-xl text-slate-500 max-w-2xl mx-auto font-medium">
            {seoData.description}
          </p>
        </motion.div>

        {/* Market Data Bar */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-20">
          {[
            { label: "Est. Salary", value: salaryStats.range, icon: DollarSign, color: "text-emerald-500" },
            { label: "Active Openings", value: "240+", icon: Briefcase, color: "text-blue-500" },
            { label: "Market Density", value: "High", icon: TrendingUp, color: "text-primary-500" },
            { label: "Remote Options", value: "45%", icon: Globe, color: "text-purple-500" },
          ].map((stat, i) => (
            <div key={i} className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm">
              <div className="flex items-center gap-3 mb-2">
                <stat.icon className={`w-4 h-4 ${stat.color}`} />
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">{stat.label}</span>
              </div>
              <div className="text-xl font-black text-slate-900">{stat.value}</div>
            </div>
          ))}
        </div>

        {/* H2 - Feature comparison section */}
        <div className="grid md:grid-cols-2 gap-12 mb-20 items-center">
          <div>
            <h2 className="text-3xl font-black mb-6">{seoData.h2s[0]}</h2>
            <div className="space-y-4">
              {[
                `Automatic resume tailoring for ${formattedCity} ATS standards`,
                `Stealth submissions that bypass bot detection`,
                `24/7 discovery of new ${formattedRole} openings`,
                `Integrated LinkedIn & Indeed application handling`,
                "Direct outreach to local tech recruiters"
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-3 text-slate-600 font-medium">
                  <CheckCircle2 className="w-5 h-5 text-primary-500 flex-shrink-0" />
                  {item}
                </div>
              ))}
            </div>
          </div>
          <div className="bg-slate-900 rounded-[2.5rem] p-8 text-white relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-primary-500/20 rounded-full blur-3xl" />
            <Bot className="w-12 h-12 text-primary-400 mb-6" />
            <h3 className="text-xl font-bold mb-4">The JobHuntin Edge</h3>
            <p className="text-slate-400 text-sm leading-relaxed mb-6 font-medium">
              Traditional job boards in {formattedCity} are saturated. Our agent uses
              advanced scraping patterns and human-simulated browsing to ensure your applications
              are at the top of the pile the moment a job goes live.
            </p>
            <div className="bg-white/5 border border-white/10 rounded-2xl p-4">
              <div className="text-xs font-bold text-slate-500 mb-1 uppercase">Top Industry</div>
              <div className="text-sm font-bold">{cityInfo?.industries?.[0] || "Technology & Innovation"}</div>
            </div>
          </div>
        </div>

        {/* H2 - Salary analysis section */}
        <section className="mb-20">
          <h2 className="text-2xl font-black mb-8">{seoData.h2s[1]}</h2>
          <div className="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm">
            <div className="grid md:grid-cols-3 gap-8">
              <div>
                <h3 className="text-lg font-bold text-slate-900 mb-3">Entry Level</h3>
                <div className="text-3xl font-black text-emerald-600 mb-2">{salaryStats.entry}</div>
                <p className="text-sm text-slate-500">0-2 years experience</p>
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-900 mb-3">Mid Level</h3>
                <div className="text-3xl font-black text-blue-600 mb-2">{salaryStats.mid}</div>
                <p className="text-sm text-slate-500">3-5 years experience</p>
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-900 mb-3">Senior Level</h3>
                <div className="text-3xl font-black text-purple-600 mb-2">{salaryStats.senior}</div>
                <p className="text-sm text-slate-500">5+ years experience</p>
              </div>
            </div>
            <div className="mt-8 p-4 bg-slate-50 rounded-2xl">
              <p className="text-sm text-slate-600">
                <strong>Pro tip:</strong> {cityInfo?.name || formattedCity} offers competitive salaries with
                {(cityInfo as any)?.costOfLivingIndex ? ` cost of living index of ${(cityInfo as any).costOfLivingIndex}` : ' excellent cost of living'}
                and {(cityInfo as any)?.remotePercentage || '45'}% remote opportunities.
              </p>
            </div>
          </div>
        </section>

        {/* H2 - Local companies section */}
        <section className="mb-20">
          <h2 className="text-2xl font-black mb-8">{seoData.h2s[2]}</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {cityInfo?.majorEmployers?.slice(0, 6).map((employer, i) => (
              <div key={i} className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center mb-4">
                  <Briefcase className="w-6 h-6 text-primary-600" />
                </div>
                <h3 className="font-bold text-slate-900 mb-2">{employer}</h3>
                <p className="text-sm text-slate-500 mb-4">{cityInfo?.industries?.[0] || 'Technology'} Company</p>
                <Link
                  to={`/jobs/${role}/${city}?company=${encodeURIComponent(employer)}`}
                  className="text-primary-600 text-sm font-bold hover:text-primary-700 transition-colors"
                >
                  View Openings →
                </Link>
              </div>
            )) || (
                <div className="col-span-full text-center py-8">
                  <p className="text-slate-500">Major employers data coming soon for {formattedCity}</p>
                </div>
              )}
          </div>
        </section>

        {/* H2 - FAQ section with semantic keywords */}
        <section className="mb-20">
          <h2 className="text-2xl font-black mb-8">{seoData.h2s[3]}</h2>
          <div className="space-y-4">
            {seoData.faqs.map((faq, i) => (
              <div key={i} className="bg-white p-6 rounded-2xl border border-slate-100">
                <h3 className="font-bold text-slate-900 mb-2">{faq.question}</h3>
                <p className="text-slate-500 text-sm font-medium">{faq.answer}</p>
              </div>
            ))}
          </div>
        </section>

        {/* H2 - Application tips section */}
        <section className="mb-20">
          <h2 className="text-2xl font-black mb-8">{seoData.h2s[4]}</h2>
          <div className="bg-gradient-to-br from-primary-50 to-blue-50 p-8 rounded-3xl border border-primary-100">
            <div className="grid md:grid-cols-2 gap-8">
              <div>
                <h3 className="text-lg font-bold text-slate-900 mb-4">Resume Optimization</h3>
                <ul className="space-y-2 text-sm text-slate-600">
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-primary-500 mt-0.5 flex-shrink-0" />
                    Tailor your resume with {cityInfo?.name || formattedCity}-specific keywords
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-primary-500 mt-0.5 flex-shrink-0" />
                    Highlight experience with local tech companies
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-primary-500 mt-0.5 flex-shrink-0" />
                    Include relevant certifications and skills
                  </li>
                </ul>
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-900 mb-4">Interview Preparation</h3>
                <ul className="space-y-2 text-sm text-slate-600">
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-primary-500 mt-0.5 flex-shrink-0" />
                    Research {cityInfo?.name || formattedCity} company culture
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-primary-500 mt-0.5 flex-shrink-0" />
                    Practice technical assessments
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-primary-500 mt-0.5 flex-shrink-0" />
                    Prepare for remote work discussions
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Aggressive Internal Linking Mesh with H3s */}
        <section className="bg-white rounded-[2.5rem] p-10 border border-slate-100 shadow-sm mb-20">
          <h2 className="text-xl font-black mb-8 text-center">Explore Related Opportunities</h2>
          <div className="grid md:grid-cols-2 gap-12">
            <div>
              <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-6 border-b border-slate-100 pb-2">
                Popular {formattedRole} Searches
              </h3>
              <div className="flex flex-wrap gap-3">
                {semanticLinks.filter(l => l.entityType === 'role' || l.entityType === 'related-role').map((link, i) => (
                  <Link
                    key={i}
                    to={link.url}
                    className="bg-slate-50 hover:bg-primary-50 text-slate-600 hover:text-primary-600 px-4 py-2 rounded-xl text-sm font-medium transition-colors border border-slate-100 hover:border-primary-100"
                    title={link.anchorText}
                  >
                    {link.anchorText}
                  </Link>
                ))}
              </div>
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-6 border-b border-slate-100 pb-2">
                Jobs Near {formattedCity}
              </h3>
<div className="flex flex-wrap gap-3">
                {semanticLinks.filter(l => l.entityType === 'location' || l.entityType === 'nearby-location').map((link, i) => (
                  <Link
                    key={i}
                    to={link.url}
                    className="bg-slate-50 hover:bg-primary-50 text-slate-600 hover:text-primary-600 px-4 py-2 rounded-xl text-sm font-medium transition-colors border border-slate-100 hover:border-primary-100"
                    title={link.anchorText}
                  >
                    {link.anchorText}
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* H2 - Feature comparison section */}
<div className="grid md:grid-cols-2 gap-12 mb-20 items-center">
  <div>
    <h2 className="text-3xl font-black mb-6">{seoData.h2s[0]}</h2>
    <div className="space-y-4">
      {[
        `Automatic resume tailoring for ${formattedCity} ATS standards`,
        `Stealth submissions that bypass bot detection`,
        `24/7 discovery of new ${formattedRole} openings`,
        `Integrated LinkedIn & Indeed application handling`,
        "Direct outreach to local tech recruiters"
      ].map((item, i) => (
        <div key={i} className="flex items-center gap-3 text-slate-600 font-medium">
          <CheckCircle2 className="w-5 h-5 text-primary-500 flex-shrink-0" />
          {item}
        </div>
      ))}
    </div>
  </div>
  <div className="bg-slate-900 rounded-[2.5rem] p-8 text-white relative overflow-hidden">
    <div className="absolute top-0 right-0 w-32 h-32 bg-primary-500/20 rounded-full blur-3xl" />
    <Bot className="w-12 h-12 text-primary-400 mb-6" />
    <h3 className="text-xl font-bold mb-4">The JobHuntin Edge</h3>
    <p className="text-slate-400 text-sm leading-relaxed mb-6 font-medium">
      Traditional job boards in {formattedCity} are saturated. Our agent uses
      advanced scraping patterns and human-simulated browsing to ensure your applications
      are at the top of the pile the moment a job goes live.
    </p>
    <div className="bg-white/5 border border-white/10 rounded-2xl p-4">
      <div className="text-xs font-bold text-slate-500 mb-1 uppercase">Top Industry</div>
      <div className="text-sm font-bold">{cityInfo?.industries?.[0] || "Technology & Innovation"}</div>
    </div>
  </div>
</div>

{/* H2 - Salary analysis section */}
<section className="mb-20">
  <h2 className="text-2xl font-black mb-8">{seoData.h2s[1]}</h2>
  <div className="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm">
    <div className="grid md:grid-cols-3 gap-8">
      <div>
        <h3 className="text-lg font-bold text-slate-900 mb-3">Entry Level</h3>
        <div className="text-3xl font-black text-emerald-600 mb-2">{salaryStats.entry}</div>
        <p className="text-sm text-slate-500">0-2 years experience</p>
      </div>
      <div>
        <h3 className="text-lg font-bold text-slate-900 mb-3">Mid Level</h3>
        <div className="text-3xl font-black text-blue-600 mb-2">{salaryStats.mid}</div>
        <p className="text-sm text-slate-500">3-5 years experience</p>
      </div>
      <div>
        <h3 className="text-lg font-bold text-slate-900 mb-3">Senior Level</h3>
        <div className="text-3xl font-black text-purple-600 mb-2">{salaryStats.senior}</div>
        <p className="text-sm text-slate-500">5+ years experience</p>
      </div>
    </div>
    <div className="mt-8 p-4 bg-slate-50 rounded-2xl">
      <p className="text-sm text-slate-600">
        <strong>Pro tip:</strong> {cityInfo?.name || formattedCity} offers competitive salaries with
        {(cityInfo as any)?.costOfLivingIndex ? ` cost of living index of ${(cityInfo as any).costOfLivingIndex}` : ' excellent cost of living'}
        and {(cityInfo as any)?.remotePercentage || '45'}% remote opportunities.
      </p>
    </div>
  </div>
</section>

{/* H2 - Local companies section */}
<section className="mb-20">
  <h2 className="text-2xl font-black mb-8">{seoData.h2s[2]}</h2>
  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
    {cityInfo?.majorEmployers?.slice(0, 6).map((employer, i) => (
      <div key={i} className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
        <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center mb-4">
          <Briefcase className="w-6 h-6 text-primary-600" />
        </div>
        <h3 className="font-bold text-slate-900 mb-2">{employer}</h3>
        <p className="text-sm text-slate-500 mb-4">{cityInfo?.industries?.[0] || 'Technology'} Company</p>
        <Link
          to={`/jobs/${role}/${city}?company=${encodeURIComponent(employer)}`}
          className="text-primary-600 text-sm font-bold hover:text-primary-700 transition-colors"
        >
          View Openings →
        </Link>
      </div>
    )) || (
        <div className="col-span-full text-center py-8">
          <p className="text-slate-500">Major employers data coming soon for {formattedCity}</p>
        </div>
      )}
  </div>
</section>

{/* H2 - FAQ section with semantic keywords */}
<section className="mb-20">
  <h2 className="text-2xl font-black mb-8">{seoData.h2s[3]}</h2>
  <div className="space-y-4">
    {seoData.faqs.map((faq, i) => (
      <div key={i} className="bg-white p-6 rounded-2xl border border-slate-100">
        <h3 className="font-bold text-slate-900 mb-2">{faq.question}</h3>
        <p className="text-slate-500 text-sm font-medium">{faq.answer}</p>
      </div>
    ))}
  </div>
</section>

{/* H2 - Application tips section */}
<section className="mb-20">
  <h2 className="text-2xl font-black mb-8">{seoData.h2s[4]}</h2>
  <div className="bg-gradient-to-br from-primary-50 to-blue-50 p-8 rounded-3xl border border-primary-100">
    <div className="grid md:grid-cols-2 gap-8">
      <div>
        <h3 className="text-lg font-bold text-slate-900 mb-4">Resume Optimization</h3>
        <ul className="space-y-2 text-sm text-slate-600">
          <li className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-primary-500 mt-0.5 flex-shrink-0" />
            Tailor your resume with {cityInfo?.name || formattedCity}-specific keywords
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-primary-500 mt-0.5 flex-shrink-0" />
            Highlight experience with local tech companies
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-primary-500 mt-0.5 flex-shrink-0" />
            Include relevant certifications and skills
          </li>
        </ul>
      </div>
      <div>
        <h3 className="text-lg font-bold text-slate-900 mb-4">Interview Preparation</h3>
        <ul className="space-y-2 text-sm text-slate-600">
          <li className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-primary-500 mt-0.5 flex-shrink-0" />
            Research {cityInfo?.name || formattedCity} company culture
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-primary-500 mt-0.5 flex-shrink-0" />
            Practice technical assessments
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-primary-500 mt-0.5 flex-shrink-0" />
            Prepare for remote work discussions
          </li>
        </ul>
      </div>
    </div>
  </div>
</section>

{/* Aggressive Internal Linking Mesh with H3s */}
<section className="bg-white rounded-[2.5rem] p-10 border border-slate-100 shadow-sm mb-20">
  <h2 className="text-xl font-black mb-8 text-center">Explore Related Opportunities</h2>
  <div className="grid md:grid-cols-2 gap-12">
    <div>
      <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-6 border-b border-slate-100 pb-2">
        Popular {formattedRole} Searches
      </h3>
      <div className="flex flex-wrap gap-3">
        {semanticLinks.filter(l => l.entityType === 'role' || l.entityType === 'related-role').map((link, i) => (
          <Link
            key={i}
            to={link.url}
            className="bg-slate-50 hover:bg-primary-50 text-slate-600 hover:text-primary-600 px-4 py-2 rounded-xl text-sm font-medium transition-colors border border-slate-100 hover:border-primary-100"
            title={link.anchorText}
          >
            {link.anchorText}
          </Link>
        ))}
      </div>
    </div>
    <div>
      <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-6 border-b border-slate-100 pb-2">
        Jobs Near {formattedCity}
      </h3>
      <div className="flex flex-wrap gap-3">
        {semanticLinks.filter(l => l.entityType === 'location' || l.entityType === 'nearby-location').map((link, i) => (
          <Link
            key={i}
            to={link.url}
            className="bg-slate-50 hover:bg-primary-50 text-slate-600 hover:text-primary-600 px-4 py-2 rounded-xl text-sm font-medium transition-colors border border-slate-100 hover:border-primary-100"
            title={link.anchorText}
          >
            {link.anchorText}
          </Link>
        ))}
      </div>
    </div>
  </div>
</section>

{/* Popular Cities & Roles for crawl paths */}
<div className="mt-10 pt-10 border-t border-slate-100">
  <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-6 text-center">
    Explore More Opportunities
  </h3>
  <div className="grid md:grid-cols-2 gap-8">
    <div>
      <h4 className="text-sm font-bold text-slate-600 mb-4">Top Cities</h4>
      <div className="flex flex-wrap gap-2">
        {['San Francisco', 'New York', 'Austin', 'Seattle', 'Los Angeles', 'Boston', 'Denver', 'Chicago'].slice(0, 6).map((city) => (
          <Link
            key={city}
            to={`/jobs/${role}/${city.toLowerCase().replace(/\s+/g, '-')}`}
            className="bg-slate-50 hover:bg-primary-50 text-slate-600 hover:text-primary-600 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border border-slate-100 hover:border-primary-100"
          >
            {city}
          </Link>
        ))}
      </div>
    </div>
    <div>
      <h4 className="text-sm font-bold text-slate-600 mb-4">Top Roles</h4>
      <div className="flex flex-wrap gap-2">
        {['Software Engineer', 'Data Scientist', 'Product Manager', 'UX Designer', 'Marketing Manager', 'AI Developer'].slice(0, 6).map((roleName) => (
          <Link
            key={roleName}
            to={`/jobs/${roleName.toLowerCase().replace(/\s+/g, '-')}/${city}`}
            className="bg-slate-50 hover:bg-primary-50 text-slate-600 hover:text-primary-600 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border border-slate-100 hover:border-primary-100"
          >
            {roleName}
          </Link>
        ))}
      </div>
    </div>
  </div>
</div>

{/* Deep Competitor Links for Authority */}
<div className="mt-10 pt-10 border-t border-slate-100">
  <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-6 text-center">
    Compare Job Search Tools
  </h3>
  <div className="flex flex-wrap justify-center gap-4">
    {semanticLinks.filter(l => l.entityType === 'competitor').map((link, i) => (
      <Link
        key={i}
        to={link.url}
        className="text-slate-500 hover:text-primary-600 text-sm font-medium transition-colors flex items-center gap-2"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-slate-300"></span>
        {link.anchorText}
      </Link>
    ))}
  </div>
</div>

{/* CTA with semantic keywords */}
<div className="bg-primary-600 rounded-[3rem] p-12 text-white text-center relative overflow-hidden shadow-2xl">
  <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl" />
  <h2 className="text-3xl font-bold mb-6 relative z-10 font-display">
    {seoData.cta.headline}
  </h2>
  <p className="text-primary-100 mb-10 relative z-10 max-w-lg mx-auto text-lg font-medium">
    {seoData.cta.description}
  </p>
  <div className="flex flex-col sm:flex-row gap-4 items-center justify-center relative z-10">
    <Link
      to="/login"
      className="bg-white text-primary-600 px-10 py-4 rounded-2xl font-black text-lg hover:scale-105 transition-transform shadow-xl shadow-white/5"
      title={`Apply for ${formattedRole} jobs in ${formattedCity} with AI automation`}
    >
      {seoData.cta.buttonText}
    </Link>
    <Link to="/pricing" className="text-primary-100 font-bold hover:underline">
      View Pricing Plans
    </Link>
  </div>
</div>
</main>
</div>