import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import 'dotenv/config'; // Ensure env vars are loaded

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITEMAP_PATH = path.resolve(__dirname, '../../public/sitemap.xml');
const REPORT_FILE = path.resolve(__dirname, '../../src/data/seo-audit-report.json');

const OPENROUTER_API_KEY = process.env.LLM_API_KEY;
const MODEL = 'openrouter/free';

if (!OPENROUTER_API_KEY) {
    console.error('❌ Error: LLM_API_KEY environment variable is not set.');
    process.exit(1);
}

interface AuditResult {
    url: string;
    seoScore: number;
    isSpam: boolean;
    spamReason?: string;
    improvements: string[];
    timestamp: string;
}

// Helper to parse sitemap
function getUrlsFromSitemap(): string[] {
    if (!fs.existsSync(SITEMAP_PATH)) {
        throw new Error(`Sitemap not found at ${SITEMAP_PATH}`);
    }
    const sitemapContent = fs.readFileSync(SITEMAP_PATH, 'utf-8');
    const urls = sitemapContent.match(/<loc>(.*?)<\/loc>/g)?.map(val => val.replace(/<\/?loc>/g, '')) || [];
    return urls;
}

// Helper to fetch page context (simplified)
async function fetchPageContent(url: string): Promise<string> {
    try {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`Status ${res.status}`);
        const html = await res.text();
        // Simple verification - just grab head and first 2000 chars of body to save tokens/time
        // or use a smarter extraction if needed. For "deep audit", we might want more.
        // Let's try to get the whole thing but truncate if huge.
        return html.substring(0, 50000); // 50k chars limit
    } catch (e: any) {
        return `Error fetching content: ${e.message}`;
    }
}

async function auditUrl(url: string): Promise<AuditResult> {
    const htmlContent = await fetchPageContent(url);

    const prompt = `
    You are an expert SEO auditor and Spam Detector.
    Analyze the following HTML content for the URL: ${url}

    Task 1: Calculate an SEO Score (0-100). 
    - 100 means perfect technical SEO, great content, proper meta tags, etc.
    - Penalize for missing title, description, h1, or thin content.

    Task 2: Detect Spam.
    - Look for keyword stuffing, hidden text, gibberish, or malicious patterns.
    - Answer "true" if it looks like spam, "false" otherwise.

    Task 3: List 3 key improvements to reach 100/100.

    HTML Content (truncated):
    ${htmlContent.substring(0, 15000)}

    Return a JSON object ONLY:
    {
      "seoScore": 85,
      "isSpam": false,
      "spamReason": null, // or string explanation
      "improvements": ["Fix missing meta description", "Add alt tags", "Increase content length"]
    }
  `;

    try {
        const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
                'HTTP-Referer': 'https://jobhuntin.com',
                'X-Title': 'JobHuntin SEO Audit',
            },
            body: JSON.stringify({
                model: MODEL,
                messages: [{ role: 'user', content: prompt }],
                temperature: 0.1, // Low temp for consistent analysis
                response_format: { type: 'json_object' }
            }),
        });

        if (!response.ok) {
            throw new Error(`OpenRouter error: ${response.statusText}`);
        }

        const data = await response.json();
        const content = data.choices[0]?.message?.content;

        if (!content) throw new Error('No content from LLM');

        // Parse JSON
        let result;
        try {
            result = JSON.parse(content);
        } catch (e) {
            // Fallback cleanup if markdown is included
            const clean = content.replace(/```json|```/g, '').trim();
            result = JSON.parse(clean);
        }

        return {
            url,
            seoScore: result.seoScore || 0,
            isSpam: result.isSpam || false,
            spamReason: result.spamReason,
            improvements: result.improvements || [],
            timestamp: new Date().toISOString()
        };

    } catch (error: any) {
        console.error(`❌ Analysis failed for ${url}:`, error.message);
        return {
            url,
            seoScore: 0,
            isSpam: false,
            spamReason: "Analysis failed",
            improvements: ["Retry analysis"],
            timestamp: new Date().toISOString()
        };
    }
}

async function main() {
    const urls = getUrlsFromSitemap();
    console.log(`🔍 Found ${urls.length} URLs in sitemap.`);

    // CLI args for limit
    const args = process.argv.slice(2);
    const limitIdx = args.indexOf('--limit');
    let limit = limitIdx !== -1 ? parseInt(args[limitIdx + 1]) : urls.length;

    console.log(`🚀 Starting audit for ${limit} URLs using ${MODEL}...`);

    const results: AuditResult[] = [];
    const BATCH_SIZE = 3; // Small batch to be safe with free tier

    // Process in batches
    for (let i = 0; i < limit; i += BATCH_SIZE) {
        const batch = urls.slice(i, i + BATCH_SIZE);
        if (batch.length === 0) break;

        console.log(`Processing batch ${i + 1}-${Math.min(i + BATCH_SIZE, limit)}...`);

        const promises = batch.map(url => auditUrl(url));
        const batchResults = await Promise.all(promises);
        results.push(...batchResults);

        // Small delay between batches
        if (i + BATCH_SIZE < limit) {
            await new Promise(r => setTimeout(r, 2000));
        }
    }

    // Save report
    // Load existing if we want to append? For now, overwrite or simple save.
    // Use a pretty print
    fs.writeFileSync(REPORT_FILE, JSON.stringify(results, null, 2));

    console.log(`\n✅ Audit Complete!`);
    console.log(`📄 Report saved to: ${REPORT_FILE}`);

    // Summary
    const avgScore = results.reduce((acc, r) => acc + r.seoScore, 0) / results.length;
    const spamCount = results.filter(r => r.isSpam).length;

    console.log(`📊 Summary:`);
    console.log(`   - URLs Audited: ${results.length}`);
    console.log(`   - Average SEO Score: ${avgScore.toFixed(1)}/100`);
    console.log(`   - Spam Flags: ${spamCount}`);
    if (spamCount > 0) {
        console.log(`   ⚠️  SPAM DETECTED in:`);
        results.filter(r => r.isSpam).forEach(r => console.log(`      - ${r.url} (${r.spamReason})`));
    }
}

main();
