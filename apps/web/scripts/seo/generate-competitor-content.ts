
/**
 * generate-competitor-content.ts
 * 
 * Uses OpenRouter (LLM) to research and generate structured data for new competitors.
 * Appends the result to src/data/competitors.json.
 * 
 * Usage:
 *   npx tsx scripts/seo/generate-competitor-content.ts "CompetitorName"
 *   npx tsx scripts/seo/generate-competitor-content.ts "CompetitorName" --url "https://competitor.com"
 *   npx tsx scripts/seo/generate-competitor-content.ts "CompetitorName" --model "openai/gpt-4o-mini"
 * 
 * Environment variables:
 *   LLM_API_KEY - OpenRouter API Key
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const COMPETITORS_FILE = path.resolve(__dirname, '../../src/data/competitors.json');

// API key from environment only — never hardcode secrets
const DEFAULT_KEY = process.env.LLM_API_KEY || "";

// Paid models with excellent quality and low cost
const PAID_MODELS = [
  'openai/gpt-4o-mini',
  'anthropic/claude-3-haiku',
];

const BACKUP_MODELS: string[] = [
  'meta-llama/llama-3.3-70b-instruct',
];

interface Competitor {
  slug: string;
  name: string;
  domain: string;
  tagline: string;
  tags: string[];
  pricing: {
    freeTrial: boolean;
    freemium: boolean;
    startingPrice: number | "Custom";
    currency: string;
  };
  features: {
    autoApply: boolean;
    resumeBuilder: boolean;
    coverLetterGen: boolean;
    networking: boolean;
    jobTracking: boolean;
    extension: boolean;
    emailFinder: boolean;
    interviewPrep: boolean;
    salaryInsights: boolean;
  };
  weaknesses: string[];
  strengths: string[];
  seoKeywords: string[];
  differentiators: string[];
  verdict: string;
  rating_vs_jobhuntin: {
    speed: number[];
    quality: number[];
    automation: number[];
    stealth: number[];
    price_value: number[];
  };
}

async function generateCompetitorData(name: string, url?: string, explicitModel?: string): Promise<Competitor> {
  const apiKey = process.env.LLM_API_KEY || DEFAULT_KEY;

  if (!apiKey) {
    throw new Error('LLM_API_KEY environment variable is missing.');
  }

  const prompt = `Research "${name}"${url ? ` (${url})` : ''}. Return JSON:
{"slug":"kebab-case","name":"Official","domain":"example.com","tagline":"<10 words","tags":["Auto-Apply","Resume"],"pricing":{"freeTrial":false,"freemium":false,"startingPrice":0,"currency":"USD"},"features":{"autoApply":false,"resumeBuilder":false,"coverLetterGen":false,"networking":false,"jobTracking":false,"extension":false,"emailFinder":false,"interviewPrep":false,"salaryInsights":false},"weaknesses":["3 cons"],"strengths":["3 pros"],"seoKeywords":["5 keywords"],"differentiators":["3 USPs"],"verdict":"2 sentences","rating_vs_jobhuntin":{"speed":[5,9],"quality":[5,9],"automation":[5,9],"stealth":[5,9],"price_value":[5,9]}}
Be objective. Highlight gaps vs JobHuntin AI.`;

  const modelsToTry = explicitModel ? [explicitModel] : PAID_MODELS;
  let lastError: Error | null = null;
  let triedModels: string[] = [];

  for (let modelIdx = 0; modelIdx < modelsToTry.length; modelIdx++) {
    const model = modelsToTry[modelIdx];
    
    // Retry logic for rate limits (up to 2 retries per model)
    for (let retry = 0; retry < 2; retry++) {
      try {
        if (retry > 0) {
          const delayMs = 5000 * retry; // 5s, then 10s
          console.log("⏳ Rate limited, waiting", delayMs / 1000, "s before retry...");
          await new Promise(r => setTimeout(r, delayMs));
        }
        
        console.log("🤖 Attempting research with model:", model, "...");
        if (triedModels[triedModels.length - 1] !== model) {
          triedModels.push(model);
        }

        // Add timeout handling
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000);

        const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`,
            'HTTP-Referer': 'https://jobhuntin.com',
            'X-Title': 'JobHuntin SEO Bot',
          },
          body: JSON.stringify({
            model: model,
            messages: [{ role: 'user', content: prompt }],
            temperature: 0.7,
          }),
          signal: controller.signal,
        });

        clearTimeout(timeoutId);
        
        if (!response.ok) {
          const errText = await response.text();
          // For rate limits, retry
          if (response.status === 429) {
            lastError = new Error(`Model ${model} rate limited: ${errText}`);
            console.warn(`⚠️  Rate limited, will retry...`);
            continue; // Retry this model
          }
          // For 404/400, try next model
          if (response.status === 404 || response.status === 400) {
            const msg = `Model ${model} not found: ${errText}`;
            console.warn("⚠️ ", msg);
            lastError = new Error(msg);
            break; // Exit retry loop, go to next model
          }
          throw new Error(`OpenRouter API Error: ${response.status} - ${errText}`);
        }

        const data = await response.json();
        if (data.error) {
          console.warn("⚠️  Model", model, "returned error:", JSON.stringify(data.error));
          lastError = new Error(JSON.stringify(data.error));
          break; // Exit retry loop
        }

        const content = data.choices[0].message?.content;
        if (!content) {
          console.warn("⚠️  Model", model, "returned empty content.");
          break; // Exit retry loop
        }

        // Success! Parse JSON
        let cleanJson = content.replace(/```json\n?|```/g, '').trim();
        const firstBrace = cleanJson.indexOf('{');
        const lastBrace = cleanJson.lastIndexOf('}');
        if (firstBrace > -1 && lastBrace > -1) {
          cleanJson = cleanJson.substring(firstBrace, lastBrace + 1);
        }

        try {
          return JSON.parse(cleanJson);
        } catch (e) {
          console.error('Failed to parse LLM response for model', model);
          break; // Exit retry loop
        }
      } catch (e: any) {
        lastError = e;
        if (e.name === 'AbortError') {
          console.warn("⚠️  Model", model, "timed out");
        } else {
          console.warn("⚠️  Error with model", model, ":", e.message);
        }
        break; // Exit retry loop
      }
    }
  }

  throw new Error(
    `All models failed.\nLast error: ${lastError?.message}\n` +
    `Tried: ${triedModels.join(', ')}\n` +
    `Check working free models at: https://openrouter.ai/models?q=free\n` +
    `Usage: npx tsx scripts/seo/generate-competitor-content.ts "Name" --model "your/model:free"`
  );
}

async function main() {
  const name = process.argv[2];
  const args = process.argv.slice(3);

  let url: string | undefined;
  let model: string | undefined;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--url' && args[i + 1]) {
      url = args[i + 1];
      i++;
    } else if (args[i] === '--model' && args[i + 1]) {
      model = args[i + 1];
      i++;
    }
  }

  if (!name) {
    console.error('Usage: npx tsx scripts/seo/generate-competitor-content.ts "Competitor Name" [--url "https://..."] [--model "provider/model"]');
    process.exit(1);
  }

  // Load existing data
  let competitors: Competitor[] = [];
  if (fs.existsSync(COMPETITORS_FILE)) {
    competitors = JSON.parse(fs.readFileSync(COMPETITORS_FILE, 'utf-8'));
  }

  // Check properly
  if (competitors.find(c => c.name.toLowerCase() === name.toLowerCase())) {
    console.log("⚠️  Competitor", name, "already exists. Skipping.");
    return;
  }

  try {
    const newCompetitor = await generateCompetitorData(name, url, model);

    // Safety check for slug collision
    if (competitors.find(c => c.slug === newCompetitor.slug)) {
      newCompetitor.slug = `${newCompetitor.slug}-${Date.now()}`;
    }

    competitors.push(newCompetitor);

    // Sort alphabetically
    competitors.sort((a, b) => a.name.localeCompare(b.name));

    fs.writeFileSync(COMPETITORS_FILE, JSON.stringify(competitors, null, 2));
    console.log("✅ Added", newCompetitor.name, "to data/competitors.json");
    console.log("   Slug:", newCompetitor.slug);
    console.log("   Verdict:", newCompetitor.verdict);

  } catch (error: any) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

main();
