# Render Database IP Whitelisting Guide

## Steps to Allow External Access
1. Log in to Render dashboard
2. Navigate to your PostgreSQL database service
3. Go to 'Settings' > 'IP Whitelist'
4. Add your public IP (from `curl ifconfig.me`)
5. Save changes

## Verification
- Allow 2-5 minutes for changes to propagate
- Test connection using:
  ```
  psql postgresql://[user]:[password]@[host]:5432/[database]
  ```
