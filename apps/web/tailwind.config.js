import { fontFamily } from "tailwindcss/defaultTheme";

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", ...fontFamily.sans],
        display: ["Poppins", ...fontFamily.sans],
        poppins: ["Poppins", ...fontFamily.sans],
        nunito: ["Nunito", ...fontFamily.sans],
      },
      colors: {
        primary: {
          50: "rgb(var(--color-primary-50) / <alpha-value>)",
          100: "rgb(var(--color-primary-100) / <alpha-value>)",
          200: "rgb(var(--color-primary-200) / <alpha-value>)",
          300: "rgb(var(--color-primary-300) / <alpha-value>)",
          400: "rgb(var(--color-primary-400) / <alpha-value>)",
          500: "rgb(var(--color-primary-500) / <alpha-value>)",
          600: "rgb(var(--color-primary-600) / <alpha-value>)",
          700: "rgb(var(--color-primary-700) / <alpha-value>)",
        },
        brand: {
          ink: "#0F172A",
          accent: "#2563eb",
          shell: "#f8fafc",
        },
      },
      boxShadow: {
        glow: "0 0 20px rgba(59, 130, 246, 0.3)",
      },
      animation: {
        "float": "float 6s ease-in-out infinite",
        "pulse-glow": "pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "gradient-x": "gradient-x 5s ease infinite",
      },
      keyframes: {
        "gradient-x": {
          "0%, 100%": { "background-size": "200% 200%", "background-position": "left center" },
          "50%": { "background-size": "200% 200%", "background-position": "right center" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-20px)" },
        },
        "pulse-glow": {
          "0%, 100%": { opacity: "1", boxShadow: "0 0 20px rgba(59, 130, 246, 0.3)" },
          "50%": { opacity: "0.8", boxShadow: "0 0 30px rgba(59, 130, 246, 0.6)" },
        },
      },
    },
  },
  plugins: [],
};
