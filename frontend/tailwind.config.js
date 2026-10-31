/** @type {import('tailwindcss').Config} */
const config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        accent: {
          DEFAULT: "#4efa72",
          dim: "#3acc5c",
          dark: "#1f6b32",
        },
        bg: {
          primary: "#0d1410",
          secondary: "#111a14",
          card: "#161e19",
          "card-hover": "#1c2820",
        },
        border: {
          DEFAULT: "rgba(78, 250, 114, 0.12)",
          hover: "rgba(78, 250, 114, 0.3)",
        },
        text: {
          primary: "#f0fdf4",
          secondary: "#9db8a0",
          muted: "#5d7a63",
        },
        "glow-green": "rgba(78, 250, 114, 0.15)",
        "glow-green-strong": "rgba(78, 250, 114, 0.25)",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
      borderRadius: {
        "4xl": "2rem",
      },
      boxShadow: {
        "glow-sm": "0 0 12px rgba(78, 250, 114, 0.15)",
        "glow-md": "0 0 24px rgba(78, 250, 114, 0.2)",
        "glow-lg": "0 0 40px rgba(78, 250, 114, 0.25)",
        card: "0 4px 24px rgba(0,0,0,0.4)",
      },
      animation: {
        "pulse-green": "pulse-green 2s ease-in-out infinite",
        "slide-up": "slide-up 0.4s ease-out forwards",
        "fade-in": "fade-in 0.6s ease-out forwards",
        "float": "float 6s ease-in-out infinite",
      },
      keyframes: {
        "pulse-green": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.4" },
        },
        "slide-up": {
          from: { opacity: "0", transform: "translateY(20px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "float": {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-12px)" },
        },
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
};

module.exports = config;
