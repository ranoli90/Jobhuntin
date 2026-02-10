import { test, expect, Page } from '@playwright/test';

/**
 * Comprehensive Auth System E2E Tests
 * Tests: Login page load, Magic Link flow, Password Login flow, Registration flow,
 *        Auth Guard, Navigation to Dashboard
 */

// Increase default timeout for all tests since auth flows involve animations
test.setTimeout(30000);

// Helper to mock Supabase auth endpoints
async function mockSupabaseAuth(page: Page) {
    // Mock getSession - return no session initially
    await page.route('**/auth/v1/token?grant_type=refresh_token', async (route) => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                access_token: '',
                token_type: 'bearer',
                expires_in: 0,
                refresh_token: '',
            }),
        });
    });
}

test.describe('Login Page - UI Elements & Structure', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login', { waitUntil: 'networkidle', timeout: 30000 });
    });

    test('should load the login page without errors', async ({ page }) => {
        // Verify no uncaught errors
        const errors: string[] = [];
        page.on('pageerror', (error) => errors.push(error.message));

        // Wait for content to render
        await page.waitForLoadState('networkidle');

        // Check the page title
        await expect(page).toHaveTitle(/JobHuntin/);

        // Verify no page errors occurred
        expect(errors).toEqual([]);
    });

    test('should display the logo and heading', async ({ page }) => {
        // The heading says "Let's get hunting" when in magic mode
        await expect(page.getByText("Let's get hunting")).toBeVisible({ timeout: 10000 });
    });

    test('should display three auth mode tabs', async ({ page }) => {
        // Check for the three tab buttons - they show first word
        const tablist = page.getByRole('tablist');
        await expect(tablist).toBeVisible({ timeout: 10000 });

        // Tabs show "Magic", "Password", "Create"
        await expect(page.getByRole('tab', { name: /Magic/i })).toBeVisible();
        await expect(page.getByRole('tab', { name: /Password/i })).toBeVisible();
        await expect(page.getByRole('tab', { name: /Create/i })).toBeVisible();
    });

    test('should display email input field', async ({ page }) => {
        await expect(page.getByPlaceholder('tech-wizard@example.com')).toBeVisible({ timeout: 10000 });
    });

    test('should display social login buttons', async ({ page }) => {
        await expect(page.getByRole('button', { name: /Continue with Google/i })).toBeVisible({ timeout: 10000 });
        await expect(page.getByRole('button', { name: /Continue with LinkedIn/i })).toBeVisible({ timeout: 10000 });
    });

    test('should display "Send Magic Link" button (default mode)', async ({ page }) => {
        await expect(page.getByRole('button', { name: /Send Magic Link/i })).toBeVisible({ timeout: 10000 });
    });

    test('should display terms and privacy links', async ({ page }) => {
        await expect(page.getByRole('link', { name: /Terms/i })).toBeVisible({ timeout: 10000 });
        await expect(page.getByRole('link', { name: /Privacy Policy/i })).toBeVisible({ timeout: 10000 });
    });

    test('should show destination hint text', async ({ page }) => {
        // Default returnTo is /app/dashboard
        await expect(page.getByText("You'll land on your dashboard after signing in")).toBeVisible({ timeout: 10000 });
    });
});

test.describe('Magic Link Flow', () => {
    test('should disable Send button when email is empty', async ({ page }) => {
        await page.goto('/login', { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForTimeout(1000);

        const sendBtn = page.getByRole('button', { name: /Send Magic Link/i });
        await expect(sendBtn).toBeVisible({ timeout: 10000 });
        await expect(sendBtn).toBeDisabled();
    });

    test('should disable Send button with invalid email', async ({ page }) => {
        await page.goto('/login', { waitUntil: 'networkidle', timeout: 30000 });

        await page.getByPlaceholder('tech-wizard@example.com').fill('not-an-email');

        const sendBtn = page.getByRole('button', { name: /Send Magic Link/i });
        await expect(sendBtn).toBeDisabled();
    });

    test('should enable Send button with valid email', async ({ page }) => {
        await page.goto('/login', { waitUntil: 'networkidle', timeout: 30000 });

        await page.getByPlaceholder('tech-wizard@example.com').fill('test@example.com');

        const sendBtn = page.getByRole('button', { name: /Send Magic Link/i });
        await expect(sendBtn).toBeEnabled();
    });

    test('should successfully send magic link and show confirmation', async ({ page }) => {
        await page.goto('/login', { waitUntil: 'networkidle', timeout: 30000 });

        const testEmail = 'testuser@example.com';

        // Intercept Supabase OTP request
        await page.route('**/auth/v1/otp**', async (route) => {
            const req = route.request();
            if (req.method() === 'POST') {
                const body = req.postDataJSON();
                // Verify the email is being sent correctly
                expect(body.email).toBe(testEmail);
                // Verify redirect URL is properly formed
                expect(body.options.emailRedirectTo).toContain('/login?returnTo=');

                await route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({}),
                });
                return;
            }
            await route.continue();
        });

        // Fill email
        await page.getByPlaceholder('tech-wizard@example.com').fill(testEmail);

        // Click send
        await page.getByRole('button', { name: /Send Magic Link/i }).click();

        // Verify success state
        await expect(page.getByText('Check your email')).toBeVisible({ timeout: 10000 });
        await expect(page.getByText(testEmail)).toBeVisible();

        // Verify instruction steps are shown
        await expect(page.getByText(/Start your JobHuntin run/)).toBeVisible();
        await expect(page.getByText(/noreply@sorce.app/)).toBeVisible();

        // Verify "Resend magic link" button exists
        await expect(page.getByRole('button', { name: /Resend magic link/i })).toBeVisible();

        // Verify "Use a different email" button exists  
        await expect(page.getByRole('button', { name: /Use a different email/i })).toBeVisible();
    });

    test('should handle magic link API error gracefully', async ({ page }) => {
        await page.goto('/login', { waitUntil: 'networkidle', timeout: 30000 });

        // Intercept with error
        await page.route('**/auth/v1/otp**', async (route) => {
            if (route.request().method() === 'POST') {
                await route.fulfill({
                    status: 422,
                    contentType: 'application/json',
                    body: JSON.stringify({
                        error: 'validation_failed',
                        message: 'Unable to validate email address',
                    }),
                });
                return;
            }
            await route.continue();
        });

        await page.getByPlaceholder('tech-wizard@example.com').fill('error@example.com');
        await page.getByRole('button', { name: /Send Magic Link/i }).click();

        // Should show error alert
        await expect(page.getByRole('alert')).toBeVisible({ timeout: 10000 });
    });

    test('should handle rate limit (429) gracefully', async ({ page }) => {
        await page.goto('/login', { waitUntil: 'networkidle', timeout: 30000 });

        // Intercept with 429
        await page.route('**/auth/v1/otp**', async (route) => {
            if (route.request().method() === 'POST') {
                await route.fulfill({
                    status: 429,
                    contentType: 'application/json',
                    body: JSON.stringify({
                        error: 'rate_limit',
                        message: 'For security purposes, you can only request this after 30 seconds',
                    }),
                });
                return;
            }
            await route.continue();
        });

        await page.getByPlaceholder('tech-wizard@example.com').fill('ratelimit@example.com');
        await page.getByRole('button', { name: /Send Magic Link/i }).click();

        // Should show error about rate limiting or cooldown
        // The magic link service has client-side rate limiting (1 per 60s)
        // so it may either hit client-side or server-side rate limit
        await expect(page.getByRole('alert')).toBeVisible({ timeout: 10000 });
    });

    test('should allow switching back from success state', async ({ page }) => {
        await page.goto('/login', { waitUntil: 'networkidle', timeout: 30000 });

        // Mock success
        await page.route('**/auth/v1/otp**', async (route) => {
            if (route.request().method() === 'POST') {
                await route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({}),
                });
                return;
            }
            await route.continue();
        });

        await page.getByPlaceholder('tech-wizard@example.com').fill('user@example.com');
        await page.getByRole('button', { name: /Send Magic Link/i }).click();

        // Wait for success state
        await expect(page.getByText('Check your email')).toBeVisible({ timeout: 10000 });

        // Click "Use a different email"
        await page.getByRole('button', { name: /Use a different email/i }).click();

        // Should go back to login form
        await expect(page.getByPlaceholder('tech-wizard@example.com')).toBeVisible({ timeout: 10000 });
    });
});

test.describe('Password Login Flow', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login', { waitUntil: 'networkidle', timeout: 30000 });
        // Switch to password mode
        await page.getByRole('tab', { name: /Password/i }).click();
        await page.waitForTimeout(500); // Wait for animation
    });

    test('should switch to password mode and show password field', async ({ page }) => {
        // Heading should change
        await expect(page.getByText('Welcome back')).toBeVisible({ timeout: 5000 });

        // Password input should be visible
        await expect(page.getByPlaceholder('••••••••')).toBeVisible();

        // Button text should change
        await expect(page.getByRole('button', { name: /Sign In/i })).toBeVisible();
    });

    test('should disable Sign In when fields are empty', async ({ page }) => {
        const signInBtn = page.getByRole('button', { name: /Sign In/i });
        await expect(signInBtn).toBeDisabled();
    });

    test('should disable Sign In when only email is filled', async ({ page }) => {
        await page.getByPlaceholder('tech-wizard@example.com').fill('user@example.com');

        const signInBtn = page.getByRole('button', { name: /Sign In/i });
        await expect(signInBtn).toBeDisabled();
    });

    test('should enable Sign In when email AND password are filled', async ({ page }) => {
        await page.getByPlaceholder('tech-wizard@example.com').fill('user@example.com');
        await page.getByPlaceholder('••••••••').fill('anypassword');

        const signInBtn = page.getByRole('button', { name: /Sign In/i });
        await expect(signInBtn).toBeEnabled();
    });

    test('should show error for invalid credentials', async ({ page }) => {
        // Mock failed login
        await page.route('**/auth/v1/token?grant_type=password', async (route) => {
            await route.fulfill({
                status: 400,
                contentType: 'application/json',
                body: JSON.stringify({
                    error: 'invalid_grant',
                    error_description: 'Invalid login credentials',
                }),
            });
        });

        await page.getByPlaceholder('tech-wizard@example.com').fill('user@example.com');
        await page.getByPlaceholder('••••••••').fill('wrongpassword');
        await page.getByRole('button', { name: /Sign In/i }).click();

        // Should show error
        await expect(page.getByRole('alert')).toBeVisible({ timeout: 10000 });
    });

    test('should navigate to dashboard on successful login', async ({ page }) => {
        // Mock successful login
        const fakeSession = {
            access_token: 'fake-access-token-123',
            token_type: 'bearer',
            expires_in: 3600,
            refresh_token: 'fake-refresh-token-456',
            user: {
                id: 'test-user-id-789',
                email: 'user@example.com',
                aud: 'authenticated',
                role: 'authenticated',
                email_confirmed_at: new Date().toISOString(),
                app_metadata: {},
                user_metadata: {},
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            },
        };

        await page.route('**/auth/v1/token?grant_type=password', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(fakeSession),
            });
        });

        // Also mock the profile endpoint that OnboardingGuard checks
        await page.route('**/api/profile**', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    id: 'test-user-id-789',
                    email: 'user@example.com',
                    has_completed_onboarding: true,
                }),
            });
        });

        // Also mock session refresh
        await page.route('**/auth/v1/token?grant_type=refresh_token', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(fakeSession),
            });
        });

        await page.getByPlaceholder('tech-wizard@example.com').fill('user@example.com');
        await page.getByPlaceholder('••••••••').fill('correctpassword');
        await page.getByRole('button', { name: /Sign In/i }).click();

        // Should navigate to dashboard
        await page.waitForURL('**/app/dashboard**', { timeout: 15000 });
        expect(page.url()).toContain('/app/dashboard');
    });
});

test.describe('Registration Flow', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login', { waitUntil: 'networkidle', timeout: 30000 });
        // Switch to register mode
        await page.getByRole('tab', { name: /Create/i }).click();
        await page.waitForTimeout(500);
    });

    test('should switch to register mode and show correct UI', async ({ page }) => {
        // Heading should change
        await expect(page.getByText('Create your vault')).toBeVisible({ timeout: 5000 });

        // Both password fields should appear
        await expect(page.getByPlaceholder('Create a strong password')).toBeVisible();
        await expect(page.getByPlaceholder('Confirm password')).toBeVisible();

        // Security checklist should appear
        await expect(page.getByText('Security Checklist')).toBeVisible();
        await expect(page.getByText('10+ characters')).toBeVisible();
        await expect(page.getByText('Contains a letter')).toBeVisible();
        await expect(page.getByText('Contains a number')).toBeVisible();
        await expect(page.getByText('Contains a symbol')).toBeVisible();

        // Button should say "Create Account"
        await expect(page.getByRole('button', { name: /Create Account/i })).toBeVisible();
    });

    test('should disable Create Account for weak passwords', async ({ page }) => {
        await page.getByPlaceholder('tech-wizard@example.com').fill('new@example.com');
        await page.getByPlaceholder('Create a strong password').fill('weak');
        await page.getByPlaceholder('Confirm password').fill('weak');

        await expect(page.getByRole('button', { name: /Create Account/i })).toBeDisabled();
    });

    test('should disable Create Account when passwords do not match', async ({ page }) => {
        await page.getByPlaceholder('tech-wizard@example.com').fill('new@example.com');
        await page.getByPlaceholder('Create a strong password').fill('StrongP@ss1!');
        await page.getByPlaceholder('Confirm password').fill('DifferentP@ss1!');

        // Should show "Passwords must match" message
        await expect(page.getByText('Passwords must match')).toBeVisible();
        await expect(page.getByRole('button', { name: /Create Account/i })).toBeDisabled();
    });

    test('should enable Create Account with strong matching passwords', async ({ page }) => {
        await page.getByPlaceholder('tech-wizard@example.com').fill('new@example.com');
        await page.getByPlaceholder('Create a strong password').fill('StrongP@ss1!');
        await page.getByPlaceholder('Confirm password').fill('StrongP@ss1!');

        await expect(page.getByRole('button', { name: /Create Account/i })).toBeEnabled();
    });

    test('should show confirmation email state after successful registration', async ({ page }) => {
        const testEmail = 'newuser@example.com';

        // Mock signup - return no session (email confirmation required)
        await page.route('**/auth/v1/signup**', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    id: 'new-user-id',
                    email: testEmail,
                    aud: 'authenticated',
                    role: 'authenticated',
                    created_at: new Date().toISOString(),
                }),
            });
        });

        await page.getByPlaceholder('tech-wizard@example.com').fill(testEmail);
        await page.getByPlaceholder('Create a strong password').fill('StrongP@ss1!');
        await page.getByPlaceholder('Confirm password').fill('StrongP@ss1!');
        await page.getByRole('button', { name: /Create Account/i }).click();

        // Should show email confirmation screen
        await expect(page.getByText('Confirm your email')).toBeVisible({ timeout: 10000 });
        await expect(page.getByText(testEmail)).toBeVisible();
        await expect(page.getByText('Verify your JobHuntin account')).toBeVisible();
    });

    test('should navigate to dashboard for auto-confirmed registration', async ({ page }) => {
        const testEmail = 'autoconfirm@example.com';

        const fakeSession = {
            access_token: 'fake-access-token-reg',
            token_type: 'bearer',
            expires_in: 3600,
            refresh_token: 'fake-refresh-token-reg',
            user: {
                id: 'reg-user-id',
                email: testEmail,
                aud: 'authenticated',
                role: 'authenticated',
                email_confirmed_at: new Date().toISOString(),
                app_metadata: {},
                user_metadata: {},
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            },
        };

        // Mock signup - return session (auto-confirmed)
        await page.route('**/auth/v1/signup**', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(fakeSession),
            });
        });

        // Mock profile
        await page.route('**/api/profile**', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    id: 'reg-user-id',
                    email: testEmail,
                    has_completed_onboarding: true,
                }),
            });
        });

        await page.route('**/auth/v1/token?grant_type=refresh_token', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(fakeSession),
            });
        });

        await page.getByPlaceholder('tech-wizard@example.com').fill(testEmail);
        await page.getByPlaceholder('Create a strong password').fill('StrongP@ss1!');
        await page.getByPlaceholder('Confirm password').fill('StrongP@ss1!');
        await page.getByRole('button', { name: /Create Account/i }).click();

        // Should navigate to dashboard
        await page.waitForURL('**/app/**', { timeout: 15000 });
    });

    test('should handle registration error', async ({ page }) => {
        // Mock signup error
        await page.route('**/auth/v1/signup**', async (route) => {
            await route.fulfill({
                status: 422,
                contentType: 'application/json',
                body: JSON.stringify({
                    error: 'user_already_exists',
                    message: 'User already registered',
                }),
            });
        });

        await page.getByPlaceholder('tech-wizard@example.com').fill('existing@example.com');
        await page.getByPlaceholder('Create a strong password').fill('StrongP@ss1!');
        await page.getByPlaceholder('Confirm password').fill('StrongP@ss1!');
        await page.getByRole('button', { name: /Create Account/i }).click();

        // Should show error
        await expect(page.getByRole('alert')).toBeVisible({ timeout: 10000 });
    });
});

test.describe('Auth Guard & Navigation', () => {
    test('should redirect unauthenticated users from /app/dashboard to /login', async ({ page }) => {
        await page.goto('/app/dashboard', { waitUntil: 'networkidle', timeout: 30000 });

        // Should redirect to login with returnTo param
        await page.waitForURL('**/login**', { timeout: 15000 });
        expect(page.url()).toContain('/login');
        expect(page.url()).toContain('returnTo');
    });

    test('should redirect from /app to /login when not authenticated', async ({ page }) => {
        await page.goto('/app', { waitUntil: 'networkidle', timeout: 30000 });

        await page.waitForURL('**/login**', { timeout: 15000 });
        expect(page.url()).toContain('/login');
    });

    test('should preserve returnTo parameter through login', async ({ page }) => {
        await page.goto('/login?returnTo=/app/dashboard', { waitUntil: 'networkidle', timeout: 30000 });

        // Should show the dashboard destination hint
        await expect(page.getByText("You'll land on your dashboard after signing in")).toBeVisible({ timeout: 10000 });
    });
});

test.describe('Mode Switching', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login', { waitUntil: 'networkidle', timeout: 30000 });
    });

    test('should switch between all three modes', async ({ page }) => {
        // Start in magic mode (default)
        await expect(page.getByText("Let's get hunting")).toBeVisible({ timeout: 10000 });

        // Switch to password
        await page.getByRole('tab', { name: /Password/i }).click();
        await expect(page.getByText('Welcome back')).toBeVisible({ timeout: 5000 });
        await expect(page.getByPlaceholder('••••••••')).toBeVisible();

        // Switch to register
        await page.getByRole('tab', { name: /Create/i }).click();
        await expect(page.getByText('Create your vault')).toBeVisible({ timeout: 5000 });
        await expect(page.getByPlaceholder('Create a strong password')).toBeVisible();
        await expect(page.getByPlaceholder('Confirm password')).toBeVisible();

        // Switch back to magic
        await page.getByRole('tab', { name: /Magic/i }).click();
        await expect(page.getByText("Let's get hunting")).toBeVisible({ timeout: 5000 });
        // Password fields should be hidden
        await expect(page.getByPlaceholder('••••••••')).not.toBeVisible();
    });

    test('should clear form errors when switching modes', async ({ page }) => {
        // Go to password mode and create an error
        await page.getByRole('tab', { name: /Password/i }).click();

        // Mock failed login
        await page.route('**/auth/v1/token?grant_type=password', async (route) => {
            await route.fulfill({
                status: 400,
                contentType: 'application/json',
                body: JSON.stringify({
                    error: 'invalid_grant',
                    error_description: 'Invalid login credentials',
                }),
            });
        });

        await page.getByPlaceholder('tech-wizard@example.com').fill('user@example.com');
        await page.getByPlaceholder('••••••••').fill('wrong');
        await page.getByRole('button', { name: /Sign In/i }).click();

        // Wait for error to appear
        await expect(page.getByRole('alert')).toBeVisible({ timeout: 10000 });

        // Switch to magic - error should clear
        await page.getByRole('tab', { name: /Magic/i }).click();
        await page.waitForTimeout(500);

        // Error alert should be gone
        await expect(page.getByRole('alert')).not.toBeVisible();
    });

    test('should clear password fields when switching to magic mode', async ({ page }) => {
        // Go to password mode and type
        await page.getByRole('tab', { name: /Password/i }).click();
        await page.getByPlaceholder('••••••••').fill('somepassword');

        // Switch to magic
        await page.getByRole('tab', { name: /Magic/i }).click();

        // Switch back to password - should be empty
        await page.getByRole('tab', { name: /Password/i }).click();
        await expect(page.getByPlaceholder('••••••••')).toHaveValue('');
    });
});

test.describe('Homepage Magic Link (Homepage Hero)', () => {
    test('should show email input on homepage', async ({ page }) => {
        await page.goto('/', { waitUntil: 'networkidle', timeout: 30000 });

        // Check for hero email input
        await expect(page.getByPlaceholder('you@example.com')).toBeVisible({ timeout: 10000 });

        // Check for Start Hunt button
        await expect(page.getByRole('button', { name: /Start Hunt/i })).toBeVisible();
    });

    test('should send magic link from homepage', async ({ page }) => {
        await page.goto('/', { waitUntil: 'networkidle', timeout: 30000 });

        // Mock the OTP endpoint
        await page.route('**/auth/v1/otp**', async (route) => {
            if (route.request().method() === 'POST') {
                await route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({}),
                });
                return;
            }
            await route.continue();
        });

        await page.getByPlaceholder('you@example.com').fill('homepage@example.com');
        await page.getByRole('button', { name: /Start Hunt/i }).click();

        // Should show success confirmation
        await expect(page.getByText(/Magic link en route/i)).toBeVisible({ timeout: 10000 });
        await expect(page.getByText('homepage@example.com')).toBeVisible();
    });

    test('should validate email on homepage', async ({ page }) => {
        await page.goto('/', { waitUntil: 'networkidle', timeout: 30000 });

        // Submit with invalid email
        await page.getByPlaceholder('you@example.com').fill('not-valid');
        await page.getByRole('button', { name: /Start Hunt/i }).click();

        // Should show error
        await expect(page.getByText(/Please enter a valid email/i)).toBeVisible({ timeout: 5000 });
    });
});
