import type { JobData, Scraper } from './types'

export const LinkedInScraper: Scraper = {
    canScrape(url: string) {
        return url.includes('linkedin.com/jobs') || url.includes('linkedin.com/search')
    },

    scrape(): JobData | null {
        // Attempt to find the job details container
        // LinkedIn has dynamic classes, so we might need multiple selectors

        const titleEl = document.querySelector('.job-details-jobs-unified-top-card__job-title')
            || document.querySelector('h1')

        const companyEl = document.querySelector('.job-details-jobs-unified-top-card__company-name')
            || document.querySelector('.job-details-jobs-unified-top-card__company-url')

        const locationEl = document.querySelector('.job-details-jobs-unified-top-card__workplace-type')

        const descriptionEl = document.querySelector('#job-details')
            || document.querySelector('.jobs-description__content')

        if (!titleEl || !descriptionEl) return null

        return {
            title: titleEl.textContent?.trim() || '',
            company: companyEl?.textContent?.trim() || '',
            location: locationEl?.textContent?.trim() || '',
            description: descriptionEl.innerHTML,
            url: window.location.href,
            source: 'linkedin'
        }
    }
}
