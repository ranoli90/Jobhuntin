import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { config } from '../config';

export function useGoogleAnalytics() {
    const location = useLocation();
    const gaId = config.analytics.gaId;
    if (!gaId) return;
    const initialized = useRef(false);

    // Grant consent on mount if user previously accepted (so initial pageview can fire)
    useEffect(() => {
        if (!window.gtag) return;
        const consent = localStorage.getItem('jobhuntin-cookie-consent-v2');
        if (consent) {
            try {
                const parsed = JSON.parse(consent);
                if (parsed?.analytics === true) {
                    window.gtag!('consent', 'update', {
                        analytics_storage: 'granted',
                        ad_storage: parsed?.marketing ? 'granted' : 'denied',
                        ad_user_data: parsed?.marketing ? 'granted' : 'denied',
                        ad_personalization: parsed?.marketing ? 'granted' : 'denied',
                    });
                }
            } catch {
                // No valid consent = keep denied
            }
        }
    }, []);

    useEffect(() => {
        // If we can't find gtag, don't do anything
        if (!window.gtag) return;

        // Respect cookie consent - only send pageviews if user accepted
        const consent = localStorage.getItem('jobhuntin-cookie-consent-v2');
        if (consent) {
            try {
                const parsed = JSON.parse(consent);
                if (parsed?.analytics !== true) return;
            } catch {
                return; // No valid consent = don't track
            }
        } else {
            return; // No consent yet = don't track (GDPR)
        }

        // Skip the first execution because index.html config handles initial load
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
