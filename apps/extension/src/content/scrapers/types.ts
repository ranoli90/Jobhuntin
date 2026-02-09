export interface JobData {
    title: string
    company: string
    location: string
    description: string
    url: string
    source: 'linkedin' | 'indeed' | 'glassdoor' | 'other'
}

export interface Scraper {
    canScrape(url: string): boolean
    scrape(): JobData | null
}
