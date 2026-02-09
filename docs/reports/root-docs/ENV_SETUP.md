---
title: Environment setup (Supabase & Render)
description: Safe variable checklist for web, web-admin, and mobile clients (no secrets committed).
---

## Web (Vite)
Create `web/.env` (or set in Render dashboard for the web service):
```
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
# Recommended to avoid redirect mismatches
VITE_APP_BASE_URL=https://your-domain
```

## Web Admin (Vite)
Create `web-admin/.env`:
```
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
# Optional: override localhost default
VITE_APP_BASE_URL=https://your-domain
```

## Mobile (Expo)
In `app.config.js` or Expo secrets:
```
EXPO_PUBLIC_SUPABASE_URL=
EXPO_PUBLIC_SUPABASE_ANON_KEY=
```

## Supabase auth redirect allowlist
Add to Supabase Dashboard → Authentication → URL Configuration:
- `https://your-domain/login`
- `https://your-domain` (root)
- Local dev: `http://localhost:5173`, `http://localhost:4173` (Vite dev/preview)
- Web-admin dev: `http://localhost:5174` (adjust if different)

## Render deployment notes
- Ensure the above env vars are set on the Render service (Build & Runtime). Do NOT store service keys in client apps; only anon keys belong here.
- If using `appBaseUrl` in code, set `VITE_APP_BASE_URL` to the canonical Render URL or your custom domain.

## Safety reminders
- Never commit real keys; use deploy-time env vars.
- Anon key only on clients; service role keys stay server-side only (none are used in this repo clients).
- If rate-limit errors occur, Supabase 429 retry hints are now respected; ensure clocks/timezones are sane on client devices.
