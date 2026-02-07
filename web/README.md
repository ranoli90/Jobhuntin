# Fizzl Web

## Local development
1. `npm install`
2. Create a `.env` file with `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, and `VITE_API_URL`.
3. `npm run dev`

Vite will boot on http://localhost:5173.

## Supabase + API integration
- `src/lib/supabase.ts` uses the `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` variables. Provide production creds in Render.
- `src/hooks/usePlan.ts` reads `VITE_API_URL` (defaults to empty string). Point it at your FastAPI base to share billing state.

## Next screens to build
1. **Applications list:** sortable HOLD table with action menu.
2. **HOLD inbox:** timeline cards showing nudges, notes, and worker events.
3. **Upgrade flow:** billing modal surfaced from plan badge to manage Stripe checkout.
