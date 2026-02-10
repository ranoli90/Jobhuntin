import type { JobData, Scraper } from './types'

export const LinkedInScraper: Scraper = {
    canScrape(url: string) {
        return url.includes('linkedin.com/jobs') || url.includes('linkedin.com/search')
    },

    scrape(): JobData | null {
        // LinkedIn has dynamic classes that change frequently.
        // Use multiple fallback selectors ordered by reliability.

        const titleEl = document.querySelector('.job-details-jobs-unified-top-card__job-title')
            ?? document.querySelector('.jobs-unified-top-card__job-title')
            ?? document.querySelector('h1.t-24')
            ?? document.querySelector('h1')

        const companyEl = document.querySelector('.job-details-jobs-unified-top-card__company-name')
            ?? document.querySelector('.job-details-jobs-unified-top-card__company-url')
            ?? document.querySelector('.jobs-unified-top-card__company-name a')

        const locationEl = document.querySelector('.job-details-jobs-unified-top-card__workplace-type')
            ?? document.querySelector('.jobs-unified-top-card__bullet')

        const descriptionEl = document.querySelector('#job-details')
            ?? document.querySelector('.jobs-description__content')
            ?? document.querySelector('.jobs-description')

        if (!titleEl) return null

        const title = titleEl.textContent?.trim() || ''
        const company = companyEl?.textContent?.trim() || ''
        const location = locationEl?.textContent?.trim() || ''

        // Extract text content instead of innerHTML to avoid XSS risk
        // when this data is rendered elsewhere in the app
        const description = descriptionEl?.textContent?.trim() || ''

        if (!title || !description) return null

        return {
            title,
            company,
            location,
            description,
            url: window.location.href,
            source: 'linkedin'
        }
    }
}
