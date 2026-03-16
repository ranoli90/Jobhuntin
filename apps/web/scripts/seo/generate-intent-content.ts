/**
 * generate-intent-content.ts
 * 
 * Generates content optimized for specific search intent
 * Implements modern SEO best practices for 2026
 */

import 'dotenv/config';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

import {
  createContentKey,
  fingerprintContent,
  hasTrackedContentFingerprint,
  hasTrackedContentKey,
  trackContentFingerprint,
  trackContentKey,
} from './deduplication';
import { SEOError, SEO_ERROR_CODES } from './errors';
import { seoLogger } from './logger';
import { incrementCounter, recordHistogram, recordTimer, SEO_METRIC_NAMES } from './metrics';
import { validateCompetitor, validateIntent, validateTopic } from './validators';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const logger = seoLogger.child({ script: 'generate-intent-content' });

// Configuration
const MODEL = process.env.LLM_MODEL || 'openai/gpt-4o-mini';
const API_BASE = process.env.LLM_API_BASE || 'https://openrouter.ai/api/v1';
const API_KEY = process.env.LLM_API_KEY;

if (!API_KEY) {
  console.error('❌ LLM_API_KEY not set');
  process.exit(1);
}

// Content templates based on intent
const CONTENT_TEMPLATES: Record<string, any> = {
  informational: {
    structure: [
      'introduction: Hook with problem + promise',
      'what-is: Clear definition with examples',
      'why-matters: Benefits and importance',
      'how-to: Step-by-step instructions',
      'best-practices: Expert tips (E-E-A-T)',
      'common-mistakes: What to avoid',
      'faq: Voice-search friendly Q&A',
      'conclusion: Summary + CTA',
    ],
    schema: 'Article',
    wordCount: { min: 1500, max: 2500 },
    features: ['expert quotes', 'data citations', 'related terms', 'internal links'],
  },
  commercial: {
    structure: [
      'introduction: Problem agitation',
      'comparison: Side-by-side feature table',
      'detailed-reviews: In-depth analysis',
      'pros-cons: Honest evaluation',
      'pricing: Clear cost breakdown',
      'recommendations: Best for specific use cases',
      'faq: Objection handling',
      'conclusion: Clear winner + CTA',
    ],
    schema: 'Review',
    wordCount: { min: 2000, max: 3500 },
    features: ['comparison tables', 'star ratings', 'pros/cons lists', 'pricing info'],
  },
  transactional: {
    structure: [
      'hero: Strong value proposition',
      'offer-details: What you get',
      'how-to-claim: Simple steps',
      'urgency: Limited time/availability',
      'trust-signals: Guarantee, reviews',
      'faq: Purchase questions',
      'cta: Multiple conversion points',
    ],
    schema: 'Product',
    wordCount: { min: 800, max: 1500 },
    features: ['urgency timers', 'trust badges', 'social proof', 'clear CTAs'],
  },
  navigational: {
    structure: [
      'quick-answer: Immediate solution',
      'step-by-step: Detailed instructions',
      'troubleshooting: Common issues',
      'alternatives: Other methods',
      'faq: Related questions',
    ],
    schema: 'FAQPage',
    wordCount: { min: 600, max: 1200 },
    features: ['quick answers', 'numbered steps', 'screenshots', 'video embeds'],
  },
};

// Generate content with modern SEO optimization
async function generateContent(
  intent: string,
  topic: string,
  competitor?: string
): Promise<string> {
  const template = CONTENT_TEMPLATES[intent] || CONTENT_TEMPLATES.informational;

  // Read SEO requirements passed from the engine (LLM intent logic)
  const dynamicRequirements = process.env.SEO_REQUIREMENTS || '';

  const prompt = `You are an expert SEO content writer. Create a comprehensive, search-optimized article.

TOPIC: "${topic}"
SEARCH INTENT: ${intent}
${competitor ? `TARGET COMPETITOR: ${competitor}` : ''}

REQUIREMENTS:
1. Word count: ${template.wordCount.min}-${template.wordCount.max} words
2. Structure: Follow this outline exactly:
${template.structure.map((s: string, i: number) => `   ${i + 1}. ${s}`).join('\n')}

SEO OPTIMIZATION:
- Include semantic keywords and related terms naturally
- Use short paragraphs (2-3 sentences max) for mobile readability
- Add bullet points and numbered lists for scannability
- Include 3-5 internal link placeholders: [LINK: related-topic]
- Write compelling meta description (150-160 chars) in first comment
- Optimize for featured snippets with clear definitions and lists
- Include "Last Updated: ${new Date().toLocaleDateString()}" near top

E-E-A-T SIGNALS:
- Write from position of expertise
- Include specific data/statistics where relevant
- Reference industry standards/best practices
- Add authoritativeness through comprehensive coverage
- Build trust with honest, balanced information

${dynamicRequirements}

CONTENT QUALITY:
- Hook readers in first 100 words
- Answer search intent completely
- Include practical, actionable advice
- End with strong call-to-action
- No fluff or generic filler content

OUTPUT FORMAT:
Return ONLY the article content in Markdown format. No explanations, no markdown code blocks around the whole content. Start with the H1 title.`;

  console.log(`\n📝 Generating ${intent} content: "${topic}"`);
  console.log(`   Target: ${template.wordCount.min}-${template.wordCount.max} words`);
  console.log(`   Schema: ${template.schema}`);
  console.log('   Calling API...');

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
        { role: 'system', content: 'You are an expert SEO content writer specializing in job search and career tools.' },
        { role: 'user', content: prompt }
      ],
      temperature: 0.7,
      max_tokens: 4000,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new SEOError(SEO_ERROR_CODES.LLM_API_ERROR, `API error: ${response.status} - ${error}`, {
      context: { intent, topic, competitor },
    });
  }

  const data = await response.json();
  const content = data.choices[0].message.content;

  if (!content || typeof content !== 'string') {
    throw new SEOError(SEO_ERROR_CODES.CONTENT_GENERATION_ERROR, 'LLM returned empty content', {
      context: { intent, topic, competitor },
    });
  }

  // Add schema markup comment at the top
  const schemaComment = `<!-- Schema: ${template.schema} | Intent: ${intent} | Generated: ${new Date().toISOString()} -->\n`;

  return schemaComment + content;
}

// Create optimized filename from title
function createFilename(content: string, intent: string): string {
  // Extract H1 title
  const h1Match = content.match(/^# (.+)$/m);
  const title = h1Match ? h1Match[1] : 'untitled';

  // Create slug
  const slug = title
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .substring(0, 60);

  return `${intent}-${slug}.md`;
}

// Save content to file
function saveContent(content: string, filename: string): string {
  const outputDir = path.resolve(__dirname, '../../content/generated');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const filepath = path.join(outputDir, filename);
  fs.writeFileSync(filepath, content);
  return filepath;
}

// Generate and save meta tags
function generateMetaTags(content: string, topic: string): Record<string, string> {
  // Extract first paragraph for meta description
  const firstPara = content.match(/\n\n(.+?)(?=\n\n)/)?.[1] || topic;
  const description = firstPara.substring(0, 160);

  // Extract H1 for title
  const h1 = content.match(/^# (.+)$/m)?.[1] || topic;
  const title = h1.length > 60 ? h1.substring(0, 57) + '...' : h1;

  return {
    title,
    description,
    ogTitle: title,
    ogDescription: description,
    keywords: topic.toLowerCase().replace(/\s+/g, ', '),
  };
}

// Main function
async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const rawIntent = args[0];
  const rawTopic = args[1];
  const rawCompetitor = args[2] || '';

  if (!rawIntent || !rawTopic) {
    console.error('Usage: tsx generate-intent-content.ts <intent> <topic> [competitor]');
    console.error('Intents: informational, commercial, transactional, navigational');
    process.exit(1);
  }

  const intent = validateIntent(rawIntent);
  const topic = validateTopic(rawTopic);
  const competitor = validateCompetitor(rawCompetitor);
  const dedupeKey = createContentKey(['intent', intent, topic, competitor]);

  if (hasTrackedContentKey(dedupeKey, { script: 'generate-intent-content', intent, topic, competitor: competitor || null })) {
    console.log('\n⚠️ Duplicate content request detected. Skipping generation.');
    return;
  }

  try {
    console.log('='.repeat(70));
    console.log('🎯 MODERN SEO CONTENT GENERATOR');
    console.log('='.repeat(70));
    console.log(`Intent: ${intent}`);
    console.log(`Topic: ${topic}`);
    if (competitor) console.log(`Competitor: ${competitor}`);
    console.log('');

    const start = Date.now();
    const content = await generateContent(intent, topic, competitor || undefined);
    const duration = ((Date.now() - start) / 1000).toFixed(1);
    const contentFingerprint = fingerprintContent(content);

    if (hasTrackedContentFingerprint(contentFingerprint, {
      script: 'generate-intent-content',
      intent,
      topic,
      competitor: competitor || null,
    })) {
      console.log('\n⚠️ Equivalent generated content already exists. Skipping save.');
      return;
    }

    const filename = createFilename(content, intent);
    const filepath = saveContent(content, filename);
    const metaTags = generateMetaTags(content, topic);

    console.log('\n✅ Content generated successfully!');
    console.log(`   Duration: ${duration}s`);
    console.log(`   File: ${filepath}`);
    console.log(`   Word count: ~${content.split(/\s+/).length}`);
    console.log('\n📋 Meta Tags:');
    console.log(`   Title: ${metaTags.title}`);
    console.log(`   Description: ${metaTags.description}`);

    // Save metadata
    const metaPath = filepath.replace('.md', '.json');
    fs.writeFileSync(metaPath, JSON.stringify({
      ...metaTags,
      dedupeKey,
      contentFingerprint,
      intent,
      topic,
      competitor: competitor || null,
      generatedAt: new Date().toISOString(),
    }, null, 2));

    trackContentKey(dedupeKey, { script: 'generate-intent-content', filepath, metaPath, intent, topic, competitor: competitor || null });
    trackContentFingerprint(contentFingerprint, { script: 'generate-intent-content', filepath, intent, topic, competitor: competitor || null });
    incrementCounter(SEO_METRIC_NAMES.CONTENT_GENERATED, 1, { script: 'generate-intent-content', intent });
    recordHistogram(SEO_METRIC_NAMES.CONTENT_LENGTH, content.length, { script: 'generate-intent-content', intent });
    recordTimer(SEO_METRIC_NAMES.CONTENT_GENERATION_TIME, Date.now() - start, { script: 'generate-intent-content', intent });
    logger.info('Generated intent content', { intent, topic, competitor: competitor || null, filepath });

  } catch (error: any) {
    incrementCounter(SEO_METRIC_NAMES.CONTENT_FAILED, 1, { script: 'generate-intent-content', intent });
    console.error('\n❌ Error:', error.message);
    process.exit(1);
  }
}

main();
