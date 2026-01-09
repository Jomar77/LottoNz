/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'base': '#3c2d66',           // dark-amethyst - Main brand color
        'accent': '#fe8302',          // princeton-orange - Powerball & CTAs
        'highlight-blue': '#0190d6',  // blue-bell - Supporting color
        'highlight-cream': '#fef68a', // banana-cream - Subtle highlights
      },
    },
  },
  plugins: [],
}
