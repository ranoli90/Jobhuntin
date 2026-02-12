# Database Migration Verification Checklist

## Connection Tests
- [ ] Verify direct database connection using psql/PgAdmin
- [ ] Test connection from application servers
- [ ] Confirm connection pooling works

## Schema Verification
- [ ] Check all tables were created
- [ ] Verify indexes exist
- [ ] Confirm constraints are in place

## Service Tests
- [ ] API endpoints using database
- [ ] Worker services
- [ ] SEO automation scripts
- [ ] Authentication flows

## Performance Checks
- [ ] Baseline query performance
- [ ] Connection pool metrics
- [ ] High volume operation tests
