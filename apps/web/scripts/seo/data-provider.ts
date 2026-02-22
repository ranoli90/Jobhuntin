
import { Pool } from 'pg';

// Initialize database connection
// Uses the same DATABASE_URL as the main app (Render/Supabase)
// Initialize database connection
// Uses the same DATABASE_URL as the main app (Render/Supabase)
const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: process.env.DATABASE_URL ? { rejectUnauthorized: false } : undefined
});

export interface JobMarketStats {
    totalJobs: number;
    averageSalary: number | null;
    minSalary: number | null;
    maxSalary: number | null;
    topCompanies: string[];
    activeSince: string; // Earliest job date found
}

/**
 * Fetches real job market statistics from the database for a specific location and role.
 * This prevents LLM hallucinations by providing factual data.
 */
export async function getCityJobStats(city: string, roleKeyword: string): Promise<JobMarketStats | null> {
    const client = await pool.connect();
    try {
        // 1. Get basic stats (count, salary)
        // We filter by location and title keywords
        // We only look at recent jobs (e.g., last 60 days) to match current market validation
        const statsQuery = `
      SELECT 
        COUNT(*) as total_jobs,
        AVG((salary_min + salary_max) / 2) as avg_salary,
        MIN(salary_min) as min_salary,
        MAX(salary_max) as max_salary,
        MIN(created_at) as earliest_job
      FROM public.jobs
      WHERE 
        location ILIKE $1 
        AND title ILIKE $2
        AND created_at > NOW() - INTERVAL '90 days'
    `;

        // 2. Get top hiring companies
        const companiesQuery = `
      SELECT company, COUNT(*) as count
      FROM public.jobs
      WHERE 
        location ILIKE $1 
        AND title ILIKE $2
        AND created_at > NOW() - INTERVAL '90 days'
        AND company IS NOT NULL
      GROUP BY company
      ORDER BY count DESC
      LIMIT 10
    `;

        const cityLike = `%${city}%`;
        const roleLike = `%${roleKeyword}%`;

        const [statsRes, companiesRes] = await Promise.all([
            client.query(statsQuery, [cityLike, roleLike]),
            client.query(companiesQuery, [cityLike, roleLike])
        ]);

        const stats = statsRes.rows[0];

        // If no jobs found, return null so the caller knows we have no data
        if (!stats || parseInt(stats.total_jobs) === 0) {
            console.log("⚠️ No real job data found for", roleKeyword, "in", city, ". Content may be generic.");
            return null;
        }

        return {
            totalJobs: parseInt(stats.total_jobs),
            averageSalary: stats.avg_salary ? Math.round(stats.avg_salary) : null,
            minSalary: stats.min_salary ? Math.round(stats.min_salary) : null,
            maxSalary: stats.max_salary ? Math.round(stats.max_salary) : null,
            topCompanies: companiesRes.rows.map(r => r.company),
            activeSince: stats.earliest_job ? new Date(stats.earliest_job).toISOString() : new Date().toISOString()
        };

    } catch (error) {
        console.warn('❌ Database error in getCityJobStats:', error);
        return null;
    } finally {
        client.release();
    }
}

/**
 * Returns a formatted prompt context string to be injected into the LLM
 */
export function formatStatsForPrompt(stats: JobMarketStats | null, city: string, role: string): string {
    if (!stats) {
        return `
    [REAL-TIME MARKET DATA]
    Status: No specific proprietary data available for this query.
    Instruction: Use general industry knowledge for ${role} in ${city}.
    `;
    }

    const companiesList = stats.topCompanies.slice(0, 5).join(', ');

    return `
  [REAL-TIME MARKET DATA - DO NOT HALLUCINATE]
  Status: Verified proprietary data provided.
  Instruction: You MUST reference these specific facts in the article.
  
  - Active Listings (90d): ${stats.totalJobs}+ verified open roles on JobHuntin
  - Salary Range: $${(stats.minSalary || 0).toLocaleString()} - $${(stats.maxSalary || 0).toLocaleString()}
  - Average Market Rate: $${(stats.averageSalary || 0).toLocaleString()}/yr
  - Top Active Employers: ${companiesList}
  
  Use this data to prove specific market knowledge. For example: "With over ${stats.totalJobs} active listings from companies like ${stats.topCompanies[0]}..."
  `;
}
