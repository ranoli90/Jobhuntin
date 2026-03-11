# API Migration Guides

Migration instructions for upgrading between API versions.

## v1 → v2

### Overview

API v2 is the platform API for integrators (job boards, ATS, staffing agencies). It uses API key authentication and provides:

- Application submission (single and batch)
- Webhook registration
- Staffing bulk submission (TEAM/ENTERPRISE)
- Usage statistics

### Authentication

| Version | Auth Method |
|---------|-------------|
| v1 | JWT Bearer (magic link, OAuth) |
| v2 | API key (`X-API-Key` header or `Authorization: Bearer <api_key>`) |

### Endpoint Mapping

| v1 (user app) | v2 (platform API) |
|---------------|-------------------|
| `POST /me/applications` (swipe) | `POST /api/v2/applications` |
| `GET /applications/{id}` | `GET /api/v2/applications/{id}` |

v1 endpoints are for the end-user web/mobile app. v2 is for B2B integrators.

### Version Selection

- **URL**: Use `/api/v2/` prefix for v2 endpoints
- **Header**: Send `Accept-Version: v2` to request v2 behavior where applicable
- **Response**: Check `X-API-Version` header to confirm version used

### Deprecation

When endpoints are deprecated:

- `X-API-Deprecated: true` and `X-API-Sunset-Date: YYYY-MM-DD` are added to responses
- `Deprecation: true` and `Sunset: <date>` (RFC 8594) are also set
- Migrate before the sunset date; deprecated endpoints are removed after that date

## Breaking Changes Log

### v2 (2024)

- New webhook system with event filtering
- Application submission accepts `resume_text` or `resume_url`
- Staffing bulk API requires TEAM or ENTERPRISE plan

### v1 (Stable)

- No breaking changes planned. v1 remains the default for user-facing endpoints.
