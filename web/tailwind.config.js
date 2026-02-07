import { fontFamily } from "tailwindcss/defaultTheme";

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["'Baloo 2'", ...fontFamily.sans],
        body: ["'Space Grotesk'", ...fontFamily.sans],
      },
      colors: {
        brand: {
          sunrise: "rgb(var(--skedaddle-sunrise) / <alpha-value>)",
          lagoon: "rgb(var(--skedaddle-lagoon) / <alpha-value>)",
          mango: "rgb(var(--skedaddle-mango) / <alpha-value>)",
          ink: "rgb(var(--skedaddle-ink) / <alpha-value>)",
          shell: "rgb(var(--skedaddle-shell) / <alpha-value>)",
        },
      },
      boxShadow: {
        wobble: "0 25px 70px rgba(15, 23, 42, 0.15)",
        pill: "0 12px 30px rgba(255, 152, 67, 0.35)",
      },
      borderRadius: {
        blob: "2rem",
      },
      transitionTimingFunction: {
        scoot: "cubic-bezier(0.32, 1.1, 0.3, 1)",
      },
    },
  },
  plugins: [],
};
