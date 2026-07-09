import type { Config } from 'tailwindcss'

// Token families copied verbatim from docs/frontend-brandkit.md §2.
// Use the class names (bg-primary, text-danger) in markup — never raw hex.
const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#4f46e5',
          50: '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
        },
        surface: {
          DEFAULT: '#ffffff',
          muted: '#f8fafc',
          border: '#e2e8f0',
          foreground: '#0f172a',
          subtle: '#64748b',
        },
        success: {
          DEFAULT: '#16a34a',
          soft: '#dcfce7',
        },
        danger: {
          DEFAULT: '#dc2626',
          soft: '#fee2e2',
        },
      },
      fontFamily: {
        sans: [
          'ui-sans-serif',
          'system-ui',
          '-apple-system',
          '"Segoe UI"',
          'Roboto',
          'sans-serif',
        ],
        mono: [
          'ui-monospace',
          '"SF Mono"',
          'Menlo',
          'Consolas',
          'monospace',
        ],
      },
    },
  },
  plugins: [],
}

export default config
