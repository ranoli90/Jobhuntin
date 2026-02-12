
// Auth Signal Content Script
// Detects JWT auth token from the main web app and syncs it to the extension

const findAuthToken = () => {
    return localStorage.getItem('auth_token');
};

const syncSession = () => {
    const token = findAuthToken();
    if (token) {
        chrome.runtime.sendMessage({
            type: 'SYNC_SESSION',
            token: token
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
    if (event.key === 'auth_token') {
        syncSession();
    }
});

// Also listen for a custom event from the web app if we want to be explicit
window.addEventListener('auth:update', () => {
    syncSession();
});
