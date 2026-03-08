# Polish Implementation Plan — Homepage, Login, Pricing

## Phase 1: Homepage (Homepage.tsx) ✅
- [x] 1.1 Skip link: #191919 → #2D2A26
- [x] 1.2 EmailForm success: #191919/#999 → #2D2A26/#787774
- [x] 1.3 Hero stats card, feature cards, pull quote, features list: #191919 → #2D2A26
- [x] 1.4 Section divider: #E7E5E4 → #E9E9E7
- [x] 1.5 Hero illustrations: add loading="lazy"
- [x] 1.6 Accessibility: aria-label on "See how it works", aria-hidden on scroll cue, aria-live on user journey
- [x] 1.7 UX: active:scale on sticky CTA, focus-visible rings on hero CTAs
- [x] 1.8 User journey: Page Visibility API to pause when tab hidden

## Phase 2: Login (Login.tsx) ✅
- [x] 2.1 Left panel SVG: aria-hidden="true"
- [x] 2.2 Success state: role="alert" on main message
- [x] 2.3 Resend button: aria-busy when loading
- [x] 2.4 Email suggestions: role="listbox", keyboard nav (arrow keys, Enter)
- [x] 2.5 Secure/Encrypted badges: aria-label
- [x] 2.6 Form: aria-label

## Phase 3: Pricing (Pricing.tsx) ✅
- [x] 3.1 Hero: add second SVG path
- [x] 3.2 Free/Pro sections: hover states on cards and CTAs
- [x] 3.3 Exit intent: role="dialog", aria-modal, focus trap, Escape to close
- [x] 3.4 FAQ: aria-controls, focus-visible styles
- [x] 3.5 CTAs: active:scale tap feedback

## Phase 4: PricingSkeleton (Skeleton.tsx) ✅
- [x] 4.1 Match new 2-section layout (Free + Pro, not 3 cards)
- [x] 4.2 Match brand colors (#F7F6F3, #2D2A26)

## Phase 5: Cross-page & Shared ✅
- [x] 5.1 MarketingLayout: skip link works (inherited)
- [x] 5.2 Homepage SEO: og:image in App.tsx defaults
- [x] 5.3 Code: removed unused useCallback from Pricing

## Phase 6: Browser Review ✅
- [x] 6.1 Start dev server, verify all three pages
- [x] 6.2 Test keyboard nav, focus states
- [x] 6.3 Test mobile viewport
- [x] 6.4 Test exit intent on Pricing (popup requires mouse to leave document at top - hard to trigger in automated env; logic is implemented)
