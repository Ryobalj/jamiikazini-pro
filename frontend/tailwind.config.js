/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        nyasi: "#2E7D32",
        bahari: "#1976D2",
        chungwa: "#F57C00",
        makaa: "#424242",
        success: "#22c55e",
        error: "#ef4444",
        warning: "#f59e0b",
        info: "#3b82f6",
      },
      fontFamily: {
        sans: ["Poppins", "Roboto", "Inter", "sans-serif"],
      },
      boxShadow: {
        soft: "0px 2px 15px rgba(0, 0, 0, 0.1)",
        strong: "0px 4px 30px rgba(0, 0, 0, 0.15)",
        glow: "0 0 8px #F57C00, 0 0 16px #F57C00", // 🔥 chungwa glow
      },
      screens: {
        xs: "420px",
        "3xl": "1920px",
      },
      keyframes: {
        popup: {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(-5px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideInLeft: {
          "0%": { opacity: "0", transform: "translateX(-10px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        slideInRight: {
          "0%": { opacity: "0", transform: "translateX(10px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        spinSlow: {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
        glowPulse: {
          "0%, 100%": {
            boxShadow: "0 0 8px #F57C00, 0 0 16px #F57C00",
            opacity: "1",
          },
          "50%": {
            boxShadow: "0 0 0px #F57C00, 0 0 0px #F57C00",
            opacity: "0.4",
          },
        },
      },
      animation: {
        popup: "popup 0.3s ease-out forwards",
        fadeIn: "fadeIn 0.3s ease-in-out",
        slideInLeft: "slideInLeft 0.25s ease-out",
        slideInRight: "slideInRight 0.25s ease-out",
        spinSlow: "spinSlow 3s linear infinite",
        glowPulse: "glowPulse 2s ease-in-out infinite", // ✨ mpulse chungwa
      },
    },
  },
  plugins: [require('tailwind-scrollbar-hide')],
};