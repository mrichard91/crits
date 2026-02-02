/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // CRITs primary colors
        crits: {
          blue: '#3399ff',
          'blue-hover': '#5583ed',
          'blue-focus': '#9ecaed',
        },
        // Light theme
        light: {
          bg: '#f9f9f9',
          'bg-secondary': '#f5f5f5',
          'bg-tertiary': '#f1f1f1',
          border: '#dfdfdf',
          'border-light': '#ddd',
          text: '#333',
          'text-secondary': '#606060',
          'text-muted': '#747862',
        },
        // Dark theme
        dark: {
          bg: '#1a1a2e',
          'bg-secondary': '#16213e',
          'bg-tertiary': '#0f3460',
          border: '#374151',
          'border-light': '#4b5563',
          text: '#e5e5e5',
          'text-secondary': '#a3a3a3',
          'text-muted': '#737373',
        },
        // Status colors
        status: {
          success: '#22c55e',
          warning: '#f59e0b',
          error: '#ef4444',
          info: '#3b82f6',
        },
      },
      fontFamily: {
        sans: ['Verdana', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.8125rem', { lineHeight: '1.25rem' }],
        'base': ['0.875rem', { lineHeight: '1.5rem' }],
      },
      boxShadow: {
        'crits': '0px 2px 3px #969696',
        'crits-dark': '0px 2px 3px rgba(0, 0, 0, 0.3)',
      },
    },
  },
  plugins: [],
}
