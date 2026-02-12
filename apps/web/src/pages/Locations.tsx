
import React, { useMemo } from 'react';
import { Helmet } from 'react-helmet-async';
import { Link } from 'react-router-dom';
import locations from '../data/locations.json';
import roles from '../data/roles.json';

// Simple check for popular cities to highlight
const POPULAR_CITIES = ['New York', 'San Francisco', 'Austin', 'London', 'Remote'];

export default function Locations() {
    // Group locations by region or just list them alphabetically
    const sortedLocations = useMemo(() =>
        [...locations].sort((a, b) => a.name.localeCompare(b.name)),
        []);

    // Group roles by category
    const rolesByCategory = useMemo(() => {
        const grouped: Record<string, typeof roles> = {};
        roles.forEach(role => {
            const cat = role.category || 'Other';
            if (!grouped[cat]) grouped[cat] = [];
            grouped[cat].push(role);
        });
        return grouped;
    }, []);

    return (
        <>
            <Helmet>
                <title>Job Hunt Locations & Roles | JobHuntin</title>
                <meta name="description" content="Browse jobs by location and role. Find the best opportunities in tech, marketing, sales, and more across top cities worldwide." />
            </Helmet>

            <div className="bg-white min-h-screen pt-24 pb-16">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

                    <div className="text-center mb-16">
                        <h1 className="text-4xl font-extrabold text-slate-900 sm:text-5xl">
                            Browse Jobs by Location & Role
                        </h1>
                        <p className="mt-4 text-xl text-slate-600">
                            Explore opportunities in your city or find your dream role.
                        </p>
                    </div>

                    {/* Locations Grid */}
                    <section className="mb-16">
                        <h2 className="text-2xl font-bold text-slate-900 mb-8 border-b pb-2">Destinations</h2>
                        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                            {sortedLocations.map(loc => (
                                <div key={loc.id} className="group">
                                    <h3 className="font-semibold text-slate-900 mb-2 group-hover:text-blue-600 transition-colors">
                                        {loc.name}
                                    </h3>
                                    <ul className="space-y-1 text-sm text-slate-500">
                                        {/* Link to top 3 roles for this city to create mesh */}
                                        {roles.slice(0, 3).map(role => (
                                            <li key={role.id}>
                                                <Link to={`/jobs/${role.id}/${loc.id}`} className="hover:text-blue-500 hover:underline block truncate">
                                                    {role.name}
                                                </Link>
                                            </li>
                                        ))}
                                        <li>
                                            <span className="text-xs text-slate-400 italic">...and {roles.length - 3} more</span>
                                        </li>
                                    </ul>
                                </div>
                            ))}
                        </div>
                    </section>

                    {/* Roles Grid */}
                    <section>
                        <h2 className="text-2xl font-bold text-slate-900 mb-8 border-b pb-2">Browse by Role</h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                            {Object.entries(rolesByCategory).map(([category, categoryRoles]) => (
                                <div key={category} className="bg-slate-50 p-6 rounded-2xl border border-slate-100">
                                    <h3 className="text-lg font-bold text-slate-900 mb-4">{category}</h3>
                                    <ul className="space-y-2">
                                        {categoryRoles.map(role => (
                                            <li key={role.id}>
                                                <Link
                                                    to={`/jobs/${role.id}/remote`}
                                                    className="text-slate-600 hover:text-blue-600 hover:underline flex items-center justify-between"
                                                >
                                                    <span>{role.name}</span>
                                                    <span className="text-xs bg-white px-2 py-1 rounded-full border border-slate-200 text-slate-400">
                                                        Apply
                                                    </span>
                                                </Link>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            ))}
                        </div>
                    </section>

                </div>
            </div>
        </>
    );
}
