# SUPABASE DATABASE FIX

## Issue: Invalid Supabase Credentials
The DATABASE_URL exists but contains wrong credentials. Connection test shows:
```
FATAL: Tenant or user not found
```

## Solution: Get Correct Credentials

1. **Go to Supabase Dashboard**
   - Visit: https://supabase.com/dashboard
   - Sign in with your account

2. **Find Your Project**
   - Project ID: `zglovpfwyobbbaaocawz`
   - If this project doesn't exist, you may need to create a new one

3. **Get Database Connection String**
   - Go to: Settings → Database
   - Copy the "Connection pooling" connection string
   - It should look like: `postgresql://postgres.[project-ref]:[password]@aws-0-us-east-1.pooler.supabase.com:5432/postgres`

4. **Update DATABASE_URL in Render**
   - Go to Render dashboard → jobhuntin-api → Environment
   - Update DATABASE_URL with the correct connection string from Supabase
   - Remove the DATABASE_URLh entry (the typo)
   - Save and redeploy

## Alternative: Reset Supabase Project
If the project is lost/corrupted:
1. Create new Supabase project
2. Get new connection string
3. Update DATABASE_URL in Render
4. Run database migrations if needed

## Verification
After updating, redeploy and check logs for:
```
DB pool created successfully
Database connectivity established
```
