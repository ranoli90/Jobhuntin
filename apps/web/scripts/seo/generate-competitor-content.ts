
/**
 * generate-competitor-content.ts
 * 
 * Uses OpenRouter (LLM) to research and generate structured data for new competitors.
 * Appends the result to src/data/competitors.json.
 * 
 * Usage:
 *   npx tsx scripts/seo/generate-competitor-content.ts "CompetitorName"
 *   npx tsx scripts/seo/generate-competitor-content.ts "CompetitorName" --url "https://competitor.com"
 *   npx tsx scripts/seo/generate-competitor-content.ts "CompetitorName" --model "google/gemini-2.0-flash-lite-preview-02-05:free"
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

// Free models that actually work on OpenRouter (updated Feb 2026)
const FREE_MODELS = [
  'google/gemini-2.0-flash-exp:free',
  'meta-llama/llama-3.3-8b-instruct:free',
  'qwen/qwen3-4b:free',
  'mistralai/mistral-small-3.1-24b-instruct:free',
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

  const prompt = `
    Research the job search tool "${name}"${url ? ` (${url})` : ''}.
    Generate a JSON object matching this TypeScript interface:

    interface Competitor {
      slug: string; // kebab-case, e.g. "lazyapply"
      name: string; // Official name
      domain: string; // e.g. "lazyapply.com"
      tagline: string; // Short marketing tagline (max 10 words)
      tags: string[]; // 3-4 categories, e.g. "Auto-Apply", "Resume Builder"
      pricing: {
        freeTrial: boolean;
        freemium: boolean;
        startingPrice: number | "Custom"; // Monthly price in USD, or "Custom" string
        currency: "USD";
      };
      features: { // boolean flags
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
      weaknesses: string[]; // 3 major cons/limitations vs JobHuntin
      strengths: string[]; // 3 major pros
      seoKeywords: string[]; // 5-8 high-intent keywords
      differentiators: string[]; // 3 unique selling points
      verdict: string; // 2-3 sentences summarizing who it's for vs JobHuntin
      rating_vs_jobhuntin: { // ratings [competitor_score, jobhuntin_score] (1-10)
        speed: number[];
        quality: number[];
        automation: number[];
        stealth: number[];
        price_value: number[];
      };
    }

    Return ONLY the raw JSON object. No markdown, no comments.
    Ensure "slug" is unique and URL-friendly.
    Be objective but highlight where it lacks compared to a comprehensive AI agent like JobHuntin.
  `;

  const modelsToTry = explicitModel ? [explicitModel] : FREE_MODELS;
  let lastError: Error | null = null;
  let triedModels: string[] = [];

  for (const model of modelsToTry) {
    try {
      console.log(`🤖 Attempting research with model: ${model}...`);
      triedModels.push(model);

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
        // If 404 (model not found/unavailable) or 400 (bad params/model id), try next
        if (response.status === 404 || response.status === 400 || response.status === 429) {
          const msg = `Model ${model} failed: ${response.status} - ${errText}`;
          console.warn(`⚠️  ${msg}`);
          lastError = new Error(msg);
          continue;
        }
        throw new Error(`OpenRouter API Error: ${response.status} - ${errText}`);
      }

      const data = await response.json();
      if (data.error) {
        console.warn(`⚠️  Model ${model} returned error: ${JSON.stringify(data.error)}`);
        lastError = new Error(JSON.stringify(data.error));
        continue;
      }

      const content = data.choices[0].message?.content;
      if (!content) {
        console.warn(`⚠️  Model ${model} returned empty content.`);
        continue;
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
        continue;
      }

    } catch (e: any) {
      lastError = e;
      console.warn(`⚠️  Error with model ${model}: ${e.message}`);
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
    console.log(`⚠️  Competitor "${name}" already exists. Skipping.`);
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
    console.log(`✅ Added "${newCompetitor.name}" to data/competitors.json`);
    console.log(`   Slug: ${newCompetitor.slug}`);
    console.log(`   Verdict: ${newCompetitor.verdict}`);

  } catch (error: any) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

main();
