
import { chromium } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const COMPETITORS_FILE = path.resolve(__dirname, '../../src/data/competitors.json');

async function scrapeCompetitor(browser: any, competitor: any) {
    const page = await browser.newPage();
    const targetUrl = competitor.domain.startsWith('http') ? competitor.domain : `https://${competitor.domain}`;
    console.log("🔍 Checking", competitor.name, "(" + targetUrl + ")...");

    try {
        // Try homepage first, then pricing
        await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });

        // Simple heuristic: search for dollar signs or "per month"
        const bodyText = await page.innerText('body');
        const priceMatches = bodyText.match(/\$\d+(\.\d{2})?/g);

        if (priceMatches) {
            const lowestPrice = Math.min(...priceMatches.map((m: string) => parseFloat(m.replace(/\$/g, ''))));
            console.log("   Found potential prices:", priceMatches.slice(0, 3).join(", "), "(Lowest: $" + lowestPrice + ")");

            // Check if it differs significantly from competitors.json
            const currentStartsAt = competitor.pricing?.starts_at || "0";
            const currentPrice = parseFloat(currentStartsAt.replace(/[^0-9.]/g, '')) || 0;
            if (lowestPrice > 0 && Math.abs(lowestPrice - currentPrice) > 1) {
                console.log("   ⚠️ Price change detected! Old:", currentStartsAt, ", New: ~$" + lowestPrice);
                return { ...competitor, pricing: { ...competitor.pricing, starts_at: `$${lowestPrice}/mo` }, updatedAt: new Date().toISOString() };
            }
        }
    } catch (e: any) {
        console.warn("   ❌ Failed to scrape", competitor.name, ":", e.message);
    } finally {
        await page.close();
    }
    return null;
}

async function main() {
    if (!fs.existsSync(COMPETITORS_FILE)) {
        console.error('Competitor data not found.');
        return;
    }

    const competitors = JSON.parse(fs.readFileSync(COMPETITORS_FILE, 'utf8'));
    const browser = await chromium.launch();
    const updates = [];
    let changedCount = 0;

    // Limit to first 5 for testing/demonstration to avoid long execution
    const activeCompetitors = process.argv.includes('--all') ? competitors : competitors.slice(0, 5);

    console.log("🚀 Starting competitive intelligence scrape for", activeCompetitors.length, "brands...");

    for (const competitor of activeCompetitors) {
        const updated = await scrapeCompetitor(browser, competitor);
        if (updated) {
            updates.push(updated);
            changedCount++;
        } else {
            updates.push(competitor);
        }
    }

    // Merge updates back if needed
    if (changedCount > 0 && process.argv.includes('--write')) {
        const fullCompetitors = competitors.map((c: any) => {
            const up = updates.find(u => u.slug === c.slug);
            return up || c;
        });
        fs.writeFileSync(COMPETITORS_FILE, JSON.stringify(fullCompetitors, null, 2));
        console.log("\n✅ Intelligence capture complete. Updated", changedCount, "competitors.");
    } else {
        console.log("\n🏁 Sweep complete.", changedCount, "potential updates found. (Run with --write to save)");
    }

    await browser.close();
}

main().catch(console.error);
