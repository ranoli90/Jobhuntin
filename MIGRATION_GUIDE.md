# Supabase to Render PostgreSQL Migration Guide

## Overview
This guide walks you through migrating your JobHuntin application from Supabase to Render PostgreSQL.

## Prerequisites
- Render account with API access
- Your current Supabase database credentials
- Python 3.8+ with required packages

## Step 1: Create Render PostgreSQL Database

### Option A: Manual Creation (Recommended)
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New** → **PostgreSQL**
3. Enter the following:
   - **Name**: `jobhuntin-db`
   - **Region**: `Oregon` (same as your app)
   - **Plan**: `Free` (or `Standard` for production)
   - **Database Name**: `jobhuntin`
   - **User**: `jobhuntin_user`
4. Click **Create Database**
5. Wait for status to show **Live**
6. Copy the **Connection URL**

### Option B: Using API
```bash
python create_render_database.py
```

## Step 2: Update Configuration

The migration scripts have already updated your configuration files:

- `.env.example` - Updated for Render PostgreSQL
- `packages/shared/config.py` - Removed Supabase dependencies
- `apps/api/main.py` - Updated database connection logic
- `.env.render` - Template for Render environment

## Step 3: Update Environment Variables

In your Render service dashboard, update these environment variables:

```bash
# Database
DATABASE_URL=postgresql://jobhuntin_user:YOUR_PASSWORD@YOUR_HOST:5432/jobhuntin

# Remove all SUPABASE_* variables
# Keep other variables (LLM_API_KEY, STRIPE_*, etc.)
```

## Step 4: Run Migration

Execute the migration script:

```bash
python migrate_to_render.py "postgresql://jobhuntin_user:YOUR_PASSWORD@YOUR_HOST:5432/jobhuntin"
```

This will:
- Connect to both Supabase and Render databases
- Create the database schema on Render
- Migrate all data from Supabase tables
- Create a standalone users table (no auth.users dependency)

## Step 5: Update Application Code

The migration scripts have already updated the main configuration files. However, you may need to update:

1. **Authentication logic** - Remove Supabase auth dependencies
2. **Storage** - Update file storage if using Supabase Storage
3. **Realtime** - Remove Supabase realtime subscriptions

## Step 6: Test the Application

1. Deploy your updated application to Render
2. Test database connectivity
3. Verify all CRUD operations work
4. Test user authentication flow

## Step 7: Cleanup (Optional)

Once verified:

1. Delete Supabase project
2. Remove Supabase dependencies from requirements.txt
3. Clean up any remaining Supabase references

## Troubleshooting

### Connection Issues
- Verify DATABASE_URL format
- Check Render database status is "Live"
- Ensure IP allowlist includes your app

### Migration Issues
- Check logs for specific error messages
- Verify table schemas match
- Ensure foreign key constraints are handled

### Performance Issues
- Consider upgrading to Standard plan
- Add database indexes as needed
- Monitor connection pooling

## Database Schema Differences

### Supabase → Render Changes
- **Users table**: Now standalone (no auth.users reference)
- **RLS policies**: Removed (Render doesn't have Supabase RLS)
- **Realtime publications**: Removed
- **Auth system**: Needs replacement (consider JWT-only)

### New Users Table Structure
```sql
CREATE TABLE users (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email       text UNIQUE NOT NULL,
    full_name   text,
    avatar_url  text,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);
```

## Support

If you encounter issues:
1. Check Render dashboard for database status
2. Review application logs
3. Verify environment variables
4. Test database connection manually

## Next Steps

After migration:
1. Implement new authentication system
2. Set up monitoring and alerts
3. Configure backups
4. Update documentation
