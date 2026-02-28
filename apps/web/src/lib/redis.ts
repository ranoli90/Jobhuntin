/**
 * NOTE: This module is used by SEO build scripts (server-side only via tsx/node).
 * It should NOT be imported by any browser-side React component.
 */
import { createClient } from 'redis';

// SECURITY: This module must ONLY run server-side. Never import in browser bundles.
if (typeof window !== 'undefined') {
  console.error('[SECURITY] redis.ts was imported in a browser context — this is a configuration error.');
}

// Redis client configuration — all values MUST come from environment variables
const redis = createClient({
  socket: {
    host: process.env.REDIS_HOST,
    port: parseInt(process.env.REDIS_PORT || '6379'),
  },
  password: process.env.REDIS_PASSWORD,
});

// Redis connection events
redis.on('error', (err) => console.error('Redis Client Error', err));
redis.on('connect', () => console.log('Redis Client Connected'));
redis.on('ready', () => console.log('Redis Client Ready'));
redis.on('end', () => console.log('Redis Client Ended'));

// Connect to Redis
redis.connect().catch(console.error);

export default redis;

// Cache service class
export class CacheService {
  private static instance: CacheService;
  private client: ReturnType<typeof createClient>;

  private constructor() {
    this.client = redis;
  }

  static getInstance(): CacheService {
    if (!CacheService.instance) {
      CacheService.instance = new CacheService();
    }
    return CacheService.instance;
  }

  async get<T>(key: string): Promise<T | null> {
    try {
      const value = await this.client.get(key);
      return value ? JSON.parse(value) as T : null;
    } catch (error) {
      console.error('Cache get error:', error);
      return null;
    }
  }

  async set(key: string, value: any, ttl?: number): Promise<void> {
    try {
      const serialized = JSON.stringify(value);
      if (ttl) {
        await this.client.setEx(key, ttl, serialized);
      } else {
        await this.client.set(key, serialized);
      }
    } catch (error) {
      console.error('Cache set error:', error);
    }
  }

  async del(key: string): Promise<void> {
    try {
      await this.client.del(key);
    } catch (error) {
      console.error('Cache delete error:', error);
    }
  }

  async mset(keyValuePairs: Record<string, any>): Promise<void> {
    try {
      const serializedPairs: string[] = [];
      for (const [key, value] of Object.entries(keyValuePairs)) {
        serializedPairs.push(key, JSON.stringify(value));
      }
      await this.client.mSet(serializedPairs);
    } catch (error) {
      console.error('Cache mset error:', error);
    }
  }

  async mget(keys: string[]): Promise<(any | null)[]> {
    try {
      const values = await this.client.mGet(keys);
      return values.map(value => value ? JSON.parse(value) : null);
    } catch (error) {
      console.error('Cache mget error:', error);
      return new Array(keys.length).fill(null);
    }
  }

  // Specific cache methods for different data types
  async cacheAISuggestions(userId: string, suggestions: any): Promise<void> {
    await this.set(`ai:suggestions:${userId}`, suggestions, 3600); // 1 hour TTL
  }

  async getAISuggestions(userId: string): Promise<any | null> {
    return this.get(`ai:suggestions:${userId}`);
  }

  async cacheParsedResume(userId: string, resumeData: any): Promise<void> {
    await this.set(`resume:parsed:${userId}`, resumeData, 7200); // 2 hours TTL
  }

  async getParsedResume(userId: string): Promise<any | null> {
    return this.get(`resume:parsed:${userId}`);
  }

  async cacheUserPreferences(userId: string, preferences: any): Promise<void> {
    await this.set(`preferences:${userId}`, preferences, 86400); // 24 hours TTL
  }

  async getUserPreferences(userId: string): Promise<any | null> {
    return this.get(`preferences:${userId}`);
  }

  async cacheJobMatches(userId: string, matches: any): Promise<void> {
    await this.set(`matches:${userId}`, matches, 1800); // 30 minutes TTL
  }

  async getJobMatches(userId: string): Promise<any | null> {
    return this.get(`matches:${userId}`);
  }

  async cacheSkills(userId: string, skills: any): Promise<void> {
    await this.set(`skills:${userId}`, skills, 3600); // 1 hour TTL
  }

  async getSkills(userId: string): Promise<any | null> {
    return this.get(`skills:${userId}`);
  }

  async clearUserCache(userId: string): Promise<void> {
    const keys = [
      `ai:suggestions:${userId}`,
      `resume:parsed:${userId}`,
      `preferences:${userId}`,
      `matches:${userId}`,
      `skills:${userId}`
    ];

    try {
      await Promise.all(keys.map(key => this.del(key)));
    } catch (error) {
      console.error('Cache clear error:', error);
    }
  }

  async healthCheck(): Promise<{ healthy: boolean; message: string }> {
    try {
      await this.client.ping();
      return { healthy: true, message: 'Redis is healthy' };
    } catch (error) {
      return {
        healthy: false,
        message: `Redis error: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }

  async getRedisInfo(): Promise<any> {
    try {
      return await this.client.info();
    } catch (error) {
      console.error('Redis info error:', error);
      return null;
    }
  }

  async close(): Promise<void> {
    try {
      await this.client.quit();
    } catch (error) {
      console.error('Redis close error:', error);
    }
  }
}
