/**
 * Durable checkpointing and health for SEO engine using Render PostgreSQL
 */

import { Pool } from 'pg';
import { PoolClient } from 'pg';

// Initialize database connection
const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://jobhuntin_user:60BpsY53MYOO4fGFlvZKwDpiXB9Up9lL@dpg-d66ck524d50c73bas62g-a.oregon-postgres.render.com/jobhuntin'
});

const SERVICE_ID = 'jobhuntin-seo-engine';

export async function loadProgress(): Promise<number> {
  let client: PoolClient | null = null;
  try {
    client = await pool.connect();
    const result = await client.query(
      'SELECT last_index FROM seo_engine_progress WHERE service_id = $1',
      [SERVICE_ID]
    );
    return result.rows[0]?.last_index || 0;
  } catch (e) {
    console.warn('⚠️ Could not load progress from database, starting from 0.', e);
    return 0;
  } finally {
    if (client) client.release();
  }
}

export async function saveProgress(
  index: number,
  dailyQuotaUsed: number,
  dailyQuotaReset: Date
) {
  let client: PoolClient | null = null;
  try {
    client = await pool.connect();
    await client.query(
      `INSERT INTO seo_engine_progress 
       (service_id, last_index, daily_quota_used, daily_quota_reset, updated_at)
       VALUES ($1, $2, $3, $4, NOW())
       ON CONFLICT (service_id) DO UPDATE SET
         last_index = EXCLUDED.last_index,
         daily_quota_used = EXCLUDED.daily_quota_used,
         daily_quota_reset = EXCLUDED.daily_quota_reset,
         updated_at = NOW()`,
      [SERVICE_ID, index, dailyQuotaUsed, dailyQuotaReset.toISOString()]
    );
    console.log('💾 Progress saved to database');
  } catch (e) {
    console.warn('⚠️ Could not save progress to database.', e);
  } finally {
    if (client) client.release();
  }
}

export async function logSubmission(batchUrlFile: string, urlsSubmitted: number, success: boolean, errorMessage?: string) {
  let client: PoolClient | null = null;
  try {
    client = await pool.connect();
    await client.query(
      `INSERT INTO seo_submission_log 
       (service_id, batch_url_file, urls_submitted, success, error_message)
       VALUES ($1, $2, $3, $4, $5)`,
      [SERVICE_ID, batchUrlFile, urlsSubmitted, success, errorMessage]
    );
  } catch (e) {
    console.warn('⚠️ Could not log submission to database.', e);
  } finally {
    if (client) client.release();
  }
}

export async function getQuotaState(): Promise<{ used: number; reset: Date }> {
  let client: PoolClient | null = null;
  try {
    client = await pool.connect();
    const result = await client.query(
      'SELECT daily_quota_used, daily_quota_reset FROM seo_engine_progress WHERE service_id = $1',
      [SERVICE_ID]
    );
    const data = result.rows[0];
    if (data) {
      const reset = new Date(data.daily_quota_reset);
      // If reset time passed, reset quota
      if (reset < new Date()) {
        await saveProgress(data.last_index || 0, 0, new Date());
        return { used: 0, reset: new Date(Date.now() + 24 * 60 * 60 * 1000) };
      }
      return { used: data.daily_quota_used, reset };
    }
    return { used: 0, reset: new Date(Date.now() + 24 * 60 * 60 * 1000) };
  } catch (e) {
    console.warn('⚠️ Could not fetch quota state from database, assuming fresh quota.', e);
    return { used: 0, reset: new Date(Date.now() + 24 * 60 * 60 * 1000) };
  } finally {
    if (client) client.release();
  }
}

export async function getHealth() {
  let client: PoolClient | null = null;
  try {
    client = await pool.connect();
    const result = await client.query(
      'SELECT last_index, daily_quota_used, daily_quota_reset, updated_at FROM seo_engine_progress WHERE service_id = $1',
      [SERVICE_ID]
    );
    const data = result.rows[0];
    const recentLogs = await client.query(
      `SELECT urls_submitted, success, created_at 
       FROM seo_submission_log 
       WHERE service_id = $1 
       ORDER BY created_at DESC 
       LIMIT 5`,
      [SERVICE_ID]
    );
    return {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      progress: data,
      recentSubmissions: recentLogs.rows
    };
  } catch (e: any) {
    console.warn('⚠️ Could not check database health:', e);
    return {
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: e.message
    };
  } finally {
    if (client) client.release();
  }
}
