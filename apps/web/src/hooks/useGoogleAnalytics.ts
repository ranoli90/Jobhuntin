import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { config } from '../config';

declare global {
    interface Window {
        gtag?: (command: string, targetId: string, config?: Record<string, any>) => void;
        dataLayer?: any[];
    }
}

export function useGoogleAnalytics() {
    const location = useLocation();
    const gaId = config.analytics.gaId || 'G-P1QLYH3M13';
    const initialized = useRef(false);

    useEffect(() => {
        // If we can't find gtag, don't do anything
        if (!window.gtag) return;

        // Skip the first execution because index.html already sent the initial pageview
        if (!initialized.current) {
            initialized.current = true;
            return;
        }

        // Send page view on subsequent route changes
        // We delay slightly to ensure document title is updated if handled by Helmet
        const timeout = setTimeout(() => {
            window.gtag!('config', gaId, {
                page_path: location.pathname + location.search,
                page_title: document.title,
            });
        }, 100);

        return () => clearTimeout(timeout);
    }, [location, gaId]);
}
