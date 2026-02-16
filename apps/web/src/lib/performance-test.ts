# Database Performance Test Script

import { query, healthCheck, getPoolStats } from '../lib/database';
import { CacheService } from '../lib/redis';
import { DatabaseMetrics, CacheMetrics, HealthMonitor } from '../lib/metrics';

export class DatabasePerformanceTest {
  static async runFullTest() {
    console.log('🚀 Starting Database Performance Test...\n');
    
    const results = {
      timestamp: new Date().toISOString(),
      database: {},
      redis: {},
      performance: {}
    };

    try {
      // 1. Database Health Check
      console.log('1️⃣ Testing Database Health...');
      const dbHealth = await healthCheck();
      results.database.health = dbHealth;
      console.log('✅ Database Health:', dbHealth);

      // 2. Connection Pool Stats
      console.log('\n2️⃣ Checking Connection Pool...');
      const poolStats = getPoolStats();
      results.database.poolStats = poolStats;
      console.log('✅ Pool Stats:', poolStats);

      // 3. Database Connection Metrics
      console.log('\n3️⃣ Testing Database Connections...');
      const connectionStats = await DatabaseMetrics.getConnectionStats();
      results.database.connections = connectionStats;
      console.log('✅ Connection Stats:', connectionStats);

      // 4. Query Performance Test
      console.log('\n4️⃣ Testing Query Performance...');
      const queryPerf = await this.testQueryPerformance();
      results.performance.queries = queryPerf;
      console.log('✅ Query Performance:', queryPerf);

      // 5. Redis Health Check
      console.log('\n5️⃣ Testing Redis Health...');
      const cacheService = CacheService.getInstance();
      const redisHealth = await cacheService.healthCheck();
      results.redis.health = redisHealth;
      console.log('✅ Redis Health:', redisHealth);

      // 6. Cache Performance Test
      console.log('\n6️⃣ Testing Cache Performance...');
      const cachePerf = await this.testCachePerformance();
      results.performance.cache = cachePerf;
      console.log('✅ Cache Performance:', cachePerf);

      // 7. Full System Health
      console.log('\n7️⃣ Full System Health Check...');
      const systemHealth = await HealthMonitor.getFullHealthStatus();
      results.system = systemHealth;
      console.log('✅ System Health:', systemHealth);

      // 8. Generate Report
      console.log('\n📊 Generating Performance Report...');
      const report = this.generateReport(results);
      console.log('\n📋 Performance Report:');
      console.log(report);

      return results;

    } catch (error) {
      console.error('❌ Performance test failed:', error);
      throw error;
    }
  }

  static async testQueryPerformance() {
    const tests = [
      {
        name: 'Simple SELECT',
        query: 'SELECT 1 as test',
        iterations: 100
      },
      {
        name: 'User Profile Query',
        query: 'SELECT COUNT(*) as count FROM users WHERE created_at > NOW() - INTERVAL \'24 hours\'',
        iterations: 50
      },
      {
        name: 'Complex JOIN',
        query: `
          SELECT u.id, u.email, COUNT(a.id) as application_count 
          FROM users u 
          LEFT JOIN applications a ON u.id = a.user_id 
          WHERE u.created_at > NOW() - INTERVAL '7 days'
          GROUP BY u.id, u.email
        `,
        iterations: 20
      }
    ];

    const results = [];

    for (const test of tests) {
      const times = [];
      
      for (let i = 0; i < test.iterations; i++) {
        const start = performance.now();
        await query(test.query);
        const end = performance.now();
        times.push(end - start);
      }

      const avgTime = times.reduce((a, b) => a + b, 0) / times.length;
      const minTime = Math.min(...times);
      const maxTime = Math.max(...times);

      results.push({
        test: test.name,
        iterations: test.iterations,
        avgTime: avgTime.toFixed(2) + 'ms',
        minTime: minTime.toFixed(2) + 'ms',
        maxTime: maxTime.toFixed(2) + 'ms',
        totalTime: times.reduce((a, b) => a + b, 0).toFixed(2) + 'ms'
      });
    }

    return results;
  }

  static async testCachePerformance() {
    const cacheService = CacheService.getInstance();
    const testData = {
      userId: 'test-user-123',
      resumeData: {
        title: 'Software Engineer',
        skills: ['JavaScript', 'React', 'Node.js'],
        years: 5,
        summary: 'Experienced developer'
      },
      preferences: {
        location: 'San Francisco',
        role_type: 'Full-time',
        salary_min: '100000'
      }
    };

    // Test Write Performance
    const writeTimes = [];
    for (let i = 0; i < 100; i++) {
      const start = performance.now();
      await cacheService.cacheParsedResume(testData.userId, testData.resumeData);
      const end = performance.now();
      writeTimes.push(end - start);
    }

    // Test Read Performance
    const readTimes = [];
    for (let i = 0; i < 100; i++) {
      const start = performance.now();
      await cacheService.getParsedResume(testData.userId);
      const end = performance.now();
      readTimes.push(end - start);
    }

    // Test Batch Operations
    const batchStart = performance.now();
    await cacheService.mset({
      [`test:user:${testData.userId}:prefs`]: testData.preferences,
      [`test:user:${testData.userId}:skills`]: testData.resumeData.skills
    });
    const batchEnd = performance.now();

    return {
      write: {
        avgTime: (writeTimes.reduce((a, b) => a + b, 0) / writeTimes.length).toFixed(2) + 'ms',
        minTime: Math.min(...writeTimes).toFixed(2) + 'ms',
        maxTime: Math.max(...writeTimes).toFixed(2) + 'ms'
      },
      read: {
        avgTime: (readTimes.reduce((a, b) => a + b, 0) / readTimes.length).toFixed(2) + 'ms',
        minTime: Math.min(...readTimes).toFixed(2) + 'ms',
        maxTime: Math.max(...readTimes).toFixed(2) + 'ms'
      },
      batch: {
        time: (batchEnd - batchStart).toFixed(2) + 'ms'
      }
    };
  }

  static generateReport(results: any) {
    const report = `
=== DATABASE PERFORMANCE REPORT ===
Generated: ${results.timestamp}

📊 DATABASE HEALTH:
- Status: ${results.database.health.healthy ? '✅ Healthy' : '❌ Unhealthy'}
- Message: ${results.database.health.message}

🔗 CONNECTION POOL:
- Total Connections: ${results.database.poolStats.totalCount}
- Idle Connections: ${results.database.poolStats.idleCount}
- Waiting Connections: ${results.database.poolStats.waitingCount}
- Max Connections: ${results.database.poolStats.max}

📈 DATABASE CONNECTIONS:
- Active: ${results.database.connections?.active || 'N/A'}
- Total: ${results.database.connections?.total || 'N/A'}
- Idle: ${results.database.connections?.idle || 'N/A'}
- Utilization: ${results.database.connections?.utilization ? results.database.connections.utilization.toFixed(1) + '%' : 'N/A'}

⚡ QUERY PERFORMANCE:
${results.performance.queries?.map((q: any) => `
  ${q.test}:
  - Avg: ${q.avgTime}
  - Min: ${q.minTime}
  - Max: ${q.maxTime}
  - Iterations: ${q.iterations}
`).join('') || 'No query performance data'}

🗄️ REDIS HEALTH:
- Status: ${results.redis.health.healthy ? '✅ Healthy' : '❌ Unhealthy'}
- Message: ${results.redis.health.message}

🚀 CACHE PERFORMANCE:
- Write Avg: ${results.performance.cache?.write.avgTime || 'N/A'}
- Read Avg: ${results.performance.cache?.read.avgTime || 'N/A'}
- Batch Time: ${results.performance.cache?.batch.time || 'N/A'}

🏥 SYSTEM HEALTH:
- Overall Status: ${results.system?.status || 'Unknown'}
- Database Status: ${results.system?.database?.healthy ? '✅ Healthy' : '❌ Unhealthy'}
- Redis Status: ${results.system?.redis?.healthy ? '✅ Healthy' : '❌ Unhealthy'}
- Uptime: ${results.system?.uptime ? Math.floor(results.system.uptime) + 's' : 'Unknown'}

📝 RECOMMENDATIONS:
${this.generateRecommendations(results)}
    `.trim();

    return report;
  }

  static generateRecommendations(results: any) {
    const recommendations = [];

    // Database recommendations
    if (results.database.connections?.utilization > 80) {
      recommendations.push('⚠️ Database connection utilization is high. Consider increasing pool size.');
    }

    if (results.database.connections?.active > 50) {
      recommendations.push('⚠️ High number of active database connections. Optimize queries or add caching.');
    }

    // Redis recommendations
    if (!results.redis.health.healthy) {
      recommendations.push('❌ Redis is unhealthy. Check Redis configuration and connectivity.');
    }

    // Performance recommendations
    if (results.performance.queries) {
      const slowQueries = results.performance.queries.filter((q: any) => 
        parseFloat(q.avgTime) > 100
      );
      
      if (slowQueries.length > 0) {
        recommendations.push('⚠️ Some queries are slow. Consider adding indexes or optimizing queries.');
      }
    }

    // Cache recommendations
    if (results.performance.cache?.read) {
      const readAvg = parseFloat(results.performance.cache.read.avgTime);
      if (readAvg > 10) {
        recommendations.push('⚠️ Cache read performance is slow. Check Redis configuration.');
      }
    }

    if (recommendations.length === 0) {
      recommendations.push('✅ All systems are performing well!');
    }

    return recommendations.join('\n');
  }
}

// Export for use in API routes or scripts
export default DatabasePerformanceTest;
