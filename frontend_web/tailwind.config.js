/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "hsl(214 18% 87%)",
        surface: "hsl(0 0% 100%)",
        muted: "hsl(210 20% 96%)",
        ink: "hsl(224 28% 14%)",
        accent: "hsl(173 76% 32%)",
        warning: "hsl(34 92% 48%)",
        danger: "hsl(0 72% 51%)"
      },
      boxShadow: {
        soft: "0 12px 36px rgb(15 23 42 / 0.08)"
      },
      keyframes: {
        "slide-in": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        },
        "pop-complete": {
          "0%": { transform: "scale(0.96)" },
          "70%": { transform: "scale(1.02)" },
          "100%": { transform: "scale(1)" }
        }
      },
      animation: {
        "slide-in": "slide-in 220ms ease-out both",
        "pop-complete": "pop-complete 260ms ease-out both"
      }
    },
  },
  plugins: [],
};
