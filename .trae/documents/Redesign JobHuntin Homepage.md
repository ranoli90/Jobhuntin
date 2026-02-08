I will redesign the homepage for `JobHuntin` within the existing `web` project, adapting the requested Next.js-style code to work in the current Vite environment while keeping the structure ready for easy migration.

### 1. Update Project Configuration

* **`web/index.html`**:

  * Update `<title>` to "JobHuntin: AI Job Search Automation".

  * Add Google Fonts CDN links for **Poppins** (Headers), **Nunito** (Playful accents), and **Inter** (Body).

* **`web/tailwind.config.js`**:

  * Extend the theme with JobHuntin's brand colors:

    * Primary: `#FF6B35` (Denver Sunset Orange)

    * Secondary: `#4A90E2` (Cool Tech Blue)

    * Neutral Bg: `#FAF9F6` (Warm Off-White)

    * Text: `#2D2D2D` (Charcoal Gray)

  * Add font families: `poppins` and `nunito`.

### 2. Implement Redesigned Homepage

* **`web/src/pages/Homepage.tsx`**:

  * **Structure**: Rewrite the file as a self-contained "Single Page" component with all sub-components defined inline (for easy copy-paste as requested).

  * **Hero Section**:

    * Full-screen (80vh) with parallax effects using `framer-motion`.

    * "Hunt Jobs with AI Magic" kinetic header.

    * "Start AI Hunt" pulsing CTA with a mock email/resume drop zone.

    * Simulated "AI Scanning" loading state.

  * **Onboarding Teaser**:

    * Asymmetric layout with robot analysis animation.

    * Stats bar with counter animations.

  * **Featured Jobs (Infinite Scroll)**:

    * Masonry-style grid with sample job cards (Tesla, Snapchat, etc.).

    * "Swipe" and "Match Score" UI elements.

  * **Comparison Section**:

    * "Why Us vs Sorce" comparison with icons.

  * **Footer**:

    * Simple branded footer with links.

  * **Tech Stack Adaptation**:

    * Use standard `<img>` tags (instead of Next.js `<Image>`) for compatibility.

    * Use `framer-motion` for all entrance and interaction animations.

    * Ensure responsive mobile-first Tailwind classes.

### 3. Verification

* The code will be valid React/TypeScript and runnable in the current Vite dev server.

* I will verify the page loads and animations trigger correctly.

