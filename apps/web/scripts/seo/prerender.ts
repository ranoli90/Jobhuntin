
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { chromium } from '@playwright/test';
import { preview } from 'vite';
import prerenderRoutes from '../../prerender.config';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DIST_DIR = path.resolve(__dirname, '../../dist');

async function prerender() {
    console.log('🚀 Starting Prerendering Process...');

    if (!fs.existsSync(DIST_DIR)) {
        console.error('❌ dist/ directory not found. Please run "npm run build" first.');
        process.exit(1);
    }

    // Start Vite Preview Server
    console.log('📦 Starting preview server...');
    const server = await preview({
        root: path.resolve(__dirname, '../../'),
        build: { outDir: 'dist' },
        preview: { port: 4173, open: false },
        configFile: path.resolve(__dirname, '../../vite.config.ts'),
        mode: 'production',
    });

    const baseUrl = server.resolvedUrls?.local[0] || 'http://localhost:4173';
    console.log(`✅ Preview server running at ${baseUrl}`);

    const browser = await chromium.launch();
    const context = await browser.newContext();
    const page = await context.newPage();

    let successCount = 0;
    let errorCount = 0;

    for (const route of prerenderRoutes) {
        try {
            const url = `${baseUrl}${route === '/' ? '' : route}`;
            console.log(`📄 Prerendering: ${route}...`);

            await page.goto(url, { waitUntil: 'networkidle' });

            // Wait for any client-side hydration or specific elements if needed
            // await page.waitForSelector('#root'); 

            const content = await page.content();

            // Calculate file path
            // e.g. / -> index.html
            // e.g. /about -> about/index.html
            // e.g. /jobs/marketing/denver -> jobs/marketing/denver/index.html

            const routePath = route.startsWith('/') ? route.slice(1) : route;
            const OUT_DIR = path.join(DIST_DIR, routePath);

            if (!fs.existsSync(OUT_DIR)) {
                fs.mkdirSync(OUT_DIR, { recursive: true });
            }

            const filePath = path.join(OUT_DIR, 'index.html');

            // Inject a marker to verify prerendering
            const finalHtml = content.replace(
                '<head>',
                '<head><meta name="prerendered" content="true"><meta name="prerender-time" content="' + new Date().toISOString() + '">'
            ); // Timestamped injection for verification

            fs.writeFileSync(filePath, finalHtml);
            successCount++;
        } catch (e) {
            console.error(`❌ Failed to prerender ${route}:`, e);
            errorCount++;
        }
    }

    await browser.close();
    server.httpServer.close();

    console.log(`\n✨ Prerendering Complete!`);
    console.log(`   Success: ${successCount}`);
    console.log(`   Errors: ${errorCount}`);
}

prerender().catch(console.error);
