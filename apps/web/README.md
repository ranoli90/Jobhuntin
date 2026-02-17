# JobHuntin Web

## Local development
1. `npm install`
2. Create a `.env` file with `VITE_API_URL` (pointing to your FastAPI backend).
3. `npm run dev`

Vite will boot on http://localhost:5173.

## API integration
- Authentication is handled via magic links through the backend API.
- `src/lib/api.ts` reads `VITE_API_URL` for all backend requests.
- `src/hooks/usePlan.ts` reads `VITE_API_URL` (defaults to empty string). Point it at your FastAPI base to share billing state.

## Next screens to build
1. **Applications list:** sortable table with action menu.
2. **Inbox:** timeline cards showing nudges, notes, and worker events.
3. **Upgrade flow:** billing modal surfaced from plan badge to manage Stripe checkout.
