import express from 'express';
import { startSEOIntegration, setupSEOHealthEndpoint } from './backend-integration.js';
import * as dotenv from 'dotenv';
import { seoLogger } from './logger.js';

dotenv.config();

const app = express();
const PORT = process.env.SEO_PORT || 3001;

// Setup health and diagnostics endpoints from backend-integration.ts
setupSEOHealthEndpoint(app);

app.get('/api/seo-status', (req, res) => {
    res.json({
        status: process.env.SEO_ENGINE_RUNNING ? 'running' : 'stopped',
        timestamp: new Date().toISOString()
    });
});

// Start integration daemon
seoLogger.info(`Starting standalone SEO Engine API Server...`);
startSEOIntegration();
process.env.SEO_ENGINE_RUNNING = 'true';

app.listen(PORT, () => {
    console.log(`🚀 SEO Engine Backend Route running on http://localhost:${PORT}`);
});
