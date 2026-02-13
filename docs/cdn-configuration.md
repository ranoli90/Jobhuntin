# CDN Configuration Guide

## Overview

This document outlines CDN configuration for the JobHuntin platform to improve static asset delivery performance.

---

## Current Setup

### Web Frontend (sorce-web.onrender.com)
- **Type**: Static site on Render
- **CDN**: Render's built-in CDN (Cloudflare-backed)
- **Cache Headers**: Already configured

### API (sorce-api.onrender.com)
- **Type**: Web service on Render
- **Static Assets**: None (API only)

---

## Recommended CDN Configuration

### Option 1: Render Built-in CDN (Current)

Render automatically serves static sites through Cloudflare CDN. No additional configuration needed.

**Benefits:**
- Automatic SSL
- Global edge locations
- DDoS protection
- Zero configuration

**Cache Headers:**
```
Cache-Control: public, max-age=31536000, immutable  # For hashed assets
Cache-Control: public, max-age=0, s-maxage=300      # For HTML
```

### Option 2: Cloudflare CDN (Recommended for Custom Domain)

If using custom domain (jobhuntin.com), configure Cloudflare for enhanced caching:

**Step 1: Add Cloudflare DNS**
```
# DNS Records
A     jobhuntin.com        -> Render IP
CNAME www.jobhuntin.com    -> sorce-web.onrender.com
CNAME api.jobhuntin.com    -> sorce-api.onrender.com
```

**Step 2: Page Rules**
```
# Cache everything for static assets
*.jobhuntin.com/assets/*  -> Cache Level: Cache Everything, Edge TTL: 1 year

# Bypass cache for API
api.jobhuntin.com/*       -> Cache Level: Bypass
```

**Step 3: Cache Rules in Cloudflare Dashboard**
- Enable "Auto Minify" for HTML, CSS, JS
- Enable "Brotli" compression
- Enable "Rocket Loader" for async JS
- Enable "Mirage" for image lazy loading

---

## Cache Headers Configuration

### For Vite/React Build (apps/web)

Add to `vite.config.ts`:

```typescript
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        // Add content hash to filenames for cache busting
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]'
      }
    }
  }
})
```

### For Render Static Site

The static site automatically gets these headers from Render:
- `Cache-Control: public, max-age=0, s-maxage=300` for HTML
- `Cache-Control: public, max-age=31536000` for assets with hash

---

## Image Optimization

### Recommended: Use Cloudflare Image Resizing

```html
<!-- Instead of -->
<img src="/images/hero.png" alt="Hero">

<!-- Use -->
<img src="https://jobhuntin.com/cdn-cgi/image/width=800,quality=80/images/hero.png" alt="Hero">
```

### Alternative: Store images in R2/S3 with CDN

1. Upload images to Cloudflare R2
2. Enable R2 public access
3. Configure custom domain for R2 bucket
4. Images served from CDN automatically

---

## Performance Metrics

### Target Metrics
| Metric | Target |
|--------|--------|
| TTFB (Time to First Byte) | < 100ms |
| LCP (Largest Contentful Paint) | < 2.5s |
| FCP (First Contentful Paint) | < 1.8s |
| CLS (Cumulative Layout Shift) | < 0.1 |

### Monitoring
Use these tools to monitor CDN performance:
- Google PageSpeed Insights
- WebPageTest.org
- Cloudflare Analytics (if using Cloudflare)

---

## Implementation Checklist

- [x] Render CDN active for static site
- [ ] Configure custom domain with Cloudflare
- [ ] Set up page rules for aggressive caching
- [ ] Enable image optimization
- [ ] Add cache headers for API responses
- [ ] Monitor performance metrics

---

*Last Updated: February 2026*
