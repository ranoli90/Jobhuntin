/**
 * Synthetic Traffic Simulation Script
 * Models user interaction patterns (CTR, Dwell Time, Bounce Rate) 
 * to simulate ranking signals for the JobHuntin platform.
 * 
 * Used for predictive modeling of visibility amplification.
 */

const fs = require('fs');
const path = require('path');

const TRAFFIC_MODELS = [
  {
    segment: 'High Intent Job Seeker',
    entryPage: '/jobs/marketing-manager/denver',
    behavior: {
      dwellTime: '4m 30s',
      pagesPerSession: 3.5,
      conversionProb: 0.12,
      bounceRate: 0.15
    }
  },
  {
    segment: 'Tech Influencer',
    entryPage: '/chrome-extension',
    behavior: {
      dwellTime: '1m 15s',
      pagesPerSession: 1.2,
      conversionProb: 0.05,
      bounceRate: 0.45
    }
  },
  {
    segment: 'Recruiter / Enterprise',
    entryPage: '/recruiters',
    behavior: {
      dwellTime: '6m 00s',
      pagesPerSession: 5.0,
      conversionProb: 0.02,
      bounceRate: 0.10
    }
  }
];

const simulateTraffic = () => {
  console.log('--- Starting Synthetic Traffic Simulation ---');
  
  const simulationResults = TRAFFIC_MODELS.map(model => {
    console.log("Simulating segment:", model.segment, "...");
    
    // Simulate some randomness in metrics
    const variance = () => (Math.random() * 0.2) - 0.1; // +/- 10%
    
    return {
      segment: model.segment,
      simulatedMetrics: {
        avgSessionDuration: model.behavior.dwellTime,
        bounceRate: (model.behavior.bounceRate + variance()).toFixed(2),
        conversionRate: (model.behavior.conversionProb + variance()).toFixed(2),
        estimatedSearchRankBoost: model.segment === 'High Intent Job Seeker' ? '+2.5 positions' : '+0.5 positions'
      }
    };
  });

  const reportPath = path.resolve(__dirname, '../../reports/traffic-simulation-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(simulationResults, null, 2));
  
  console.log('\n--- Simulation Complete ---');
  simulationResults.forEach((res) => {
    console.log("-", res.segment + ": Est. Rank Boost:", res.simulatedMetrics.estimatedSearchRankBoost);
  });
  console.log("Detailed report saved to:", reportPath);
};

simulateTraffic();
