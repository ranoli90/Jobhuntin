/**
 * Browser-side cache implementation using localStorage.
 * Replaces the server-side Redis cache for client-side components.
 */

export class BrowserCacheService {
    private static instance: BrowserCacheService;

    private constructor() { }

    static getInstance(): BrowserCacheService {
        if (!BrowserCacheService.instance) {
            BrowserCacheService.instance = new BrowserCacheService();
        }
        return BrowserCacheService.instance;
    }

    private getKey(userId: string, type: string): string {
        return `jobhuntin:cache:${userId}:${type}`;
    }

    async get<T>(key: string): Promise<T | null> {
        try {
            const value = localStorage.getItem(key);
            if (!value) return null;

            const parsed = JSON.parse(value);
            // Check for TTL if we implemented it, but for now simple storage
            // Could add { value, expiresAt } structure
            if (parsed.expiresAt && parsed.expiresAt < Date.now()) {
                localStorage.removeItem(key);
                return null;
            }
            return parsed.value as T;
        } catch (error) {
            console.warn('Browser cache get error:', error);
            return null;
        }
    }

    async set(key: string, value: any, ttlSeconds?: number): Promise<void> {
        const item = {
            value,
            expiresAt: ttlSeconds ? Date.now() + (ttlSeconds * 1000) : null
        };
        try {
            localStorage.setItem(key, JSON.stringify(item));
        } catch (error) {
            const isQuotaExceeded = error instanceof DOMException &&
                (error.name === 'QuotaExceededError' || (error as DOMException & { code?: number }).code === 22);
            if (isQuotaExceeded) {
                try {
                    localStorage.removeItem(key);
                    localStorage.setItem(key, JSON.stringify(item));
                } catch {
                    console.warn('Browser cache: storage full, could not persist', key);
                }
            } else {
                console.warn('Browser cache set error:', error);
            }
        }
    }

    async del(key: string): Promise<void> {
        localStorage.removeItem(key);
    }

    // Domain specific methods matching Redis CacheService interface

    async cacheParsedResume(userId: string, resumeData: any): Promise<void> {
        await this.set(this.getKey(userId, 'resume:parsed'), resumeData, 7200); // 2 hours
    }

    async getParsedResume(userId: string): Promise<any | null> {
        return this.get(this.getKey(userId, 'resume:parsed'));
    }

    async cacheSkills(userId: string, skills: any): Promise<void> {
        await this.set(this.getKey(userId, 'skills'), skills, 3600); // 1 hour
    }

    async getSkills(userId: string): Promise<any | null> {
        return this.get(this.getKey(userId, 'skills'));
    }

    async cacheUserPreferences(userId: string, preferences: any): Promise<void> {
        await this.set(this.getKey(userId, 'preferences'), preferences, 86400); // 24 hours
    }

    async getUserPreferences(userId: string): Promise<any | null> {
        return this.get(this.getKey(userId, 'preferences'));
    }

    // AISuggestions and Matches
    async cacheAISuggestions(userId: string, suggestions: any): Promise<void> {
        await this.set(this.getKey(userId, 'ai:suggestions'), suggestions, 3600);
    }

    async getAISuggestions(userId: string): Promise<any | null> {
        return this.get(this.getKey(userId, 'ai:suggestions'));
    }

    async cacheJobMatches(userId: string, matches: any): Promise<void> {
        await this.set(this.getKey(userId, 'matches'), matches, 1800);
    }

    async getJobMatches(userId: string): Promise<any | null> {
        return this.get(this.getKey(userId, 'matches'));
    }

    async clearUserCache(userId: string): Promise<void> {
        const keys = [
            this.getKey(userId, 'resume:parsed'),
            this.getKey(userId, 'skills'),
            this.getKey(userId, 'preferences'),
            this.getKey(userId, 'ai:suggestions'),
            this.getKey(userId, 'matches')
        ];
        keys.forEach(key => localStorage.removeItem(key));
    }
}
