/**
 * generate-trending-content.ts
 * 
 * Generates SEO content for trending topics, news, and current events
 * Covers job market trends, salary reports, industry news
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const API_KEY = process.env.LLM_API_KEY || '';
const API_BASE = process.env.LLM_API_BASE || 'https://openrouter.ai/api/v1';
const MODEL = process.env.LLM_MODEL || 'openai/gpt-4o-mini';

const TOPIC = process.argv[2] || 'AI job market trends';

interface GeneratedContent {
  title: string;
  metaDescription: string;
  h1: string;
  content: string;
  keywords: string[];
  faqs: Array<{ question: string; answer: string }>;
}

async function generateTrendingContent(topic: string): Promise<GeneratedContent> {
  const currentDate = new Date().toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'long' 
  });

  const prompt = `You are an expert career industry analyst and SEO content writer for JobHuntin.com.

Write a comprehensive, engaging article about: "${topic}"

Context:
- Publication date: ${currentDate}
- Target audience: Job seekers, career changers, professionals
- Purpose: Provide actionable insights while ranking for related keywords

Requirements:
1. Title: Catchy, includes topic and year, under 60 chars
2. Meta description: Under 155 chars, compelling CTA
3. Content: 1500+ words, unique insights, actionable advice
4. Include current data/trends specific to ${currentDate}
5. Natural keyword integration (no stuffing)
6. Include salary data where relevant
7. Mention AI job tools naturally (JobHuntin as solution)

Structure:
- Introduction with hook
- Current state/overview
- Key trends and statistics
- Impact on job seekers
- Actionable tips
- Future outlook
- FAQ section (5 questions)

Return as JSON:
{
  "title": "...",
  "metaDescription": "...",
  "h1": "...",
  "content": "Full markdown content...",
  "keywords": ["keyword1", "keyword2", ...],
  "faqs": [{"question": "...", "answer": "..."}, ...]
}`;

  const response = await fetch(`${API_BASE}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_KEY}`,
      'HTTP-Referer': 'https://jobhuntin.com',
      'X-Title': 'JobHuntin SEO Engine',
    },
    body: JSON.stringify({
      model: MODEL,
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.7,
      max_tokens: 4000,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`API error: ${response.status} - ${error}`);
  }

  const data = await response.json();
  const content = data.choices[0]?.message?.content;
  
  if (!content) {
    throw new Error('No content generated');
  }

  // Extract JSON from response
  const jsonMatch = content.match(/\{[\s\S]*\}/);
  if (!jsonMatch) {
    throw new Error('Could not parse JSON from response');
  }

  return JSON.parse(jsonMatch[0]);
}

function generatePageHTML(content: GeneratedContent, topic: string): string {
  const slug = topic.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
  const currentDate = new Date().toISOString();
  
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${content.title}</title>
  <meta name="description" content="${content.metaDescription}">
  <meta name="keywords" content="${content.keywords.join(', ')}">
  <link rel="canonical" href="https://jobhuntin.com/news/${slug}">
  
  <!-- Open Graph -->
  <meta property="og:title" content="${content.title}">
  <meta property="og:description" content="${content.metaDescription}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="https://jobhuntin.com/news/${slug}">
  <meta property="article:published_time" content="${currentDate}">
  
  <!-- Schema.org Article -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "${content.title}",
    "description": "${content.metaDescription}",
    "datePublished": "${currentDate}",
    "author": {
      "@type": "Organization",
      "name": "JobHuntin"
    },
    "publisher": {
      "@type": "Organization",
      "name": "JobHuntin",
      "url": "https://jobhuntin.com"
    },
    "mainEntityOfPage": {
      "@type": "WebPage",
      "@id": "https://jobhuntin.com/news/${slug}"
    }
  }
  </script>
  
  <!-- FAQ Schema -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": ${JSON.stringify(content.faqs.map(faq => ({
      "@type": "Question",
      "name": faq.question,
      "acceptedAnswer": {
        "@type": "Answer",
        "text": faq.answer
      }
    })))}
  }
  </script>
</head>
<body>
  <article>
    <h1>${content.h1}</h1>
    <time datetime="${currentDate}">${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</time>
    
    <div class="content">
      ${content.content.split('\n').map(line => {
        if (line.startsWith('## ')) return `<h2>${line.slice(3)}</h2>`;
        if (line.startsWith('### ')) return `<h3>${line.slice(4)}</h3>`;
        if (line.startsWith('- ')) return `<li>${line.slice(2)}</li>`;
        if (line.trim() === '') return '';
        return `<p>${line}</p>`;
      }).join('\n')}
    </div>
    
    <section class="faq">
      <h2>Frequently Asked Questions</h2>
      ${content.faqs.map(faq => `
        <div class="faq-item">
          <h3>${faq.question}</h3>
          <p>${faq.answer}</p>
        </div>
      `).join('')}
    </section>
  </article>
</body>
</html>`;
}

async function main() {
  console.log(`\n📰 Generating trending content for: "${TOPIC}"`);
  console.log(`🧠 Model: ${MODEL}`);
  
  if (!API_KEY) {
    console.error('❌ LLM_API_KEY not set');
    process.exit(1);
  }

  try {
    const content = await generateTrendingContent(TOPIC);
    console.log(`\n✅ Content generated!`);
    console.log(`📝 Title: ${content.title}`);
    console.log(`📊 Keywords: ${content.keywords.slice(0, 5).join(', ')}...`);
    
    // Generate HTML
    const html = generatePageHTML(content, TOPIC);
    
    // Save to file
    const slug = TOPIC.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
    const outputDir = path.resolve(__dirname, '../../public/news');
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }
    
    const outputPath = path.join(outputDir, `${slug}.html`);
    fs.writeFileSync(outputPath, html);
    
    console.log(`\n💾 Saved to: ${outputPath}`);
    console.log(`🔗 URL: https://jobhuntin.com/news/${slug}`);
    
    // Also save metadata
    const metaPath = path.join(outputDir, `${slug}.json`);
    fs.writeFileSync(metaPath, JSON.stringify({
      topic: TOPIC,
      ...content,
      generatedAt: new Date().toISOString(),
      model: MODEL,
    }, null, 2));
    
  } catch (error) {
    console.error('❌ Failed:', error);
    process.exit(1);
  }
}

main();
