/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        serif: ['"Fraunces Variable"', '"Iowan Old Style"', 'Georgia', 'serif'],
        sans: ['"Inter Variable"', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
      },
      colors: {
        paper: 'var(--paper)',
        ink: { DEFAULT: 'var(--ink)', 2: 'var(--ink-2)', 3: 'var(--ink-3)' },
        hairline: 'var(--hairline)',
        accent: {
          DEFAULT: 'var(--accent)',
          ink: 'var(--accent-ink)',
          text: 'var(--accent-text)',
          soft: 'var(--accent-soft)',
          tint: 'var(--accent-tint)',
          line: 'var(--accent-line)',
        },
        danger: 'var(--danger)',
        // kept for backward compatibility
        brand: { 50: 'var(--brand-50)', 100: 'var(--brand-100)', 500: 'var(--brand-500)', 600: 'var(--brand-600)', 700: 'var(--brand-700)' },
      },
    },
  },
  plugins: [],
}
