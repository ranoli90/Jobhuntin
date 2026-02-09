import { LinkedInScraper } from './scrapers/linkedin'
import { JobData } from './scrapers/types'

console.log('Sorce Content Script Active')

function detectJob() {
    const url = window.location.href
    let jobData: JobData | null = null

    if (LinkedInScraper.canScrape(url)) {
        console.log('Detected LinkedIn Job Page')
        jobData = LinkedInScraper.scrape()
    }

    if (jobData) {
        console.log('Job Data Extracted:', jobData)
        // Send to background or popup
        chrome.runtime.sendMessage({ type: 'JOB_DETECTED', data: jobData })
    }
}

// Run on load and URL change (SPA)
detectJob()

let lastUrl = window.location.href
new MutationObserver(() => {
    if (window.location.href !== lastUrl) {
        lastUrl = window.location.href
        detectJob()
    }
}).observe(document, { subtree: true, childList: true })
