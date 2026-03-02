// Simple A/B Testing Framework
import { useState, useEffect, useCallback } from 'react';

export interface ExperimentConfig {
  id: string;
  name: string;
  variants: {
    [key: string]: {
      name: string;
      weight: number; // 0-1, should sum to 1.0
    };
  };
  targetUrl?: string;
  startDate?: Date;
  endDate?: Date;
}

export interface ABTestResult {
  experimentId: string;
  variant: string;
  timestamp: Date;
  conversion?: boolean;
  metadata?: Record<string, any>;
}

class ABTestingManager {
  private experiments: Map<string, ExperimentConfig> = new Map();
  private userAssignments: Map<string, string> = new Map();
  private results: ABTestResult[] = [];

  constructor() {
    this.loadFromStorage();
  }

  // Register a new experiment
  registerExperiment(config: ExperimentConfig) {
    this.experiments.set(config.id, config);
    this.saveToStorage();
  }

  // Get the variant for a user
  getVariant(experimentId: string, userId?: string): string | null {
    const config = this.experiments.get(experimentId);
    if (!config) return null;

    // Check if user is already assigned
    const key = `${experimentId}:${userId || 'anonymous'}`;
    if (this.userAssignments.has(key)) {
      return this.userAssignments.get(key)!;
    }

    // Check if experiment is active
    const now = new Date();
    if (config.startDate && now < config.startDate) return null;
    if (config.endDate && now > config.endDate) return null;

    // Assign variant based on weights
    const random = Math.random();
    let cumulative = 0;
    
    for (const [variantKey, variant] of Object.entries(config.variants)) {
      cumulative += variant.weight;
      if (random <= cumulative) {
        this.userAssignments.set(key, variantKey);
        this.saveToStorage();
        
        // Track assignment
        this.trackResult({
          experimentId,
          variant: variantKey,
          timestamp: now
        });
        
        return variantKey;
      }
    }

    return null;
  }

  // Track a conversion event
  trackConversion(experimentId: string, userId?: string, metadata?: Record<string, any>) {
    const variant = this.getVariant(experimentId, userId);
    if (!variant) return;

    this.trackResult({
      experimentId,
      variant,
      timestamp: new Date(),
      conversion: true,
      metadata
    });
  }

  // Track any result (assignment or conversion)
  private trackResult(result: ABTestResult) {
    this.results.push(result);
    this.saveToStorage();
  }

  // Get experiment results
  getResults(experimentId: string): ABTestResult[] {
    return this.results.filter(r => r.experimentId === experimentId);
  }

  // Get conversion rate for a variant
  getConversionRate(experimentId: string, variant: string): number {
    const results = this.getResults(experimentId);
    const variantResults = results.filter(r => r.variant === variant);
    const conversions = variantResults.filter(r => r.conversion).length;
    const total = variantResults.length;
    
    return total > 0 ? conversions / total : 0;
  }

  // Save to localStorage
  private saveToStorage() {
    try {
      const data = {
        experiments: Array.from(this.experiments.entries()),
        userAssignments: Array.from(this.userAssignments.entries()),
        results: this.results
      };
      localStorage.setItem('ab_testing', JSON.stringify(data));
    } catch (error) {
      console.error('Failed to save AB testing data:', error);
    }
  }

  // Load from localStorage
  private loadFromStorage() {
    try {
      const data = localStorage.getItem('ab_testing');
      if (!data) return;

      const parsed = JSON.parse(data);
      
      this.experiments = new Map(parsed.experiments || []);
      this.userAssignments = new Map(parsed.userAssignments || []);
      this.results = parsed.results || [];
    } catch (error) {
      console.error('Failed to load AB testing data:', error);
    }
  }

  // Clear all data
  clearData() {
    this.experiments.clear();
    this.userAssignments.clear();
    this.results = [];
    localStorage.removeItem('ab_testing');
  }
}

// Singleton instance
export const abTesting = new ABTestingManager();

// Hook for using AB tests in React components
export function useABTest(experimentId: string, userId?: string) {
  const [variant, setVariant] = useState<string | null>(null);

  useEffect(() => {
    const assignedVariant = abTesting.getVariant(experimentId, userId);
    setVariant(assignedVariant);
  }, [experimentId, userId]);

  const trackConversion = useCallback((metadata?: Record<string, any>) => {
    abTesting.trackConversion(experimentId, userId, metadata);
  }, [experimentId, userId]);

  return { variant, trackConversion };
}

// Predefined experiments
export const EXPERIMENTS = {
  // Homepage CTA button color
  HOMEPAGE_CTA_COLOR: {
    id: 'homepage-cta-color',
    name: 'Homepage CTA Button Color',
    variants: {
      purple: { name: 'Purple', weight: 0.5 },
      green: { name: 'Green', weight: 0.5 }
    }
  },
  
  // Onboarding flow order
  ONBOARDING_ORDER: {
    id: 'onboarding-order',
    name: 'Onboarding Step Order',
    variants: {
      original: { name: 'Original Order', weight: 0.5 },
      optimized: { name: 'Optimized Order', weight: 0.5 }
    }
  },
  
  // Pricing page layout
  PRICING_LAYOUT: {
    id: 'pricing-layout',
    name: 'Pricing Page Layout',
    variants: {
      standard: { name: 'Standard', weight: 0.7 },
      compact: { name: 'Compact', weight: 0.3 }
    }
  }
} as const;

// Initialize experiments (in production only)
if (typeof window !== 'undefined' && import.meta.env.PROD) {
  // Register experiments
  Object.values(EXPERIMENTS).forEach(config => {
    abTesting.registerExperiment(config);
  });
}
