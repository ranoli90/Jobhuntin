# Database Connection Fix

## Issue: Invalid Database Credentials
The DATABASE_URL exists but contains wrong credentials. Connection test shows:
```
FATAL: Tenant or user not found
```

## Solution: Get Correct Credentials

1. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com
   - Sign in with your account

2. **Find Your Database**
   - Navigate to your PostgreSQL database service
   - Click on the database to view details

3. **Get Database Connection String**
   - Go to the database details page
   - Copy the "Internal Connection String" or "External Connection String"
   - The format should be: `postgresql://user:password@host:port/database`

4. **Update DATABASE_URL in Render**
   - Go to your API service → Environment tab
   - Update DATABASE_URL with the correct connection string
   - Save and redeploy

## Alternative: Create New Database
If the database is lost/corrupted:
1. Create new Render PostgreSQL database
2. Get new connection string
3. Update DATABASE_URL in your API service
4. Run database migrations if needed

## Verification
After updating, redeploy and check logs for:
```
DB pool created successfully
Database connectivity established
```
