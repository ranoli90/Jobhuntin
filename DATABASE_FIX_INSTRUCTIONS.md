# DATABASE_URL FIX - INSTRUCTIONS

## 🚨 ROOT CAUSE IDENTIFIED

The application is failing because **DATABASE_URL environment variable is missing** or misconfigured from the Render service.

## 📋 Error Analysis

From the logs:
```
DB pool attempt 1/3 failed: Tenant or user not found. This usually means DATABASE_URL credentials are incorrect.
Could not create DB pool after 3 attempts. The application will start in degraded mode without database connectivity.
```

## 🔧 IMMEDIATE FIX REQUIRED

### Step 1: Go to Render Dashboard
1. Visit: https://dashboard.render.com
2. Login with your credentials

### Step 2: Navigate to API Service
1. Find service: `jobhuntin-api`
2. Click on the service name

### Step 3: Add Environment Variable
1. Click on the **"Environment"** tab
2. Click **"Add Environment Variable"**
3. Enter the following:

**Key:** `DATABASE_URL`

**Value:** Configure with your Render PostgreSQL connection string

### Step 4: Save and Redeploy
1. Click **"Save Changes"**
2. Click **"Manual Deploy"** → **"Deploy Latest Commit"**

## 🎯 ALTERNATIVE: CREATE RENDER DATABASE

If you need a new database:

### Option A: Create Render PostgreSQL Database
1. In Render Dashboard, click **"New"** → **"PostgreSQL"**
2. Choose a name (e.g., `jobhuntin-db`)
3. Select the same region as your app
4. Click **"Create Database"**

### Option B: Update DATABASE_URL
Once created, Render will provide a connection string like:
```
postgresql://user:password@host:port/database
```

Use this as your DATABASE_URL.

## 🔍 Verification

After setting DATABASE_URL:

1. Check the logs in Render dashboard
2. Look for successful database connection messages:
   ```
   DB pool created successfully
   Database connectivity established
   ```

3. Test API endpoints that require database access

## 🚀 Next Steps

1. Add the DATABASE_URL environment variable
2. Monitor the deployment logs
3. Test database connectivity
4. Verify all API endpoints work correctly
