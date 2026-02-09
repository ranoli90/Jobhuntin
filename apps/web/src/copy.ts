// JobHuntin Brand Voice & Copy Constants
// Central source of truth for all user-facing copy

export const COPY = {
  // Brand basics
  brandName: "JobHuntin",
  tagline: "Apply to 100 jobs before breakfast",
  
  // Hero / Landing
  hero: {
    headline: "Apply to 100 jobs before breakfast",
    subheadline: "JobHuntin is your AI job-hunting teammate. We find perfect matches, fill out applications, and handle the boring stuff—so you can focus on nailing interviews.",
    ctaPrimary: "Start applying free",
    ctaSecondary: "See how it works",
    trustBadge: "No credit card required • 10 free applications • Cancel anytime",
  },
  
  // Actions / Buttons
  actions: {
    apply: "JobHuntin this job",
    skip: "Not for me",
    save: "Save for later",
    continue: "Let's go",
    back: "Back",
    submit: "Ship it",
    upload: "Upload",
    upgrade: "Unlock unlimited",
    invite: "Invite the team",
    export: "Export CSV",
    refresh: "Find more jobs",
  },
  
  // Empty states
  empty: {
    jobs: {
      title: "No jobs match your filters",
      description: "Try broadening your search or check back soon—we add new jobs every hour.",
      action: "Adjust filters",
    },
    applications: {
      title: "No applications yet",
      description: "Start swiping on jobs and we'll track everything here. Your first interview is closer than you think.",
      action: "Browse jobs",
    },
    holds: {
      title: "No HOLDs right now",
      description: "That's a good thing! It means applications are flowing smoothly. We'll ping you if employers ask questions.",
      action: "Check applications",
    },
    billing: {
      title: "Billing info unavailable",
      description: "Something went sideways, but your data is safe. Please try again.",
      action: "Retry",
    },
  },
  
  // Error messages (human, reassuring)
  errors: {
    generic: "Something went sideways, but your data is safe. Please try again.",
    network: "Looks like the internet hiccuped. Give it another shot?",
    upload: "Upload didn't work. Check your file size (max 5MB) and try again.",
    auth: "Session expired. Let's get you back in—sign in again.",
    api: "Our servers are a bit busy. Try again in a moment.",
  },
  
  // Success messages (celebratory, playful)
  success: {
    applied: "🚀 JobHuntin'd! Application sent.",
    saved: "✓ Saved to your list",
    uploaded: "✓ Resume uploaded and parsed",
    preferences: "✓ Preferences saved—we'll find better matches now",
    upgraded: "🎉 Welcome to Pro! Unlimited applications unlocked.",
    invite: "✓ Invite sent",
    hold: "✓ Response drafted—ready to send",
    firstApplication: {
      title: "You did it! 🎉",
      description: "Your first application is off to the races. This is just the beginning.",
    },
  },
  
  // Onboarding
  onboarding: {
    step1: {
      title: "Welcome to JobHuntin!",
      description: "We're going to get you set up in just 2 minutes.",
      checklist: [
        "Upload your resume (or paste your LinkedIn)",
        "Set your job preferences",
        "Start applying to perfect matches",
      ],
    },
    step2: {
      title: "Upload your resume",
      description: "We'll use this to find perfect matches",
    },
    step3: {
      title: "Job preferences",
      description: "Tell us what you're looking for",
    },
    step4: {
      title: "You're ready to job hunt!",
      description: "We've got your resume and preferences. Let's find you some perfect job matches.",
      nextSteps: [
        "We'll scan for jobs matching your profile",
        "You swipe right on jobs you like",
        "We apply for you with a personalized message",
        "You get interview requests directly",
      ],
    },
  },
  
  // Trust & Safety
  trust: {
    howItWorks: "How JobHuntin applies on your behalf",
    whatWeNeverDo: "What we never do",
    pillars: [
      { title: "We never spam employers", description: "Every application is thoughtful and tailored. We don't blast generic resumes." },
      { title: "Your data stays yours", description: "Encrypted storage, no selling to third parties, delete anytime with one click." },
      { title: "We never modify without approval", description: "Every resume tweak and cover letter is shown to you first. You always approve." },
      { title: "Your email, your identity", description: "All applications come from your email address. Employers never know we helped." },
      { title: "No Terms of Service violations", description: "We respect job site rules. We don't scrape illegally or use fake accounts." },
    ],
  },
  
  // Navigation labels
  nav: {
    dashboard: "Dashboard",
    jobs: "Jobs",
    applications: "Applications",
    holds: "HOLDs",
    team: "Team",
    billing: "Billing",
    logout: "Log out",
  },
  
  // Misc UI
  ui: {
    loading: "Loading...",
    justNow: "Just now",
    today: "Today",
    yesterday: "Yesterday",
    unlimited: "Unlimited",
    free: "Free",
    pro: "Pro",
    team: "Team",
  },
} as const;

// Type-safe helper for accessing copy
export type CopyKeys = keyof typeof COPY;
