/**
 * generate-aggressive-competitor-content.ts
 * 
 * Enhanced version with aggressive SEO optimization using OpenRouter LLM
 * Generates competitor comparison content with advanced SEO techniques
 * 
 * Usage:
 *   npx tsx scripts/seo/generate-aggressive-competitor-content.ts "CompetitorName"
 *   npx tsx scripts/seo/generate-aggressive-competitor-content.ts "CompetitorName" --aggressive
 *   npx tsx scripts/seo/generate-aggressive-competitor-content.ts "CompetitorName" --url "https://competitor.com"
 * 
 * Environment variables:
 *   LLM_API_KEY - OpenRouter API Key
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const COMPETITORS_FILE = path.resolve(__dirname, '../../src/data/competitors.json');

// Enhanced API key with fallback
const DEFAULT_KEY = "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";

// Premium models for aggressive SEO content
const PREMIUM_MODELS = [
  'nvidia/nemotron-3-nano-30b-a3b:free', // Using robust free model as "premium" substitute per user request
  'anthropic/claude-3-sonnet:beta',
  'openai/gpt-4-turbo-preview',
  'google/gemini-pro',
  'anthropic/claude-3-haiku:beta'
];

// Fallback free models
const FREE_MODELS = [
  'nvidia/nemotron-3-nano-30b-a3b:free',
  'nvidia/nemotron-nano-12b-v2-vl:free',
  'nvidia/nemotron-nano-9b-v2:free',
  'openrouter/aurora-alpha',
  'google/gemini-2.0-flash-lite-preview-02-05:free',
  'meta-llama/llama-3-8b-instruct:free',
  'mistralai/mistral-7b-instruct:free',
  'microsoft/phi-3-medium-128k-instruct:free'
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
  // New aggressive SEO fields
  seoTitle?: string;
  seoDescription?: string;
  h1?: string;
  h2s?: string[];
  contentSections?: ContentSection[];
  schema?: object[];
  semanticKeywords?: string[];
  lsiKeywords?: string[];
  entityMentions?: string[];
}

interface ContentSection {
  heading: string;
  content: string;
  keywords: string[];
  entities: string[];
}

/**
 * Generate aggressive SEO content using advanced LLM prompting
 */
async function generateAggressiveSEOContent(
  competitorName: string,
  url?: string,
  aggressive: boolean = false
): Promise<Competitor> {
  const apiKey = process.env.LLM_API_KEY || DEFAULT_KEY;

  if (!apiKey) {
    throw new Error('LLM_API_KEY environment variable is missing.');
  }

  const modelsToTry = aggressive ? [...PREMIUM_MODELS, ...FREE_MODELS] : FREE_MODELS;

  // Aggressive SEO prompt for maximum ranking potential
  const aggressivePrompt = `
    You are an expert SEO content strategist. Create the most aggressive, high-ranking competitor analysis for "${competitorName}" that will dominate search results.

    Generate a comprehensive JSON object with these requirements:

    1. **AGGRESSIVE SEO TITLE**: Create a title that will rank #1 for "${competitorName} vs JobHuntin" and related searches
    2. **MAXIMUM KEYWORD DENSITY**: Include 50+ high-intent keywords naturally
    3. **SEMANTIC KEYWORDS**: Add 20+ LSI (Latent Semantic Indexing) keywords
    4. **ENTITY OPTIMIZATION**: Include 15+ named entities Google recognizes
    5. **CONTENT SECTIONS**: Generate 8 detailed content sections with keyword-rich headings
    6. **SCHEMA MARKUP**: Provide comprehensive JSON-LD schema for Product, Review, FAQPage
    6. **SCHEMA MARKUP**: Provide comprehensive JSON-LD schema for Product, Review, FAQPage
    7. **COMPETITIVE ADVANTAGES**: Clearly position JobHuntin as the superior choice
    8. **RATINGS**: Rate vs JobHuntin on Speed, Quality, Automation, Stealth, Price. JobHuntin score should be 9 or 10. Format: [competitor_score, jobhuntin_score]

    Required JSON structure:

    {
      "slug": "kebab-case-competitor-name",
      "name": "${competitorName}",
      "domain": "competitor-domain.com",
      "tagline": "Compelling 8-word tagline with power words",
      "tags": ["Auto-Apply", "AI-Agent", "Job-Search"],
      "pricing": {
        "freeTrial": boolean,
        "freemium": boolean,
        "startingPrice": 29.99,
        "currency": "USD"
      },
      "features": {
        "autoApply": boolean,
        "resumeBuilder": boolean,
        "coverLetterGen": boolean,
        "networking": boolean,
        "jobTracking": boolean,
        "extension": boolean,
        "emailFinder": boolean,
        "interviewPrep": boolean,
        "salaryInsights": boolean
      },
      "weaknesses": [
        "Specific weakness that JobHuntin solves better",
        "Another major limitation vs JobHuntin",
        "Final critical disadvantage"
      ],
      "strengths": [
        "One genuine strength (be objective)",
        "Another positive aspect",
        "Final strength"
      ],
      "seoKeywords": [
        "${competitorName} vs JobHuntin",
        "${competitorName} alternative 2026",
        "is ${competitorName} worth it",
        "JobHuntin vs ${competitorName}",
        "${competitorName} pricing",
        "${competitorName} features",
        "${competitorName} review",
        "${competitorName} pros and cons",
        "best ${competitorName} alternative",
        "switch from ${competitorName} to JobHuntin"
      ],
      "differentiators": [
        "JobHuntin's unique advantage #1",
        "JobHuntin's superior feature #2", 
        "JobHuntin's game-changing benefit #3"
      ],
      "verdict": "2-3 sentences explaining why users should choose JobHuntin over ${competitorName}",
      "rating_vs_jobhuntin": {
        "speed": [6, 10],
        "quality": [7, 9],
        "automation": [4, 10],
        "stealth": [2, 10],
        "price_value": [8, 9]
      },
      "seoTitle": "${competitorName} vs JobHuntin (2026): #1 Comparison & Why JobHuntin Wins",
      "seoDescription": "Complete ${competitorName} vs JobHuntin comparison (2026). See pricing, features, success rates & why 10,000+ users switched. Updated daily with real user reviews.",
      "h1": "${competitorName} vs JobHuntin: The Ultimate Comparison (2026 Winner Revealed)",
      "h2s": [
        "Feature Comparison: ${competitorName} vs JobHuntin Side-by-Side",
        "Pricing Analysis: Which Tool Gives You More Value?",
        "User Success Rates: Real Numbers Compared",
        "Application Quality: AI vs Manual Submissions",
        "Speed Test: How Fast Can You Land Interviews?",
        "Customer Support: Response Times & Quality",
        "Hidden Costs: What ${competitorName} Doesn't Tell You",
        "Final Verdict: Why JobHuntin Dominates in 2026"
      ],
      "contentSections": [
        {
          "heading": "Why 10,000+ Users Switched from ${competitorName} to JobHuntin",
          "content": "Detailed analysis of migration patterns and user satisfaction improvements...",
          "keywords": ["${competitorName} alternative", "switch to JobHuntin", "user migration"],
          "entities": ["${competitorName}", "JobHuntin", "user satisfaction", "job search automation"]
        }
      ],
      "schema": [
        {
          "@context": "https://schema.org",
          "@type": "Product",
          "name": "${competitorName} vs JobHuntin Comparison",
          "description": "Comprehensive comparison between ${competitorName} and JobHuntin job search tools",
          "brand": {
            "@type": "Brand",
            "name": "JobHuntin"
          },
          "offers": {
            "@type": "Offer",
            "price": "19",
            "priceCurrency": "USD"
          }
        }
      ],
      "semanticKeywords": [
        "job search automation comparison",
        "AI job application tools 2026",
        "best job search software",
        "automated job application reviews"
      ],
      "lsiKeywords": [
        "career advancement technology",
        "employment search optimization",
        "professional job matching",
        "resume submission automation"
      ],
      "entityMentions": [
        "Artificial Intelligence",
        "Machine Learning",
        "Natural Language Processing",
        "Job Search Optimization",
        "Career Development",
        "Employment Technology"
      ]
    }

    Make this content extremely persuasive and SEO-optimized. Use power words, emotional triggers, and compelling statistics. Position JobHuntin as the clear winner while maintaining credibility.

    Return ONLY the raw JSON object. No markdown, no comments, no explanations.
  `;

  let lastError: Error | null = null;

  for (const model of modelsToTry) {
    try {
      console.log(`🤖 Generating aggressive SEO content with ${model}...`);

      const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`,
          'HTTP-Referer': 'https://jobhuntin.com',
          'X-Title': 'JobHuntin SEO Aggressive Bot',
        },
        body: JSON.stringify({
          model: model,
          messages: [{ role: 'user', content: aggressivePrompt }],
          temperature: 0.8,
          max_tokens: 4000,
        }),
      });

      if (!response.ok) {
        const errText = await response.text();
        if (response.status === 404 || response.status === 400 || response.status === 429) {
          console.warn(`⚠️  Model ${model} failed: ${response.status} - ${errText}`);
          lastError = new Error(errText);
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

      // Clean and parse JSON
      let cleanJson = content.replace(/```json\n?|```/g, '').trim();
      const firstBrace = cleanJson.indexOf('{');
      const lastBrace = cleanJson.lastIndexOf('}');

      if (firstBrace > -1 && lastBrace > -1) {
        cleanJson = cleanJson.substring(firstBrace, lastBrace + 1);
      }

      try {
        const result = JSON.parse(cleanJson);
        console.log(`✅ Successfully generated aggressive SEO content with ${model}`);
        return result;
      } catch (e) {
        console.error('Failed to parse JSON from model:', model);
        continue;
      }

    } catch (e: any) {
      lastError = e;
      console.warn(`⚠️  Error with model ${model}: ${e.message}`);
    }
  }

  throw new Error(
    `All models failed. Last error: ${lastError?.message}\n` +
    `Tried: ${modelsToTry.join(', ')}\n` +
    `Check OpenRouter status at: https://openrouter.ai/status`
  );
}

/**
 * Main execution function
 */
async function main() {
  const name = process.argv[2];
  const args = process.argv.slice(3);

  if (!name) {
    console.error('Usage: npx tsx scripts/seo/generate-aggressive-competitor-content.ts "Competitor Name" [--aggressive] [--url "https://..."]');
    process.exit(1);
  }

  const aggressive = args.includes('--aggressive');
  let url: string | undefined;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--url' && args[i + 1]) {
      url = args[i + 1];
      i++;
    }
  }

  console.log(`🚀 Starting aggressive SEO content generation for: ${name}`);
  if (aggressive) console.log('🔥 AGGRESSIVE MODE ACTIVATED - Using premium models');

  try {
    // Load existing data
    let competitors: Competitor[] = [];
    if (fs.existsSync(COMPETITORS_FILE)) {
      competitors = JSON.parse(fs.readFileSync(COMPETITORS_FILE, 'utf-8'));
    }

    // Check for duplicates
    if (competitors.find(c => c.name.toLowerCase() === name.toLowerCase())) {
      console.log(`⚠️  Competitor "${name}" already exists. Updating with aggressive SEO...`);

      // Update existing competitor with aggressive SEO
      const existingIndex = competitors.findIndex(c => c.name.toLowerCase() === name.toLowerCase());
      const updatedCompetitor = await generateAggressiveSEOContent(name, url, aggressive);

      // Merge with existing data to preserve important fields
      competitors[existingIndex] = {
        ...competitors[existingIndex],
        ...updatedCompetitor,
        name: competitors[existingIndex].name, // Preserve original name
        slug: competitors[existingIndex].slug, // Preserve original slug
      };
    } else {
      // Generate new competitor with aggressive SEO
      const newCompetitor = await generateAggressiveSEOContent(name, url, aggressive);

      // Check for slug collision
      if (competitors.find(c => c.slug === newCompetitor.slug)) {
        newCompetitor.slug = `${newCompetitor.slug}-${Date.now()}`;
      }

      competitors.push(newCompetitor);
    }

    // Sort alphabetically
    competitors.sort((a, b) => a.name.localeCompare(b.name));

    // Save updated data
    fs.writeFileSync(COMPETITORS_FILE, JSON.stringify(competitors, null, 2));

    console.log(`✅ Successfully updated competitor data with aggressive SEO`);
    console.log(`📊 Total competitors: ${competitors.length}`);

    if (aggressive) {
      console.log(`🔥 Aggressive SEO features added:`);
      console.log(`   - Enhanced title tags`);
      console.log(`   - Advanced schema markup`);
      console.log(`   - Semantic keyword optimization`);
      console.log(`   - Entity-based content`);
      console.log(`   - Comprehensive content sections`);
    }

  } catch (error: any) {
    console.error('❌ Error generating aggressive SEO content:', error.message);
    process.exit(1);
  }
}

main();