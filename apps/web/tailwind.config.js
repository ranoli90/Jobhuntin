import { fontFamily } from "tailwindcss/defaultTheme";

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", ...fontFamily.sans],
        serif: ["'Merriweather'", "'Playfair Display'", ...fontFamily.serif],
        body: ["Inter", ...fontFamily.sans],
      },
      colors: {
        border: "rgb(var(--border))",
        input: "rgb(var(--input))",
        ring: "rgb(var(--ring))",
        background: "rgb(var(--background))",
        foreground: "rgb(var(--foreground))",
        primary: {
          DEFAULT: "rgb(var(--primary))",
          foreground: "rgb(var(--primary-foreground))",
          50: '#fafafa',
          100: '#f4f4f5',
          200: '#e4e4e7',
          300: '#d4d4d8',
          400: '#a1a1aa',
          500: '#71717a',
          600: '#52525b',
          700: '#3f3f46',
          800: '#27272a',
          900: '#18181b',
        },
        secondary: {
          DEFAULT: "rgb(var(--secondary))",
          foreground: "rgb(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "rgb(var(--destructive))",
          foreground: "rgb(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "rgb(var(--muted))",
          foreground: "rgb(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "rgb(var(--accent))",
          foreground: "rgb(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "rgb(var(--popover))",
          foreground: "rgb(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "rgb(var(--card))",
          foreground: "rgb(var(--card-foreground))",
        },
        // Notion-esque minimal palette + legacy brand colors for Login/marketing
        // Matches Homepage design tokens for UI continuity
        brand: {
          black: "#000000",
          ink: "#121212", // Very dark gray for slightly softer text than pure black
          text: "#2D2A26", // Homepage primary text
          muted: "#787774", // Homepage muted text
          border: "#E3E2E0", // Homepage borders
          white: "#FFFFFF",
          gray: "#F6F5F4", // The "Notion Gray" for secondary backgrounds
          grayDark: "#EAEAEA", // For 1px borders
          primary: "#455DD3", // Homepage primary blue — use for buttons, nav active, accents
          primaryHover: "#3A4FB8",
          accent: "#2563EB", // Fallback blue
          sunrise: "#FF9C6B",
          lagoon: "#17BEBB",
          plum: "#6A4C93",
          mango: "#FFC857",
        },
        // Semantic colors (muted/professional)
        success: {
          500: '#10B981', // Emerald
        },
        warning: {
          500: '#F59E0B', // Amber
        },
        error: {
          500: '#EF4444', // Red
        },
      },
      boxShadow: {
        // Flat, subtle shadows instead of heavy glows
        card: "0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.03)",
        elevated: "0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.03)",
        flat: "0 2px 0 0 rgba(0, 0, 0, 0.05)",
      },
      borderRadius: {
        sm: '4px',
        md: '8px',
        lg: '12px',
        xl: '16px',
        full: '9999px', // for pills
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
