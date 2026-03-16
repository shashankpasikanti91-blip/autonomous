/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./*.{js,ts,jsx,tsx}",
    "./src/**/*.{js,ts,jsx,tsx}",
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./layouts/**/*.{js,ts,jsx,tsx}",
    "./hooks/**/*.{js,ts,jsx,tsx}",
    "./services/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#2563eb",
        secondary: "#1f2937",
        success: "#10b981",
        warning: "#f59e0b",
        error: "#ef4444",
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "Roboto",
          "Oxygen",
          "Ubuntu",
          "Cantarell",
          '"Fira Sans"',
          '"Droid Sans"',
          '"Helvetica Neue"',
          "sans-serif",
        ],
        mono: [
          "SFMono-Regular",
          "Consolas",
          '"Liberation Mono"',
          "Menlo",
          "Courier",
          "monospace",
        ],
      },
      backgroundImage: {
        "gradient-primary": "linear-gradient(135deg, #2563eb 0%, #1e40af 100%)",
        "gradient-success": "linear-gradient(135deg, #10b981 0%, #059669 100%)",
        "gradient-warning": "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
        "gradient-error": "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)",
      },
      animation: {
        "spin-slow": "spin 3s linear infinite",
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      spacing: {
        "128": "32rem",
        "144": "36rem",
      },
      borderRadius: {
        "4xl": "2rem",
        "5xl": "2.5rem",
      },
      boxShadow: {
        "lg-soft": "0 2px 8px rgba(0, 0, 0, 0.1)",
        "xl-soft": "0 4px 16px rgba(0, 0, 0, 0.1)",
      },
    },
  },
  plugins: [],
  corePlugins: {
    preflight: true,
  },
};
