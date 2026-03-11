# Frontend & Admin Audit Report — Two Cycles

**Date:** 2025-03-11  
**Scope:** apps/web (frontend), apps/web-admin (admin)  
**Cycles:** 2 (identical checks each cycle)

## Cycle 1 vs Cycle 2

Cycle 2 produced no new findings. All findings below are from Cycle 1 and unchanged in Cycle 2.

---

## Frontend (apps/web)

### TypeScript
- **Error:** `src/components/ui/Button.tsx:54` — `SlotProps` children type incompatible with `ReactI18NextChildren | Iterable<ReactI18NextChildren>`. `Record<string, unknown>` not assignable to `ReactNode`.

### ESLint
- Passed (exit 0)

### Build
- Passed (`npx vite build`)

### Depcheck
- Unused: `@tanstack/react-virtual`; dev: `@axe-core/cli`, `autoprefixer`, `postcss`, `type-coverage`
- Missing: `playwright` (tests/debug-login.cjs), `@emotion/is-prop-valid` (vendor chunk)

### npm audit (--audit-level=high)
- **High:** robots-txt-guard (ReDoS), serialize-javascript (RCE)
- **Moderate:** esbuild, prismjs, tough-cookie
- **Fix:** `npm audit fix` for some; `--force` requires breaking changes

---

## Admin (apps/web-admin)

### TypeScript
- Passed (exit 0)

### ESLint
- No ESLint config found

### Build
- Passed (`npx vite build`)

### npm audit
- **Moderate:** esbuild (via vite)

---

## Conclusion

No new findings in Cycle 2. Report only; no fixes applied.
