import AxeBuilder from '@axe-core/playwright';
import type { Page } from '@playwright/test';

export type AccessibilityViolation = {
  id: string;
  impact?: string;
  description: string;
  helpUrl: string;
  nodes: { target: string[]; html: string }[];
};

export async function runAxeAudit(page: Page, context?: string) {
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa'])
    .disableRules(['color-contrast']) // optional: adjust if contrast false positives occur
    .analyze();

  const violations: AccessibilityViolation[] = results.violations.map((v) => ({
    id: v.id,
    impact: v.impact,
    description: v.description,
    helpUrl: v.helpUrl,
    nodes: v.nodes.map((n) => ({ target: n.target as string[], html: n.html })),
  }));

  const seriousOrWorse = violations.filter((v) => v.impact === 'serious' || v.impact === 'critical');
  if (seriousOrWorse.length) {
    const summary = seriousOrWorse
      .map((v) => `${v.id} (${v.impact}): ${v.description}\n Targets: ${v.nodes
        .map((n) => n.target.join(', '))
        .join('; ')}`)
      .join('\n\n');
    throw new Error(`Accessibility violations${context ? ` on ${context}` : ''}:\n${summary}`);
  }

  return { violations };
}
