
// Auth Signal Content Script
// Detects Supabase session from the main web app and syncs it to the extension

console.log("Sorce Auth Sync Script Loaded");

// Function to find the Supabase token in localStorage
const findAuthToken = () => {
    // 1. Check explicit sorce-session key first
    const sorceSession = localStorage.getItem('sorce-session');
    if (sorceSession) {
        try {
            return JSON.parse(sorceSession);
        } catch (e) {
            console.error("Failed to parse sorce-session", e);
        }
    }

    // 2. Fallback: Look for keys starting with sb- and ending with -auth-token
    const keys = Object.keys(localStorage);
    const authKey = keys.find(k => k.startsWith('sb-') && k.endsWith('-auth-token'));

    if (authKey) {
        const sessionStr = localStorage.getItem(authKey);
        if (sessionStr) {
            try {
                const session = JSON.parse(sessionStr);
                return session;
            } catch (e) {
                console.error("Failed to parse auth session", e);
            }
        }
    }
    return null;
};

const syncSession = () => {
    const session = findAuthToken();
    if (session) {
        console.log("Sorce: Found session, syncing to extension...");
        chrome.runtime.sendMessage({
            type: 'SYNC_SESSION',
            session: session
        }, (response) => {
            // Handle runtime.lastError to avoid noise
            if (chrome.runtime.lastError) {
                // This is expected if extension is not installed or background script is inactive
                // console.log("Extension not reachable"); 
            } else {
                console.log("Sorce: Sync response", response);
            }
        });
    }
};

// Sync on load
syncSession();

// Sync on storage changes (login/logout)
window.addEventListener('storage', (event) => {
    if (event.key === 'sorce-session' || (event.key && event.key.startsWith('sb-') && event.key.endsWith('-auth-token'))) {
        syncSession();
    }
});

// Also listen for a custom event from the web app if we want to be explicit
window.addEventListener('SORCE_AUTH_CHANGED', () => {
    syncSession();
});
