export const jobhuntinTheme = {
  name: "JOBHUNTIN",
  brandVoice: ["playful", "scrappy", "energetic"],
  colors: {
    sunrise: "#FF9C6B",
    lagoon: "#17BEBB",
    plum: "#6A4C93",
    mango: "#FFC857",
    ink: "#101828",
    shell: "#FFF8F1",
  },
  typography: {
    primary: "'Baloo 2', 'Inter', system-ui, sans-serif",
    secondary: "'Space Grotesk', 'Inter', system-ui, sans-serif",
    scale: {
      hero: "clamp(2.8rem, 4vw, 4.5rem)",
      headline: "clamp(2rem, 2.6vw, 3rem)",
      title: "1.75rem",
      body: "1rem",
      small: "0.9rem",
    },
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 40,
    xxl: 64,
  },
  radii: {
    pill: "999px",
    blob: "32px",
    card: "24px",
    chip: "999px",
  },
  shadows: {
    float: "0 25px 70px rgba(16, 24, 40, 0.15)",
    card: "0 18px 40px rgba(255, 156, 107, 0.25)",
    badge: "0 10px 25px rgba(23, 190, 187, 0.35)",
  },
};

export type JobHuntinTheme = typeof jobhuntinTheme;
