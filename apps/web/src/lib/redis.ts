import Redis from 'redis';

// Redis client configuration
const redis = new Redis({
  host: process.env.REDIS_HOST || 'redis-18567.c270.us-east-1-3.ec2.cloud.redislabs.com',
  port: parseInt(process.env.REDIS_PORT || '18567'),
  password: process.env.REDIS_PASSWORD || 'your-redis-password',
  retryDelayOnFailover: 100,
  maxRetriesPerRequest: 3,
  lazyConnect: true,
  keepAlive: 30000,
  connectTimeout: 10000,
  commandTimeout: 5000,
});

// Redis event listeners
redis.on('connect', () => {
  console.log('Connected to Redis successfully');
});

redis.on('ready', () => {
  console.log('Redis client ready for commands');
});

redis.on('error', (err: Error) => {
  console.error('Redis connection error:', err);
});

redis.on('close', () => {
  console.log('Redis connection closed');
});

redis.on('reconnecting', () => {
  console.log('Redis client reconnecting...');
});

// Cache service wrapper
export class CacheService {
  private static instance: CacheService;
  
  static getInstance(): CacheService {
    if (!CacheService.instance) {
      CacheService.instance = new CacheService();
    }
    return CacheService.instance;
  }

  // Get cached value
  async get<T>(key: string): Promise<T | null> {
    try {
      const value = await redis.get(key);
      return value ? JSON.parse(value) : null;
    } catch (error) {
      console.error('Cache get error:', error);
      return null;
    }
  }

  // Set cached value with TTL
  async set(key: string, value: any, ttl: number = 3600): Promise<void> {
    try {
      await redis.setex(key, ttl, JSON.stringify(value));
    } catch (error) {
      console.error('Cache set error:', error);
    }
  }

  // Delete cached value
  async del(key: string): Promise<void> {
    try {
      await redis.del(key);
    } catch (error) {
      console.error('Cache delete error:', error);
    }
  }

  // Check if key exists
  async exists(key: string): Promise<boolean> {
    try {
      const result = await redis.exists(key);
      return result === 1;
    } catch (error) {
      console.error('Cache exists error:', error);
      return false;
    }
  }

  // Set multiple values
  async mset(keyValuePairs: Record<string, any>, ttl: number = 3600): Promise<void> {
    try {
      const pipeline = redis.pipeline();
      
      Object.entries(keyValuePairs).forEach(([key, value]: [string, any]) => {
        pipeline.setex(key, ttl, JSON.stringify(value));
      });
      
      await pipeline.exec();
    } catch (error) {
      console.error('Cache mset error:', error);
    }
  }

  // Get multiple values
  async mget<T>(keys: string[]): Promise<(T | null)[]> {
    try {
      const values = await redis.mget(...keys);
      return values.map((value: string | null) => value ? JSON.parse(value) : null);
    } catch (error) {
      console.error('Cache mget error:', error);
      return keys.map(() => null);
    }
  }

  // Cache AI suggestions for 24 hours
  async cacheAISuggestions(userId: string, suggestions: any): Promise<void> {
    const key = `ai:suggestions:${userId}`;
    await this.set(key, suggestions, 86400);
  }

  // Get cached AI suggestions
  async getAISuggestions(userId: string): Promise<any | null> {
    const key = `ai:suggestions:${userId}`;
    return this.get(key);
  }

  // Cache parsed resume data for 7 days
  async cacheParsedResume(userId: string, resumeData: any): Promise<void> {
    const key = `resume:parsed:${userId}`;
    await this.set(key, resumeData, 604800);
  }

  // Get cached parsed resume
  async getParsedResume(userId: string): Promise<any | null> {
    const key = `resume:parsed:${userId}`;
    return this.get(key);
  }

  // Cache user preferences for 1 hour
  async cacheUserPreferences(userId: string, preferences: any): Promise<void> {
    const key = `preferences:${userId}`;
    await this.set(key, preferences, 3600);
  }

  // Get cached user preferences
  async getUserPreferences(userId: string): Promise<any | null> {
    const key = `preferences:${userId}`;
    return this.get(key);
  }

  // Cache job matches for 30 minutes
  async cacheJobMatches(userId: string, matches: any): Promise<void> {
    const key = `matches:${userId}`;
    await this.set(key, matches, 1800);
  }

  // Get cached job matches
  async getJobMatches(userId: string): Promise<any | null> {
    const key = `matches:${userId}`;
    return this.get(key);
  }

  // Cache skills data for 6 hours
  async cacheSkills(userId: string, skills: any): Promise<void> {
    const key = `skills:${userId}`;
    await this.set(key, skills, 21600);
  }

  // Get cached skills data
  async getSkills(userId: string): Promise<any | null> {
    const key = `skills:${userId}`;
    return this.get(key);
  }

  // Clear all user-related cache
  async clearUserCache(userId: string): Promise<void> {
    const patterns = [
      `ai:suggestions:${userId}`,
      `resume:parsed:${userId}`,
      `preferences:${userId}`,
      `matches:${userId}`,
      `skills:${userId}`
    ];

    try {
      await redis.del(...patterns);
    } catch (error) {
      console.error('Clear user cache error:', error);
    }
  }

  // Health check
  async healthCheck(): Promise<{ healthy: boolean; message: string }> {
    try {
      const result = await redis.ping();
      return {
        healthy: result === 'PONG',
        message: result === 'PONG' ? 'Redis connection successful' : 'Redis ping failed'
      };
    } catch (error: unknown) {
      return {
        healthy: false,
        message: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  // Get Redis info
  async getRedisInfo(): Promise<any> {
    try {
      const info = await redis.info();
      return info;
    } catch (error: unknown) {
      console.error('Redis info error:', error);
      return null;
    }
  }

  // Close Redis connection
  async close(): Promise<void> {
    await redis.quit();
    console.log('Redis connection closed');
  }
}

export default redis;
