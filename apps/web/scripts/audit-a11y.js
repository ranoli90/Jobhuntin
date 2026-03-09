#!/usr/bin/env node
/**
 * UI/UX & accessibility audit using @axe-core/cli (no sign-up).
 * Start the dev server first: npm run dev
 * Then: npm run audit:a11y
 * Or pass URL: node scripts/audit-a11y.js http://localhost:5173
 */
const { spawn } = require('child_process');
const url = process.argv[2] || 'http://127.0.0.1:5173';
console.log('Running axe-core accessibility audit on', url);
console.log('(Start dev server with "npm run dev" if not already running.)\n');
const child = spawn('npx', ['@axe-core/cli', url, '--exit'], {
  stdio: 'inherit',
  shell: true,
  cwd: require('path').resolve(__dirname, '..'),
});
child.on('close', (code) => process.exit(code ?? 0));
