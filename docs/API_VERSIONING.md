# API Versioning Strategy

## Overview

This document describes the API versioning strategy for the JobHuntin API to ensure backward compatibility and smooth evolution of the API.

## Version Format

- **Current Version**: `v1`
- **Supported Versions**: `v1`, `v2`
- **Version Format**: Semantic versioning with major version increments (v1, v2, v3, etc.)

## Version Negotiation

### Header-Based Versioning

Clients can specify their desired API version using the `Accept-Version` header:

```http
GET /api/endpoint HTTP/1.1
Accept-Version: v2
```

### Response Headers

All API responses include version information:

- `X-API-Version`: Current API version being used
- `X-Supported-Versions`: Comma-separated list of all supported versions

Example:
```http
HTTP/1.1 200 OK
X-API-Version: v1
X-Supported-Versions: v1,v2
```

### Default Behavior

If no `Accept-Version` header is provided, the API defaults to the current version (`v1`).

## Versioning Rules

### Major Version Changes (v1 → v2)

Major version increments indicate breaking changes:

- **Removed endpoints**: Endpoints removed in v2 are not available
- **Changed request/response formats**: Field names, types, or structures may change
- **Changed authentication**: Authentication mechanisms may evolve
- **Changed error codes**: Error response formats may change

### Backward Compatibility

- **Deprecation Period**: Endpoints/features are deprecated for at least 6 months before removal
- **Deprecation Headers**: Deprecated endpoints include `X-API-Deprecated: true` and `X-API-Sunset-Date: YYYY-MM-DD`, plus RFC 8594 `Deprecation: true` and `Sunset: <date>`
- **Migration Guides**: Breaking changes include migration guides in the changelog

## URL-Based Versioning

Some endpoints use URL-based versioning for clarity:

- `/api/v2/applications` - API v2 applications endpoint
- `/api/v2/webhooks` - API v2 webhooks endpoint

These endpoints are part of the v2 API and require the `Accept-Version: v2` header or use the `/api/v2` prefix.

## Version Lifecycle

1. **Development**: New versions are developed in feature branches
2. **Beta**: Beta versions are available with `Accept-Version: v2-beta` (if supported)
3. **Stable**: Stable versions are fully supported and documented
4. **Deprecated**: Deprecated versions receive security updates only
5. **Sunset**: Sunset versions are no longer available

## Error Handling

### Unsupported Version

If a client requests an unsupported version:

```json
{
  "error": {
    "code": "UNSUPPORTED_API_VERSION",
    "message": "API version 'v3' is not supported",
    "detail": "Supported versions: v1, v2",
    "requested_version": "v3",
    "supported_versions": ["v1", "v2"]
  }
}
```

HTTP Status: `400 Bad Request`

## Best Practices

### For API Consumers

1. **Always specify version**: Use `Accept-Version` header to lock in a specific version
2. **Monitor deprecation headers**: Check for `X-API-Deprecated` and plan migrations
3. **Test version upgrades**: Test your integration when upgrading API versions
4. **Read changelog**: Review breaking changes before upgrading

### For API Developers

1. **Maintain backward compatibility**: Avoid breaking changes in the same major version
2. **Deprecate before removing**: Give 6+ months notice before removing features
3. **Document changes**: Update changelog and migration guides
4. **Version increment rules**:
   - **Major (v1 → v2)**: Breaking changes
   - **Minor (v1.0 → v1.1)**: New features, backward compatible
   - **Patch (v1.0.0 → v1.0.1)**: Bug fixes, backward compatible

## Examples

### Request with Version Header

```bash
curl -H "Accept-Version: v2" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     https://api.jobhuntin.com/api/applications
```

### Response with Version Headers

```http
HTTP/1.1 200 OK
X-API-Version: v2
X-Supported-Versions: v1,v2
Content-Type: application/json

{
  "applications": [...]
}
```

### Unsupported Version Error

```http
HTTP/1.1 400 Bad Request
X-API-Version: v1
X-Supported-Versions: v1,v2
Content-Type: application/json

{
  "error": {
    "code": "UNSUPPORTED_API_VERSION",
    "message": "API version 'v3' is not supported",
    "detail": "Supported versions: v1, v2",
    "requested_version": "v3",
    "supported_versions": ["v1", "v2"]
  }
}
```

## Changelog

### v2 (Current Beta)
- New webhook system
- Enhanced application submission API
- Improved error responses

### v1 (Stable)
- Initial API release
- Magic link authentication
- Application management
- Job matching

## Migration Guides

See [MIGRATION_GUIDES.md](./MIGRATION_GUIDES.md) for detailed migration instructions between versions.
