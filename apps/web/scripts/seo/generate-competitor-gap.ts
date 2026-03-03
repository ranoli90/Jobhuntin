/**
 * generate-competitor-gap.ts
 * 
 * Generates content targeting competitor weaknesses and content gaps
 * Uses competitive intelligence to create superior content
 */

import 'dotenv/config';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const MODEL = process.env.LLM_MODEL || 'openai/gpt-4o-mini';
const API_BASE = process.env.LLM_API_BASE || 'https://openrouter.ai/api/v1';
const API_KEY = process.env.LLM_API_KEY;

if (!API_KEY) {
  console.error('❌ LLM_API_KEY not set');
  process.exit(1);
}

// Competitor intelligence database
// ⚠️ IMPORTANT: All claims must be factual and verifiable
// ✅ DO: State observable facts (pricing from their website, features they list)
// ✅ DO: Compare feature sets objectively
// ❌ DO NOT: Make unsubstantiated negative claims
// ❌ DO NOT: Create fake reviews or testimonials
const COMPETITOR_INTEL: Record<string, any> = {
  'teal': {
    pricing: '$9-29/month (from tealhq.com)',
    features: ['Resume builder', 'Job tracker', 'LinkedIn optimization'],
    comparisonPoints: {
      jobhuntinAdvantage: ['AI-powered auto-apply', 'Multi-platform job aggregation', 'Real-time application tracking'],
      differentiator: 'JobHuntin focuses on complete automation vs Teal\'s manual tracking approach',
    },
  },
  'lazyapply': {
    pricing: '$99-249 one-time (from lazyapply.com)',
    features: ['Auto-apply', 'Resume upload', 'Basic tracking'],
    comparisonPoints: {
      jobhuntinAdvantage: ['AI resume tailoring for each job', 'Cover letter generation', 'Interview preparation tools', 'Lower total cost of ownership'],
      differentiator: 'JobHuntin provides AI-powered personalization vs LazyApply\'s template-based approach',
    },
  },
  'simplify': {
    pricing: 'Free - $9/month (from simplify.jobs)',
    features: ['Auto-fill applications', 'Job tracking', 'Chrome extension'],
    comparisonPoints: {
      jobhuntinAdvantage: ['Native mobile app', 'AI-powered resume optimization', 'Direct job board integrations beyond browser extension'],
      differentiator: 'JobHuntin offers full-platform automation vs Simplify\'s browser-only approach',
    },
  },
};

async function generateCompetitorGapContent(
  competitor: string,
  gapKeywords: string[]
): Promise<string> {
  const intel = COMPETITOR_INTEL[competitor.toLowerCase()] || {
    pricing: 'Contact for pricing',
    features: ['Job search tools', 'Application tracking'],
    comparisonPoints: {
      jobhuntinAdvantage: ['AI-powered automation', 'Comprehensive platform'],
      differentiator: 'JobHuntin focuses on complete AI automation vs manual processes',
    },
  };

  const prompt = `Create a comprehensive, factual comparison article comparing ${competitor} and JobHuntin.

COMPETITOR: ${competitor}
COMPETITOR PRICING: ${intel.pricing}
COMPETITOR FEATURES: ${intel.features.join(', ')}
JOBHUNTIN ADVANTAGES: ${intel.comparisonPoints.jobhuntinAdvantage.join(', ')}
KEY DIFFERENTIATOR: ${intel.comparisonPoints.differentiator}
CONTENT GAPS TO TARGET: ${gapKeywords.join(', ')}

⚠️ CRITICAL INSTRUCTIONS:
1. Be FACTUAL and OBJECTIVE - only state verifiable facts
2. NO fake reviews or testimonials - only reference real user experiences if cited
3. NO unsubstantiated negative claims about competitor
4. Focus on DIFFERENCES, not putting down the competitor
5. Let readers decide based on their needs

ARTICLE STRUCTURE:
1. H1: "${competitor} vs JobHuntin: Which is Right for You? (2026)"
2. Introduction: Brief overview of both tools, who this comparison is for
3. H2: "Quick Comparison Table"
   - Side-by-side: Features, Pricing, Best For
   - Be objective - show where each wins
4. H2: "What is ${competitor}?"
   - Brief description based on their website
   - Key features they offer
   - Who it's best for
5. H2: "What is JobHuntin?"
   - Brief description of our platform
   - Key features we offer
   - Who it's best for
6. H2: "Feature Comparison"
   - Detailed comparison of key features
   - Use table format
   - Highlight JobHuntin's AI automation focus
7. H2: "Pricing Comparison"
   - ${competitor}: ${intel.pricing}
   - JobHuntin pricing
   - Value analysis (features per dollar)
8. H2: "When to Choose ${competitor}"
   - Be honest about scenarios where they might be better
   - Builds trust and credibility
9. H2: "When to Choose JobHuntin"
   - Scenarios where our AI automation shines
   - Users who want complete job search automation
10. H2: "How to Get Started with JobHuntin"
    - Simple onboarding steps
    - Free trial information
    - Migration tips (if switching)
11. H2: FAQ
    - "Can I try both before deciding?"
    - "Do I need a credit card for the free trial?"
    - "Can I switch from ${competitor} to JobHuntin?"
12. Conclusion: Summarize key differences, encourage free trial

SEO REQUIREMENTS:
- Include semantic keywords naturally: ${gapKeywords.join(', ')}
- Target featured snippets with comparison tables
- Use comparison schema markup
- Include internal links: [LINK: features], [LINK: pricing], [LINK: free-trial]
- Word count: 2000-3000 words
- Tone: Professional, balanced, helpful - help readers make the right choice for THEM

OUTPUT: Return only the article content in Markdown format, starting with H1.`;

  console.log(`\n🎯 Generating competitor gap content: ${competitor}`);
  console.log(`   Targeting gaps: ${gapKeywords.join(', ')}`);

  const response = await fetch(`${API_BASE}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_KEY}`,
      'HTTP-Referer': 'https://jobhuntin.com',
    },
    body: JSON.stringify({
      model: MODEL,
      messages: [
        { role: 'system', content: 'You are an expert copywriter specializing in competitive comparison content.' },
        { role: 'user', content: prompt }
      ],
      temperature: 0.7,
      max_tokens: 4000,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`API error: ${response.status} - ${error}`);
  }

  const data = await response.json();
  return data.choices[0].message.content;
}

function createFilename(competitor: string): string {
  return `${competitor.toLowerCase()}-alternatives-2026.md`;
}

function saveContent(content: string, filename: string): string {
  const outputDir = path.resolve(__dirname, '../../content/comparisons');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  const filepath = path.join(outputDir, filename);
  fs.writeFileSync(filepath, content);
  return filepath;
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const competitor = args[0];
  const gapKeywordsStr = args[1];
  
  if (!competitor || !gapKeywordsStr) {
    console.error('Usage: tsx generate-competitor-gap.ts <competitor> <gap-keywords>');
    console.error('Example: tsx generate-competitor-gap.ts teal "teal alternative,teal vs jobhuntin"');
    process.exit(1);
  }
  
  const gapKeywords = gapKeywordsStr.split(',');
  
  try {
    console.log('='.repeat(70));
    console.log('🎯 COMPETITOR GAP CONTENT GENERATOR');
    console.log('='.repeat(70));
    
    const start = Date.now();
    const content = await generateCompetitorGapContent(competitor, gapKeywords);
    const duration = ((Date.now() - start) / 1000).toFixed(1);
    
    const filename = createFilename(competitor);
    const filepath = saveContent(content, filename);
    
    console.log('\n✅ Content generated successfully!');
    console.log(`   Duration: ${duration}s`);
    console.log(`   File: ${filepath}`);
    console.log(`   Word count: ~${content.split(/\s+/).length}`);
    
    // Save metadata
    const meta = {
      competitor,
      gapKeywords,
      generatedAt: new Date().toISOString(),
      url: `https://jobhuntin.com/vs/${competitor.toLowerCase()}-alternatives`,
    };
    fs.writeFileSync(filepath.replace('.md', '.json'), JSON.stringify(meta, null, 2));
    
  } catch (error: any) {
    console.error('\n❌ Error:', error.message);
    process.exit(1);
  }
}

main();
