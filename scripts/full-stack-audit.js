#!/usr/bin/env node
/**
 * Full-stack repo audit runner (no sign-up tools only).
 * Runs: TypeScript, ESLint, depcheck, knip, npm audit, type-coverage (web);
 *       ruff, mypy, bandit, pip-audit, vulture, radon, semgrep, detect-secrets, deptry (Python);
 *       hadolint (Docker).
 * Usage: node scripts/full-stack-audit.js [--skip-install]
 * Output: audit-report-<timestamp>.txt
 */

const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const WEB_DIR = path.join(ROOT, 'apps', 'web');
const REPORT = path.join(ROOT, `audit-report-${Date.now()}.txt`);
const skipInstall = process.argv.includes('--skip-install');

const out = { lines: [] };
function log(msg) {
  const line = typeof msg === 'string' ? msg : JSON.stringify(msg);
  out.lines.push(line);
  console.log(line);
}

function run(name, cmd, args, cwd = ROOT, env = {}) {
  log(`\n${'='.repeat(60)}`);
  log(`AUDIT: ${name}`);
  log(`${'='.repeat(60)}\n`);
  const result = spawnSync(cmd, args, {
    cwd,
    encoding: 'utf8',
    shell: true,
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env, ...env },
  });
  const stdout = (result.stdout || '').trim();
  const stderr = (result.stderr || '').trim();
  if (stdout) log(stdout);
  if (stderr) log(stderr);
  if (result.status !== 0) log(`Exit code: ${result.status}`);
  return result.status;
}

function runOptional(name, cmd, args, cwd = ROOT, env = {}) {
  log(`\n--- ${name} ---`);
  const result = spawnSync(cmd, args, {
    cwd,
    encoding: 'utf8',
    shell: true,
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env, ...env },
  });
  const stdout = (result.stdout || '').trim();
  const stderr = (result.stderr || '').trim();
  if (stdout) log(stdout);
  if (stderr) log(stderr);
  return result.status;
}

function main() {
  log('FULL-STACK AUDIT REPORT');
  log('Generated: ' + new Date().toISOString());
  let hasErrors = false;

  // --- Frontend (apps/web) ---
  if (!skipInstall) {
    log('\nInstalling web dependencies...');
    run('npm install (web)', 'npm', ['install', '--no-audit', '--no-fund'], WEB_DIR);
  }

  log('\n--- FRONTEND AUDITS (apps/web) ---');
  if (run('TypeScript (tsc --noEmit)', 'npx', ['tsc', '--noEmit'], WEB_DIR) !== 0) hasErrors = true;
  if (run('ESLint', 'npx', ['eslint', 'src', '--ext', '.ts,.tsx', '--max-warnings', '99999'], WEB_DIR) !== 0) hasErrors = true;
  runOptional('Depcheck (unused deps)', 'npx', ['depcheck', '--ignores=@types/*,eslint-plugin-*,eslint-config-*,eslint-import-resolver-*,react-hook-form,react-syntax-highlighter,undraw-svg,zod,redis,@types/redis,react-i18next'], WEB_DIR);
  runOptional('Knip (dead code)', 'npx', ['knip', '--no-exit-code'], WEB_DIR);
  runOptional('Type coverage', 'npx', ['type-coverage', '--strict', '--at-least', '90'], WEB_DIR);
  if (run('npm audit', 'npm', ['audit', '--audit-level=high'], WEB_DIR) !== 0) hasErrors = true;

  // --- Backend (Python) ---
  log('\n--- BACKEND AUDITS (Python) ---');
  const py = process.platform === 'win32' ? 'python' : 'python3';
  if (run('Ruff (lint)', py, ['-m', 'ruff', 'check', 'apps', 'packages', 'shared', 'scripts', '--select', 'E,W,F,I', '--ignore', 'E501,E402', '--output-format', 'concise']) !== 0) hasErrors = true;
  if (run('Mypy (types)', py, ['-m', 'mypy', 'apps/api/', 'apps/worker/', 'packages/backend/', 'shared/', '--ignore-missing-imports', '--no-error-summary'], ROOT, { PYTHONPATH: 'apps:packages:.' }) !== 0) hasErrors = true;
  if (run('Bandit (security)', py, ['-m', 'bandit', '-c', 'pyproject.toml', '-r', 'apps', 'packages', 'shared', 'scripts', '-x', '.venv,node_modules,__pycache__', '-f', 'txt', '-q']) !== 0) hasErrors = true;
  if (run('pip-audit (vulns)', py, ['-m', 'pip_audit', '-r', 'requirements.txt', '-r', 'requirements-dev.txt']) !== 0) hasErrors = true;
  runOptional('Semgrep (security/bugs)', py, ['-m', 'semgrep', 'scan', '--config', 'auto', '--metrics=off', 'apps', 'packages', 'shared', 'scripts']);
  runOptional('Vulture (dead code)', py, ['-m', 'vulture', 'apps', 'packages', 'shared', 'scripts', '--min-confidence', '80']);
  runOptional('Radon (complexity)', py, ['-m', 'radon', 'cc', 'apps', 'packages', 'shared', '-a', '-s', '--total-average']);
  runOptional('Deptry (deps)', py, ['-m', 'deptry', '.', '--no-cache']);
  runOptional('Detect-secrets (secrets)', py, ['-m', 'detect_secrets', 'scan', 'apps', 'packages', 'shared', 'scripts', '--all-files']);

  // --- Docker ---
  log('\n--- DOCKER AUDITS ---');
  runOptional('Hadolint (Dockerfile)', 'docker', ['run', '--rm', '-v', `${ROOT}:/app`, '-w', '/app', 'hadolint/hadolint', 'hadolint', 'Dockerfile'], ROOT);

  log('\n' + '='.repeat(60));
  log(hasErrors ? 'AUDIT COMPLETE (some checks reported issues)' : 'AUDIT COMPLETE (all checks passed or non-blocking)');
  log('='.repeat(60));

  fs.writeFileSync(REPORT, out.lines.join('\n'), 'utf8');
  log(`\nReport written to: ${REPORT}`);
  process.exit(hasErrors ? 1 : 0);
}

main();
