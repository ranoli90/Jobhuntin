// Content Enhancement for Job Pages - Prevents thin content penalties
export interface ContentEnhancement {
  title: string;
  description: string;
  sections: ContentSection[];
  faqs: FAQItem[];
  localInsights: LocalInsight[];
  uniqueValue: string;
}

export interface ContentSection {
  heading: string;
  content: string;
  wordCount: number;
  keywords: string[];
  entities: string[];
}

export interface FAQItem {
  question: string;
  answer: string;
}

export interface LocalInsight {
  category: string;
  insight: string;
  data?: string;
  source?: string;
}

export interface CityData {
  population?: string;
  industries?: string[];
  techHub?: boolean;
  startupScene?: boolean;
  remotePercentage?: number;
  averageSalary?: number;
  costOfLiving?: number;
  majorEmployers?: string[];
  jobMarketTrends?: string;
  country?: string;
}

export interface RoleData {
  avgSalary?: number;
  demandLevel?: string;
  remotePercentage?: number;
  skills?: string[];
  careerPath?: string[];
  certifications?: string[];
  growthRate?: string;
}

/**
 * Generates unique, valuable content for job pages to avoid thin content penalties
 */
export function generateEnhancedContent(
  role: string,
  city: string,
  roleData?: RoleData,
  cityData?: CityData,
): ContentEnhancement {
  const currentYear = new Date().getFullYear();
  const currentMonth = new Date().toLocaleString("default", { month: "long" });

  // Generate unique value proposition
  const uniqueValue = generateUniqueValue(role, city, roleData, cityData);

  // Generate content sections with 400-600 words total
  const sections = generateContentSections(role, city, roleData, cityData);

  // Generate FAQs for user intent
  const faqs = generateFAQs(role, city, roleData, cityData);

  // Generate local insights
  const localInsights = generateLocalInsights(city, cityData, role, roleData);

  // Generate SEO-optimized title and description
  const { title, description } = generateSEOTitleAndDescription(
    role,
    city,
    roleData,
    cityData,
  );

  return {
    title,
    description,
    sections,
    faqs,
    localInsights,
    uniqueValue,
  };
}

function generateUniqueValue(
  role: string,
  city: string,
  roleData?: RoleData,
  cityData?: CityData,
): string {
  const insights = [];
  const currentYear = new Date().getFullYear();

  // City-specific insights
  if (cityData) {
    if (cityData.techHub) {
      insights.push(
        `${city} is a major tech hub with ${cityData.remotePercentage || 35}% remote opportunities`,
      );
    }
    if (cityData.startupScene) {
      insights.push(
        `${city}'s startup ecosystem is thriving, with venture capital flowing into ${cityData.industries?.join(", ") || "tech"}`,
      );
    }
    if (cityData.costOfLiving && cityData.averageSalary) {
      const affordability =
        (cityData.averageSalary / cityData.costOfLiving) * 100;
      insights.push(
        `The salary-to-cost-of-living ratio in ${city} is ${affordability.toFixed(0)}%`,
      );
    }
  }

  // Role-specific insights
  if (roleData) {
    if (roleData.growthRate) {
      insights.push(
        `${role} roles are projected to grow ${roleData.growthRate} through ${currentYear}`,
      );
    }
    if (roleData.remotePercentage) {
      insights.push(
        `${roleData.remotePercentage}% of ${role} positions offer remote work flexibility`,
      );
    }
    if (roleData.certifications && roleData.certifications.length > 0) {
      insights.push(
        `Top certifications for ${role}s include ${roleData.certifications.slice(0, 3).join(", ")}`,
      );
    }
  }

  // Combined insight
  return insights.length > 0
    ? insights.join(". ")
    : `Discover ${role} opportunities in ${city} with our AI-powered job search platform`;
}

function generateContentSections(
  role: string,
  city: string,
  roleData?: RoleData,
  cityData?: CityData,
): ContentSection[] {
  const sections: ContentSection[] = [];

  // Section 1: Market Overview (150-200 words)
  sections.push({
    heading: `${city} ${role} Job Market Overview (${new Date().getFullYear()})`,
    content: generateMarketOverview(role, city, roleData, cityData),
    wordCount: 180,
    keywords: [
      `${role} jobs ${city}`,
      `${city} employment`,
      `${role} career ${city}`,
    ],
    entities: [role, city, "job market", "employment trends"],
  });

  // Section 2: Salary & Compensation (150-200 words)
  sections.push({
    heading: `${role} Salary in ${city}: Complete Breakdown`,
    content: generateSalaryContent(role, city, roleData, cityData),
    wordCount: 175,
    keywords: [
      `${role} salary ${city}`,
      `${role} pay ${city}`,
      `${role} compensation`,
    ],
    entities: [role, city, "salary", "compensation", "benefits"],
  });

  // Section 3: Top Employers (100-150 words)
  sections.push({
    heading: `Top Companies Hiring ${role}s in ${city}`,
    content: generateEmployersContent(city, role, cityData),
    wordCount: 125,
    keywords: [
      `${role} companies ${city}`,
      `employers ${city} ${role}`,
      `hiring ${role}`,
    ],
    entities: [city, role, "companies", "employers", "hiring"],
  });

  // Section 4: Career Path (100-150 words)
  sections.push({
    heading: `${role} Career Path in ${city}`,
    content: generateCareerPathContent(role, city, roleData),
    wordCount: 125,
    keywords: [
      `${role} career ${city}`,
      `${role} advancement`,
      `${role} growth`,
    ],
    entities: [role, city, "career path", "professional development"],
  });

  return sections;
}

function generateMarketOverview(
  role: string,
  city: string,
  roleData?: RoleData,
  cityData?: CityData,
): string {
  const currentYear = new Date().getFullYear();
  const demandLevel = roleData?.demandLevel || "growing";
  const remotePercentage = roleData?.remotePercentage || 35;
  const industries = cityData?.industries || [
    "Technology",
    "Healthcare",
    "Finance",
  ];

  return `The ${role} job market in ${city} is ${demandLevel} as of ${new Date().toLocaleString("default", { month: "long", year: "numeric" })}. 
  ${cityData?.techHub ? "As a major tech hub, " : ""}the city offers ${remotePercentage}% remote ${role} positions, 
  making it attractive for both local and remote job seekers. 
  Key industries hiring ${role}s include ${industries.slice(0, 3).join(", ")}. 
  The competitive landscape means skilled ${role}s can command premium salaries, especially those with specialized skills in emerging technologies. 
  Recent market analysis shows increased demand for ${role} positions with AI and automation skills, reflecting the evolving tech landscape in ${city}.`;
}

function generateSalaryContent(
  role: string,
  city: string,
  roleData?: RoleData,
  cityData?: CityData,
): string {
  const avgSalary = roleData?.avgSalary || 75_000;
  const cityAvgSalary = cityData?.averageSalary || 80_000;
  const isUS = cityData?.country === "USA";
  const currency = isUS ? "$" : "€";

  const formatSalary = (value: number) =>
    `${currency}${Math.round(value / 1000)}k`;

  return `${role} salaries in ${city} range from ${formatSalary(avgSalary * 0.7)} for entry-level positions to ${formatSalary(avgSalary * 1.5)} for senior roles. 
  The average ${role} salary in ${city} is ${formatSalary(cityAvgSalary)}, slightly above the national average. 
  ${cityData?.costOfLiving ? `With a cost of living index of ${cityData.costOfLiving}, the real purchasing power of salaries in ${city} is approximately ${Math.round((cityAvgSalary / cityData.costOfLiving) * 100)}%.` : ""} 
  Remote ${role} positions typically offer ${formatSalary(avgSalary * 1.1)} to ${formatSalary(avgSalary * 1.3)} due to reduced overhead costs. 
  Companies in ${city} are increasingly offering comprehensive benefits packages including health insurance, retirement plans, and professional development budgets to attract top ${role} talent.`;
}

function generateEmployersContent(
  city: string,
  role: string,
  cityData?: CityData,
): string {
  const employers = cityData?.majorEmployers || [
    "Fortune 500 companies",
    "Growing startups",
    "Healthcare systems",
    "Financial institutions",
  ];

  const industry = cityData?.industries?.[0] || "technology";

  return `Top employers hiring ${role}s in ${city} include ${employers.slice(0, 4).join(", ")}. 
  These companies are actively seeking ${role} talent to support their ${industry} operations. 
  Many offer competitive compensation packages, flexible work arrangements, and clear career progression paths. 
  The ${industry} sector in ${city} is particularly active, with companies investing heavily in ${role} expertise and digital transformation initiatives. 
  Job seekers with relevant ${role} skills and experience in ${industry} will find numerous opportunities across these organizations.`;
}

function generateCareerPathContent(
  role: string,
  city: string,
  roleData?: RoleData,
): string {
  const careerPath = roleData?.careerPath || [
    `Junior ${role}`,
    `${role} I`,
    `Senior ${role}`,
    `Lead ${role}`,
    `${role} Manager`,
  ];

  const growthRate = roleData?.growthRate || "moderate";
  const certifications = roleData?.certifications || [];

  return `The typical ${role} career path in ${city} progresses from ${careerPath[0]} to ${careerPath.at(-1)} over 5-10 years. 
  ${certifications.length > 0 ? `Key certifications like ${certifications.slice(0, 2).join(" or ")} can significantly accelerate career advancement.` : ""} 
  With ${growthRate} growth projected for ${role} positions, professionals who continuously update their skills and build strong portfolios can expect rapid advancement. 
  ${city}'s competitive business environment creates numerous opportunities for ${role}s to take on leadership roles and drive strategic initiatives. 
  Networking within ${city}'s professional community and staying current with industry trends are essential for long-term career success.`;
}

function generateFAQs(
  role: string,
  city: string,
  roleData?: RoleData,
  cityData?: CityData,
): FAQItem[] {
  return [
    {
      question: `What is the average ${role} salary in ${city}?`,
      answer: `The average ${role} salary in ${city} ranges from $${Math.round((roleData?.avgSalary || 75_000) / 1000)}k to $${Math.round(((roleData?.avgSalary || 75_000) * 1.5) / 1000)}k, with experienced professionals earning at the higher end of the range.`,
    },
    {
      question: `Is ${city} a good city for ${role} careers?`,
      answer: `${city} ${cityData?.techHub ? "is an excellent choice" : "offers solid opportunities"} for ${role} professionals. ${cityData?.startupScene ? "The thriving startup scene" : "The established business environment"} provides diverse opportunities for career growth and innovation.`,
    },
    {
      question: `What skills are most in demand for ${role} positions in ${city}?`,
      answer: `${roleData?.skills?.slice(0, 5).join(", ") || "Technical skills, communication, problem-solving"} are highly valued by ${city} employers. ${roleData?.remotePercentage ? "Remote work capabilities and" : ""} experience with modern tools and technologies are essential for competitive advantage.`,
    },
    {
      question: `How competitive is the ${role} job market in ${city}?`,
      answer: `The ${role} market in ${city} is ${roleData?.demandLevel || "moderately competitive"}. ${cityData?.techHub ? "As a major tech hub" : "With growing demand"} for skilled professionals, qualified ${role}s have strong negotiating power and multiple career options.`,
    },
    {
      question: `What are the best companies to work for as a ${role} in ${city}?`,
      answer: `Top employers include ${cityData?.majorEmployers?.slice(0, 3).join(", ") || "Leading companies in the area"}. These organizations offer competitive compensation, professional development, and stable work environments for ${role} professionals.`,
    },
  ];
}

function generateLocalInsights(
  city: string,
  cityData?: CityData,
  role?: string,
  roleData?: RoleData,
): LocalInsight[] {
  const insights: LocalInsight[] = [];

  // Market trends
  insights.push({
    category: "Market Trends",
    insight: `${city} ${role} market shows ${roleData?.demandLevel || "steady"} growth with ${roleData?.remotePercentage || 35}% remote positions available`,
    source: "Local market analysis",
  });

  // Industry focus
  if (cityData?.industries?.length) {
    insights.push({
      category: "Industry Focus",
      insight: `${city}'s ${cityData.industries[0]} sector leads in ${role} hiring, followed by ${cityData.industries[1] || "technology"}`,
      source: "Industry employment data",
    });
  }

  // Remote work
  insights.push({
    category: "Remote Work",
    insight: `${role} positions in ${city} offer ${roleData?.remotePercentage || 35}% remote work flexibility with hybrid options`,
    source: "Remote work statistics",
  });

  // Salary insights
  if (roleData?.avgSalary && cityData?.averageSalary) {
    insights.push({
      category: "Salary Insights",
      insight: `${role} salaries in ${city} average ${Math.round(roleData.avgSalary / 1000)}k, ${Math.round((roleData.avgSalary / cityData.averageSalary) * 100)}% above city average`,
      source: "Salary survey data",
    });
  }

  return insights;
}

function generateSEOTitleAndDescription(
  role: string,
  city: string,
  roleData?: RoleData,
  cityData?: CityData,
): { title: string; description: string } {
  const currentYear = new Date().getFullYear();
  const demandLevel = roleData?.demandLevel || "growing";

  const title = `${role} Jobs in ${city} (${currentYear}) | ${demandLevel} Opportunities`;

  const description = `Find ${role} jobs in ${city} with competitive salaries and growth opportunities. 
  ${cityData?.techHub ? "As a major tech hub," : ""} ${city} offers ${roleData?.remotePercentage || 35}% remote positions. 
  Average salary: $${Math.round((roleData?.avgSalary || 75_000) / 1000)}k. 
  Apply to top employers and advance your ${role} career in ${city} with our AI-powered job search platform.`;

  return { title, description };
}
