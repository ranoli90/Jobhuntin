// Backend Integration for Render Deployment
// Add this to your main server file (e.g., server.js, app.js, or main backend file)

import { startSEOIntegration, getSEOHealth } from './scripts/seo/backend-integration.js';

// Add this at the start of your backend initialization
console.log('🚀 Starting backend with SEO integration...');

// Start the SEO engine when your backend starts
startSEOIntegration();

// Optional: Add a health check endpoint
app.get('/api/seo-health', (req, res) => {
  const health = getSEOHealth();
  res.json(health);
});

// Your existing backend code continues below...

/* 
DEPLOYMENT INSTRUCTIONS FOR RENDER:

1. Add these environment variables in your Render dashboard:
   - GOOGLE_SERVICE_ACCOUNT_KEY: Paste the entire JSON content from your service account file
   - GOOGLE_SEARCH_CONSOLE_SITE: https://jobhuntin.com
   - NODE_ENV: production

2. Update your package.json scripts section:
   "scripts": {
     "start": "node your-main-server-file.js && npm run seo:backend",
     "seo:backend": "npx tsx scripts/seo/backend-integration.ts"
   }

3. The SEO engine will automatically start when your backend deploys

4. Monitor the logs in Render dashboard - you'll see SEO engine activity

5. Check indexing status with: npm run seo:verify
*/