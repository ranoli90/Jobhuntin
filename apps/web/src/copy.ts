// JobHuntin Brand Voice & Copy Constants
// Central source of truth for all user-facing copy

export const COPY = {
  // Brand basics
  brandName: "JobHuntin",
  tagline: "Other people applied to your dream job today. Did you?",
  
  // Hero / Landing
  hero: {
    headline: "Other people applied to your dream job today. Did you?",
    subheadline: "JobHuntin's AI agent fires off 100 tailored applications while you sleep. Wake up to interview requests, not rejection silence.",
    ctaPrimary: "Start free — before they hire someone else",
    ctaSecondary: "Watch it work",
    trustBadge: "No credit card • 10 free apps • 2-minute setup",
  },
  
  // Actions / Buttons
  actions: {
    apply: "JobHuntin this job",
    skip: "Pass",
    save: "Save for later",
    continue: "Let's go",
    back: "Back",
    submit: "Ship it",
    upload: "Upload",
    upgrade: "Go unlimited now",
    invite: "Add your team",
    export: "Export CSV",
    refresh: "Find more jobs",
  },
  
  // Empty states
  empty: {
    jobs: {
      title: "Zero matches? Your competitors aren't waiting.",
      description: "Widen your filters. New roles drop every hour and the best ones fill fast.",
      action: "Adjust filters",
    },
    applications: {
      title: "Every hour without applications is an interview you'll never get.",
      description: "People who start today land interviews 3x faster. Let's fix that.",
      action: "Start applying now",
    },
    holds: {
      title: "All clear — you're on fire!",
      description: "No pending questions means your applications are sailing through. Keep the momentum.",
      action: "View applications",
    },
    billing: {
      title: "Billing info unavailable",
      description: "Your data is safe. Hit retry and we'll sort it out.",
      action: "Retry",
    },
  },
  
  // Error messages (human, reassuring)
  errors: {
    generic: "Something went sideways, but your data is safe. Try again.",
    network: "Internet hiccuped. Give it another shot?",
    upload: "Upload failed. Check file size (max 5MB) and retry.",
    auth: "Session expired — sign in to keep your streak going.",
    api: "Servers are catching their breath. Try again in a moment.",
  },
  
  // Success messages (celebratory, playful)
  success: {
    applied: "🚀 Sent! One step closer to your offer letter.",
    saved: "✓ Saved — don't wait too long, it might fill.",
    uploaded: "✓ Resume locked and loaded.",
    preferences: "✓ Preferences saved — better matches incoming.",
    upgraded: "🎉 Pro unlocked! Unlimited applications, zero limits.",
    invite: "✓ Invite sent — more teammates, more firepower.",
    hold: "✓ Response drafted — send it before they move on.",
    firstApplication: {
      title: "First one's away! 🎉",
      description: "Most users land their first interview within 48 hours. You're in the game now.",
    },
  },
  
  // Onboarding
  onboarding: {
    step1: {
      title: "Let's get you hired.",
      description: "Two minutes of setup. Hundreds of applications on autopilot.",
      checklist: [
        "Drop your resume (or paste your LinkedIn)",
        "Tell us what you want",
        "We start applying — you start interviewing",
      ],
    },
    step2: {
      title: "Drop your resume",
      description: "This is what gets you matched. The better the resume, the better the jobs.",
    },
    step3: {
      title: "What's the dream role?",
      description: "Set it and forget it — we'll do the hunting.",
    },
    step4: {
      title: "You're live.",
      description: "Your AI agent is armed and ready. The first applications go out within minutes.",
      nextSteps: [
        "Scanning thousands of listings right now",
        "You approve jobs you love",
        "We tailor and send every application",
        "Interview requests land in your inbox",
      ],
    },
  },
  
  // Trust & Safety
  trust: {
    howItWorks: "How JobHuntin applies on your behalf",
    whatWeNeverDo: "What we never do",
    pillars: [
      { title: "We never spam employers", description: "Every application is tailored. Generic blasts get you blacklisted — we don't do that." },
      { title: "Your data stays yours", description: "Encrypted, never sold, delete anytime. Period." },
      { title: "You approve everything", description: "Every resume tweak and cover letter gets your sign-off first." },
      { title: "Your email, your identity", description: "Employers see you, not us. Completely invisible." },
      { title: "100% ToS compliant", description: "We play by the rules so your accounts stay safe." },
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
