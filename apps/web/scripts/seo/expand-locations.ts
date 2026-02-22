/**
 * Script to expand locations.json with complete SEO data
 * Run with: npx tsx scripts/seo/expand-locations.ts
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

interface LocationData {
  id: string;
  name: string;
  country: string;
  state: string;
  population: string | number;
  industry?: string;
  slug?: string;
  medianIncome?: number;
  costOfLivingIndex?: number;
  unemploymentRate?: number;
  majorEmployers?: string[];
  industries?: string[];
  techHub?: boolean;
  startupScene?: boolean;
  remoteFriendly?: boolean;
  seoTitle?: string;
  seoDescription?: string;
  h1?: string;
  h2s?: string[];
  contentSections?: any[];
  localKeywords?: string[];
  longTailKeywords?: string[];
  semanticKeywords?: string[];
  entityMentions?: string[];
  schema?: any[];
  lastUpdated?: string;
  semanticTriples?: any[];
  knowledgeGraphTargets?: string[];
  remotePercentage?: number;
}

// City data with employers and industries
const cityData: Record<string, Partial<LocationData>> = {
  // US Tech Hubs
  'san-francisco': {
    majorEmployers: ['Salesforce', 'Uber', 'Airbnb', 'Twitter', 'Stripe', 'Dropbox', 'Lyft', 'Instacart', 'Square', 'Meta'],
    industries: ['Technology', 'Fintech', 'SaaS', 'AI/ML', 'Healthcare Tech'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 120000,
    costOfLivingIndex: 280,
    unemploymentRate: 3.2,
  },
  'new-york': {
    majorEmployers: ['Google', 'Meta', 'Amazon', 'Goldman Sachs', 'JPMorgan', 'Bloomberg', 'Spotify', 'Etsy', 'ViacomCBS', 'IBM'],
    industries: ['Finance', 'Technology', 'Media', 'Advertising', 'Healthcare'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 95000,
    costOfLivingIndex: 240,
    unemploymentRate: 4.5,
  },
  'seattle': {
    majorEmployers: ['Amazon', 'Microsoft', 'Google', 'Boeing', 'T-Mobile', 'Tableau', 'Zillow', 'Redfin', 'Nordstrom', 'Expedia'],
    industries: ['Technology', 'Aerospace', 'E-commerce', 'Cloud Computing', 'Gaming'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 105000,
    costOfLivingIndex: 195,
    unemploymentRate: 3.8,
  },
  'austin': {
    majorEmployers: ['Tesla', 'Oracle', 'Google', 'Apple', 'Meta', 'Netflix', 'Indeed', 'Dell', 'IBM', 'Whole Foods'],
    industries: ['Technology', 'Finance', 'Healthcare', 'E-commerce', 'Startups'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 85000,
    costOfLivingIndex: 180,
    unemploymentRate: 4.2,
  },
  'los-angeles': {
    majorEmployers: ['Google', 'Netflix', 'Disney', 'Hulu', 'SpaceX', 'Snap Inc', 'YouTube', 'Activision', 'Uber', 'Amazon'],
    industries: ['Entertainment', 'Technology', 'Aerospace', 'Gaming', 'Media'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 78000,
    costOfLivingIndex: 210,
    unemploymentRate: 5.1,
  },
  'denver': {
    majorEmployers: ['Google', 'Amazon', 'Palantir', 'SendGrid', 'Guild Education', 'WW', 'Lockheed Martin', 'DaVita', 'CH2M Hill', 'Arrow Electronics'],
    industries: ['Technology', 'Aerospace', 'Telecommunications', 'Healthcare', 'Energy'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 82000,
    costOfLivingIndex: 165,
    unemploymentRate: 3.9,
  },
  'boston': {
    majorEmployers: ['Google', 'Amazon', 'Microsoft', 'HubSpot', 'Wayfair', 'Tripadvisor', 'Akamai', 'Vertex', 'Moderna', 'DraftKings'],
    industries: ['Biotech', 'Technology', 'Healthcare', 'Education', 'Finance'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 90000,
    costOfLivingIndex: 185,
    unemploymentRate: 4.0,
  },
  'chicago': {
    majorEmployers: ['Google', 'Salesforce', 'Groupon', 'Grubhub', 'Cameo', 'Tempus', 'Caterpillar', 'Boeing', 'Allstate', 'United Airlines'],
    industries: ['Finance', 'Technology', 'Manufacturing', 'Healthcare', 'Logistics'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 72000,
    costOfLivingIndex: 145,
    unemploymentRate: 5.2,
  },
  'miami': {
    majorEmployers: ['Citrix', 'OpenEnglish', 'Reef Technology', 'Nearpod', 'Kaseya', 'Ultimate Software', 'Wix', 'Thrasio', 'Boats Group', 'Mojang'],
    industries: ['Fintech', 'Technology', 'Real Estate', 'Tourism', 'Healthcare'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 62000,
    costOfLivingIndex: 160,
    unemploymentRate: 4.8,
  },
  'atlanta': {
    majorEmployers: ['Google', 'Microsoft', 'Salesforce', 'NCR', 'Mailchimp', 'Cox Enterprises', 'Home Depot', 'Coca-Cola', 'Delta', 'Visa'],
    industries: ['Fintech', 'Technology', 'Logistics', 'Healthcare', 'Media'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 72000,
    costOfLivingIndex: 135,
    unemploymentRate: 4.3,
  },
  // Additional US Cities
  'portland': {
    majorEmployers: ['Nike', 'Intel', 'Daimler', 'Sage Software', 'Puppet', 'Elemental', 'New Relic', 'Airbnb', 'Amazon', 'Wieden+Kennedy'],
    industries: ['Technology', 'Manufacturing', 'Sportswear', 'Creative', 'Healthcare'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 74000,
    costOfLivingIndex: 155,
    unemploymentRate: 4.5,
  },
  'phoenix': {
    majorEmployers: ['Intel', 'GoDaddy', 'Carvana', 'DoorDash', 'Honeywell', 'Benchmark Electronics', 'Microchip Technology', 'Insight Enterprises', 'Banner Health', 'State Farm'],
    industries: ['Technology', 'Semiconductors', 'Healthcare', 'Finance', 'Manufacturing'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 65000,
    costOfLivingIndex: 125,
    unemploymentRate: 4.0,
  },
  'dallas': {
    majorEmployers: ['AT&T', 'Texas Instruments', 'Southwest Airlines', 'American Airlines', 'ExxonMobil', 'Capital One', 'Match Group', 'StackPath', 'Baylor Scott & White', 'Verizon'],
    industries: ['Telecommunications', 'Technology', 'Energy', 'Finance', 'Healthcare'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 68000,
    costOfLivingIndex: 130,
    unemploymentRate: 4.2,
  },
  'houston': {
    majorEmployers: ['IBM', 'HP Enterprise', 'Oracle', 'Sysco', 'Halliburton', 'Baker Hughes', 'Apache Corp', 'FMC Technologies', 'BMC Software', 'HighRadius'],
    industries: ['Energy', 'Technology', 'Healthcare', 'Aerospace', 'Manufacturing'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 62000,
    costOfLivingIndex: 120,
    unemploymentRate: 5.5,
  },
  'san-diego': {
    majorEmployers: ['Qualcomm', 'Intuit', 'Illumina', ' ViaSat', 'GoDaddy', 'BD', 'Thermo Fisher', 'Teradata', 'Hologic', 'Sony'],
    industries: ['Biotech', 'Technology', 'Defense', 'Healthcare', 'Telecommunications'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 82000,
    costOfLivingIndex: 175,
    unemploymentRate: 4.1,
  },
  'minneapolis': {
    majorEmployers: ['Target', 'Best Buy', 'General Mills', '3M', 'UnitedHealth', 'Thomson Reuters', 'Medtronic', 'Cargill', 'Ameriprise', 'Xcel Energy'],
    industries: ['Retail', 'Healthcare', 'Food', 'Technology', 'Finance'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 72000,
    costOfLivingIndex: 130,
    unemploymentRate: 3.5,
  },
  'nashville': {
    majorEmployers: ['Amazon', 'Oracle', 'HCA Healthcare', 'Bridgestone', 'Asurion', 'Change Healthcare', 'Eventbrite', 'SmileDirectClub', 'Snapshot', 'Dollar General'],
    industries: ['Healthcare', 'Technology', 'Music/Entertainment', 'Finance', 'Automotive'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 62000,
    costOfLivingIndex: 125,
    unemploymentRate: 3.8,
  },
  'charlotte': {
    majorEmployers: ['Bank of America', 'Wells Fargo', 'Truist', 'Honeywell', 'Duke Energy', 'LendingTree', 'AvidXchange', 'Apex Clean Energy', 'Red Ventures', 'Spectrum'],
    industries: ['Finance', 'Banking', 'Technology', 'Energy', 'Healthcare'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 65000,
    costOfLivingIndex: 115,
    unemploymentRate: 4.0,
  },
  'salt-lake-city': {
    majorEmployers: ['Adobe', 'Overstock', 'Ancestry', 'Qualtrics', 'Pluralsight', 'Domo', 'HealthCatalyst', 'Instructure', 'CHG Healthcare', 'Northrop Grumman'],
    industries: ['Technology', 'Healthcare', 'Finance', 'Outdoor Recreation', 'Education'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 68000,
    costOfLivingIndex: 130,
    unemploymentRate: 3.2,
  },
  'raleigh': {
    majorEmployers: ['Red Hat', 'IBM', 'Cisco', 'NetApp', 'Biogen', 'SAS Institute', 'Lenovo', 'Epic Games', 'Citrix', 'Burt\'s Bees'],
    industries: ['Technology', 'Biotech', 'Healthcare', 'Education', 'Research'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 70000,
    costOfLivingIndex: 120,
    unemploymentRate: 3.8,
  },
  'pittsburgh': {
    majorEmployers: ['Google', 'Uber', 'Meta', 'Amazon', 'Duolingo', 'Argo AI', 'Aurora', 'Aptiv', 'PPG', 'Alcoa'],
    industries: ['Technology', 'Autonomous Vehicles', 'Healthcare', 'Robotics', 'Finance'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 58000,
    costOfLivingIndex: 105,
    unemploymentRate: 4.8,
  },
  'detroit': {
    majorEmployers: ['Quicken Loans', 'Ford', 'General Motors', 'Stellantis', 'Amazon', 'Google', 'StockX', 'Guardian Industries', 'DTE Energy', 'Blue Cross'],
    industries: ['Automotive', 'Technology', 'Manufacturing', 'Finance', 'Healthcare'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 55000,
    costOfLivingIndex: 100,
    unemploymentRate: 5.8,
  },
  // International Cities
  'london': {
    majorEmployers: ['Google', 'Amazon', 'Meta', 'Apple', 'Microsoft', 'DeepMind', 'Revolut', 'Monzo', 'TransferWise', 'Deliveroo'],
    industries: ['Finance', 'Technology', 'Fintech', 'Media', 'Healthcare'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 65000,
    costOfLivingIndex: 200,
    unemploymentRate: 4.5,
  },
  'toronto': {
    majorEmployers: ['Google', 'Amazon', 'Microsoft', 'Shopify', 'Wattpad', 'Watson', 'Rypple', 'Kik', '1Password', 'Element AI'],
    industries: ['Technology', 'Finance', 'AI/ML', 'Healthcare', 'Education'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 75000,
    costOfLivingIndex: 145,
    unemploymentRate: 5.5,
  },
  'berlin': {
    majorEmployers: ['Amazon', 'Google', 'Zalando', 'Delivery Hero', 'N26', 'SumUp', 'HelloFresh', 'Wunder Mobility', 'SoundCloud', 'Tier Mobility'],
    industries: ['Technology', 'E-commerce', 'Fintech', 'Gaming', 'Mobility'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 55000,
    costOfLivingIndex: 130,
    unemploymentRate: 5.2,
  },
  'amsterdam': {
    majorEmployers: ['Booking.com', 'Uber', 'Netflix', 'Adyen', 'Takeaway.com', 'WeTransfer', 'Just Eat', 'Mendix', 'Optiver', 'TomTom'],
    industries: ['Technology', 'Fintech', 'E-commerce', 'Travel', 'AI/ML'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 60000,
    costOfLivingIndex: 155,
    unemploymentRate: 4.0,
  },
  'singapore': {
    majorEmployers: ['Google', 'Meta', 'Amazon', 'Grab', 'Sea Group', 'Razer', 'Carousell', 'PatSnap', 'Trax', 'Ninja Van'],
    industries: ['Technology', 'Finance', 'E-commerce', 'Biotech', 'Logistics'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 85000,
    costOfLivingIndex: 195,
    unemploymentRate: 2.8,
  },
  'sydney': {
    majorEmployers: ['Atlassian', 'Canva', 'Afterpay', 'Airwallex', 'SafetyCulture', 'Envato', 'Hipages', 'Airtasker', 'Campaign Monitor', 'Nearmap'],
    industries: ['Technology', 'Finance', 'Fintech', 'Media', 'Healthcare'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 78000,
    costOfLivingIndex: 175,
    unemploymentRate: 4.2,
  },
  'dubai': {
    majorEmployers: ['Amazon', 'Microsoft', 'Google', 'Careem', 'Noon', 'Tabby', 'Tamara', 'Emerging Markets Property Group', 'Property Finder', 'Beam'],
    industries: ['Technology', 'Finance', 'E-commerce', 'Real Estate', 'Tourism'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 70000,
    costOfLivingIndex: 145,
    unemploymentRate: 3.0,
  },
  'tel-aviv': {
    majorEmployers: ['Google', 'Microsoft', 'Amazon', 'Meta', 'Apple', 'Waze', 'Mobileye', 'Fiverr', 'Wix', 'SimilarWeb'],
    industries: ['Technology', 'Cybersecurity', 'AI/ML', 'Fintech', 'Healthcare'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 55000,
    costOfLivingIndex: 135,
    unemploymentRate: 4.5,
  },
  'paris': {
    majorEmployers: ['Google', 'Amazon', 'Meta', 'Blablacar', 'Veepee', 'Doctolib', 'Qonto', 'Swile', 'Back Market', 'ContentSquare'],
    industries: ['Technology', 'Fintech', 'E-commerce', 'Healthcare', 'AI/ML'],
    techHub: true,
    startupScene: true,
    remoteFriendly: true,
    medianIncome: 52000,
    costOfLivingIndex: 145,
    unemploymentRate: 7.2,
  },
};

function generateSeoFields(location: LocationData): LocationData {
  const name = location.name;
  const year = new Date().getFullYear();
  const month = new Date().toLocaleString('default', { month: 'long' });
  
  const hasRichData = cityData[location.id];
  
  return {
    ...location,
    ...hasRichData,
    slug: location.id,
    remotePercentage: hasRichData?.remoteFriendly ? 45 : 25,
    seoTitle: `${name} Tech Jobs (${year}): Find Your Next Role | JobHuntin`,
    seoDescription: `Discover ${hasRichData?.majorEmployers?.length || 50}+ tech jobs in ${name}. Average salary $${Math.floor((hasRichData?.medianIncome || 75000) / 1000)}K. Top employers: ${(hasRichData?.majorEmployers || ['Top tech companies']).slice(0, 3).join(', ')}.`,
    h1: `Tech Jobs in ${name}: ${hasRichData?.majorEmployers?.length || 100}+ Opportunities`,
    h2s: [
      `Top Tech Companies Hiring in ${name}`,
      `Average Tech Salaries in ${name} (${year})`,
      `Best Tech Skills to Get Hired in ${name}`,
      `Remote vs On-site Jobs in ${name}`,
      `How to Land a Tech Job in ${name} Fast`,
      `${name} Tech Industry Overview`,
      `Networking & Tech Events in ${name}`,
      `Cost of Living for Tech Workers in ${name}`,
    ],
    localKeywords: [
      `${name} tech jobs`,
      `${name} software engineer`,
      `${name} developer jobs`,
      `tech jobs ${name}`,
      `${name} startups`,
      `${name} IT jobs`,
      `${name} remote jobs`,
      `${name} coding bootcamp`,
    ],
    longTailKeywords: [
      `best tech companies ${name}`,
      `average software engineer salary ${name}`,
      `how to get tech job ${name}`,
      `${name} tech scene`,
      `moving to ${name} for tech job`,
    ],
    lastUpdated: new Date().toISOString().split('T')[0],
  };
}

function expandLocations() {
  const locationsPath = path.resolve(__dirname, '../../src/data/locations.json');
  const locations: LocationData[] = JSON.parse(fs.readFileSync(locationsPath, 'utf-8'));
  
  const expandedLocations = locations.map(loc => {
    if (cityData[loc.id]) {
      return generateSeoFields(loc);
    }
    // For cities without rich data, still add basic SEO fields
    return {
      ...loc,
      slug: loc.id,
      majorEmployers: loc.industry ? [`${loc.industry.split(',')[0]} Companies`, 'Local Startups', 'Tech Firms'] : ['Local Employers', 'Startups', 'Tech Companies'],
      industries: loc.industry ? loc.industry.split(', ') : ['Technology', 'Services'],
      techHub: false,
      startupScene: false,
      remoteFriendly: true,
      remotePercentage: 35,
      medianIncome: 65000,
      costOfLivingIndex: 120,
      unemploymentRate: 4.5,
      seoTitle: `${loc.name} Jobs (${new Date().getFullYear()}): Find Opportunities | JobHuntin`,
      seoDescription: `Find tech jobs in ${loc.name}, ${loc.state || loc.country}. Browse opportunities from top local employers.`,
      h1: `Jobs in ${loc.name}: Opportunities & Career Guide`,
      h2s: [
        `Top Employers in ${loc.name}`,
        `Job Market Overview`,
        `How to Find Jobs in ${loc.name}`,
        `Salary Guide for ${loc.name}`,
      ],
      localKeywords: [`${loc.name} jobs`, `jobs ${loc.name}`, `${loc.name} careers`],
      longTailKeywords: [`find jobs in ${loc.name}`, `${loc.name} job search`],
      lastUpdated: new Date().toISOString().split('T')[0],
    };
  });
  
  fs.writeFileSync(locationsPath, JSON.stringify(expandedLocations, null, 2));
  console.log("✅ Expanded", expandedLocations.length, "locations with SEO data");

  const citiesWithRichData = expandedLocations.filter((l) => cityData[l.id!]).length;
  console.log("   -", citiesWithRichData, "cities with rich employer/industry data");
}

expandLocations();
