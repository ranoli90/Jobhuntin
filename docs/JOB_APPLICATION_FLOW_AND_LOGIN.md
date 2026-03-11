# Job Application Flow: Where We Apply & Login

## Where applications happen

Applications are submitted **directly on the job’s site**:

- **Company ATS** (Greenhouse, Lever, Workday, etc.): `application_url` points to the company’s apply page. We open that URL in Playwright and fill the form.
- **Indeed**: `application_url` is often an Indeed-hosted page. Clicking “Apply” typically requires an Indeed account.
- **LinkedIn**: Same idea — apply via LinkedIn’s UI, which often requires a LinkedIn login.

So the agent applies on the site that owns the URL.

## Login requirement

| Site type | Login needed? | How it works |
|----------|----------------|--------------|
| **Company ATS** (Greenhouse, Lever, Workday, etc.) | Usually no | Apply directly on the company’s career page. No job board account. |
| **Indeed** | Yes | User must connect their Indeed account. We store `oauth_credentials` in profile and use them for login. |
| **LinkedIn** | Yes | Same idea — user connects LinkedIn; we store credentials and use them when applying. |
| **Other job boards** | Depends | Some redirect to external ATS (no login). Others require login first. |

## How we handle login

1. **Profile `oauth_credentials`**  
   User connects their LinkedIn/Indeed/etc. during onboarding or in settings. We store `oauth_credentials` in their profile.

2. **OAuth flow**  
   When the agent hits a login page:
   - Uses `OAuthHandler.detect_oauth_flow()`
   - If it detects a login flow, it uses `oauth_credentials` from the profile
   - Fills email/password and completes the OAuth flow

3. **If credentials are missing**  
   OAuth fails and we continue without login. The application may fail for sites that require login.

## What users need to do

1. **Connect accounts** (optional but recommended)  
   For Indeed/LinkedIn:  
   - User connects their account in settings  
   - We store credentials securely

2. **Apply without connecting**  
   For jobs that go directly to a company ATS (Greenhouse, Lever, etc.), we can usually apply without any job board login.

## Proxy sources

| Source | Used for | Notes |
|--------|----------|------|
| **GimmeProxy API** | JobSpy scraping | Free proxy per request |
| **PubProxy API** | JobSpy scraping | Fallback |
| **Public proxy lists** (GitHub raw URLs) | JobSpy scraping | e.g. TheSpeedX/PROXY-List, ShiftyTR/Proxy-List |

Proxies are used for **scraping** (JobSpy). The **apply agent** does not use proxies by default; it can be configured with `agent_proxies` for rate limit handling.
