import { fontFamily } from "tailwindcss/defaultTheme";

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", ...fontFamily.sans],
        poppins: ["Poppins", ...fontFamily.sans],
        nunito: ["Nunito", ...fontFamily.sans],
      },
      colors: {
        jobhunt: {
          primary: "#FF6B35", // Vibrant Denver sunset orange
          secondary: "#4A90E2", // Cool tech blue
          background: "#FAF9F6", // Warm off-white
          text: "#2D2D2D", // Soft charcoal gray
          "text-light": "#64748B",
        },
      },
      boxShadow: {
        glow: "0 0 20px rgba(255, 107, 53, 0.3)",
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
          "0%, 100%": { opacity: "1", boxShadow: "0 0 20px rgba(255, 107, 53, 0.3)" },
          "50%": { opacity: "0.8", boxShadow: "0 0 30px rgba(255, 107, 53, 0.6)" },
        },
      },
    },
  },
  plugins: [],
};
