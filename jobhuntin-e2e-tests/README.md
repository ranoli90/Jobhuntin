# JobHuntin Production E2E Suite (Playwright)

Comprehensive, production-safe Playwright coverage for all public pages on https://jobhuntin.com. Includes crawling-based discovery, accessibility (axe), performance metrics, visual regression, responsiveness, and multi-browser/device execution.

## Prerequisites
- Node.js 18+
- npm 8+

## Setup
```bash
npm install
```

Optional: set custom target via `.env`:
```
BASE_URL=https://jobhuntin.com
CRAWL_DEPTH=3
CRAWL_MAX_PAGES=60
```

## Key Scripts
- `npm test` — full suite (all projects)
- `npm run discover` — crawl and save URLs to `reports/discovered-urls.json`
- `npm run baseline` — create/update visual baselines
- `npm run test:accessibility` — axe-focused run
- `npm run test:performance` — performance checks
- `npm run test:responsive` — viewport snapshots
- `npm run test:chromium|firefox|webkit|mobile` — per-browser/device
- `npm run report` — open latest HTML report

## Visual Baselines
- Stored under `baselines/`
- First run: `npm run baseline`
- Update after intentional changes: `npm run baseline:update`

## Running Notes
- Tests are read-only: avoid form submissions and auth flows.
- Crawling stays within the jobhuntin.com domain and skips auth/log out patterns.
- Traces, screenshots, and videos for failures are in `test-results/` and `reports/html`.

## CI Tips
- Set `CI=1` to enable retries and limit workers.
- Artifacts: upload `reports/html`, `reports/results.json`, and `test-results/`.

## Troubleshooting
- Empty discovery: check network or adjust `BASE_URL/CRAWL_DEPTH/CRAWL_MAX_PAGES`.
- Visual diffs: regenerate baselines if changes are expected.
- Performance thresholds: tweak in `src/utils/performance.ts` if environment differs.
