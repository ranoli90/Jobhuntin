
// Auth Signal Content Script
// Detects Supabase session from the main web app and syncs it to the extension

// The web app stores the actual Supabase session under the standard
// `sb-<project-ref>-auth-token` localStorage key.  The lightweight
// `sorce-session` key only contains a login-status flag (no tokens).
// We sync the REAL Supabase session to the extension background so the
// popup can call `supabase.auth.getSession()` successfully.

const findAuthSession = () => {
    // Look for the standard Supabase auth token key
    const keys = Object.keys(localStorage);
    const authKey = keys.find(k => k.startsWith('sb-') && k.endsWith('-auth-token'));

    if (authKey) {
        const sessionStr = localStorage.getItem(authKey);
        if (sessionStr) {
            try {
                return JSON.parse(sessionStr);
            } catch (e) {
                console.error('Failed to parse Supabase auth session', e);
            }
        }
    }
    return null;
};

const syncSession = () => {
    const session = findAuthSession();
    if (session) {
        chrome.runtime.sendMessage({
            type: 'SYNC_SESSION',
            session: session
        }, () => {
            // Handle runtime.lastError to avoid noise
            if (chrome.runtime.lastError) {
                // This is expected if extension is not installed or background script is inactive
            }
        });
    }
};

// Sync on load
syncSession();

// Sync on storage changes (login/logout)
window.addEventListener('storage', (event) => {
    // React to Supabase auth key changes OR the lightweight sorce-session flag
    if (
        (event.key && event.key.startsWith('sb-') && event.key.endsWith('-auth-token')) ||
        event.key === 'sorce-session'
    ) {
        syncSession();
    }
});

// Also listen for a custom event from the web app if we want to be explicit
window.addEventListener('SORCE_AUTH_CHANGED', () => {
    syncSession();
});
