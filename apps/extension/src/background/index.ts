// Sorce Extension Background Worker
// console removed: Background Worker Loaded

const API_BASE_URL = (import.meta.env.VITE_API_URL || "https://sorce-api.onrender.com").replace(/\/$/, "");

// Handle messages from content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {

  if (message.type === 'JOB_DETECTED') {
    handleJobDetected(message.data, sender)
      .then(() => sendResponse({ success: true }))
      .catch((err) => sendResponse({ success: false, error: err.message }));
    return true; // Keep message channel open for async response
  }

  if (message.type === 'SYNC_SESSION') {
    // Store under generic key for backward compat
    const storageUpdate: Record<string, unknown> = { session: message.session };

    // Also store under the Supabase storage key so supabase.auth.getSession()
    // in the popup picks up the synced session from the web app.
    // The Supabase JS client stores sessions as `sb-<project-ref>-auth-token`.
    const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || ''; // Available at build time
    try {
      const url = new URL(supabaseUrl || '');
      const projectRef = url.hostname.split('.')[0];
      if (projectRef) {
        storageUpdate[`sb-${projectRef}-auth-token`] = JSON.stringify(message.session);
      }
    } catch {
      // URL parsing failed — fall back to generic key only
    }

    chrome.storage.local.set(storageUpdate, () => {
      sendResponse({ success: true });

      // Notify user
      chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icon-128.png',
        title: 'Sorce Connected',
        message: `Extension successfully linked to your account.`
      });
    });
    return true;
  }
});

async function getAuthToken(): Promise<string | null> {
  const data = await chrome.storage.local.get(['session']);
  const session = data.session as { access_token?: string } | undefined;
  return session?.access_token || null;
}

async function handleJobDetected(jobData: any, sender: chrome.runtime.MessageSender) {
  try {

    const token = await getAuthToken();

    // Store in local storage first (offline support/backup)
    const jobs = await chrome.storage.local.get(['savedJobs']);
    // Define type or cast
    const savedJobs: any[] = jobs.savedJobs ? (Array.isArray(jobs.savedJobs) ? jobs.savedJobs : []) : [];

    // Check for duplicates
    const isDuplicate = savedJobs.some((j: any) => j.url === (sender.tab?.url || jobData.url));
    if (!isDuplicate) {
      savedJobs.push({
        ...jobData,
        detectedAt: new Date().toISOString(),
        url: sender.tab?.url || jobData.url
      });
      await chrome.storage.local.set({ savedJobs });
    }

    // Send to API if authenticated
    if (token) {
      try {
        const response = await fetch(`${API_BASE_URL}/jobs`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            title: jobData.title,
            company: jobData.company,
            location: jobData.location,
            description: jobData.description,
            url: sender.tab?.url || jobData.url,
            source: "extension",
            raw_data: jobData
          })
        });

        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }


        // Show success notification
        chrome.notifications.create({
          type: 'basic',
          iconUrl: 'icon-128.png',
          title: 'Job Saved!',
          message: `${jobData.title} at ${jobData.company} added to your board.`
        });

      } catch (apiError) {
        console.error("Failed to send to API:", apiError);
        // Show offline notification
        chrome.notifications.create({
          type: 'basic',
          iconUrl: 'icon-128.png',
          title: 'Job Saved Locally',
          message: `Saved offline. Will sync when online.`
        });
      }
    } else {
      console.warn("User not authenticated in extension");
      chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icon-128.png',
        title: 'Job Saved Locally',
        message: `Please sign in to sync jobs.`
      });
    }

  } catch (error) {
    console.error("Failed to process job:", error);
    throw error;
  }
}

// Handle extension installation
chrome.runtime.onInstalled.addListener(() => {
});
