import { getHealth } from '../scripts/seo/supabase-checkpoint.js';

export default async function handler(req: Request) {
  try {
    const health = await getHealth();
    return new Response(JSON.stringify(health), {
      status: health.status === 'healthy' ? 200 : 503,
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (e) {
    return new Response(JSON.stringify({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: e instanceof Error ? e.message : String(e)
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
