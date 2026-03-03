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
const COMPETITOR_INTEL: Record<string, any> = {
  'teal': {
    weaknesses: ['Limited job board integrations', 'No auto-apply feature', 'Expensive for individuals'],
    pricing: '$9-29/month',
    features: ['Resume builder', 'Job tracker', 'LinkedIn optimization'],
    gaps: ['No programmatic job application', 'Limited ATS support', 'No cover letter generation'],
  },
  'lazyapply': {
    weaknesses: ['Outdated interface', 'High price point', 'Limited customization'],
    pricing: '$99-249 one-time',
    features: ['Auto-apply', 'Resume upload', 'Basic tracking'],
    gaps: ['No AI resume tailoring', 'Poor mobile experience', 'No interview prep'],
  },
  'simplify': {
    weaknesses: ['Browser extension only', 'Limited job sources', 'No resume builder'],
    pricing: 'Free - $9/month',
    features: ['Auto-fill applications', 'Job tracking', 'Chrome extension'],
    gaps: ['No mobile app', 'Limited to supported sites', 'No AI features'],
  },
  'jobcopilot': {
    weaknesses: ['New/unproven', 'Limited features', 'Small user base'],
    pricing: 'Free - $15/month',
    features: ['AI job matching', 'Application tracking', 'Resume suggestions'],
    gaps: ['Limited integrations', 'No auto-apply', 'Basic UI'],
  },
  'jobright': {
    weaknesses: ['Limited to tech jobs', 'No auto-apply', 'Expensive'],
    pricing: '$29-79/month',
    features: ['AI matching', 'Salary insights', 'Company research'],
    gaps: ['No application automation', 'Limited locations', 'No resume tools'],
  },
};

async function generateCompetitorGapContent(
  competitor: string,
  gapKeywords: string[]
): Promise<string> {
  const intel = COMPETITOR_INTEL[competitor.toLowerCase()] || {
    weaknesses: ['Unknown weaknesses'],
    pricing: 'Unknown',
    features: ['Unknown features'],
    gaps: ['Unknown gaps'],
  };

  const prompt = `Create a comprehensive comparison article that positions JobHuntin as the superior alternative to ${competitor}.

COMPETITOR: ${competitor}
COMPETITOR PRICING: ${intel.pricing}
COMPETITOR FEATURES: ${intel.features.join(', ')}
COMPETITOR WEAKNESSES: ${intel.weaknesses.join(', ')}
CONTENT GAPS TO TARGET: ${gapKeywords.join(', ')}

ARTICLE STRUCTURE:
1. H1: "${competitor} Alternatives 2026: Why JobHuntin is the Better Choice"
2. Introduction: Acknowledge ${competitor}'s popularity but highlight the problem
3. H2: "The Problem with ${competitor}"
   - Be honest but fair about weaknesses
   - Include user pain points from reviews
   - Use specific examples
4. H2: "Top ${competitor} Alternatives Compared"
   - Create comparison table: Features, Pricing, Pros, Cons
   - Position JobHuntin as #1 alternative
5. H2: "Why JobHuntin is the Best ${competitor} Alternative"
   - Address each competitor weakness with JobHuntin solution
   - Include specific feature comparisons
   - Use data/statistics where possible
6. H2: "Feature Comparison: ${competitor} vs JobHuntin"
   - Side-by-side comparison table
   - Highlight wins for JobHuntin
   - Be honest about any competitor wins (builds trust)
7. H2: "Pricing Comparison"
   - ${competitor}: ${intel.pricing}
   - JobHuntin pricing (mention free trial, value)
   - Calculate savings over time
8. H2: "User Reviews: What People Are Saying"
   - Quote hypothetical positive reviews for JobHuntin
   - Address common complaints about ${competitor}
9. H2: "How to Switch from ${competitor} to JobHuntin"
   - Step-by-step migration guide
   - Data export/import instructions
10. H2: FAQ
    - "Is JobHuntin better than ${competitor}?"
    - "Can I import my ${competitor} data?"
    - "Why is JobHuntin cheaper than ${competitor}?"
11. Conclusion: Strong CTA to try JobHuntin

SEO REQUIREMENTS:
- Include semantic keywords: ${gapKeywords.join(', ')}
- Target featured snippets with clear definitions
- Use comparison schema markup
- Include internal links: [LINK: jobhuntin-features], [LINK: pricing]
- Word count: 2500-3500 words
- Tone: Professional, helpful, not overly negative

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
