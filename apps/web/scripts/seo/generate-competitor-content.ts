
/**
 * generate-competitor-content.ts
 * 
 * Uses OpenRouter (LLM) to research and generate structured data for new competitors.
 * Appends the result to src/data/competitors.json.
 * 
 * Usage:
 *   npx tsx scripts/seo/generate-competitor-content.ts "CompetitorName"
 *   npx tsx scripts/seo/generate-competitor-content.ts "CompetitorName" --url "https://competitor.com"
 * 
 * Environment variables:
 *   LLM_API_KEY - OpenRouter API Key
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const COMPETITORS_FILE = path.resolve(__dirname, '../../src/data/competitors.json');

// Default key provided by user (should ideally be in .env)
const DEFAULT_KEY = "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";

// List of free models to try in order
const FREE_MODELS = [
  'google/gemini-2.0-flash-lite-preview-02-05:free',
  'meta-llama/llama-3-8b-instruct:free',
  'microsoft/phi-3-medium-128k-instruct:free',
  'huggingfaceh4/zephyr-7b-beta:free',
  'openchat/openchat-7b:free'
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
  ratings: {
    features: number;
    value: number;
    easeOfUse: number;
    support: number;
    overall: number;
  };
}

async function generateCompetitorData(name: string, url?: string): Promise<Competitor> {
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
      ratings: { // 1-5 float ratings
        features: number;
        value: number;
        easeOfUse: number;
        support: number;
        overall: number;
      };
    }

    Return ONLY the raw JSON object. No markdown, no comments.
    Ensure "slug" is unique and URL-friendly.
    Be objective but highlight where it lacks compared to a comprehensive AI agent like JobHuntin.
  `;

  let lastError: Error | null = null;

  for (const model of FREE_MODELS) {
    try {
      console.log(`🤖 Attempting research with model: ${model}...`);

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
      });

      if (!response.ok) {
        const errText = await response.text();
        // If 404 (model not found/unavailable), try next
        if (response.status === 404 || response.status === 429) { // 429 rate limit also try next? usually standard, but let's try
          console.warn(`⚠️  Model ${model} failed: ${response.status} - ${errText}`);
          continue;
        }
        throw new Error(`OpenRouter API Error: ${response.status} - ${errText}`);
      }

      const data = await response.json();
      // Check for error inside 200 OK (OpenRouter sometimes does this for some upstream errors)
      if (data.error) {
        console.warn(`⚠️  Model ${model} returned error: ${JSON.stringify(data.error)}`);
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

  throw new Error(`All free models failed. Last error: ${lastError?.message}`);
}

async function main() {
  const name = process.argv[2];
  const urlArgIndex = process.argv.indexOf('--url');
  const url = urlArgIndex > -1 ? process.argv[urlArgIndex + 1] : undefined;

  if (!name) {
    console.error('Usage: npx tsx scripts/seo/generate-competitor-content.ts "Competitor Name" [--url "https://..."]');
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
    const newCompetitor = await generateCompetitorData(name, url);

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
