import { test, expect, Page } from '@playwright/test';

test.describe('AI Features - Semantic Match', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/app/matches', { waitUntil: 'networkidle', timeout: 30000 });
  });

  test('should display match results page with proper structure', async ({ page }) => {
    await expect(page.getByText('Semantic Match Analysis')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Match Results')).toBeVisible();
  });

  test('should show no job selected state when no jobId param', async ({ page }) => {
    await expect(page.getByText('No Job Selected')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Browse Jobs')).toBeVisible();
  });

  test('should navigate to job selection when clicking Browse Jobs', async ({ page }) => {
    await page.getByText('Browse Jobs').click();
    await page.waitForURL('**/app/jobs**', { timeout: 10000 });
  });

  test('should load match results when jobId is provided', async ({ page }) => {
    await page.goto('/app/matches?jobId=test-job-123', { waitUntil: 'networkidle' });

    await page.route('**/api/ai/semantic-match', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          job_id: 'test-job-123',
          score: 0.85,
          semantic_similarity: 0.88,
          skill_match_ratio: 0.82,
          experience_alignment: 0.85,
          matched_skills: ['React', 'TypeScript', 'Node.js'],
          missing_skills: ['GraphQL', 'Docker'],
          reasoning: 'Strong match for the role based on technical skills alignment.',
          confidence: 'high',
          passed_dealbreakers: true,
          dealbreaker_reasons: [],
        }),
      });
    });

    await expect(page.getByText('85% Match')).toBeVisible({ timeout: 10000 });
  });

  test('should display score visualization components', async ({ page }) => {
    await page.goto('/app/matches?jobId=test-job-456', { waitUntil: 'networkidle' });

    await page.route('**/api/ai/semantic-match', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          job_id: 'test-job-456',
          score: 0.72,
          semantic_similarity: 0.75,
          skill_match_ratio: 0.70,
          experience_alignment: 0.71,
          matched_skills: ['Python', 'Django'],
          missing_skills: ['AWS', 'Kubernetes'],
          reasoning: 'Good match with room for improvement in cloud skills.',
          confidence: 'medium',
          passed_dealbreakers: true,
          dealbreaker_reasons: [],
        }),
      });
    });

    await expect(page.getByText('Semantic Similarity')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Skill Match')).toBeVisible();
    await expect(page.getByText('Experience Alignment')).toBeVisible();
  });

  test('should show dealbreaker warnings when present', async ({ page }) => {
    await page.goto('/app/matches?jobId=test-job-789', { waitUntil: 'networkidle' });

    await page.route('**/api/ai/semantic-match', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          job_id: 'test-job-789',
          score: 0.45,
          semantic_similarity: 0.50,
          skill_match_ratio: 0.40,
          experience_alignment: 0.45,
          matched_skills: ['JavaScript'],
          missing_skills: ['React', 'TypeScript', 'Node.js', 'PostgreSQL'],
          reasoning: 'Significant skill gaps detected.',
          confidence: 'low',
          passed_dealbreakers: false,
          dealbreaker_reasons: ['Salary below minimum threshold', 'Location not compatible'],
        }),
      });
    });

    await expect(page.getByText('Dealbreaker Issues Detected')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Salary below minimum threshold')).toBeVisible();
    await expect(page.getByText('Location not compatible')).toBeVisible();
  });

  test('should expand and collapse match explanation', async ({ page }) => {
    await page.goto('/app/matches?jobId=test-job-exp', { waitUntil: 'networkidle' });

    await page.route('**/api/ai/semantic-match', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          job_id: 'test-job-exp',
          score: 0.80,
          semantic_similarity: 0.82,
          skill_match_ratio: 0.78,
          experience_alignment: 0.80,
          matched_skills: ['React', 'TypeScript'],
          missing_skills: ['GraphQL'],
          reasoning: 'This is a detailed explanation of the match analysis that should be expandable.',
          confidence: 'high',
          passed_dealbreakers: true,
          dealbreaker_reasons: [],
        }),
      });
    });

    await expect(page.getByText('Match Explanation')).toBeVisible({ timeout: 10000 });
    await page.getByText('Match Explanation').click();
    await expect(page.getByText('This is a detailed explanation')).toBeVisible();
  });

  test('should export match report', async ({ page }) => {
    await page.goto('/app/matches?jobId=test-job-export', { waitUntil: 'networkidle' });

    await page.route('**/api/ai/semantic-match', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          job_id: 'test-job-export',
          score: 0.90,
          semantic_similarity: 0.92,
          skill_match_ratio: 0.88,
          experience_alignment: 0.90,
          matched_skills: ['React', 'TypeScript', 'Node.js'],
          missing_skills: [],
          reasoning: 'Excellent match for the position.',
          confidence: 'high',
          passed_dealbreakers: true,
          dealbreaker_reasons: [],
        }),
      });
    });

    await expect(page.getByRole('button', { name: /Export/i })).toBeVisible({ timeout: 10000 });
  });
});

test.describe('AI Features - Resume Tailoring', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/app/ai-tailor', { waitUntil: 'networkidle', timeout: 30000 });
  });

  test('should display resume tailor page', async ({ page }) => {
    await expect(page.getByText('Resume Tailor')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Upload Resume')).toBeVisible();
    await expect(page.getByText('Job Details')).toBeVisible();
  });

  test('should allow switching between URL and paste mode', async ({ page }) => {
    await expect(page.getByRole('button', { name: /URL/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Paste/i })).toBeVisible();

    await page.getByRole('button', { name: /URL/i }).click();
    await expect(page.getByPlaceholder(/https:\/\//i)).toBeVisible();

    await page.getByRole('button', { name: /Paste/i }).click();
    await expect(page.getByPlaceholder(/Paste the job description/i)).toBeVisible();
  });

  test('should show file upload dropzone', async ({ page }) => {
    await expect(page.getByText(/Drop your resume here/i)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('PDF only, max 5MB')).toBeVisible();
  });

  test('should display tailor button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Tailor Resume/i })).toBeVisible({ timeout: 10000 });
  });

  test('should show loading state during tailoring', async ({ page }) => {
    await page.route('**/api/ai/tailor-resume', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          original_summary: 'Original summary',
          tailored_summary: 'Tailored summary',
          highlighted_skills: ['React', 'TypeScript'],
          emphasized_experiences: [],
          added_keywords: ['Agile', 'CI/CD'],
          ats_optimization_score: 0.85,
          tailoring_confidence: 'high',
        }),
      });
    });

    await page.getByRole('button', { name: /Tailor Resume/i }).click();
    await expect(page.getByText(/Tailoring/i)).toBeVisible({ timeout: 5000 });
  });

  test('should display tailoring results', async ({ page }) => {
    await page.route('**/api/ai/tailor-resume', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          original_summary: 'Original summary text',
          tailored_summary: 'Optimized tailored summary with highlighted keywords',
          highlighted_skills: ['React', 'TypeScript', 'Node.js'],
          emphasized_experiences: [{ company: 'TechCorp', highlight: 'Led team' }],
          added_keywords: ['Agile', 'CI/CD', 'Microservices'],
          ats_optimization_score: 0.88,
          tailoring_confidence: 'high',
        }),
      });
    });

    await page.getByRole('button', { name: /Tailor Resume/i }).click();

    await expect(page.getByText('Tailored Summary')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Highlighted Skills')).toBeVisible();
    await expect(page.getByText('Added Keywords')).toBeVisible();
  });

  test('should handle tailoring error gracefully', async ({ page }) => {
    await page.route('**/api/ai/tailor-resume', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error: { code: 'TAILORING_FAILED', message: 'Could not process resume' },
        }),
      });
    });

    await page.getByRole('button', { name: /Tailor Resume/i }).click();

    await expect(page.getByText('Tailoring Failed')).toBeVisible({ timeout: 10000 });
  });
});

test.describe('AI Features - ATS Scoring', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/app/ats-score', { waitUntil: 'networkidle', timeout: 30000 });
  });

  test('should display ATS score page', async ({ page }) => {
    await expect(page.getByText('ATS Score Dashboard')).toBeVisible({ timeout: 10000 });
    await expect(page.getByPlaceholder(/Paste your resume/i)).toBeVisible();
    await expect(page.getByPlaceholder(/Paste the job description/i)).toBeVisible();
  });

  test('should show calculate button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Calculate ATS Score/i })).toBeVisible({ timeout: 10000 });
  });

  test('should display ATS score results with 23 metrics', async ({ page }) => {
    await page.route('**/api/ai/ats-score', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          overall_score: 0.78,
          metrics: {
            keyword_match: 0.82,
            skills_relevance: 0.75,
            experience_alignment: 0.80,
            quantifiable_achievements: 0.70,
            action_verbs: 0.85,
            format_score: 0.90,
            section_completeness: 0.88,
            contact_info: 1.0,
            summary_quality: 0.72,
            education_relevance: 0.65,
            certification_match: 0.50,
            readability_score: 0.80,
            length_score: 0.85,
            ats_compatibility: 0.78,
            spelling_grammar: 0.95,
            consistency: 0.88,
            dates_format: 0.90,
            bullet_points: 0.75,
            file_format: 1.0,
            personalization: 0.70,
            industry_keywords: 0.68,
            soft_skills: 0.72,
            technical_skills: 0.80,
          },
          recommendations: [
            'Add more quantifiable achievements',
            'Include relevant certifications',
            'Improve industry-specific keyword density',
          ],
        }),
      });
    });

    await page.getByRole('button', { name: /Calculate ATS Score/i }).click();

    await expect(page.getByText('78%')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Overall ATS Score')).toBeVisible();
    await expect(page.getByText('23 Metrics Analysis')).toBeVisible();
  });

  test('should show optimization recommendations', async ({ page }) => {
    await page.route('**/api/ai/ats-score', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          overall_score: 0.65,
          metrics: {
            keyword_match: 0.60,
            skills_relevance: 0.65,
            experience_alignment: 0.70,
            quantifiable_achievements: 0.40,
            action_verbs: 0.75,
            format_score: 0.80,
            section_completeness: 0.85,
            contact_info: 0.90,
            summary_quality: 0.55,
            education_relevance: 0.60,
            certification_match: 0.30,
            readability_score: 0.70,
            length_score: 0.75,
            ats_compatibility: 0.68,
            spelling_grammar: 0.90,
            consistency: 0.82,
            dates_format: 0.85,
            bullet_points: 0.65,
            file_format: 0.95,
            personalization: 0.50,
            industry_keywords: 0.45,
            soft_skills: 0.60,
            technical_skills: 0.70,
          },
          recommendations: [
            'Add more quantifiable achievements with metrics',
            'Include relevant certifications section',
            'Improve professional summary quality',
            'Increase industry-specific keyword usage',
          ],
        }),
      });
    });

    await page.getByRole('button', { name: /Calculate ATS Score/i }).click();

    await expect(page.getByText('Optimization Recommendations')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Add more quantifiable achievements')).toBeVisible();
  });

  test('should detect ATS platform', async ({ page }) => {
    await page.route('**/api/ai/ats-score', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          overall_score: 0.75,
          metrics: { keyword_match: 0.80 },
          recommendations: [],
        }),
      });
    });

    const jobDesc = page.getByPlaceholder(/Paste the job description/i);
    await jobDesc.fill('This job is posted on Greenhouse. Apply now...');

    await page.getByRole('button', { name: /Calculate ATS Score/i }).click();

    await expect(page.getByText('Greenhouse')).toBeVisible({ timeout: 10000 });
  });
});

test.describe('AI Features - Error Handling', () => {
  test('should handle network errors gracefully', async ({ page }) => {
    await page.goto('/app/ats-score', { waitUntil: 'networkidle' });

    await page.route('**/api/ai/ats-score', async (route) => {
      await route.abort('failed');
    });

    await page.getByRole('button', { name: /Calculate ATS Score/i }).click();

    await expect(page.getByText(/Failed|Error/i)).toBeVisible({ timeout: 10000 });
  });

  test('should handle rate limiting', async ({ page }) => {
    await page.goto('/app/ats-score', { waitUntil: 'networkidle' });

    await page.route('**/api/ai/ats-score', async (route) => {
      await route.fulfill({
        status: 429,
        contentType: 'application/json',
        body: JSON.stringify({
          error: { code: 'RATE_LIMITED', message: 'Too many requests' },
        }),
      });
    });

    await page.getByRole('button', { name: /Calculate ATS Score/i }).click();

    await expect(page.getByText(/Too many requests|Rate limited/i)).toBeVisible({ timeout: 10000 });
  });
});

test.describe('AI Features - Loading States', () => {
  test('should show loading spinner during semantic match', async ({ page }) => {
    await page.goto('/app/matches?jobId=test-loading', { waitUntil: 'networkidle' });

    await page.route('**/api/ai/semantic-match', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 3000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          job_id: 'test-loading',
          score: 0.80,
          semantic_similarity: 0.82,
          skill_match_ratio: 0.78,
          experience_alignment: 0.80,
          matched_skills: ['React'],
          missing_skills: [],
          reasoning: 'Good match',
          confidence: 'high',
          passed_dealbreakers: true,
          dealbreaker_reasons: [],
        }),
      });
    });

    await expect(page.getByText(/Analyzing|Loading/i)).toBeVisible({ timeout: 5000 });
  });
});
