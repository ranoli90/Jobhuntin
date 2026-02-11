/**
 * Durable checkpointing and health for SEO engine using Supabase
 */

import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.SUPABASE_URL!;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;
if (!supabaseUrl || !supabaseServiceKey) throw new Error('Missing Supabase env vars');

const supabase = createClient(supabaseUrl, supabaseServiceKey, {
  auth: { persistSession: false }
});

const SERVICE_ID = 'jobhuntin-seo-engine';

export async function loadProgress(): Promise<number> {
  try {
    const { data, error } = await supabase
      .from('seo_engine_progress')
      .select('last_index')
      .eq('service_id', SERVICE_ID)
      .single();
    if (error && error.code !== 'PGRST116') throw error;
    return data?.last_index ?? 0;
  } catch (e) {
    console.warn('⚠️ Could not load progress from Supabase, starting from 0.', e);
    return 0;
  }
}

export async function saveProgress(index: number, dailyQuotaUsed: number, dailyQuotaReset: Date) {
  try {
    const { error } = await supabase
      .from('seo_engine_progress')
      .upsert({
        service_id: SERVICE_ID,
        last_index: index,
        daily_quota_used: dailyQuotaUsed,
        daily_quota_reset: dailyQuotaReset.toISOString(),
        updated_at: new Date().toISOString()
      }, { onConflict: 'service_id' });
    if (error) throw error;
    console.log('💾 Progress saved to Supabase');
  } catch (e) {
    console.warn('⚠️ Could not save progress to Supabase.', e);
  }
}

export async function logSubmission(batchUrlFile: string, urlsSubmitted: number, success: boolean, errorMessage?: string) {
  try {
    const { error } = await supabase
      .from('seo_submission_log')
      .insert({
        service_id: SERVICE_ID,
        batch_url_file: batchUrlFile,
        urls_submitted: urlsSubmitted,
        success,
        error_message: errorMessage
      });
    if (error) throw error;
  } catch (e) {
    console.warn('⚠️ Could not log submission to Supabase.', e);
  }
}

export async function getQuotaState(): Promise<{ used: number; reset: Date }> {
  try {
    const { data, error } = await supabase
      .from('seo_engine_progress')
      .select('daily_quota_used, daily_quota_reset')
      .eq('service_id', SERVICE_ID)
      .single();
    if (error && error.code !== 'PGRST116') throw error;
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
    console.warn('⚠️ Could not fetch quota state from Supabase, assuming fresh quota.', e);
    return { used: 0, reset: new Date(Date.now() + 24 * 60 * 60 * 1000) };
  }
}

export async function getHealth() {
  try {
    const { data, error } = await supabase
      .from('seo_engine_progress')
      .select('last_index, daily_quota_used, daily_quota_reset, updated_at')
      .eq('service_id', SERVICE_ID)
      .single();
    if (error && error.code !== 'PGRST116') throw error;
    const recentLogs = await supabase
      .from('seo_submission_log')
      .select('urls_submitted, success, created_at')
      .eq('service_id', SERVICE_ID)
      .order('created_at', { ascending: false })
      .limit(5);
    return {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      progress: data,
      recentSubmissions: recentLogs.data || [],
      environment: {
        GOOGLE_SERVICE_ACCOUNT_KEY: !!process.env.GOOGLE_SERVICE_ACCOUNT_KEY,
        GOOGLE_SEARCH_CONSOLE_SITE: process.env.GOOGLE_SEARCH_CONSOLE_SITE,
        SUPABASE_URL: process.env.SUPABASE_URL
      }
    };
  } catch (e) {
    return {
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: e instanceof Error ? e.message : String(e)
    };
  }
}
