# Backup Strategy

## Overview

This document outlines the backup strategy for the JobHuntin platform infrastructure on Render.

---

## Current Backup Configuration

### PostgreSQL Database (jobhuntin-db)

| Setting | Value | Notes |
|---------|-------|-------|
| Plan | Basic 256MB | Starter tier |
| Point-in-Time Recovery (PITR) | ❌ Not available | Requires Standard plan ($7/mo) |
| Automated Backups | ❌ Not available | Requires Standard plan |
| Manual Backups | Via Render API | See scripts below |

### Redis (jobhuntin-redis)

| Setting | Value | Notes |
|---------|-------|-------|
| Plan | Free | Starter tier |
| Persistence | ❌ Not available | Data is in-memory only |
| Backup | Not supported | Render Redis Free is ephemeral |

---

## Recommended Backup Strategy

### Option 1: Upgrade Render PostgreSQL (Recommended)

Upgrade to **Standard** plan ($7/mo) for:
- Point-in-Time Recovery (7-day window)
- Automated daily backups
- High Availability option

**Steps:**
1. Go to Render Dashboard → Database → Info
2. Click "Change Plan"
3. Select "Standard"
4. Confirm upgrade (brief downtime ~30s)

### Option 2: Self-Managed Backups (Current Plan)

Since we're on the Basic plan, implement manual backups:

```bash
# Daily backup script
pg_dump "postgresql://jobhuntin_user:PASSWORD@dpg-d66ck524d50c73bas62g-a.oregon-postgres.render.com/jobhuntin" \
  --format=custom \
  --file="backup_$(date +%Y%m%d_%H%M%S).dump"
```

---

## Backup Schedule

| Type | Frequency | Retention | Location |
|------|-----------|-----------|----------|
| Database dump | Daily | 7 days | S3/R2 |
| Config backup | Weekly | 30 days | GitHub (private repo) |
| Environment vars | On change | 90 days | 1Password |

---

## Backup Scripts

### Automated Daily Database Backup

Create `scripts/backup_database.py`:

```python
#!/usr/bin/env python
"""
Daily database backup script.
Run via cron or Render cron job.
"""

import os
import subprocess
from datetime import datetime
import boto3

DATABASE_URL = os.environ.get("DATABASE_URL")
BACKUP_BUCKET = os.environ.get("BACKUP_BUCKET", "jobhuntin-backups")

def create_backup():
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"jobhuntin_{timestamp}.dump"
    
    # Create pg_dump
    subprocess.run([
        "pg_dump", DATABASE_URL,
        "--format=custom",
        "--file", filename
    ], check=True)
    
    # Upload to S3/R2
    s3 = boto3.client("s3")
    s3.upload_file(filename, BACKUP_BUCKET, f"database/{filename}")
    
    # Cleanup local file
    os.remove(filename)
    
    print(f"Backup created: {filename}")
    return filename

def cleanup_old_backups():
    """Remove backups older than 7 days."""
    s3 = boto3.client("s3")
    cutoff = datetime.utcnow().timestamp() - (7 * 24 * 60 * 60)
    
    response = s3.list_objects_v2(Bucket=BACKUP_BUCKET, Prefix="database/")
    
    for obj in response.get("Contents", []):
        if obj["LastModified"].timestamp() < cutoff:
            s3.delete_object(Bucket=BACKUP_BUCKET, Key=obj["Key"])
            print(f"Deleted old backup: {obj['Key']}")

if __name__ == "__main__":
    create_backup()
    cleanup_old_backups()
```

---

## Restore Procedures

### Restore from pg_dump

```bash
# Download backup from S3
aws s3 cp s3://jobhuntin-backups/database/jobhuntin_20260213.dump .

# Restore to database
pg_restore \
  --dbname="postgresql://jobhuntin_user:PASSWORD@dpg-d66ck524d50c73bas62g-a.oregon-postgres.render.com/jobhuntin" \
  --clean \
  --if-exists \
  jobhuntin_20260213.dump
```

### Point-in-Time Recovery (PITR)

Available with Standard plan:

1. Go to Render Dashboard → Database
2. Click "Restore to Point in Time"
3. Select target timestamp
4. Render creates new database instance
5. Update DATABASE_URL in services
6. Verify data integrity
7. Delete old database (optional)

---

## Backup Verification

Weekly backup integrity check:

```bash
# Create test database
createdb test_restore

# Restore backup to test database
pg_restore --dbname=test_restore backup.dump

# Verify table counts
psql test_restore -c "SELECT table_name, n_live_tup FROM pg_stat_user_tables;"

# Cleanup
dropdb test_restore
```

---

## Environment Variable Backup

Store critical secrets in a secure password manager:

| Variable | Location |
|----------|----------|
| DATABASE_URL | 1Password, Render |
| JWT_SECRET | 1Password, Render |
| REDIS_URL | 1Password, Render |
| LLM_API_KEY | 1Password, Render |
| STRIPE_SECRET_KEY | 1Password, Render |
| RENDER_API_KEY | 1Password, GitHub |

---

## Monitoring Backup Health

Add to health check:

```python
@app.get("/healthz")
async def healthz():
    # Check backup freshness
    last_backup = await get_last_backup_time()
    backup_age_hours = (datetime.utcnow() - last_backup).total_seconds() / 3600
    
    if backup_age_hours > 26:  # More than 26 hours = missed backup
        return {"status": "degraded", "backup_age_hours": backup_age_hours}
    
    return {"status": "ok", "backup_age_hours": backup_age_hours}
```

---

## Action Items

- [ ] Upgrade PostgreSQL to Standard plan for PITR
- [ ] Set up S3/R2 bucket for backup storage
- [ ] Configure daily backup cron job
- [ ] Add backup health check to /healthz
- [ ] Document restore procedures in runbook
- [ ] Schedule quarterly backup restore drills

---

*Last Updated: February 2026*
