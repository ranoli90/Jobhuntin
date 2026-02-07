# Database Migrations

SQL-first migrations compatible with Supabase.

## Running locally

```bash
# Option A: Supabase CLI (if using supabase local)
supabase db reset          # applies schema.sql + all migrations

# Option B: Plain psql against a vanilla Postgres
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/sorce"

# Apply base schema first
psql "$DATABASE_URL" -f supabase/schema.sql

# Then run migrations in order
for f in supabase/migrations/0*.sql; do
  echo "Applying $f ..."
  psql "$DATABASE_URL" -f "$f"
done
```

## Conventions

- Files are numbered `NNN_description.sql` and run in lexicographic order.
- Each migration is idempotent (`IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`).
- New enum values use `ADD VALUE IF NOT EXISTS` for forward-compatibility.
- Never remove columns or enum values in a migration; deprecate them instead.
- JSON fields (`meta`, `payload`, `profile_data`) are read with `.get()` defaults
  so new keys don't break old code.
