import React, { useMemo } from "react";
import { Link } from "react-router-dom";
import { MapPin, Briefcase, Building2, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";
import { SEO } from "../components/marketing/SEO";
import { ConversionCTA } from "../components/seo/ConversionCTA";
import { useDynamicData } from "../hooks/useDynamicData";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";

const POPULAR_CITIES = [
  "New York",
  "San Francisco",
  "Austin",
  "London",
  "Remote",
];

export default function Locations() {
  const { data: locationsData, loading: loadingLocations } = useDynamicData(
    () => import("../data/locations.json"),
  );
  const { data: rolesData, loading: loadingRoles } = useDynamicData(
    () => import("../data/roles.json"),
  );

  const locations = locationsData ?? [];
  const roles = rolesData ?? [];

  const sortedLocations = useMemo(
    () => [...locations].sort((a, b) => a.name.localeCompare(b.name)),
    [locations],
  );

  const rolesByCategory = useMemo(() => {
    type RoleItem = { id: string; name: string; category?: string };
    const grouped: Record<string, RoleItem[]> = {};
    for (const role of roles as RoleItem[]) {
      const cat = role.category || "Other";
      if (!grouped[cat]) grouped[cat] = [];
      grouped[cat].push(role);
    }
    return grouped;
  }, [roles]);

  if (loadingLocations || loadingRoles) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <LoadingSpinner label="Loading..." />
      </div>
    );
  }

  const title = "Find Jobs by Location & Role | Remote, NYC, SF, Austin & More";
  const description =
    "Browse AI-powered job opportunities by location and role. Find remote jobs, tech roles in NYC, marketing positions in Austin, and more. JobHuntin auto-applies to matches.";
  const canonicalUrl = "https://jobhuntin.com/locations";

  return (
    <div className="bg-white min-h-screen">
      <SEO
        title={title}
        description={description}
        ogTitle={title}
        canonicalUrl={canonicalUrl}
        schema={[
          {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            name: "Jobs by Location and Role",
            description: description,
            url: canonicalUrl,
          },
          {
            "@context": "https://schema.org",
            "@type": "ItemList",
            name: "Job Locations",
            numberOfItems: locations.length,
            itemListElement: locations.slice(0, 20).map((loc, index) => ({
              "@type": "ListItem",
              position: index + 1,
              name: loc.name,
              url: `https://jobhuntin.com/jobs/software-engineer/${loc.id}`,
            })),
          },
          {
            "@context": "https://schema.org",
            "@type": "ItemList",
            name: "Job Roles",
            numberOfItems: roles.length,
            itemListElement: roles.slice(0, 20).map((role, index) => ({
              "@type": "ListItem",
              position: index + 1,
              name: role.name,
              url: `https://jobhuntin.com/jobs/${role.id}/remote`,
            })),
          },
        ]}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center gap-2 bg-primary-50 text-primary-600 px-4 py-1 rounded-full text-sm font-bold mb-6 border border-primary-100">
            <MapPin className="w-4 h-4" />
            Location-Based Job Discovery
          </div>
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-sans font-black mb-6 text-slate-900">
            Find Jobs by Location <br />
            <span className="text-primary-600 font-black">& Role</span>
          </h1>
          <p className="text-lg sm:text-xl text-slate-500 max-w-2xl mx-auto font-medium">
            Browse AI-powered job opportunities in your city or target role.
            JobHuntin discovers and auto-applies to matching positions.
          </p>
        </motion.div>

        <section className="mb-20" aria-labelledby="locations-heading">
          <div className="flex items-center gap-3 mb-8">
            <Building2 className="w-6 h-6 text-primary-600" />
            <h2
              id="locations-heading"
              className="text-2xl font-bold text-slate-900"
            >
              Popular Job Markets
            </h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {sortedLocations.map((loc) => (
              <motion.div
                key={loc.id}
                className="group bg-white rounded-2xl border border-slate-100 p-4 hover:border-primary-200 hover:shadow-lg transition-all"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <h3 className="font-bold text-slate-900 mb-3 group-hover:text-primary-600 transition-colors flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-slate-400" />
                  {loc.name}
                </h3>
                <ul className="space-y-1.5 text-sm text-slate-500">
                  {roles.slice(0, 3).map((role) => (
                    <li key={role.id}>
                      <Link
                        to={`/jobs/${role.id}/${loc.id}`}
                        className="hover:text-primary-600 hover:underline block truncate transition-colors"
                      >
                        {role.name}
                      </Link>
                    </li>
                  ))}
                  <li>
                    <Link
                      to={`/jobs/software-engineer/${loc.id}`}
                      className="text-xs text-primary-600 font-medium hover:underline flex items-center gap-1"
                    >
                      View all <ArrowRight className="w-3 h-3" />
                    </Link>
                  </li>
                </ul>
              </motion.div>
            ))}
          </div>
        </section>

        <section className="mb-20" aria-labelledby="roles-heading">
          <div className="flex items-center gap-3 mb-8">
            <Briefcase className="w-6 h-6 text-primary-600" />
            <h2
              id="roles-heading"
              className="text-2xl font-bold text-slate-900"
            >
              Browse by Job Role
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Object.entries(rolesByCategory).map(
              ([category, categoryRoles]) => (
                <motion.div
                  key={category}
                  className="bg-slate-50 p-6 rounded-2xl border border-slate-100 hover:border-primary-200 transition-colors"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <h3 className="text-lg font-bold text-slate-900 mb-4">
                    {category}
                  </h3>
                  <ul className="space-y-2">
                    {categoryRoles.map((role) => (
                      <li key={role.id}>
                        <Link
                          to={`/jobs/${role.id}/remote`}
                          className="text-slate-600 hover:text-primary-600 hover:underline flex items-center justify-between group"
                        >
                          <span>{role.name}</span>
                          <span className="text-xs bg-white px-2 py-1 rounded-full border border-slate-200 text-slate-400 group-hover:border-primary-200 group-hover:text-primary-600 transition-colors">
                            Apply
                          </span>
                        </Link>
                      </li>
                    ))}
                  </ul>
                </motion.div>
              ),
            )}
          </div>
        </section>

        <ConversionCTA variant="location" />
      </main>
    </div>
  );
}
