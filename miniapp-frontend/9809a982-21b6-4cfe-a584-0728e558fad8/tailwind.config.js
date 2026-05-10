
/** @type {import('tailwindcss').Config} */
export default {
  content: [
  './index.html',
  './src/**/*.{js,ts,jsx,tsx}'
],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        serif: ['"Playfair Display"', 'serif'],
      },
      colors: {
        university: {
          navy: '#1e293b',
          dark: '#0f172a',
          cream: '#faf7f2',
          ivory: '#f5f0e8',
          accent: '#3b82f6', // Blue for web
          pdf: '#f59e0b',    // Amber for PDF
        }
      },
      boxShadow: {
        'soft': '0 4px 20px -2px rgba(0, 0, 0, 0.05)',
      }
    },
  },
  plugins: [],
}
