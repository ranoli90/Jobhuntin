// Enhanced Conversion Funnel Tracking
import { useCallback } from 'react';

export type FunnelType = 'onboarding' | 'job_search' | 'application' | 'pricing' | 'engagement';

export interface FunnelEvent {
  id: string;
  type: 'page_view' | 'form_start' | 'form_submit' | 'cta_click' | 'conversion' | 'drop_off';
  funnel: 'onboarding' | 'job_search' | 'application' | 'pricing' | 'engagement';
  step: string;
  timestamp: Date;
  userId?: string;
  sessionId: string;
  metadata?: Record<string, any>;
  value?: number; // For monetary values
}

export interface FunnelMetrics {
  totalEvents: number;
  conversions: number;
  conversionRate: number;
  dropOffRate: number;
  averageTimeToConvert: number;
  revenue: number;
}

class FunnelTracker {
  private events: FunnelEvent[] = [];
  private sessions: Map<string, Date> = new Map();
  private userSessions: Map<string, string> = new Map();

  constructor() {
    this.loadFromStorage();
    this.initializeSession();
  }

  // Initialize or get session ID
  private initializeSession(): string {
    let sessionId = sessionStorage.getItem('funnel_session_id');
    
    if (!sessionId) {
      sessionId = this.generateSessionId();
      sessionStorage.setItem('funnel_session_id', sessionId);
    }
    
    // Track session start
    if (!this.sessions.has(sessionId)) {
      this.sessions.set(sessionId, new Date());
    }
    
    return sessionId;
  }

  // Generate unique session ID
  private generateSessionId(): string {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  // Track an event
  track(event: Omit<FunnelEvent, 'id' | 'timestamp' | 'sessionId'>) {
    const sessionId = this.initializeSession();
    
    const fullEvent: FunnelEvent = {
      id: this.generateEventId(),
      timestamp: new Date(),
      sessionId,
      ...event
    };

    this.events.push(fullEvent);
    this.saveToStorage();

    // Send to analytics if available
    if (typeof window !== 'undefined' && (window as any).gtag) {
      const gtag = (window as any).gtag;
      
      // Track as custom event
      gtag('event', `${event.funnel}_${event.step}`, {
        event_category: 'funnel',
        event_label: event.type,
        value: event.value,
        custom_map: {
          'custom_parameter_1': event.userId || 'anonymous',
          'custom_parameter_2': event.step,
          'custom_parameter_3': event.funnel
        }
      });

      // Track conversion events
      if (event.type === 'conversion') {
        gtag('event', 'conversion', {
          event_category: 'ecommerce',
          event_label: event.step,
          value: event.value,
          currency: 'USD'
        });
      }
    }
  }

  // Track page view
  trackPageView(page: string, funnel: FunnelType, step: string, userId?: string) {
    this.track({
      type: 'page_view',
      funnel,
      step,
      userId,
      metadata: { page }
    });
  }

  // Track form interaction
  trackFormStart(formName: string, funnel: FunnelType, step: string, userId?: string) {
    this.track({
      type: 'form_start',
      funnel,
      step: formName,
      userId,
      metadata: { formName }
    });
  }

  trackFormSubmit(formName: string, funnel: FunnelType, step: string, userId?: string, value?: number) {
    this.track({
      type: 'form_submit',
      funnel,
      step: formName,
      userId,
      value,
      metadata: { formName }
    });
  }

  // Track CTA clicks
  trackCTAClick(ctaName: string, funnel: FunnelType, step: string, userId?: string) {
    this.track({
      type: 'cta_click',
      funnel,
      step: ctaName,
      userId,
      metadata: { ctaName }
    });
  }

  // Track conversions
  trackConversion(conversionType: string, funnel: FunnelType, step: string, userId?: string, value?: number) {
    this.track({
      type: 'conversion',
      funnel,
      step: conversionType,
      userId,
      value,
      metadata: { conversionType }
    });
  }

  // Track drop-offs
  trackDropOff(funnel: FunnelType, step: string, userId?: string, reason?: string) {
    this.track({
      type: 'drop_off',
      funnel,
      step,
      userId,
      metadata: { reason }
    });
  }

  // Associate user with session
  associateUser(userId: string) {
    const sessionId = this.initializeSession();
    this.userSessions.set(userId, sessionId);
  }

  // Get funnel metrics
  getMetrics(funnel: string, step?: string, timeRange?: { start: Date; end: Date }): FunnelMetrics {
    let filteredEvents = this.events.filter(e => e.funnel === funnel);
    
    if (step) {
      filteredEvents = filteredEvents.filter(e => e.step === step);
    }
    
    if (timeRange) {
      filteredEvents = filteredEvents.filter(e => 
        e.timestamp >= timeRange.start && e.timestamp <= timeRange.end
      );
    }

    const conversions = filteredEvents.filter(e => e.type === 'conversion');
    const totalEvents = filteredEvents.length;
    const revenue = conversions.reduce((sum, event) => sum + (event.value || 0), 0);

    // Calculate drop-off rate
    const dropOffEvents = filteredEvents.filter(e => e.type === 'drop_off');
    const dropOffRate = totalEvents > 0 ? dropOffEvents.length / totalEvents : 0;

    // Calculate average time to convert
    const conversionEvents = filteredEvents.filter(e => e.type === 'conversion');
    const avgTimeToConvert = this.calculateAverageTimeToConvert(conversionEvents);

    return {
      totalEvents,
      conversions: conversions.length,
      conversionRate: totalEvents > 0 ? conversions.length / totalEvents : 0,
      dropOffRate,
      averageTimeToConvert: avgTimeToConvert,
      revenue
    };
  }

  // Get funnel flow visualization
  getFunnelFlow(funnel: string): Array<{ step: string; events: number; conversions: number; rate: number }> {
    const steps = this.getFunnelSteps(funnel);
    
    return steps.map(step => {
      const stepEvents = this.events.filter(e => e.funnel === funnel && e.step === step);
      const stepConversions = stepEvents.filter(e => e.type === 'conversion');
      
      return {
        step,
        events: stepEvents.length,
        conversions: stepConversions.length,
        rate: stepEvents.length > 0 ? stepConversions.length / stepEvents.length : 0
      };
    });
  }

  // Get funnel steps in order
  private getFunnelSteps(funnel: string): string[] {
    const stepMap: Record<string, string[]> = {
      onboarding: [
        'homepage_visit',
        'email_capture',
        'magic_link_sent',
        'onboarding_start',
        'resume_upload',
        'preferences',
        'skills_review',
        'contact_confirm',
        'onboarding_complete'
      ],
      job_search: [
        'dashboard_visit',
        'jobs_view',
        'filter_applied',
        'job_swipe',
        'job_details',
        'job_apply'
      ],
      application: [
        'application_start',
        'application_submit',
        'application_status_update',
        'interview_scheduled',
        'offer_received'
      ],
      pricing: [
        'pricing_page_visit',
        'plan_comparison',
        'upgrade_click',
        'payment_start',
        'payment_complete'
      ],
      engagement: [
        'daily_active',
        'return_visit',
        'feature_usage',
        'social_share',
        'referral'
      ]
    };

    return stepMap[funnel] || [];
  }

  // Calculate average time to convert
  private calculateAverageTimeToConvert(conversions: FunnelEvent[]): number {
    if (conversions.length === 0) return 0;

    const sessionTimes = conversions.map(conv => {
      const sessionStart = this.sessions.get(conv.sessionId);
      return sessionStart ? conv.timestamp.getTime() - sessionStart.getTime() : 0;
    }).filter(time => time > 0);

    if (sessionTimes.length === 0) return 0;
    
    return sessionTimes.reduce((sum, time) => sum + time, 0) / sessionTimes.length;
  }

  // Generate unique event ID
  private generateEventId(): string {
    return 'event_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  // Save to localStorage
  private saveToStorage() {
    try {
      const data = {
        events: this.events,
        sessions: Array.from(this.sessions.entries()),
        userSessions: Array.from(this.userSessions.entries())
      };
      localStorage.setItem('funnel_tracking', JSON.stringify(data));
    } catch (error) {
      console.error('Failed to save funnel tracking data:', error);
    }
  }

  // Load from localStorage
  private loadFromStorage() {
    try {
      const data = localStorage.getItem('funnel_tracking');
      if (!data) return;

      const parsed = JSON.parse(data);
      
      this.events = parsed.events || [];
      this.sessions = new Map(parsed.sessions || []);
      this.userSessions = new Map(parsed.userSessions || []);
    } catch (error) {
      console.error('Failed to load funnel tracking data:', error);
    }
  }

  // Clear data
  clearData() {
    this.events = [];
    this.sessions.clear();
    this.userSessions.clear();
    localStorage.removeItem('funnel_tracking');
    sessionStorage.removeItem('funnel_session_id');
  }
}

// Singleton instance
export const funnelTracker = new FunnelTracker();

// React hook for funnel tracking
export function useFunnelTracking(funnel: FunnelType, step: string, userId?: string) {
  const trackPageView = useCallback((metadata?: Record<string, any>) => {
    funnelTracker.trackPageView(window.location.pathname, funnel, step, userId);
  }, [funnel, step, userId]);

  const trackFormStart = useCallback((formName: string) => {
    funnelTracker.trackFormStart(formName, funnel, step, userId);
  }, [funnel, step, userId]);

  const trackFormSubmit = useCallback((formName: string, value?: number) => {
    funnelTracker.trackFormSubmit(formName, funnel, step, userId, value);
  }, [funnel, step, userId]);

  const trackCTAClick = useCallback((ctaName: string) => {
    funnelTracker.trackCTAClick(ctaName, funnel, step, userId);
  }, [funnel, step, userId]);

  const trackConversion = useCallback((conversionType: string, value?: number) => {
    funnelTracker.trackConversion(conversionType, funnel, step, userId, value);
  }, [funnel, step, userId]);

  const trackDropOff = useCallback((reason?: string) => {
    funnelTracker.trackDropOff(funnel, step, userId, reason);
  }, [funnel, step, userId]);

  return {
    trackPageView,
    trackFormStart,
    trackFormSubmit,
    trackCTAClick,
    trackConversion,
    trackDropOff
  };
}
