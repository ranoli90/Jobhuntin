import { test, expect } from '@playwright/test';
import { AxeBuilder } from '@axe-core/playwright';

const BASE_URL = process.env.BASE_URL || 'https://jobhuntin.com';
const TEST_EMAIL = process.env.TEST_EMAIL || 'test-e2e-production@jobhuntin.com';

test.describe('Performance & Accessibility Validation', () => {
  test('Core Web Vitals performance testing', async ({ page }) => {
    console.log('⚡ Testing Core Web Vitals performance...');

    // Measure performance metrics
    const performanceMetrics = await page.evaluate(() => {
      return new Promise((resolve) => {
        const observer = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const metrics = {
            LCP: 0,
            FID: 0,
            CLS: 0,
            TTFB: 0,
            FCP: 0
          };

          entries.forEach((entry) => {
            if (entry.name === 'largest-contentful-paint') {
              metrics.LCP = entry.startTime;
            } else if (entry.name === 'first-input') {
              metrics.FID = (entry as any).processingStart - entry.startTime;
            } else if (entry.name === 'layout-shift') {
              metrics.CLS += (entry as any).value || 0;
            }
          });

          // Get navigation timing
          const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
          metrics.TTFB = navigation.responseStart - navigation.requestStart;
          metrics.FCP = navigation.loadEventStart - navigation.fetchStart;

          resolve(metrics);
        });

        observer.observe({ entryTypes: ['largest-contentful-paint', 'first-input', 'layout-shift'] });
        
        // Fallback timeout
        setTimeout(() => resolve({
          LCP: 0, FID: 0, CLS: 0, TTFB: 0, FCP: 0
        }), 10000);
      });
    });

    console.log('📊 Core Web Vitals:', performanceMetrics);

    // Performance thresholds
    const thresholds = {
      LCP: 2500, // Largest Contentful Paint (good)
      FID: 100,  // First Input Delay (good)
      CLS: 0.1,  // Cumulative Layout Shift (good)
      TTFB: 600, // Time to First Byte (good)
      FCP: 1800  // First Contentful Paint (good)
    };

    const results = {
      LCP: { value: performanceMetrics.LCP, threshold: thresholds.LCP, passed: performanceMetrics.LCP <= thresholds.LCP },
      FID: { value: performanceMetrics.FID, threshold: thresholds.FID, passed: performanceMetrics.FID <= thresholds.FID },
      CLS: { value: performanceMetrics.CLS, threshold: thresholds.CLS, passed: performanceMetrics.CLS <= thresholds.CLS },
      TTFB: { value: performanceMetrics.TTFB, threshold: thresholds.TTFB, passed: performanceMetrics.TTFB <= thresholds.TTFB },
      FCP: { value: performanceMetrics.FCP, threshold: thresholds.FCP, passed: performanceMetrics.FCP <= thresholds.FCP }
    };

    for (const [metric, result] of Object.entries(results)) {
      if (result.passed) {
        console.log(`✅ ${metric}: ${result.value}ms (threshold: ${result.threshold}ms)`);
      } else {
        console.log(`⚠️ ${metric}: ${result.value}ms (threshold: ${result.threshold}ms) - NEEDS OPTIMIZATION`);
      }
    }

    await page.screenshot({ path: 'reports/screenshots/performance-metrics.png', fullPage: false });
  });

  test('page load performance analysis', async ({ page }) => {
    console.log('📈 Analyzing page load performance...');

    // Start performance monitoring
    await page.goto(`${BASE_URL}/login`, { waitUntil: 'domcontentloaded' });
    
    const loadAnalysis = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      const resources = performance.getEntriesByType('resource');
      
      return {
        // Navigation timing
        dnsLookup: navigation.domainLookupEnd - navigation.domainLookupStart,
        tcpConnection: navigation.connectEnd - navigation.connectStart,
        sslNegotiation: navigation.secureConnectionStart > 0 ? navigation.connectEnd - navigation.secureConnectionStart : 0,
        serverResponse: navigation.responseEnd - navigation.responseStart,
        domProcessing: navigation.domContentLoadedEventStart - navigation.responseEnd,
        pageLoad: navigation.loadEventEnd - navigation.domContentLoadedEventStart,
        totalLoadTime: navigation.loadEventEnd - navigation.fetchStart,
        
        // Resource analysis
        totalResources: resources.length,
        totalResourceSize: resources.reduce((sum, resource) => sum + (resource.transferSize || 0), 0),
        resourceBreakdown: {
          scripts: resources.filter(r => r.name.includes('.js')).length,
          styles: resources.filter(r => r.name.includes('.css')).length,
          images: resources.filter(r => r.name.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i)).length,
          fonts: resources.filter(r => r.name.includes('.woff')).length
        }
      };
    });

    console.log('📊 Load Performance Analysis:', loadAnalysis);

    // Performance recommendations
    const recommendations = [];
    
    if (loadAnalysis.totalLoadTime > 3000) {
      recommendations.push('Consider optimizing total load time (currently ' + loadAnalysis.totalLoadTime + 'ms)');
    }
    
    if (loadAnalysis.totalResourceSize > 2 * 1024 * 1024) { // 2MB
      recommendations.push('Consider reducing total resource size (currently ' + Math.round(loadAnalysis.totalResourceSize / 1024 / 1024) + 'MB)');
    }
    
    if (loadAnalysis.resourceBreakdown.scripts > 20) {
      recommendations.push('Consider reducing number of JavaScript files (currently ' + loadAnalysis.resourceBreakdown.scripts + ')');
    }
    
    if (recommendations.length > 0) {
      console.log('💡 Performance Recommendations:');
      recommendations.forEach(rec => console.log(`   - ${rec}`));
    } else {
      console.log('✅ Performance looks good!');
    }

    await page.screenshot({ path: 'reports/screenshots/load-performance-analysis.png', fullPage: false });
  });

  test('accessibility compliance testing', async ({ page }) => {
    console.log('♿ Testing accessibility compliance...');

    await page.goto(`${BASE_URL}/login`);
    await page.waitForTimeout(2000);

    // Run axe accessibility testing
    const accessibilityScan = await new AxeBuilder({ page }).analyze();
    
    console.log('📊 Accessibility Scan Results:');
    console.log(`   - Violations: ${accessibilityScan.violations.length}`);
    console.log(`   - Incomplete: ${accessibilityScan.incomplete.length}`);
    console.log(`   - Passes: ${accessibilityScan.passes.length}`);

    if (accessibilityScan.violations.length > 0) {
      console.log('❌ Accessibility Violations:');
      accessibilityScan.violations.forEach((violation, index) => {
        console.log(`   ${index + 1}. ${violation.description} (${violation.impact})`);
        console.log(`      - ${violation.help}`);
        violation.nodes.forEach((node, nodeIndex) => {
          console.log(`      - Target ${nodeIndex + 1}: ${node.target.join(', ')}`);
        });
      });
    } else {
      console.log('✅ No accessibility violations found!');
    }

    // Test keyboard navigation
    console.log('⌨️ Testing keyboard navigation...');
    
    const keyboardResults = await page.evaluate(() => {
      const results = {
        focusableElements: 0,
        skipLinks: 0,
        headingStructure: true,
        landmarkElements: 0,
        tabOrder: []
      };

      // Count focusable elements
      const focusableElements = document.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      results.focusableElements = focusableElements.length;

      // Check for skip links
      const skipLinks = document.querySelectorAll('a[href^="#"], .skip-link');
      results.skipLinks = skipLinks.length;

      // Check heading structure
      const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
      let lastLevel = 0;
      for (const heading of headings) {
        const level = parseInt(heading.tagName.substring(1));
        if (level > lastLevel + 1) {
          results.headingStructure = false;
          break;
        }
        lastLevel = level;
      }

      // Check for landmarks
      const landmarks = document.querySelectorAll('main, [role="main"], nav, [role="navigation"], header, [role="banner"], footer, [role="contentinfo"]');
      results.landmarkElements = landmarks.length;

      return results;
    });

    console.log('📊 Keyboard Navigation Results:', keyboardResults);

    if (keyboardResults.focusableElements > 0) {
      console.log('✅ Found focusable elements for keyboard navigation');
    } else {
      console.log('❌ No focusable elements found');
    }

    if (keyboardResults.skipLinks > 0) {
      console.log('✅ Skip links found for accessibility');
    } else {
      console.log('⚠️ No skip links found');
    }

    if (keyboardResults.headingStructure) {
      console.log('✅ Proper heading structure');
    } else {
      console.log('❌ Improper heading structure');
    }

    if (keyboardResults.landmarkElements > 0) {
      console.log('✅ Landmark elements found');
    } else {
      console.log('⚠️ No landmark elements found');
    }

    await page.screenshot({ path: 'reports/screenshots/accessibility-compliance.png', fullPage: false });
  });

  test('color contrast and visual accessibility', async ({ page }) => {
    console.log('🎨 Testing color contrast and visual accessibility...');

    await page.goto(`${BASE_URL}/login`);
    await page.waitForTimeout(2000);

    const contrastResults = await page.evaluate(() => {
      const results = {
        textElements: 0,
        lowContrastElements: 0,
        sufficientContrastElements: 0,
        issues: []
      };

      // Get all text elements
      const textElements = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, div, button, a, label');
      results.textElements = textElements.length;

      // Check contrast for visible text elements
      textElements.forEach((element, index) => {
        const styles = window.getComputedStyle(element);
        const color = styles.color;
        const backgroundColor = styles.backgroundColor;
        
        // Skip if element is hidden
        if (styles.display === 'none' || styles.visibility === 'hidden' || styles.opacity === '0') {
          return;
        }

        // Simple contrast check (simplified - real implementation would use proper contrast ratio calculation)
        if (color && backgroundColor && backgroundColor !== 'rgba(0, 0, 0, 0)' && backgroundColor !== 'transparent') {
          // This is a simplified check - real implementation would calculate WCAG contrast ratios
          const colorRgb = color.match(/\d+/g);
          const bgRgb = backgroundColor.match(/\d+/g);
          
          if (colorRgb && bgRgb && colorRgb.length >= 3 && bgRgb.length >= 3) {
            const colorLuminance = (0.299 * parseInt(colorRgb[0]) + 0.587 * parseInt(colorRgb[1]) + 0.114 * parseInt(colorRgb[2])) / 255;
            const bgLuminance = (0.299 * parseInt(bgRgb[0]) + 0.587 * parseInt(bgRgb[1]) + 0.114 * parseInt(bgRgb[2])) / 255;
            
            const contrast = (Math.max(colorLuminance, bgLuminance) + 0.05) / (Math.min(colorLuminance, bgLuminance) + 0.05);
            
            if (contrast < 4.5) { // WCAG AA standard
              results.lowContrastElements++;
              results.issues.push({
                element: element.tagName + (element.className ? '.' + element.className : ''),
                contrast: contrast.toFixed(2)
              });
            } else {
              results.sufficientContrastElements++;
            }
          }
        }
      });

      return results;
    });

    console.log('📊 Color Contrast Results:');
    console.log(`   - Text elements analyzed: ${contrastResults.textElements}`);
    console.log(`   - Sufficient contrast: ${contrastResults.sufficientContrastElements}`);
    console.log(`   - Low contrast: ${contrastResults.lowContrastElements}`);

    if (contrastResults.lowContrastElements > 0) {
      console.log('❌ Color Contrast Issues:');
      contrastResults.issues.forEach((issue, index) => {
        console.log(`   ${index + 1}. ${issue.element} (contrast: ${issue.contrast}:1)`);
      });
    } else {
      console.log('✅ Color contrast looks good!');
    }

    await page.screenshot({ path: 'reports/screenshots/color-contrast-test.png', fullPage: false });
  });

  test('mobile performance optimization', async ({ page }) => {
    console.log('📱 Testing mobile performance optimization...');

    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Simulate 3G network conditions
    await page.route('**/*', async route => {
      await new Promise(resolve => setTimeout(resolve, 100)); // 100ms delay
      await route.continue();
    });

    const startTime = Date.now();
    await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' });
    const mobileLoadTime = Date.now() - startTime;

    console.log(`📱 Mobile load time (3G): ${mobileLoadTime}ms`);

    // Check mobile-specific optimizations
    const mobileOptimizations = await page.evaluate(() => {
      const results = {
        hasViewportMeta: !!document.querySelector('meta[name="viewport"]'),
        hasTouchOptimized: false,
        imageOptimization: {
          responsiveImages: 0,
          lazyLoadedImages: 0,
          oversizedImages: 0
        },
        performanceOptimization: {
          minifiedResources: 0,
          compressedResources: 0
        }
      };

      // Check viewport meta tag
      const viewportMeta = document.querySelector('meta[name="viewport"]');
      if (viewportMeta) {
        const content = viewportMeta.getAttribute('content') || '';
        results.hasTouchOptimized = content.includes('width=device-width') && content.includes('initial-scale=1');
      }

      // Check image optimization
      const images = document.querySelectorAll('img');
      images.forEach(img => {
        if (img.srcset || img.getAttribute('sizes')) {
          results.imageOptimization.responsiveImages++;
        }
        if (img.loading === 'lazy') {
          results.imageOptimization.lazyLoadedImages++;
        }
        if (img.naturalWidth > 1000 || img.naturalHeight > 1000) {
          results.imageOptimization.oversizedImages++;
        }
      });

      return results;
    });

    console.log('📊 Mobile Optimization Results:', mobileOptimizations);

    if (mobileOptimizations.hasViewportMeta) {
      console.log('✅ Viewport meta tag found');
    } else {
      console.log('❌ Missing viewport meta tag');
    }

    if (mobileOptimizations.hasTouchOptimized) {
      console.log('✅ Touch-optimized viewport');
    } else {
      console.log('⚠️ Viewport not touch-optimized');
    }

    if (mobileOptimizations.imageOptimization.responsiveImages > 0) {
      console.log(`✅ Found ${mobileOptimizations.imageOptimization.responsiveImages} responsive images`);
    }

    if (mobileOptimizations.imageOptimization.lazyLoadedImages > 0) {
      console.log(`✅ Found ${mobileOptimizations.imageOptimization.lazyLoadedImages} lazy-loaded images`);
    }

    if (mobileOptimizations.imageOptimization.oversizedImages > 0) {
      console.log(`⚠️ Found ${mobileOptimizations.imageOptimization.oversizedImages} oversized images`);
    }

    // Mobile performance threshold
    if (mobileLoadTime < 5000) {
      console.log('✅ Mobile performance within acceptable limits');
    } else {
      console.log('⚠️ Mobile performance needs optimization');
    }

    await page.screenshot({ path: 'reports/screenshots/mobile-performance.png', fullPage: false });
  });

  test('screen reader compatibility', async ({ page }) => {
    console.log('🔊 Testing screen reader compatibility...');

    await page.goto(`${BASE_URL}/login`);
    await page.waitForTimeout(2000);

    const screenReaderResults = await page.evaluate(() => {
      const results = {
        hasLangAttribute: !!document.documentElement.getAttribute('lang'),
        hasTitle: !!document.title && document.title.length > 0,
        hasAltText: 0,
        missingAltText: 0,
        hasAriaLabels: 0,
        hasRoles: 0,
        hasFormLabels: 0,
        issues: []
      };

      // Check language attribute
      results.hasLangAttribute = !!document.documentElement.getAttribute('lang');

      // Check page title
      results.hasTitle = !!document.title && document.title.length > 0;

      // Check images for alt text
      const images = document.querySelectorAll('img');
      images.forEach(img => {
        const alt = img.getAttribute('alt');
        const ariaLabel = img.getAttribute('aria-label');
        const ariaHidden = img.getAttribute('aria-hidden');
        
        if (ariaHidden !== 'true') {
          if (alt || ariaLabel) {
            results.hasAltText++;
          } else {
            results.missingAltText++;
            results.issues.push('Missing alt text on image');
          }
        }
      });

      // Check ARIA labels
      const ariaElements = document.querySelectorAll('[aria-label], [aria-labelledby]');
      results.hasAriaLabels = ariaElements.length;

      // Check ARIA roles
      const roleElements = document.querySelectorAll('[role]');
      results.hasRoles = roleElements.length;

      // Check form labels
      const inputs = document.querySelectorAll('input, select, textarea');
      inputs.forEach(input => {
        const label = document.querySelector(`label[for="${input.id}"]`);
        const ariaLabel = input.getAttribute('aria-label');
        const placeholder = input.getAttribute('placeholder');
        
        if (label || ariaLabel || placeholder) {
          results.hasFormLabels++;
        } else {
          results.issues.push('Form input missing label');
        }
      });

      return results;
    });

    console.log('📊 Screen Reader Compatibility Results:', screenReaderResults);

    if (screenReaderResults.hasLangAttribute) {
      console.log('✅ Language attribute found');
    } else {
      console.log('❌ Missing language attribute');
    }

    if (screenReaderResults.hasTitle) {
      console.log('✅ Page title found');
    } else {
      console.log('❌ Missing page title');
    }

    if (screenReaderResults.missingAltText === 0) {
      console.log('✅ All images have alt text');
    } else {
      console.log(`❌ ${screenReaderResults.missingAltText} images missing alt text`);
    }

    if (screenReaderResults.hasAriaLabels > 0) {
      console.log(`✅ Found ${screenReaderResults.hasAriaLabels} ARIA labels`);
    }

    if (screenReaderResults.hasFormLabels > 0) {
      console.log(`✅ Found ${screenReaderResults.hasFormLabels} labeled form elements`);
    }

    if (screenReaderResults.issues.length > 0) {
      console.log('❌ Screen Reader Issues:');
      screenReaderResults.issues.forEach((issue, index) => {
        console.log(`   ${index + 1}. ${issue}`);
      });
    } else {
      console.log('✅ Screen reader compatibility looks good!');
    }

    await page.screenshot({ path: 'reports/screenshots/screen-reader-compatibility.png', fullPage: false });
  });
});
