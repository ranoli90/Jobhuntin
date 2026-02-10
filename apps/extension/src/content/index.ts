import { LinkedInScraper } from './scrapers/linkedin'
import type { JobData } from './scrapers/types'

// console removed: Content Script Active

let detectTimeout: ReturnType<typeof setTimeout> | null = null

function detectJob() {
    const url = window.location.href
    let jobData: JobData | null = null

    if (LinkedInScraper.canScrape(url)) {
        jobData = LinkedInScraper.scrape()
    }

    if (jobData) {
        // Send to background or popup
        chrome.runtime.sendMessage({ type: 'JOB_DETECTED', data: jobData }, () => {
            // Silently handle disconnected port (extension reload, etc.)
            if (chrome.runtime.lastError) {
                // Expected when extension context invalidated
            }
        })
    }
}

// Debounced version for MutationObserver to avoid excessive calls
function debouncedDetectJob() {
    if (detectTimeout) clearTimeout(detectTimeout)
    detectTimeout = setTimeout(detectJob, 500)
}

// Run on load (with a small delay to let SPA content render)
setTimeout(detectJob, 1000)

let lastUrl = window.location.href
new MutationObserver(() => {
    if (window.location.href !== lastUrl) {
        lastUrl = window.location.href
        debouncedDetectJob()
    }
}).observe(document, { subtree: true, childList: true })
