import { Pool } from 'pg';

// Database connection pool configuration
const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://jobhuntin_user:60BpsY53MYOO4fGFlvZKwDpiXB9Up9lL@dpg-d66ck524d50c73bas62g-a.oregon-postgres.render.com/jobhuntin',
  max: 20, // Maximum number of connections in the pool
  idleTimeoutMillis: 30000, // How long a client is allowed to remain idle before being closed
  connectionTimeoutMillis: 2000, // How long to wait when connecting a new client
  ssl: {
    rejectUnauthorized: false // Required for Render PostgreSQL
  }
});

// Pool event listeners for monitoring
pool.on('connect', (client) => {
  console.log('New database connection established');
});

pool.on('acquire', (client) => {
  console.log('Database connection acquired from pool');
});

pool.on('remove', (client) => {
  console.log('Database connection removed from pool');
});

pool.on('error', (err, client) => {
  console.error('Database pool error:', err);
});

// Query wrapper with timing and error handling
export async function query(text: string, params?: any[]) {
  const start = Date.now();
  try {
    const client = await pool.connect();
    try {
      const res = await client.query(text, params);
      const duration = Date.now() - start;
      console.log('Database query executed', { 
        query: text.substring(0, 100), 
        duration: `${duration}ms`, 
        rows: res.rowCount 
      });
      return res;
    } finally {
      client.release();
    }
  } catch (error) {
    const duration = Date.now() - start;
    console.error('Database query error', { 
      query: text.substring(0, 100), 
      duration: `${duration}ms`, 
      error: error instanceof Error ? error.message : 'Unknown error'
    });
    throw error;
  }
}

// Transaction helper
export async function transaction<T>(callback: (client: any) => Promise<T>): Promise<T> {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const result = await callback(client);
    await client.query('COMMIT');
    return result;
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  } finally {
    client.release();
  }
}

// Health check function
export async function healthCheck() {
  try {
    const result = await query('SELECT 1 as health_check');
    return { 
      healthy: true, 
      message: 'Database connection successful',
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    return { 
      healthy: false, 
      message: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString()
    };
  }
}

// Get pool statistics
export function getPoolStats() {
  return {
    totalCount: pool.totalCount,
    idleCount: pool.idleCount,
    waitingCount: pool.waitingCount,
    max: pool.options.max
  };
}

// Graceful shutdown
export async function closePool() {
  await pool.end();
  console.log('Database connection pool closed');
}

export default pool;
