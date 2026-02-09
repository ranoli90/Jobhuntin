# Magic Link Troubleshooting & Verification Report

## Summary
The magic link functionality on the Login and Homepage has been enhanced to provide better error messages and robust logging. Automated tests have been added to verify the client-side logic.

## Configuration Checklist
To ensure the magic link works in production (and local development), you must verify the following configurations:

### 1. Environment Variables
Ensure these variables are set in your `.env` (local) or Render.com Environment:

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_SUPABASE_URL` | Your Supabase Project URL | `https://xyz.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | Your Supabase Anon/Public Key | `eyJhbG...` |
| `VITE_APP_BASE_URL` | The URL of your app (important for redirects) | `https://your-app.onrender.com` |

> **Critical**: If `VITE_APP_BASE_URL` is missing, the app defaults to `window.location.origin`. This usually works, but explicit configuration is safer for email links.

### 2. Supabase Dashboard Settings
1.  Go to **Authentication** > **URL Configuration**.
2.  **Site URL**: Set this to your production URL (e.g., `https://your-app.onrender.com`).
3.  **Redirect URLs**: Add the following whitelisted paths:
    *   `http://localhost:5173/**` (for local dev)
    *   `https://your-app.onrender.com/**` (for production)
    *   **Crucial**: Ensure `https://your-app.onrender.com/login` is allowed, as the magic link redirects there first.

### 3. Email Templates
1.  Go to **Authentication** > **Email Templates** > **Magic Link**.
2.  Ensure the template uses the `{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=magiclink` pattern or similar.
3.  Supabase handles the construction, but ensure the link in the email is clickable.

## Debugging
If users report issues:
1.  Open the **Browser Console** (F12).
2.  Look for logs starting with `[MagicLink]`.
3.  You will see:
    *   `Target Email`
    *   `Origin`
    *   `Return To`
    *   `Full Redirect URL`
4.  If the **Supabase Error** group appears, check the `Message` and `Status`.
    *   `Status: 429` -> Rate limit exceeded.
    *   `Status: 400` or `422` -> Invalid configuration or redirect URL.

## Automated Tests
A new test suite has been added: `web/tests/magic_link.spec.ts`.
Run it with:
```bash
cd web
npx playwright test tests/magic_link.spec.ts
```
This test mocks the Supabase API to verify the frontend correctly handles:
*   Successful request submission.
*   API errors (displaying them to the user).
*   Input validation.
