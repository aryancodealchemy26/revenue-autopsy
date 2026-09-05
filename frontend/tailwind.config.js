/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: '#FAFAFA',
        surface: {
          DEFAULT: '#FFFFFF',
          subtle: '#F8FAFC',
          hover: '#F1F5F9',
        },
        slate: {
          850: '#172033',
          950: '#0B0F19',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'Fira Code', 'SFMono-Regular', 'monospace'],
      },
    },
  },
  plugins: [],
}
