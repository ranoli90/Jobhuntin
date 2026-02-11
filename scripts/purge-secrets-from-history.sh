#!/usr/bin/env bash
# =============================================================================
# PURGE COMMITTED SECRETS FROM GIT HISTORY
# =============================================================================
#
# This script removes sensitive files from the entire git history using
# git-filter-repo. After running, ALL collaborators must re-clone the repo.
#
# PREREQUISITES:
#   pip install git-filter-repo
#   OR: brew install git-filter-repo (macOS)
#
# IMPORTANT:
#   1. Ensure all team members have pushed their branches
#   2. Back up the repository before running
#   3. After running, force-push all branches
#   4. All collaborators must delete their local clones and re-clone
#   5. Rotate ALL secrets that were ever committed (even after purging,
#      they may exist in forks, CI caches, or backups)
#
# USAGE:
#   cd /path/to/Quickly
#   bash scripts/purge-secrets-from-history.sh
#
# =============================================================================

set -euo pipefail

echo "============================================="
echo " PURGING SECRETS FROM GIT HISTORY"
echo "============================================="
echo ""
echo "WARNING: This rewrites git history. All collaborators must re-clone."
echo "Press Ctrl+C to abort, or Enter to continue..."
read -r

# Files to purge from history
FILES_TO_PURGE=(
    "apps/web/service-account.json"
    "apps/web/.env"
    "apps/extension/.env"
)

# Patterns to purge (catch any service account keys that may have been committed)
PATTERNS_TO_PURGE=(
    "service-account.json"
    "service-account*.json"
    "credentials.json"
    "client_secret*.json"
)

echo ""
echo "Step 1: Purging specific files..."
for file in "${FILES_TO_PURGE[@]}"; do
    echo "  Purging: $file"
    git filter-repo --invert-paths --path "$file" --force || true
done

echo ""
echo "Step 2: Purging filename patterns..."
for pattern in "${PATTERNS_TO_PURGE[@]}"; do
    echo "  Purging pattern: $pattern"
    git filter-repo --invert-paths --path-glob "$pattern" --force || true
done

echo ""
echo "Step 3: Cleaning up..."
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo ""
echo "============================================="
echo " DONE - NEXT STEPS:"
echo "============================================="
echo ""
echo "1. Verify the purge:"
echo "   git log --all --full-history -- apps/web/service-account.json"
echo "   (should return no results)"
echo ""
echo "2. Force-push ALL branches:"
echo "   git push --force --all"
echo "   git push --force --tags"
echo ""
echo "3. Notify all collaborators to:"
echo "   - Delete their local clone"
echo "   - Re-clone from the remote"
echo ""
echo "4. CRITICAL: Rotate these secrets even after purging:"
echo "   - Google Service Account key (console.cloud.google.com)"
echo "   - Supabase anon key and URL (supabase.com dashboard)"
echo "   - Any other secrets that were in .env files"
echo ""
echo "5. Check and invalidate any CI/CD caches that may contain the old secrets."
