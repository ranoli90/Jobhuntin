I will implement the **Sorcé Precision System** as strictly requested, focusing on exact metrics, high contrast, and a utilitarian "precision" aesthetic.

### **Phase 1: The Precision System (Configuration)**
We will strip the current design system entirely and replace it with the strict Sorcé specifications.

1.  **Tailwind Configuration (`tailwind.config.js`)**:
    *   **Colors**: Define the 6-color palette exactly:
        *   `sorce-bg-main`: `#0a0a0a`
        *   `sorce-bg-card`: `#111111`
        *   `sorce-accent`: `#10ff95` (The "Precision" Green)
        *   `sorce-text-main`: `#f8fafc`
        *   `sorce-text-muted`: `#94a3b8`
        *   `sorce-border`: `#334155`
    *   **Typography**: Set `Inter` as the sole font family.
    *   **Radius**: Set default and extended border radius to exactly `12px`.
    *   **Container**: Configure `max-width: 1440px` and center it.

2.  **Global Styles (`index.css`)**:
    *   Import `Inter` (Weights 100-900).
    *   Reset `body` to `bg-[#0a0a0a]` and `text-[#f8fafc]`.
    *   Remove all existing animations, glows, and soft shadows.

### **Phase 2: Component Refactoring (The Wireframe)**
1.  **The Grid System**:
    *   Implement a wrapper component or utility class for the **12-column grid** with **24px gutters**.

2.  **Hero Section (`Hero.tsx`)**:
    *   **Layout**: Strict grid alignment.
    *   **Typography**: `h1` set to exactly `120px` (using arbitrary value `text-[120px]`) with tight tracking.
    *   **Styling**:
        *   No gradients, no blurs.
        *   **1px Borders**: All elements (buttons, cards) will have `border border-[#334155]`.
        *   **CTA**: Solid `#10ff95` background or outlined with the accent color.

3.  **Base Components**:
    *   **Button**: Square off slightly (12px radius), 1px border, precise padding.
    *   **Badge**: 1px border, mono-color background (e.g., `#111`), 12px radius.

### **Deliverables**
*   Updated `tailwind.config.js` & `index.css`.
*   Refactored `Hero.tsx` strictly adhering to the "Precision" wireframe.
