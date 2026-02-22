
import Parser from 'rss-parser';
import { Pool } from 'pg';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Initialize RSS Parser
const parser = new Parser();

// Database Pool - Uses the same DATABASE_URL as the main app (Render/Supabase)
// nosemgrep: problem-based-packs.insecure-transport.js-node.bypass-tls-verification - Render PostgreSQL may require this
const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: process.env.DATABASE_URL ? { rejectUnauthorized: false } : undefined
});

// Cities to monitor (could be loaded from locations.json)
const LOCATIONS_FILE = path.resolve(__dirname, '../../src/data/locations.json');
let monitoredCities: string[] = ['Austin', 'New York', 'San Francisco', 'Seattle', 'Chicago'];

try {
    if (fs.existsSync(LOCATIONS_FILE)) {
        const locations = JSON.parse(fs.readFileSync(LOCATIONS_FILE, 'utf-8'));
        // Take top 5 major cities for now to avoid hitting rate limits
        monitoredCities = locations
            .filter((l: any) => l.population > 500000)
            .slice(0, 5)
            .map((l: any) => l.name);
    }
} catch (e) {
    console.warn('⚠️ Could not load locations.json, using defaults.');
}

const SEARCH_QUERIES = [
    'Hiring',
    'Layoffs',
    'New Headquarters',
    'Tech Hub',
    'Business Expansion'
];

interface NewsTrigger {
    city: string;
    headline: string;
    source: string;
    url: string;
    summary: string;
    publishedAt: string;
    topic: string;
}

/**
 * Polls Google News for a specific query
 */
async function fetchNewsForCity(city: string, topic: string): Promise<NewsTrigger[]> {
    const query = `${topic} ${city}`;
    const encodedQuery = encodeURIComponent(query);
    const feedUrl = `https://news.google.com/rss/search?q=${encodedQuery}&hl=en-US&gl=US&ceid=US:en`;

    try {
        const feed = await parser.parseURL(feedUrl);
        const recentItems = feed.items.slice(0, 3); // Top 3 stories

        return recentItems.map(item => ({
            city,
            headline: item.title || 'Unknown Title',
            source: item.contentSnippet || item.content || '', // Google RSS puts snippet in content
            url: item.link || '',
            summary: item.contentSnippet || '',
            publishedAt: item.pubDate || new Date().toISOString(),
            topic
        }));
    } catch (error) {
        console.warn("⚠️ Failed to fetch news for", city, ":", error);
        return [];
    }
}

/**
 * Saves relevant news triggers to the database
 */
async function saveTrigger(trigger: NewsTrigger) {
    // Console log independently of DB success
    console.log("📰 TRIGGER FOUND:", trigger.city, trigger.headline);
    console.log("   URL:", trigger.url);

    if (!process.env.DATABASE_URL) {
        console.log('   (Skipping DB save: DATABASE_URL not set)');
        return;
    }

    const client = await pool.connect();
    try {
        // Insert trigger
        await client.query(`
      INSERT INTO seo_news_triggers (city, headline, url, summary, topic, published_at)
      VALUES ($1, $2, $3, $4, $5, $6)
      ON CONFLICT (url) DO NOTHING
    `, [trigger.city, trigger.headline, trigger.url, trigger.summary, trigger.topic, trigger.publishedAt]);

        console.log(`   ✅ Saved to database`);
    } catch (error) {
        console.warn(`   ⚠️  DB Save Failed (Authentication/Connection error). Continuing...`);
    } finally {
        client.release();
    }
}

async function main() {
    console.log("🌍 Starting Global News Monitor for", monitoredCities.length, "cities...");

    // Initialize DB table once
    if (process.env.DATABASE_URL) {
        const client = await pool.connect();
        try {
            await client.query(`
              CREATE TABLE IF NOT EXISTS seo_news_triggers (
                id SERIAL PRIMARY KEY,
                city VARCHAR(255),
                headline TEXT,
                url TEXT UNIQUE,
                summary TEXT,
                topic VARCHAR(100),
                published_at TIMESTAMP,
                processed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
              );
            `);
        } catch (e) {
            console.warn('⚠️ Table creation failed:', e);
        } finally {
            client.release();
        }
    }

    for (const city of monitoredCities) {
        for (const query of SEARCH_QUERIES) {
            console.log("🔍 Scanning:", query, "in", city, "...");
            const news = await fetchNewsForCity(city, query);

            for (const item of news) {
                // Simple filter: ensure it's actually recent (last 24h)
                const pubDate = new Date(item.publishedAt);
                const yesterday = new Date();
                yesterday.setDate(yesterday.getDate() - 1);

                if (!isNaN(pubDate.getTime()) && pubDate > yesterday) {
                    await saveTrigger(item);
                }
            }

            // Be nice to Google
            await new Promise(r => setTimeout(r, 1000));
        }
    }

    console.log('🏁 News Scan Complete.');
    process.exit(0);
}

main().catch(console.error);
