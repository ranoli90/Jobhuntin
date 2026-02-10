
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const LOCATIONS_FILE = path.resolve(__dirname, '../../src/data/locations.json');

const MAJOR_CITIES = [
    // USA
    { id: "new-york", name: "New York", country: "USA", state: "NY", population: "8.8M", industry: "Finance, Tech, Media" },
    { id: "los-angeles", name: "Los Angeles", country: "USA", state: "CA", population: "3.8M", industry: "Entertainment, Aerospace" },
    { id: "chicago", name: "Chicago", country: "USA", state: "IL", population: "2.7M", industry: "Finance, Logistics" },
    { id: "houston", name: "Houston", country: "USA", state: "TX", population: "2.3M", industry: "Energy, Healthcare" },
    { id: "phoenix", name: "Phoenix", country: "USA", state: "AZ", population: "1.6M", industry: "Electronics, Tourism" },
    { id: "philadelphia", name: "Philadelphia", country: "USA", state: "PA", population: "1.6M", industry: "Education, Biotech" },
    { id: "san-antonio", name: "San Antonio", country: "USA", state: "TX", population: "1.4M", industry: "Defense, Tourism" },
    { id: "san-diego", name: "San Diego", country: "USA", state: "CA", population: "1.3M", industry: "Biotech, Defense" },
    { id: "dallas", name: "Dallas", country: "USA", state: "TX", population: "1.3M", industry: "Telecom, Finance" },
    { id: "san-jose", name: "San Jose", country: "USA", state: "CA", population: "1M", industry: "Tech, AI" },
    { id: "austin", name: "Austin", country: "USA", state: "TX", population: "1M", industry: "Tech, Gaming" },
    { id: "jacksonville", name: "Jacksonville", country: "USA", state: "FL", population: "950k", industry: "Finance, Logistics" },
    { id: "fort-worth", name: "Fort Worth", country: "USA", state: "TX", population: "930k", industry: "Aviation, Logistics" },
    { id: "columbus", name: "Columbus", country: "USA", state: "OH", population: "900k", industry: "Insurance, Tech" },
    { id: "indianapolis", name: "Indianapolis", country: "USA", state: "IN", population: "880k", industry: "Pharma, Logistics" },
    { id: "charlotte", name: "Charlotte", country: "USA", state: "NC", population: "870k", industry: "Banking, Fintech" },
    { id: "san-francisco", name: "San Francisco", country: "USA", state: "CA", population: "815k", industry: "Tech, AI, VC" },
    { id: "seattle", name: "Seattle", country: "USA", state: "WA", population: "740k", industry: "Tech, E-commerce" },
    { id: "denver", name: "Denver", country: "USA", state: "CO", population: "715k", industry: "Energy, Tech" },
    { id: "washington-dc", name: "Washington DC", country: "USA", state: "DC", population: "690k", industry: "Government, Defense" },
    { id: "boston", name: "Boston", country: "USA", state: "MA", population: "675k", industry: "Education, Biotech" },
    { id: "el-paso", name: "El Paso", country: "USA", state: "TX", population: "670k", industry: "Trade, Defense" },
    { id: "nashville", name: "Nashville", country: "USA", state: "TN", population: "690k", industry: "Music, Healthcare" },
    { id: "detroit", name: "Detroit", country: "USA", state: "MI", population: "640k", industry: "Auto, Tech" },
    { id: "oklahoma-city", name: "Oklahoma City", country: "USA", state: "OK", population: "680k", industry: "Energy, Aero" },
    { id: "portland", name: "Portland", country: "USA", state: "OR", population: "650k", industry: "Tech, Outdoor" },
    { id: "las-vegas", name: "Las Vegas", country: "USA", state: "NV", population: "640k", industry: "Tourism, Tech" },
    { id: "memphis", name: "Memphis", country: "USA", state: "TN", population: "630k", industry: "Logistics, Trade" },
    { id: "louisville", name: "Louisville", country: "USA", state: "KY", population: "630k", industry: "Logistics, Healthcare" },
    { id: "baltimore", name: "Baltimore", country: "USA", state: "MD", population: "580k", industry: "Education, Logistics" },
    { id: "milwaukee", name: "Milwaukee", country: "USA", state: "WI", population: "570k", industry: "Manufacturing, Tech" },
    { id: "albuquerque", name: "Albuquerque", country: "USA", state: "NM", population: "560k", industry: "Defense, Energy" },
    { id: "tucson", name: "Tucson", country: "USA", state: "AZ", population: "540k", industry: "Defense, Tech" },
    { id: "fresno", name: "Fresno", country: "USA", state: "CA", population: "540k", industry: "Ag, Logistics" },
    { id: "sacramento", name: "Sacramento", country: "USA", state: "CA", population: "525k", industry: "Gov, Tech" },
    { id: "atlanta", name: "Atlanta", country: "USA", state: "GA", population: "500k", industry: "Fintech, Logistics" },
    { id: "kansas-city", name: "Kansas City", country: "USA", state: "MO", population: "500k", industry: "Logistics, Tech" },
    { id: "miami", name: "Miami", country: "USA", state: "FL", population: "450k", industry: "Finance, Tech" },
    { id: "raleigh", name: "Raleigh", country: "USA", state: "NC", population: "470k", industry: "Biotech, Tech" },
    { id: "minneapolis", name: "Minneapolis", country: "USA", state: "MN", population: "430k", industry: "Finance, Tech" },
    { id: "tampa", name: "Tampa", country: "USA", state: "FL", population: "390k", industry: "Finance, Healthcare" },
    { id: "st-louis", name: "St Louis", country: "USA", state: "MO", population: "300k", industry: "Finance, Tech" },
    { id: "pittsburgh", name: "Pittsburgh", country: "USA", state: "PA", population: "300k", industry: "AI, Healthcare" },
    { id: "cincinnati", name: "Cincinnati", country: "USA", state: "OH", population: "310k", industry: "Media, Trade" },
    { id: "salt-lake-city", name: "Salt Lake City", country: "USA", state: "UT", population: "200k", industry: "Tech, Finance" },
    { id: "boulder", name: "Boulder", country: "USA", state: "CO", population: "108k", industry: "Tech, Climate" },
    { id: "palo-alto", name: "Palo Alto", country: "USA", state: "CA", population: "65k", industry: "Tech, VC" },
    { id: "cambridge", name: "Cambridge", country: "USA", state: "MA", population: "120k", industry: "Education, AI" },

    // International
    { id: "london", name: "London", country: "UK", state: "ENG", population: "9M", industry: "Finance, Tech" },
    { id: "manchester", name: "Manchester", country: "UK", state: "ENG", population: "550k", industry: "Media, Tech" },
    { id: "birmingham", name: "Birmingham", country: "UK", state: "ENG", population: "1.1M", industry: "Finance, Trade" },
    { id: "berlin", name: "Berlin", country: "Germany", state: "BE", population: "3.7M", industry: "Startups, Tech" },
    { id: "hamburg", name: "Hamburg", country: "Germany", state: "HH", population: "1.8M", industry: "Logistics, Media" },
    { id: "munich", name: "Munich", country: "Germany", state: "BY", population: "1.5M", industry: "Auto, Tech" },
    { id: "paris", name: "Paris", country: "France", state: "IDF", population: "2.1M", industry: "Luxury, Tech" },
    { id: "lyon", name: "Lyon", country: "France", state: "ARA", population: "520k", industry: "Pharma, Tech" },
    { id: "toronto", name: "Toronto", country: "Canada", state: "ON", population: "2.9M", industry: "Tech, Finance" },
    { id: "vancouver", name: "Vancouver", country: "Canada", state: "BC", population: "675k", industry: "SaaS, Tech" },
    { id: "montreal", name: "Montreal", country: "Canada", state: "QC", population: "1.8M", industry: "AI, Gaming" },
    { id: "sydney", name: "Sydney", country: "Australia", state: "NSW", population: "5.3M", industry: "Finance, Tech" },
    { id: "melbourne", name: "Melbourne", country: "Australia", state: "VIC", population: "5M", industry: "Design, Tech" },
    { id: "singapore", name: "Singapore", country: "Singapore", state: "SG", population: "5.6M", industry: "Fintech, Logistics" },
    { id: "tokyo", name: "Tokyo", country: "Japan", state: "TYO", population: "14M", industry: "Tech, Finance" },
    { id: "dublin", name: "Dublin", country: "Ireland", state: "LE", population: "545k", industry: "Tech, Finance" },
    { id: "amsterdam", name: "Amsterdam", country: "Netherlands", state: "NH", population: "870k", industry: "SaaS, Fintech" },
    { id: "stockholm", name: "Stockholm", country: "Sweden", state: "AB", population: "975k", industry: "Gaming, Tech" },
    { id: "tel-aviv", name: "Tel Aviv", country: "Israel", state: "TA", population: "460k", industry: "Cyber, Tech" },
    { id: "bangalore", name: "Bangalore", country: "India", state: "KA", population: "8.4M", industry: "Tech, Software" },
    { id: "madrid", name: "Madrid", country: "Spain", state: "MD", population: "3.3M", industry: "Finance, Tech" },
    { id: "oslo", name: "Oslo", country: "Norway", state: "OS", population: "700k", industry: "Energy, Tech" },
];

function main() {
    console.log(`Generating data for ${MAJOR_CITIES.length} cities...`);
    fs.writeFileSync(LOCATIONS_FILE, JSON.stringify(MAJOR_CITIES, null, 2));
    console.log(`✅ Success! Metadata saved to ${LOCATIONS_FILE}`);
}

main();
