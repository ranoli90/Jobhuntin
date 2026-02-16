import pool from './database';
import redis, { CacheService } from './redis';

// Database metrics collection
export class DatabaseMetrics {
  static async getConnectionStats() {
    try {
      const totalQuery = 'SELECT count(*) FROM pg_stat_activity';
      const activeQuery = "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'";
      const idleQuery = "SELECT count(*) FROM pg_stat_activity WHERE state = 'idle'";
      
      const [total, active, idle] = await Promise.all([
        pool.query(totalQuery),
        pool.query(activeQuery),
        pool.query(idleQuery)
      ]);

      return {
        total: parseInt(total.rows[0].count),
        active: parseInt(active.rows[0].count),
        idle: parseInt(idle.rows[0].count),
        maxConnections: 103,
        utilization: (parseInt(total.rows[0].count) / 103) * 100,
        poolStats: {
          totalCount: pool.totalCount,
          idleCount: pool.idleCount,
          waitingCount: pool.waitingCount,
          max: pool.options.max
        }
      };
    } catch (error) {
      console.error('Error getting connection stats:', error);
      return null;
    }
  }

  static async getSlowQueries() {
    try {
      const query = `
        SELECT query, mean_time, calls, total_time
        FROM pg_stat_statements 
        ORDER BY mean_time DESC 
        LIMIT 10
      `;
      
      const result = await pool.query(query);
      return result.rows;
    } catch (error) {
      console.error('Error getting slow queries:', error);
      return [];
    }
  }

  static async getDatabaseSize() {
    try {
      const query = `
        SELECT 
          pg_size_pretty(pg_database_size(current_database())) as database_size,
          pg_size_pretty(pg_total_relation_size('pg_stat_statements')) as stats_size
      `;
      
      const result = await pool.query(query);
      return result.rows[0];
    } catch (error) {
      console.error('Error getting database size:', error);
      return null;
    }
  }

  static async getTableStats() {
    try {
      const query = `
        SELECT 
          schemaname,
          tablename,
          n_tup_ins as inserts,
          n_tup_upd as updates,
          n_tup_del as deletes,
          n_live_tup as live_tuples,
          n_dead_tup as dead_tuples,
          last_vacuum,
          last_autovacuum,
          last_analyze,
          last_autoanalyze
        FROM pg_stat_user_tables 
        ORDER BY n_live_tup DESC
        LIMIT 20
      `;
      
      const result = await pool.query(query);
      return result.rows;
    } catch (error) {
      console.error('Error getting table stats:', error);
      return [];
    }
  }

  static async getIndexStats() {
    try {
      const query = `
        SELECT 
          schemaname,
          tablename,
          indexname,
          idx_scan as index_scans,
          idx_tup_read as tuples_read,
          idx_tup_fetch as tuples_fetched
        FROM pg_stat_user_indexes 
        ORDER BY idx_scan DESC
        LIMIT 20
      `;
      
      const result = await pool.query(query);
      return result.rows;
    } catch (error) {
      console.error('Error getting index stats:', error);
      return [];
    }
  }
}

// Cache metrics collection
export class CacheMetrics {
  static async getRedisStats() {
    try {
      const info = await redis.info();
      const lines = info.split('\r\n');
      const stats: Record<string, any> = {};
      
      lines.forEach((line: string) => {
        if (line.includes(':')) {
          const [key, value] = line.split(':');
          stats[key] = value;
        }
      });

      return {
        connected_clients: parseInt(stats.connected_clients || '0'),
        used_memory: stats.used_memory_human,
        used_memory_peak: stats.used_memory_peak_human,
        total_commands_processed: parseInt(stats.total_commands_processed || '0'),
        total_connections_received: parseInt(stats.total_connections_received || '0'),
        keyspace_hits: parseInt(stats.keyspace_hits || '0'),
        keyspace_misses: parseInt(stats.keyspace_misses || '0'),
        hit_rate: stats.keyspace_hits && stats.keyspace_misses 
          ? (parseInt(stats.keyspace_hits) / (parseInt(stats.keyspace_hits) + parseInt(stats.keyspace_misses)) * 100).toFixed(2)
          : '0'
      };
    } catch (error) {
      console.error('Error getting Redis stats:', error);
      return null;
    }
  }

  static async getCacheKeyStats(pattern: string = '*') {
    try {
      const keys = await redis.keys(pattern);
      const keyTypes = await Promise.all(
        keys.map((key: string) => redis.type(key))
      );
      
      const typeCount: Record<string, number> = {};
      keyTypes.forEach((type: string) => {
        typeCount[type] = (typeCount[type] || 0) + 1;
      });

      return {
        totalKeys: keys.length,
        typeDistribution: typeCount,
        sampleKeys: keys.slice(0, 10)
      };
    } catch (error) {
      console.error('Error getting cache key stats:', error);
      return null;
    }
  }
}

// Application health check
export class HealthMonitor {
  static async getFullHealthStatus() {
    const cacheService = CacheService.getInstance();
    
    try {
      const [dbHealth, redisHealth, dbStats, redisStats] = await Promise.all([
        pool.query('SELECT 1 as health_check'),
        cacheService.healthCheck(),
        DatabaseMetrics.getConnectionStats(),
        CacheMetrics.getRedisStats()
      ]);

      return {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        database: {
          healthy: true,
          stats: dbStats,
          connections: dbStats?.poolStats || {}
        },
        redis: {
          healthy: redisHealth.healthy,
          stats: redisStats
        },
        uptime: process.uptime(),
        memory: process.memoryUsage()
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Unknown error',
        uptime: process.uptime(),
        memory: process.memoryUsage()
      };
    }
  }

  static async getPerformanceMetrics() {
    try {
      const [dbStats, redisStats, slowQueries, tableStats] = await Promise.all([
        DatabaseMetrics.getConnectionStats(),
        CacheMetrics.getRedisStats(),
        DatabaseMetrics.getSlowQueries(),
        DatabaseMetrics.getTableStats()
      ]);

      return {
        timestamp: new Date().toISOString(),
        database: {
          connections: dbStats,
          slowQueries: slowQueries.slice(0, 5),
          tableStats: tableStats.slice(0, 10)
        },
        redis: redisStats,
        system: {
          uptime: process.uptime(),
          memory: process.memoryUsage(),
          cpu: process.cpuUsage()
        }
      };
    } catch (error) {
      console.error('Error getting performance metrics:', error);
      return {
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
}

// Alert thresholds
export const ALERT_THRESHOLDS = {
  database: {
    connectionUtilization: 80, // percentage
    slowQueryThreshold: 1000, // milliseconds
    maxConnections: 90 // percentage of max
  },
  redis: {
    memoryUtilization: 80, // percentage
    hitRate: 90, // minimum percentage
    connectionCount: 100 // maximum connections
  },
  system: {
    memoryUtilization: 80, // percentage
    uptime: 0 // minimum uptime in seconds
  }
};

// Alert checker
export class AlertChecker {
  static async checkAlerts() {
    const metrics = await HealthMonitor.getPerformanceMetrics();
    const alerts: string[] = [];

    // Database alerts
    if (metrics.database?.connections?.utilization && metrics.database.connections.utilization > ALERT_THRESHOLDS.database.connectionUtilization) {
      alerts.push(`Database connection utilization high: ${metrics.database.connections.utilization.toFixed(1)}%`);
    }

    if (metrics.database?.slowQueries && metrics.database.slowQueries.length > 0) {
      const slowest = metrics.database.slowQueries[0];
      if (parseFloat(slowest.mean_time) > ALERT_THRESHOLDS.database.slowQueryThreshold) {
        alerts.push(`Slow query detected: ${slowest.mean_time}ms average`);
      }
    }

    // Redis alerts
    if (metrics.redis?.hit_rate && parseFloat(metrics.redis.hit_rate) < ALERT_THRESHOLDS.redis.hitRate) {
      alerts.push(`Redis hit rate low: ${metrics.redis.hit_rate}%`);
    }

    if (metrics.redis?.connected_clients && metrics.redis.connected_clients > ALERT_THRESHOLDS.redis.connectionCount) {
      alerts.push(`Redis connection count high: ${metrics.redis.connected_clients}`);
    }

    // System alerts
    if (metrics.system?.memory) {
      const memoryUtilization = (metrics.system.memory.heapUsed / metrics.system.memory.heapTotal) * 100;
      if (memoryUtilization > ALERT_THRESHOLDS.system.memoryUtilization) {
        alerts.push(`Memory utilization high: ${memoryUtilization.toFixed(1)}%`);
      }
    }

    return {
      timestamp: new Date().toISOString(),
      alerts,
      metrics
    };
  }
}

export default {
  DatabaseMetrics,
  CacheMetrics,
  HealthMonitor,
  AlertChecker
};
