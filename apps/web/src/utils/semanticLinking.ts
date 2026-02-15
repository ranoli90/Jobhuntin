/**
 * Semantic Internal Linking System
 * Creates intelligent internal linking based on entity relationships and topical clusters
 * Uses advanced SEO techniques for maximum authority distribution
 */

interface SemanticLink {
  url: string;
  anchorText: string;
  semanticRelationship: string;
  entityType: string;
  priority: 'high' | 'medium' | 'low';
  topicalRelevance: number;
}

interface EntityRelationship {
  source: string;
  target: string;
  relationship: string;
  strength: number;
}

/**
 * Generate semantic internal links for location + role pages
 * Creates entity-based linking that Google can understand
 */
export function generateSemanticLinksForLocationRole(
  role: string,
  location: string,
  roleData: any,
  locationData: any
): SemanticLink[] {
  const links: SemanticLink[] = [];

  // High-priority semantic relationships
  links.push({
    url: `/jobs/${role.toLowerCase().replace(/\s+/g, '-')}`,
    anchorText: `${role} jobs nationwide`,
    semanticRelationship: 'role-expansion',
    entityType: 'role',
    priority: 'high',
    topicalRelevance: 0.95
  });

  links.push({
    url: `/jobs/all/${location.toLowerCase().replace(/\s+/g, '-')}`,
    anchorText: `all tech jobs in ${location}`,
    semanticRelationship: 'location-expansion',
    entityType: 'location',
    priority: 'high',
    topicalRelevance: 0.95
  });

  // Category-based linking
  if (roleData?.category) {
    links.push({
      url: `/best/${roleData.category.toLowerCase().replace(/\s+/g, '-')}`,
      anchorText: `best ${roleData.category} tools`,
      semanticRelationship: 'category-relationship',
      entityType: 'category',
      priority: 'high',
      topicalRelevance: 0.90
    });
  }

  // Competitor comparison linking (only to existing competitor pages)
  // Note: We link to actual competitor pages from competitors.json
  links.push({
    url: `/vs/simplify`,
    anchorText: `Simplify vs JobHuntin comparison`,
    semanticRelationship: 'competitor-comparison',
    entityType: 'competitor',
    priority: 'medium',
    topicalRelevance: 0.85
  });

  links.push({
    url: `/vs/teal`,
    anchorText: `Teal vs JobHuntin comparison`,
    semanticRelationship: 'competitor-comparison',
    entityType: 'competitor',
    priority: 'medium',
    topicalRelevance: 0.85
  });

  // Related roles linking (semantic clustering)
  const relatedRoles = getRelatedRoles(role);
  relatedRoles.forEach(relatedRole => {
    links.push({
      url: `/jobs/${relatedRole.toLowerCase().replace(/\s+/g, '-')}/${location.toLowerCase().replace(/\s+/g, '-')}`,
      anchorText: `${relatedRole} jobs in ${location}`,
      semanticRelationship: 'role-similarity',
      entityType: 'related-role',
      priority: 'medium',
      topicalRelevance: 0.80
    });
  });

  // Location cluster linking
  const nearbyCities = getNearbyCities(location);
  nearbyCities.forEach(city => {
    links.push({
      url: `/jobs/${role.toLowerCase().replace(/\s+/g, '-')}/${city.toLowerCase().replace(/\s+/g, '-')}`,
      anchorText: `${role} jobs in ${city}`,
      semanticRelationship: 'geographic-proximity',
      entityType: 'nearby-location',
      priority: 'medium',
      topicalRelevance: 0.75
    });
  });

  // Category page linking (using actual categories from categories.json)
  links.push({
    url: `/best/ai-auto-apply-tools`,
    anchorText: `best AI auto-apply tools`,
    semanticRelationship: 'category-relationship',
    entityType: 'category',
    priority: 'high',
    topicalRelevance: 0.90
  });

  return links.sort((a, b) => b.topicalRelevance - a.topicalRelevance);
}

/**
 * Generate entity relationships for Google's Knowledge Graph
 */
export function generateEntityRelationships(
  role: string,
  location: string,
  roleData: any,
  locationData: any
): EntityRelationship[] {
  const relationships: EntityRelationship[] = [];

  // Primary entity relationships
  relationships.push({
    source: location,
    target: role,
    relationship: 'employs',
    strength: 0.95
  });

  relationships.push({
    source: role,
    target: location,
    relationship: 'located_in',
    strength: 0.95
  });

  // Industry relationships
  if (locationData?.industry) {
    relationships.push({
      source: location,
      target: locationData.industry,
      relationship: 'specializes_in',
      strength: 0.90
    });

    relationships.push({
      source: role,
      target: locationData.industry,
      relationship: 'works_in',
      strength: 0.85
    });
  }

  // Company relationships
  if (locationData?.majorEmployers) {
    locationData.majorEmployers.forEach((company: string) => {
      relationships.push({
        source: company,
        target: role,
        relationship: 'hires',
        strength: 0.80
      });

      relationships.push({
        source: location,
        target: company,
        relationship: 'hosts',
        strength: 0.75
      });
    });
  }

  // Skill relationships
  if (roleData?.skills) {
    roleData.skills.forEach((skill: string) => {
      relationships.push({
        source: role,
        target: skill,
        relationship: 'requires',
        strength: 0.85
      });
    });
  }

  return relationships;
}

/**
 * Get semantically related roles for topical clustering
 */
function getRelatedRoles(role: string): string[] {
  const roleClusters: Record<string, string[]> = {
    'software-engineer': ['backend-developer', 'frontend-developer', 'full-stack-developer', 'devops-engineer'],
    'data-scientist': ['data-analyst', 'machine-learning-engineer', 'data-engineer', 'business-analyst'],
    'product-manager': ['product-owner', 'program-manager', 'project-manager', 'business-analyst'],
    'ui-ux-designer': ['product-designer', 'visual-designer', 'interaction-designer', 'user-researcher'],
    'marketing-manager': ['digital-marketing-manager', 'content-marketing-manager', 'growth-manager', 'brand-manager'],
    'sales-representative': ['account-executive', 'business-development-representative', 'sales-engineer', 'customer-success-manager']
  };

  const normalizedRole = role.toLowerCase().replace(/\s+/g, '-');
  return roleClusters[normalizedRole] || ['senior-' + normalizedRole, 'lead-' + normalizedRole, 'principal-' + normalizedRole];
}

/**
 * Get geographically nearby cities for local clustering
 */
function getNearbyCities(location: string): string[] {
  const cityClusters: Record<string, string[]> = {
    'san-francisco': ['oakland', 'berkeley', 'san-jose', 'palo-alto', 'mountain-view'],
    'new-york': ['brooklyn', 'queens', 'manhattan', 'bronx', 'staten-island'],
    'austin': ['round-rock', 'cedar-park', 'georgetown', 'leander', 'pflugerville'],
    'seattle': ['bellevue', 'redmond', 'kirkland', 'tacoma', 'everett'],
    'los-angeles': ['santa-monica', 'beverly-hills', 'culver-city', 'burbank', 'glendale'],
    'chicago': ['evanston', 'oak-park', 'cicero', 'berwyn', 'elmhurst'],
    'boston': ['cambridge', 'somerville', 'brookline', 'newton', 'quincy'],
    'denver': ['boulder', 'aurora', 'lakewood', 'thornton', 'westminster']
  };

  const normalizedLocation = location.toLowerCase().replace(/\s+/g, '-');
  return cityClusters[normalizedLocation] || [];
}

/**
 * Calculate semantic similarity between two entities
 */
export function calculateSemanticSimilarity(entity1: string, entity2: string): number {
  // Simple implementation - in production, use word embeddings or NLP libraries
  const commonWords = entity1.toLowerCase().split(/\s+/)
    .filter(word => entity2.toLowerCase().split(/\s+/).includes(word));

  const totalWords = new Set([...entity1.toLowerCase().split(/\s+/), ...entity2.toLowerCase().split(/\s+/)]).size;
  return commonWords.length / totalWords;
}

/**
 * Generate topical cluster suggestions for content strategy
 */
export function generateTopicalClusters(role: string, location: string): string[][] {
  return [
    // Primary cluster: Role-specific content
    [`${role} jobs in ${location}`, `${role} salary ${location}`, `${role} skills ${location}`, `${role} companies ${location}`],

    // Secondary cluster: Location-specific content
    [`${location} tech jobs`, `${location} startups`, `${location} cost of living`, `${location} tech scene`],

    // Tertiary cluster: Career development
    [`${role} career path`, `${role} certifications`, `${role} interview questions`, `${role} resume tips`],

    // Quaternary cluster: Company-specific content
    [`${location} tech companies`, `best companies in ${location}`, `${location} startup jobs`, `${location} remote jobs`]
  ];
}