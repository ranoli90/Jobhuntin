type Dict = Record<string, Record<string, string>>;

const dictionaries: Dict = {
  en: {
    "dashboard.activeRadar": "Active Radar",
    "dashboard.swipeRight": "Swipe right to let AI apply for you.",
    "dashboard.resetFilters": "Reset filters and rescan",
    "dashboard.loadMore": "Load more matches",
    "dashboard.loadingMore": "Loading more",
    "dashboard.noMatches":
      "You've reviewed all matches for your current filters. Try broadening your location, lowering salary floors, or clearing keywords to discover more leads.",
    "dashboard.reviewSwipes": "Review Swipes",
    "dashboard.filterPlaceholder": "Filter location...",
    "dashboard.matchAlert": "Match Alert! High-fit role detected.",
    "dashboard.sweepComplete": "Radar Sweep Complete",
    "dashboard.aiAgentMonitoring": "Your AI agent is actively monitoring",
    "dashboard.aiAgentMonitoringNewListings": "new job listings",
    "dashboard.aiAgentMonitoringSource":
      "across LinkedIn and Wellfound. New matches will appear in your dashboard shortly.",
    "dashboard.jobsRemaining": "jobs remaining",
    "dashboard.showingApplications": "Showing {count} of {total} applications",
    "dashboard.firstStepsTitle": "Your first 3 steps",
    "dashboard.firstSteps1":
      "Swipe right on jobs you like — our AI will apply for you",
    "dashboard.firstSteps2": "Check Applications to track status",
    "dashboard.firstSteps3":
      "Answer any HOLD questions to keep applications moving",
    "dashboard.dismiss": "Dismiss",
    "dashboard.dismissFirstSteps": "Dismiss first steps",

    "applications.emptyTitle": "No applications yet",
    "applications.emptyDescription":
      "Your agent hasn't found any opportunities yet. Start swiping on jobs to get matches.",
    "applications.noResults": "No Results",
    "applications.noActiveApplications": "No Active Applications",
    "applications.searchNoResults":
      "No applications found matching your search.",
    "applications.searchNoResultsDesktop":
      "We couldn't find any applications matching your search.",
    "applications.errorLoading": "Unable to load applications.",
    "applications.emptyDesktopDescription":
      "No applications yet. Start searching to find job opportunities.",
    "applications.startSearching": "Start Searching",
    "applications.loadMore": "Load more",

    // Onboarding - Welcome Step
    "onboarding.welcomeTitle": "Find Your Dream Job.",
    "onboarding.welcomeSubtitle":
      "We'll help you apply to jobs automatically. Setup takes about 2–3 minutes.",
    "onboarding.startSetup": "Start setup",
    "onboarding.feature1Title": "Upload Resume",
    "onboarding.feature1Desc": "We'll analyze your skills and experience",
    "onboarding.feature2Title": "Set Preferences",
    "onboarding.feature2Desc": "Tell us where and what you want to work",
    "onboarding.feature3Title": "Auto-Apply",
    "onboarding.feature3Desc": "We'll apply to jobs for you automatically",

    // Onboarding - Resume Step
    "onboarding.resumeTitle": "Upload your resume",
    "onboarding.resumeSubtitle": "We'll use this to find perfect matches",
    "onboarding.uploadResume": "Upload Resume",
    "onboarding.dragAndDrop": "Drag and drop your resume here",
    "onboarding.fileTypes": "PDF, DOCX up to 15MB",
    "onboarding.linkedinPlaceholder": "LinkedIn Profile (optional)",
    "onboarding.linkedinError": "Please enter a valid LinkedIn URL",
    "onboarding.skipResumeTitle": "Skip resume?",
    "onboarding.skipResumeDesc":
      "Resume improves match quality by ~40%. You can add it later in Settings.",
    "onboarding.skipForNow": "Skip for now",
    "onboarding.goBack": "Go back",
    "onboarding.parsingPreview": "Here's what we found:",
    "onboarding.looksGoodContinue": "Looks good, continue",
    "onboarding.reupload": "Re-upload",
    "onboarding.parsingErrorHint":
      "You can try a different file, or skip and add your details manually in the next steps.",

    // Onboarding - Skill Review Step
    "onboarding.skillsTitle": "Review your skills",
    "onboarding.skillsSubtitle": "Verify the skills we detected",
    "onboarding.noSkills": "No skills detected from your resume",
    "onboarding.addSkillPlaceholder": "Add a skill...",
    "onboarding.saveSkill": "Save",
    "onboarding.cancel": "Cancel",
    "onboarding.yearsExperience": "years",
    "onboarding.confidence": "confidence",
    "onboarding.skillsCount": "{count} skills",
    "onboarding.maxSkillsReached": "Maximum reached",
    "onboarding.maxSkillsDesc":
      "You can add up to 100 skills. Remove some to add more.",
    "onboarding.contextLengthHint": "Max 200 characters",
    "onboarding.careerGoalsRequired":
      "Please select experience level and search urgency.",
    "onboarding.expLevelEntry": "Entry Level",
    "onboarding.expLevelEntrySub": "0–1 years",
    "onboarding.expLevelJunior": "Junior",
    "onboarding.expLevelJuniorSub": "1–3 years",
    "onboarding.expLevelMid": "Mid-Level",
    "onboarding.expLevelMidSub": "3–5 years",
    "onboarding.expLevelSenior": "Senior",
    "onboarding.expLevelSeniorSub": "5–10 years",
    "onboarding.expLevelStaff": "Staff+",
    "onboarding.expLevelStaffSub": "10+ years",
    "onboarding.urgencyActive": "Actively Looking",
    "onboarding.urgencyActiveDesc": "Interviewing and ready to move",
    "onboarding.urgencyOpen": "Open to Offers",
    "onboarding.urgencyOpenDesc": "Happy but curious about opportunities",
    "onboarding.urgencyExploring": "Just Exploring",
    "onboarding.urgencyExploringDesc": "No rush, seeing what's out there",
    "onboarding.goalSeniorIc": "Senior IC Role",
    "onboarding.goalManagement": "Management",
    "onboarding.goalCareerChange": "Career Change",
    "onboarding.goalHigherComp": "Higher Comp",
    "onboarding.goalWorkLife": "Work-Life Balance",
    "onboarding.goalStartup": "Startup Experience",
    "onboarding.reasonGrowth": "Career Growth",
    "onboarding.reasonCompensation": "Compensation",
    "onboarding.reasonCulture": "Company Culture",
    "onboarding.reasonLayoff": "Layoff / Restructuring",
    "onboarding.reasonRelocation": "Relocation",
    "onboarding.reasonContract": "Contract Ending",
    "onboarding.reasonNotEmployed": "Not Currently Employed",

    // Onboarding - Contact Step
    "onboarding.contactTitle": "Confirm your details",
    "onboarding.contactSubtitle": "Verify the info we extracted",
    "onboarding.firstName": "First name",
    "onboarding.lastName": "Last name",
    "onboarding.email": "Email",
    "onboarding.phone": "Phone",
    "onboarding.required": "Required",
    "onboarding.invalidFormat": "Invalid format",
    "onboarding.didYouMean": "Did you mean",

    // Onboarding - Preferences Step
    "onboarding.preferencesTitle": "Job preferences",
    "onboarding.preferencesSubtitle": "Tell us what you're looking for",
    "onboarding.location": "Location",
    "onboarding.locationPlaceholder": "e.g., Remote, San Francisco",
    "onboarding.roleType": "Role type",
    "onboarding.rolePlaceholder": "e.g., Product Manager",
    "onboarding.minSalary": "Min salary (optional)",
    "onboarding.maxSalary": "Max salary (optional)",
    "onboarding.salaryHint": "Annual salary in USD",
    "onboarding.remoteOnly": "Remote only",
    "onboarding.onsiteOnly": "Onsite only",
    "onboarding.workAuthorized": "Work authorized",
    "onboarding.workAuthorizedDesc":
      "I am authorized to work in my target location",
    "onboarding.visaSponsorship": "Need visa sponsorship",
    "onboarding.visaSponsorshipDesc":
      "Only show roles offering visa sponsorship",
    "onboarding.excludedCompanies": "Excluded companies",
    "onboarding.excludedKeywords": "Excluded keywords",
    "onboarding.useAISuggestion": "Use AI suggestion",
    "onboarding.salaryErrorMax": "Max must be ≥ min",
    "onboarding.salaryErrorCap": "Cannot exceed $10M",

    // Onboarding - Work Style Step
    "onboarding.workStyleTitle": "Work style",
    "onboarding.workStyleSubtitle": "Help us find your ideal environment",
    "onboarding.workStyleQuestion1":
      "Your team is blocked by a dependency. You:",
    "onboarding.workStyleQ1Option1": "Build a workaround and move forward",
    "onboarding.workStyleQ1Option2": "Escalate to get unblocked",
    "onboarding.workStyleQ1Option3": "Document the blocker and wait",
    "onboarding.workStyleQ1Option4": "Pick up other work while waiting",
    "onboarding.workStyleQuestion2": "Best way to learn a new technology:",
    "onboarding.workStyleQ2Option1": "Read docs thoroughly first",
    "onboarding.workStyleQ2Option2": "Build something small immediately",
    "onboarding.workStyleQ2Option3": "Pair with someone experienced",
    "onboarding.workStyleQ2Option4": "Take a structured course",
    "onboarding.workStyleQuestion3": "Which environment do you thrive in?",
    "onboarding.workStyleQ3Option1": "Early-stage startup (chaos, ownership)",
    "onboarding.workStyleQ3Option2": "Growth-stage company (scaling, process)",
    "onboarding.workStyleQ3Option3": "Enterprise (stability, specialization)",
    "onboarding.workStyleQ3Option4": "No strong preference",
    "onboarding.workStyleQuestion4": "Preferred way to collaborate:",
    "onboarding.workStyleQ4Option1": "Async (Slack, docs, PRs)",
    "onboarding.workStyleQ4Option2": "Real-time (meetings, pairing)",
    "onboarding.workStyleQ4Option3": "Mixed depending on urgency",
    "onboarding.workStyleQ4Option4": "Whatever the team prefers",
    "onboarding.workStyleQuestion5": "Ideal work pace:",
    "onboarding.workStyleQ5Option1": "Fast (ship fast, iterate)",
    "onboarding.workStyleQ5Option2": "Steady (predictable sprints)",
    "onboarding.workStyleQ5Option3": "Methodical (thorough before shipping)",
    "onboarding.workStyleQ5Option4": "Varies by project",
    "onboarding.workStyleQuestion6": "How do you prefer to own work?",
    "onboarding.workStyleQ6Option1": "Solo (end-to-end ownership)",
    "onboarding.workStyleQ6Option2": "Team (collaborative ownership)",
    "onboarding.workStyleQ6Option3": "Lead (guide others, delegate)",
    "onboarding.workStyleQ6Option4": "Mix depending on scope",
    "onboarding.workStyleQuestion7": "In 3 years, what's your ideal role?",
    "onboarding.workStyleQ7Option1": "Individual contributor (deep expertise)",
    "onboarding.workStyleQ7Option2": "Tech lead (team influence)",
    "onboarding.workStyleQ7Option3": "Engineering manager (people leadership)",
    "onboarding.workStyleQ7Option4": "Founder/CTO (company building)",
    "onboarding.workStyleQ7Option5": "Open to multiple paths",
    "onboarding.questionCounter": "Question {current} of {total}",
    "onboarding.saveWorkStyle": "Save Work Style",
    "onboarding.skip": "Skip",
    "onboarding.prev": "Prev",

    // Onboarding - Ready Step
    "onboarding.readyTitle": "You're ready!",
    "onboarding.readySubtitle": "Time to start job hunting",
    "onboarding.systemOnline": "System Online",
    "onboarding.calibrationSuccess":
      "Calibration successful. Your digital twin is initialized.",
    "onboarding.operationalDirectives": "Operational Directives",
    "onboarding.confirmedIdentity": "Confirmed Identity",
    "onboarding.aoiGeolocation": "AOI Geolocation",
    "onboarding.targetClassification": "Target Classification",
    "onboarding.matchStrength": "Match Strength",
    "onboarding.dataPoints": "Data Points",
    "onboarding.launchCommandCenter": "LAUNCH COMMAND CENTER",
    "onboarding.fullSystemAuthority": "Full system authority granted",
    "onboarding.shareArchetype": "SHARE YOUR ARCHETYPE",
    "onboarding.referFriend": "REFER A FRIEND",
    "onboarding.alreadyComplete": "Already set up",
    "onboarding.redirectingToDashboard": "Redirecting to your dashboard...",
    "onboarding.welcomeBack": "Welcome back!",
    "onboarding.pickingUpAt": "Picking up at {step}.",
    "onboarding.copiedClipboard": "Copied to clipboard!",
    "onboarding.shareOnSocial": "Share it on social media",
    "onboarding.linkCopied": "Link copied!",
    "onboarding.shareWithFriends": "Share with friends",
    "onboarding.copyFailed": "Couldn't copy",
    "onboarding.browserBlocked": "Your browser blocked clipboard access",
    "onboarding.profileStrength": "Profile Strength",
    "onboarding.startJobHunting": "Start Job Hunting",
    "onboarding.setupComplete": "Setup complete!",
    "onboarding.resumeAddedBadge": "Resume Added",
    "onboarding.locationSetBadge": "Location Set",
    "onboarding.jobTitleSetBadge": "Job Title Set",

    // Onboarding - Skills Step
    "onboarding.aboutConfidence": "About confidence scores",
    "onboarding.addFirstSkill": "Add your first skill",
    "onboarding.addMissingSkill": "Add a missing skill",
    "onboarding.addSkill": "Add skill",
    "onboarding.addSkillButton": "Add",
    "onboarding.aiExtracted": "AI-extracted",
    "onboarding.aiSuggestions": "AI suggestions",
    "onboarding.confidenceHelp":
      "Confidence reflects how relevant this skill is to your target roles",
    "onboarding.contextPlaceholder": "e.g., Used daily at previous role",
    "onboarding.deleteSkill": "Remove skill",
    "onboarding.detectedSkills": "Detected skills",
    "onboarding.editSkill": "Edit skill",
    "onboarding.highConfidence": "HIGH",
    "onboarding.highConfidenceLabel": "High confidence",
    "onboarding.lowConfidence": "LOW",
    "onboarding.lowConfidenceLabel": "Low confidence",
    "onboarding.mediumConfidence": "MEDIUM",
    "onboarding.mediumConfidenceLabel": "Medium confidence",
    "onboarding.noSkillsDesc": "Upload a resume or add skills manually",
    "onboarding.noSkillsHelp": "You can add skills later from your profile",
    "onboarding.noSkillsTitle": "No skills detected",
    "onboarding.noSkillsWarning":
      "Adding skills improves job matching accuracy",
    "onboarding.reviewRecommended": "Review recommended",
    "onboarding.saveSkills": "Save skills",
    "onboarding.skillExistsDesc": "This skill is already in your list",
    "onboarding.skillExistsTitle": "Skill exists",
    "onboarding.skillNamePlaceholder":
      "e.g., React, Python, Project Management",
    "onboarding.skillsDetected": "skills detected",
    "onboarding.skipSkills": "Skip for now",
    "onboarding.verified": "Verified",
    "onboarding.experience": "Experience",
    "onboarding.projects": "projects",
    "onboarding.years": "years",
    "onboarding.yearsPlaceholder": "Years of experience",
    "onboarding.found": "found",
    "onboarding.more": "more",
    "onboarding.question": "Question",

    // Onboarding - Contact Step
    "onboarding.emailPlaceholder": "your@email.com",
    "onboarding.emailPrivacy":
      "We'll never share your email with employers without permission",
    "onboarding.firstNamePlaceholder": "First name",
    "onboarding.lastNamePlaceholder": "Last name",
    "onboarding.phonePlaceholder": "+1 (555) 000-0000",
    "onboarding.phoneHint": "Optional — for recruiter calls",
    "onboarding.phoneInvalid": "Please enter a valid phone number",
    "onboarding.confirmIdentity": "Confirm your identity",
    "onboarding.verifyDetails": "Verify the info we extracted",
    "onboarding.formErrors": "Please fix the errors below",
    "onboarding.errorsPlural": "errors",
    "onboarding.errorsSingular": "error",

    // Onboarding - Preferences Step
    "onboarding.excludedCompaniesHint": "Companies you don't want to apply to",
    "onboarding.excludedCompaniesPlaceholder": "e.g., Company A, Company B",
    "onboarding.excludedKeywordsHint": "Job titles or keywords to exclude",
    "onboarding.excludedKeywordsPlaceholder": "e.g., intern, junior",
    "onboarding.workArrangement": "Work arrangement",
    "onboarding.workAuthorization": "Work authorization",
    "onboarding.suggestedLocation": "Suggested location",
    "onboarding.suggestedRole": "Suggested role",
    "onboarding.savePreferences": "Save preferences",
    "onboarding.salaryExceeds": "Salary exceeds maximum",
    "onboarding.salaryGreaterThanZero": "Must be greater than zero",
    "onboarding.minSalaryRequired": "Minimum salary required",
    "onboarding.maxSalaryRequired": "Maximum salary required",
    "onboarding.minGreaterThanMax": "Min must be less than max",
    "onboarding.validNumber": "Must be a valid number",

    // Onboarding - Career Goals Step
    "onboarding.careerGoalsTitle": "Career Goals",
    "onboarding.careerGoalsSubtitle": "Help us understand where you're headed",
    "onboarding.experienceLevel": "Experience Level",
    "onboarding.searchUrgency": "How urgently are you looking?",
    "onboarding.primaryGoal": "Primary career goal",
    "onboarding.whyLeaving": "Why are you looking?",
    "onboarding.saveContinue": "Save & Continue",

    // Onboarding - Ready/Launch Step
    "onboarding.launchTitle": "Launch",
    "onboarding.launchReady": "Ready.",
    "onboarding.launchSubtitle":
      "Your AI job hunter is armed and ready to find your perfect match",
    "onboarding.startMyHunt": "Start My Hunt",
    "onboarding.scanningJobs":
      "Scanning 10,000+ jobs for your perfect match\u2026",
    "onboarding.profileComplete": "Profile",
    "onboarding.complete": "Complete",
    "onboarding.journeySoFar": "Your Journey So Far",
    "onboarding.yourDetails": "Your Details",
    "onboarding.yourLocation": "Your Location",
    "onboarding.targetRole": "Target Role",
    "onboarding.strategyStrength": "Strategy Strength",
    "onboarding.profilePoints": "Profile Points",
    "onboarding.globalPriority": "Global Priority",
    "onboarding.seniorImpactRole": "Senior Impact Role",
    "onboarding.techProfessional": "tech professional",
    "onboarding.shareArchetypeText":
      "I just set up my AI job hunter on JobHuntin as a {role}. Check it out! #JobHuntin",
    "onboarding.referFriendText":
      "Join me on JobHuntin and let AI apply for you! https://jobhuntin.com",

    // Onboarding - Resume Step
    "onboarding.clickToUpload": "Click to upload",
    "onboarding.skipUpload": "Skip for now",
    "onboarding.parsingSuccess": "Resume parsed successfully",
    "onboarding.professionalTitle": "Professional title",

    // Onboarding - Work Style
    "onboarding.yourWorkStyle": "Your Work Style",

    // Onboarding - Misc
    "onboarding.allSet": "You're all set! Let's job hunt!",
    "onboarding.growthEndpointHint":
      "One optional step didn't complete. You're ready to job hunt!",
    "onboarding.almostThere": "Almost there!",
    "onboarding.buildingProfile": "Building your profile",
    "onboarding.somethingWrong": "We couldn't complete that. Please try again.",
    "onboarding.settingUpProfile": "Setting up your profile",
    "onboarding.setup": "Setup",
    "onboarding.setupTime": "2-3 min setup",
    "onboarding.clearProgress": "Clear progress and start over",
    "onboarding.confirmRestart": "Are you sure? This will clear your progress.",
    "onboarding.confirmRestartTitle": "Restart onboarding?",
    "onboarding.restartOnboarding": "Restart onboarding and clear progress",
    "onboarding.locationBadge": "Location",
    "onboarding.roleBadge": "Role",
    "onboarding.skillsBadge": "Skills",
    "onboarding.resumeBadge": "Resume",

    // Onboarding - Common
    "onboarding.continue": "Continue",
    "onboarding.back": "Back",
    "onboarding.step": "Step",
    "onboarding.of": "of",
    "onboarding.restart": "Restart",
    "onboarding.keyboardHint": "Ctrl+Enter to continue",
    "onboarding.pickingUp": "Picking up at",

    "holds.responseRequired": "RESPONSE REQUIRED",

    "app.loading": "Loading...",
    "app.error": "Something went wrong. Please try again.",
    "app.retry": "Try Again",
    "resumeRetry.offline":
      "You're offline. The resume will be automatically uploaded when you reconnect.",
    "resumeRetry.maxReached":
      "Maximum retry attempts reached. Please try uploading again or contact support.",
    "resumeRetry.retryingIn": "Retrying in {minutes} min...",
    "resumeRetry.ready": "Ready to retry.",
    "resumeRetry.offlineTitle": "Offline - Resume Saved",
    "resumeRetry.failedTitle": "Upload Failed",
    "resumeRetry.pendingTitle": "Resume Upload Pending",
    "resumeRetry.retrying": "Retrying...",
    "resumeRetry.retryNow": "Retry Now",
    "resumeRetry.clear": "Clear",
    "resumeRetry.attemptOf": "Attempt {current} of {max}",
    "resumeRetry.reuploadHint": "Re-upload your resume to try again.",
    "app.save": "Save",
    "app.cancel": "Cancel",
    "app.delete": "Delete",
    "app.confirm": "Confirm",
    "nav.dashboard": "Dashboard",
    "nav.jobs": "Jobs",
    "nav.applications": "Applications",
    "nav.settings": "Settings",
    "nav.billing": "Billing",
    "nav.team": "Team",
    "status.applied": "Applied",
    "status.needsInput": "Needs Input",
    "status.failed": "Failed",
    "status.queued": "Queued",
    "status.processing": "Processing",

    "jobAlerts.title": "Job Alerts",
    "jobAlerts.description":
      "Manage your job search alerts and get notified when matching jobs are posted",
    "jobAlerts.createAlert": "Create Alert",
    "jobAlerts.createFirstAlert": "Create Your First Alert",
    "jobAlerts.editAlert": "Edit Alert",
    "jobAlerts.updateAlert": "Update Alert",
    "jobAlerts.alertName": "Alert Name",
    "jobAlerts.alertNamePlaceholder": "e.g., Software Engineer Jobs",
    "jobAlerts.keywords": "Keywords",
    "jobAlerts.keywordPlaceholder": "e.g., React, TypeScript",
    "jobAlerts.locations": "Locations",
    "jobAlerts.locationPlaceholder": "e.g., San Francisco, CA",
    "jobAlerts.minSalary": "Minimum Salary",
    "jobAlerts.maxSalary": "Maximum Salary",
    "jobAlerts.salaryPlaceholder": "50000",
    "jobAlerts.salaryRange": "Salary",
    "jobAlerts.frequency": "Alert Frequency",
    "jobAlerts.daily": "Daily",
    "jobAlerts.weekly": "Weekly",
    "jobAlerts.monthly": "Monthly",
    "jobAlerts.remoteOnly": "Remote jobs only",
    "jobAlerts.searchPlaceholder": "Search alerts...",
    "jobAlerts.noAlerts": "No job alerts yet",
    "jobAlerts.noAlertsDescription":
      "Create your first job alert to get notified when matching jobs are posted",
    "jobAlerts.noSearchResults": "No alerts match your search",
    "jobAlerts.active": "Active",
    "jobAlerts.inactive": "Inactive",
    "jobAlerts.toggle": "Toggle",
    "jobAlerts.lastSent": "Last sent",
    "jobAlerts.confirmDelete": "Are you sure you want to delete this alert?",
    "jobAlerts.errorLoading": "Could not load job alerts",

    "cookies.description":
      'We use cookies to analyze traffic and optimize your experience. By clicking "Accept all", you consent to our use of analytics and marketing cookies. "Reject all" uses only essential system cookies. See our',
    "cookies.privacyPolicy": "Privacy Policy",
    "cookies.forDetails": "for details.",
    "cookies.rejectAll": "Reject all",
    "cookies.managePreferences": "Manage preferences",
    "cookies.acceptAnalytics": "Accept analytics",
    "cookies.acceptAll": "Accept all",
    "cookies.title": "Cookie consent",
    "cookies.essential": "Essential",
    "cookies.essentialDescription":
      "Required for the site to function (auth, security, preferences). Cannot be disabled.",
    "cookies.analytics": "Analytics",
    "cookies.analyticsDescription":
      "Helps us understand how visitors use the site (e.g. page views, flows). No personal data is shared.",
    "cookies.marketing": "Marketing",
    "cookies.marketingDescription":
      "Used for advertising and remarketing. May share data with partners.",
    "cookies.cancel": "Cancel",
    "cookies.savePreferences": "Save preferences",

    "login.checkInbox": "Check your email",
    "login.sentTo": "We sent a magic link to",
    "login.checkSpam": "Didn't receive it? Check your spam folder.",
    "login.step1": "Open your inbox (check spam too)",
    "login.step2": "Find the email from JobHuntin",
    "login.step3": "Click the magic link to sign in",
    "login.resendLink": "Resend link",
    "login.resendIn": "Resend in {seconds}s",
    "login.sending": "Sending...",
    "login.useDifferentEmail": "Use a different email",
    "login.welcomeBack": "Let's get you hired",
    "login.signInTitle": "Sign in to JobHuntin",
    "login.magicLinkHint": "We'll send you a magic link. No password needed.",
    "login.email": "Email address",
    "login.emailPlaceholder": "you@example.com",
    "login.continue": "Continue",
    "login.sessionExpired": "Session expired",
    "login.signInAgain": "Please sign in again.",
    "login.secure": "Secure • Encrypted • No passwords stored",
    "login.sidebarTitleLine1": "Your AI agent",
    "login.sidebarTitleLine2": "is ready to hunt",
    "login.sidebarSubtitle":
      "Sign in to access your dashboard, track applications, and land more interviews.",
    "login.feature1": "100+ tailored applications daily",
    "login.feature2": "Matches from 50+ job boards",
    "login.feature3": "One-click apply everywhere",

    "404.title": "404",
    "404.heading": "This page doesn't exist.",
    "404.description":
      "The page you're looking for couldn't be found. Try searching for jobs or head back to the homepage.",
    "404.startFree": "Start free — 10 applications on us",
    "404.backHome": "Back to home",
    "404.popularSearches": "Popular job searches",
    "404.findNextRole": "Find your next role with AI",
    "404.applyWithAI": "Apply with AI",

    "settings.title": "Settings",
    "settings.profilePreferences": "Profile & preferences",
    "settings.profileDetails": "Profile details",
    "settings.addYourName": "Add your name",
    "settings.recruiterHint": "Make it easier for recruiters to recognize you.",
    "settings.fullName": "Full name",
    "settings.headline": "Headline",
    "settings.headlinePlaceholder": "e.g., Product Designer @ Stripe",
    "settings.bio": "Bio",
    "settings.bioPlaceholder":
      "Tell companies what makes you a standout candidate",
    "settings.saveProfile": "Save profile",
    "settings.saving": "Saving…",
    "settings.resume": "Resume",
    "settings.resumeOnFile":
      "You have a resume on file. Upload a new one to replace it or keep building your profile.",
    "settings.resumeUploadHint":
      "Upload your resume so we can personalize applications.",
    "settings.uploadNewResume": "Upload new resume",
    "settings.uploading": "Uploading…",
    "settings.jobPreferences": "Job preferences",
    "settings.location": "Location",
    "settings.locationPlaceholder": "e.g. Remote, San Francisco",
    "settings.roleType": "Role type",
    "settings.rolePlaceholder": "e.g. Product Designer, Software Engineer",
    "settings.minSalary": "Min salary (optional)",
    "settings.maxSalary": "Max salary (optional)",
    "settings.salaryHint": "Annual salary in USD",
    "settings.savePreferences": "Save preferences",
    "settings.remoteOnly": "Remote only",
    "settings.remoteOnlyDesc": "Prioritize remote-first roles",
    "settings.workAuthorized": "Work authorized",
    "settings.workAuthorizedDesc":
      "I am authorized to work in my target location",
    "settings.visaSponsorship": "Need visa sponsorship",
    "settings.visaSponsorshipDesc": "Only show roles offering visa sponsorship",
    "settings.excludedCompanies": "Excluded companies",
    "settings.excludedKeywords": "Excluded keywords",
    "settings.dataPrivacy": "Data & privacy",
    "settings.exportDescription":
      "Export your data (profile, applications, events) for portability. See our",
    "settings.exportForDetails": "for details.",
    "settings.exportData": "Export my data",
    "settings.exporting": "Exporting…",

    "maintenance.title": "We're making things better",
    "maintenance.description":
      "JobHuntin is temporarily unavailable for scheduled maintenance. We're improving performance and adding new features.",
    "maintenance.expectedBack":
      "We expect to be back within 15–30 minutes. You can check back shortly or contact support if you need assistance.",
    "maintenance.contactSupport": "Contact support",
    "maintenance.progressSaved":
      "Your progress is saved. When we're back, you can pick up right where you left off.",

    "homepage.checkInbox": "Check your inbox",
    "homepage.magicLinkSent": "Magic link sent!",
    "homepage.enterValidEmail": "Enter a valid email",
    "homepage.startFree": "Start free",
    "homepage.sending": "Sending…",

    "pricing.subtitle":
      "One interview from JobHuntin covers this cost forever. People who wait lose roles to people who don't.",
    "pricing.monthly": "Monthly",
    "pricing.annual": "Annual",
    "pricing.save20": "Save 20% with annual billing",
    "pricing.starter": "Starter",
    "pricing.proHunter": "Pro Hunter",
    "pricing.agency": "Agency",
    "pricing.perMonth": "/mo",
    "pricing.billedMonthly": "Billed monthly",
    "pricing.billedAnnually": "Billed annually",
    "pricing.startFree": "Start free",
    "pricing.goToDashboard": "Go to Dashboard",
    "pricing.startTrial": "Start free 7-day trial",
    "pricing.currentPlan": "Current Plan",
    "pricing.contactSales": "Contact Sales",
    "pricing.faqTitle": "Questions? We've got answers.",
    "pricing.faqCancel": "Can I cancel anytime?",
    "pricing.faqCancelA":
      "Yes. One click in your dashboard. No awkward phone calls.",
    "pricing.faqWork": "Does this actually work?",
    "pricing.faqWorkA":
      "We've sent over 1M applications. Our users interview at Google, Amazon, and startups daily.",
    "pricing.faqSafe": "Is my data safe?",
    "pricing.faqSafeA":
      "We use bank-level encryption. Your resume is only shared with employers you apply to.",
    "pricing.faqHired": "What if I get hired?",
    "pricing.faqHiredA":
      "Then we did our job! Cancel your sub and pop the champagne.",

    "successStories.headingWon": "THEY",
    "successStories.headingNext": "WON.",
    "successStories.headingYou": "YOU'RE NEXT.",
    "successStories.subtitle": "Real people. Real offers. No BS.",
    "successStories.ctaTitle": "YOUR TURN.",
    "successStories.ctaDescription":
      "Every hour you wait, someone else gets the interview you wanted.",
    "successStories.startFreeTrial": "Start free trial",
    "successStories.hired": "HIRED",

    "chromeExt.badge": "v2.0 Now Available",
    "chromeExt.heading1": 'The "Add to Cart"',
    "chromeExt.heading2": "for your career.",
    "chromeExt.description":
      "Browse LinkedIn, Indeed, or Glassdoor. See a job you like? Click one button. Our AI handles the resume tailoring, cover letter, and submission.",
    "chromeExt.addToChrome": "Add to Chrome",
    "chromeExt.watchDemo": "Watch Demo",
    "chromeExt.addedToQueue": "Added to Queue",
    "chromeExt.added": "Added",
    "chromeExt.autoApply": "Auto-Apply",
    "chromeExt.apply": "Apply",
    "chromeExt.agentIntelligence": "Agent Intelligence",
    "chromeExt.parsingOpportunities": "Parsing opportunities...",
    "chromeExt.matchScore": "Match Score: 94%",
    "chromeExt.tailoringResume": "Tailoring resume for role...",
    "chromeExt.draftingCoverLetter": "Drafting cover letter...",
    "chromeExt.taskQueued": "Task queued in cloud.",
    "chromeExt.autonomousSync": "Autonomous Sync",
    "chromeExt.applicationPending": "Application pending submission",
    "chromeExt.worksWhere": "Works where you hunt.",
    "chromeExt.platformsHint":
      "Native integration with the platforms you already use.",
    "chromeExt.parsingLatency": "Parsing Latency",
    "chromeExt.fieldAccuracy": "Field Accuracy",
    "chromeExt.activeScouting": "Active Scouting",

    "about.badge": "12,000+ job seekers stopped scrolling",
    "about.heading1": "The end of the",
    "about.heading2": "infinite scroll.",
    "about.heroDescription":
      "We built JobHuntin because finding a job shouldn't be a full-time job. So we moved the hard part to an engine that never sleeps.",
    "about.experienceMagic": "Experience the magic",
    "about.watchStory": "Watch the story",
    "about.enterpriseIntelligence": "Enterprise-Grade Intelligence",
    "about.digitalDouble": "A digital double that hunts for you.",
    "about.digitalDoubleDesc":
      'Our system doesn\'t just "find" jobs. It analyzes your unique skills, matches them against real market demand, and handles the entire application lifecycle — from the initial find to the final submit.',
    "about.privacyFirst": "Privacy First",
    "about.privacyFirstDesc":
      "Encrypted, never sold. Recruiters only see what you approve.",
    "about.lightningPrecision": "Lightning Precision",
    "about.lightningPrecisionDesc":
      "Thousands of jobs parsed per minute. Your match scores update in milliseconds.",
    "about.successRate": "Success Rate",
    "about.timeSaved": "Time Saved",
    "about.howEngineWorks": "How the engine works.",
    "about.howEngineDesc":
      "Four steps. Zero effort from you. Applications that actually get responses.",
    "about.parse": "Parse",
    "about.parseDesc":
      "We build your digital twin from your resume and LinkedIn.",
    "about.scout": "Scout",
    "about.scoutDesc": "AI agents scan the web for jobs that match your DNA.",
    "about.tailor": "Tailor",
    "about.tailorDesc":
      "Resumes and cover letters are rewritten for every single job.",
    "about.apply": "Apply",
    "about.applyDesc":
      "Submissions happen automatically. You just track notifications.",
    "about.visionHeading": "Every day you wait, someone else gets hired.",
    "about.visionDescription":
      "Your time should be spent in interviews, not on job boards. The people who start today land roles 3x faster.",
    "about.getStartedFree": "Get Started for Free",
    "about.noCardRequired":
      "No credit card required. Cancel anytime. Actually works.",

    "contact.getInTouch": "Get in Touch",
    "contact.headingLine1": "We're here to help you",
    "contact.headingLine2": "land your dream job.",
    "contact.subtitle":
      "Whether you have questions, need support, or want to explore partnerships, our team is ready to help.",
    "contact.sendMessage": "Send us a message",
    "contact.name": "Name",
    "contact.email": "Email",
    "contact.company": "Company",
    "contact.companyPlaceholder": "Acme Corp (optional)",
    "contact.inquiryType": "Inquiry Type",
    "contact.generalQuestion": "General Question",
    "contact.technicalSupport": "Technical Support",
    "contact.salesInquiry": "Sales Inquiry",
    "contact.partnership": "Partnership",
    "contact.message": "Message",
    "contact.messagePlaceholder": "Tell us how we can help you...",
    "contact.sending": "Sending...",
    "contact.sendMessageBtn": "Send Message",
    "contact.messageSent": "Message Sent!",
    "contact.messageSentDescription":
      "We'll get back to you within 24 hours. Keep an eye on your inbox for a response from our team.",
    "contact.backToHomepage": "Back to Homepage",
    "contact.otherWays": "Other ways to reach us",
    "contact.emailLabel": "Email",
    "contact.respondWithin24": "We respond within 24 hours",
    "contact.salesTeam": "Sales Team",
    "contact.salesHint": "For enterprise and team plans",
    "contact.securityPrivacy": "Security & Privacy",
    "contact.privacyHint": "For data protection inquiries",
    "contact.needImmediateHelp": "Need immediate help?",
    "contact.faqHint":
      "Check out our comprehensive FAQ section or browse our documentation for quick answers to common questions.",
    "contact.browseGuides": "Browse Guides",
    "contact.viewPricing": "View Pricing",
    "contact.responseTime": "Response Time",
    "contact.responseTimeDesc":
      "We typically respond to all inquiries within 24 hours during business days (Monday-Friday, 9AM-5PM EST).",
  },
  fr: {
    "dashboard.activeRadar": "Radar actif",
    "dashboard.swipeRight":
      "Faites glisser à droite pour laisser l'IA postuler pour vous.",
    "dashboard.resetFilters": "Réinitialiser les filtres et relancer",
    "dashboard.loadMore": "Charger plus d'offres",
    "dashboard.loadingMore": "Chargement...",
    "dashboard.noMatches":
      "Vous avez examiné toutes les offres pour ces filtres. Élargissez la localisation ou abaissez le salaire minimum pour en trouver plus.",
    "dashboard.reviewSwipes": "Revoir les swipes",
    "dashboard.filterPlaceholder": "Filtrer par localisation...",
    "dashboard.matchAlert": "Alerte match ! Offre très adaptée détectée.",
    "dashboard.sweepComplete": "Balayage terminé",
    "dashboard.aiAgentMonitoring": "Votre agent IA surveille activement les",
    "dashboard.aiAgentMonitoringNewListings": "nouvelles offres d'emploi",
    "dashboard.aiAgentMonitoringSource":
      "sur LinkedIn et Wellfound. Les nouveaux matchs apparaîtront bientôt sur votre tableau de bord.",
    "dashboard.jobsRemaining": "offres restantes",
    "dashboard.showingApplications":
      "{count} sur {total} candidatures affichées",
    "dashboard.firstStepsTitle": "Vos 3 premières étapes",
    "dashboard.firstSteps1":
      "Swipez à droite sur les offres qui vous plaisent — notre IA postulera pour vous",
    "dashboard.firstSteps2": "Consultez Candidatures pour suivre le statut",
    "dashboard.firstSteps3":
      "Répondez aux questions HOLD pour faire avancer vos candidatures",
    "dashboard.dismiss": "Fermer",
    "dashboard.dismissFirstSteps": "Fermer les premières étapes",

    "applications.emptyTitle": "Aucune candidature",
    "applications.emptyDescription":
      "Votre agent n'a pas encore trouvé d'opportunités. Commencez à swiper sur des offres pour obtenir des matchs.",
    "applications.noResults": "Aucun résultat",
    "applications.noActiveApplications": "Aucune candidature active",
    "applications.searchNoResults":
      "Aucune candidature ne correspond à votre recherche.",
    "applications.searchNoResultsDesktop":
      "Aucune candidature ne correspond à votre recherche.",
    "applications.errorLoading": "Impossible de charger les candidatures.",
    "applications.emptyDesktopDescription":
      "Aucune candidature pour l'instant. Commencez à rechercher pour trouver des opportunités.",
    "applications.startSearching": "Commencer la recherche",
    "applications.loadMore": "Charger plus",

    // Onboarding - Welcome Step (French)
    "onboarding.welcomeTitle": "Trouvez l'emploi de vos rêves.",
    "onboarding.welcomeSubtitle":
      "Nous vous aiderons à postuler automatiquement. La configuration prend environ 2–3 minutes.",
    "onboarding.startSetup": "Commencer",
    "onboarding.feature1Title": "Télécharger le CV",
    "onboarding.feature1Desc":
      "Nous analyserons vos compétences et votre expérience",
    "onboarding.feature2Title": "Définir les préférences",
    "onboarding.feature2Desc": "Dites-nous où et quoi vous voulez travailler",
    "onboarding.feature3Title": "Candidature auto",
    "onboarding.feature3Desc":
      "Nous postulerons aux emplois pour vous automatiquement",

    // Onboarding - Resume Step (French)
    "onboarding.resumeTitle": "Téléchargez votre CV",
    "onboarding.resumeSubtitle":
      "Nous l'utiliserons pour trouver les matchs parfaits",
    "onboarding.uploadResume": "Télécharger le CV",
    "onboarding.dragAndDrop": "Glissez-déposez votre CV ici",
    "onboarding.fileTypes": "PDF, DOCX jusqu'à 15 Mo",
    "onboarding.linkedinPlaceholder": "Profil LinkedIn (optionnel)",
    "onboarding.linkedinError": "Veuillez entrer une URL LinkedIn valide",
    "onboarding.skipResumeTitle": "Passer le CV ?",
    "onboarding.skipResumeDesc":
      "Le CV améliore la qualité des matchs d'environ 40%. Vous pouvez l'ajouter plus tard dans Paramètres.",
    "onboarding.skipForNow": "Passer pour l'instant",
    "onboarding.goBack": "Retour",
    "onboarding.parsingPreview": "Voici ce que nous avons trouvé :",
    "onboarding.looksGoodContinue": "Ça semble bien, continuer",
    "onboarding.reupload": "Re-télécharger",
    "onboarding.parsingErrorHint":
      "Vous pouvez essayer un autre fichier, ou passer et ajouter vos informations manuellement aux étapes suivantes.",

    // Onboarding - Skill Review Step (French)
    "onboarding.skillsTitle": "Vérifiez vos compétences",
    "onboarding.skillsSubtitle":
      "Vérifiez les compétences que nous avons détectées",
    "onboarding.noSkills": "Aucune compétence détectée dans votre CV",
    "onboarding.addSkillPlaceholder": "Ajouter une compétence...",
    "onboarding.saveSkill": "Enregistrer",
    "onboarding.cancel": "Annuler",
    "onboarding.yearsExperience": "années",
    "onboarding.confidence": "confiance",
    "onboarding.skillsCount": "{count} compétences",
    "onboarding.maxSkillsReached": "Maximum atteint",
    "onboarding.maxSkillsDesc":
      "Vous pouvez ajouter jusqu'à 100 compétences. Supprimez-en pour en ajouter plus.",
    "onboarding.contextLengthHint": "Max 200 caractères",
    "onboarding.careerGoalsRequired":
      "Veuillez sélectionner le niveau d'expérience et l'urgence de recherche.",
    "onboarding.expLevelEntry": "Débutant",
    "onboarding.expLevelEntrySub": "0–1 an",
    "onboarding.expLevelJunior": "Junior",
    "onboarding.expLevelJuniorSub": "1–3 ans",
    "onboarding.expLevelMid": "Intermédiaire",
    "onboarding.expLevelMidSub": "3–5 ans",
    "onboarding.expLevelSenior": "Senior",
    "onboarding.expLevelSeniorSub": "5–10 ans",
    "onboarding.expLevelStaff": "Staff+",
    "onboarding.expLevelStaffSub": "10+ ans",
    "onboarding.urgencyActive": "Recherche active",
    "onboarding.urgencyActiveDesc": "En entretiens et prêt à bouger",
    "onboarding.urgencyOpen": "Ouvert aux offres",
    "onboarding.urgencyOpenDesc": "Content mais curieux des opportunités",
    "onboarding.urgencyExploring": "En exploration",
    "onboarding.urgencyExploringDesc": "Pas pressé, je vois ce qui existe",
    "onboarding.goalSeniorIc": "Rôle IC Senior",
    "onboarding.goalManagement": "Management",
    "onboarding.goalCareerChange": "Réorientation",
    "onboarding.goalHigherComp": "Meilleure rémunération",
    "onboarding.goalWorkLife": "Équilibre vie pro/perso",
    "onboarding.goalStartup": "Expérience startup",
    "onboarding.reasonGrowth": "Évolution de carrière",
    "onboarding.reasonCompensation": "Rémunération",
    "onboarding.reasonCulture": "Culture d'entreprise",
    "onboarding.reasonLayoff": "Licenciement / Restructuration",
    "onboarding.reasonRelocation": "Déménagement",
    "onboarding.reasonContract": "Fin de contrat",
    "onboarding.reasonNotEmployed": "Sans emploi actuellement",

    // Onboarding - Contact Step (French)
    "onboarding.contactTitle": "Confirmez vos coordonnées",
    "onboarding.contactSubtitle":
      "Vérifiez les informations que nous avons extraites",
    "onboarding.firstName": "Prénom",
    "onboarding.lastName": "Nom",
    "onboarding.email": "E-mail",
    "onboarding.phone": "Téléphone",
    "onboarding.required": "Requis",
    "onboarding.invalidFormat": "Format invalide",
    "onboarding.didYouMean": "Vouliez-vous dire",

    // Onboarding - Preferences Step (French)
    "onboarding.preferencesTitle": "Préférences d'emploi",
    "onboarding.preferencesSubtitle": "Dites-nous ce que vous cherchez",
    "onboarding.location": "Localisation",
    "onboarding.locationPlaceholder": "ex. Télétravail, Paris",
    "onboarding.roleType": "Type de poste",
    "onboarding.rolePlaceholder": "ex. Chef de produit",
    "onboarding.minSalary": "Salaire min (optionnel)",
    "onboarding.maxSalary": "Salaire max (optionnel)",
    "onboarding.salaryHint": "Salaire annuel en USD",
    "onboarding.remoteOnly": "Télétravail uniquement",
    "onboarding.onsiteOnly": "Sur site uniquement",
    "onboarding.workAuthorized": "Autorisé à travailler",
    "onboarding.workAuthorizedDesc":
      "Je suis autorisé à travailler dans ma zone cible",
    "onboarding.visaSponsorship": "Besoin de parrainage visa",
    "onboarding.visaSponsorshipDesc":
      "Afficher uniquement les offres avec parrainage",
    "onboarding.excludedCompanies": "Entreprises exclues",
    "onboarding.excludedKeywords": "Mots-clés exclus",
    "onboarding.useAISuggestion": "Utiliser la suggestion IA",
    "onboarding.salaryErrorMax": "Le max doit être ≥ au min",
    "onboarding.salaryErrorCap": "Ne peut pas dépasser 10 M$",

    // Onboarding - Work Style Step (French)
    "onboarding.workStyleTitle": "Style de travail",
    "onboarding.workStyleSubtitle":
      "Aidez-nous à trouver votre environnement idéal",
    "onboarding.workStyleQuestion1": "Comment préférez-vous travailler ?",
    "onboarding.workStyleQuestion2": "Comment apprenez-vous le mieux ?",
    "onboarding.workStyleQuestion3": "Quelle étape d'entreprise ?",
    "onboarding.workStyleQuestion4": "Préférence de communication ?",
    "onboarding.workStyleQuestion5": "Préférence de rythme ?",
    "onboarding.workStyleQuestion6": "Niveau de propriété ?",
    "onboarding.workStyleQuestion7": "Trajectoire de carrière ?",
    "onboarding.autonomyPreference": "Je préfère l'autonomie",
    "onboarding.guidancePreference": "Je préfère le guidage",
    "onboarding.mixPreference": "Je préfère un mix",

    // Onboarding - Ready Step (French)
    "onboarding.readyTitle": "Vous êtes prêt !",
    "onboarding.readySubtitle":
      "Il est temps de commencer à chercher un emploi",
    "onboarding.profileStrength": "Force du profil",
    "onboarding.startJobHunting": "Commencer la recherche",
    "onboarding.setupComplete": "Configuration terminée !",
    "onboarding.resumeAddedBadge": "CV ajouté",
    "onboarding.locationSetBadge": "Localisation définie",
    "onboarding.jobTitleSetBadge": "Titre défini",

    // Onboarding - Common (French)
    "onboarding.continue": "Continuer",
    "onboarding.back": "Retour",
    "onboarding.step": "Étape",
    "onboarding.of": "sur",
    "onboarding.restart": "Recommencer",
    "onboarding.confirmRestart":
      "Êtes-vous sûr ? Cela effacera votre progression.",
    "onboarding.confirmRestartTitle": "Recommencer l'intégration ?",
    "onboarding.growthEndpointHint":
      "Une étape optionnelle n'a pas abouti. Vous êtes prêt à chercher !",
    "onboarding.welcomeBack": "Bon retour !",
    "onboarding.pickingUp": "Reprise à",

    "holds.responseRequired": "RÉPONSE REQUISE",

    "app.loading": "Chargement...",
    "app.error": "Une erreur est survenue. Veuillez réessayer.",
    "app.retry": "Réessayer",
    "resumeRetry.offline":
      "Hors ligne. Le CV sera téléchargé automatiquement à la reconnexion.",
    "resumeRetry.maxReached":
      "Nombre maximum de tentatives atteint. Réessayez ou contactez le support.",
    "resumeRetry.retryingIn": "Nouvelle tentative dans {minutes} min...",
    "resumeRetry.ready": "Prêt à réessayer.",
    "resumeRetry.offlineTitle": "Hors ligne - CV enregistré",
    "resumeRetry.failedTitle": "Échec du téléchargement",
    "resumeRetry.pendingTitle": "Téléchargement du CV en attente",
    "resumeRetry.retrying": "Nouvelle tentative...",
    "resumeRetry.retryNow": "Réessayer maintenant",
    "resumeRetry.clear": "Effacer",
    "resumeRetry.attemptOf": "Tentative {current} sur {max}",
    "resumeRetry.reuploadHint":
      "Téléchargez à nouveau votre CV pour réessayer.",
    "app.save": "Enregistrer",
    "app.cancel": "Annuler",
    "app.delete": "Supprimer",
    "app.confirm": "Confirmer",
    "nav.dashboard": "Tableau de bord",
    "nav.jobs": "Emplois",
    "nav.applications": "Candidatures",
    "nav.settings": "Paramètres",
    "nav.billing": "Facturation",
    "nav.team": "Équipe",
    "status.applied": "Candidaté",
    "status.needsInput": "Saisie requise",
    "status.failed": "Échoué",
    "status.queued": "En file d'attente",
    "status.processing": "En cours",

    "jobAlerts.title": "Alertes emploi",
    "jobAlerts.description":
      "Gérez vos alertes de recherche et soyez notifié des offres correspondantes",
    "jobAlerts.createAlert": "Créer une alerte",
    "jobAlerts.createFirstAlert": "Créer votre première alerte",
    "jobAlerts.editAlert": "Modifier l'alerte",
    "jobAlerts.updateAlert": "Mettre à jour l'alerte",
    "jobAlerts.alertName": "Nom de l'alerte",
    "jobAlerts.alertNamePlaceholder": "ex. Emplois Ingénieur logiciel",
    "jobAlerts.keywords": "Mots-clés",
    "jobAlerts.keywordPlaceholder": "ex. React, TypeScript",
    "jobAlerts.locations": "Localisations",
    "jobAlerts.locationPlaceholder": "ex. Paris, Lyon",
    "jobAlerts.minSalary": "Salaire minimum",
    "jobAlerts.maxSalary": "Salaire maximum",
    "jobAlerts.salaryPlaceholder": "50000",
    "jobAlerts.salaryRange": "Salaire",
    "jobAlerts.frequency": "Fréquence des alertes",
    "jobAlerts.daily": "Quotidien",
    "jobAlerts.weekly": "Hebdomadaire",
    "jobAlerts.monthly": "Mensuel",
    "jobAlerts.remoteOnly": "Télétravail uniquement",
    "jobAlerts.searchPlaceholder": "Rechercher des alertes...",
    "jobAlerts.noAlerts": "Aucune alerte emploi",
    "jobAlerts.noAlertsDescription":
      "Créez votre première alerte pour être notifié des offres correspondantes",
    "jobAlerts.noSearchResults":
      "Aucune alerte ne correspond à votre recherche",
    "jobAlerts.active": "Active",
    "jobAlerts.inactive": "Inactive",
    "jobAlerts.toggle": "Activer/Désactiver",
    "jobAlerts.lastSent": "Dernier envoi",
    "jobAlerts.confirmDelete":
      "Êtes-vous sûr de vouloir supprimer cette alerte ?",
    "jobAlerts.errorLoading": "Erreur de chargement des alertes",

    "cookies.description":
      'Nous utilisons des cookies pour analyser le trafic et optimiser votre expérience. En cliquant sur "Tout accepter", vous consentez à l\'utilisation de nos cookies d\'analyse et de marketing. "Tout refuser" utilise uniquement les cookies système essentiels. Voir notre',
    "cookies.privacyPolicy": "Politique de confidentialité",
    "cookies.forDetails": "pour plus de détails.",
    "cookies.rejectAll": "Tout refuser",
    "cookies.managePreferences": "Gérer les préférences",
    "cookies.acceptAnalytics": "Accepter l'analyse",
    "cookies.acceptAll": "Tout accepter",
    "cookies.title": "Consentement aux cookies",
    "cookies.essential": "Essentiels",
    "cookies.essentialDescription":
      "Nécessaires au fonctionnement du site (auth, sécurité, préférences). Non désactivables.",
    "cookies.analytics": "Analytiques",
    "cookies.analyticsDescription":
      "Nous aident à comprendre l'utilisation du site (pages vues, parcours). Aucune donnée personnelle partagée.",
    "cookies.marketing": "Marketing",
    "cookies.marketingDescription":
      "Utilisés pour la publicité et le remarketing. Peuvent partager des données avec des partenaires.",
    "cookies.cancel": "Annuler",
    "cookies.savePreferences": "Enregistrer les préférences",

    "login.checkInbox": "Vérifiez votre e-mail",
    "login.sentTo": "Nous avons envoyé un lien magique à",
    "login.checkSpam": "Pas reçu ? Vérifiez vos spams.",
    "login.step1": "Ouvrez votre boîte de réception (et les spams)",
    "login.step2": "Trouvez l'e-mail de JobHuntin",
    "login.step3": "Cliquez sur le lien magique pour vous connecter",
    "login.resendLink": "Renvoyer le lien",
    "login.resendIn": "Renvoyer dans {seconds}s",
    "login.sending": "Envoi...",
    "login.useDifferentEmail": "Utiliser un autre e-mail",
    "login.welcomeBack": "Décrochez votre prochain poste",
    "login.signInTitle": "Connexion à JobHuntin",
    "login.magicLinkHint":
      "Nous vous enverrons un lien magique. Pas de mot de passe requis.",
    "login.email": "Adresse e-mail",
    "login.emailPlaceholder": "vous@exemple.com",
    "login.continue": "Continuer",
    "login.sessionExpired": "Session expirée",
    "login.signInAgain": "Veuillez vous reconnecter.",
    "login.secure": "Sécurisé • Chiffré • Aucun mot de passe stocké",
    "login.sidebarTitleLine1": "Votre agent IA",
    "login.sidebarTitleLine2": "est prêt à chasser",
    "login.sidebarSubtitle":
      "Connectez-vous pour accéder à votre tableau de bord, suivre vos candidatures et décrocher plus d'entretiens.",
    "login.feature1": "100+ candidatures personnalisées par jour",
    "login.feature2": "Offres de 50+ plateformes",
    "login.feature3": "Postuler en un clic partout",

    "404.title": "404",
    "404.heading": "Cette page n'existe pas.",
    "404.description":
      "La page demandée est introuvable. Essayez de rechercher des emplois ou retournez à l'accueil.",
    "404.startFree": "Commencer gratuitement — 10 candidatures offertes",
    "404.backHome": "Retour à l'accueil",
    "404.popularSearches": "Recherches populaires",
    "404.findNextRole": "Trouvez votre prochain poste avec l'IA",
    "404.applyWithAI": "Postuler avec l'IA",

    "settings.title": "Paramètres",
    "settings.profilePreferences": "Profil et préférences",
    "settings.profileDetails": "Détails du profil",
    "settings.addYourName": "Ajoutez votre nom",
    "settings.recruiterHint": "Facilitez la reconnaissance par les recruteurs.",
    "settings.fullName": "Nom complet",
    "settings.headline": "Titre",
    "settings.headlinePlaceholder": "ex. Product Designer @ Stripe",
    "settings.bio": "Bio",
    "settings.bioPlaceholder": "Décrivez ce qui vous distingue aux entreprises",
    "settings.saveProfile": "Enregistrer le profil",
    "settings.saving": "Enregistrement…",
    "settings.resume": "CV",
    "settings.resumeOnFile":
      "Vous avez un CV enregistré. Téléchargez-en un nouveau pour le remplacer.",
    "settings.resumeUploadHint":
      "Téléchargez votre CV pour personnaliser les candidatures.",
    "settings.uploadNewResume": "Télécharger un nouveau CV",
    "settings.uploading": "Téléchargement…",
    "settings.jobPreferences": "Préférences d'emploi",
    "settings.location": "Localisation",
    "settings.locationPlaceholder": "ex. Télétravail, Paris",
    "settings.roleType": "Type de poste",
    "settings.rolePlaceholder": "ex. Product Designer, Ingénieur logiciel",
    "settings.minSalary": "Salaire min (optionnel)",
    "settings.maxSalary": "Salaire max (optionnel)",
    "settings.salaryHint": "Salaire annuel en USD",
    "settings.savePreferences": "Enregistrer les préférences",
    "settings.remoteOnly": "Télétravail uniquement",
    "settings.remoteOnlyDesc": "Prioriser les rôles à distance",
    "settings.workAuthorized": "Autorisé à travailler",
    "settings.workAuthorizedDesc":
      "Je suis autorisé à travailler dans ma zone cible",
    "settings.visaSponsorship": "Besoin de parrainage visa",
    "settings.visaSponsorshipDesc":
      "Afficher uniquement les offres avec parrainage",
    "settings.excludedCompanies": "Entreprises exclues",
    "settings.excludedKeywords": "Mots-clés exclus",
    "settings.dataPrivacy": "Données et confidentialité",
    "settings.exportDescription":
      "Exportez vos données (profil, candidatures, événements). Consultez notre",
    "settings.exportForDetails": "pour plus de détails.",
    "settings.exportData": "Exporter mes données",
    "settings.exporting": "Export en cours…",

    "maintenance.title": "Nous améliorons le service",
    "maintenance.description":
      "JobHuntin est temporairement indisponible pour maintenance. Nous améliorons les performances et ajoutons de nouvelles fonctionnalités.",
    "maintenance.expectedBack":
      "Retour prévu sous 15 à 30 minutes. Réessayez bientôt ou contactez le support si besoin.",
    "maintenance.contactSupport": "Contacter le support",
    "maintenance.progressSaved":
      "Votre progression est enregistrée. À notre retour, vous pourrez reprendre là où vous en étiez.",

    "homepage.checkInbox": "Vérifiez votre boîte de réception",
    "homepage.magicLinkSent": "Lien magique envoyé !",
    "homepage.enterValidEmail": "Entrez un e-mail valide",
    "homepage.startFree": "Commencer gratuitement",
    "homepage.sending": "Envoi…",

    "pricing.subtitle":
      "Un entretien décroché via JobHuntin couvre ce coût pour toujours. Ceux qui attendent perdent des postes au profit de ceux qui agissent.",
    "pricing.monthly": "Mensuel",
    "pricing.annual": "Annuel",
    "pricing.save20": "Économisez 20 % avec l'abonnement annuel",
    "pricing.starter": "Starter",
    "pricing.proHunter": "Pro Hunter",
    "pricing.agency": "Agency",
    "pricing.perMonth": "/mois",
    "pricing.billedMonthly": "Facturé mensuellement",
    "pricing.billedAnnually": "Facturé annuellement",
    "pricing.startFree": "Commencer gratuitement",
    "pricing.goToDashboard": "Aller au tableau de bord",
    "pricing.startTrial": "Essai gratuit 7 jours",
    "pricing.currentPlan": "Plan actuel",
    "pricing.contactSales": "Contacter les ventes",
    "pricing.faqTitle": "Des questions ? Nous avons les réponses.",
    "pricing.faqCancel": "Puis-je annuler à tout moment ?",
    "pricing.faqCancelA":
      "Oui. Un clic dans votre tableau de bord. Pas d'appels gênants.",
    "pricing.faqWork": "Est-ce que ça marche vraiment ?",
    "pricing.faqWorkA":
      "Nous avons envoyé plus d'1 million de candidatures. Nos utilisateurs passent des entretiens chez Google, Amazon et des startups chaque jour.",
    "pricing.faqSafe": "Mes données sont-elles en sécurité ?",
    "pricing.faqSafeA":
      "Nous utilisons un chiffrement de niveau bancaire. Votre CV n'est partagé qu'avec les employeurs auxquels vous postulez.",
    "pricing.faqHired": "Et si je suis embauché ?",
    "pricing.faqHiredA":
      "Alors nous avons réussi ! Annulez votre abonnement et sabrez le champagne.",

    "successStories.headingWon": "ILS",
    "successStories.headingNext": "ONT RÉUSSI.",
    "successStories.headingYou": "À VOUS.",
    "successStories.subtitle": "De vrais gens. De vraies offres. Sans blabla.",
    "successStories.ctaTitle": "VOTRE TOUR.",
    "successStories.ctaDescription":
      "Chaque heure d'attente, quelqu'un d'autre décroche l'entretien que vous vouliez.",
    "successStories.startFreeTrial": "Essai gratuit",
    "successStories.hired": "EMBAUCHÉ",

    "chromeExt.badge": "v2.0 disponible",
    "chromeExt.heading1": 'Le "Ajouter au panier"',
    "chromeExt.heading2": "pour votre carrière.",
    "chromeExt.description":
      "Parcourez LinkedIn, Indeed ou Glassdoor. Une offre vous plaît ? Un clic. Notre IA gère le CV, la lettre de motivation et l'envoi.",
    "chromeExt.addToChrome": "Ajouter à Chrome",
    "chromeExt.watchDemo": "Voir la démo",
    "chromeExt.addedToQueue": "Ajouté à la file",
    "chromeExt.added": "Ajouté",
    "chromeExt.autoApply": "Postuler auto",
    "chromeExt.apply": "Postuler",
    "chromeExt.agentIntelligence": "Intelligence agent",
    "chromeExt.parsingOpportunities": "Analyse des offres...",
    "chromeExt.matchScore": "Score de match : 94 %",
    "chromeExt.tailoringResume": "Adaptation du CV...",
    "chromeExt.draftingCoverLetter": "Rédaction de la lettre...",
    "chromeExt.taskQueued": "Tâche en file.",
    "chromeExt.autonomousSync": "Synchronisation autonome",
    "chromeExt.applicationPending": "Candidature en attente",
    "chromeExt.worksWhere": "Là où vous cherchez.",
    "chromeExt.platformsHint":
      "Intégration native avec les plateformes que vous utilisez.",
    "chromeExt.parsingLatency": "Latence d'analyse",
    "chromeExt.fieldAccuracy": "Précision des champs",
    "chromeExt.activeScouting": "Recherche active",

    "about.badge": "12 000+ chercheurs d'emploi ont arrêté de scroller",
    "about.heading1": "La fin du",
    "about.heading2": "scroll infini.",
    "about.heroDescription":
      "Nous avons créé JobHuntin car chercher un emploi ne devrait pas être un travail à temps plein. Nous avons délégué la partie difficile à un moteur qui ne dort jamais.",
    "about.experienceMagic": "Découvrez la magie",
    "about.watchStory": "Voir l'histoire",
    "about.enterpriseIntelligence": "Intelligence de niveau entreprise",
    "about.digitalDouble": "Un double numérique qui chasse pour vous.",
    "about.digitalDoubleDesc":
      'Notre système ne "trouve" pas juste des offres. Il analyse vos compétences, les compare à la demande réelle et gère tout le cycle de candidature.',
    "about.privacyFirst": "Confidentialité d'abord",
    "about.privacyFirstDesc":
      "Chiffré, jamais vendu. Les recruteurs ne voient que ce que vous approuvez.",
    "about.lightningPrecision": "Précision éclair",
    "about.lightningPrecisionDesc":
      "Des milliers d'offres analysées par minute. Vos scores de match se mettent à jour en millisecondes.",
    "about.successRate": "Taux de succès",
    "about.timeSaved": "Temps gagné",
    "about.howEngineWorks": "Comment fonctionne le moteur.",
    "about.howEngineDesc":
      "Quatre étapes. Zéro effort de votre part. Des candidatures qui obtiennent des réponses.",
    "about.parse": "Analyser",
    "about.parseDesc":
      "Nous créons votre jumeau numérique à partir de votre CV et LinkedIn.",
    "about.scout": "Explorer",
    "about.scoutDesc":
      "Les agents IA scannent le web pour des offres qui correspondent à votre profil.",
    "about.tailor": "Adapter",
    "about.tailorDesc":
      "CV et lettres de motivation réécrits pour chaque offre.",
    "about.apply": "Postuler",
    "about.applyDesc":
      "Les envois sont automatiques. Vous suivez les notifications.",
    "about.visionHeading":
      "Chaque jour d'attente, quelqu'un d'autre est embauché.",
    "about.visionDescription":
      "Votre temps devrait être passé en entretiens, pas sur les sites d'emploi. Ceux qui commencent aujourd'hui décrochent des postes 3× plus vite.",
    "about.getStartedFree": "Commencer gratuitement",
    "about.noCardRequired":
      "Pas de carte bancaire. Annulez quand vous voulez. Ça marche vraiment.",

    "contact.getInTouch": "Contactez-nous",
    "contact.headingLine1": "Nous sommes là pour vous aider à",
    "contact.headingLine2": "décrocher l'emploi de vos rêves.",
    "contact.subtitle":
      "Questions, support ou partenariats : notre équipe est prête à vous aider.",
    "contact.sendMessage": "Envoyez-nous un message",
    "contact.name": "Nom",
    "contact.email": "E-mail",
    "contact.company": "Entreprise",
    "contact.companyPlaceholder": "Acme Corp (optionnel)",
    "contact.inquiryType": "Type de demande",
    "contact.generalQuestion": "Question générale",
    "contact.technicalSupport": "Support technique",
    "contact.salesInquiry": "Demande commerciale",
    "contact.partnership": "Partenariat",
    "contact.message": "Message",
    "contact.messagePlaceholder":
      "Dites-nous comment nous pouvons vous aider...",
    "contact.sending": "Envoi...",
    "contact.sendMessageBtn": "Envoyer",
    "contact.messageSent": "Message envoyé !",
    "contact.messageSentDescription":
      "Nous vous répondrons sous 24 heures. Surveillez votre boîte de réception.",
    "contact.backToHomepage": "Retour à l'accueil",
    "contact.otherWays": "Autres moyens de nous joindre",
    "contact.emailLabel": "E-mail",
    "contact.respondWithin24": "Réponse sous 24 heures",
    "contact.salesTeam": "Équipe commerciale",
    "contact.salesHint": "Pour les plans entreprise et équipe",
    "contact.securityPrivacy": "Sécurité et confidentialité",
    "contact.privacyHint": "Pour les demandes de protection des données",
    "contact.needImmediateHelp": "Besoin d'aide immédiate ?",
    "contact.faqHint":
      "Consultez notre FAQ ou notre documentation pour des réponses rapides.",
    "contact.browseGuides": "Parcourir les guides",
    "contact.viewPricing": "Voir les tarifs",
    "contact.responseTime": "Délai de réponse",
    "contact.responseTimeDesc":
      "Nous répondons généralement sous 24 heures en jours ouvrés (lun-ven, 9h-17h EST).",
  },
};

const rtlLocales = ["ar", "he", "fa", "ur"];

// RTL language detection and support
export function isRTLLanguage(locale: string): boolean {
  const rtlLanguages = ["ar", "he", "fa", "ur", "ps", "yi"];
  return rtlLanguages.includes(locale);
}

export function getDirection(locale: string): "ltr" | "rtl" {
  return isRTLLanguage(locale) ? "rtl" : "ltr";
}

export function setDocumentDirection(locale: string) {
  const direction = getDirection(locale);
  document.documentElement.dir = direction;
  document.documentElement.lang = locale;
}

const LANGUAGE_KEY = "jobhuntin-language";

export function getLocale(): string {
  if (typeof window === "undefined") return "en";
  const stored = localStorage.getItem(LANGUAGE_KEY);
  if (stored) return stored;
  return navigator.language || navigator.languages?.[0] || "en";
}

export function t(key: string, locale?: string): string {
  const lang = (locale || getLocale()).split("-")[0].toLowerCase();
  const dict = dictionaries[lang] || dictionaries.en;
  return dict[key] || dictionaries.en[key] || key;
}

/** Format a translation with {param} placeholders */
export function formatT(
  key: string,
  parameters: Record<string, string | number>,
  locale?: string,
): string {
  let string_ = t(key, locale);
  for (const [k, v] of Object.entries(parameters)) {
    string_ = string_.replaceAll(new RegExp(`\\{${k}\\}`, "g"), String(v));
  }
  return string_;
}
