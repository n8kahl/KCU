/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          100: "#d4f1f4",
          500: "#189ab4",
          700: "#0f5f75"
        }
      }
    }
  },
  plugins: [],
};
